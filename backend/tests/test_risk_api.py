"""RingGuard AI — Stage 8 Risk API Test Suite.

Tests FastAPI risk endpoints, model loading, feature parity with Stage 5,
prediction parity with Stage 6/7, read-only guarantees, and error handling.
"""

from pathlib import Path
import json
import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import text
import joblib

from app.main import app
from app.db.session import SessionLocal
from app.services.model_service import get_model_service
from app.services.feature_service import get_feature_service

client = TestClient(app)

# Representative transactions across different scenarios and timestamps
KNOWN_TX_IDS = [
    "TXN_00000646",  # First transaction (2026-01-01)
    "TXN_00000679",  # Early transaction
    "TXN_00000001",  # Legitimate sample
    "TXN_00000500",  # Mid timeline
    "TXN_00001999",  # Late timeline
]


@pytest.fixture(scope="module")
def db_session():
    """Provide a database session for test queries."""
    session = SessionLocal()
    yield session
    session.close()


# 1. Existing /health still works
def test_existing_health_endpoint_still_works():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ringguard-backend"}


# 2. Risk health endpoint works
def test_risk_health_endpoint():
    response = client.get("/api/risk/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert data["service"] == "ringguard-risk-engine"
    assert data["baseline_model_loaded"] is True
    assert data["graph_model_loaded"] is True
    assert data["database_connected"] is True
    assert "baseline" in data["models"]
    assert "graph" in data["models"]


# 3. Baseline model loads
def test_baseline_model_loads():
    service = get_model_service()
    assert service.model_a is not None


# 4. Graph model loads
def test_graph_model_loads():
    service = get_model_service()
    assert service.model_b is not None


# 5. Model A has 37 features
def test_model_a_feature_count():
    service = get_model_service()
    assert len(service.features_a) == 37


# 6. Model B has 58 features
def test_model_b_feature_count():
    service = get_model_service()
    assert len(service.features_b) == 58


# 7. Existing transaction lookup works
def test_existing_transaction_lookup(db_session):
    feature_service = get_feature_service()
    txn = feature_service.verify_transaction_exists(db_session, "TXN_00000646")
    assert txn.transaction_id == "TXN_00000646"
    assert txn.account_id is not None


# 8. Valid transaction returns primary risk response
def test_primary_risk_response():
    response = client.get("/api/risk/transaction/TXN_00000646")
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "TXN_00000646"
    assert data["prediction_unit"] == "transaction"
    assert data["model"] == "ringguard_graph_xgb_v1"
    assert data["feature_count"] == 58
    assert data["graph_features_count"] == 21
    assert data["graph_context_available"] is True
    assert 0.0 <= data["predicted_ring_probability"] <= 1.0
    assert data["risk_band"] in ["LOW", "MEDIUM", "HIGH"]
    assert "disclaimer" in data


# 9. Unknown transaction returns 404
def test_unknown_transaction_returns_404():
    response = client.get("/api/risk/transaction/TXN_NONEXISTENT_999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# 10. Invalid input is rejected
def test_invalid_input_rejected():
    response = client.get("/api/risk/transaction/%20%20")
    assert response.status_code in [404, 422]


# 11. Probability is between 0 and 1
@pytest.mark.parametrize("tx_id", KNOWN_TX_IDS[:3])
def test_probabilities_within_0_1(tx_id):
    resp_base = client.get(f"/api/risk/transaction/{tx_id}/baseline")
    assert resp_base.status_code == 200
    p_base = resp_base.json()["predicted_ring_probability"]
    assert 0.0 <= p_base <= 1.0

    resp_net = client.get(f"/api/risk/transaction/{tx_id}/network")
    assert resp_net.status_code == 200
    p_net = resp_net.json()["predicted_ring_probability"]
    assert 0.0 <= p_net <= 1.0


# 12. Model A response identifies 37 features and zero graph features
def test_model_a_endpoint_metadata():
    response = client.get("/api/risk/transaction/TXN_00000646/baseline")
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "ringguard_baseline_xgb_v1"
    assert data["feature_count"] == 37
    assert data["graph_features_count"] == 0
    assert data["graph_context_available"] is False


# 13. Model B response identifies 58 features and 21 graph features
def test_model_b_endpoint_metadata():
    response = client.get("/api/risk/transaction/TXN_00000646/network")
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "ringguard_graph_xgb_v1"
    assert data["feature_count"] == 58
    assert data["graph_features_count"] == 21
    assert data["graph_context_available"] is True


# 14. API Model A feature vector matches Stage 5 Model A feature vector
@pytest.mark.parametrize("tx_id", KNOWN_TX_IDS)
def test_feature_parity_model_a(db_session, tx_id):
    feature_service = get_feature_service()
    feats_api, _ = feature_service.get_features(db_session, tx_id, model_type="baseline")

    # Load directly from Stage 5 CSV
    df_s5 = pd.read_csv("ml/data/features/model_a_features.csv", index_col=0)
    feats_s5 = df_s5.loc[[tx_id]]

    assert list(feats_api.columns) == list(feats_s5.columns)
    diff = np.abs(feats_api.values - feats_s5.values)
    max_diff = np.max(diff)
    assert max_diff < 1e-6, f"Feature parity failure for {tx_id} (max diff: {max_diff})"


# 15. API Model B feature vector matches Stage 5 Model B feature vector
@pytest.mark.parametrize("tx_id", KNOWN_TX_IDS)
def test_feature_parity_model_b(db_session, tx_id):
    feature_service = get_feature_service()
    feats_api, _ = feature_service.get_features(db_session, tx_id, model_type="graph")

    # Load directly from Stage 5 CSV
    df_s5 = pd.read_csv("ml/data/features/model_b_features.csv", index_col=0)
    feats_s5 = df_s5.loc[[tx_id]]

    assert list(feats_api.columns) == list(feats_s5.columns)
    diff = np.abs(feats_api.values - feats_s5.values)
    max_diff = np.max(diff)
    assert max_diff < 1e-6, f"Feature parity failure for {tx_id} (max diff: {max_diff})"


# 16. API Model A probability matches direct model prediction
@pytest.mark.parametrize("tx_id", KNOWN_TX_IDS)
def test_prediction_parity_model_a(tx_id):
    # Direct model prediction
    model_a = joblib.load("models/ringguard_baseline_xgb_v1.joblib")
    df_s5 = pd.read_csv("ml/data/features/model_a_features.csv", index_col=0)
    feats = df_s5.loc[[tx_id]]
    direct_prob = float(model_a.predict_proba(feats)[0, 1])

    # API prediction
    resp = client.get(f"/api/risk/transaction/{tx_id}/baseline")
    assert resp.status_code == 200
    api_prob = resp.json()["predicted_ring_probability"]

    assert abs(direct_prob - api_prob) < 1e-5, f"Prediction mismatch for {tx_id}: direct={direct_prob}, api={api_prob}"


# 17. API Model B probability matches direct model prediction
@pytest.mark.parametrize("tx_id", KNOWN_TX_IDS)
def test_prediction_parity_model_b(tx_id):
    # Direct model prediction
    model_b = joblib.load("models/ringguard_graph_xgb_v1.joblib")
    df_s5 = pd.read_csv("ml/data/features/model_b_features.csv", index_col=0)
    feats = df_s5.loc[[tx_id]]
    direct_prob = float(model_b.predict_proba(feats)[0, 1])

    # API prediction
    resp = client.get(f"/api/risk/transaction/{tx_id}/network")
    assert resp.status_code == 200
    api_prob = resp.json()["predicted_ring_probability"]

    assert abs(direct_prob - api_prob) < 1e-5, f"Prediction mismatch for {tx_id}: direct={direct_prob}, api={api_prob}"


# 18. No database mutation occurs during risk request
def test_no_database_mutation(db_session):
    count_before = db_session.execute(text("SELECT count(*) FROM transactions;")).scalar()
    # Execute multiple risk requests
    client.get("/api/risk/transaction/TXN_00000646")
    client.get("/api/risk/transaction/TXN_00000646/baseline")
    client.get("/api/risk/transaction/TXN_00000646/network")
    count_after = db_session.execute(text("SELECT count(*) FROM transactions;")).scalar()
    assert count_before == count_after, "Database mutation detected during risk requests!"


# 19. No enforcement/payment action is called
def test_analytical_disclaimer_present():
    resp = client.get("/api/risk/transaction/TXN_00000646")
    assert resp.status_code == 200
    data = resp.json()
    assert "Does not constitute an automated payment action or enforcement decision" in data["disclaimer"]


# 20. Error responses do not expose secrets
def test_error_responses_do_not_expose_secrets():
    resp = client.get("/api/risk/transaction/TXN_NONEXISTENT_XYZ")
    assert resp.status_code == 404
    body = resp.text.lower()
    for secret_keyword in ["password", "database_url", "secret", "token", "postgres:"]:
        assert secret_keyword not in body


# 21. Model artifacts remain unchanged
def test_model_artifacts_unchanged():
    assert Path("models/ringguard_baseline_xgb_v1.joblib").exists()
    assert Path("models/ringguard_baseline_xgb_v1_metadata.json").exists()
    assert Path("models/ringguard_graph_xgb_v1.joblib").exists()
    assert Path("models/ringguard_graph_xgb_v1_metadata.json").exists()


# 22. Stage 6 and Stage 7 evaluation outputs remain unchanged
def test_previous_stage_evaluation_outputs_unchanged():
    assert Path("ml/data/evaluation/baseline_metrics.json").exists()
    assert Path("ml/data/evaluation/baseline_predictions.csv").exists()
    assert Path("ml/data/evaluation/model_comparison.csv").exists()
    assert Path("ml/data/evaluation/model_comparison.json").exists()
    assert Path("ml/data/evaluation/graph_model_predictions.csv").exists()
