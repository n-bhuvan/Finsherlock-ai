"""RingGuard AI — Stage 12 Business Economics Test Suite.

Tests transparent separation of observed benchmark data, user modeling assumptions,
and derived economic calculations (Net Value Saved = Estimated Loss Avoided - Friction - Investigation).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_business_economics_default_parameters():
    """Verify economics endpoint with default operational parameters."""
    response = client.get("/api/analytics/economics")
    assert response.status_code == 200
    data = response.json()

    # 1. Observed benchmark values (exact verified database numbers)
    obs = data["observed_benchmark_values"]
    assert obs["total_evaluated_transactions"] == 2000
    assert obs["total_ring_fraud_transactions"] == 233
    assert obs["total_ring_fraud_accounts"] == 72
    assert obs["total_ring_fraud_exposure_inr"] == 7864287.0
    assert obs["synthetic_held_out_false_positive_rate"] == 0.0

    # 2. Operational modeling assumptions
    assump = data["operational_modeling_assumptions"]
    assert assump["interception_rate"] == 0.85
    assert assump["cost_per_investigation_inr"] == 350.0
    assert assump["friction_cost_per_false_positive_inr"] == 1200.0

    # 3. Derived economic estimates
    derived = data["derived_economic_estimates"]
    expected_loss_avoided = round(7864287.0 * 0.85, 2)
    expected_inv_cost = round(233 * 350.0, 2)
    expected_friction_cost = round(0 * 1200.0, 2)
    expected_net_value = round(expected_loss_avoided - expected_friction_cost - expected_inv_cost, 2)

    assert derived["estimated_fraud_loss_avoided_inr"] == expected_loss_avoided
    assert derived["total_investigation_cost_inr"] == expected_inv_cost
    assert derived["total_friction_cost_inr"] == expected_friction_cost
    assert derived["net_value_saved_inr"] == expected_net_value
    assert derived["roi_multiple"] > 0.0

    # 4. Disclaimers
    assert any("audited RingGuard synthetic benchmark dataset" in d for d in data["disclaimers"])
    assert any("Estimated Fraud Loss Avoided" in d for d in data["disclaimers"])


def test_business_economics_custom_parameters():
    """Verify economics calculations adapt accurately to custom inputs."""
    params = {
        "interception_rate": 0.90,
        "cost_per_investigation": 500.0,
        "friction_cost_per_fp": 2000.0,
    }
    response = client.get("/api/analytics/economics", params=params)
    assert response.status_code == 200
    data = response.json()

    assump = data["operational_modeling_assumptions"]
    assert assump["interception_rate"] == 0.90
    assert assump["cost_per_investigation_inr"] == 500.0
    assert assump["friction_cost_per_false_positive_inr"] == 2000.0

    derived = data["derived_economic_estimates"]
    expected_loss_avoided = round(7864287.0 * 0.90, 2)
    expected_inv_cost = round(233 * 500.0, 2)
    expected_net_value = round(expected_loss_avoided - expected_inv_cost, 2)

    assert derived["estimated_fraud_loss_avoided_inr"] == expected_loss_avoided
    assert derived["total_investigation_cost_inr"] == expected_inv_cost
    assert derived["net_value_saved_inr"] == expected_net_value


def test_business_economics_validation_bounds():
    """Verify input parameter validation limits."""
    # Out of range interception rate (> 1.0)
    resp = client.get("/api/analytics/economics?interception_rate=1.5")
    assert resp.status_code == 422

    # Below minimum cost per investigation (< 100.0)
    resp = client.get("/api/analytics/economics?cost_per_investigation=50")
    assert resp.status_code == 422
