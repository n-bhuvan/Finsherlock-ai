#!/usr/bin/env python3
"""RingGuard AI — Evaluate Hard-Negative Challenge Dataset CLI.

Stage 13: Advanced Evaluation + Hard Negatives.
Extracts point-in-time features on the challenge dataset and evaluates frozen
Model A (Baseline, 37 features) and Model B (Graph-Enhanced, 58 features).
Computes overall metrics, threshold sweeps (0.10-0.90), and category-level FP slices.
Exports artifacts to ml/data/evaluation/challenge_comparison.json and .csv.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import joblib

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.features.pipeline import FeaturePipeline
from ml.evaluation.metrics import evaluate_binary_predictions


def run_threshold_evaluation(y_true: np.ndarray, y_prob: np.ndarray, threshold: float) -> Dict[str, Any]:
    """Calculate binary classification metrics at a specified threshold."""
    metrics = evaluate_binary_predictions(y_true, y_prob, threshold=threshold)
    return metrics


def run_threshold_sweep(y_true: np.ndarray, prob_a: np.ndarray, prob_b: np.ndarray) -> List[Dict[str, Any]]:
    """Evaluate both models across thresholds from 0.10 to 0.90 in steps of 0.05."""
    thresholds = [round(t, 2) for t in np.arange(0.10, 0.95, 0.05)]
    sweep_results = []

    for t in thresholds:
        mA = evaluate_binary_predictions(y_true, prob_a, threshold=t)
        mB = evaluate_binary_predictions(y_true, prob_b, threshold=t)

        sweep_results.append({
            "threshold": t,
            "model_a": {
                "precision": mA["precision"],
                "recall": mA["recall"],
                "f1": mA["f1"],
                "fpr": mA["false_positive_rate"],
                "fp_count": mA["confusion_matrix"]["false_positives"],
                "tp_count": mA["confusion_matrix"]["true_positives"],
            },
            "model_b": {
                "precision": mB["precision"],
                "recall": mB["recall"],
                "f1": mB["f1"],
                "fpr": mB["false_positive_rate"],
                "fp_count": mB["confusion_matrix"]["false_positives"],
                "tp_count": mB["confusion_matrix"]["true_positives"],
            },
            "deltas": {
                "precision_delta": round(mB["precision"] - mA["precision"], 4),
                "recall_delta": round(mB["recall"] - mA["recall"], 4),
                "f1_delta": round(mB["f1"] - mA["f1"], 4),
                "fpr_delta": round(mB["false_positive_rate"] - mA["false_positive_rate"], 4),
                "fp_delta": mB["confusion_matrix"]["false_positives"] - mA["confusion_matrix"]["false_positives"],
            }
        })
    return sweep_results


def run_category_slice_analysis(
    df_meta: pd.DataFrame,
    y_true: np.ndarray,
    prob_a: np.ndarray,
    prob_b: np.ndarray,
    threshold: float = 0.70,
) -> List[Dict[str, Any]]:
    """Analyze false positives and true positives across each hard-negative category."""
    categories = sorted(df_meta["challenge_category"].unique())
    pred_a = (prob_a >= threshold).astype(int)
    pred_b = (prob_b >= threshold).astype(int)

    slices = []
    for cat in categories:
        mask = (df_meta["challenge_category"] == cat).values
        cat_y = y_true[mask]
        cat_pa = prob_a[mask]
        cat_pb = prob_b[mask]
        cat_pred_a = pred_a[mask]
        cat_pred_b = pred_b[mask]

        total = int(len(cat_y))
        num_legit = int(np.sum(cat_y == 0))
        num_ring = int(np.sum(cat_y == 1))

        # False positives (actual legit, predicted ring)
        fp_a = int(np.sum((cat_y == 0) & (cat_pred_a == 1)))
        fp_b = int(np.sum((cat_y == 0) & (cat_pred_b == 1)))
        fpr_a = round(float(fp_a / num_legit), 4) if num_legit > 0 else 0.0
        fpr_b = round(float(fp_b / num_legit), 4) if num_legit > 0 else 0.0

        # True positives (actual ring, predicted ring)
        tp_a = int(np.sum((cat_y == 1) & (cat_pred_a == 1)))
        tp_b = int(np.sum((cat_y == 1) & (cat_pred_b == 1)))

        cat_name = str(df_meta[df_meta["challenge_category"] == cat]["category_name"].iloc[0])
        notes = str(df_meta[df_meta["challenge_category"] == cat]["notes"].iloc[0])

        slices.append({
            "challenge_category": cat,
            "category_name": cat_name,
            "description": notes,
            "total_transactions": total,
            "num_legitimate": num_legit,
            "num_ring": num_ring,
            "threshold": threshold,
            "model_a": {
                "fp_count": fp_a,
                "fpr": fpr_a,
                "tp_count": tp_a,
                "mean_probability": round(float(np.mean(cat_pa)), 4),
            },
            "model_b": {
                "fp_count": fp_b,
                "fpr": fpr_b,
                "tp_count": tp_b,
                "mean_probability": round(float(np.mean(cat_pb)), 4),
            },
            "deltas": {
                "fp_delta": fp_b - fp_a,
                "fpr_delta": round(fpr_b - fpr_a, 4),
                "mean_prob_delta": round(float(np.mean(cat_pb) - np.mean(cat_pa)), 4),
            },
        })
    return slices


def main():
    print("=" * 75)
    print("RINGGUARD AI -- HARD-NEGATIVE CHALLENGE EVALUATION (STAGE 13)")
    print("=" * 75)

    challenge_dir = REPO_ROOT / "ml" / "data" / "challenge"
    models_dir = REPO_ROOT / "models"
    eval_dir = REPO_ROOT / "ml" / "data" / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)

    if not challenge_dir.exists():
        print(f"[ERROR] Challenge directory not found at: {challenge_dir}")
        print("Run 'python scripts/generate_challenge_data.py' first.")
        sys.exit(1)

    # 1. Run Feature Pipeline on Challenge CSVs
    print("\n[INFO] Running feature extraction on ml/data/challenge/ ...")
    pipeline = FeaturePipeline(data_dir=str(challenge_dir))
    X_a, X_b, y_meta, manifest = pipeline.run_pipeline()

    print(f"  Total Challenge Transactions Extracted: {len(X_a):,}")
    print(f"  Model A Feature Shape: {X_a.shape} (Expected: 37 columns)")
    print(f"  Model B Feature Shape: {X_b.shape} (Expected: 58 columns)")

    # 2. Verify Feature Ordering Against Model Metadata
    meta_a_path = models_dir / "ringguard_baseline_xgb_v1_metadata.json"
    meta_b_path = models_dir / "ringguard_graph_xgb_v1_metadata.json"
    with open(meta_a_path, "r", encoding="utf-8") as f:
        meta_a = json.load(f)
    with open(meta_b_path, "r", encoding="utf-8") as f:
        meta_b = json.load(f)

    expected_cols_a = meta_a["feature_names"]
    expected_cols_b = meta_b["feature_names"]

    assert list(X_a.columns) == expected_cols_a, "Model A columns do not match expected 37 features!"
    assert list(X_b.columns) == expected_cols_b, "Model B columns do not match expected 58 features!"
    print("  [PASS] Feature ordering and dimensions verified against frozen model metadata.")

    # 3. Load Challenge Metadata for Ground Truth and Categories
    df_chal_meta = pd.read_csv(challenge_dir / "challenge_metadata.csv")
    y_true = df_chal_meta["target_binary"].values.astype(int)

    num_pos = int(np.sum(y_true == 1))
    num_neg = int(np.sum(y_true == 0))
    print(f"  Ground Truth Counts: Total={len(y_true)}, Ring Fraud (Controls)={num_pos}, Legitimate (Hard Negatives)={num_neg}")

    # 4. Load Frozen Models
    print("\n[INFO] Loading frozen Model A and Model B binaries...")
    model_a_path = models_dir / "ringguard_baseline_xgb_v1.joblib"
    model_b_path = models_dir / "ringguard_graph_xgb_v1.joblib"

    model_a = joblib.load(model_a_path)
    model_b = joblib.load(model_b_path)
    print("  [PASS] Frozen models loaded successfully.")

    # 5. Predict Probabilities
    print("\n[INFO] Generating challenge predictions...")
    prob_a = model_a.predict_proba(X_a)[:, 1]
    prob_b = model_b.predict_proba(X_b)[:, 1]

    # 6. Overall Evaluation at T=0.70 (Production Threshold)
    print("\n" + "=" * 70)
    print("OVERALL METRICS AT PRODUCTION THRESHOLD (T = 0.70):")
    print("=" * 70)
    metrics_a_070 = run_threshold_evaluation(y_true, prob_a, threshold=0.70)
    metrics_b_070 = run_threshold_evaluation(y_true, prob_b, threshold=0.70)

    delta_070 = {
        "pr_auc_delta": round(metrics_b_070["pr_auc"] - metrics_a_070["pr_auc"], 4),
        "roc_auc_delta": round(metrics_b_070["roc_auc"] - metrics_a_070["roc_auc"], 4),
        "precision_delta": round(metrics_b_070["precision"] - metrics_a_070["precision"], 4),
        "recall_delta": round(metrics_b_070["recall"] - metrics_a_070["recall"], 4),
        "f1_delta": round(metrics_b_070["f1"] - metrics_a_070["f1"], 4),
        "fpr_delta": round(metrics_b_070["false_positive_rate"] - metrics_a_070["false_positive_rate"], 4),
        "fp_delta": metrics_b_070["confusion_matrix"]["false_positives"] - metrics_a_070["confusion_matrix"]["false_positives"],
        "tp_delta": metrics_b_070["confusion_matrix"]["true_positives"] - metrics_a_070["confusion_matrix"]["true_positives"],
    }

    print(f"{'Metric':<25s} | {'Model A (Baseline)':<18s} | {'Model B (Graph)':<18s} | {'Delta (B - A)':<15s}")
    print("-" * 85)
    print(f"{'PR-AUC':<25s} | {metrics_a_070['pr_auc']:<18.4f} | {metrics_b_070['pr_auc']:<18.4f} | {delta_070['pr_auc_delta']:<+15.4f}")
    print(f"{'ROC-AUC':<25s} | {metrics_a_070['roc_auc']:<18.4f} | {metrics_b_070['roc_auc']:<18.4f} | {delta_070['roc_auc_delta']:<+15.4f}")
    print(f"{'Precision (T=0.70)':<25s} | {metrics_a_070['precision']:<18.4f} | {metrics_b_070['precision']:<18.4f} | {delta_070['precision_delta']:<+15.4f}")
    print(f"{'Recall (T=0.70)':<25s} | {metrics_a_070['recall']:<18.4f} | {metrics_b_070['recall']:<18.4f} | {delta_070['recall_delta']:<+15.4f}")
    print(f"{'F1 Score (T=0.70)':<25s} | {metrics_a_070['f1']:<18.4f} | {metrics_b_070['f1']:<18.4f} | {delta_070['f1_delta']:<+15.4f}")
    print(f"{'False Positive Rate':<25s} | {metrics_a_070['false_positive_rate']:<18.4f} | {metrics_b_070['false_positive_rate']:<18.4f} | {delta_070['fpr_delta']:<+15.4f}")
    cm_a = metrics_a_070["confusion_matrix"]
    cm_b = metrics_b_070["confusion_matrix"]
    print(f"{'False Positives (FP)':<25s} | {cm_a['false_positives']:<18d} | {cm_b['false_positives']:<18d} | {delta_070['fp_delta']:<+15d}")
    print(f"{'True Positives (TP)':<25s} | {cm_a['true_positives']:<18d} | {cm_b['true_positives']:<18d} | {delta_070['tp_delta']:<+15d}")

    # 7. Overall Evaluation at T=0.50 (Baseline Threshold)
    metrics_a_050 = run_threshold_evaluation(y_true, prob_a, threshold=0.50)
    metrics_b_050 = run_threshold_evaluation(y_true, prob_b, threshold=0.50)
    delta_050 = {
        "pr_auc_delta": round(metrics_b_050["pr_auc"] - metrics_a_050["pr_auc"], 4),
        "roc_auc_delta": round(metrics_b_050["roc_auc"] - metrics_a_050["roc_auc"], 4),
        "precision_delta": round(metrics_b_050["precision"] - metrics_a_050["precision"], 4),
        "recall_delta": round(metrics_b_050["recall"] - metrics_a_050["recall"], 4),
        "f1_delta": round(metrics_b_050["f1"] - metrics_a_050["f1"], 4),
        "fpr_delta": round(metrics_b_050["false_positive_rate"] - metrics_a_050["false_positive_rate"], 4),
        "fp_delta": metrics_b_050["confusion_matrix"]["false_positives"] - metrics_a_050["confusion_matrix"]["false_positives"],
        "tp_delta": metrics_b_050["confusion_matrix"]["true_positives"] - metrics_a_050["confusion_matrix"]["true_positives"],
    }

    # 8. Threshold Sweep
    sweep = run_threshold_sweep(y_true, prob_a, prob_b)

    # 9. Category Slice Breakdown (at T=0.70)
    print("\n" + "=" * 70)
    print("HARD-NEGATIVE CATEGORY SLICE ANALYSIS (AT T = 0.70):")
    print("=" * 70)
    category_slices = run_category_slice_analysis(df_chal_meta, y_true, prob_a, prob_b, threshold=0.70)

    print(f"{'Category':<25s} | {'Count':<6s} | {'A FPs':<6s} | {'A FPR':<8s} | {'B FPs':<6s} | {'B FPR':<8s} | {'Delta FP':<8s}")
    print("-" * 85)
    for cs in category_slices:
        print(
            f"{cs['challenge_category']:<25s} | {cs['total_transactions']:<6d} | "
            f"{cs['model_a']['fp_count']:<6d} | {cs['model_a']['fpr']:<8.4f} | "
            f"{cs['model_b']['fp_count']:<6d} | {cs['model_b']['fpr']:<8.4f} | "
            f"{cs['deltas']['fp_delta']:<+8d}"
        )

    # 10. Persist Challenge Comparison Artifacts
    challenge_payload = {
        "dataset_summary": {
            "name": "ringguard_challenge_v1",
            "seed": 20260905,
            "total_transactions": len(y_true),
            "legitimate_hard_negatives": num_neg,
            "ring_fraud_controls": num_pos,
            "category_count": len(category_slices),
        },
        "overall_metrics_t_0_70": {
            "model_a": metrics_a_070,
            "model_b": metrics_b_070,
            "deltas": delta_070,
        },
        "overall_metrics_t_0_50": {
            "model_a": metrics_a_050,
            "model_b": metrics_b_050,
            "deltas": delta_050,
        },
        "category_slices": category_slices,
        "threshold_sweep": sweep,
        "disclaimer": (
            "Hard-Negative Challenge Set / Robustness Stress Test. "
            "Evaluated strictly against frozen Model A and Model B without retraining. "
            "Separate from the official held-out benchmark."
        )
    }

    json_path = eval_dir / "challenge_comparison.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(challenge_payload, f, indent=2)
    print(f"\n[INFO] Persisted JSON artifact to: {json_path}")

    # Also build a flat CSV for category slices
    csv_rows = []
    for cs in category_slices:
        csv_rows.append({
            "category": cs["challenge_category"],
            "category_name": cs["category_name"],
            "total_samples": cs["total_transactions"],
            "model_a_fp_count": cs["model_a"]["fp_count"],
            "model_a_fpr": cs["model_a"]["fpr"],
            "model_b_fp_count": cs["model_b"]["fp_count"],
            "model_b_fpr": cs["model_b"]["fpr"],
            "fp_delta": cs["deltas"]["fp_delta"],
            "fpr_delta": cs["deltas"]["fpr_delta"],
        })
    df_cat_csv = pd.DataFrame(csv_rows)
    csv_path = eval_dir / "challenge_comparison.csv"
    df_cat_csv.to_csv(csv_path, index=False)
    print(f"[INFO] Persisted CSV artifact to: {csv_path}")

    print("\n" + "=" * 75)
    print("CHALLENGE EVALUATION COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    main()
