"""RingGuard AI — Deterministic Risk Policy Engine Service.

Stage 19: Deterministic Risk Policy Engine + Next-Best-Action (NBA).
Evaluates multi-stage risk, evidence, uncertainty, and systemic context
to produce explainable Next-Best-Action recommendations for human analysts.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Set
from sqlalchemy.orm import Session
from pathlib import Path

from app.db.session import SessionLocal
from app.models.transaction import Transaction
from app.policy.schemas import (
    PolicyAction,
    ActionPriority,
    HumanReviewRole,
    PolicyDecision,
    PolicyRuleDefinition,
    PolicyRulesCatalogResponse,
)
from app.prioritization.service import PortfolioPrioritizationService
from app.anomaly.service import SystemicAnomalyService
from app.investigation.adaptive import AdaptiveInvestigationEngine
from app.counterfactual.service import CounterfactualAttributionService
from app.evidence.engine import EvidenceEngine
from app.services.model_service import get_model_service
from app.services.feature_service import get_feature_service
from ml.calibration.calibrator import RiskCalibrator


POLICY_VERSION = "ringguard_policy_v1"

# ------------------------------------------------------------------------------
# DETERMINISTIC POLICY RULES CATALOG
# ------------------------------------------------------------------------------

POLICY_RULES_CATALOG: List[PolicyRuleDefinition] = [
    PolicyRuleDefinition(
        rule_id="POLICY_RULE_0_FALLBACK_REVIEW",
        precedence=1,
        recommended_action=PolicyAction.FALLBACK_REVIEW,
        title="Rule 0 -- Fallback Review (Missing / Inconsistent Data)",
        condition_description="Any critical upstream signal is missing, unavailable, inconsistent, or invalid.",
        rationale_template="Required decision signal is unavailable or inconsistent; manual review is required.",
        required_human_role=HumanReviewRole.RISK_ANALYST,
        action_priority=ActionPriority.MEDIUM,
    ),
    PolicyRuleDefinition(
        rule_id="POLICY_RULE_1_REQUEST_VERIFICATION",
        precedence=2,
        recommended_action=PolicyAction.REQUEST_VERIFICATION,
        title="Rule 1 -- Request Verification (High Uncertainty / Conflicting Evidence)",
        condition_description="investigative_uncertainty > 0.40 OR conflicting evidence is present.",
        rationale_template="High decision uncertainty or contradictory structural evidence prevents reliable clearance.",
        required_human_role=HumanReviewRole.FRAUD_INVESTIGATOR,
        action_priority=ActionPriority.HIGH,
    ),
    PolicyRuleDefinition(
        rule_id="POLICY_RULE_2_ESCALATE",
        precedence=3,
        recommended_action=PolicyAction.ESCALATE,
        title="Rule 2 -- Escalate (Critical Corroborated Syndicate Risk)",
        condition_description="calibrated_risk_score >= 0.85 AND corroborated_structural_domains >= 2 AND systemic_anomaly_score >= 0.35 AND expected_value > 0.",
        rationale_template="Critical calibrated risk corroborated by >=2 structural domains, elevated systemic anomaly, and positive expected value.",
        required_human_role=HumanReviewRole.SENIOR_RISK_ANALYST,
        action_priority=ActionPriority.CRITICAL,
    ),
    PolicyRuleDefinition(
        rule_id="POLICY_RULE_3_HOLD_FOR_REVIEW",
        precedence=4,
        recommended_action=PolicyAction.HOLD_FOR_REVIEW,
        title="Rule 3 -- Hold for Review (High Risk Positive EV)",
        condition_description="calibrated_risk_score >= 0.70 AND expected_value > 0 AND corroborated_structural_domains >= 1 AND investigative_uncertainty <= 0.40.",
        rationale_template="High calibrated risk with positive expected value and confirmed structural evidence within acceptable uncertainty.",
        required_human_role=HumanReviewRole.RISK_ANALYST,
        action_priority=ActionPriority.MEDIUM_HIGH,
    ),
    PolicyRuleDefinition(
        rule_id="POLICY_RULE_4_MONITOR",
        precedence=5,
        recommended_action=PolicyAction.MONITOR,
        title="Rule 4 -- Monitor (Moderate Risk or Elevated Background Activity)",
        condition_description="(calibrated_risk_score >= 0.20 AND calibrated_risk_score < 0.70) OR (low risk but systemic anomaly >= 0.35 or uncertainty > 0.12).",
        rationale_template="Moderate risk posture or elevated background activity warrants analytical telemetry observation.",
        required_human_role=HumanReviewRole.AUTOMATED_TELEMETRY_ANALYST,
        action_priority=ActionPriority.LOW_MEDIUM,
    ),
    PolicyRuleDefinition(
        rule_id="POLICY_RULE_5_ALLOW",
        precedence=6,
        recommended_action=PolicyAction.ALLOW,
        title="Rule 5 -- Clear Low Risk Allow",
        condition_description="calibrated_risk_score < 0.20 AND investigative_uncertainty <= 0.12 AND corroborated_structural_domains == 0 AND systemic_anomaly_score < 0.35.",
        rationale_template="Low calibrated risk with resolved uncertainty, zero structural evidence, and low systemic anomaly.",
        required_human_role=HumanReviewRole.NONE,
        action_priority=ActionPriority.LOW,
    ),
]


# Global cached calibrator singleton
_shared_calibrator_b: Optional[RiskCalibrator] = None


def get_shared_calibrator_b() -> Optional[RiskCalibrator]:
    """Retrieve or initialize the global shared Model B calibrator singleton."""
    global _shared_calibrator_b
    if _shared_calibrator_b is None:
        repo_root = Path(__file__).resolve().parents[3]
        calib_path = repo_root / "models" / "calibrator_model_b.joblib"
        if calib_path.exists():
            try:
                _shared_calibrator_b = RiskCalibrator.load(calib_path)
            except Exception:
                _shared_calibrator_b = None
    return _shared_calibrator_b


class PolicyDecisionEngine:
    """Deterministic, transparent risk policy decision engine."""

    def __init__(
        self,
        db: Optional[Session] = None,
        calibrator: Optional[RiskCalibrator] = None,
        prioritization_service: Optional[PortfolioPrioritizationService] = None,
        anomaly_service: Optional[SystemicAnomalyService] = None,
        adaptive_engine: Optional[AdaptiveInvestigationEngine] = None,
        cf_service: Optional[CounterfactualAttributionService] = None,
        evidence_engine: Optional[EvidenceEngine] = None,
    ):
        self.db = db or SessionLocal()
        self._owns_session = db is None

        # Shared singleton calibrator and underlying services
        self.calibrator = calibrator or get_shared_calibrator_b()
        self.evidence_engine = evidence_engine or EvidenceEngine(self.db)
        self.anomaly_service = anomaly_service or SystemicAnomalyService(
            self.db, evidence_engine=self.evidence_engine
        )
        self.prioritization_service = prioritization_service or PortfolioPrioritizationService(
            self.db, calibrator=self.calibrator, anomaly_service=self.anomaly_service
        )
        self.adaptive_engine = adaptive_engine or AdaptiveInvestigationEngine(
            self.db, calibrator=self.calibrator
        )
        self.cf_service = cf_service or CounterfactualAttributionService(
            self.db, calibrator=self.calibrator
        )

    def close(self):
        """Close database session if self-owned."""
        if self._owns_session:
            self.db.close()

    @staticmethod
    def get_rules_catalog() -> PolicyRulesCatalogResponse:
        """Return transparent policy rules catalog."""
        return PolicyRulesCatalogResponse(
            policy_version=POLICY_VERSION,
            rule_count=len(POLICY_RULES_CATALOG),
            precedence_order=[r.rule_id for r in POLICY_RULES_CATALOG],
            rules=POLICY_RULES_CATALOG,
        )

    def evaluate_signals(
        self,
        transaction_id: str,
        account_id: str,
        timestamp: str,
        calibrated_risk_score: Optional[float],
        expected_value: Optional[float],
        priority_score: Optional[float],
        systemic_anomaly_score: Optional[float],
        investigative_uncertainty: Optional[float],
        evidence_domains: Optional[List[str]] = None,
        evidence_count: int = 0,
        has_conflicting_evidence: bool = False,
        supporting_evidence_ids: Optional[List[str]] = None,
        counterfactual_context: Optional[Dict[str, Any]] = None,
    ) -> PolicyDecision:
        """Evaluate signals deterministically across the declared precedence order."""
        evidence_domains = evidence_domains or []
        supporting_evidence_ids = supporting_evidence_ids or []
        corroborated_structural_domains = len(set(evidence_domains))

        # ----------------------------------------------------------------------
        # RULE 0: FALLBACK_REVIEW (Precedence 1)
        # Any critical signal missing, None, or invalid
        # ----------------------------------------------------------------------
        is_missing_signal = (
            calibrated_risk_score is None
            or expected_value is None
            or priority_score is None
            or systemic_anomaly_score is None
            or investigative_uncertainty is None
            or not (0.0 <= calibrated_risk_score <= 1.0)
            or not (0.0 <= systemic_anomaly_score <= 1.0)
            or not (0.0 <= investigative_uncertainty <= 1.0)
        )

        if is_missing_signal:
            return PolicyDecision(
                transaction_id=transaction_id,
                account_id=account_id,
                timestamp=timestamp,
                calibrated_risk_score=calibrated_risk_score if calibrated_risk_score is not None else 0.50,
                expected_value=expected_value if expected_value is not None else 0.0,
                priority_score=priority_score if priority_score is not None else 0.50,
                systemic_anomaly_score=systemic_anomaly_score if systemic_anomaly_score is not None else 0.50,
                investigative_uncertainty=investigative_uncertainty if investigative_uncertainty is not None else 0.50,
                evidence_domains=evidence_domains,
                evidence_count=evidence_count,
                corroborated_structural_domains=corroborated_structural_domains,
                has_conflicting_evidence=has_conflicting_evidence,
                recommended_action=PolicyAction.FALLBACK_REVIEW,
                action_priority=ActionPriority.MEDIUM,
                policy_rule_id="POLICY_RULE_0_FALLBACK_REVIEW",
                policy_version=POLICY_VERSION,
                policy_reason="Required decision signal is unavailable or inconsistent; manual review is required.",
                required_human_role=HumanReviewRole.RISK_ANALYST,
                required_verification="Inspect data pipeline health and verify transaction context manually due to unavailable or inconsistent upstream signals.",
                supporting_evidence_ids=supporting_evidence_ids,
                blocking_conditions=["Critical analytical signals unavailable or degraded"],
                confidence=0.50,
                human_approval_required=True,
                execution_status="NOT_EXECUTED",
                autonomous_action_taken=False,
                disclaimer="Manual review required due to unavailable signals.",
                counterfactual_context=counterfactual_context,
            )

        # Non-null values safe to unpack
        p_calib = round(float(calibrated_risk_score), 4)
        ev = round(float(expected_value), 2)
        prio = round(float(priority_score), 4)
        anom = round(float(systemic_anomaly_score), 4)
        unc = round(float(investigative_uncertainty), 4)
        confidence = round(max(0.0, min(1.0, 1.0 - unc)), 4)

        # ----------------------------------------------------------------------
        # RULE 1: REQUEST_VERIFICATION (Precedence 2)
        # investigative_uncertainty > 0.40 OR conflicting evidence present
        # ----------------------------------------------------------------------
        if unc > 0.40 or has_conflicting_evidence:
            conflict_str = "Conflicting evidence detected during structural investigation" if has_conflicting_evidence else "Investigative uncertainty is elevated"
            return PolicyDecision(
                transaction_id=transaction_id,
                account_id=account_id,
                timestamp=timestamp,
                calibrated_risk_score=p_calib,
                expected_value=ev,
                priority_score=prio,
                systemic_anomaly_score=anom,
                investigative_uncertainty=unc,
                evidence_domains=evidence_domains,
                evidence_count=evidence_count,
                corroborated_structural_domains=corroborated_structural_domains,
                has_conflicting_evidence=has_conflicting_evidence,
                recommended_action=PolicyAction.REQUEST_VERIFICATION,
                action_priority=ActionPriority.HIGH,
                policy_rule_id="POLICY_RULE_1_REQUEST_VERIFICATION",
                policy_version=POLICY_VERSION,
                policy_reason=f"{conflict_str} (uncertainty={unc:.4f}, conflicting={has_conflicting_evidence}); customer and entity verification required before clearance.",
                required_human_role=HumanReviewRole.FRAUD_INVESTIGATOR,
                required_verification="Perform customer verification and review contradictory signals across data sources before making a risk determination.",
                supporting_evidence_ids=supporting_evidence_ids,
                blocking_conditions=["Uncertainty exceeds operational threshold (>0.40)" if unc > 0.40 else "Contradictory structural evidence uncovered"],
                confidence=confidence,
                human_approval_required=True,
                execution_status="NOT_EXECUTED",
                autonomous_action_taken=False,
                disclaimer="Verification recommendation -- no automated customer contact executed.",
                counterfactual_context=counterfactual_context,
            )

        # ----------------------------------------------------------------------
        # RULE 2: ESCALATE (Precedence 3)
        # calibrated_risk >= 0.85 AND domains >= 2 AND anomaly >= 0.35 AND ev > 0
        # ----------------------------------------------------------------------
        if p_calib >= 0.85 and corroborated_structural_domains >= 2 and anom >= 0.35 and ev > 0:
            domains_str = ", ".join(evidence_domains) if evidence_domains else "multiple"
            return PolicyDecision(
                transaction_id=transaction_id,
                account_id=account_id,
                timestamp=timestamp,
                calibrated_risk_score=p_calib,
                expected_value=ev,
                priority_score=prio,
                systemic_anomaly_score=anom,
                investigative_uncertainty=unc,
                evidence_domains=evidence_domains,
                evidence_count=evidence_count,
                corroborated_structural_domains=corroborated_structural_domains,
                has_conflicting_evidence=has_conflicting_evidence,
                recommended_action=PolicyAction.ESCALATE,
                action_priority=ActionPriority.CRITICAL,
                policy_rule_id="POLICY_RULE_2_ESCALATE",
                policy_version=POLICY_VERSION,
                policy_reason=(
                    f"Critical calibrated risk ({p_calib:.4f} >= 0.85) corroborated by {corroborated_structural_domains} "
                    f"structural evidence domains ({domains_str}), elevated systemic anomaly ({anom:.4f} >= 0.35), "
                    f"and positive net expected value (INR {ev:.2f} > 0)."
                ),
                required_human_role=HumanReviewRole.SENIOR_RISK_ANALYST,
                required_verification="Escalate to senior risk management. Review multi-entity network linkages, infrastructure anomalies, and fund flow before taking manual protective action.",
                supporting_evidence_ids=supporting_evidence_ids,
                blocking_conditions=[
                    "Critical calibrated risk exceeds 0.85",
                    f"Corroborated structural domains ({corroborated_structural_domains}) >= 2",
                    "Elevated systemic anomaly index",
                ],
                confidence=confidence,
                human_approval_required=True,
                execution_status="NOT_EXECUTED",
                autonomous_action_taken=False,
                disclaimer="Escalation recommendation -- no autonomous enforcement executed.",
                counterfactual_context=counterfactual_context,
            )

        # ----------------------------------------------------------------------
        # RULE 3: HOLD_FOR_REVIEW (Precedence 4)
        # calibrated_risk >= 0.70 AND ev > 0 AND domains >= 1 AND uncertainty <= 0.40
        # ----------------------------------------------------------------------
        if p_calib >= 0.70 and ev > 0 and corroborated_structural_domains >= 1 and unc <= 0.40:
            domains_str = ", ".join(evidence_domains) if evidence_domains else "structural"
            return PolicyDecision(
                transaction_id=transaction_id,
                account_id=account_id,
                timestamp=timestamp,
                calibrated_risk_score=p_calib,
                expected_value=ev,
                priority_score=prio,
                systemic_anomaly_score=anom,
                investigative_uncertainty=unc,
                evidence_domains=evidence_domains,
                evidence_count=evidence_count,
                corroborated_structural_domains=corroborated_structural_domains,
                has_conflicting_evidence=has_conflicting_evidence,
                recommended_action=PolicyAction.HOLD_FOR_REVIEW,
                action_priority=ActionPriority.MEDIUM_HIGH,
                policy_rule_id="POLICY_RULE_3_HOLD_FOR_REVIEW",
                policy_version=POLICY_VERSION,
                policy_reason=(
                    f"High calibrated risk ({p_calib:.4f} >= 0.70) with positive expected value (INR {ev:.2f} > 0), "
                    f"corroborated structural evidence ({domains_str}), and acceptable uncertainty ({unc:.4f} <= 0.40)."
                ),
                required_human_role=HumanReviewRole.RISK_ANALYST,
                required_verification="Queue case for human review. Verify beneficiary details, transaction history, and account profile.",
                supporting_evidence_ids=supporting_evidence_ids,
                blocking_conditions=[
                    "High calibrated risk exceeds 0.70",
                    "Positive expected value justifies human review queue placement",
                ],
                confidence=confidence,
                human_approval_required=True,
                execution_status="NOT_EXECUTED",
                autonomous_action_taken=False,
                disclaimer="Human review queue recommendation -- no transaction hold executed.",
                counterfactual_context=counterfactual_context,
            )

        # ----------------------------------------------------------------------
        # RULE 4: MONITOR (Precedence 5)
        # calibrated_risk >= 0.20 (did not meet ESCALATE or HOLD_FOR_REVIEW)
        # OR: low risk (<0.20) but systemic anomaly >= 0.35 or uncertainty > 0.12 or structural evidence
        # ----------------------------------------------------------------------
        is_elevated_risk = (p_calib >= 0.20)
        is_elevated_context = (p_calib < 0.20 and (anom >= 0.35 or unc > 0.12 or corroborated_structural_domains > 0))

        if is_elevated_risk or is_elevated_context:
            reason = (
                f"Elevated or moderate calibrated risk ({p_calib:.4f} >= 0.20) warrants analytical observation."
                if is_elevated_risk
                else f"Low risk ({p_calib:.4f}) with elevated background context (anomaly={anom:.4f}, uncertainty={unc:.4f}, structural_domains={corroborated_structural_domains}) warrants observation."
            )
            return PolicyDecision(
                transaction_id=transaction_id,
                account_id=account_id,
                timestamp=timestamp,
                calibrated_risk_score=p_calib,
                expected_value=ev,
                priority_score=prio,
                systemic_anomaly_score=anom,
                investigative_uncertainty=unc,
                evidence_domains=evidence_domains,
                evidence_count=evidence_count,
                corroborated_structural_domains=corroborated_structural_domains,
                has_conflicting_evidence=has_conflicting_evidence,
                recommended_action=PolicyAction.MONITOR,
                action_priority=ActionPriority.LOW_MEDIUM,
                policy_rule_id="POLICY_RULE_4_MONITOR",
                policy_version=POLICY_VERSION,
                policy_reason=reason,
                required_human_role=HumanReviewRole.AUTOMATED_TELEMETRY_ANALYST,
                required_verification="Analytical observation only. Add account and transaction pattern to automated telemetry watchlist.",
                supporting_evidence_ids=supporting_evidence_ids,
                blocking_conditions=["Telemetry monitoring active for background signal tracking"],
                confidence=confidence,
                human_approval_required=True,
                execution_status="NOT_EXECUTED",
                autonomous_action_taken=False,
                disclaimer="Telemetry observation recommendation -- no automated account action executed.",
                counterfactual_context=counterfactual_context,
            )

        # ----------------------------------------------------------------------
        # RULE 5: ALLOW (Precedence 6)
        # calibrated_risk < 0.20 AND uncertainty <= 0.12 AND domains == 0 AND anomaly < 0.35
        # ----------------------------------------------------------------------
        if p_calib < 0.20 and unc <= 0.12 and corroborated_structural_domains == 0 and anom < 0.35:
            return PolicyDecision(
                transaction_id=transaction_id,
                account_id=account_id,
                timestamp=timestamp,
                calibrated_risk_score=p_calib,
                expected_value=ev,
                priority_score=prio,
                systemic_anomaly_score=anom,
                investigative_uncertainty=unc,
                evidence_domains=[],
                evidence_count=evidence_count,
                corroborated_structural_domains=0,
                has_conflicting_evidence=False,
                recommended_action=PolicyAction.ALLOW,
                action_priority=ActionPriority.LOW,
                policy_rule_id="POLICY_RULE_5_ALLOW",
                policy_version=POLICY_VERSION,
                policy_reason=(
                    f"Low calibrated risk ({p_calib:.4f} < 0.20) with fully resolved uncertainty ({unc:.4f} <= 0.12), "
                    f"zero structural evidence, and low systemic anomaly ({anom:.4f} < 0.35)."
                ),
                required_human_role=HumanReviewRole.NONE,
                required_verification="None. Transaction risk is within acceptable operational tolerance.",
                supporting_evidence_ids=[],
                blocking_conditions=[],
                confidence=confidence,
                human_approval_required=True,
                execution_status="NOT_EXECUTED",
                autonomous_action_taken=False,
                disclaimer="Analytical recommendation only -- no payment approval executed.",
                counterfactual_context=counterfactual_context,
            )

        # ----------------------------------------------------------------------
        # Default Fallback (Precedence 1 Fallthrough Safety)
        # ----------------------------------------------------------------------
        return PolicyDecision(
            transaction_id=transaction_id,
            account_id=account_id,
            timestamp=timestamp,
            calibrated_risk_score=p_calib,
            expected_value=ev,
            priority_score=prio,
            systemic_anomaly_score=anom,
            investigative_uncertainty=unc,
            evidence_domains=evidence_domains,
            evidence_count=evidence_count,
            corroborated_structural_domains=corroborated_structural_domains,
            has_conflicting_evidence=has_conflicting_evidence,
            recommended_action=PolicyAction.FALLBACK_REVIEW,
            action_priority=ActionPriority.MEDIUM,
            policy_rule_id="POLICY_RULE_0_FALLBACK_REVIEW",
            policy_version=POLICY_VERSION,
            policy_reason="Case signals did not meet criteria for clear ALLOW or standard escalation; routed to review fallback.",
            required_human_role=HumanReviewRole.RISK_ANALYST,
            required_verification="Conduct standard manual case review.",
            supporting_evidence_ids=supporting_evidence_ids,
            blocking_conditions=["Signal combination does not meet definitive clearance criteria"],
            confidence=confidence,
            human_approval_required=True,
            execution_status="NOT_EXECUTED",
            autonomous_action_taken=False,
            disclaimer="Manual review required due to unavailable signals.",
            counterfactual_context=counterfactual_context,
        )

    def evaluate_transaction(self, transaction_id: str) -> PolicyDecision:
        """Evaluate a real transaction in the database by orchestrating existing services."""
        clean_id = transaction_id.strip().upper()
        tx = self.db.query(Transaction).filter(Transaction.transaction_id == clean_id).first()
        if not tx:
            raise KeyError(f"Transaction '{transaction_id}' not found in database.")

        account_id = tx.account_id
        timestamp_iso = tx.timestamp.isoformat()

        # 1. Stage 16 Portfolio Prioritization & Expected Value
        try:
            prio_res = self.prioritization_service.prioritize_transaction(clean_id)
            calibrated_risk = prio_res.risk_score
            expected_value = prio_res.expected_value
            priority_score = prio_res.priority_score
            # Stage 16 prio_res ALREADY computes Stage 15 systemic_anomaly_score!
            systemic_anomaly = prio_res.systemic_anomaly_score
        except Exception:
            calibrated_risk = None
            expected_value = None
            priority_score = None
            systemic_anomaly = None

        # 2. Stage 15 Systemic Anomaly Score fallback (only if prio_res did not provide it)
        if systemic_anomaly is None:
            try:
                anom_res = self.anomaly_service.analyze_transaction(clean_id)
                systemic_anomaly = anom_res.systemic_anomaly_score
            except Exception:
                systemic_anomaly = None

        # 3. Stage 17 Adaptive Investigation & Uncertainty
        try:
            adapt_res = self.adaptive_engine.run_investigation(clean_id, include_context=False)
            uncertainty = adapt_res.final_uncertainty
            has_conflicting = (
                adapt_res.stopping_reason == "CONFLICTING_EVIDENCE"
                or any(
                    getattr(s, "evidence_quality", None) == "CONFLICTING"
                    or (hasattr(getattr(s, "evidence_quality", None), "value") and s.evidence_quality.value == "CONFLICTING")
                    for s in adapt_res.steps
                )
            )
            
            # Extract corroborated structural evidence domains from adaptive steps
            domains: Set[str] = set()
            for step in adapt_res.steps:
                if step.evidence_count > 0:
                    if "device" in step.tool_name:
                        domains.add("DEVICE")
                    elif "ip" in step.tool_name:
                        domains.add("IP")
                    elif "beneficiary" in step.tool_name:
                        domains.add("BENEFICIARY")
                    elif "account" in step.tool_name:
                        domains.add("ACCOUNT_NETWORK")
                    elif "fund_flow" in step.tool_name:
                        domains.add("FUND_FLOW")
                    elif "timeline" in step.tool_name or "transaction" in step.tool_name:
                        domains.add("TIMELINE")

            # Check Stage 9 verified evidence items only if steps had no domains
            if not domains and adapt_res.evidence_ids:
                ev_items = self.evidence_engine.extract_evidence_for_transaction(clean_id).items
                for e in ev_items:
                    t = e.evidence_type.value if hasattr(e.evidence_type, "value") else str(e.evidence_type)
                    if "DEVICE" in t:
                        domains.add("DEVICE")
                    elif "IP" in t:
                        domains.add("IP")
                    elif "BENEFICIARY" in t:
                        domains.add("BENEFICIARY")
                    elif "MULTI_HOP" in t or "ACCOUNT" in t:
                        domains.add("ACCOUNT_NETWORK")
                    elif "FUND_FLOW" in t or "RAPID" in t:
                        domains.add("FUND_FLOW")

            evidence_domains = sorted(list(domains))
            evidence_count = len(adapt_res.evidence_ids)
            supporting_evidence_ids = adapt_res.evidence_ids
        except Exception as e:
            uncertainty = None
            has_conflicting = False
            evidence_domains = []
            evidence_count = 0
            supporting_evidence_ids = []

        # 4. Stage 18 Counterfactual Attribution context (direct TreeSHAP)
        counterfactual_context = None
        try:
            attributions, raw_p, calib_p, _, _ = self.cf_service.compute_attributions(clean_id)
            if attributions:
                strongest = attributions[0]
                counterfactual_context = {
                    "strongest_driver": strongest.feature_name,
                    "driver_contribution": strongest.contribution,
                    "driver_direction": strongest.direction.value,
                    "largest_reduction_delta": 0.0,
                }
        except Exception:
            counterfactual_context = None

        return self.evaluate_signals(
            transaction_id=clean_id,
            account_id=account_id,
            timestamp=timestamp_iso,
            calibrated_risk_score=calibrated_risk,
            expected_value=expected_value,
            priority_score=priority_score,
            systemic_anomaly_score=systemic_anomaly,
            investigative_uncertainty=uncertainty,
            evidence_domains=evidence_domains,
            evidence_count=evidence_count,
            has_conflicting_evidence=has_conflicting,
            supporting_evidence_ids=supporting_evidence_ids,
            counterfactual_context=counterfactual_context,
        )
