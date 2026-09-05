"""RingGuard AI — Stage 13 Challenge Evaluation Tests.

Tests:
1. Challenge dataset schema and entity integrity.
2. Ground truth consistency (binary labels matching string labels).
3. Leakage prevention (zero target labels or category metadata in feature matrices).
4. Feature dimensions (Model A = exactly 37, Model B = exactly 58).
5. Point-in-time graph and behavioral feature correctness (zero NaNs, zero Infs).
6. Frozen model binary immutability (SHA-256 checksums match pre-change baselines).
7. Official held-out benchmark immutability (SHA-256 checksums match pre-change baselines).
8. Evaluation invariants (confusion matrix counts sum to N, metrics in [0.0, 1.0]).
9. Challenge API endpoint contract (returns 200 OK with actual persisted data).
"""

import hashlib
import json
from pathlib import Path
import pandas as pd
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]
CHALLENGE_DIR = REPO_ROOT / "ml" / "data" / "challenge"
MODELS_DIR = REPO_ROOT / "models"
EVAL_DIR = REPO_ROOT / "ml" / "data" / "evaluation"

# Verified Stage 13 pre-change checksum baselines
PRE_CHANGE_MODEL_A_SHA256 = "ed8fa6e28177614e7fd494767e74ed9987a54b23a38ada74efe5a8cb8a7b06f0"
PRE_CHANGE_MODEL_B_SHA256 = "3ddd77d9caa27e65f7369ecd9e1cb6267404f4ff73a132a2b735f5da4568752e"
PRE_CHANGE_HELD_OUT_JSON_SHA256 = "5cc297a7c4a404dbdcc30b0b80ff05f285de991fa3a01f915f737d779515ad75"
PRE_CHANGE_HELD_OUT_CSV_SHA256 = "08345b585b9230407dd913eb64187acbffb3ed0f64c00a8eca7ac7a3c42fec8e"


def test_challenge_dataset_files_exist():
    """Verify all required challenge CSV files and metadata exist."""
    required_files = [
        "customers.csv",
        "accounts.csv",
        "devices.csv",
        "ips.csv",
        "beneficiaries.csv",
        "merchants.csv",
        "transactions.csv",
        "challenge_metadata.csv",
        "dataset_metadata.json",
    ]
    for fname in required_files:
        fpath = CHALLENGE_DIR / fname
        assert fpath.exists(), f"Missing required challenge file: {fname}"


def test_challenge_dataset_row_counts():
    """Verify challenge dataset row counts match expected target distribution."""
    df_tx = pd.read_csv(CHALLENGE_DIR / "transactions.csv")
    df_acc = pd.read_csv(CHALLENGE_DIR / "accounts.csv")
    df_meta = pd.read_csv(CHALLENGE_DIR / "challenge_metadata.csv")

    assert len(df_tx) == 754
    assert len(df_acc) == 200
    assert len(df_meta) == 754

    # Target composition
    num_legit = int((df_tx["ground_truth_label"] == "legitimate").sum())
    num_ring = int((df_tx["ground_truth_label"] == "ring").sum())

    assert num_legit == 607
    assert num_ring == 147


def test_challenge_ground_truth_consistency():
    """Verify labels in transactions.csv match challenge_metadata.csv exactly."""
    df_tx = pd.read_csv(CHALLENGE_DIR / "transactions.csv")
    df_meta = pd.read_csv(CHALLENGE_DIR / "challenge_metadata.csv")

    assert (df_tx["transaction_id"].values == df_meta["transaction_id"].values).all()
    assert (df_tx["ground_truth_label"].values == df_meta["ground_truth_label"].values).all()

    # Verify target_binary mapping
    for _, row in df_meta.iterrows():
        if row["ground_truth_label"] == "ring":
            assert row["target_binary"] == 1
        else:
            assert row["target_binary"] == 0


def test_leakage_prevention_feature_matrices():
    """Verify target labels and scenario metadata are strictly absent from feature matrices."""
    from ml.features.pipeline import FeaturePipeline

    pipeline = FeaturePipeline(data_dir=str(CHALLENGE_DIR))
    X_a, X_b, y_meta, manifest = pipeline.run_pipeline()

    forbidden_cols = [
        "ground_truth_label",
        "target_binary",
        "scenario_id",
        "scenario_type",
        "challenge_category",
        "category_name",
        "notes",
        "transaction_id",
        "account_id",
    ]

    for col in forbidden_cols:
        assert col not in X_a.columns, f"Leaked column '{col}' found in Model A features!"
        assert col not in X_b.columns, f"Leaked column '{col}' found in Model B features!"


def test_feature_dimensions_and_ordering():
    """Verify Model A has 37 features and Model B has 58 features matching frozen metadata."""
    from ml.features.pipeline import FeaturePipeline

    pipeline = FeaturePipeline(data_dir=str(CHALLENGE_DIR))
    X_a, X_b, _, _ = pipeline.run_pipeline()

    with open(MODELS_DIR / "ringguard_baseline_xgb_v1_metadata.json", "r", encoding="utf-8") as f:
        meta_a = json.load(f)
    with open(MODELS_DIR / "ringguard_graph_xgb_v1_metadata.json", "r", encoding="utf-8") as f:
        meta_b = json.load(f)

    assert X_a.shape == (754, 37)
    assert X_b.shape == (754, 58)

    assert list(X_a.columns) == meta_a["feature_names"]
    assert list(X_b.columns) == meta_b["feature_names"]

    # Verify zero NaNs and zero Infs
    assert not X_a.isna().any().any(), "Model A contains NaNs!"
    assert not X_b.isna().any().any(), "Model B contains NaNs!"
    assert not np.isinf(X_a.values).any(), "Model A contains Infs!"
    assert not np.isinf(X_b.values).any(), "Model B contains Infs!"


def test_frozen_model_binary_immutability():
    """Verify SHA-256 checksums of model binaries match pre-change baselines exactly."""
    sha_a = hashlib.sha256((MODELS_DIR / "ringguard_baseline_xgb_v1.joblib").read_bytes()).hexdigest()
    sha_b = hashlib.sha256((MODELS_DIR / "ringguard_graph_xgb_v1.joblib").read_bytes()).hexdigest()

    assert sha_a == PRE_CHANGE_MODEL_A_SHA256, "Model A joblib was modified!"
    assert sha_b == PRE_CHANGE_MODEL_B_SHA256, "Model B joblib was modified!"


def test_held_out_benchmark_immutability():
    """Verify SHA-256 checksums of Stage 7 held-out benchmark artifacts are untouched."""
    sha_json = hashlib.sha256((EVAL_DIR / "model_comparison.json").read_bytes()).hexdigest()
    sha_csv = hashlib.sha256((EVAL_DIR / "model_comparison.csv").read_bytes()).hexdigest()

    assert sha_json == PRE_CHANGE_HELD_OUT_JSON_SHA256, "Official held-out model_comparison.json was modified!"
    assert sha_csv == PRE_CHANGE_HELD_OUT_CSV_SHA256, "Official held-out model_comparison.csv was modified!"


def test_evaluation_math_invariants():
    """Verify confusion matrix counts sum to N and metrics fall within [0.0, 1.0]."""
    with open(EVAL_DIR / "challenge_comparison.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for thresh_key in ["overall_metrics_t_0_70", "overall_metrics_t_0_50"]:
        m_set = data[thresh_key]
        for model_key in ["model_a", "model_b"]:
            m = m_set[model_key]
            cm = m["confusion_matrix"]
            total = cm["true_positives"] + cm["false_positives"] + cm["true_negatives"] + cm["false_negatives"]
            assert total == 754, f"Confusion matrix total {total} != 754 in {thresh_key}/{model_key}"

            assert 0.0 <= m["pr_auc"] <= 1.0
            assert 0.0 <= m["roc_auc"] <= 1.0
            assert 0.0 <= m["precision"] <= 1.0
            assert 0.0 <= m["recall"] <= 1.0
            assert 0.0 <= m["f1"] <= 1.0
            assert 0.0 <= m["false_positive_rate"] <= 1.0


def test_challenge_api_endpoint():
    """Verify GET /api/analytics/challenge returns 200 OK with actual persisted data."""
    client = TestClient(app)
    response = client.get("/api/analytics/challenge")

    assert response.status_code == 200
    json_data = response.json()

    assert json_data["status"] == "Available"
    assert json_data["dataset_summary"]["total_transactions"] == 754
    assert json_data["dataset_summary"]["legitimate_hard_negatives"] == 607
    assert json_data["dataset_summary"]["ring_fraud_controls"] == 147

    # Verify metrics at T=0.70 are present and non-zero
    m70 = json_data["overall_metrics_t_0_70"]
    assert m70["model_a"]["pr_auc"] == 0.2105
    assert m70["model_b"]["pr_auc"] == 0.2056
    assert m70["deltas"]["pr_auc_delta"] == -0.0049

    # Verify category slices are present
    assert len(json_data["category_slices"]) == 8
