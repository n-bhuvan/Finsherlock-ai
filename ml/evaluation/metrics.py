"""RingGuard AI — Classification Evaluation Metrics.

Stage 6: Transaction-Only Baseline XGBoost.
Computes primary and secondary classification metrics for binary fraud/ring detection.
"""

from typing import Dict, Any, Union
import numpy as np
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    precision_recall_curve,
    auc,
)


def evaluate_binary_predictions(
    y_true: Union[np.ndarray, list],
    y_prob: Union[np.ndarray, list],
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """Calculate comprehensive binary classification metrics.
    
    Args:
        y_true: Ground truth binary labels (0 or 1).
        y_prob: Predicted probabilities for the positive class [0, 1].
        threshold: Decision threshold for discrete classification (default 0.5).
        
    Returns:
        Dictionary containing primary and secondary evaluation metrics.
    """
    y_true_arr = np.asarray(y_true, dtype=int)
    y_prob_arr = np.asarray(y_prob, dtype=float)

    # Discrete predictions at threshold
    y_pred = (y_prob_arr >= threshold).astype(int)

    # Class counts
    pos_count = int(np.sum(y_true_arr == 1))
    neg_count = int(np.sum(y_true_arr == 0))

    # Confusion matrix
    # Format: [[TN, FP], [FN, TP]]
    cm = confusion_matrix(y_true_arr, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    # Primary Ranking Metrics (threshold-independent)
    if pos_count > 0 and neg_count > 0:
        pr_auc = float(average_precision_score(y_true_arr, y_prob_arr))
        roc_auc = float(roc_auc_score(y_true_arr, y_prob_arr))
    else:
        pr_auc = 0.0
        roc_auc = 0.0

    # Threshold-dependent metrics (at baseline threshold 0.5)
    precision = float(precision_score(y_true_arr, y_pred, zero_division=0))
    recall = float(recall_score(y_true_arr, y_pred, zero_division=0))
    f1 = float(f1_score(y_true_arr, y_pred, zero_division=0))
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    return {
        "pr_auc": round(pr_auc, 4),
        "roc_auc": round(roc_auc, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "threshold": threshold,
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        "support": {
            "total": len(y_true_arr),
            "positive_count": pos_count,
            "negative_count": neg_count,
            "positive_rate": round(pos_count / len(y_true_arr), 4) if len(y_true_arr) > 0 else 0.0,
        },
    }
