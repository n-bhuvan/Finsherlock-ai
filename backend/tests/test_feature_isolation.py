"""RingGuard AI — Stage 12 Feature Isolation Test Suite.

Tests the in-silico feature isolation / sensitivity analysis endpoint,
mathematically valid baseline substitutions, provenance-grounded evidence mapping,
and explicit scientific disclaimers.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_feature_isolation_hero_case_txn_00000203():
    """Verify feature isolation on primary hero case TXN_00000203."""
    response = client.get("/api/risk/transaction/TXN_00000203/feature-isolation")
    assert response.status_code == 200
    data = response.json()

    assert data["transaction_id"] == "TXN_00000203"
    assert 0.99 <= data["original_probability"] <= 1.0
    assert 0.0 <= data["isolated_probability"] <= 1.0
    assert data["risk_band_original"] == "HIGH"
    assert data["isolated_features_count"] == 21
    assert len(data["isolated_features"]) == 21

    # Exact mathematical delta
    expected_delta = round(data["original_probability"] - data["isolated_probability"], 8)
    assert abs(data["delta"] - expected_delta) < 1e-6
    expected_pct_delta = round(expected_delta * 100.0, 4)
    assert abs(data["percentage_point_delta"] - expected_pct_delta) < 1e-4

    # Baseline values sanity check (Stage 5 semantics)
    baselines = data["baseline_values_used"]
    assert baselines["g_in_degree"] == 1.0
    assert baselines["g_device_count"] == 1.0
    assert baselines["g_ip_count"] == 1.0
    assert baselines["g_connected_accounts_count"] == 0.0
    assert baselines["g_shared_device_accounts_count"] == 0.0
    assert baselines["g_has_shared_device"] == 0.0
    assert baselines["g_component_size"] >= 5.0

    # Methodology & scientific limitations disclosures
    assert "In-silico model feature-isolation" in data["methodology"]
    assert any("not a causal intervention" in lim for lim in data["limitations"])
    assert any("delta 0.0000" in lim for lim in data["limitations"])

    # Attributions structure
    assert len(data["attributions"]) > 0
    top_attr = data["attributions"][0]
    assert "feature_name" in top_attr
    assert "importance_rank_in_model_b" in top_attr
    assert "provenance_status" in top_attr


def test_feature_isolation_control_case_txn_00000646():
    """Verify feature isolation on low-risk control case TXN_00000646."""
    response = client.get("/api/risk/transaction/TXN_00000646/feature-isolation")
    assert response.status_code == 200
    data = response.json()

    assert data["transaction_id"] == "TXN_00000646"
    assert data["original_probability"] < 0.20
    assert data["risk_band_original"] == "LOW"
    assert data["risk_band_isolated"] == "LOW"
    assert data["isolated_features_count"] == 21


def test_feature_isolation_nonexistent_transaction():
    """Verify 404 returned for nonexistent transaction."""
    response = client.get("/api/risk/transaction/TXN_DOES_NOT_EXIST/feature-isolation")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_feature_isolation_whitespace_id():
    """Verify 422 returned for empty/whitespace transaction ID."""
    response = client.get("/api/risk/transaction/%20%20/feature-isolation")
    assert response.status_code in (404, 422)
