"""RingGuard AI — Stage 17 Adaptive Uncertainty-Driven Investigation Engine.

V2 Stage 17: Uncertainty-Driven Investigation + Stopping Policy.
Coordinates deterministic Expected Information Gain (EIG) estimation,
granular simulated tool budgeting, evidence quality classification,
deterministic uncertainty updating, and strict stopping policy precedence.

Strictly adheres to:
- Read-only execution with PermissionGuard authorization.
- Temporal safety: All queries enforce point-in-time boundary (as_of = tx.timestamp).
- Non-enforcement: AI predicts and investigates; human review remains mandatory.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from sqlalchemy.orm import Session
import numpy as np

from app.models.transaction import Transaction
from app.models.account import Account
from app.investigation.schemas import (
    ToolExecutionStatus,
    ToolExecutionResult,
    StoppingReason,
    EvidenceQualityType,
    AdaptiveInvestigationStep,
    AdaptiveInvestigationResponse,
)
from app.investigation.service import InvestigationService
from app.investigation.permissions import PermissionGuard
from app.services.model_service import get_model_service
from app.services.feature_service import get_feature_service, TransactionNotFoundError
from ml.calibration.calibrator import RiskCalibrator
from ml.evaluation.cold_start import determine_graph_confidence


# ==============================================================================
# TOOL SIMULATION COSTS & BASE RELEVANCE
# ==============================================================================

# Granular simulated tool execution costs in INR (Stage 17 / Stage 15 specification)
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

# Correction 3: Fixed deterministic tool preference ordering for tie-breaking
DETERMINISTIC_TOOL_PREFERENCE: List[str] = [
    "find_shared_devices",
    "trace_fund_flow",
    "find_common_beneficiaries",
    "find_related_accounts",
    "get_risk_features",
    "reconstruct_timeline",
    "find_shared_ips",
    "get_transactions",
    "get_account",
]

# Core structural tools evaluated for conflicting evidence detection (Correction 4)
CORE_STRUCTURAL_TOOLS: Set[str] = {
    "find_shared_devices",
    "find_shared_ips",
    "find_common_beneficiaries",
    "find_related_accounts",
}


class AdaptiveInvestigationEngine:
    """Stage 17 deterministic uncertainty-driven investigation engine."""

    def __init__(
        self,
        db: Session,
        models_dir: Optional[Path] = None,
        calibrator: Optional[RiskCalibrator] = None,
    ):
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

        self._calibrator_b: Optional[RiskCalibrator] = calibrator
        if self._calibrator_b is None:
            self._load_calibrators()

        # Cached Stage 15 and Stage 16 services for context integration
        self._anom_svc: Optional[Any] = None
        self._prio_svc: Optional[Any] = None

    def _load_calibrators(self) -> None:
        """Load frozen post-hoc Model B calibrator if available."""
        calib_b_path = self.models_dir / "calibrator_model_b.joblib"
        if calib_b_path.exists():
            try:
                self._calibrator_b = RiskCalibrator.load(calib_b_path)
            except Exception:
                self._calibrator_b = None

    # --------------------------------------------------------------------------
    # 1. INITIAL UNCERTAINTY HEURISTIC
    # --------------------------------------------------------------------------

    @staticmethod
    def compute_initial_uncertainty(p_calibrated: float, graph_confidence: str) -> float:
        """Compute initial investigative uncertainty U_0 in [0.05, 0.95].
        
        Strictly defined as a deterministic investigative-state heuristic, NOT
        a Bayesian posterior probability.
        
        Formula:
            U_0 = clip(1.0 - 2.0 * |p_calibrated - 0.5| + Delta_confidence, 0.05, 0.95)
            where:
                Delta = 0.35 for UNAVAILABLE
                Delta = 0.20 for LIMITED
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
    # 2. DETERMINISTIC INFORMATION GAIN & TIE-BREAKING
    # --------------------------------------------------------------------------

    @staticmethod
    def compute_redundancy_penalty(
        tool_name: str,
        executed_tools: List[str],
        evidence_collected: List[Dict[str, Any]],
    ) -> float:
        """Compute domain-overlap and prior-evidence redundancy penalty in [0.0, 0.60]."""
        if tool_name in executed_tools:
            return 1.0  # Already executed: 100% redundant

        penalty = 0.0
        # Domain overlaps
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

        # Prior evidence collected in this tool domain
        if any(e.get("source_tool") == tool_name for e in evidence_collected):
            penalty += 0.30

        return round(max(0.0, min(0.60, penalty)), 4)

    def estimate_expected_information_gain(
        self,
        tool_name: str,
        current_uncertainty: float,
        executed_tools: List[str],
        evidence_collected: List[Dict[str, Any]],
    ) -> float:
        """Estimate pre-execution expected information gain EIG in [0.0, 1.0].
        
        Formula:
            EIG(T) = U_{k-1} * BaseRelevance(T) * (1.0 - RedundancyPenalty(T))
        """
        if tool_name in executed_tools:
            return 0.0

        base_rel = TOOL_BASE_RELEVANCE.get(tool_name, 0.50)
        penalty = self.compute_redundancy_penalty(tool_name, executed_tools, evidence_collected)
        eig = current_uncertainty * base_rel * (1.0 - penalty)
        return round(max(0.0, min(1.0, float(eig))), 4)

    def select_next_best_tool(
        self,
        current_uncertainty: float,
        executed_tools: List[str],
        accumulated_cost: float,
        tool_budget: float,
        evidence_collected: List[Dict[str, Any]],
    ) -> Optional[Tuple[str, float]]:
        """Select eligible tool with highest EIG fitting within budget.
        
        Correction 3: Fixed Deterministic Tie-Breaking Rule:
        1. Highest EIG (descending)
        2. Lowest tool execution cost (ascending)
        3. Deterministic tool preference order in DETERMINISTIC_TOOL_PREFERENCE
        """
        all_tools = list(TOOL_SIMULATED_COSTS.keys())
        eligible: List[Tuple[str, float, float, int]] = []

        for t in all_tools:
            if t in executed_tools:
                continue
            cost = TOOL_SIMULATED_COSTS[t]
            if (accumulated_cost + cost) > tool_budget:
                continue
            eig = self.estimate_expected_information_gain(
                t, current_uncertainty, executed_tools, evidence_collected
            )
            pref_idx = (
                DETERMINISTIC_TOOL_PREFERENCE.index(t)
                if t in DETERMINISTIC_TOOL_PREFERENCE
                else 999
            )
            eligible.append((t, eig, cost, pref_idx))

        if not eligible:
            return None

        # Sort: (-eig, cost, pref_idx) guarantees deterministic tie-breaking
        eligible.sort(key=lambda x: (-x[1], x[2], x[3]))
        best_tool, best_eig, _, _ = eligible[0]
        return best_tool, best_eig

    # --------------------------------------------------------------------------
    # 3. EVIDENCE QUALITY & UNCERTAINTY REVISION RULES
    # --------------------------------------------------------------------------

    @staticmethod
    def evaluate_evidence_quality(
        tool_name: str,
        result: ToolExecutionResult,
        p_calibrated: float,
        executed_tools: List[str],
        all_results_by_tool: Dict[str, ToolExecutionResult],
    ) -> EvidenceQualityType:
        """Classify evidence quality obtained from tool execution.
        
        Correction 4:
        - STRONG: Verified structural records linking entities or corroborating ring activity.
        - WEAK_OR_EMPTY: 0 records returned, informational baseline tools, or single isolated transaction.
        - CONFLICTING: High calibrated risk (>= 0.70) AND MULTIPLE structural queries executed
          AND ALL of them returned zero records (severe model-vs-infrastructure discrepancy).
        """
        # Informational metadata / risk features do not constitute independent structural ring evidence
        if tool_name in ["get_account", "get_risk_features"]:
            return EvidenceQualityType.WEAK_OR_EMPTY

        # For trace_fund_flow, a single hop is merely the originating transaction itself.
        # Strong fund flow evidence requires multi-hop flow (> 1) or genuine linked evidence IDs.
        if tool_name == "trace_fund_flow":
            if result.status == ToolExecutionStatus.SUCCESS and (result.result_count > 1 or len(result.evidence_ids) > 0):
                return EvidenceQualityType.STRONG
            return EvidenceQualityType.WEAK_OR_EMPTY

        # Core structural tools: shared devices, shared IPs, common beneficiaries, related accounts, timeline
        has_records = (
            result.status == ToolExecutionStatus.SUCCESS
            and result.result_count > 0
        )
        if has_records:
            return EvidenceQualityType.STRONG

        # Check for genuine multi-source structural contradiction (Correction 4)
        if p_calibrated >= 0.70 and tool_name in CORE_STRUCTURAL_TOOLS:
            executed_structural = [
                t for t in executed_tools if t in CORE_STRUCTURAL_TOOLS
            ]
            if tool_name not in executed_structural:
                executed_structural.append(tool_name)

            if len(executed_structural) >= 2:
                # Check if ALL executed structural tools returned 0 records
                all_empty = True
                for st in executed_structural:
                    r = all_results_by_tool.get(st)
                    if r and r.status == ToolExecutionStatus.SUCCESS and r.result_count > 0:
                        all_empty = False
                        break
                if all_empty:
                    return EvidenceQualityType.CONFLICTING

        return EvidenceQualityType.WEAK_OR_EMPTY

    @staticmethod
    def update_uncertainty(
        current_u: float,
        quality: EvidenceQualityType,
        result_count: int,
    ) -> Tuple[float, float]:
        """Deterministic uncertainty update rule.
        
        Returns:
            (new_uncertainty, uncertainty_reduction)
        """
        if quality == EvidenceQualityType.STRONG and result_count > 0:
            # Scaled yield bounded between 0.15 and 0.45
            info_yield = min(0.45, 0.15 + 0.06 * min(result_count, 5))
            new_u = max(0.05, min(0.95, round(current_u * (1.0 - info_yield), 4)))
            reduction = round(current_u - new_u, 4)
            return new_u, reduction

        elif quality == EvidenceQualityType.CONFLICTING:
            # Conflicting signals increase uncertainty
            new_u = max(0.05, min(0.95, round(current_u + 0.10, 4)))
            return new_u, 0.0

        else:
            # WEAK_OR_EMPTY leaves uncertainty unchanged
            return current_u, 0.0

    # --------------------------------------------------------------------------
    # 4. DETERMINISTIC STOPPING POLICY (Correction 8)
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
        """Evaluate explicit deterministic stopping criteria in strict priority order.
        
        Correction 8: Precedence order is strictly enforced:
        1. CONFLICTING_EVIDENCE_REQUIRES_HUMAN_REVIEW
        2. SUFFICIENT_EVIDENCE
        3. UNCERTAINTY_LOW_ENOUGH
        4. MAX_INVESTIGATION_STEPS
        5. INVESTIGATION_COST_TOO_HIGH
        6. EVIDENCE_EXHAUSTED
        7. INFORMATION_GAIN_TOO_LOW
        """
        # 1. Severe discrepancy
        if has_conflicting_evidence:
            return (
                True,
                StoppingReason.CONFLICTING_EVIDENCE_REQUIRES_HUMAN_REVIEW,
                "Severe discrepancy detected: High model risk with zero structural entities across multiple investigations.",
            )

        # 2. Corroborated multi-source ring evidence gathered (>= 2 distinct domains)
        distinct_sources = {
            ev.get("source_tool") for ev in evidence_collected if ev.get("source_tool")
        }
        if len(distinct_sources) >= 2 and len(evidence_collected) >= 2:
            return (
                True,
                StoppingReason.SUFFICIENT_EVIDENCE,
                f"Sufficient corroborating evidence gathered across {len(distinct_sources)} distinct investigative domains.",
            )

        # 3. Uncertainty low enough (U <= 0.12)
        if current_u <= 0.12:
            return (
                True,
                StoppingReason.UNCERTAINTY_LOW_ENOUGH,
                f"Investigative uncertainty successfully reduced to target threshold ({current_u:.4f} <= 0.12).",
            )

        # 4. Reached maximum allowed investigation steps (step_count >= max_steps)
        if step_count >= max_steps:
            return (
                True,
                StoppingReason.MAX_INVESTIGATION_STEPS,
                f"Reached maximum allowed investigation steps ({step_count}/{max_steps}).",
            )

        # 5. Tool cost ceiling reached or remaining budget cannot afford any tool
        if accumulated_cost >= tool_budget:
            return (
                True,
                StoppingReason.INVESTIGATION_COST_TOO_HIGH,
                f"Accumulated tool query cost (₹{accumulated_cost:.2f}) reached budget ceiling (₹{tool_budget:.2f}).",
            )

        if candidate_tools_remaining:
            cheapest_remaining = min([TOOL_SIMULATED_COSTS[t] for t in candidate_tools_remaining])
            if (accumulated_cost + cheapest_remaining) > tool_budget:
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

        # 7. Information gain dropped below utility threshold
        if next_expected_ig < 0.05:
            return (
                True,
                StoppingReason.INFORMATION_GAIN_TOO_LOW,
                f"Next best expected information gain ({next_expected_ig:.4f}) dropped below utility threshold (0.05).",
            )

        return (False, StoppingReason.IN_PROGRESS, "Investigation in progress.")

    # --------------------------------------------------------------------------
    # 5. ADAPTIVE INVESTIGATION ORCHESTRATION
    # --------------------------------------------------------------------------

    def run_investigation(
        self,
        transaction_id: str,
        max_steps: int = 5,
        tool_budget: float = 150.0,
        include_context: bool = True,
    ) -> AdaptiveInvestigationResponse:
        """Execute a complete Stage 17 uncertainty-driven investigation session."""
        clean_id = transaction_id.strip()

        # 1. Fetch transaction record
        tx = self.db.query(Transaction).filter(Transaction.transaction_id == clean_id).first()
        if not tx:
            raise TransactionNotFoundError(f"Transaction '{clean_id}' not found in database.")

        account_id = tx.account_id
        exposure = float(tx.amount)
        # Point-in-time boundary ISO string (Correction 2: Temporal Safety)
        as_of_iso = tx.timestamp.isoformat()

        # 2. Extract model features and calibrated risk
        feats_df_b, _ = self.feature_service.get_features(self.db, clean_id, model_type="graph")
        p_raw_b = float(self.model_service.predict_graph(feats_df_b))

        feats_df_a, _ = self.feature_service.get_features(self.db, clean_id, model_type="baseline")
        p_raw_a = float(self.model_service.predict_baseline(feats_df_a))

        if self._calibrator_b is not None:
            p_calibrated = float(self._calibrator_b.predict_calibrated_proba([p_raw_b])[0])
        else:
            p_calibrated = p_raw_b

        p_calibrated = round(max(0.0, min(1.0, p_calibrated)), 4)
        graph_confidence = determine_graph_confidence(feats_df_b.iloc[0])

        # Compute initial investigative uncertainty U_0
        initial_u = self.compute_initial_uncertainty(p_calibrated, graph_confidence)
        current_u = initial_u

        # State tracking variables
        accumulated_cost: float = 0.0
        trace_steps: List[AdaptiveInvestigationStep] = []
        evidence_collected: List[Dict[str, Any]] = []
        all_evidence_ids: List[str] = []
        executed_tools: List[str] = []
        all_results_by_tool: Dict[str, ToolExecutionResult] = {}
        has_conflicting_evidence: bool = False
        stopping_reason: StoppingReason = StoppingReason.IN_PROGRESS
        stopping_rationale: str = "Investigation in progress."

        # 3. Adaptive Investigation Loop (up to max_steps)
        for step in range(1, max_steps + 1):
            candidate_tools = [t for t in TOOL_SIMULATED_COSTS.keys() if t not in executed_tools]

            # Select next best tool using deterministic tie-breaking (Correction 3)
            selection = self.select_next_best_tool(
                current_u, executed_tools, accumulated_cost, tool_budget, evidence_collected
            )
            next_eig = selection[1] if selection else 0.0

            # Pre-execution stopping policy evaluation
            should_stop, stop_reason, stop_msg = self.evaluate_stopping_policy(
                step_count=step - 1,
                max_steps=max_steps,
                current_u=current_u,
                accumulated_cost=accumulated_cost,
                tool_budget=tool_budget,
                candidate_tools_remaining=candidate_tools,
                next_expected_ig=next_eig,
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

            chosen_tool, expected_eig = selection
            tool_cost = TOOL_SIMULATED_COSTS[chosen_tool]
            u_before = current_u

            # Execute controlled read-only tool with strict point-in-time boundary (Correction 2)
            tool_result = self._dispatch_tool(chosen_tool, clean_id, account_id, as_of_iso)
            executed_tools.append(chosen_tool)
            accumulated_cost += tool_cost
            all_results_by_tool[chosen_tool] = tool_result

            # Evaluate evidence quality (Correction 4)
            evidence_quality = self.evaluate_evidence_quality(
                chosen_tool, tool_result, p_calibrated, executed_tools, all_results_by_tool
            )
            if evidence_quality == EvidenceQualityType.CONFLICTING:
                has_conflicting_evidence = True

            # Update investigative uncertainty
            u_after, u_delta = self.update_uncertainty(
                current_u, evidence_quality, tool_result.result_count
            )
            current_u = u_after

            # Collect genuine evidence IDs if present
            step_ev_ids = tool_result.evidence_ids or []
            for ev_id in step_ev_ids:
                if ev_id not in all_evidence_ids:
                    all_evidence_ids.append(ev_id)

            if evidence_quality == EvidenceQualityType.STRONG:
                evidence_collected.append({
                    "step": step,
                    "source_tool": chosen_tool,
                    "target": tool_result.target,
                    "result_count": tool_result.result_count,
                    "evidence_ids": step_ev_ids,
                    "summary": f"{chosen_tool} returned {tool_result.result_count} verified records.",
                })

            # Formulate concise, explainable rationale without hidden chain-of-thought
            target_id = tool_result.target or clean_id
            if evidence_quality == EvidenceQualityType.STRONG:
                step_rationale = (
                    f"Selected {chosen_tool} (EIG={expected_eig:.3f}). "
                    f"Discovered {tool_result.result_count} verified records; "
                    f"reduced investigative uncertainty from {u_before:.4f} to {u_after:.4f}."
                )
                actual_yield = round(min(0.45, 0.15 + 0.06 * min(tool_result.result_count, 5)), 4)
            elif evidence_quality == EvidenceQualityType.CONFLICTING:
                step_rationale = (
                    f"Selected {chosen_tool} (EIG={expected_eig:.3f}). "
                    f"Zero structural records found despite high model risk ({p_calibrated:.4f}); "
                    f"contradiction increased uncertainty to {u_after:.4f}."
                )
                actual_yield = 0.0
            else:
                step_rationale = (
                    f"Selected {chosen_tool} (EIG={expected_eig:.3f}). "
                    f"No records discovered; investigative uncertainty remained unchanged at {u_after:.4f}."
                )
                actual_yield = 0.0

            step_record = AdaptiveInvestigationStep(
                step_number=step,
                tool_name=chosen_tool,
                target_id=str(target_id),
                tool_cost=tool_cost,
                estimated_information_gain=expected_eig,
                actual_information_yield=actual_yield,
                uncertainty_before=u_before,
                uncertainty_after=u_after,
                uncertainty_reduction=u_delta,
                evidence_count=tool_result.result_count,
                evidence_ids=step_ev_ids,
                evidence_quality=evidence_quality,
                step_rationale=step_rationale,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            trace_steps.append(step_record)

            # Post-execution stopping policy evaluation
            remaining_after = [t for t in TOOL_SIMULATED_COSTS.keys() if t not in executed_tools]
            next_sel_after = self.select_next_best_tool(
                current_u, executed_tools, accumulated_cost, tool_budget, evidence_collected
            )
            next_eig_after = next_sel_after[1] if next_sel_after else 0.0

            should_stop_post, stop_reason_post, stop_msg_post = self.evaluate_stopping_policy(
                step_count=step,
                max_steps=max_steps,
                current_u=current_u,
                accumulated_cost=accumulated_cost,
                tool_budget=tool_budget,
                candidate_tools_remaining=remaining_after,
                next_expected_ig=next_eig_after,
                evidence_collected=evidence_collected,
                has_conflicting_evidence=has_conflicting_evidence,
            )

            if should_stop_post:
                stopping_reason = stop_reason_post
                stopping_rationale = stop_msg_post
                break

        if stopping_reason == StoppingReason.IN_PROGRESS:
            stopping_reason = StoppingReason.MAX_INVESTIGATION_STEPS
            stopping_rationale = f"Completed maximum allowed investigation steps ({len(trace_steps)}/{max_steps})."

        # 4. Integrate Stage 15 & 16 context (Correction 5)
        sys_anom_score: Optional[float] = None
        prio_score: Optional[float] = None
        exp_value: Optional[float] = None
        prio_rank: Optional[int] = None

        if include_context:
            try:
                if self._anom_svc is None:
                    from app.anomaly.service import SystemicAnomalyService
                    self._anom_svc = SystemicAnomalyService(self.db)
                anom_res = self._anom_svc.analyze_transaction(clean_id)
                sys_anom_score = anom_res.systemic_anomaly_score
            except Exception:
                sys_anom_score = None

            try:
                if self._prio_svc is None:
                    from app.prioritization.service import PortfolioPrioritizationService
                    self._prio_svc = PortfolioPrioritizationService(
                        self.db, calibrator=self._calibrator_b, anomaly_service=self._anom_svc
                    )
                prio_res = self._prio_svc.prioritize_transaction(clean_id)
                prio_score = prio_res.priority_score
                exp_value = prio_res.expected_value
                prio_rank = prio_res.priority_rank
            except Exception:
                prio_score = None
                exp_value = None
                prio_rank = None

        total_reduction = round(initial_u - current_u, 4)
        rel_reduction = round((initial_u - current_u) / initial_u, 4) if initial_u > 0 else 0.0
        candidate_remaining = [t for t in TOOL_SIMULATED_COSTS.keys() if t not in executed_tools]

        return AdaptiveInvestigationResponse(
            transaction_id=clean_id,
            account_id=account_id,
            timestamp=as_of_iso,
            exposure_amount=exposure,
            calibrated_risk_score=p_calibrated,
            model_b_raw_probability=round(p_raw_b, 4),
            model_a_raw_probability=round(p_raw_a, 4),
            graph_confidence=graph_confidence,
            initial_uncertainty=initial_u,
            final_uncertainty=current_u,
            uncertainty_reduction=total_reduction,
            relative_uncertainty_reduction=rel_reduction,
            step_count=len(trace_steps),
            max_steps=max_steps,
            total_tool_cost=round(accumulated_cost, 2),
            max_tool_budget=tool_budget,
            selected_tools=executed_tools,
            candidate_tools_remaining=candidate_remaining,
            steps=trace_steps,
            evidence_ids=all_evidence_ids,
            stop_decision="STOP",
            stopping_reason=stopping_reason.value if hasattr(stopping_reason, "value") else str(stopping_reason),
            stopping_rationale=stopping_rationale,
            stage15_systemic_anomaly_score=sys_anom_score,
            stage16_priority_score=prio_score,
            stage16_expected_value=exp_value,
            stage16_priority_rank=prio_rank,
            human_approval_required=True,
            disclaimer="INVESTIGATION DECISION SUPPORT: Read-only investigative uncertainty engine. Does not take autonomous financial or account enforcement actions.",
        )

    # --------------------------------------------------------------------------
    # 6. TOOL DISPATCHER (Point-in-Time Temporal Safeguard)
    # --------------------------------------------------------------------------

    def _dispatch_tool(
        self,
        tool_name: str,
        transaction_id: str,
        account_id: str,
        as_of_iso: str,
    ) -> ToolExecutionResult:
        """Dispatch candidate tool call with strict point-in-time temporal boundary."""
        PermissionGuard.check_permission("INVESTIGATION_READ")
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
                source="adaptive_investigation_engine",
                evidence_ids=[],
                error_details=f"Unknown tool: {tool_name}",
            )
