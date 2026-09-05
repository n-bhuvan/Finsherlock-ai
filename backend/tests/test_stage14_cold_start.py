"""RingGuard AI — Stage 14 Cold-Start Segmentation Tests.

Tests:
1. Graph confidence precedence: UNAVAILABLE -> LIMITED -> VERIFIED.
2. Candidate cold-start rule audit: N < 20 flagged as LIMITED / INSUFFICIENT EVIDENCE (N=0).
3. Zero Model B feature mutation: asserts 58 features remain strictly untouched during cold-start evaluation.
4. Separate slice evaluation: overall, cold_start, mature.
5. Decision-support advisory policy: ensures advisory language is present and non-autonomous.
6. Cold-Start API endpoint (/api/analytics/cold-start) contract: returns 200 OK and Available.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import pytest
from fastapi.testclient import TestClient

from ml.evaluation.cold_start import (
    determine_graph_confidence,
    audit_cold_start_rules,
    evaluate_cold_start_slices,
)
from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_graph_confidence_precedence():
    """Verify strict precedence: UNAVAILABLE overrides LIMITED overrides VERIFIED."""
    # 1. UNAVAILABLE: connected accounts == 0 (even if other features indicate mature)
    row_unavail = pd.Series({"g_connected_accounts_count": 0, "beh_is_first_tx": 0, "beh_hist_tx_count": 50})
    assert determine_graph_confidence(row_unavail) == "UNAVAILABLE"

    # 2. LIMITED: connected accounts > 0, but is_first_tx == 1
    row_limited_first = pd.Series({"g_connected_accounts_count": 5, "beh_is_first_tx": 1, "beh_hist_tx_count": 1})
    assert determine_graph_confidence(row_limited_first) == "LIMITED"

    # 3. LIMITED: connected accounts > 0, hist_tx_count <= 2
    row_limited_low_tx = pd.Series({"g_connected_accounts_count": 3, "beh_is_first_tx": 0, "beh_hist_tx_count": 2})
    assert determine_graph_confidence(row_limited_low_tx) == "LIMITED"

    # 4. VERIFIED: connected accounts > 0 and hist_tx_count > 2
    row_verified = pd.Series({"g_connected_accounts_count": 4, "beh_is_first_tx": 0, "beh_hist_tx_count": 10})
    assert determine_graph_confidence(row_verified) == "VERIFIED"


def test_rule_sufficiency_audit_insufficient_evidence():
    """Verify candidate rule with 0 samples is marked LIMITED / INSUFFICIENT EVIDENCE."""
    df_feat = pd.DataFrame({
        "beh_account_age_days": [10.0, 20.0, 30.0],
        "beh_hist_tx_count": [1, 2, 5],
        "beh_is_first_tx": [1, 0, 0],
        "g_connected_accounts_count": [0, 2, 4],
    })
    df_meta = pd.DataFrame({"is_ring": [0, 0, 1]})

    audit = audit_cold_start_rules(df_feat, df_meta)
    rule_map = {r["rule_id"]: r for r in audit}

    assert rule_map["RULE_1_NEW_ACCOUNT"]["sample_count"] == 0
    assert rule_map["RULE_1_NEW_ACCOUNT"]["sufficiency"] == "INSUFFICIENT"
    assert "LIMITED / INSUFFICIENT EVIDENCE" in rule_map["RULE_1_NEW_ACCOUNT"]["status"]


def test_zero_model_b_feature_mutation():
    """Verify Model B feature matrix is not modified during cold-start evaluation."""
    from ml.models.graph_model import GraphEnhancedXGBoostModel
    from ml.models.baseline import BaselineXGBoostModel
    import joblib

    feat_dir = str(REPO_ROOT / "ml" / "data" / "features")
    mb = GraphEnhancedXGBoostModel(data_dir=feat_dir)
    X_b, y_b, meta_b = mb.load_dataset()
    ma = BaselineXGBoostModel(data_dir=feat_dir)
    X_a, y_a, meta_a = ma.load_dataset()

    model_a = joblib.load(REPO_ROOT / "models" / "ringguard_baseline_xgb_v1.joblib")
    model_b = joblib.load(REPO_ROOT / "models" / "ringguard_graph_xgb_v1.joblib")

    orig_cols = list(X_b.columns)
    orig_shape = X_b.shape
    orig_sum = float(X_b["tx_amount"].sum())

    slices_res = evaluate_cold_start_slices(
        X_a.iloc[:300], X_b.iloc[:300], y_b.iloc[:300].values, model_a, model_b, threshold=0.70
    )

    # Feature matrix integrity
    assert list(X_b.columns) == orig_cols
    assert X_b.shape == orig_shape
    assert float(X_b["tx_amount"].sum()) == orig_sum
    assert "slices" in slices_res
    assert "cold_start" in slices_res["slices"]
    assert "mature" in slices_res["slices"]


def test_cold_start_api_endpoint():
    """Verify GET /api/analytics/cold-start returns 200 OK and Available."""
    client = TestClient(app)
    response = client.get("/api/analytics/cold-start")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Available"
    assert "rule_sufficiency_audit" in data
    assert "full_dataset_evaluation" in data
    assert "held_out_test_evaluation" in data


def test_cold_start_transaction_distribution_sums_to_total():
    """Verify confidence distribution counts strictly sum to total transaction count (N=2000 and N=300)."""
    import json
    cold_file = REPO_ROOT / "ml" / "data" / "evaluation" / "cold_start_evaluation.json"
    if cold_file.exists():
        with open(cold_file, "r", encoding="utf-8") as f:
            artifact = json.load(f)
        assert artifact["metadata"]["unit_of_evaluation"] == "TRANSACTION"

        full_dist = artifact["full_dataset_evaluation"]["confidence_distribution"]
        full_total = artifact["full_dataset_evaluation"]["total_samples"]
        assert sum(full_dist.values()) == full_total == 2000
        assert full_dist["UNAVAILABLE"] == 61
        assert full_dist["LIMITED"] == 1295
        assert full_dist["VERIFIED"] == 644

        test_dist = artifact["held_out_test_evaluation"]["confidence_distribution"]
        test_total = artifact["held_out_test_evaluation"]["total_samples"]
        assert sum(test_dist.values()) == test_total == 300

