"""RingGuard AI — V2 Stage 16: Portfolio Risk Prioritization + Expected Value Tests.

Validates:
1. Deterministic priority score reproducibility
2. Portfolio ranking reproducibility and ordering
3. High-risk/high-exposure case prioritization (Hero TXN_00000203)
4. Low-risk control cases prioritization and negative EV (TXN_00000646, TXN_00000500)
5. Exact decision-theoretic expected-value mathematical formulation
6. Economic assumptions visibility and parameter auditability
7. Synthetic monetary value disclaimer presence
8. Interpretable priority reason generation answering "Why investigate this case?"
9. FastAPI endpoints validation and typed responses
10. Nonexistent and whitespace transaction handling (404 / 422)
11. Read-only defense-only governance (human_approval_required = True)
12. Stage 15 systemic anomaly integration verification
13. Portfolio limit & normalization stability (Correction 5)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.prioritization.service import PortfolioPrioritizationService
from app.prioritization.schemas import PrioritizedCaseItem, PortfolioPrioritizationResponse


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def prio_service(db_session: Session):
    return PortfolioPrioritizationService(db_session)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# 1. DETERMINISTIC PRIORITY SCORE
def test_deterministic_priority_score(prio_service: PortfolioPrioritizationService):
    """Verify that repeated evaluation of the same transaction yields identical priority scores."""
    r1 = prio_service.prioritize_transaction("TXN_00000203")
    r2 = prio_service.prioritize_transaction("TXN_00000203")

    assert r1.transaction_id == r2.transaction_id
    assert r1.priority_score == r2.priority_score
    assert r1.expected_value == r2.expected_value
    assert r1.expected_loss_avoided == r2.expected_loss_avoided
    assert r1.friction_cost == r2.friction_cost
    assert r1.investigation_cost == r2.investigation_cost
    assert r1.ev_normalized == r2.ev_normalized
    assert r1.network_leverage == r2.network_leverage
    assert r1.systemic_anomaly_score == r2.systemic_anomaly_score
    assert r1.investigative_uncertainty == r2.investigative_uncertainty
    assert r1.priority_reason == r2.priority_reason


# 2. PORTFOLIO RANKING REPRODUCIBILITY
def test_portfolio_ranking_reproducibility(prio_service: PortfolioPrioritizationService):
    """Verify that repeated portfolio queries produce identical case ordering and scores."""
    p1 = prio_service.prioritize_portfolio(limit=10)
    p2 = prio_service.prioritize_portfolio(limit=10)

    assert p1.total_cases_evaluated == p2.total_cases_evaluated
    assert len(p1.cases) == len(p2.cases)

    for i in range(len(p1.cases)):
        c1 = p1.cases[i]
        c2 = p2.cases[i]
        assert c1.transaction_id == c2.transaction_id
        assert c1.priority_rank == c2.priority_rank == (i + 1)
        assert c1.priority_score == c2.priority_score
        assert c1.expected_value == c2.expected_value


# 3. HIGH-RISK / HIGH-EXPOSURE CASE PRIORITIZATION (HERO TXN_00000203)
def test_hero_case_high_priority_and_positive_ev(prio_service: PortfolioPrioritizationService):
    """Verify hero case TXN_00000203 receives high priority score and high positive EV."""
    res = prio_service.prioritize_transaction("TXN_00000203")

    assert res.transaction_id == "TXN_00000203"
    assert res.risk_score >= 0.95
    assert res.exposure >= 90000.0
    assert res.expected_value > 80000.0  # Massive positive net value saved
    assert res.ev_normalized > 0.90
    assert res.priority_score >= 0.70
    assert res.recommended_action == "PRIORITIZE_INVESTIGATION"
    assert "net saved" in res.priority_reason.lower() or "expected value" in res.priority_reason.lower()


# 4. LOW-RISK CONTROL CASE PRIORITIZATION & NEGATIVE EV
def test_control_cases_low_priority_and_negative_ev(prio_service: PortfolioPrioritizationService):
    """Verify control transactions receive low priority scores and negative expected values."""
    for cid in ["TXN_00000646", "TXN_00000500"]:
        res = prio_service.prioritize_transaction(cid)
        assert res.risk_score < 0.05
        # For near-zero risk, investigation cost (350) + friction (~1200) far exceed loss avoided (< 1)
        assert res.expected_value < 0.0
        # Negative EV must be clipped to 0.0 in EVnorm (Correction 1)
        assert res.ev_normalized == 0.0
        assert res.priority_score < 0.40
        assert res.recommended_action in ["LOW_PRIORITY", "NO_IMMEDIATE_INVESTIGATION"]
        assert "negative expected value" in res.priority_reason.lower()


# 5. EXPECTED-VALUE MATHEMATICAL FORMULATION
def test_expected_value_mathematical_formulation(prio_service: PortfolioPrioritizationService):
    """Verify exact mathematical reconciliation: EV = Loss Avoided - Friction - Investigation Cost."""
    res = prio_service.prioritize_transaction("TXN_00000203")

    p = res.risk_score
    exp = res.exposure
    r_int = res.economic_assumptions.interception_rate
    cfp = res.economic_assumptions.friction_cost_per_false_positive_cfp
    cinv = res.economic_assumptions.cost_per_investigation_cinv

    expected_loss_avoided = round(p * exp * r_int, 2)
    expected_friction_cost = round((1.0 - p) * cfp, 2)
    expected_investigation_cost = round(cinv, 2)
    expected_net_value = round(expected_loss_avoided - expected_friction_cost - expected_investigation_cost, 2)

    assert res.expected_loss_avoided == expected_loss_avoided
    assert res.friction_cost == expected_friction_cost
    assert res.investigation_cost == expected_investigation_cost
    assert res.expected_value == expected_net_value


# 6. ECONOMIC ASSUMPTIONS VISIBILITY & AUDITABILITY
def test_economic_assumptions_visibility(prio_service: PortfolioPrioritizationService):
    """Verify all predeclared economic assumptions are explicitly exposed."""
    res = prio_service.prioritize_transaction("TXN_00000203")
    assumptions = res.economic_assumptions

    assert assumptions.interception_rate == 0.85
    assert assumptions.cost_per_investigation_cinv == 350.0
    assert assumptions.friction_cost_per_false_positive_cfp == 1200.0
    assert assumptions.ev_cap == 85000.0
    assert assumptions.simulated_estimate is True


# 7. SYNTHETIC MONETARY VALUE DISCLAIMER
def test_synthetic_monetary_value_disclaimer(prio_service: PortfolioPrioritizationService):
    """Verify disclaimer clearly labels values as simulated estimates and disclaims real Razorpay loss."""
    res = prio_service.prioritize_transaction("TXN_00000203")

    assert "SIMULATED / SYNTHETIC ESTIMATE" in res.synthetic_monetary_value_disclaimer
    assert "synthetic benchmark data" in res.synthetic_monetary_value_disclaimer
    assert "do not represent real Razorpay" in res.synthetic_monetary_value_disclaimer


# 8. PRIORITY REASON GENERATION
def test_priority_reason_generation(prio_service: PortfolioPrioritizationService):
    """Verify priority reason answers 'Why investigate this case before another?'."""
    r_high = prio_service.prioritize_transaction("TXN_00000203")
    r_low = prio_service.prioritize_transaction("TXN_00000646")

    assert len(r_high.priority_reason) > 20
    assert "₹" in r_high.priority_reason or "INR" in r_high.priority_reason
    assert "expected value" in r_high.priority_reason.lower()

    assert len(r_low.priority_reason) > 20
    assert "negative expected value" in r_low.priority_reason.lower()


# 9. FASTAPI ENDPOINTS VALIDATION
def test_fastapi_prioritization_endpoints(client: TestClient):
    """Verify FastAPI GET endpoints return typed responses."""
    # Health
    h = client.get("/api/prioritization/health")
    assert h.status_code == 200
    assert h.json()["status"] == "ok"
    assert h.json()["stage"] == 16

    # Transaction
    t = client.get("/api/prioritization/transaction/TXN_00000203")
    assert t.status_code == 200
    data_t = t.json()
    assert data_t["transaction_id"] == "TXN_00000203"
    assert data_t["expected_value"] > 0
    assert data_t["priority_score"] > 0

    # Portfolio
    p = client.get("/api/prioritization/portfolio?limit=5")
    assert p.status_code == 200
    data_p = p.json()
    assert data_p["total_cases_evaluated"] == 5
    assert len(data_p["cases"]) == 5
    # Verify cases are sorted descending by priority_score
    scores = [c["priority_score"] for c in data_p["cases"]]
    assert scores == sorted(scores, reverse=True)


# 10. NONEXISTENT & WHITESPACE TRANSACTION HANDLING
def test_fastapi_error_handling(client: TestClient):
    """Verify invalid inputs return HTTP 422 and non-existent IDs return HTTP 404."""
    r_empty = client.get("/api/prioritization/transaction/   ")
    assert r_empty.status_code == 422

    r_none = client.get("/api/prioritization/transaction/TXN_DOES_NOT_EXIST_9999")
    assert r_none.status_code == 404


# 11. READ-ONLY / SECURITY BOUNDARY
def test_read_only_and_human_approval_required(prio_service: PortfolioPrioritizationService):
    """Verify defense-only governance: human approval mandatory, no autonomous writes."""
    res = prio_service.prioritize_transaction("TXN_00000203")
    assert res.human_approval_required is True

    port = prio_service.prioritize_portfolio(limit=3)
    assert port.human_approval_required is True
    for c in port.cases:
        assert c.human_approval_required is True


# 12. STAGE 15 SYSTEMIC ANOMALY INTEGRATION
def test_stage15_systemic_anomaly_integration(prio_service: PortfolioPrioritizationService):
    """Verify Stage 15 systemic anomaly score is cleanly integrated without mutation."""
    res = prio_service.prioritize_transaction("TXN_00000203")
    assert res.systemic_anomaly_score > 0.50  # Hero case has elevated infrastructure & ring anomaly


# 13. PORTFOLIO LIMIT / NORMALIZATION STABILITY (CORRECTION 5)
def test_portfolio_limit_and_normalization_stability(prio_service: PortfolioPrioritizationService):
    """Verify that portfolio size (limit=5 vs limit=20) does not alter a transaction's priority score."""
    res_single = prio_service.prioritize_transaction("TXN_00000203")

    port_5 = prio_service.prioritize_portfolio(limit=5)
    port_20 = prio_service.prioritize_portfolio(limit=20)

    # Find TXN_00000203 in both portfolios
    case_in_5 = next((c for c in port_5.cases if c.transaction_id == "TXN_00000203"), None)
    case_in_20 = next((c for c in port_20.cases if c.transaction_id == "TXN_00000203"), None)

    assert case_in_5 is not None
    assert case_in_20 is not None

    # Priority score and EVnorm must be 100% invariant to batch size / limit
    assert case_in_5.priority_score == res_single.priority_score
    assert case_in_20.priority_score == res_single.priority_score
    assert case_in_5.ev_normalized == res_single.ev_normalized
    assert case_in_20.ev_normalized == res_single.ev_normalized
    assert case_in_5.expected_value == res_single.expected_value
    assert case_in_20.expected_value == res_single.expected_value
