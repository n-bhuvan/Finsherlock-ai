"""RingGuard AI — Feature Engineering Test Suite.

Stage 5: Feature Engineering.
Validates transaction features, point-in-time behavioral features, point-in-time graph features,
target leakage prevention, temporal point-in-time safety, Model A and Model B contracts,
data integrity, and deterministic reproducibility.
"""

import pytest
import pandas as pd
import numpy as np
from sqlalchemy import text

from app.db.session import SessionLocal
from ml.features.pipeline import FeaturePipeline
from ml.features.transaction import TransactionFeatureExtractor, TRANSACTION_FEATURE_COLUMNS
from ml.features.behavior import PointInTimeBehaviorExtractor, BEHAVIORAL_FEATURE_COLUMNS
from ml.features.graph import PointInTimeGraphExtractor, POINT_IN_TIME_GRAPH_FEATURE_COLUMNS
from ml.features.validator import FeatureValidator


@pytest.fixture(scope="module")
def pipeline_data():
    """Load raw relational data once for testing."""
    session = SessionLocal()
    try:
        pipeline = FeaturePipeline(session=session)
        dfs = pipeline.load_data()
        return pipeline, dfs
    finally:
        session.close()


@pytest.fixture(scope="module")
def extracted_datasets(pipeline_data):
    """Execute pipeline once and provide output datasets."""
    pipeline, _ = pipeline_data
    X_a, X_b, y_meta, manifest = pipeline.run_pipeline()
    return X_a, X_b, y_meta, manifest


# 1. Transaction Feature Generation Test
def test_transaction_feature_generation(pipeline_data):
    _, dfs = pipeline_data
    df_tx = dfs["transactions"].copy()
    extractor = TransactionFeatureExtractor()
    feats = extractor.extract_features(df_tx)

    assert len(feats) == len(df_tx)
    assert list(feats.columns) == TRANSACTION_FEATURE_COLUMNS
    assert (feats["tx_amount"] > 0).all()
    assert (feats["tx_log_amount"] > 0).all()
    assert feats["tx_hour"].between(0, 23).all()
    assert feats["tx_day_of_week"].between(0, 6).all()
    assert feats["tx_is_weekend"].isin([0, 1]).all()
    assert feats["tx_is_transfer_p2p"].isin([0, 1]).all()
    assert feats["tx_is_payment_p2m"].isin([0, 1]).all()
    assert not feats.isna().any().any()


# 2. Behavioral Feature Generation Test
def test_behavioral_feature_generation(pipeline_data):
    _, dfs = pipeline_data
    df_tx = dfs["transactions"].copy()
    df_acc = dfs["accounts"].copy()
    extractor = PointInTimeBehaviorExtractor(df_acc)
    feats = extractor.extract_features(df_tx)

    assert len(feats) == len(df_tx)
    assert list(feats.columns) == BEHAVIORAL_FEATURE_COLUMNS
    assert (feats["beh_account_age_days"] >= 0).all()
    assert (feats["beh_tx_sequence_num"] >= 1).all()
    assert (feats["beh_hist_tx_count"] >= 0).all()
    assert not feats.isna().any().any()


# 3. CRITICAL: Point-in-Time Behavioral Safety Regression Test
def test_point_in_time_behavioral_safety(pipeline_data):
    """Proves future transactions (t > T) cannot alter features of past transactions (t <= T)."""
    _, dfs = pipeline_data
    df_tx = dfs["transactions"].copy()
    df_acc = dfs["accounts"].copy()
    df_tx["dt"] = pd.to_datetime(df_tx["timestamp"], utc=True)
    df_tx = df_tx.sort_values(by=["dt", "transaction_id"]).reset_index(drop=True)

    # 1. Compute on full 2,000 transactions
    extractor = PointInTimeBehaviorExtractor(df_acc)
    full_feats = extractor.extract_features(df_tx)

    # 2. Compute on truncated first 500 transactions
    cutoff_txs = df_tx.iloc[:500].copy()
    trunc_feats = extractor.extract_features(cutoff_txs)

    # 3. Assert exact equality for the first 500 transactions
    first_500_full = full_feats.iloc[:500]
    pd.testing.assert_frame_equal(first_500_full, trunc_feats)


# 4. CRITICAL: Point-in-Time Graph Safety Regression Test
def test_point_in_time_graph_safety(pipeline_data):
    """Proves future graph relationships (t > T) cannot alter earlier point-in-time graph features."""
    _, dfs = pipeline_data
    df_tx = dfs["transactions"].copy()
    df_tx["dt"] = pd.to_datetime(df_tx["timestamp"], utc=True)
    df_tx = df_tx.sort_values(by=["dt", "transaction_id"]).reset_index(drop=True)

    # 1. Compute on full 2,000 transactions
    extractor = PointInTimeGraphExtractor(dfs)
    full_graph_feats = extractor.extract_features(df_tx)

    # 2. Compute on truncated first 300 transactions
    cutoff_txs = df_tx.iloc[:300].copy()
    trunc_graph_feats = extractor.extract_features(cutoff_txs)

    # 3. Assert exact equality for the first 300 transactions
    first_300_full = full_graph_feats.iloc[:300]
    pd.testing.assert_frame_equal(first_300_full, trunc_graph_feats)


# 5. Target Leakage Prevention Test
def test_target_leakage_prevention(extracted_datasets):
    X_a, X_b, y_meta, _ = extracted_datasets

    # Ensure prohibited target columns are NEVER in feature matrices
    prohibited = ["ground_truth_label", "scenario_type", "scenario_id", "is_ring", "is_fraud"]
    for col in prohibited:
        assert col not in X_a.columns, f"Target leakage in Model A: '{col}' found"
        assert col not in X_b.columns, f"Target leakage in Model B: '{col}' found"

    # Ensure target labels ARE in target_metadata
    assert "is_ring" in y_meta.columns
    assert "ground_truth_label" in y_meta.columns
    assert "scenario_type" in y_meta.columns


# 6. Identifier Isolation Test
def test_identifier_isolation(extracted_datasets):
    X_a, X_b, _, _ = extracted_datasets
    # Ensure raw identifiers are indices, not predictive numeric/categorical features
    assert "account_id" not in X_a.columns
    assert "account_id" not in X_b.columns
    assert "transaction_id" not in X_a.columns
    assert "transaction_id" not in X_b.columns


# 7. Model A Feature Contract Test
def test_model_a_feature_contract(extracted_datasets):
    X_a, _, _, _ = extracted_datasets
    # Model A: Transaction (15) + Behavior (22) = 37 features
    assert len(X_a.columns) == 37
    assert len(X_a) == 2000

    # Must contain all transaction and behavioral features
    for c in TRANSACTION_FEATURE_COLUMNS:
        assert c in X_a.columns
    for c in BEHAVIORAL_FEATURE_COLUMNS:
        assert c in X_a.columns

    # Must NOT contain graph features
    for c in POINT_IN_TIME_GRAPH_FEATURE_COLUMNS:
        assert c not in X_a.columns


# 8. Model B Feature Contract Test
def test_model_b_feature_contract(extracted_datasets):
    X_a, X_b, _, _ = extracted_datasets
    # Model B: Model A (37) + Graph (21) = 58 features
    assert len(X_b.columns) == 58
    assert len(X_b) == 2000

    # Must contain all Model A features
    for c in X_a.columns:
        assert c in X_b.columns

    # Must contain all point-in-time graph features
    for c in POINT_IN_TIME_GRAPH_FEATURE_COLUMNS:
        assert c in X_b.columns


# 9. Dataset Alignment Test
def test_dataset_alignment(extracted_datasets):
    X_a, X_b, y_meta, _ = extracted_datasets
    assert list(X_a.index) == list(X_b.index)
    assert list(X_a.index) == list(y_meta.index)
    assert len(X_a) == 2000


# 10. Missing Values and Infinity Test
def test_missing_and_infinity_values(extracted_datasets):
    X_a, X_b, y_meta, _ = extracted_datasets
    assert not X_a.isna().any().any()
    assert not X_b.isna().any().any()
    assert not y_meta.isna().any().any()
    assert not np.isinf(X_a.values).any()
    assert not np.isinf(X_b.values).any()


# 11. Deterministic Reproducibility Test
def test_deterministic_reproducibility(pipeline_data):
    pipeline, _ = pipeline_data
    X_a1, X_b1, y1, _ = pipeline.run_pipeline()
    X_a2, X_b2, y2, _ = pipeline.run_pipeline()

    pd.testing.assert_frame_equal(X_a1, X_a2)
    pd.testing.assert_frame_equal(X_b1, X_b2)
    pd.testing.assert_frame_equal(y1, y2)


# 12. Source Data Integrity Test
def test_source_data_integrity():
    session = SessionLocal()
    try:
        tx_count = session.execute(text("SELECT count(*) FROM transactions;")).scalar()
        acc_count = session.execute(text("SELECT count(*) FROM accounts;")).scalar()
        cust_count = session.execute(text("SELECT count(*) FROM customers;")).scalar()
        assert tx_count == 2000
        assert acc_count == 500
        assert cust_count == 500
    finally:
        session.close()
