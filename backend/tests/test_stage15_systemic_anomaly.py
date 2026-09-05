"""RingGuard AI — V2 Stage 15: Systemic Risk Anomaly Detection Tests.

Validates:
1. Deterministic output reproducibility
2. Customer/account-level anomaly detection
3. Merchant-level anomaly detection on P2M and NOT_APPLICABLE on P2P
4. Ring/network-level topological anomaly
5. Possible systemic anomaly non-causal wording compliance
6. Unavailable data handling (failure rates, GPS coordinates)
7. Evidence provenance and linkage to Stage 9 EvidenceEngine
8. No unsupported bank/PSP causal accusations
9. Human-in-the-loop and defense-only non-enforcement invariants
10. FastAPI endpoint validation and error handling
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.transaction import Transaction
from app.anomaly.service import SystemicAnomalyService
from app.anomaly.schemas import (
    AnomalyScope,
    SignalStatus,
    SystemicAnomalyResponse,
)


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def anomaly_service(db_session: Session):
    return SystemicAnomalyService(db_session)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# 1. DETERMINISTIC OUTPUT
def test_deterministic_output(anomaly_service: SystemicAnomalyService):
    """Verify that repeated analysis of the same transaction yields identical results."""
    res1 = anomaly_service.analyze_transaction("TXN_00000203")
    res2 = anomaly_service.analyze_transaction("TXN_00000203")

    assert res1.transaction_id == res2.transaction_id
    assert res1.systemic_anomaly_score == res2.systemic_anomaly_score
    assert res1.anomaly_detected == res2.anomaly_detected
    assert res1.primary_contributing_scope == res2.primary_contributing_scope

    for scope_key in ["account", "merchant", "ring_network", "systemic_infrastructure"]:
        s1 = res1.scopes[scope_key]
        s2 = res2.scopes[scope_key]
        assert s1.anomaly_score == s2.anomaly_score
        assert s1.status == s2.status
        assert s1.reason == s2.reason
        assert len(s1.signals) == len(s2.signals)


# 2. ACCOUNT / CUSTOMER ANOMALY
def test_account_level_signals(anomaly_service: SystemicAnomalyService):
    """Verify account-level velocity and amount signals are computed from actual data."""
    res = anomaly_service.analyze_transaction("TXN_00000203")
    account_scope = res.scopes["account"]

    assert account_scope.scope == AnomalyScope.ACCOUNT
    signal_names = {s.name for s in account_scope.signals}
    assert "velocity_burst_1h" in signal_names
    assert "velocity_burst_24h" in signal_names
    assert "transaction_amount_spike" in signal_names
    assert "new_hardware_or_network_endpoint" in signal_names

    # Check that available signals have valid values
    for s in account_scope.signals:
        if s.status == SignalStatus.AVAILABLE:
            assert s.value is not None


# 3. MERCHANT ANOMALY (P2M vs P2P)
def test_merchant_scope_p2p_is_not_applicable(anomaly_service: SystemicAnomalyService):
    """Verify P2P transfers cleanly return NOT_APPLICABLE with zero score."""
    res = anomaly_service.analyze_transaction("TXN_00000203")
    m_scope = res.scopes["merchant"]

    assert m_scope.scope == AnomalyScope.MERCHANT
    assert m_scope.status == "NOT_APPLICABLE"
    assert m_scope.anomaly_detected is False
    assert m_scope.anomaly_score == 0.0
    assert "P2P" in m_scope.reason


def test_merchant_scope_p2m_evaluates_merchant_data(
    anomaly_service: SystemicAnomalyService, db_session: Session
):
    """Verify P2M transaction evaluates real merchant category and risk rating."""
    p2m_tx = (
        db_session.query(Transaction)
        .filter(Transaction.merchant_id.isnot(None))
        .first()
    )
    assert p2m_tx is not None

    res = anomaly_service.analyze_transaction(p2m_tx.transaction_id)
    m_scope = res.scopes["merchant"]

    assert m_scope.scope == AnomalyScope.MERCHANT
    assert m_scope.status in ["NORMAL", "ANOMALOUS"]
    assert len(m_scope.signals) > 0

    sig_names = {s.name for s in m_scope.signals}
    assert "merchant_volume_burst_24h" in sig_names
    assert "merchant_category_risk_rating" in sig_names


# 4. RING / NETWORK ANOMALY
def test_ring_network_anomaly_detected_on_syndicate_hero(anomaly_service: SystemicAnomalyService):
    """Verify hero case TXN_00000203 triggers network coordination anomaly."""
    res = anomaly_service.analyze_transaction("TXN_00000203")
    ring_scope = res.scopes["ring_network"]

    assert ring_scope.scope == AnomalyScope.RING_NETWORK
    assert ring_scope.status == "ANOMALOUS"
    assert ring_scope.anomaly_detected is True
    assert ring_scope.anomaly_score >= 0.60
    assert len(ring_scope.evidence_ids) > 0
    assert any("MULTIHOP" in eid or "DEV" in eid for eid in ring_scope.evidence_ids)


# 5. POSSIBLE SYSTEMIC ANOMALY NON-CAUSAL WORDING
def test_systemic_infrastructure_non_causal_safety_wording(anomaly_service: SystemicAnomalyService):
    """Verify non-causal, evidence-based wording on infrastructure anomaly."""
    res = anomaly_service.analyze_transaction("TXN_00000203")
    infra_scope = res.scopes["systemic_infrastructure"]

    assert infra_scope.scope == AnomalyScope.SYSTEMIC_INFRASTRUCTURE
    assert infra_scope.status == "ANOMALOUS"
    assert "Possible systemic anomaly" in infra_scope.reason
    assert "Elevated infrastructure-level correlation" in infra_scope.reason
    assert "Requires verification" in infra_scope.reason
    assert "Not proof of causal fault or fraud" in infra_scope.reason


# 6. UNAVAILABLE DATA HANDLING (NO FABRICATION)
def test_unavailable_signals_explicitly_flagged(anomaly_service: SystemicAnomalyService):
    """Verify missing signals are represented as UNAVAILABLE, never fabricated."""
    res = anomaly_service.analyze_transaction("TXN_00000203")

    # In Account scope: failure rate is UNAVAILABLE
    acc_signals = {s.name: s for s in res.scopes["account"].signals}
    assert "transaction_failure_rate" in acc_signals
    assert acc_signals["transaction_failure_rate"].status == SignalStatus.UNAVAILABLE
    assert acc_signals["transaction_failure_rate"].value is None

    # In Infrastructure scope: geographic coordinates & PSP entity are UNAVAILABLE
    infra_signals = {s.name: s for s in res.scopes["systemic_infrastructure"].signals}
    assert "geographic_coordinates" in infra_signals
    assert infra_signals["geographic_coordinates"].status == SignalStatus.UNAVAILABLE
    assert infra_signals["geographic_coordinates"].value is None

    assert "psp_gateway_entity" in infra_signals
    assert infra_signals["psp_gateway_entity"].status == SignalStatus.UNAVAILABLE
    assert infra_signals["psp_gateway_entity"].value is None


# 7. EVIDENCE PROVENANCE
def test_evidence_provenance_linkage(anomaly_service: SystemicAnomalyService):
    """Verify evidence IDs trace strictly to Stage 9 EvidenceEngine."""
    res = anomaly_service.analyze_transaction("TXN_00000203")

    assert len(res.all_evidence_ids) > 0
    for eid in res.all_evidence_ids:
        assert eid.startswith("EVD_")


# 8. NO UNSUPPORTED BANK / PSP CAUSAL CLAIMS
def test_no_unsupported_bank_or_psp_causal_accusations(anomaly_service: SystemicAnomalyService):
    """Verify that generated text never claims any bank or PSP caused fraud."""
    test_ids = ["TXN_00000203", "TXN_00000646", "TXN_00000500"]

    forbidden_phrases = [
        "caused the fraud",
        "caused fraud",
        "caused the anomaly",
        "is responsible for fraud",
        "bank caused",
        "psp caused",
        "gateway caused",
        "provider caused",
    ]

    for tid in test_ids:
        res = anomaly_service.analyze_transaction(tid)
        full_text = " ".join([
            res.defense_only_disclaimer,
            *[s.reason for s in res.scopes.values()],
            *[sig.description for s in res.scopes.values() for sig in s.signals]
        ]).lower()

        for phrase in forbidden_phrases:
            assert phrase not in full_text, f"Forbidden causal claim found in {tid}: '{phrase}'"


# 9. HUMAN-IN-THE-LOOP & DEFENSE ONLY
def test_human_in_the_loop_governance(anomaly_service: SystemicAnomalyService):
    """Verify defense-only invariants: human approval required, no autonomous actions."""
    res = anomaly_service.analyze_transaction("TXN_00000203")

    assert res.human_approval_required is True
    assert res.requires_verification is True
    assert "Defense-only decision support" in res.defense_only_disclaimer
    assert "Human verification is strictly required" in res.defense_only_disclaimer


# 10. FASTAPI ENDPOINTS
def test_api_anomaly_health_endpoint(client: TestClient):
    """Verify GET /api/anomaly/health returns operational status."""
    res = client.get("/api/anomaly/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["stage"] == 15
    assert data["defense_only"] is True
    assert data["human_approval_required"] is True


def test_api_anomaly_transaction_endpoint(client: TestClient):
    """Verify GET /api/anomaly/transaction/{id} returns typed response."""
    res = client.get("/api/anomaly/transaction/TXN_00000203")
    assert res.status_code == 200
    data = res.json()

    assert data["transaction_id"] == "TXN_00000203"
    assert "systemic_anomaly_score" in data
    assert "scopes" in data
    assert "account" in data["scopes"]
    assert "merchant" in data["scopes"]
    assert "ring_network" in data["scopes"]
    assert "systemic_infrastructure" in data["scopes"]
    assert data["human_approval_required"] is True


def test_api_anomaly_whitespace_rejection(client: TestClient):
    """Verify invalid/whitespace transaction IDs return HTTP 422."""
    res = client.get("/api/anomaly/transaction/   ")
    assert res.status_code == 422


def test_api_anomaly_not_found(client: TestClient):
    """Verify non-existent transaction IDs return HTTP 404."""
    res = client.get("/api/anomaly/transaction/TXN_NONEXISTENT_999999")
    assert res.status_code == 404
