#!/usr/bin/env python3
"""RingGuard AI — Train Baseline XGBoost (Model A).

Stage 6: Transaction-Only Baseline XGBoost.
Trains the baseline binary classifier on Transaction + Behavior features only (37 features),
evaluates performance chronologically across Train / Validation / Held-Out Test,
and exports model binaries, metadata, predictions, and feature importances.
"""

import json
import sys
from pathlib import Path
import pandas as pd

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.models.baseline import BaselineXGBoostModel
from ml.evaluation.metrics import evaluate_binary_predictions


def main():
    print("=" * 70)
    print("RINGGUARD AI -- TRAIN BASELINE XGBOOST (STAGE 6 - MODEL A)")
    print("=" * 70)

    # 1. Initialize Model
    model = BaselineXGBoostModel()

    # 2. Load Dataset
    print("\n[INFO] Loading Model A features and target metadata...")
    X, y, meta = model.load_dataset()
    print(f"  Dataset loaded: {len(X):,} prediction rows, {X.shape[1]} predictive features")
    print(f"  Total Ring/Positive: {int(y.sum()):,} ({y.mean() * 100:.2f}%), Legit/Negative: {int((y == 0).sum()):,}")

    # 3. Chronological Train / Validation / Test Split
    print("\n[INFO] Performing chronological split (70% Train, 15% Val, 15% Test)...")
    (X_train, y_train, meta_train), (X_val, y_val, meta_val), (X_test, y_test, meta_test) = model.chronological_split(X, y, meta)

    print(f"  TRAIN : {len(X_train):,} rows | Ring: {int(y_train.sum()):,} ({y_train.mean() * 100:.2f}%) | Legit: {int((y_train == 0).sum()):,}")
    print(f"          Start: {meta_train['dt_timestamp'].min()} -> End: {meta_train['dt_timestamp'].max()}")
    print(f"  VAL   : {len(X_val):,} rows | Ring: {int(y_val.sum()):,} ({y_val.mean() * 100:.2f}%) | Legit: {int((y_val == 0).sum()):,}")
    print(f"          Start: {meta_val['dt_timestamp'].min()} -> End: {meta_val['dt_timestamp'].max()}")
    print(f"  TEST  : {len(X_test):,} rows | Ring: {int(y_test.sum()):,} ({y_test.mean() * 100:.2f}%) | Legit: {int((y_test == 0).sum()):,}")
    print(f"          Start: {meta_test['dt_timestamp'].min()} -> End: {meta_test['dt_timestamp'].max()}")

    # 4. Train Model
    print("\n[INFO] Fitting XGBoost classifier on Training data...")
    model.train(X_train, y_train)
    print(f"  Training scale_pos_weight: {model.scale_pos_weight:.4f}")

    # 5. Predict Probabilities
    p_train = model.predict_proba(X_train)
    p_val = model.predict_proba(X_val)
    p_test = model.predict_proba(X_test)

    # 6. Evaluate Splits
    m_train = evaluate_binary_predictions(y_train, p_train, threshold=0.5)
    m_val = evaluate_binary_predictions(y_val, p_val, threshold=0.5)
    m_test = evaluate_binary_predictions(y_test, p_test, threshold=0.5)

    all_metrics = {
        "train": m_train,
        "validation": m_val,
        "held_out_test": m_test,
    }

    # 7. Print Metric Summary
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS (THRESHOLD = 0.5):")
    print("=" * 70)
    splits = [("TRAIN", m_train), ("VALIDATION", m_val), ("HELD-OUT TEST", m_test)]
    for s_name, m in splits:
        print(f"\n--- {s_name} ({m['support']['total']} rows, {m['support']['positive_count']} positive) ---")
        print(f"  PR-AUC              : {m['pr_auc']:.4f}")
        print(f"  ROC-AUC             : {m['roc_auc']:.4f}")
        print(f"  Precision           : {m['precision']:.4f}")
        print(f"  Recall              : {m['recall']:.4f}")
        print(f"  F1 Score            : {m['f1']:.4f}")
        print(f"  False Positive Rate : {m['false_positive_rate']:.4f}")
        cm = m['confusion_matrix']
        print(f"  Confusion Matrix    : TP={cm['true_positives']}, FP={cm['false_positives']}, TN={cm['true_negatives']}, FN={cm['false_negatives']}")

    # 8. Feature Importances
    df_importance = model.get_feature_importances()
    print("\n" + "-" * 40)
    print("TOP 10 FEATURE IMPORTANCES (MODEL A):")
    print("-" * 40)
    for _, row in df_importance.head(10).iterrows():
        print(f"  #{int(row['rank']):2d} {row['feature_name']:30s}: {row['importance']:.4f}")

    # 9. Save Artifacts
    eval_dir = REPO_ROOT / "ml" / "data" / "evaluation"
    models_dir = REPO_ROOT / "models"
    eval_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    # Save model binary and metadata
    model_bin_path = models_dir / "ringguard_baseline_xgb_v1.joblib"
    model_meta_path = models_dir / "ringguard_baseline_xgb_v1_metadata.json"
    model.save_artifacts(
        model_path=str(model_bin_path),
        metadata_path=str(model_meta_path),
        metrics_dict=all_metrics,
    )
    print(f"\n[INFO] Model saved to: {model_bin_path}")
    print(f"[INFO] Metadata saved to: {model_meta_path}")

    # Save metrics json
    metrics_path = eval_dir / "baseline_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"[INFO] Evaluation metrics saved to: {metrics_path}")

    # Save feature importance csv
    importance_path = eval_dir / "baseline_feature_importance.csv"
    df_importance.to_csv(importance_path, index=False)
    print(f"[INFO] Feature importance saved to: {importance_path}")

    # Save predictions dataframe across all 2,000 rows
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
    preds_path = eval_dir / "baseline_predictions.csv"
    df_preds.to_csv(preds_path, index=False)
    print(f"[INFO] Predictions saved to: {preds_path} ({len(df_preds)} rows)")

    print("\n" + "=" * 70)
    print("STAGE 6 BASELINE TRAINING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
