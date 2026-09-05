"""RingGuard AI — Stage 15 Test Suite: Investigation Efficiency & Agent Architecture.

Comprehensive test verification covering all 22 required operational criteria:
1. compute_initial_uncertainty bounded in [0.05, 0.95].
2. compute_initial_uncertainty higher for ambiguous probabilities than extreme.
3. compute_initial_uncertainty applies +0.20 delta for LIMITED graph confidence.
4. compute_initial_uncertainty applies +0.35 delta for UNAVAILABLE graph confidence.
5. compute_initial_uncertainty applies 0.0 delta for VERIFIED graph confidence.
6. estimate_expected_information_gain bounded in [0.0, 1.0].
7. estimate_expected_information_gain returns 0.0 for executed tools.
8. estimate_expected_information_gain applies redundancy penalty.
9. select_next_best_tool selects highest E[IG] tool fitting remaining budget.
10. select_next_best_tool returns None when no tool fits budget.
11. update_uncertainty reduces uncertainty on corroborating evidence.
12. update_uncertainty leaves uncertainty unchanged on empty/no results.
13. update_uncertainty handles conflicting evidence appropriately.
14. evaluate_stopping_policy triggers SUFFICIENT_EVIDENCE on >= 2 distinct sources.
15. evaluate_stopping_policy triggers UNCERTAINTY_LOW_ENOUGH when U <= 0.12.
16. evaluate_stopping_policy triggers INVESTIGATION_COST_TOO_HIGH when budget exhausted.
17. evaluate_stopping_policy triggers MAX_INVESTIGATION_STEPS when step limit reached.
18. evaluate_stopping_policy triggers CONFLICTING_EVIDENCE_REQUIRES_HUMAN_REVIEW.
19. derive_next_best_action enforces human_approval_required == True.
20. derive_next_best_action correctly assigns advisory actions.
21. CasePrioritizationService computes deterministic priority ranking with network leverage.
22. FastAPI endpoints (/agent/run, /agent/{id}/state, /agent/prioritization, /agent/efficiency).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.investigation.agent import (
    InvestigationAgent,
    TOOL_SIMULATED_COSTS,
    TOOL_BASE_RELEVANCE,
    compute_modeled_net_value_saved,
)
from app.investigation.schemas import (
    StoppingReason,
    NextBestActionType,
    ToolExecutionResult,
    ToolExecutionStatus,
)
from app.investigation.prioritization import CasePrioritizationService
from app.investigation.efficiency import InvestigationEfficiencyService


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ==============================================================================
# 1-5: INITIAL UNCERTAINTY TESTS
# ==============================================================================

def test_initial_uncertainty_bounded():
    """1. Uncertainty score must be bounded in [0.05, 0.95]."""
    for p in [0.0, 0.01, 0.5, 0.99, 1.0]:
        for conf in ["VERIFIED", "LIMITED", "UNAVAILABLE"]:
            u = InvestigationAgent.compute_initial_uncertainty(p, conf)
            assert 0.05 <= u <= 0.95, f"Uncertainty {u} out of bounds for p={p}, conf={conf}"


def test_initial_uncertainty_ambiguity_sensitivity():
    """2. Ambiguous probability (p=0.5) must yield higher uncertainty than extreme (p=0.9)."""
    u_ambig = InvestigationAgent.compute_initial_uncertainty(0.50, "VERIFIED")
    u_extreme = InvestigationAgent.compute_initial_uncertainty(0.95, "VERIFIED")
    assert u_ambig > u_extreme


def test_initial_uncertainty_limited_confidence_delta():
    """3. LIMITED graph confidence must add +0.20 delta."""
    u_verified = InvestigationAgent.compute_initial_uncertainty(0.80, "VERIFIED")
    u_limited = InvestigationAgent.compute_initial_uncertainty(0.80, "LIMITED")
    assert round(u_limited - u_verified, 2) == 0.20


def test_initial_uncertainty_unavailable_confidence_delta():
    """4. UNAVAILABLE graph confidence must add +0.35 delta."""
    u_verified = InvestigationAgent.compute_initial_uncertainty(0.80, "VERIFIED")
    u_unavail = InvestigationAgent.compute_initial_uncertainty(0.80, "UNAVAILABLE")
    assert round(u_unavail - u_verified, 2) == 0.35


def test_initial_uncertainty_verified_confidence_delta():
    """5. VERIFIED graph confidence has 0.0 delta."""
    # At p=0.80, ambiguity = 1.0 - 2 * 0.30 = 0.40
    u_verified = InvestigationAgent.compute_initial_uncertainty(0.80, "VERIFIED")
    assert u_verified == 0.40


# ==============================================================================
# 6-10: EXPECTED INFORMATION GAIN & TOOL SELECTION TESTS
# ==============================================================================

def test_expected_information_gain_bounded():
    """6. Expected information gain must be in [0.0, 1.0]."""
    for tool in TOOL_BASE_RELEVANCE.keys():
        e_ig = InvestigationAgent.estimate_expected_information_gain(
            tool_name=tool,
            current_uncertainty=0.50,
            executed_tools=[],
            evidence_collected=[],
        )
        assert 0.0 <= e_ig <= 1.0


def test_expected_information_gain_zero_for_executed():
    """7. Executed tool must have E[IG] == 0.0."""
    e_ig = InvestigationAgent.estimate_expected_information_gain(
        tool_name="find_shared_devices",
        current_uncertainty=0.50,
        executed_tools=["find_shared_devices"],
        evidence_collected=[],
    )
    assert e_ig == 0.0


def test_expected_information_gain_redundancy_penalty():
    """8. Related executed tools must penalize subsequent tool E[IG]."""
    e_ig_fresh = InvestigationAgent.estimate_expected_information_gain(
        tool_name="find_shared_ips",
        current_uncertainty=0.50,
        executed_tools=[],
        evidence_collected=[],
    )
    e_ig_penalized = InvestigationAgent.estimate_expected_information_gain(
        tool_name="find_shared_ips",
        current_uncertainty=0.50,
        executed_tools=["find_shared_devices"],
        evidence_collected=[],
    )
    assert e_ig_penalized < e_ig_fresh


def test_select_next_best_tool_budget_compliance(db_session: Session):
    """9. Tool selection must prioritize highest E[IG] within remaining budget."""
    agent = InvestigationAgent(db_session)
    # Remaining budget ₹40: can afford get_account (15), get_transactions (25), find_related_accounts (30), etc.
    # but not trace_fund_flow (45).
    tool, ig = agent.select_next_best_tool(
        current_uncertainty=0.50,
        executed_tools=[],
        accumulated_cost=110.0,
        tool_budget=150.0,
        evidence_collected=[],
    )
    assert tool is not None
    assert TOOL_SIMULATED_COSTS[tool] <= 40.0
    assert tool != "trace_fund_flow"


def test_select_next_best_tool_exhausted_budget(db_session: Session):
    """10. Return None when budget cannot afford any candidate tool."""
    agent = InvestigationAgent(db_session)
    tool_sel = agent.select_next_best_tool(
        current_uncertainty=0.50,
        executed_tools=[],
        accumulated_cost=145.0,
        tool_budget=150.0,  # Remaining ₹5, cheapest tool is ₹15
        evidence_collected=[],
    )
    assert tool_sel is None


# ==============================================================================
# 11-13: UNCERTAINTY UPDATES & CONFLICT HANDLING
# ==============================================================================

def test_update_uncertainty_supporting_evidence():
    """11. Corroborating evidence must strictly reduce uncertainty."""
    res = ToolExecutionResult(
        tool_name="find_shared_devices",
        status=ToolExecutionStatus.SUCCESS,
        target="ACC_000213",
        result_count=3,
        source="device",
        evidence_ids=["EV_001"],
    )
    new_u, delta, conflict = InvestigationAgent.update_uncertainty(
        current_u=0.40,
        tool_name="find_shared_devices",
        result=res,
        p_calibrated=0.85,
        prior_evidence_count=0,
    )
    assert new_u < 0.40
    assert delta > 0.0
    assert conflict is False


def test_update_uncertainty_empty_evidence_no_change():
    """12. Empty tool execution must leave uncertainty unchanged (no fabricated reduction)."""
    res = ToolExecutionResult(
        tool_name="find_shared_ips",
        status=ToolExecutionStatus.EMPTY,
        target="ACC_000054",
        result_count=0,
        source="ip",
        evidence_ids=[],
    )
    new_u, delta, conflict = InvestigationAgent.update_uncertainty(
        current_u=0.35,
        tool_name="find_shared_ips",
        result=res,
        p_calibrated=0.10,
        prior_evidence_count=0,
    )
    assert new_u == 0.35
    assert delta == 0.0
    assert conflict is False


def test_update_uncertainty_conflicting_evidence():
    """13. Contradictory evidence (high risk model vs empty infrastructure) flags conflict."""
    res = ToolExecutionResult(
        tool_name="find_shared_devices",
        status=ToolExecutionStatus.EMPTY,
        target="ACC_000099",
        result_count=0,
        source="device",
        evidence_ids=[],
    )
    new_u, delta, conflict = InvestigationAgent.update_uncertainty(
        current_u=0.30,
        tool_name="find_shared_devices",
        result=res,
        p_calibrated=0.85,  # High risk prior
        prior_evidence_count=0,
    )
    assert conflict is True
    assert new_u > 0.30


# ==============================================================================
# 14-18: STOPPING POLICY TESTS
# ==============================================================================

def test_stopping_policy_sufficient_evidence():
    """14. Stop when >= 2 distinct structural domains have evidence."""
    evs = [
        {"source_tool": "find_shared_devices", "result_count": 2},
        {"source_tool": "trace_fund_flow", "result_count": 4},
    ]
    should_stop, reason, _ = InvestigationAgent.evaluate_stopping_policy(
        step_count=2,
        max_steps=5,
        current_u=0.25,
        accumulated_cost=80.0,
        tool_budget=150.0,
        candidate_tools_remaining=["get_account"],
        next_expected_ig=0.15,
        evidence_collected=evs,
        has_conflicting_evidence=False,
    )
    assert should_stop is True
    assert reason == StoppingReason.SUFFICIENT_EVIDENCE


def test_stopping_policy_uncertainty_low_enough():
    """15. Stop when uncertainty <= 0.12."""
    should_stop, reason, _ = InvestigationAgent.evaluate_stopping_policy(
        step_count=1,
        max_steps=5,
        current_u=0.10,  # <= 0.12
        accumulated_cost=35.0,
        tool_budget=150.0,
        candidate_tools_remaining=["get_account"],
        next_expected_ig=0.08,
        evidence_collected=[],
        has_conflicting_evidence=False,
    )
    assert should_stop is True
    assert reason == StoppingReason.UNCERTAINTY_LOW_ENOUGH


def test_stopping_policy_cost_too_high():
    """16. Stop when accumulated cost reaches or exceeds budget."""
    should_stop, reason, _ = InvestigationAgent.evaluate_stopping_policy(
        step_count=3,
        max_steps=5,
        current_u=0.30,
        accumulated_cost=150.0,  # budget ceiling
        tool_budget=150.0,
        candidate_tools_remaining=["get_account"],
        next_expected_ig=0.15,
        evidence_collected=[],
        has_conflicting_evidence=False,
    )
    assert should_stop is True
    assert reason == StoppingReason.INVESTIGATION_COST_TOO_HIGH


def test_stopping_policy_max_steps():
    """17. Stop when step limit is reached."""
    should_stop, reason, _ = InvestigationAgent.evaluate_stopping_policy(
        step_count=5,
        max_steps=5,
        current_u=0.30,
        accumulated_cost=90.0,
        tool_budget=150.0,
        candidate_tools_remaining=["get_account"],
        next_expected_ig=0.10,
        evidence_collected=[],
        has_conflicting_evidence=False,
    )
    assert should_stop is True
    assert reason == StoppingReason.MAX_INVESTIGATION_STEPS


def test_stopping_policy_conflicting_evidence():
    """18. Stop when conflicting evidence triggers specialist review."""
    should_stop, reason, _ = InvestigationAgent.evaluate_stopping_policy(
        step_count=1,
        max_steps=5,
        current_u=0.40,
        accumulated_cost=35.0,
        tool_budget=150.0,
        candidate_tools_remaining=["get_account"],
        next_expected_ig=0.20,
        evidence_collected=[],
        has_conflicting_evidence=True,
    )
    assert should_stop is True
    assert reason == StoppingReason.CONFLICTING_EVIDENCE_REQUIRES_HUMAN_REVIEW


# ==============================================================================
# 19-20: ADVISORY NEXT BEST ACTION TESTS
# ==============================================================================

def test_next_best_action_human_approval_mandatory():
    """19. All next-best-action outputs must strictly set human_approval_required == True."""
    for action_cond in [
        (0.90, 0.10, "VERIFIED", StoppingReason.SUFFICIENT_EVIDENCE, [{"source_tool": "t1"}, {"source_tool": "t2"}], 10000.0, False),
        (0.05, 0.10, "VERIFIED", StoppingReason.UNCERTAINTY_LOW_ENOUGH, [], 500.0, False),
        (0.40, 0.30, "VERIFIED", StoppingReason.MAX_INVESTIGATION_STEPS, [], 1000.0, False),
        (0.75, 0.35, "LIMITED", StoppingReason.MAX_INVESTIGATION_STEPS, [], 60000.0, False),
        (0.85, 0.50, "VERIFIED", StoppingReason.CONFLICTING_EVIDENCE_REQUIRES_HUMAN_REVIEW, [], 5000.0, True),
    ]:
        nba = InvestigationAgent.derive_next_best_action(
            p_calibrated=action_cond[0],
            current_u=action_cond[1],
            graph_confidence=action_cond[2],
            stopping_reason=action_cond[3],
            evidence_collected=action_cond[4],
            exposure_amount=action_cond[5],
            has_conflicting_evidence=action_cond[6],
        )
        assert nba.human_approval_required is True


def test_next_best_action_classification():
    """20. Correct mapping of advisory action categories."""
    # Allow: low risk, low uncertainty, no evidence
    nba_allow = InvestigationAgent.derive_next_best_action(
        p_calibrated=0.05,
        current_u=0.10,
        graph_confidence="VERIFIED",
        stopping_reason=StoppingReason.UNCERTAINTY_LOW_ENOUGH,
        evidence_collected=[],
        exposure_amount=1000.0,
        has_conflicting_evidence=False,
    )
    assert nba_allow.recommended_action == NextBestActionType.ALLOW

    # Hold: high risk, corroborated evidence
    nba_hold = InvestigationAgent.derive_next_best_action(
        p_calibrated=0.85,
        current_u=0.15,
        graph_confidence="VERIFIED",
        stopping_reason=StoppingReason.SUFFICIENT_EVIDENCE,
        evidence_collected=[{"source_tool": "t1"}, {"source_tool": "t2"}],
        exposure_amount=20000.0,
        has_conflicting_evidence=False,
    )
    assert nba_hold.recommended_action == NextBestActionType.HOLD_FOR_REVIEW

    # Escalate: high exposure > 50,000
    nba_esc = InvestigationAgent.derive_next_best_action(
        p_calibrated=0.85,
        current_u=0.15,
        graph_confidence="VERIFIED",
        stopping_reason=StoppingReason.SUFFICIENT_EVIDENCE,
        evidence_collected=[{"source_tool": "t1"}, {"source_tool": "t2"}],
        exposure_amount=75000.0,
        has_conflicting_evidence=False,
    )
    assert nba_esc.recommended_action == NextBestActionType.ESCALATE_TO_ANALYST


# ==============================================================================
# 21: CASE PRIORITIZATION TESTS
# ==============================================================================

def test_case_prioritization_deterministic_ranking(db_session: Session):
    """21. CasePrioritizationService ranks primary fraud rings above low-risk controls."""
    prio_service = CasePrioritizationService(db_session)
    resp = prio_service.prioritize_cases(
        transaction_ids=["TXN_00000203", "TXN_00000646", "TXN_00000500"],
        limit=3,
    )
    assert resp.total_pending_cases == 3
    # TXN_00000203 (ring fraud ₹99,500) must rank #1
    assert resp.cases[0].transaction_id == "TXN_00000203"
    assert resp.cases[0].triage_rank == 1
    assert resp.cases[0].priority_score > resp.cases[1].priority_score
    assert resp.cases[0].network_leverage > 0.0


# ==============================================================================
# 22: FASTAPI ENDPOINT INTEGRATION TESTS
# ==============================================================================

def test_fastapi_endpoints(client: TestClient):
    """22. Verify all 4 Stage 15 endpoints return valid responses."""
    # A. Efficiency benchmark endpoint
    r_eff = client.get("/api/investigation/agent/efficiency")
    assert r_eff.status_code == 200
    d_eff = r_eff.json()
    assert d_eff["status"] == "Available"
    assert "overall" in d_eff["slices"]
    assert "ring_fraud" in d_eff["slices"]

    # B. Prioritization queue endpoint
    r_prio = client.get("/api/investigation/agent/prioritization?limit=4")
    assert r_prio.status_code == 200
    d_prio = r_prio.json()
    assert d_prio["total_pending_cases"] >= 1
    assert len(d_prio["cases"]) >= 1

    # C. Run investigation endpoint
    r_run = client.post(
        "/api/investigation/agent/run",
        json={"transaction_id": "TXN_00000203", "max_steps": 3, "tool_budget": 120.0},
    )
    assert r_run.status_code == 200
    d_run = r_run.json()
    assert d_run["transaction_id"] == "TXN_00000203"
    assert d_run["step_count"] >= 1
    assert d_run["stopping_status"] == "STOPPED"
    assert d_run["next_best_action"]["human_approval_required"] is True

    # D. Get investigation state endpoint
    r_state = client.get("/api/investigation/agent/TXN_00000203/state")
    assert r_state.status_code == 200
    d_state = r_state.json()
    assert d_state["transaction_id"] == "TXN_00000203"
    assert d_state["calibrated_risk"] > 0.90


# ==============================================================================
# 23: ECONOMIC FORMULA TESTS (Exact Approved Stage 12/14 Formula)
# Modeled Net Value Saved = Modeled Loss Avoided - (FP * CFP) - ((TP + FP) * Cinv)
# ==============================================================================

def test_economic_formula_scenario_1_tp0_fp0():
    """Scenario 1: TP=0, FP=0 (Cleared case, no human review or friction).
    Modeled Net Value Saved = 0 - 0 - 0 = 0.00
    """
    net = compute_modeled_net_value_saved(
        modeled_loss_avoided=0.0,
        tp=0.0,
        fp=0.0,
        c_fp=1200.0,
        c_inv=350.0,
    )
    assert net == 0.00


def test_economic_formula_scenario_2_tp_pos_fp0():
    """Scenario 2: TP>0, FP=0 (True positive flag without false positive friction).
    Net = Loss Avoided - 0 - (TP * 350)
    """
    loss_avoided = 50000.0 * 0.85
    tp = 1.0
    fp = 0.0
    expected_net = loss_avoided - (0.0 * 1200.0) - ((1.0 + 0.0) * 350.0)
    net = compute_modeled_net_value_saved(
        modeled_loss_avoided=loss_avoided,
        tp=tp,
        fp=fp,
        c_fp=1200.0,
        c_inv=350.0,
    )
    assert net == round(expected_net, 2)
    assert net == round(42500.0 - 350.0, 2)


def test_economic_formula_scenario_3_tp0_fp_pos():
    """Scenario 3: TP=0, FP>0 (Pure false positive flag: friction + investigation overhead).
    Net = 0 - (FP * 1200) - (FP * 350)
    """
    tp = 0.0
    fp = 1.0
    expected_net = 0.0 - (1.0 * 1200.0) - ((0.0 + 1.0) * 350.0)
    net = compute_modeled_net_value_saved(
        modeled_loss_avoided=0.0,
        tp=tp,
        fp=fp,
        c_fp=1200.0,
        c_inv=350.0,
    )
    assert net == round(expected_net, 2)
    assert net == -1550.00


def test_economic_formula_scenario_4_tp_pos_fp_pos():
    """Scenario 4: TP>0, FP>0 (Mixed/probabilistic flagged case).
    Net = Loss Avoided - (FP * 1200) - ((TP + FP) * 350)
    """
    tp = 0.80
    fp = 0.20
    loss_avoided = 25000.0 * 0.80 * 0.85  # 17,000.0
    expected_net = 17000.0 - (0.20 * 1200.0) - ((0.80 + 0.20) * 350.0)
    net = compute_modeled_net_value_saved(
        modeled_loss_avoided=loss_avoided,
        tp=tp,
        fp=fp,
        c_fp=1200.0,
        c_inv=350.0,
    )
    assert net == round(expected_net, 2)
    assert net == round(17000.0 - 240.0 - 350.0, 2)
    assert net == 16410.00


# ==============================================================================
# 24: UNCERTAINTY INVARIANT ENFORCEMENT ACROSS ALL STAGES [0.05, 0.95]
# ==============================================================================

def test_uncertainty_invariant_across_all_lifecycle_stages(db_session: Session):
    """Ensure uncertainty is strictly bounded within [0.05, 0.95] across all lifecycle steps."""
    # A. Initialization
    for p in [0.0, 0.001, 0.1, 0.5, 0.9, 0.999, 1.0]:
        for conf in ["VERIFIED", "LIMITED", "UNAVAILABLE"]:
            u0 = InvestigationAgent.compute_initial_uncertainty(p, conf)
            assert 0.05 <= u0 <= 0.95, f"Initial U0 out of bounds: {u0} for p={p}, conf={conf}"

    # B. Corroborating evidence updates (cannot drop below 0.05)
    res_succ = ToolExecutionResult(
        tool_name="find_shared_devices",
        status=ToolExecutionStatus.SUCCESS,
        target="ACC_TEST",
        result_count=100,  # massive evidence
        source="device",
        evidence_ids=["EV_1", "EV_2"],
    )
    u_curr = 0.06
    u_after, _, _ = InvestigationAgent.update_uncertainty(
        current_u=u_curr,
        tool_name="find_shared_devices",
        result=res_succ,
        p_calibrated=0.95,
        prior_evidence_count=5,
    )
    assert 0.05 <= u_after <= 0.95

    # C. Empty evidence updates
    res_empty = ToolExecutionResult(
        tool_name="find_shared_ips",
        status=ToolExecutionStatus.EMPTY,
        target="ACC_TEST",
        result_count=0,
        source="ip",
        evidence_ids=[],
    )
    u_after_empty, _, _ = InvestigationAgent.update_uncertainty(
        current_u=0.05,
        tool_name="find_shared_ips",
        result=res_empty,
        p_calibrated=0.10,
        prior_evidence_count=0,
    )
    assert u_after_empty == 0.05

    # D. Conflicting evidence updates (cannot exceed 0.95)
    u_high = 0.92
    u_after_conflict, _, is_conflict = InvestigationAgent.update_uncertainty(
        current_u=u_high,
        tool_name="find_shared_devices",
        result=res_empty,
        p_calibrated=0.90,
        prior_evidence_count=0,
    )
    assert is_conflict is True
    assert 0.05 <= u_after_conflict <= 0.95

    # E. Full investigation session verification on a mature low-risk case
    agent = InvestigationAgent(db_session)
    res_mature = agent.run_investigation("TXN_00000001", max_steps=5, tool_budget=150.0)
    assert 0.05 <= res_mature.initial_uncertainty <= 0.95
    assert 0.05 <= res_mature.current_uncertainty <= 0.95
    assert res_mature.initial_uncertainty != 0.0
    assert res_mature.current_uncertainty != 0.0

