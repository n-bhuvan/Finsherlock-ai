"""RingGuard AI — Stage 14 Threshold Policy Optimization Tests.

Tests:
1. 4 separate discrete policy scenarios: T*_F1, T*_FPR, T*_Precision, T*_Economic.
2. Infeasibility handling: returns INFEASIBLE_ON_VALIDATION with threshold=None (no fabricated numbers).
3. Post-freeze evaluation: evaluates test set strictly at its own frozen threshold without cross-contamination.
4. Economic sensitivity analysis: 50%, 70%, 85%, 100% tiers computed correctly.
5. Strict economic terminology: modeled loss avoided, modeled friction cost, modeled investigation cost, modeled net value saved.
6. Threshold API endpoint (/api/analytics/threshold-policies) contract: returns 200 OK and Available.
"""

from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient

from ml.evaluation.threshold_optimizer import ThresholdPolicyOptimizer
from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_threshold_optimizer_separate_scenarios():
    """Verify optimizer creates 4 distinct scenario keys."""
    opt = ThresholdPolicyOptimizer()
    y_val = np.array([0, 0, 0, 0, 1, 1, 0, 1, 0, 1])
    p_val = np.array([0.05, 0.1, 0.2, 0.15, 0.8, 0.85, 0.3, 0.75, 0.25, 0.9])
    amounts = np.array([1000, 2000, 1500, 500, 50000, 45000, 1200, 60000, 800, 75000])

    opt.run_validation_sweep(y_val, p_val, amounts)
    assert opt.is_optimized is True

    required_keys = ["T_star_f1", "T_star_fpr", "T_star_precision", "T_star_economic"]
    for k in required_keys:
        assert k in opt.policy_scenarios
        assert "status" in opt.policy_scenarios[k]
        assert "scenario_name" in opt.policy_scenarios[k]

    # Verify T*_Economic is designated as recommended
    assert opt.policy_scenarios["T_star_economic"].get("is_recommended") is True


def test_infeasible_constraint_handling():
    """Verify optimizer returns INFEASIBLE_ON_VALIDATION when constraint is impossible."""
    opt = ThresholdPolicyOptimizer()
    # Pathological data where false positive rate cannot be <= 0.02
    y_val = np.array([0, 0, 0, 0, 1])
    p_val = np.array([0.99, 0.98, 0.97, 0.96, 0.95])  # all negatives scored higher than positive!
    amounts = np.array([1000, 1000, 1000, 1000, 10000])

    opt.run_validation_sweep(y_val, p_val, amounts)
    # Scenario 2 requires FPR <= 0.02
    assert opt.policy_scenarios["T_star_fpr"]["status"] == "INFEASIBLE_ON_VALIDATION"
    assert opt.policy_scenarios["T_star_fpr"]["threshold"] is None

    # Scenario 3 requires Precision >= 0.85
    assert opt.policy_scenarios["T_star_precision"]["status"] == "INFEASIBLE_ON_VALIDATION"
    assert opt.policy_scenarios["T_star_precision"]["threshold"] is None


def test_held_out_test_evaluation_uses_frozen_thresholds():
    """Verify held-out test evaluation uses each policy's own frozen threshold."""
    opt = ThresholdPolicyOptimizer()
    y_val = np.array([0]*10 + [1]*5)
    p_val = np.array([0.1]*10 + [0.9]*5)
    amounts_val = np.array([1000]*15)

    opt.run_validation_sweep(y_val, p_val, amounts_val)

    y_test = np.array([0]*10 + [1]*5)
    p_test = np.array([0.2]*10 + [0.85]*5)
    amounts_test = np.array([2000]*15)

    test_res = opt.evaluate_held_out_test(y_test, p_test, amounts_test)
    for k, res in test_res.items():
        if opt.policy_scenarios[k]["status"] == "FEASIBLE":
            assert res["status"] == "EVALUATED"
            assert res["threshold_applied"] == opt.policy_scenarios[k]["threshold"]
            assert "modeled_net_value_saved" in res["modeled_economics"]
            assert "modeled_loss_avoided" in res["modeled_economics"]
        else:
            assert res["status"] == "NOT_EVALUATED_INFEASIBLE_POLICY"
            assert res["threshold_applied"] is None


def test_economic_sensitivity_tiers():
    """Verify economic sensitivity evaluates 4 distinct tiers (50%, 70%, 85%, 100%)."""
    opt = ThresholdPolicyOptimizer()
    y_val = np.array([0]*10 + [1]*5)
    p_val = np.array([0.1]*10 + [0.9]*5)
    amounts_val = np.array([1000]*10 + [50000]*5)

    opt.run_validation_sweep(y_val, p_val, amounts_val)
    assert len(opt.sensitivity_analysis) == 4

    rates = [t["interception_rate"] for t in opt.sensitivity_analysis]
    assert rates == [0.50, 0.70, 0.85, 1.00]
    for tier in opt.sensitivity_analysis:
        assert "modeled_net_value_saved" in tier
        assert "modeled_loss_avoided" in tier
        assert "is_stable_with_baseline" in tier


def test_threshold_policies_api_endpoint():
    """Verify GET /api/analytics/threshold-policies returns 200 OK and populated structure."""
    client = TestClient(app)
    response = client.get("/api/analytics/threshold-policies")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Available"
    assert "validation_derived_policies" in data
    assert "economic_sensitivity_analysis" in data
    assert "held_out_test_evaluation" in data
    assert "T_star_economic" in data["validation_derived_policies"]


def test_economic_reconciliation_exact_formula():
    """Verify Modeled Net Value Saved strictly equals Loss Avoided - (FP * CFP) - ((TP + FP) * Cinv)."""
    import json
    opt = ThresholdPolicyOptimizer(interception_rate=0.85, fp_friction_cost=1200.0, investigation_cost=350.0)
    y = np.array([0, 0, 0, 1, 1])
    y_pred = np.array([0, 1, 0, 1, 1])  # TN=2, FP=1, FN=0, TP=2
    amounts = np.array([500.0, 1000.0, 1500.0, 20000.0, 30000.0])

    cm = {"true_positives": 2, "false_positives": 1, "true_negatives": 2, "false_negatives": 0}
    econ = opt._compute_economic_value(amounts, y, y_pred, interception=0.85, cm=cm)

    assert econ["tp_count"] == 2
    assert econ["fp_count"] == 1
    assert econ["flagged_case_count"] == 3  # TP + FP
    expected_loss_avoided = round((20000.0 + 30000.0) * 0.85, 2)
    expected_friction = round(1 * 1200.0, 2)
    expected_investigation = round(3 * 350.0, 2)
    expected_net = round(expected_loss_avoided - expected_friction - expected_investigation, 2)

    assert econ["modeled_loss_avoided"] == expected_loss_avoided
    assert econ["modeled_friction_cost"] == expected_friction
    assert econ["modeled_investigation_cost"] == expected_investigation
    assert econ["modeled_net_value_saved"] == expected_net

    # Also test against the loaded threshold_optimization.json
    thresh_file = REPO_ROOT / "ml" / "data" / "evaluation" / "threshold_optimization.json"
    if thresh_file.exists():
        with open(thresh_file, "r", encoding="utf-8") as f:
            artifact = json.load(f)
        for policy_key, eval_data in artifact.get("held_out_test_evaluation", {}).items():
            if eval_data.get("status") == "EVALUATED":
                cm_data = eval_data["metrics"]["confusion_matrix"]
                econ_data = eval_data["modeled_economics"]
                tp = cm_data["true_positives"]
                fp = cm_data["false_positives"]
                cases = tp + fp
                expected_case_cost = round(cases * 350.0, 2)
                expected_fp_cost = round(fp * 1200.0, 2)
                expected_net_saved = round(econ_data["modeled_loss_avoided"] - expected_fp_cost - expected_case_cost, 2)
                assert econ_data["modeled_investigation_cost"] == expected_case_cost
                assert econ_data["modeled_friction_cost"] == expected_fp_cost
                assert econ_data["modeled_net_value_saved"] == expected_net_saved

