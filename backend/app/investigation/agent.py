"""RingGuard AI — Bounded Uncertainty-Driven Investigation Agent.

Stage 15: Investigation Efficiency + Business Impact.
Coordinates deterministic Expected Information Gain estimation, granular simulated tool
budgeting, factual uncertainty updating, explicit stopping criteria, and advisory
next-best-action decision support.

Strictly adheres to the defense-only mandate:
AI predicts. Evidence supports. Investigation adapts. Rules authorize. Humans decide. Outcomes verify.
Zero autonomous financial transactions or account state modifications.
"""

from datetime import datetime, timezone
from pathlib import Path
import math
from typing import Dict, Any, List, Optional, Tuple, Set
from sqlalchemy.orm import Session
import pandas as pd

from app.models.transaction import Transaction
from app.models.account import Account
from app.investigation.schemas import (
    StoppingReason,
    NextBestActionType,
    NextBestActionResponse,
    InvestigationTraceStep,
    InvestigationStateResponse,
    ToolExecutionResult,
    ToolExecutionStatus,
)
from app.investigation.service import InvestigationService
from app.services.model_service import get_model_service
from app.services.feature_service import get_feature_service, TransactionNotFoundError
from ml.calibration.calibrator import RiskCalibrator
from ml.evaluation.cold_start import determine_graph_confidence


# ==============================================================================
# OPERATIONAL CONFIGURATION & TOOL SIMULATION COSTS
# ==============================================================================

# Granular simulated tool execution costs in INR (Build Spec Section 15.B)
# Configured so multiple bounded queries can execute within the ₹150.00 ceiling.
TOOL_SIMULATED_COSTS: Dict[str, float] = {
    "get_account": 15.0,
    "get_transactions": 25.0,
    "find_related_accounts": 30.0,
    "find_shared_devices": 35.0,
    "find_shared_ips": 25.0,
    "find_common_beneficiaries": 30.0,
    "trace_fund_flow": 45.0,
    "reconstruct_timeline": 30.0,
    "get_risk_features": 20.0,
}

# Domain-specific base relevance for information gain estimation
TOOL_BASE_RELEVANCE: Dict[str, float] = {
    "find_shared_devices": 0.85,
    "trace_fund_flow": 0.80,
    "find_common_beneficiaries": 0.75,
    "find_related_accounts": 0.70,
    "get_risk_features": 0.65,
    "reconstruct_timeline": 0.60,
    "find_shared_ips": 0.55,
    "get_transactions": 0.50,
    "get_account": 0.40,
}

# Standard economic constants (aligned with Stages 12 & 14)
DEFAULT_INTERCEPTION_RATE: float = 0.85
COST_HUMAN_INVESTIGATION: float = 350.0   # ₹350.00 per flagged case (15 min human analyst)
COST_FALSE_POSITIVE: float = 1200.0       # ₹1,200.00 per false positive customer friction


def compute_modeled_net_value_saved(
    modeled_loss_avoided: float,
    tp: float,
    fp: float,
    c_fp: float = COST_FALSE_POSITIVE,
    c_inv: float = COST_HUMAN_INVESTIGATION,
) -> float:
    """Exact approved Stage 12/14 economic formula:
    Modeled Net Value Saved = Modeled Loss Avoided - (FP * CFP) - ((TP + FP) * Cinv)
    """
    investigation_overhead = (tp + fp) * c_inv
    friction_cost = fp * c_fp
    return round(modeled_loss_avoided - friction_cost - investigation_overhead, 2)


# In-memory investigation state cache keyed by transaction_id
_INVESTIGATION_CACHE: Dict[str, InvestigationStateResponse] = {}


class InvestigationAgent:
    """Bounded uncertainty-driven investigation agent for risk analysts."""

    def __init__(self, db: Session, models_dir: Optional[Path] = None):
        self.db = db
        self.inv_service = InvestigationService(db)
        self.model_service = get_model_service()
        self.feature_service = get_feature_service()

        if models_dir:
            self.models_dir = Path(models_dir)
        else:
            current_dir = Path(__file__).resolve().parent
            repo_root = current_dir.parents[2]
            self.models_dir = repo_root / "models"

        self._calibrator_b: Optional[RiskCalibrator] = None
        self._load_calibrators()

    def _load_calibrators(self) -> None:
        """Load frozen post-hoc Model B calibrator if available."""
        calib_b_path = self.models_dir / "calibrator_model_b.joblib"
        if calib_b_path.exists():
            try:
                self._calibrator_b = RiskCalibrator.load(calib_b_path)
            except Exception:
                self._calibrator_b = None

    # --------------------------------------------------------------------------
    # 1. UNCERTAINTY HEURISTIC
    # --------------------------------------------------------------------------

    @staticmethod
    def compute_initial_uncertainty(p_calibrated: float, graph_confidence: str) -> float:
        """Compute initial investigative-state uncertainty U_0 in [0.05, 0.95].
        
        Strictly defined as a deterministic investigative-state heuristic, NOT
        statistical model uncertainty.
        
        Formula:
            U_0 = clip(1.0 - 2 * |p_calibrated - 0.5| + Delta_confidence, 0.05, 0.95)
            where:
                Delta = 0.20 for LIMITED
                Delta = 0.35 for UNAVAILABLE
                Delta = 0.00 for VERIFIED
        """
        conf_upper = (graph_confidence or "VERIFIED").upper()
        if conf_upper == "UNAVAILABLE":
            delta = 0.35
        elif conf_upper == "LIMITED":
            delta = 0.20
        else:
            delta = 0.00

        ambiguity = 1.0 - 2.0 * abs(p_calibrated - 0.5)
        u0 = max(0.05, min(0.95, ambiguity + delta))
        return round(float(u0), 4)

    # --------------------------------------------------------------------------
    # 2. EXPECTED INFORMATION GAIN HEURISTIC
    # --------------------------------------------------------------------------

    @staticmethod
    def estimate_expected_information_gain(
        tool_name: str,
        current_uncertainty: float,
        executed_tools: List[str],
        evidence_collected: List[Dict[str, Any]],
    ) -> float:
        """Estimate pre-execution expected information gain E[IG] in [0.0, 1.0].
        
        Formula:
            E[IG](T) = U_{k-1} * BaseRelevance(T) * (1.0 - RedundancyPenalty(T))
        """
        if tool_name in executed_tools:
            return 0.0

        base_rel = TOOL_BASE_RELEVANCE.get(tool_name, 0.50)

        # Domain overlap redundancy penalty
        penalty = 0.0
        if tool_name == "find_shared_ips" and "find_shared_devices" in executed_tools:
            penalty += 0.20
        elif tool_name == "find_shared_devices" and "find_shared_ips" in executed_tools:
            penalty += 0.15
        elif tool_name == "trace_fund_flow" and "find_common_beneficiaries" in executed_tools:
            penalty += 0.15
        elif tool_name == "reconstruct_timeline" and "get_transactions" in executed_tools:
            penalty += 0.20
        elif tool_name == "find_related_accounts" and "find_shared_devices" in executed_tools:
            penalty += 0.10

        # Check existing evidence severity in domain
        if any(e.get("source_tool") == tool_name for e in evidence_collected):
            penalty += 0.30

        penalty = max(0.0, min(0.60, penalty))
        e_ig = current_uncertainty * base_rel * (1.0 - penalty)
        return round(max(0.0, min(1.0, float(e_ig))), 4)

    def select_next_best_tool(
        self,
        current_uncertainty: float,
        executed_tools: List[str],
        accumulated_cost: float,
        tool_budget: float,
        evidence_collected: List[Dict[str, Any]],
    ) -> Optional[Tuple[str, float]]:
        """Select eligible tool with highest E[IG] that fits within tool_budget."""
        all_tools = list(TOOL_SIMULATED_COSTS.keys())
        eligible: List[Tuple[str, float]] = []

        for t in all_tools:
            if t in executed_tools:
                continue
            cost = TOOL_SIMULATED_COSTS[t]
            if (accumulated_cost + cost) > tool_budget:
                continue
            e_ig = self.estimate_expected_information_gain(
                t, current_uncertainty, executed_tools, evidence_collected
            )
            eligible.append((t, e_ig))

        if not eligible:
            return None

        # Sort descending by E[IG], tie-breaker by lower cost
        eligible.sort(key=lambda x: (x[1], -TOOL_SIMULATED_COSTS[x[0]]), reverse=True)
        best_tool, best_ig = eligible[0]
        return best_tool, best_ig

    # --------------------------------------------------------------------------
    # 3. UNCERTAINTY UPDATING & EVIDENCE CORROBORATION
    # --------------------------------------------------------------------------

    @staticmethod
    def update_uncertainty(
        current_u: float,
        tool_name: str,
        result: ToolExecutionResult,
        p_calibrated: float,
        prior_evidence_count: int,
    ) -> Tuple[float, float, bool]:
        """Update investigative-state uncertainty U_k based on factual tool output.
        
        Returns:
            (new_uncertainty, uncertainty_reduction, is_conflicting)
        """
        # Case A: Factual corroborating structural evidence uncovered
        if result.status == ToolExecutionStatus.SUCCESS and result.result_count > 0:
            # Scale yield by verified result count (bounded between 0.15 and 0.40)
            info_yield = min(0.40, 0.15 + 0.05 * min(result.result_count, 5))
            new_u = max(0.05, min(0.95, current_u * (1.0 - info_yield)))
            reduction = round(current_u - new_u, 4)
            return round(new_u, 4), reduction, False

        # Case B: Empty or Not Found result
        if result.status in [ToolExecutionStatus.EMPTY, ToolExecutionStatus.NOT_FOUND] or result.result_count == 0:
            # Check for conflict: If model predicted high risk (>= 0.70) but core structural queries return 0
            if p_calibrated >= 0.70 and tool_name in ["find_shared_devices", "find_common_beneficiaries"]:
                # Penalize uncertainty due to conflicting benign infrastructure signals
                new_u = max(0.05, min(0.95, current_u + 0.10))
                return round(new_u, 4), 0.0, True
            else:
                # Weak or empty evidence leaves uncertainty unchanged
                bounded_u = max(0.05, min(0.95, current_u))
                return round(bounded_u, 4), 0.0, False

        # Case C: Unhandled status
        bounded_u = max(0.05, min(0.95, current_u))
        return round(bounded_u, 4), 0.0, False

    # --------------------------------------------------------------------------
    # 4. DETERMINISTIC STOPPING POLICY
    # --------------------------------------------------------------------------

    @staticmethod
    def evaluate_stopping_policy(
        step_count: int,
        max_steps: int,
        current_u: float,
        accumulated_cost: float,
        tool_budget: float,
        candidate_tools_remaining: List[str],
        next_expected_ig: float,
        evidence_collected: List[Dict[str, Any]],
        has_conflicting_evidence: bool,
    ) -> Tuple[bool, StoppingReason, str]:
        """Evaluate explicit deterministic stopping criteria in strict priority order."""
        # 1. Severe discrepancy
        if has_conflicting_evidence:
            return (
                True,
                StoppingReason.CONFLICTING_EVIDENCE_REQUIRES_HUMAN_REVIEW,
                "Severe discrepancy detected between model risk prior and factual infrastructure evidence.",
            )

        # 2. Corroborated multi-source ring evidence gathered (>= 2 distinct high-severity structural types)
        distinct_sources: Set[str] = set()
        for ev in evidence_collected:
            source = ev.get("source_tool")
            if source:
                distinct_sources.add(source)
        if len(distinct_sources) >= 2 and len(evidence_collected) >= 2:
            return (
                True,
                StoppingReason.SUFFICIENT_EVIDENCE,
                f"Sufficient corroborating evidence gathered across {len(distinct_sources)} distinct investigative domains.",
            )

        # 3. Uncertainty low enough
        if current_u <= 0.12:
            return (
                True,
                StoppingReason.UNCERTAINTY_LOW_ENOUGH,
                f"Investigative uncertainty successfully reduced to target threshold ({current_u:.4f} <= 0.12).",
            )

        # 4. Reached maximum allowed investigation steps
        if step_count >= max_steps:
            return (
                True,
                StoppingReason.MAX_INVESTIGATION_STEPS,
                f"Reached maximum allowed investigation steps ({step_count}/{max_steps}).",
            )

        # 5. Tool cost exceeded or budget exhausted
        if accumulated_cost >= tool_budget:
            return (
                True,
                StoppingReason.INVESTIGATION_COST_TOO_HIGH,
                f"Accumulated tool query cost (₹{accumulated_cost:.2f}) reached budget ceiling (₹{tool_budget:.2f}).",
            )

        cheapest_remaining = (
            min([TOOL_SIMULATED_COSTS[t] for t in candidate_tools_remaining])
            if candidate_tools_remaining
            else 0.0
        )
        if candidate_tools_remaining and (accumulated_cost + cheapest_remaining > tool_budget):
            return (
                True,
                StoppingReason.INVESTIGATION_COST_TOO_HIGH,
                f"Remaining budget (₹{tool_budget - accumulated_cost:.2f}) cannot afford any remaining tool (cheapest ₹{cheapest_remaining:.2f}).",
            )

        # 6. All candidate tools exhausted
        if not candidate_tools_remaining:
            return (
                True,
                StoppingReason.EVIDENCE_EXHAUSTED,
                "All registered controlled investigation tools have been executed.",
            )

        # 7. Information gain too low
        if next_expected_ig < 0.05:
            return (
                True,
                StoppingReason.INFORMATION_GAIN_TOO_LOW,
                f"Next best expected information gain ({next_expected_ig:.4f}) dropped below utility threshold (0.05).",
            )

        return (False, StoppingReason.IN_PROGRESS, "Investigation in progress.")

    # --------------------------------------------------------------------------
    # 5. ADVISORY NEXT-BEST-ACTION SYNTHESIS
    # --------------------------------------------------------------------------

    @staticmethod
    def derive_next_best_action(
        p_calibrated: float,
        current_u: float,
        graph_confidence: str,
        stopping_reason: StoppingReason,
        evidence_collected: List[Dict[str, Any]],
        exposure_amount: float,
        has_conflicting_evidence: bool,
        interception_rate: float = DEFAULT_INTERCEPTION_RATE,
    ) -> NextBestActionResponse:
        """Synthesize decision-support recommendation with mandatory human approval flag."""
        # Action mapping
        if (
            has_conflicting_evidence
            or stopping_reason == StoppingReason.CONFLICTING_EVIDENCE_REQUIRES_HUMAN_REVIEW
            or exposure_amount > 50000.0
        ):
            action = NextBestActionType.ESCALATE_TO_ANALYST
            reason = (
                f"High exposure (₹{exposure_amount:,.2f}) or conflicting evidence requires "
                f"specialist risk analyst review."
            )
            sufficiency = "MODERATE"
        elif p_calibrated >= 0.70 and (
            stopping_reason == StoppingReason.SUFFICIENT_EVIDENCE or len(evidence_collected) >= 2
        ):
            action = NextBestActionType.HOLD_FOR_REVIEW
            reason = (
                f"High calibrated risk ({p_calibrated:.4f}) corroborated by verified structural ring evidence."
            )
            sufficiency = "HIGH"
        elif graph_confidence in ["LIMITED", "UNAVAILABLE"] or current_u > 0.40:
            action = NextBestActionType.REQUEST_ADDITIONAL_VERIFICATION
            reason = (
                f"Graph confidence is {graph_confidence} with elevated investigative uncertainty ({current_u:.4f}). "
                f"Step-up identity/device verification recommended."
            )
            sufficiency = "LOW"
        elif p_calibrated < 0.20 and current_u <= 0.15 and len(evidence_collected) == 0:
            action = NextBestActionType.ALLOW
            reason = (
                f"Low calibrated risk ({p_calibrated:.4f}) with minimal investigative uncertainty ({current_u:.4f}) "
                f"and zero suspicious corroborations."
            )
            sufficiency = "HIGH"
        else:
            action = NextBestActionType.MONITOR
            reason = (
                f"Moderate risk profile ({p_calibrated:.4f}). Continuous behavioral monitoring recommended."
            )
            sufficiency = "MODERATE" if evidence_collected else "LOW"

        # Economic reconciliation (Stages 12 & 14 exact approved formula)
        # Modeled Net Value Saved = Modeled Loss Avoided - (FP * CFP) - ((TP + FP) * Cinv)
        is_flagged = action in [
            NextBestActionType.HOLD_FOR_REVIEW,
            NextBestActionType.ESCALATE_TO_ANALYST,
            NextBestActionType.REQUEST_ADDITIONAL_VERIFICATION,
        ]
        if is_flagged:
            tp = round(p_calibrated, 4)
            fp = round(max(0.0, 1.0 - p_calibrated), 4)
            loss_avoided = round(exposure_amount * p_calibrated * interception_rate, 2)
        else:
            tp = 0.0
            fp = 0.0
            loss_avoided = 0.0

        net_value = compute_modeled_net_value_saved(
            modeled_loss_avoided=loss_avoided,
            tp=tp,
            fp=fp,
            c_fp=COST_FALSE_POSITIVE,
            c_inv=COST_HUMAN_INVESTIGATION,
        )

        policy_factors = [
            f"Calibrated Risk: {p_calibrated:.4f}",
            f"Investigative Uncertainty: {current_u:.4f}",
            f"Graph Confidence: {graph_confidence}",
            f"Exposure Amount: ₹{exposure_amount:,.2f}",
            f"Stopping Trigger: {stopping_reason.value}",
            f"Human Review Routing: {'FLAGGED' if is_flagged else 'CLEARED'}",
        ]

        confidence_score = round(max(0.10, min(0.99, 1.0 - current_u)), 4)
        if is_flagged:
            econ_narrative = (
                f"Modeled loss avoided: ₹{loss_avoided:,.2f} ({int(interception_rate*100)}% interception). "
                f"Modeled net value saved: ₹{net_value:,.2f} after customer friction (₹{fp * COST_FALSE_POSITIVE:,.2f}) "
                f"and human review overhead (₹{(tp + fp) * COST_HUMAN_INVESTIGATION:,.2f})."
            )
        else:
            econ_narrative = (
                f"Transaction cleared without human review routing. Modeled investigation overhead: ₹0.00. "
                f"Customer friction: ₹0.00. Net value impact: ₹0.00."
            )

        return NextBestActionResponse(
            recommended_action=action,
            confidence_score=confidence_score,
            evidence_sufficiency=sufficiency,
            expected_financial_impact=econ_narrative,
            reason=reason,
            policy_relevant_factors=policy_factors,
            human_approval_required=True,  # STRICT REGULATORY SAFETY REQUIREMENT
        )

    # --------------------------------------------------------------------------
    # 6. BOUNDED INVESTIGATION ORCHESTRATION
    # --------------------------------------------------------------------------

    def run_investigation(
        self,
        transaction_id: str,
        max_steps: int = 5,
        tool_budget: float = 150.0,
        interception_rate: float = DEFAULT_INTERCEPTION_RATE,
    ) -> InvestigationStateResponse:
        """Execute a complete bounded uncertainty-driven investigation session."""
        clean_id = transaction_id.strip()

        # 1. Fetch transaction record
        tx = self.db.query(Transaction).filter(Transaction.transaction_id == clean_id).first()
        if not tx:
            raise TransactionNotFoundError(f"Transaction '{clean_id}' not found in database.")

        account_id = tx.account_id
        exposure = float(tx.amount)

        # 2. Extract Stage 8/14 features and probabilities
        feats_df_b, _ = self.feature_service.get_features(self.db, clean_id, model_type="graph")
        p_raw_b = self.model_service.predict_graph(feats_df_b)

        feats_df_a, _ = self.feature_service.get_features(self.db, clean_id, model_type="baseline")
        p_raw_a = self.model_service.predict_baseline(feats_df_a)

        # Apply Model B calibrator if available
        if self._calibrator_b is not None:
            p_calibrated = float(self._calibrator_b.predict_calibrated_proba([p_raw_b])[0])
        else:
            p_calibrated = p_raw_b

        p_calibrated = round(max(0.0, min(1.0, p_calibrated)), 4)

        # Determine Stage 14 point-in-time graph confidence
        graph_confidence = determine_graph_confidence(feats_df_b.iloc[0])

        # Compute initial uncertainty U_0
        initial_u = self.compute_initial_uncertainty(p_calibrated, graph_confidence)
        current_u = initial_u

        # Compute deterministic priority score (Formula 107)
        connected_accs = float(feats_df_b["g_connected_accounts_count"].iloc[0]) if "g_connected_accounts_count" in feats_df_b else 0.0
        network_leverage = min(1.0, connected_accs / 10.0)
        amount_norm = min(exposure, 100000.0) / 100000.0
        priority_score = round(
            0.35 * p_calibrated + 0.30 * amount_norm + 0.20 * initial_u + 0.15 * network_leverage,
            4,
        )

        # State tracking variables
        accumulated_cost: float = 0.0
        trace: List[InvestigationTraceStep] = []
        evidence_collected: List[Dict[str, Any]] = []
        executed_tools: List[str] = []
        has_conflicting_evidence: bool = False
        stopping_reason: StoppingReason = StoppingReason.IN_PROGRESS
        stopping_rationale: str = "Investigation in progress."

        # 3. Bounded investigation loop (up to max_steps)
        for step in range(1, max_steps + 1):
            candidate_tools = [t for t in TOOL_SIMULATED_COSTS.keys() if t not in executed_tools]

            # Find next best candidate
            selection = self.select_next_best_tool(
                current_u, executed_tools, accumulated_cost, tool_budget, evidence_collected
            )

            next_ig = selection[1] if selection else 0.0

            # Evaluate stopping criteria BEFORE execution
            should_stop, stop_reason, stop_msg = self.evaluate_stopping_policy(
                step_count=step - 1,
                max_steps=max_steps,
                current_u=current_u,
                accumulated_cost=accumulated_cost,
                tool_budget=tool_budget,
                candidate_tools_remaining=candidate_tools,
                next_expected_ig=next_ig,
                evidence_collected=evidence_collected,
                has_conflicting_evidence=has_conflicting_evidence,
            )

            if should_stop:
                stopping_reason = stop_reason
                stopping_rationale = stop_msg
                break

            if not selection:
                stopping_reason = StoppingReason.INVESTIGATION_COST_TOO_HIGH
                stopping_rationale = "No remaining tools fit within the configured investigation budget."
                break

            chosen_tool, expected_ig = selection
            tool_cost = TOOL_SIMULATED_COSTS[chosen_tool]
            u_before = current_u

            # 4. Execute controlled read-only tool
            as_of_iso = tx.timestamp.isoformat()
            tool_result = self._dispatch_tool(chosen_tool, clean_id, account_id, as_of_iso)

            executed_tools.append(chosen_tool)
            accumulated_cost += tool_cost

            # 5. Update uncertainty
            u_after, u_delta, is_conflict = self.update_uncertainty(
                current_u, chosen_tool, tool_result, p_calibrated, len(evidence_collected)
            )
            current_u = u_after
            if is_conflict:
                has_conflicting_evidence = True

            # Extract evidence items if present
            if tool_result.status == ToolExecutionStatus.SUCCESS and tool_result.result_count > 0:
                evidence_collected.append({
                    "step": step,
                    "source_tool": chosen_tool,
                    "target": tool_result.target,
                    "result_count": tool_result.result_count,
                    "evidence_ids": tool_result.evidence_ids,
                    "summary": f"{chosen_tool} returned {tool_result.result_count} verified records.",
                })

            # Record trace step
            target_id = tool_result.target or (account_id if "account" in chosen_tool or "device" in chosen_tool or "ip" in chosen_tool or "beneficiar" in chosen_tool else clean_id)
            ev_summary = (
                f"Discovered {tool_result.result_count} records via {chosen_tool}."
                if tool_result.result_count > 0
                else f"No corroborating records found via {chosen_tool}."
            )
            selection_reason = f"Highest expected information gain ({expected_ig:.4f}) within remaining budget."

            trace_step = InvestigationTraceStep(
                step_number=step,
                tool_name=chosen_tool,
                target_id=str(target_id),
                simulated_cost=tool_cost,
                expected_information_gain=expected_ig,
                selection_reason=selection_reason,
                uncertainty_before=u_before,
                uncertainty_after=u_after,
                uncertainty_reduction=u_delta,
                tool_status=tool_result.status.value,
                evidence_count=tool_result.result_count,
                evidence_summary=ev_summary,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            trace.append(trace_step)

            # Re-evaluate stopping criteria AFTER execution
            remaining_after = [t for t in TOOL_SIMULATED_COSTS.keys() if t not in executed_tools]
            next_sel_after = self.select_next_best_tool(
                current_u, executed_tools, accumulated_cost, tool_budget, evidence_collected
            )
            next_ig_after = next_sel_after[1] if next_sel_after else 0.0

            should_stop_after, stop_reason_after, stop_msg_after = self.evaluate_stopping_policy(
                step_count=step,
                max_steps=max_steps,
                current_u=current_u,
                accumulated_cost=accumulated_cost,
                tool_budget=tool_budget,
                candidate_tools_remaining=remaining_after,
                next_expected_ig=next_ig_after,
                evidence_collected=evidence_collected,
                has_conflicting_evidence=has_conflicting_evidence,
            )

            if should_stop_after:
                stopping_reason = stop_reason_after
                stopping_rationale = stop_msg_after
                break

        # Fallback if loop finishes without explicit stop
        if stopping_reason == StoppingReason.IN_PROGRESS:
            stopping_reason = StoppingReason.MAX_INVESTIGATION_STEPS
            stopping_rationale = f"Completed all {len(trace)} allowable investigation steps."

        # 6. Derive Next Best Action
        next_action = self.derive_next_best_action(
            p_calibrated=p_calibrated,
            current_u=current_u,
            graph_confidence=graph_confidence,
            stopping_reason=stopping_reason,
            evidence_collected=evidence_collected,
            exposure_amount=exposure,
            has_conflicting_evidence=has_conflicting_evidence,
            interception_rate=interception_rate,
        )

        # 7. Synthesize modeled economics dict (exact approved Stage 12/14 formula)
        is_flagged = next_action.recommended_action in [
            NextBestActionType.HOLD_FOR_REVIEW,
            NextBestActionType.ESCALATE_TO_ANALYST,
            NextBestActionType.REQUEST_ADDITIONAL_VERIFICATION,
        ]
        tp = round(p_calibrated, 4) if is_flagged else 0.0
        fp = round(max(0.0, 1.0 - p_calibrated), 4) if is_flagged else 0.0
        loss_avoided = round(exposure * p_calibrated * interception_rate, 2) if is_flagged else 0.0
        net_value = compute_modeled_net_value_saved(
            modeled_loss_avoided=loss_avoided,
            tp=tp,
            fp=fp,
            c_fp=COST_FALSE_POSITIVE,
            c_inv=COST_HUMAN_INVESTIGATION,
        )
        human_review_overhead = round((tp + fp) * COST_HUMAN_INVESTIGATION, 2)
        customer_friction_risk = round(fp * COST_FALSE_POSITIVE, 2)

        modeled_economics = {
            "exposure_amount": exposure,
            "calibrated_risk": p_calibrated,
            "assumed_interception_rate": interception_rate,
            "is_flagged_for_human_review": is_flagged,
            "modeled_tp_count": tp,
            "modeled_fp_count": fp,
            "modeled_loss_avoided": loss_avoided,
            "simulated_investigation_tool_cost": round(accumulated_cost, 2),
            "human_review_cost_benchmark": human_review_overhead,
            "customer_friction_risk": customer_friction_risk,
            "modeled_net_value_saved": net_value,
        }

        candidate_tools_remaining = [t for t in TOOL_SIMULATED_COSTS.keys() if t not in executed_tools]

        response = InvestigationStateResponse(
            transaction_id=clean_id,
            account_id=account_id,
            exposure_amount=exposure,
            model_a_probability=round(p_raw_a, 4),
            model_b_probability=round(p_raw_b, 4),
            calibrated_risk=p_calibrated,
            graph_confidence=graph_confidence,
            initial_uncertainty=initial_u,
            current_uncertainty=current_u,
            total_uncertainty_reduction=round(initial_u - current_u, 4),
            step_count=len(trace),
            max_steps=max_steps,
            total_simulated_tool_cost=round(accumulated_cost, 2),
            max_tool_budget=tool_budget,
            stopping_status="STOPPED" if stopping_reason != StoppingReason.IN_PROGRESS else "IN_PROGRESS",
            stopping_reason=stopping_reason,
            stopping_rationale=stopping_rationale,
            priority_score=priority_score,
            trace=trace,
            evidence_collected=evidence_collected,
            tools_executed=executed_tools,
            candidate_tools_remaining=candidate_tools_remaining,
            next_best_action=next_action,
            modeled_economics=modeled_economics,
        )

        # Cache state
        _INVESTIGATION_CACHE[clean_id] = response
        return response

    def get_investigation_state(self, transaction_id: str) -> InvestigationStateResponse:
        """Retrieve cached investigation state or run bounded investigation on the fly."""
        clean_id = transaction_id.strip()
        if clean_id in _INVESTIGATION_CACHE:
            return _INVESTIGATION_CACHE[clean_id]
        return self.run_investigation(clean_id)

    # --------------------------------------------------------------------------
    # 7. TOOL DISPATCHER
    # --------------------------------------------------------------------------

    def _dispatch_tool(
        self,
        tool_name: str,
        transaction_id: str,
        account_id: str,
        as_of_iso: str,
    ) -> ToolExecutionResult:
        """Dispatch candidate tool call to InvestigationService."""
        if tool_name == "get_account":
            return self.inv_service.get_account(account_id, as_of=as_of_iso)
        elif tool_name == "get_transactions":
            return self.inv_service.get_transactions(account_id, end_time=as_of_iso, limit=20)
        elif tool_name == "find_related_accounts":
            return self.inv_service.find_related_accounts(account_id, as_of=as_of_iso, limit=10)
        elif tool_name == "find_shared_devices":
            return self.inv_service.find_shared_devices(account_id, as_of=as_of_iso)
        elif tool_name == "find_shared_ips":
            return self.inv_service.find_shared_ips(account_id, as_of=as_of_iso)
        elif tool_name == "find_common_beneficiaries":
            return self.inv_service.find_common_beneficiaries(account_id, as_of=as_of_iso)
        elif tool_name == "trace_fund_flow":
            return self.inv_service.trace_fund_flow(transaction_id, as_of=as_of_iso, max_depth=2, max_results=20)
        elif tool_name == "reconstruct_timeline":
            return self.inv_service.reconstruct_timeline(transaction_id, as_of=as_of_iso)
        elif tool_name == "get_risk_features":
            return self.inv_service.get_risk_features(transaction_id, model_type="graph")
        else:
            return ToolExecutionResult(
                tool_name=tool_name,
                status=ToolExecutionStatus.UNAVAILABLE,
                target=transaction_id,
                as_of=as_of_iso,
                result=None,
                result_count=0,
                source="investigation_agent",
                evidence_ids=[],
                error_details=f"Unknown tool: {tool_name}",
            )
