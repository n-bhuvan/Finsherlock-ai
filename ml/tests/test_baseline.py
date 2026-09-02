"""RingGuard AI — Stage 6 Baseline Model Test Suite.

Validates Model A data integrity, lack of graph features, absence of target/ID leakage,
chronological splitting, training reproducibility, and model artifact persistence.
"""

import json
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import joblib

from ml.models.baseline import BaselineXGBoostModel
from ml.evaluation.metrics import evaluate_binary_predictions


@pytest.fixture(scope="module")
def trained_baseline():
    """Load, split, and train the baseline model once for testing."""
    model = BaselineXGBoostModel()
    X, y, meta = model.load_dataset()
    splits = model.chronological_split(X, y, meta)
    (X_train, y_train, meta_train), (X_val, y_val, meta_val), (X_test, y_test, meta_test) = splits
    model.train(X_train, y_train)
    return {
        "model": model,
        "X": X,
        "y": y,
        "meta": meta,
        "splits": splits,
    }


# 1. Model A contains NO graph features
def test_model_a_contains_no_graph_features(trained_baseline):
    X = trained_baseline["X"]
    graph_cols = [c for c in X.columns if c.startswith("g_") or "graph" in c.lower()]
    assert len(graph_cols) == 0, f"Graph features found in Model A: {graph_cols}"
    assert X.shape[1] == 37, f"Expected 37 features in Model A, got {X.shape[1]}"


# 2. Model A contains NO target columns
def test_model_a_contains_no_target_columns(trained_baseline):
    X = trained_baseline["X"]
    prohibited = ["ground_truth_label", "scenario_type", "scenario_id", "is_ring", "is_fraud", "target", "label"]
    for col in prohibited:
        assert col not in [c.lower() for c in X.columns], f"Target leakage found in Model A: {col}"


# 3. Model A contains NO raw IDs as predictive features
def test_model_a_contains_no_raw_ids(trained_baseline):
    X = trained_baseline["X"]
    id_cols = ["transaction_id", "account_id", "customer_id", "device_id", "ip_id", "beneficiary_id", "merchant_id"]
    for col in id_cols:
        assert col not in X.columns, f"Raw ID found as predictive feature in Model A: {col}"


# 4. Train, validation, and test transaction IDs are mutually disjoint
def test_splits_are_disjoint_and_complete(trained_baseline):
    (X_train, _, _), (X_val, _, _), (X_test, _, _) = trained_baseline["splits"]
    train_ids = set(X_train.index)
    val_ids = set(X_val.index)
    test_ids = set(X_test.index)

    assert len(train_ids.intersection(val_ids)) == 0, "Train and Val IDs overlap"
    assert len(train_ids.intersection(test_ids)) == 0, "Train and Test IDs overlap"
    assert len(val_ids.intersection(test_ids)) == 0, "Val and Test IDs overlap"

    all_ids = train_ids | val_ids | test_ids
    assert len(all_ids) == 2000, f"Expected 2000 total IDs across splits, got {len(all_ids)}"
    assert len(X_train) == 1400
    assert len(X_val) == 300
    assert len(X_test) == 300


# 5. Chronological ordering is strictly preserved
def test_chronological_ordering_preserved(trained_baseline):
    (_, _, meta_train), (_, _, meta_val), (_, _, meta_test) = trained_baseline["splits"]
    train_max = pd.to_datetime(meta_train["dt_timestamp"]).max()
    val_min = pd.to_datetime(meta_val["dt_timestamp"]).min()
    val_max = pd.to_datetime(meta_val["dt_timestamp"]).max()
    test_min = pd.to_datetime(meta_test["dt_timestamp"]).min()

    assert train_max <= val_min, f"Train max ({train_max}) > Val min ({val_min})"
    assert val_max <= test_min, f"Val max ({val_max}) > Test min ({test_min})"


# 6. scale_pos_weight is calculated strictly on training data
def test_scale_pos_weight_uses_train_only(trained_baseline):
    model = trained_baseline["model"]
    (_, y_train, _), _, _ = trained_baseline["splits"]
    expected_spw = float((y_train == 0).sum() / y_train.sum())
    assert abs(model.scale_pos_weight - expected_spw) < 1e-6
    assert abs(model.scale_pos_weight - 8.210526) < 1e-4


# 7. Probability outputs are within [0, 1]
def test_probability_outputs_bounded_in_0_1(trained_baseline):
    model = trained_baseline["model"]
    (X_train, _, _), (X_val, _, _), (X_test, _, _) = trained_baseline["splits"]
    for split_X in [X_train, X_val, X_test]:
        probs = model.predict_proba(split_X)
        assert len(probs) == len(split_X)
        assert (probs >= 0.0).all() and (probs <= 1.0).all()


# 8. Prediction rows align exactly with transaction IDs
def test_predictions_align_with_transaction_ids(trained_baseline):
    eval_csv = Path("ml/data/evaluation/baseline_predictions.csv")
    assert eval_csv.exists(), "baseline_predictions.csv does not exist"
    df_preds = pd.read_csv(eval_csv)
    assert len(df_preds) == 2000
    assert df_preds["transaction_id"].nunique() == 2000
    assert (df_preds["predicted_ring_probability"] >= 0.0).all()
    assert (df_preds["predicted_ring_probability"] <= 1.0).all()


# 9. Reproducibility test
def test_training_reproducibility():
    model1 = BaselineXGBoostModel()
    X1, y1, meta1 = model1.load_dataset()
    (X_tr1, y_tr1, _), _, (X_te1, y_te1, _) = model1.chronological_split(X1, y1, meta1)
    model1.train(X_tr1, y_tr1)
    p1 = model1.predict_proba(X_te1)

    model2 = BaselineXGBoostModel()
    X2, y2, meta2 = model2.load_dataset()
    (X_tr2, y_tr2, _), _, (X_te2, y_te2, _) = model2.chronological_split(X2, y2, meta2)
    model2.train(X_tr2, y_tr2)
    p2 = model2.predict_proba(X_te2)

    np.testing.assert_allclose(p1, p2, atol=1e-6)


# 10. Saved model artifact loads and predicts
def test_saved_model_artifact_loads_and_predicts(trained_baseline):
    model_path = Path("models/ringguard_baseline_xgb_v1.joblib")
    meta_path = Path("models/ringguard_baseline_xgb_v1_metadata.json")
    assert model_path.exists(), "Saved model joblib missing"
    assert meta_path.exists(), "Saved model metadata missing"

    # Load via BaselineXGBoostModel.load()
    loaded_model = BaselineXGBoostModel.load(str(model_path))
    (_, _, _), _, (X_test, _, _) = trained_baseline["splits"]

    original_preds = trained_baseline["model"].predict_proba(X_test)
    loaded_preds = loaded_model.predict_proba(X_test)

    np.testing.assert_allclose(original_preds, loaded_preds, atol=1e-6)
