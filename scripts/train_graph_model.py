#!/usr/bin/env python3
"""RingGuard AI — Train Graph-Enhanced XGBoost (Model B) and Compare with Model A.

Stage 7: Graph-Enhanced XGBoost.
Trains Model B on Transaction + Behavior + Point-in-Time Graph features (58 features),
evaluates performance chronologically across Train / Validation / Held-Out Test,
compares results against Model A baseline, and persists all model and comparison artifacts.
"""

import json
import sys
from pathlib import Path
import pandas as pd

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.models.graph_model import GraphEnhancedXGBoostModel
from ml.evaluation.metrics import evaluate_binary_predictions
from ml.evaluation.comparison import compare_models, save_comparison_artifacts


def main():
    print("=" * 70)
    print("RINGGUARD AI -- TRAIN GRAPH-ENHANCED XGBOOST (STAGE 7 - MODEL B)")
    print("=" * 70)

    # 1. Initialize Model B
    model_b = GraphEnhancedXGBoostModel()

    # 2. Load Dataset
    print("\n[INFO] Loading Model B features and target metadata...")
    X, y, meta = model_b.load_dataset()
    print(f"  Dataset loaded: {len(X):,} prediction rows, {X.shape[1]} predictive features")
    print(f"  Total Ring/Positive: {int(y.sum()):,} ({y.mean() * 100:.2f}%), Legit/Negative: {int((y == 0).sum()):,}")

    # 3. Chronological Train / Validation / Test Split (Identical to Model A)
    print("\n[INFO] Performing chronological split (70% Train, 15% Val, 15% Test)...")
    (X_train, y_train, meta_train), (X_val, y_val, meta_val), (X_test, y_test, meta_test) = model_b.chronological_split(X, y, meta)

    print(f"  TRAIN : {len(X_train):,} rows | Ring: {int(y_train.sum()):,} ({y_train.mean() * 100:.2f}%) | Legit: {int((y_train == 0).sum()):,}")
    print(f"          Start: {meta_train['dt_timestamp'].min()} -> End: {meta_train['dt_timestamp'].max()}")
    print(f"  VAL   : {len(X_val):,} rows | Ring: {int(y_val.sum()):,} ({y_val.mean() * 100:.2f}%) | Legit: {int((y_val == 0).sum()):,}")
    print(f"          Start: {meta_val['dt_timestamp'].min()} -> End: {meta_val['dt_timestamp'].max()}")
    print(f"  TEST  : {len(X_test):,} rows | Ring: {int(y_test.sum()):,} ({y_test.mean() * 100:.2f}%) | Legit: {int((y_test == 0).sum()):,}")
    print(f"          Start: {meta_test['dt_timestamp'].min()} -> End: {meta_test['dt_timestamp'].max()}")

    # 4. Train Model B
    print("\n[INFO] Fitting Graph-Enhanced XGBoost classifier on Training data...")
    model_b.train(X_train, y_train)
    print(f"  Training scale_pos_weight: {model_b.scale_pos_weight:.4f}")

    # 5. Predict Probabilities
    p_train = model_b.predict_proba(X_train)
    p_val = model_b.predict_proba(X_val)
    p_test = model_b.predict_proba(X_test)

    # 6. Evaluate Splits for Model B
    mb_train = evaluate_binary_predictions(y_train, p_train, threshold=0.5)
    mb_val = evaluate_binary_predictions(y_val, p_val, threshold=0.5)
    mb_test = evaluate_binary_predictions(y_test, p_test, threshold=0.5)

    metrics_b = {
        "train": mb_train,
        "validation": mb_val,
        "held_out_test": mb_test,
    }

    # 7. Load Model A Baseline Metrics for Comparison
    baseline_metrics_path = REPO_ROOT / "ml" / "data" / "evaluation" / "baseline_metrics.json"
    if not baseline_metrics_path.exists():
        raise FileNotFoundError(f"Model A baseline metrics not found at: {baseline_metrics_path}")

    with open(baseline_metrics_path, "r", encoding="utf-8") as f:
        metrics_a = json.load(f)

    # 8. Compute Model Comparison & Deltas
    df_comparison, comparison_dict = compare_models(metrics_a, metrics_b)

    # 9. Print Evaluation & Comparison Results
    print("\n" + "=" * 70)
    print("MODEL A (BASELINE) vs. MODEL B (GRAPH-ENHANCED) COMPARISON:")
    print("=" * 70)

    splits = [("TRAIN", "train"), ("VALIDATION", "validation"), ("HELD-OUT TEST", "held_out_test")]
    for display_name, split_key in splits:
        print(f"\n--- {display_name} SPLIT ---")
        split_df = df_comparison[df_comparison["split"] == split_key]
        print(f"{'Metric':<22} | {'Model A (37 f)':<15} | {'Model B (58 f)':<15} | {'Delta (B - A)':<15}")
        print("-" * 72)
        for _, row in split_df.iterrows():
            print(f"{row['metric_label']:<22} | {row['model_a_baseline']:<15.4f} | {row['model_b_graph']:<15.4f} | {row['delta']:<+15.4f}")

    # 10. Feature Importances
    df_importance = model_b.get_feature_importances()
    print("\n" + "-" * 50)
    print("TOP 10 OVERALL FEATURE IMPORTANCES (MODEL B):")
    print("-" * 50)
    for _, row in df_importance.head(10).iterrows():
        print(f"  #{int(row['rank']):2d} [{row['feature_group']:11s}] {row['feature_name']:32s}: {row['importance']:.4f}")

    df_graph_imp = df_importance[df_importance["feature_group"] == "graph"]
    print("\n" + "-" * 50)
    print(f"GRAPH FEATURE IMPORTANCES ({len(df_graph_imp)} features, total weight: {df_graph_imp['importance'].sum():.4f}):")
    print("-" * 50)
    for _, row in df_graph_imp.head(10).iterrows():
        print(f"  Overall Rank #{int(row['rank']):2d} | {row['feature_name']:35s}: {row['importance']:.4f}")

    # 11. Save Artifacts
    eval_dir = REPO_ROOT / "ml" / "data" / "evaluation"
    models_dir = REPO_ROOT / "models"
    eval_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    # Save Model B binary and metadata
    model_b_bin_path = models_dir / "ringguard_graph_xgb_v1.joblib"
    model_b_meta_path = models_dir / "ringguard_graph_xgb_v1_metadata.json"
    model_b.save_artifacts(
        model_path=str(model_b_bin_path),
        metadata_path=str(model_b_meta_path),
        metrics_dict=metrics_b,
    )
    print(f"\n[INFO] Model B binary saved to: {model_b_bin_path}")
    print(f"[INFO] Model B metadata saved to: {model_b_meta_path}")

    # Save comparison artifacts
    csv_comp, json_comp = save_comparison_artifacts(df_comparison, comparison_dict, output_dir=str(eval_dir))
    print(f"[INFO] Model comparison CSV saved to: {csv_comp}")
    print(f"[INFO] Model comparison JSON saved to: {json_comp}")

    # Save feature importance CSV
    importance_path = eval_dir / "graph_model_feature_importance.csv"
    df_importance.to_csv(importance_path, index=False)
    print(f"[INFO] Feature importance saved to: {importance_path}")

    # Save predictions dataframe
    pred_records = []
    for s_label, m_df, y_s, p_s in [
        ("train", meta_train, y_train, p_train),
        ("validation", meta_val, y_val, p_val),
        ("test", meta_test, y_test, p_test),
    ]:
        for (tx_id, r_meta), actual, prob in zip(m_df.iterrows(), y_s, p_s):
            pred_records.append({
                "transaction_id": tx_id,
                "timestamp": str(r_meta["dt_timestamp"]),
                "split": s_label,
                "actual_label": int(actual),
                "predicted_ring_probability": round(float(prob), 6),
            })

    df_preds = pd.DataFrame(pred_records)
    preds_path = eval_dir / "graph_model_predictions.csv"
    df_preds.to_csv(preds_path, index=False)
    print(f"[INFO] Model B predictions saved to: {preds_path} ({len(df_preds)} rows)")

    print("\n" + "=" * 70)
    print("STAGE 7 GRAPH-ENHANCED XGBOOST TRAINING & COMPARISON COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
