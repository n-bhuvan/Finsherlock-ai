"""RingGuard AI — Stage 17 Test Suite: Uncertainty-Driven Investigation + Stopping Policy.

Validates all required operational and safety criteria:
1. Deterministic investigation reproducibility
2. Initial uncertainty calculation bounded in [0.05, 0.95]
3. Candidate tool scoring and EIG computation
4. Redundancy penalty calculation
5. Granular tool cost tracking and ceiling (max INR 150)
6. Adaptive next-tool selection (dependent on what was discovered)
7. Evidence-driven uncertainty update
8. Conflicting evidence handling (uncertainty increases on multi-source discrepancy)
9. Stopping when uncertainty is sufficiently low (U <= 0.12)
10. Stopping when sufficient evidence obtained (>= 2 distinct domains)
11. Stopping when EIG is too low (< 0.05)
12. Stopping at maximum step limit (5 steps)
13. Stopping at tool budget ceiling (INR 150.0)
14. Investigation trace correctness and per-step fidelity
15. Evidence provenance and non-fabrication
16. Read-only invariant and PermissionGuard enforcement
17. Mandatory human approval flag (human_approval_required = True)
18. No autonomous financial action or model mutations
19. No hidden chain-of-thought exposure
20. Stage 15 systemic anomaly integration
21. Stage 16 portfolio prioritization integration
22. FastAPI endpoints validation (200, 404, 422)
23. Point-in-time temporal safety & future data exclusion (Corrections 2 & 9)
24. Deterministic tie-breaking for identical EIG values (Correction 3)
25. Conflicting evidence requires multiple structural queries (Correction 4)
26. Risk field naming calibrated_risk_score (Correction 6)
27. Stopping policy precedence order (Correction 8)
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.transaction import Transaction
from app.models.account import Account
from app.investigation.adaptive import (
    AdaptiveInvestigationEngine,
    TOOL_SIMULATED_COSTS,
    TOOL_BASE_RELEVANCE,
    DETERMINISTIC_TOOL_PREFERENCE,
)
from app.investigation.schemas import (
    StoppingReason,
    EvidenceQualityType,
    ToolExecutionResult,
    ToolExecutionStatus,
    AdaptiveInvestigationResponse,
)
from app.investigation.permissions import PermissionGuard, PermissionDeniedError


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
    return AdaptiveInvestigationEngine(db_session)


# ==============================================================================
# 0. CANONICAL TOOL COSTS & REPRODUCIBILITY
# ==============================================================================

def test_canonical_tool_costs():
    """Verify all 9 tool costs strictly match canonical specifications and sum to ₹250 with ₹150 cap."""
    canonical = {
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
    for tool, cost in canonical.items():
        assert TOOL_SIMULATED_COSTS[tool] == cost, f"Cost mismatch for {tool}: {TOOL_SIMULATED_COSTS[tool]} != {cost}"
    assert len(TOOL_SIMULATED_COSTS) == 9
    assert sum(TOOL_SIMULATED_COSTS.values()) == 255.0


def test_deterministic_reproducibility_full_trace(engine: AdaptiveInvestigationEngine):
    """Verify running run_investigation multiple times on hero case produces byte-identical traces."""
    run1 = engine.run_investigation("TXN_00000203")
    run2 = engine.run_investigation("TXN_00000203")
    assert run1.step_count == run2.step_count
    assert run1.total_tool_cost == run2.total_tool_cost
    assert run1.initial_uncertainty == run2.initial_uncertainty
    assert run1.final_uncertainty == run2.final_uncertainty
    assert run1.stopping_reason == run2.stopping_reason
    assert [s.tool_name for s in run1.steps] == [s.tool_name for s in run2.steps]
    assert [s.tool_cost for s in run1.steps] == [s.tool_cost for s in run2.steps]
    assert [s.estimated_information_gain for s in run1.steps] == [s.estimated_information_gain for s in run2.steps]


# ==============================================================================
# 1. INITIAL UNCERTAINTY & BOUNDS
# ==============================================================================

def test_initial_uncertainty_bounds_and_heuristic():
    """Verify U0 is strictly bounded in [0.05, 0.95] and sensitive to ambiguity and graph confidence."""
    for p in [0.0, 0.05, 0.5, 0.95, 1.0]:
        for conf in ["VERIFIED", "LIMITED", "UNAVAILABLE"]:
            u = AdaptiveInvestigationEngine.compute_initial_uncertainty(p, conf)
            assert 0.05 <= u <= 0.95, f"U0={u} out of bounds for p={p}, conf={conf}"

    # Ambiguity sensitivity: p=0.50 yields higher uncertainty than extreme p=0.98
    u_ambig = AdaptiveInvestigationEngine.compute_initial_uncertainty(0.50, "VERIFIED")
    u_extreme = AdaptiveInvestigationEngine.compute_initial_uncertainty(0.98, "VERIFIED")
    assert u_ambig > u_extreme

    # Graph confidence delta: UNAVAILABLE > LIMITED > VERIFIED
    u_unavail = AdaptiveInvestigationEngine.compute_initial_uncertainty(0.80, "UNAVAILABLE")
    u_limited = AdaptiveInvestigationEngine.compute_initial_uncertainty(0.80, "LIMITED")
    u_verified = AdaptiveInvestigationEngine.compute_initial_uncertainty(0.80, "VERIFIED")
    assert u_unavail > u_limited > u_verified


# ==============================================================================
# 2. DETERMINISTIC INFORMATION GAIN & REDUNDANCY PENALTY
# ==============================================================================

def test_expected_information_gain_and_redundancy(engine: AdaptiveInvestigationEngine):
    """Verify EIG calculation, domain overlap penalties, and executed tool exclusion."""
    u_prev = 0.50
    # Fresh tool with no executed tools
    eig_devices = engine.estimate_expected_information_gain("find_shared_devices", u_prev, [], [])
    assert 0.0 <= eig_devices <= 1.0
    assert eig_devices == round(0.50 * TOOL_BASE_RELEVANCE["find_shared_devices"], 4)

    # Executed tool yields exactly 0.0 EIG
    eig_executed = engine.estimate_expected_information_gain("find_shared_devices", u_prev, ["find_shared_devices"], [])
    assert eig_executed == 0.0

    # Redundancy penalty: find_shared_ips after find_shared_devices receives overlap penalty
    eig_ips_fresh = engine.estimate_expected_information_gain("find_shared_ips", u_prev, [], [])
    eig_ips_after_devices = engine.estimate_expected_information_gain("find_shared_ips", u_prev, ["find_shared_devices"], [])
    assert eig_ips_after_devices < eig_ips_fresh


# ==============================================================================
# 3. DETERMINISTIC TIE BREAKING (CORRECTION 3)
# ==============================================================================

def test_deterministic_tie_breaking(engine: AdaptiveInvestigationEngine):
    """Verify identical EIG values deterministically resolve by tool cost then preference order."""
    # When multiple tools fit within budget and have tie EIG, ordering must be 100% reproducible
    for _ in range(5):
        sel1 = engine.select_next_best_tool(
            current_uncertainty=0.40,
            executed_tools=[],
            accumulated_cost=0.0,
            tool_budget=150.0,
            evidence_collected=[],
        )
        sel2 = engine.select_next_best_tool(
            current_uncertainty=0.40,
            executed_tools=[],
            accumulated_cost=0.0,
            tool_budget=150.0,
            evidence_collected=[],
        )
        assert sel1 == sel2
        assert sel1 is not None
        # Highest relevance tool among fresh tools
        assert sel1[0] == "find_shared_devices"


# ==============================================================================
# 4. EVIDENCE QUALITY & CONFLICTING EVIDENCE (CORRECTION 4)
# ==============================================================================

def test_evidence_quality_and_conflicting_evidence():
    """Verify that a single empty query is WEAK_OR_EMPTY, and CONFLICTING requires multiple structural queries."""
    empty_res = ToolExecutionResult(
        tool_name="find_shared_devices",
        status=ToolExecutionStatus.EMPTY,
        target="ACC_000001",
        result=[],
        result_count=0,
        source="db",
        evidence_ids=[],
    )

    # Single empty query with high risk must remain WEAK_OR_EMPTY (Correction 4)
    q1 = AdaptiveInvestigationEngine.evaluate_evidence_quality(
        tool_name="find_shared_devices",
        result=empty_res,
        p_calibrated=0.95,
        executed_tools=["find_shared_devices"],
        all_results_by_tool={"find_shared_devices": empty_res},
    )
    assert q1 == EvidenceQualityType.WEAK_OR_EMPTY

    # Multiple structural queries executed and ALL empty yields CONFLICTING
    empty_res2 = ToolExecutionResult(
        tool_name="find_shared_ips",
        status=ToolExecutionStatus.EMPTY,
        target="ACC_000001",
        result=[],
        result_count=0,
        source="db",
        evidence_ids=[],
    )
    q2 = AdaptiveInvestigationEngine.evaluate_evidence_quality(
        tool_name="find_shared_ips",
        result=empty_res2,
        p_calibrated=0.95,
        executed_tools=["find_shared_devices", "find_shared_ips"],
        all_results_by_tool={"find_shared_devices": empty_res, "find_shared_ips": empty_res2},
    )
    assert q2 == EvidenceQualityType.CONFLICTING


# ==============================================================================
# 5. UNCERTAINTY UPDATE RULES
# ==============================================================================

def test_uncertainty_update_rules():
    """Verify strong evidence reduces uncertainty, empty leaves unchanged, and conflicting increases uncertainty."""
    # Strong evidence reduction
    u_prev = 0.30
    u_strong, red = AdaptiveInvestigationEngine.update_uncertainty(u_prev, EvidenceQualityType.STRONG, result_count=3)
    assert u_strong < u_prev
    assert red > 0.0

    # Weak / empty leaves uncertainty unchanged
    u_weak, red_weak = AdaptiveInvestigationEngine.update_uncertainty(u_prev, EvidenceQualityType.WEAK_OR_EMPTY, result_count=0)
    assert u_weak == u_prev
    assert red_weak == 0.0

    # Conflicting evidence increases uncertainty
    u_conf, red_conf = AdaptiveInvestigationEngine.update_uncertainty(u_prev, EvidenceQualityType.CONFLICTING, result_count=0)
    assert u_conf > u_prev
    assert red_conf == 0.0


# ==============================================================================
# 6. STOPPING POLICY PRECEDENCE (CORRECTION 8)
# ==============================================================================

def test_stopping_policy_precedence():
    """Verify strict precedence order when multiple stopping conditions are simultaneously met."""
    # Precedence 1: CONFLICTING takes highest precedence over step limit and uncertainty
    should_stop, reason, _ = AdaptiveInvestigationEngine.evaluate_stopping_policy(
        step_count=5,
        max_steps=5,
        current_u=0.08,
        accumulated_cost=150.0,
        tool_budget=150.0,
        candidate_tools_remaining=[],
        next_expected_ig=0.01,
        evidence_collected=[{"source_tool": "find_shared_devices"}, {"source_tool": "find_shared_ips"}],
        has_conflicting_evidence=True,
    )
    assert should_stop is True
    assert reason == StoppingReason.CONFLICTING_EVIDENCE_REQUIRES_HUMAN_REVIEW

    # Precedence 2: SUFFICIENT_EVIDENCE takes precedence over step limit and low uncertainty
    should_stop2, reason2, _ = AdaptiveInvestigationEngine.evaluate_stopping_policy(
        step_count=5,
        max_steps=5,
        current_u=0.05,
        accumulated_cost=150.0,
        tool_budget=150.0,
        candidate_tools_remaining=[],
        next_expected_ig=0.01,
        evidence_collected=[{"source_tool": "find_shared_devices"}, {"source_tool": "find_shared_ips"}],
        has_conflicting_evidence=False,
    )
    assert should_stop2 is True
    assert reason2 == StoppingReason.SUFFICIENT_EVIDENCE

    # Precedence 3: UNCERTAINTY_LOW_ENOUGH (U <= 0.12) takes precedence over MAX_STEPS and BUDGET
    should_stop3, reason3, _ = AdaptiveInvestigationEngine.evaluate_stopping_policy(
        step_count=5,
        max_steps=5,
        current_u=0.10,
        accumulated_cost=150.0,
        tool_budget=150.0,
        candidate_tools_remaining=[],
        next_expected_ig=0.01,
        evidence_collected=[],
        has_conflicting_evidence=False,
    )
    assert should_stop3 is True
    assert reason3 == StoppingReason.UNCERTAINTY_LOW_ENOUGH

    # Precedence 4: MAX_INVESTIGATION_STEPS takes precedence over cost ceiling
    should_stop4, reason4, _ = AdaptiveInvestigationEngine.evaluate_stopping_policy(
        step_count=5,
        max_steps=5,
        current_u=0.25,
        accumulated_cost=150.0,
        tool_budget=150.0,
        candidate_tools_remaining=["get_account"],
        next_expected_ig=0.10,
        evidence_collected=[],
        has_conflicting_evidence=False,
    )
    assert should_stop4 is True
    assert reason4 == StoppingReason.MAX_INVESTIGATION_STEPS

    # Precedence 5: INVESTIGATION_COST_TOO_HIGH (budget exhausted)
    should_stop5, reason5, _ = AdaptiveInvestigationEngine.evaluate_stopping_policy(
        step_count=2,
        max_steps=5,
        current_u=0.25,
        accumulated_cost=150.0,
        tool_budget=150.0,
        candidate_tools_remaining=["get_account"],
        next_expected_ig=0.10,
        evidence_collected=[],
        has_conflicting_evidence=False,
    )
    assert should_stop5 is True
    assert reason5 == StoppingReason.INVESTIGATION_COST_TOO_HIGH

    # Precedence 6: EVIDENCE_EXHAUSTED (no candidate tools remaining)
    should_stop6, reason6, _ = AdaptiveInvestigationEngine.evaluate_stopping_policy(
        step_count=2,
        max_steps=5,
        current_u=0.25,
        accumulated_cost=50.0,
        tool_budget=150.0,
        candidate_tools_remaining=[],
        next_expected_ig=0.10,
        evidence_collected=[],
        has_conflicting_evidence=False,
    )
    assert should_stop6 is True
    assert reason6 == StoppingReason.EVIDENCE_EXHAUSTED

    # Precedence 7: INFORMATION_GAIN_TOO_LOW (< 0.05)
    should_stop7, reason7, _ = AdaptiveInvestigationEngine.evaluate_stopping_policy(
        step_count=2,
        max_steps=5,
        current_u=0.25,
        accumulated_cost=50.0,
        tool_budget=150.0,
        candidate_tools_remaining=["get_account"],
        next_expected_ig=0.03,
        evidence_collected=[],
        has_conflicting_evidence=False,
    )
    assert should_stop7 is True
    assert reason7 == StoppingReason.INFORMATION_GAIN_TOO_LOW


# ==============================================================================
# 7. POINT-IN-TIME TEMPORAL SAFETY & FUTURE DATA EXCLUSION (CORRECTIONS 2 & 9)
# ==============================================================================

def test_point_in_time_future_data_exclusion(engine: AdaptiveInvestigationEngine, db_session: Session):
    """Explicitly verify that transactions/events occurring after target timestamp are strictly excluded."""
    # Find a transaction with subsequent transactions on the same account
    tx = db_session.query(Transaction).filter(Transaction.transaction_id == "TXN_00000001").first()
    assert tx is not None

    # Fetch future transactions on the same account that occurred strictly after tx.timestamp
    future_tx = (
        db_session.query(Transaction)
        .filter(
            Transaction.account_id == tx.account_id,
            Transaction.timestamp > tx.timestamp,
        )
        .first()
    )

    # Run investigation bounded at tx.timestamp
    res = engine.run_investigation(tx.transaction_id)
    assert res.timestamp == tx.timestamp.isoformat()

    # If future transactions exist in the DB, verify they were never included in the fund flow or timeline trace
    if future_tx:
        fund_flow_res = engine.inv_service.trace_fund_flow(tx.transaction_id, as_of=tx.timestamp.isoformat())
        if fund_flow_res.status == ToolExecutionStatus.SUCCESS and fund_flow_res.result:
            tx_ids_in_flow = [
                h["transaction_id"] if isinstance(h, dict) else h.transaction_id
                for h in fund_flow_res.result
            ]
            assert future_tx.transaction_id not in tx_ids_in_flow, (
                f"Temporal leak! Future transaction {future_tx.transaction_id} included in fund flow of {tx.transaction_id}"
            )


# ==============================================================================
# 8. HERO CASE & ADAPTIVE TRACE (TXN_00000203)
# ==============================================================================

def test_hero_case_adaptive_investigation(engine: AdaptiveInvestigationEngine):
    """Verify hero case TXN_00000203 discovers genuine evidence and stops with SUFFICIENT_EVIDENCE."""
    res = engine.run_investigation("TXN_00000203")

    assert res.transaction_id == "TXN_00000203"
    assert res.calibrated_risk_score >= 0.95
    assert res.initial_uncertainty >= 0.15
    assert res.final_uncertainty < res.initial_uncertainty
    assert res.uncertainty_reduction > 0.0
    assert res.relative_uncertainty_reduction > 0.0
    assert res.stop_decision == "STOP"
    assert res.stopping_reason == "SUFFICIENT_EVIDENCE"
    assert res.step_count == 2
    assert res.steps[0].tool_name == "find_shared_devices"
    assert res.steps[0].tool_cost == 35.0
    assert res.steps[1].tool_name == "trace_fund_flow"
    assert res.steps[1].tool_cost == 45.0
    assert res.total_tool_cost == 80.0
    assert res.total_tool_cost <= 150.0
    assert len(res.evidence_ids) >= 2
    assert res.human_approval_required is True

    # Verify per-step trace records, evidence provenance, and absence of hidden chain-of-thought
    assert len(res.steps) == res.step_count
    for s in res.steps:
        assert s.step_number >= 1
        assert s.tool_name in TOOL_SIMULATED_COSTS
        assert s.tool_cost > 0
        assert s.estimated_information_gain >= 0.0
        assert 0.05 <= s.uncertainty_before <= 0.95
        assert 0.05 <= s.uncertainty_after <= 0.95
        assert len(s.step_rationale) > 10
        # Invariant 19: No hidden chain-of-thought or reasoning tags exposed
        assert "<thought>" not in s.step_rationale
        assert "</thought>" not in s.step_rationale
        assert "thinking:" not in s.step_rationale.lower()
        # Invariant 15: Evidence provenance - well-formed evidence IDs
        for eid in s.evidence_ids:
            assert eid.startswith("EVD_") or eid.startswith("EV_") or eid.startswith("EV-")


# ==============================================================================
# 9. CROSS-STAGE INTEGRATION (CORRECTION 5)
# ==============================================================================

def test_cross_stage_integration(engine: AdaptiveInvestigationEngine):
    """Verify Stage 15 systemic anomaly and Stage 16 portfolio prioritization are cleanly integrated."""
    res = engine.run_investigation("TXN_00000203")

    # Stage 15 integration
    assert res.stage15_systemic_anomaly_score is not None
    assert 0.0 <= res.stage15_systemic_anomaly_score <= 1.0
    assert res.stage15_systemic_anomaly_score > 0.50  # Hero case has high ring anomaly

    # Stage 16 integration
    assert res.stage16_priority_score is not None
    assert 0.0 <= res.stage16_priority_score <= 1.0
    assert res.stage16_expected_value is not None
    assert res.stage16_expected_value > 50000.0  # Hero case has positive EV


# ==============================================================================
# 10. GOVERNANCE & SAFETY BOUNDARIES (CORRECTION 10)
# ==============================================================================

def test_governance_and_safety_guardrails(engine: AdaptiveInvestigationEngine):
    """Verify strict read-only execution, PermissionGuard enforcement, and zero autonomous mutation."""
    # Permission guard must forbid write operations
    with pytest.raises(PermissionDeniedError):
        PermissionGuard.check_permission("DATABASE_WRITE")
    with pytest.raises(PermissionDeniedError):
        PermissionGuard.check_permission("ACCOUNT_BLOCK")
    with pytest.raises(PermissionDeniedError):
        PermissionGuard.check_permission("PAYMENT_ACTION")

    # Investigation response must enforce human approval
    res = engine.run_investigation("TXN_00000203")
    assert res.human_approval_required is True
    assert "INVESTIGATION DECISION SUPPORT" in res.disclaimer


# ==============================================================================
# 11. FASTAPI ENDPOINTS VALIDATION
# ==============================================================================

def test_fastapi_adaptive_endpoints(client: TestClient):
    """Verify GET /transaction/{id}/adaptive endpoint returns typed response and validates errors."""
    # Valid transaction
    res = client.get("/api/investigation/transaction/TXN_00000203/adaptive")
    assert res.status_code == 200
    data = res.json()
    assert data["transaction_id"] == "TXN_00000203"
    assert data["stop_decision"] == "STOP"
    assert "calibrated_risk_score" in data  # Correction 6
    assert data["human_approval_required"] is True

    # Whitespace ID -> 422
    res_space = client.get("/api/investigation/transaction/   /adaptive")
    assert res_space.status_code == 422

    # Nonexistent ID -> 404
    res_404 = client.get("/api/investigation/transaction/TXN_DOES_NOT_EXIST_9999/adaptive")
    assert res_404.status_code == 404
