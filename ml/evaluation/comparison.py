"""RingGuard AI — Model A vs. Model B Comparison Engine.

Stage 7: Graph-Enhanced XGBoost.
Computes scientific, controlled performance comparisons between Model A (Baseline)
and Model B (Graph-Enhanced), calculating metric deltas across all evaluation splits.
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd


COMPARISON_METRIC_KEYS = [
    ("pr_auc", "PR-AUC"),
    ("roc_auc", "ROC-AUC"),
    ("precision", "Precision"),
    ("recall", "Recall"),
    ("f1", "F1 Score"),
    ("false_positive_rate", "False Positive Rate"),
]


def compare_models(
    metrics_a: Dict[str, Any],
    metrics_b: Dict[str, Any],
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Compare Model A and Model B metrics across Train, Validation, and Test splits.
    
    Args:
        metrics_a: Evaluation metrics dictionary for Model A.
        metrics_b: Evaluation metrics dictionary for Model B.
        
    Returns:
        (df_comparison, structured_comparison_dict)
    """
    records = []
    structured = {}

    splits = ["train", "validation", "held_out_test"]

    for split in splits:
        ma_split = metrics_a.get(split, {})
        mb_split = metrics_b.get(split, {})
        structured[split] = {}

        for key, label in COMPARISON_METRIC_KEYS:
            val_a = float(ma_split.get(key, 0.0))
            val_b = float(mb_split.get(key, 0.0))
            delta = round(val_b - val_a, 4)

            records.append({
                "split": split,
                "metric_key": key,
                "metric_label": label,
                "model_a_baseline": val_a,
                "model_b_graph": val_b,
                "delta": delta,
            })

            structured[split][key] = {
                "metric_label": label,
                "model_a_baseline": val_a,
                "model_b_graph": val_b,
                "delta": delta,
            }

        # Include confusion matrix deltas
        cm_a = ma_split.get("confusion_matrix", {})
        cm_b = mb_split.get("confusion_matrix", {})
        structured[split]["confusion_matrix"] = {
            "model_a": cm_a,
            "model_b": cm_b,
        }

    df_comp = pd.DataFrame(records)
    return df_comp, structured


def save_comparison_artifacts(
    df_comparison: pd.DataFrame,
    comparison_dict: Dict[str, Any],
    output_dir: str = "ml/data/evaluation",
) -> Tuple[Path, Path]:
    """Persist comparison CSV and JSON artifacts."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "model_comparison.csv"
    json_path = out_dir / "model_comparison.json"

    df_comparison.to_csv(csv_path, index=False)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(comparison_dict, f, indent=2)

    return csv_path, json_path
