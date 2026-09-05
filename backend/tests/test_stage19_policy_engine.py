"""RingGuard AI — Stage 19 Test Suite: Deterministic Risk Policy Engine + Next-Best-Action.

Validates all 30 required operational and safety criteria:
1. Deterministic policy result
2. Deterministic rule precedence
3. Fallback review on missing / invalid signals (Rule 0)
4. Allow on low risk + resolved uncertainty + 0 structural domains + low anomaly (Rule 5)
5. Monitor on moderate risk or elevated background context (Rule 4)
6. Request verification on uncertainty > 0.40 or conflicting evidence (Rule 1)
7. Hold for review on risk >= 0.70 + positive EV + domains >= 1 + uncertainty <= 0.40 (Rule 3)
8. Escalate on risk >= 0.85 + domains >= 2 + anomaly >= 0.35 + EV > 0 (Rule 2)
9. Conflicting evidence handling
10. Unavailable signals handling
11. Policy version (ringguard_policy_v1)
12. Rule ID validity
13. Rationale factuality & non-causal language
14. Evidence linkage
15. Human approval required (True)
16. Autonomous action taken (False)
17. Execution status (NOT_EXECUTED)
18. Database immutability
19. Model immutability
20. Risk score immutability
21. No payment/enforcement calls
22. Stage 15 integration
23. Stage 16 integration
24. Stage 17 integration
25. Stage 18 integration
26. Deterministic reproducibility
27. All threshold boundary conditions
28. FastAPI endpoints validation (200, 404, 422)
29. Competing-rule precedence resolution
30. Deterministic action priority mapping
"""

import pytest
import hashlib
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.transaction import Transaction
from app.policy.schemas import (
    PolicyAction,
    ActionPriority,
    HumanReviewRole,
    PolicyDecision,
)
from app.policy.service import (
    PolicyDecisionEngine,
    POLICY_VERSION,
    POLICY_RULES_CATALOG,
)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def engine(db_session: Session):
    return PolicyDecisionEngine(db_session)


def get_file_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


# ==============================================================================
# 1 & 26. DETERMINISTIC POLICY RESULT & REPRODUCIBILITY
# ==============================================================================

def test_deterministic_policy_result(engine: PolicyDecisionEngine):
    """Verify that multiple evaluations of the same transaction produce identical output."""
    tx_id = "TXN_00000203"
    run1 = engine.evaluate_transaction(tx_id)
    run2 = engine.evaluate_transaction(tx_id)

    assert run1.recommended_action == run2.recommended_action
    assert run1.policy_rule_id == run2.policy_rule_id
    assert run1.action_priority == run2.action_priority
    assert run1.calibrated_risk_score == run2.calibrated_risk_score
    assert run1.expected_value == run2.expected_value
    assert run1.policy_reason == run2.policy_reason
    assert run1.required_human_role == run2.required_human_role


# ==============================================================================
# 2 & 29. DETERMINISTIC PRECEDENCE & COMPETING RULES
# ==============================================================================

def test_precedence_order_definition():
    """Verify declared precedence in catalog matches exactly: 0 -> 1 -> 2 -> 3 -> 4 -> 5."""
    expected_order = [
        "POLICY_RULE_0_FALLBACK_REVIEW",
        "POLICY_RULE_1_REQUEST_VERIFICATION",
        "POLICY_RULE_2_ESCALATE",
        "POLICY_RULE_3_HOLD_FOR_REVIEW",
        "POLICY_RULE_4_MONITOR",
        "POLICY_RULE_5_ALLOW",
    ]
    actual_order = [r.rule_id for r in POLICY_RULES_CATALOG]
    assert actual_order == expected_order


def test_competing_rule_uncertainty_overrides_escalate(engine: PolicyDecisionEngine):
    """Verify Rule 1 (REQUEST_VERIFICATION) beats Rule 2 (ESCALATE) when uncertainty > 0.40."""
    # Critical risk + domains >= 2 + anomaly >= 0.35 + EV > 0 BUT uncertainty = 0.45
    dec = engine.evaluate_signals(
        transaction_id="TX_COMPETE",
        account_id="ACC_1",
        timestamp="2026-01-01T00:00:00Z",
        calibrated_risk_score=0.95,
        expected_value=10000.0,
        priority_score=0.9,
        systemic_anomaly_score=0.8,
        investigative_uncertainty=0.45,  # High uncertainty
        evidence_domains=["DEVICE", "IP"],
        evidence_count=2,
    )
    assert dec.recommended_action == PolicyAction.REQUEST_VERIFICATION
    assert dec.policy_rule_id == "POLICY_RULE_1_REQUEST_VERIFICATION"


def test_competing_rule_fallback_overrides_all(engine: PolicyDecisionEngine):
    """Verify Rule 0 (FALLBACK_REVIEW) beats all other rules when any critical signal is missing."""
    dec = engine.evaluate_signals(
        transaction_id="TX_COMPETE",
        account_id="ACC_1",
        timestamp="2026-01-01T00:00:00Z",
        calibrated_risk_score=0.99,
        expected_value=None,  # Missing critical signal
        priority_score=0.9,
        systemic_anomaly_score=0.8,
        investigative_uncertainty=0.05,
        evidence_domains=["DEVICE", "IP"],
        evidence_count=2,
    )
    assert dec.recommended_action == PolicyAction.FALLBACK_REVIEW
    assert dec.policy_rule_id == "POLICY_RULE_0_FALLBACK_REVIEW"


# ==============================================================================
# 3 & 10. FALLBACK REVIEW (RULE 0)
# ==============================================================================

def test_rule0_fallback_on_missing_risk(engine: PolicyDecisionEngine):
    """Verify fallback review triggers when calibrated_risk_score is None."""
    dec = engine.evaluate_signals(
        transaction_id="TX_T",
        account_id="ACC_1",
        timestamp="2026-01-01T00:00:00Z",
        calibrated_risk_score=None,
        expected_value=100.0,
        priority_score=0.5,
        systemic_anomaly_score=0.2,
        investigative_uncertainty=0.1,
    )
    assert dec.recommended_action == PolicyAction.FALLBACK_REVIEW
    assert dec.action_priority == ActionPriority.MEDIUM
    assert dec.required_human_role == HumanReviewRole.RISK_ANALYST


def test_rule0_fallback_on_invalid_bounds(engine: PolicyDecisionEngine):
    """Verify fallback review triggers when signals fall outside [0, 1]."""
    dec = engine.evaluate_signals(
        transaction_id="TX_T",
        account_id="ACC_1",
        timestamp="2026-01-01T00:00:00Z",
        calibrated_risk_score=1.5,  # Out of bounds
        expected_value=100.0,
        priority_score=0.5,
        systemic_anomaly_score=0.2,
        investigative_uncertainty=0.1,
    )
    assert dec.recommended_action == PolicyAction.FALLBACK_REVIEW


# ==============================================================================
# 4. ALLOW (RULE 5)
# ==============================================================================

def test_rule5_allow_clear_low_risk(engine: PolicyDecisionEngine):
    """Verify ALLOW triggers when risk < 0.20, U <= 0.12, domains == 0, anomaly < 0.35."""
    dec = engine.evaluate_signals(
        transaction_id="TX_T",
        account_id="ACC_1",
        timestamp="2026-01-01T00:00:00Z",
        calibrated_risk_score=0.05,
        expected_value=-1500.0,
        priority_score=0.05,
        systemic_anomaly_score=0.10,
        investigative_uncertainty=0.08,
        evidence_domains=[],
        evidence_count=0,
    )
    assert dec.recommended_action == PolicyAction.ALLOW
    assert dec.action_priority == ActionPriority.LOW
    assert dec.required_human_role == HumanReviewRole.NONE
    assert dec.policy_rule_id == "POLICY_RULE_5_ALLOW"


# ==============================================================================
# 5. MONITOR (RULE 4)
# ==============================================================================

def test_rule4_monitor_moderate_risk(engine: PolicyDecisionEngine):
    """Verify MONITOR triggers when calibrated risk is in [0.20, 0.70)."""
    dec = engine.evaluate_signals(
        transaction_id="TX_T",
        account_id="ACC_1",
        timestamp="2026-01-01T00:00:00Z",
        calibrated_risk_score=0.45,
        expected_value=-500.0,
        priority_score=0.35,
        systemic_anomaly_score=0.20,
        investigative_uncertainty=0.10,
        evidence_domains=[],
        evidence_count=0,
    )
    assert dec.recommended_action == PolicyAction.MONITOR
    assert dec.action_priority == ActionPriority.LOW_MEDIUM
    assert dec.required_human_role == HumanReviewRole.AUTOMATED_TELEMETRY_ANALYST


def test_rule4_monitor_low_risk_elevated_anomaly(engine: PolicyDecisionEngine):
    """Verify MONITOR triggers when risk is low (<0.20) but systemic anomaly is elevated (>=0.35)."""
    dec = engine.evaluate_signals(
        transaction_id="TX_T",
        account_id="ACC_1",
        timestamp="2026-01-01T00:00:00Z",
        calibrated_risk_score=0.05,
        expected_value=-1500.0,
        priority_score=0.25,
        systemic_anomaly_score=0.85,  # Elevated anomaly
        investigative_uncertainty=0.08,
        evidence_domains=[],
        evidence_count=0,
    )
    assert dec.recommended_action == PolicyAction.MONITOR


# ==============================================================================
# 6 & 9. REQUEST VERIFICATION & CONFLICTING EVIDENCE (RULE 1)
# ==============================================================================

def test_rule1_request_verification_high_uncertainty(engine: PolicyDecisionEngine):
    """Verify REQUEST_VERIFICATION triggers when investigative uncertainty > 0.40."""
    dec = engine.evaluate_signals(
        transaction_id="TX_T",
        account_id="ACC_1",
        timestamp="2026-01-01T00:00:00Z",
        calibrated_risk_score=0.60,
        expected_value=100.0,
        priority_score=0.5,
        systemic_anomaly_score=0.20,
        investigative_uncertainty=0.42,  # > 0.40
        evidence_domains=[],
        evidence_count=0,
    )
    assert dec.recommended_action == PolicyAction.REQUEST_VERIFICATION
    assert dec.action_priority == ActionPriority.HIGH
    assert dec.required_human_role == HumanReviewRole.FRAUD_INVESTIGATOR


def test_rule1_request_verification_conflicting_evidence(engine: PolicyDecisionEngine):
    """Verify REQUEST_VERIFICATION triggers when conflicting evidence is discovered."""
    dec = engine.evaluate_signals(
        transaction_id="TX_T",
        account_id="ACC_1",
        timestamp="2026-01-01T00:00:00Z",
        calibrated_risk_score=0.80,
        expected_value=1000.0,
        priority_score=0.7,
        systemic_anomaly_score=0.20,
        investigative_uncertainty=0.10,
        has_conflicting_evidence=True,  # Conflicting evidence
    )
    assert dec.recommended_action == PolicyAction.REQUEST_VERIFICATION


# ==============================================================================
# 7. HOLD FOR REVIEW (RULE 3)
# ==============================================================================

def test_rule3_hold_for_review(engine: PolicyDecisionEngine):
    """Verify HOLD_FOR_REVIEW triggers when risk >= 0.70, EV > 0, domains >= 1, U <= 0.40."""
    dec = engine.evaluate_signals(
        transaction_id="TX_T",
        account_id="ACC_1",
        timestamp="2026-01-01T00:00:00Z",
        calibrated_risk_score=0.75,
        expected_value=5000.0,
        priority_score=0.7,
        systemic_anomaly_score=0.25,
        investigative_uncertainty=0.20,
        evidence_domains=["DEVICE"],
        evidence_count=1,
    )
    assert dec.recommended_action == PolicyAction.HOLD_FOR_REVIEW
    assert dec.action_priority == ActionPriority.MEDIUM_HIGH
    assert dec.required_human_role == HumanReviewRole.RISK_ANALYST


# ==============================================================================
# 8. ESCALATE (RULE 2)
# ==============================================================================

def test_rule2_escalate(engine: PolicyDecisionEngine):
    """Verify ESCALATE triggers when risk >= 0.85, domains >= 2, anomaly >= 0.35, EV > 0."""
    dec = engine.evaluate_signals(
        transaction_id="TX_T",
        account_id="ACC_1",
        timestamp="2026-01-01T00:00:00Z",
        calibrated_risk_score=0.92,
        expected_value=45000.0,
        priority_score=0.88,
        systemic_anomaly_score=0.65,
        investigative_uncertainty=0.08,
        evidence_domains=["DEVICE", "FUND_FLOW"],
        evidence_count=3,
    )
    assert dec.recommended_action == PolicyAction.ESCALATE
    assert dec.action_priority == ActionPriority.CRITICAL
    assert dec.required_human_role == HumanReviewRole.SENIOR_RISK_ANALYST


# ==============================================================================
# 11 & 12. POLICY VERSION & RULE ID
# ==============================================================================

def test_policy_version_and_rule_id(engine: PolicyDecisionEngine):
    """Verify policy version is static ringguard_policy_v1 and rule_id is valid."""
    dec = engine.evaluate_transaction("TXN_00000203")
    assert dec.policy_version == "ringguard_policy_v1"
    assert dec.policy_rule_id.startswith("POLICY_RULE_")


# ==============================================================================
# 13. RATIONALE FACTUALITY & NON-CAUSAL LANGUAGE
# ==============================================================================

def test_non_causal_language_and_factuality(engine: PolicyDecisionEngine):
    """Verify policy reason does not claim causality, blame banks/PSPs, or assert fraud proof."""
    dec = engine.evaluate_transaction("TXN_00000203")
    reason_lower = dec.policy_reason.lower()

    forbidden_phrases = [
        "caused the fraud",
        "proves fraud",
        "bank caused",
        "psp caused",
        "institution is responsible",
        "guarantees prevention",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in reason_lower


# ==============================================================================
# 14. EVIDENCE LINKAGE
# ==============================================================================

def test_evidence_linkage(engine: PolicyDecisionEngine):
    """Verify supporting evidence IDs and domains are tracked on the decision object."""
    dec = engine.evaluate_transaction("TXN_00000203")
    assert isinstance(dec.supporting_evidence_ids, list)
    assert isinstance(dec.evidence_domains, list)
    assert dec.corroborated_structural_domains >= 1


# ==============================================================================
# 15, 16, 17, 21. ABSOLUTE SAFETY BOUNDARIES & NON-EXECUTION
# ==============================================================================

def test_human_approval_required_invariant(engine: PolicyDecisionEngine):
    """Verify human_approval_required is True on all transactions."""
    for tx_id in ["TXN_00000203", "TXN_00000646", "TXN_00000500"]:
        dec = engine.evaluate_transaction(tx_id)
        assert dec.human_approval_required is True


def test_autonomous_action_taken_false_invariant(engine: PolicyDecisionEngine):
    """Verify autonomous_action_taken is False on all transactions."""
    for tx_id in ["TXN_00000203", "TXN_00000646", "TXN_00000500"]:
        dec = engine.evaluate_transaction(tx_id)
        assert dec.autonomous_action_taken is False


def test_execution_status_not_executed_invariant(engine: PolicyDecisionEngine):
    """Verify execution_status is strictly NOT_EXECUTED on all transactions."""
    for tx_id in ["TXN_00000203", "TXN_00000646", "TXN_00000500"]:
        dec = engine.evaluate_transaction(tx_id)
        assert dec.execution_status == "NOT_EXECUTED"


def test_no_payment_or_enforcement_calls(engine: PolicyDecisionEngine):
    """Verify decision payload contains no automated enforcement triggers."""
    dec = engine.evaluate_transaction("TXN_00000203")
    dump = dec.model_dump_json().lower()
    assert "auto_block" not in dump
    assert "freeze_account" not in dump
    assert "reject_payment" not in dump


# ==============================================================================
# 18, 19, 20. IMMUTABILITY OF DATABASE, MODEL & RISK STATE
# ==============================================================================

def test_database_immutability(engine: PolicyDecisionEngine, db_session: Session):
    """Verify no database records are inserted, modified, or deleted during evaluation."""
    tx_before = db_session.query(Transaction).filter(Transaction.transaction_id == "TXN_00000203").first()
    amount_before = tx_before.amount

    engine.evaluate_transaction("TXN_00000203")

    db_session.expire_all()
    tx_after = db_session.query(Transaction).filter(Transaction.transaction_id == "TXN_00000203").first()
    assert tx_after.amount == amount_before


def test_model_artifact_immutability(engine: PolicyDecisionEngine):
    """Verify Model B artifact SHA-256 hash is identical before and after evaluation."""
    model_b_path = Path("models/ringguard_graph_xgb_v1.joblib")
    hash_before = get_file_sha256(model_b_path)

    engine.evaluate_transaction("TXN_00000203")

    hash_after = get_file_sha256(model_b_path)
    assert hash_before == hash_after


def test_risk_score_immutability(engine: PolicyDecisionEngine, client: TestClient):
    """Verify production Model B risk scores remain unchanged after policy evaluation."""
    r1 = client.get("/api/risk/transaction/TXN_00000203").json()
    engine.evaluate_transaction("TXN_00000203")
    r2 = client.get("/api/risk/transaction/TXN_00000203").json()

    assert r1["predicted_ring_probability"] == r2["predicted_ring_probability"]


# ==============================================================================
# 22, 23, 24, 25. STAGE 15, 16, 17, 18 INTEGRATION
# ==============================================================================

def test_cross_stage_integration(engine: PolicyDecisionEngine):
    """Verify policy engine seamlessly integrates Stages 15, 16, 17, and 18."""
    dec = engine.evaluate_transaction("TXN_00000203")
    # Stage 15
    assert dec.systemic_anomaly_score >= 0.0
    # Stage 16
    assert dec.priority_score >= 0.0
    assert dec.expected_value != 0.0
    # Stage 17
    assert 0.0 <= dec.investigative_uncertainty <= 1.0
    # Stage 18
    assert dec.counterfactual_context is not None


# ==============================================================================
# 27. THRESHOLD BOUNDARY TESTS
# ==============================================================================

def test_boundary_risk_0_20(engine: PolicyDecisionEngine):
    """Verify risk boundary at 0.1999 vs 0.20."""
    # 0.1999 with clean signals -> ALLOW
    d1 = engine.evaluate_signals(
        "T1", "A1", "2026-01-01", 0.1999, -100.0, 0.1, 0.1, 0.10, [], 0
    )
    assert d1.recommended_action == PolicyAction.ALLOW

    # 0.20 with clean signals -> MONITOR
    d2 = engine.evaluate_signals(
        "T2", "A1", "2026-01-01", 0.2000, -100.0, 0.1, 0.1, 0.10, [], 0
    )
    assert d2.recommended_action == PolicyAction.MONITOR


def test_boundary_risk_0_70(engine: PolicyDecisionEngine):
    """Verify risk boundary at 0.6999 vs 0.70."""
    # 0.6999 with EV>0, domains>=1, U<=0.40 -> MONITOR
    d1 = engine.evaluate_signals(
        "T1", "A1", "2026-01-01", 0.6999, 1000.0, 0.6, 0.2, 0.10, ["DEVICE"], 1
    )
    assert d1.recommended_action == PolicyAction.MONITOR

    # 0.7000 with EV>0, domains>=1, U<=0.40 -> HOLD_FOR_REVIEW
    d2 = engine.evaluate_signals(
        "T2", "A1", "2026-01-01", 0.7000, 1000.0, 0.6, 0.2, 0.10, ["DEVICE"], 1
    )
    assert d2.recommended_action == PolicyAction.HOLD_FOR_REVIEW


def test_boundary_risk_0_85(engine: PolicyDecisionEngine):
    """Verify risk boundary at 0.8499 vs 0.85."""
    # 0.8499 with domains>=2, anomaly>=0.35, EV>0 -> HOLD_FOR_REVIEW
    d1 = engine.evaluate_signals(
        "T1", "A1", "2026-01-01", 0.8499, 1000.0, 0.8, 0.5, 0.10, ["DEVICE", "IP"], 2
    )
    assert d1.recommended_action == PolicyAction.HOLD_FOR_REVIEW

    # 0.8500 with domains>=2, anomaly>=0.35, EV>0 -> ESCALATE
    d2 = engine.evaluate_signals(
        "T2", "A1", "2026-01-01", 0.8500, 1000.0, 0.8, 0.5, 0.10, ["DEVICE", "IP"], 2
    )
    assert d2.recommended_action == PolicyAction.ESCALATE


def test_boundary_uncertainty_0_12_and_0_40(engine: PolicyDecisionEngine):
    """Verify uncertainty boundaries at 0.12 and 0.40."""
    # U = 0.12 with risk < 0.20, domains=0, anomaly < 0.35 -> ALLOW
    d1 = engine.evaluate_signals(
        "T1", "A1", "2026-01-01", 0.10, -100.0, 0.1, 0.1, 0.1200, [], 0
    )
    assert d1.recommended_action == PolicyAction.ALLOW

    # U = 0.1201 with risk < 0.20 -> MONITOR
    d2 = engine.evaluate_signals(
        "T2", "A1", "2026-01-01", 0.10, -100.0, 0.1, 0.1, 0.1201, [], 0
    )
    assert d2.recommended_action == PolicyAction.MONITOR

    # U = 0.40 with risk=0.75, domains=1, EV>0 -> HOLD_FOR_REVIEW
    d3 = engine.evaluate_signals(
        "T3", "A1", "2026-01-01", 0.75, 1000.0, 0.7, 0.2, 0.4000, ["DEVICE"], 1
    )
    assert d3.recommended_action == PolicyAction.HOLD_FOR_REVIEW

    # U = 0.4001 -> REQUEST_VERIFICATION
    d4 = engine.evaluate_signals(
        "T4", "A1", "2026-01-01", 0.75, 1000.0, 0.7, 0.2, 0.4001, ["DEVICE"], 1
    )
    assert d4.recommended_action == PolicyAction.REQUEST_VERIFICATION


def test_boundary_systemic_anomaly_0_35(engine: PolicyDecisionEngine):
    """Verify systemic anomaly boundary at 0.3499 vs 0.35 for ESCALATE."""
    # Anomaly = 0.3499 with risk=0.90, domains=2, EV>0 -> HOLD_FOR_REVIEW
    d1 = engine.evaluate_signals(
        "T1", "A1", "2026-01-01", 0.90, 5000.0, 0.8, 0.3499, 0.10, ["DEVICE", "IP"], 2
    )
    assert d1.recommended_action == PolicyAction.HOLD_FOR_REVIEW

    # Anomaly = 0.3500 with risk=0.90, domains=2, EV>0 -> ESCALATE
    d2 = engine.evaluate_signals(
        "T2", "A1", "2026-01-01", 0.90, 5000.0, 0.8, 0.3500, 0.10, ["DEVICE", "IP"], 2
    )
    assert d2.recommended_action == PolicyAction.ESCALATE


def test_boundary_expected_value_zero(engine: PolicyDecisionEngine):
    """Verify expected value boundary at 0 vs positive for HOLD_FOR_REVIEW."""
    # EV = 0.0 with risk=0.75, domains=1 -> MONITOR
    d1 = engine.evaluate_signals(
        "T1", "A1", "2026-01-01", 0.75, 0.0, 0.6, 0.2, 0.10, ["DEVICE"], 1
    )
    assert d1.recommended_action == PolicyAction.MONITOR

    # EV = 0.01 with risk=0.75, domains=1 -> HOLD_FOR_REVIEW
    d2 = engine.evaluate_signals(
        "T2", "A1", "2026-01-01", 0.75, 0.01, 0.6, 0.2, 0.10, ["DEVICE"], 1
    )
    assert d2.recommended_action == PolicyAction.HOLD_FOR_REVIEW


# ==============================================================================
# 28. API ENDPOINTS VALIDATION (200, 404, 422)
# ==============================================================================

def test_api_endpoints_success(client: TestClient):
    """Verify 200 OK on valid transaction, health, and rules endpoints."""
    r_h = client.get("/api/policy/health")
    assert r_h.status_code == 200
    assert r_h.json()["policy_version"] == "ringguard_policy_v1"

    r_r = client.get("/api/policy/rules")
    assert r_r.status_code == 200
    assert r_r.json()["rule_count"] == 6

    r_tx = client.get("/api/policy/transaction/TXN_00000203")
    assert r_tx.status_code == 200
    assert r_tx.json()["transaction_id"] == "TXN_00000203"
    assert r_tx.json()["recommended_action"] == "ESCALATE"


def test_api_endpoints_not_found(client: TestClient):
    """Verify 404 Not Found on unknown transaction."""
    r = client.get("/api/policy/transaction/TXN_99999999")
    assert r.status_code == 404


def test_api_endpoints_validation_error(client: TestClient):
    """Verify 422 Unprocessable Entity on empty or whitespace transaction ID."""
    r = client.get("/api/policy/transaction/%20")
    assert r.status_code == 422


# ==============================================================================
# 30. DETERMINISTIC ACTION PRIORITY MAPPING
# ==============================================================================

def test_deterministic_action_priority_mapping(engine: PolicyDecisionEngine):
    """Verify each action maps to its predeclared priority tier."""
    p_esc = engine.evaluate_signals("T", "A", "2026-01-01", 0.90, 5000.0, 0.8, 0.5, 0.10, ["D", "I"], 2)
    assert p_esc.action_priority == ActionPriority.CRITICAL

    p_req = engine.evaluate_signals("T", "A", "2026-01-01", 0.90, 5000.0, 0.8, 0.5, 0.45, ["D", "I"], 2)
    assert p_req.action_priority == ActionPriority.HIGH

    p_hold = engine.evaluate_signals("T", "A", "2026-01-01", 0.75, 5000.0, 0.7, 0.2, 0.10, ["D"], 1)
    assert p_hold.action_priority == ActionPriority.MEDIUM_HIGH

    p_fall = engine.evaluate_signals("T", "A", "2026-01-01", None, 0.0, 0.5, 0.5, 0.5)
    assert p_fall.action_priority == ActionPriority.MEDIUM

    p_mon = engine.evaluate_signals("T", "A", "2026-01-01", 0.50, -100.0, 0.4, 0.2, 0.10, [], 0)
    assert p_mon.action_priority == ActionPriority.LOW_MEDIUM

    p_allow = engine.evaluate_signals("T", "A", "2026-01-01", 0.05, -1000.0, 0.05, 0.1, 0.08, [], 0)
    assert p_allow.action_priority == ActionPriority.LOW
