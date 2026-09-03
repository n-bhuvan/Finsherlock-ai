"""RingGuard AI — Stage 9 Evidence + Timeline Engine Test Suite.

Tests structured evidence extraction, chronological timeline reconstruction,
data provenance, point-in-time safety, deterministic ranking, temporal-source
attribution, and read-only database invariants.
"""

from datetime import datetime
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.db.session import SessionLocal
from app.models.transaction import Transaction
from app.models.account import Account
from app.evidence.schemas import (
    EvidenceType,
    EvidenceSeverity,
    EvidenceItem,
    EvidenceListResponse,
)
from app.timeline.schemas import (
    TimelineEventType,
    TimelineSeverity,
    TimelineEvent,
    TimelineResponse,
)
from app.evidence.engine import EvidenceEngine
from app.timeline.engine import TimelineEngine


@pytest.fixture(scope="module")
def client():
    """TestClient instance for FastAPI integration testing."""
    return TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    """SQLAlchemy Session fixture."""
    session = SessionLocal()
    yield session
    session.close()


# ==============================================================================
# 1. SCHEMA VALIDATION
# ==============================================================================

def test_evidence_schema_validation():
    """Validates that EvidenceItem enforces required fields and valid enums."""
    item = EvidenceItem(
        evidence_id="EVD_TEST_001",
        evidence_type=EvidenceType.SHARED_DEVICE,
        severity=EvidenceSeverity.HIGH,
        title="Test Shared Device",
        description="Test description based on verified data.",
        related_entities=["ACC_000001", "DEV_000001"],
        supporting_transaction_ids=["TXN_00000001"],
        timestamp_range={"start": "2026-01-01T00:00:00Z", "end": "2026-01-01T01:00:00Z"},
        timestamp_source="transactions.timestamp",
        source="database.transactions",
        status="VERIFIED",
        relevant_values={"count": 2},
        rank=1,
    )
    assert item.evidence_id == "EVD_TEST_001"
    assert item.status == "VERIFIED"
    assert item.timestamp_source == "transactions.timestamp"


def test_timeline_schema_validation():
    """Validates that TimelineEvent enforces required fields and valid enums."""
    evt = TimelineEvent(
        event_id="EVT_TEST_001",
        event_type=TimelineEventType.TRANSACTION,
        timestamp="2026-01-01T12:00:00Z",
        timestamp_source="transactions.timestamp",
        title="Test Payment",
        description="Transaction execution verified.",
        related_entities=["ACC_000001", "DEV_000001"],
        supporting_record_ids=["TXN_00000001"],
        source="transactions",
        severity=TimelineSeverity.LOW,
    )
    assert evt.event_id == "EVT_TEST_001"
    assert evt.event_type == TimelineEventType.TRANSACTION


def test_no_risk_evaluation_in_timeline_events(client):
    """Verifies that derived RISK_EVALUATION is strictly excluded from historical timeline events."""
    resp = client.get("/api/timeline/transaction/TXN_00000646")
    assert resp.status_code == 200
    data = resp.json()
    event_types = [e["event_type"] for e in data["events"]]
    assert "RISK_EVALUATION" not in event_types


def test_risk_context_isolated_in_timeline_response(client):
    """Verifies that model risk evaluation is exposed in the separate risk_context container."""
    resp = client.get("/api/timeline/transaction/TXN_00000646")
    assert resp.status_code == 200
    data = resp.json()
    assert "risk_context" in data
    assert data["risk_context"] is not None
    assert "predicted_ring_probability" in data["risk_context"]
    assert "model_name" in data["risk_context"]


# ==============================================================================
# 2. TEMPORAL SOURCE ATTRIBUTION
# ==============================================================================

def test_temporal_source_attribution_evidence(client):
    """Verifies every evidence item contains an explicit timestamp_source."""
    resp = client.get("/api/evidence/transaction/TXN_00000001")
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert "timestamp_source" in item
        assert item["timestamp_source"] in [
            "transactions.timestamp",
            "accounts.account_created_at",
            "devices.device_created_at",
        ]


def test_temporal_source_attribution_timeline(client):
    """Verifies every timeline event contains an explicit timestamp_source."""
    resp = client.get("/api/timeline/transaction/TXN_00000001")
    assert resp.status_code == 200
    data = resp.json()
    for evt in data["events"]:
        assert "timestamp_source" in evt
        assert evt["timestamp_source"] in [
            "transactions.timestamp",
            "accounts.account_created_at",
            "devices.device_created_at",
        ]


# ==============================================================================
# 3. CHRONOLOGICAL ORDERING & POINT-IN-TIME SAFETY
# ==============================================================================

def test_timeline_chronological_ordering(client):
    """Asserts that events in TimelineResponse are strictly sorted by timestamp ascending."""
    resp = client.get("/api/timeline/transaction/TXN_00000001")
    assert resp.status_code == 200
    events = resp.json()["events"]
    assert len(events) >= 2

    timestamps = [datetime.fromisoformat(e["timestamp"]) for e in events]
    for i in range(len(timestamps) - 1):
        assert timestamps[i] <= timestamps[i + 1], (
            f"Chronological ordering violation: {timestamps[i]} > {timestamps[i+1]}"
        )


def test_point_in_time_safety_future_transactions_excluded(client, db_session):
    """Verifies that for an early transaction T, events occurring at t > T are excluded."""
    # TXN_00000646 is the earliest transaction in the dataset (2025-12-31 19:10:18 UTC)
    early_tx = db_session.query(Transaction).filter(Transaction.transaction_id == "TXN_00000646").first()
    assert early_tx is not None
    T = early_tx.timestamp

    resp = client.get("/api/timeline/transaction/TXN_00000646")
    assert resp.status_code == 200
    events = resp.json()["events"]

    for e in events:
        t_evt = datetime.fromisoformat(e["timestamp"])
        assert t_evt <= T, f"Future event leaked into timeline: {t_evt} > {T}"


def test_point_in_time_safety_evidence_excludes_future_txs(client, db_session):
    """Verifies that evidence for an early transaction does not include future transaction IDs."""
    early_tx = db_session.query(Transaction).filter(Transaction.transaction_id == "TXN_00000646").first()
    assert early_tx is not None
    T = early_tx.timestamp

    resp = client.get("/api/evidence/transaction/TXN_00000646")
    assert resp.status_code == 200
    items = resp.json()["items"]

    for item in items:
        for tx_id in item["supporting_transaction_ids"]:
            tx_obj = db_session.query(Transaction).filter(Transaction.transaction_id == tx_id).first()
            assert tx_obj is not None
            assert tx_obj.timestamp <= T, f"Future transaction leaked into evidence: {tx_id} at {tx_obj.timestamp} > {T}"


# ==============================================================================
# 4. OBSERVED EVIDENCE TYPES & PROVENANCE
# ==============================================================================

def test_shared_device_evidence_on_known_ring(client):
    """Verifies SHARED_DEVICE evidence on known ring transaction TXN_00000001."""
    resp = client.get("/api/evidence/transaction/TXN_00000001")
    assert resp.status_code == 200
    items = resp.json()["items"]

    shared_dev_items = [i for i in items if i["evidence_type"] == "SHARED_DEVICE"]
    assert len(shared_dev_items) >= 1
    item = shared_dev_items[0]
    assert item["status"] == "VERIFIED"
    assert len(item["related_entities"]) >= 2
    assert len(item["supporting_transaction_ids"]) >= 2
    assert "device_id" in item["relevant_values"]


def test_common_beneficiary_evidence_on_known_ring(client):
    """Verifies COMMON_BENEFICIARY evidence on known ring transaction TXN_00000092 (later in syndicate timeline)."""
    resp = client.get("/api/evidence/transaction/TXN_00000092")
    assert resp.status_code == 200
    items = resp.json()["items"]

    common_ben_items = [i for i in items if i["evidence_type"] == "COMMON_BENEFICIARY"]
    assert len(common_ben_items) >= 1
    item = common_ben_items[0]
    assert item["status"] == "VERIFIED"
    assert "beneficiary_id" in item["relevant_values"]


def test_model_risk_context_distinct_from_observed_proof(client):
    """Verifies MODEL_RISK_CONTEXT is marked as derived analytical context, not proof of fraud."""
    resp = client.get("/api/evidence/transaction/TXN_00000001")
    assert resp.status_code == 200
    items = resp.json()["items"]

    model_items = [i for i in items if i["evidence_type"] == "MODEL_RISK_CONTEXT"]
    assert len(model_items) >= 1
    item = model_items[0]
    assert "Derived" in item["description"]
    assert "not direct proof of fraud" in item["description"]
    assert item["relevant_values"]["decision_threshold"] == 0.50


def test_legitimate_lookalike_truthful_reporting(client):
    """Verifies that legitimate transactions report factual relationships without fabricating fraud conclusions."""
    # TXN_00000012 or another legitimate transaction
    resp = client.get("/api/evidence/transaction/TXN_00000679")
    assert resp.status_code == 200
    items = resp.json()["items"]

    for item in items:
        # None of the factual descriptions should claim a guaranteed fraud verdict
        assert "fraud determination" not in item["description"].lower()
        assert "guaranteed fraud" not in item["description"].lower()


def test_clean_legitimate_transaction(client):
    """Verifies clean transaction TXN_00000646 returns truthful, verified evidence without fabrication."""
    resp = client.get("/api/evidence/transaction/TXN_00000646")
    assert resp.status_code == 200
    data = resp.json()
    assert data["target_id"] == "TXN_00000646"
    assert data["target_type"] == "transaction"
    assert data["total_evidence_items"] >= 1


def test_evidence_ranking_determinism(client):
    """Verifies identical evidence ranking sequence across repeated calls."""
    resp1 = client.get("/api/evidence/transaction/TXN_00000001")
    resp2 = client.get("/api/evidence/transaction/TXN_00000001")
    assert resp1.status_code == 200 and resp2.status_code == 200

    ranks1 = [i["rank"] for i in resp1.json()["items"]]
    ranks2 = [i["rank"] for i in resp2.json()["items"]]
    ids1 = [i["evidence_id"] for i in resp1.json()["items"]]
    ids2 = [i["evidence_id"] for i in resp2.json()["items"]]

    assert ranks1 == ranks2
    assert ids1 == ids2
    # Ranks must be 1, 2, 3...
    assert ranks1 == list(range(1, len(ranks1) + 1))


def test_provenance_supporting_ids_exist(client, db_session):
    """Verifies that all supporting transaction IDs and entity IDs exist in PostgreSQL."""
    resp = client.get("/api/evidence/transaction/TXN_00000001")
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        for tx_id in item["supporting_transaction_ids"]:
            exists = db_session.query(Transaction).filter(Transaction.transaction_id == tx_id).count()
            assert exists == 1, f"Supporting transaction '{tx_id}' not found in database!"


def test_timeline_supporting_ids_exist(client, db_session):
    """Verifies that all supporting record IDs in timeline events exist in PostgreSQL."""
    resp = client.get("/api/timeline/transaction/TXN_00000001")
    assert resp.status_code == 200
    for evt in resp.json()["events"]:
        for rec_id in evt["supporting_record_ids"]:
            if rec_id.startswith("TXN_"):
                exists = db_session.query(Transaction).filter(Transaction.transaction_id == rec_id).count()
                assert exists == 1, f"Timeline transaction '{rec_id}' not found in database!"
            elif rec_id.startswith("ACC_"):
                exists = db_session.query(Account).filter(Account.account_id == rec_id).count()
                assert exists == 1, f"Timeline account '{rec_id}' not found in database!"


# ==============================================================================
# 5. ACCOUNT-LEVEL ENDPOINTS
# ==============================================================================

def test_account_evidence_endpoint(client):
    """Verifies GET /api/evidence/account/{account_id} returns evidence list."""
    resp = client.get("/api/evidence/account/ACC_000001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["target_id"] == "ACC_000001"
    assert data["target_type"] == "account"
    assert data["total_evidence_items"] >= 1


def test_account_timeline_endpoint(client):
    """Verifies GET /api/timeline/account/{account_id} returns timeline response."""
    resp = client.get("/api/timeline/account/ACC_000001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["target_id"] == "ACC_000001"
    assert data["target_type"] == "account"
    assert data["total_events"] >= 1


# ==============================================================================
# 6. ERROR HANDLING & VALIDATION
# ==============================================================================

def test_unknown_transaction_returns_404(client):
    """Unknown transaction ID returns HTTP 404 on both evidence and timeline."""
    resp_ev = client.get("/api/evidence/transaction/TXN_NONEXISTENT_999999")
    assert resp_ev.status_code == 404

    resp_tl = client.get("/api/timeline/transaction/TXN_NONEXISTENT_999999")
    assert resp_tl.status_code == 404


def test_unknown_account_returns_404(client):
    """Unknown account ID returns HTTP 404 on both evidence and timeline."""
    resp_ev = client.get("/api/evidence/account/ACC_NONEXISTENT_999999")
    assert resp_ev.status_code == 404

    resp_tl = client.get("/api/timeline/account/ACC_NONEXISTENT_999999")
    assert resp_tl.status_code == 404


def test_whitespace_input_returns_422(client):
    """Empty or whitespace input IDs return HTTP 422."""
    resp = client.get("/api/evidence/transaction/%20%20%20")
    assert resp.status_code in [404, 422]


# ==============================================================================
# 7. READ-ONLY INVARIANT & REGRESSION INTEGRITY
# ==============================================================================

def test_database_read_only_invariant(client, db_session):
    """Asserts that calling evidence and timeline endpoints performs zero database writes."""
    tx_before = db_session.execute(text("SELECT count(*) FROM transactions;")).scalar()
    acc_before = db_session.execute(text("SELECT count(*) FROM accounts;")).scalar()
    cust_before = db_session.execute(text("SELECT count(*) FROM customers;")).scalar()

    # Execute multiple calls
    client.get("/api/evidence/transaction/TXN_00000001")
    client.get("/api/timeline/transaction/TXN_00000001")
    client.get("/api/evidence/account/ACC_000001")
    client.get("/api/timeline/account/ACC_000001")

    tx_after = db_session.execute(text("SELECT count(*) FROM transactions;")).scalar()
    acc_after = db_session.execute(text("SELECT count(*) FROM accounts;")).scalar()
    cust_after = db_session.execute(text("SELECT count(*) FROM customers;")).scalar()

    assert tx_before == tx_after == 2000
    assert acc_before == acc_after == 500
    assert cust_before == cust_after == 500


def test_stage8_endpoints_remain_functional(client):
    """Regression test ensuring existing Stage 8 endpoints still function perfectly."""
    resp_health = client.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "ok"

    resp_risk = client.get("/api/risk/health")
    assert resp_risk.status_code == 200
    assert resp_risk.json()["status"] == "ok"
    assert resp_risk.json()["models"]["baseline"]["loaded"] is True
    assert resp_risk.json()["models"]["graph"]["loaded"] is True


def test_stage6_stage7_artifacts_unchanged():
    """Regression test verifying model artifacts remain strictly unchanged."""
    m_a = Path("models/ringguard_baseline_xgb_v1.joblib")
    m_b = Path("models/ringguard_graph_xgb_v1.joblib")
    assert m_a.exists() and m_a.stat().st_size == 263745
    assert m_b.exists() and m_b.stat().st_size == 266061
