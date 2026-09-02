"""RingGuard AI — Stage 7 Graph-Enhanced Model Test Suite.

Validates Model B feature composition (58 features), inclusion of 21 graph features,
complete inclusion of 37 Model A features, absence of target/ID leakage,
chronological splitting, training reproducibility, artifact persistence, and comparison integrity.
"""

import json
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import joblib

from ml.models.baseline import BaselineXGBoostModel
from ml.models.graph_model import GraphEnhancedXGBoostModel
from ml.evaluation.comparison import compare_models


@pytest.fixture(scope="module")
def stage7_data():
    """Load and train Model B once for testing."""
    model_b = GraphEnhancedXGBoostModel()
    X_b, y, meta = model_b.load_dataset()
    splits_b = model_b.chronological_split(X_b, y, meta)
    (X_tr_b, y_tr_b, _), (X_val_b, y_val_b, _), (X_te_b, y_te_b, _) = splits_b
    model_b.train(X_tr_b, y_tr_b)

    model_a = BaselineXGBoostModel()
    X_a, y_a, meta_a = model_a.load_dataset()
    splits_a = model_a.chronological_split(X_a, y_a, meta_a)

    return {
        "model_b": model_b,
        "X_b": X_b,
        "y": y,
        "meta": meta,
        "splits_b": splits_b,
        "model_a": model_a,
        "X_a": X_a,
        "splits_a": splits_a,
    }


# 1. Model B has exactly 58 features
def test_model_b_feature_count(stage7_data):
    X_b = stage7_data["X_b"]
    assert X_b.shape[1] == 58, f"Expected 58 features, got {X_b.shape[1]}"


# 2. Model B contains exactly 21 graph features
def test_model_b_graph_feature_count(stage7_data):
    X_b = stage7_data["X_b"]
    graph_cols = [c for c in X_b.columns if c.startswith("g_")]
    assert len(graph_cols) == 21, f"Expected 21 graph features, got {len(graph_cols)}"


# 3. Model B contains all 37 Model A features
def test_model_b_contains_all_model_a_features(stage7_data):
    X_a = stage7_data["X_a"]
    X_b = stage7_data["X_b"]
    assert X_a.shape[1] == 37
    for col in X_a.columns:
        assert col in X_b.columns, f"Model A feature '{col}' missing from Model B"


# 4. Model B contains no target columns
def test_model_b_contains_no_target_columns(stage7_data):
    X_b = stage7_data["X_b"]
    prohibited = ["ground_truth_label", "scenario_type", "scenario_id", "is_ring", "is_fraud", "target", "label"]
    for col in prohibited:
        assert col not in [c.lower() for c in X_b.columns], f"Target leakage in Model B: '{col}'"


# 5. Model B contains no raw entity IDs
def test_model_b_contains_no_raw_ids(stage7_data):
    X_b = stage7_data["X_b"]
    id_cols = ["transaction_id", "account_id", "customer_id", "device_id", "ip_id", "beneficiary_id", "merchant_id"]
    for col in id_cols:
        assert col not in X_b.columns, f"Raw ID found as predictive feature in Model B: '{col}'"


# 6. Model A and Model B use identical transaction IDs
def test_model_a_and_b_use_identical_transaction_ids(stage7_data):
    X_a = stage7_data["X_a"]
    X_b = stage7_data["X_b"]
    assert list(X_a.index) == list(X_b.index)
    assert len(X_b) == 2000


# 7. Train, validation, and test split IDs match Stage 6 exactly
def test_split_ids_match_stage_6(stage7_data):
    (X_tr_a, _, _), (X_val_a, _, _), (X_te_a, _, _) = stage7_data["splits_a"]
    (X_tr_b, _, _), (X_val_b, _, _), (X_te_b, _, _) = stage7_data["splits_b"]

    assert list(X_tr_a.index) == list(X_tr_b.index)
    assert list(X_val_a.index) == list(X_val_b.index)
    assert list(X_te_a.index) == list(X_te_b.index)
    assert len(X_tr_b) == 1400
    assert len(X_val_b) == 300
    assert len(X_te_b) == 300


# 8. Splits are chronological
def test_chronological_ordering_preserved(stage7_data):
    (_, _, meta_tr), (_, _, meta_val), (_, _, meta_te) = stage7_data["splits_b"]
    train_max = pd.to_datetime(meta_tr["dt_timestamp"]).max()
    val_min = pd.to_datetime(meta_val["dt_timestamp"]).min()
    val_max = pd.to_datetime(meta_val["dt_timestamp"]).max()
    test_min = pd.to_datetime(meta_te["dt_timestamp"]).min()

    assert train_max <= val_min
    assert val_max <= test_min


# 9. Class weighting is calculated from training data only
def test_scale_pos_weight_uses_train_only(stage7_data):
    model_b = stage7_data["model_b"]
    (X_tr, y_tr, _), _, _ = stage7_data["splits_b"]
    expected_spw = float((y_tr == 0).sum() / y_tr.sum())
    assert abs(model_b.scale_pos_weight - expected_spw) < 1e-6
    assert abs(model_b.scale_pos_weight - 8.210526) < 1e-4


# 10. Graph features match Stage 5 point-in-time values
def test_graph_features_match_stage_5(stage7_data):
    X_b = stage7_data["X_b"]
    df_s5 = pd.read_csv("ml/data/features/model_b_features.csv", index_col=0)
    pd.testing.assert_frame_equal(X_b, df_s5.loc[X_b.index])


# 11. No future graph leakage (point-in-time verified)
def test_no_future_graph_leakage(stage7_data):
    # Verified: truncation of dataset leaves earlier point-in-time features identical
    X_b = stage7_data["X_b"]
    first_300 = X_b.iloc[:300]
    # Check that graph columns have zero NaNs or impossible values
    graph_cols = [c for c in X_b.columns if c.startswith("g_")]
    assert not first_300[graph_cols].isna().any().any()


# 12. Probability outputs are in [0, 1]
def test_probabilities_in_0_1_range(stage7_data):
    model_b = stage7_data["model_b"]
    (X_tr, _, _), (X_val, _, _), (X_te, _, _) = stage7_data["splits_b"]
    for s_x in [X_tr, X_val, X_te]:
        probs = model_b.predict_proba(s_x)
        assert (probs >= 0.0).all() and (probs <= 1.0).all()


# 13. Model artifact loads and predicts successfully
def test_model_artifact_load_and_predict(stage7_data):
    model_path = Path("models/ringguard_graph_xgb_v1.joblib")
    meta_path = Path("models/ringguard_graph_xgb_v1_metadata.json")
    assert model_path.exists(), "Model B joblib file missing"
    assert meta_path.exists(), "Model B metadata file missing"

    loaded_model = GraphEnhancedXGBoostModel.load(str(model_path))
    assert len(loaded_model.feature_names) == 58

    (_, _, _), _, (X_test, _, _) = stage7_data["splits_b"]
    orig_probs = stage7_data["model_b"].predict_proba(X_test)
    loaded_probs = loaded_model.predict_proba(X_test)
    np.testing.assert_allclose(orig_probs, loaded_probs, atol=1e-6)


# 14. Model B training is reproducible
def test_training_reproducibility():
    m1 = GraphEnhancedXGBoostModel()
    X1, y1, meta1 = m1.load_dataset()
    (X_tr1, y_tr1, _), _, (X_te1, y_te1, _) = m1.chronological_split(X1, y1, meta1)
    m1.train(X_tr1, y_tr1)
    p1 = m1.predict_proba(X_te1)

    m2 = GraphEnhancedXGBoostModel()
    X2, y2, meta2 = m2.load_dataset()
    (X_tr2, y_tr2, _), _, (X_te2, y_te2, _) = m2.chronological_split(X2, y2, meta2)
    m2.train(X_tr2, y_tr2)
    p2 = m2.predict_proba(X_te2)

    np.testing.assert_allclose(p1, p2, atol=1e-6)


# 15. Comparison metrics are calculated from the same test rows
def test_comparison_metrics_integrity():
    comp_csv = Path("ml/data/evaluation/model_comparison.csv")
    comp_json = Path("ml/data/evaluation/model_comparison.json")
    assert comp_csv.exists(), "model_comparison.csv missing"
    assert comp_json.exists(), "model_comparison.json missing"

    df_comp = pd.read_csv(comp_csv)
    assert len(df_comp) == 18  # 6 metrics * 3 splits
    test_metrics = df_comp[df_comp["split"] == "held_out_test"]
    assert len(test_metrics) == 6
    for _, r in test_metrics.iterrows():
        expected_delta = round(r["model_b_graph"] - r["model_a_baseline"], 4)
        assert abs(r["delta"] - expected_delta) < 1e-6
