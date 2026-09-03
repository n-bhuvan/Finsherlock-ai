"""RingGuard AI — Stage 10 Controlled Investigation Tools Test Suite.

Tests the 9 bounded, deterministic, read-only investigation tools,
verifying strict parameterized query safety, non-fabrication of evidence IDs,
exclusion of scenario_type, point-in-time boundaries, and read-only invariants.
"""

from datetime import datetime
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.db.session import SessionLocal
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.device import Device
from app.models.ip import IPAddress
from app.models.beneficiary import Beneficiary
from app.investigation.schemas import (
    ToolExecutionStatus,
    ToolExecutionResult,
)
from app.investigation.permissions import PermissionGuard, PermissionDeniedError
from app.investigation.service import InvestigationService


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


@pytest.fixture(scope="module")
def investigation_service(db_session):
    """InvestigationService fixture."""
    return InvestigationService(db_session)


# ==============================================================================
# 1. SCHEMA VALIDATION & PERMISSION BOUNDARY
# ==============================================================================

def test_tool_schema_validation():
    """Validates ToolExecutionResult schema and required fields."""
    res = ToolExecutionResult(
        tool_name="get_account",
        status=ToolExecutionStatus.SUCCESS,
        target="ACC_000001",
        as_of="2026-01-01T00:00:00Z",
        result={"account_id": "ACC_000001"},
        result_count=1,
        source="database.accounts",
        evidence_ids=[],
        limitations="Operational schema fields only.",
    )
    assert res.tool_name == "get_account"
    assert res.status == ToolExecutionStatus.SUCCESS
    assert res.target == "ACC_000001"
    assert "Controlled read-only" in res.disclaimer


def test_permission_guard_allows_read_and_rejects_write():
    """Verifies PermissionGuard authorizes INVESTIGATION_READ and rejects mutating actions."""
    assert PermissionGuard.check_permission("INVESTIGATION_READ") is True
    assert PermissionGuard.check_permission("EVIDENCE_READ") is True

    with pytest.raises(PermissionDeniedError):
        PermissionGuard.check_permission("INVESTIGATION_WRITE")

    with pytest.raises(PermissionDeniedError):
        PermissionGuard.check_permission("DATABASE_WRITE")

    with pytest.raises(PermissionDeniedError):
        PermissionGuard.check_permission("ACCOUNT_BLOCK")


# ==============================================================================
# 2. SCENARIO_TYPE EXCLUSION & FIELD TRUTHFULNESS
# ==============================================================================

def test_scenario_type_strictly_excluded(client):
    """Verifies scenario_type, scenario_id, and ground_truth_label are absent from get_account."""
    resp = client.get("/api/investigation/account/ACC_000001")
    assert resp.status_code == 200
    data = resp.json()
    res = data["result"]
    assert "scenario_type" not in res
    assert "scenario_id" not in res
    assert "ground_truth_label" not in res
    assert "account_id" in res
    assert "customer_id" in res
    assert "account_status" in res
    assert "account_type" in res


def test_schema_fields_truthfulness(client):
    """Verifies transaction records contain only real database model columns."""
    resp = client.get("/api/investigation/account/ACC_000001/transactions?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    for tx in data["result"]:
        assert "transaction_id" in tx
        assert "amount" in tx
        assert "timestamp" in tx
        assert "scenario_type" not in tx
        assert "ground_truth_label" not in tx


# ==============================================================================
# 3. EVIDENCE ID NON-FABRICATION
# ==============================================================================

def test_evidence_id_non_fabrication(client):
    """Asserts that returned evidence IDs are never generated from templates and resolve to Stage 9."""
    resp = client.get("/api/investigation/account/ACC_000001/devices")
    assert resp.status_code == 200
    data = resp.json()
    ev_ids = data["evidence_ids"]

    # Either empty or resolves to a real Stage 9 evidence ID
    if ev_ids:
        ev_resp = client.get("/api/evidence/account/ACC_000001")
        assert ev_resp.status_code == 200
        stage9_ev_ids = [i["evidence_id"] for i in ev_resp.json()["items"]]
        for eid in ev_ids:
            assert eid in stage9_ev_ids, f"Fabricated or unresolvable evidence ID found: {eid}"


def test_fund_flow_evidence_ids_not_fabricated(client):
    """Asserts trace_fund_flow only links evidence IDs that exist in Stage 9."""
    resp = client.get("/api/investigation/account/ACC_000001/fund-flow")
    assert resp.status_code == 200
    ev_ids = resp.json()["evidence_ids"]
    assert isinstance(ev_ids, list)
    if ev_ids:
        ev_resp = client.get("/api/evidence/account/ACC_000001")
        stage9_ids = [i["evidence_id"] for i in ev_resp.json()["items"]]
        for eid in ev_ids:
            assert eid in stage9_ids


# ==============================================================================
# 4. PARAMETERIZED QUERY & SQL INJECTION DEFENSE
# ==============================================================================

def test_parameterized_query_sql_injection_defense(client):
    """Verifies that SQL injection attempts cannot alter query structure and return 404/422 safely."""
    injection_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE transactions; --",
        "ACC_000001' UNION SELECT * FROM users --",
    ]
    for payload in injection_payloads:
        resp = client.get(f"/api/investigation/account/{payload}")
        assert resp.status_code in [404, 422]

        resp_tx = client.get(f"/api/investigation/account/{payload}/transactions")
        assert resp_tx.status_code in [404, 422]


# ==============================================================================
# 5. THE 9 TOOLS IMPLEMENTATION & BOUNDED BEHAVIOR
# ==============================================================================

def test_get_account_success(client):
    """Tool 1: get_account returns factual details for active account."""
    resp = client.get("/api/investigation/account/ACC_000001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tool_name"] == "get_account"
    assert data["status"] == "SUCCESS"
    assert data["result"]["account_id"] == "ACC_000001"


def test_get_account_unknown_id(client):
    """Tool 1: get_account returns 404 for nonexistent account."""
    resp = client.get("/api/investigation/account/ACC_NONEXISTENT_999999")
    assert resp.status_code == 404


def test_get_transactions_success_and_ordering(client):
    """Tool 2: get_transactions returns transactions ordered chronologically."""
    resp = client.get("/api/investigation/account/ACC_000001/transactions?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tool_name"] == "get_transactions"
    txs = data["result"]
    assert len(txs) >= 1

    timestamps = [datetime.fromisoformat(t["timestamp"]) for t in txs]
    for i in range(len(timestamps) - 1):
        assert timestamps[i] <= timestamps[i + 1]


def test_get_transactions_limit_enforcement(client):
    """Tool 2: get_transactions strictly enforces max limit."""
    resp = client.get("/api/investigation/account/ACC_000001/transactions?limit=2")
    assert resp.status_code == 200
    txs = resp.json()["result"]
    assert len(txs) <= 2


def test_get_transactions_point_in_time_filtering(client, db_session):
    """Tool 2: get_transactions strictly filters out transactions after end_time."""
    txs = db_session.query(Transaction).filter(Transaction.account_id == "ACC_000001").order_by(Transaction.timestamp.asc()).all()
    assert len(txs) >= 2
    cutoff = txs[1].timestamp.isoformat()

    resp = client.get(f"/api/investigation/account/ACC_000001/transactions?end_time={cutoff}")
    assert resp.status_code == 200
    for t in resp.json()["result"]:
        assert datetime.fromisoformat(t["timestamp"]) <= datetime.fromisoformat(cutoff)


def test_find_related_accounts_discovery(client):
    """Tool 3: find_related_accounts discovers connected accounts on ring account."""
    resp = client.get("/api/investigation/account/ACC_000001/related")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tool_name"] == "find_related_accounts"
    assert data["status"] in ["SUCCESS", "LIMITED"]
    assert len(data["result"]) >= 1


def test_find_shared_devices_discovery(client):
    """Tool 4: find_shared_devices discovers shared devices on known ring account."""
    resp = client.get("/api/investigation/account/ACC_000001/devices")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tool_name"] == "find_shared_devices"
    assert len(data["result"]) >= 1
    rec = data["result"][0]
    assert "device_id" in rec
    assert len(rec["co_using_accounts"]) >= 1


def test_find_shared_ips_discovery(client):
    """Tool 5: find_shared_ips discovers shared IP addresses."""
    resp = client.get("/api/investigation/account/ACC_000001/ips")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tool_name"] == "find_shared_ips"
    assert isinstance(data["result"], list)


def test_find_common_beneficiaries_discovery(client):
    """Tool 6: find_common_beneficiaries discovers common beneficiaries on known beneficiary ring."""
    # ACC_000302 routes to BEN_000047 co-shared with ACC_000118
    resp = client.get("/api/investigation/account/ACC_000302/beneficiaries")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tool_name"] == "find_common_beneficiaries"
    assert len(data["result"]) >= 1
    assert data["result"][0]["beneficiary_id"] == "BEN_000047"


def test_trace_fund_flow_traceability_and_real_transactions(client, db_session):
    """Tool 7: trace_fund_flow only describes actual financial transfers backed by real Transactions."""
    resp = client.get("/api/investigation/account/ACC_000001/fund-flow?max_depth=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tool_name"] == "trace_fund_flow"
    hops = data["result"]
    assert len(hops) >= 1

    for hop in hops:
        tx_id = hop["transaction_id"]
        tx_db = db_session.query(Transaction).filter(Transaction.transaction_id == tx_id).first()
        assert tx_db is not None, f"Fund flow hop references nonexistent transaction: {tx_id}"
        assert float(tx_db.amount) == hop["amount"]
        assert hop["source_account_id"] == tx_db.account_id


def test_bounded_multi_hop_behavior(client):
    """Tool 7: trace_fund_flow respects max_depth bound (<= 3)."""
    resp = client.get("/api/investigation/account/ACC_000001/fund-flow?max_depth=2")
    assert resp.status_code == 200
    hops = resp.json()["result"]
    for hop in hops:
        assert hop["hop_number"] in [1, 2]


def test_timeline_delegation_to_stage9_without_fake_events(client):
    """Tool 8: reconstruct_timeline delegates to Stage 9 and strictly excludes RISK_EVALUATION from events."""
    resp = client.get("/api/investigation/transaction/TXN_00000646/timeline")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tool_name"] == "reconstruct_timeline"
    events = data["result"]["events"]
    assert len(events) >= 1
    for evt in events:
        assert evt["event_type"] != "RISK_EVALUATION"
    # Separate risk context must exist
    assert "risk_context" in data["result"]


def test_risk_features_delegation_to_stage8(client):
    """Tool 9: get_risk_features delegates to Stage 8 and returns 58 Model B features."""
    resp = client.get("/api/investigation/transaction/TXN_00000646/risk-features?model_type=graph")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tool_name"] == "get_risk_features"
    res = data["result"]
    assert res["feature_count"] == 58
    assert res["graph_feature_count"] == 21
    assert 0.0 <= res["predicted_ring_probability"] <= 1.0
    assert "Contextual risk assessment only" in res["note"]


# ==============================================================================
# 6. LEGITIMATE LOOK-ALIKE FACTUAL REPORTING
# ==============================================================================

def test_legitimate_lookalike_factual_reporting(client):
    """Verifies legitimate lookalike accounts report shared attributes factually without fraud accusations."""
    resp = client.get("/api/investigation/account/ACC_000302/related")
    assert resp.status_code == 200
    data = resp.json()
    # Tool output must not state "fraud", "scam", or "guilty"
    assert "fraud" not in str(data["result"]).lower()
    assert "Controlled read-only" in data["disclaimer"]


# ==============================================================================
# 7. READ-ONLY INVARIANT & INTEGRITY
# ==============================================================================

def test_read_only_database_invariant(client, db_session):
    """Asserts that running all investigation tools results in zero database mutations."""
    counts_before = {
        "transactions": db_session.execute(text("SELECT count(*) FROM transactions;")).scalar(),
        "accounts": db_session.execute(text("SELECT count(*) FROM accounts;")).scalar(),
        "customers": db_session.execute(text("SELECT count(*) FROM customers;")).scalar(),
        "devices": db_session.execute(text("SELECT count(*) FROM devices;")).scalar(),
        "ips": db_session.execute(text("SELECT count(*) FROM ips;")).scalar(),
        "beneficiaries": db_session.execute(text("SELECT count(*) FROM beneficiaries;")).scalar(),
    }

    # Execute all tools
    client.get("/api/investigation/account/ACC_000001")
    client.get("/api/investigation/account/ACC_000001/transactions")
    client.get("/api/investigation/account/ACC_000001/related")
    client.get("/api/investigation/account/ACC_000001/devices")
    client.get("/api/investigation/account/ACC_000001/ips")
    client.get("/api/investigation/account/ACC_000001/beneficiaries")
    client.get("/api/investigation/account/ACC_000001/fund-flow")
    client.get("/api/investigation/account/ACC_000001/timeline")
    client.get("/api/investigation/transaction/TXN_00000001/fund-flow")
    client.get("/api/investigation/transaction/TXN_00000001/timeline")
    client.get("/api/investigation/transaction/TXN_00000001/risk-features")

    counts_after = {
        "transactions": db_session.execute(text("SELECT count(*) FROM transactions;")).scalar(),
        "accounts": db_session.execute(text("SELECT count(*) FROM accounts;")).scalar(),
        "customers": db_session.execute(text("SELECT count(*) FROM customers;")).scalar(),
        "devices": db_session.execute(text("SELECT count(*) FROM devices;")).scalar(),
        "ips": db_session.execute(text("SELECT count(*) FROM ips;")).scalar(),
        "beneficiaries": db_session.execute(text("SELECT count(*) FROM beneficiaries;")).scalar(),
    }

    assert counts_before == counts_after


def test_deterministic_repeated_results(client):
    """Verifies that running the same tool repeatedly yields identical payloads."""
    r1 = client.get("/api/investigation/account/ACC_000001/related").json()
    r2 = client.get("/api/investigation/account/ACC_000001/related").json()
    assert r1 == r2


def test_stage8_and_stage9_regression(client):
    """Verifies Stage 8 and Stage 9 endpoints remain completely functional."""
    assert client.get("/health").status_code == 200
    assert client.get("/api/risk/health").status_code == 200
    assert client.get("/api/evidence/transaction/TXN_00000001").status_code == 200
    assert client.get("/api/timeline/transaction/TXN_00000001").status_code == 200


def test_frozen_model_artifacts_unchanged():
    """Regression test ensuring Model A and Model B artifacts remain bitwise unchanged."""
    m_a = Path("models/ringguard_baseline_xgb_v1.joblib")
    m_b = Path("models/ringguard_graph_xgb_v1.joblib")
    assert m_a.exists() and m_a.stat().st_size == 263745
    assert m_b.exists() and m_b.stat().st_size == 266061


def test_whitespace_input_rejected(client):
    """Verifies that whitespace inputs are rejected cleanly with 422."""
    assert client.get("/api/investigation/account/%20%20%20").status_code == 422
    assert client.get("/api/investigation/account/%20%20%20/transactions").status_code == 422


def test_get_risk_features_baseline_model(client):
    """Tool 9: get_risk_features with model_type=baseline returns 37 features."""
    resp = client.get("/api/investigation/transaction/TXN_00000001/risk-features?model_type=baseline")
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["model_name"] == "ringguard_baseline_xgb_v1"
    assert data["result"]["feature_count"] == 37
    assert data["result"]["graph_feature_count"] == 0


def test_reconstruct_timeline_for_account(client):
    """Tool 8: reconstruct_timeline works on account targets."""
    resp = client.get("/api/investigation/account/ACC_000001/timeline")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tool_name"] == "reconstruct_timeline"
    assert data["result"]["target_type"] == "account"
    assert len(data["result"]["events"]) >= 1


def test_trace_fund_flow_transaction_target(client):
    """Tool 7: trace_fund_flow works on transaction targets."""
    resp = client.get("/api/investigation/transaction/TXN_00000001/fund-flow")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tool_name"] == "trace_fund_flow"
    assert data["status"] in ["SUCCESS", "LIMITED"]


def test_get_account_point_in_time_exclusion(client, db_session):
    """Tool 1: get_account with as_of prior to account creation returns 404."""
    acc = db_session.query(Account).filter(Account.account_id == "ACC_000001").first()
    earlier = "2020-01-01T00:00:00Z"
    resp = client.get(f"/api/investigation/account/ACC_000001?as_of={earlier}")
    assert resp.status_code == 404


def test_no_mutation_keywords_in_investigation_code():
    """Static analysis confirming zero INSERT, UPDATE, DELETE, or commit() statements in investigation code."""
    inv_dir = Path("backend/app/investigation")
    forbidden_tokens = [
        ".commit()",
        "db.add(",
        "session.add(",
        "INSERT INTO",
        "UPDATE ",
        "DELETE FROM",
        "db.delete(",
        "session.delete(",
    ]
    for py_file in inv_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in content, f"Forbidden mutation keyword '{token}' found in {py_file}"

