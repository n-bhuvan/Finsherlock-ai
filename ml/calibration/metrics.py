"""RingGuard AI — Probability Calibration Metrics.

Stage 14: Cold Start + Calibration + Thresholding.
Computes Brier Score, Expected Calibration Error (ECE), and reliability curves.
"""

from typing import Dict, Any, List, Union
import numpy as np
from sklearn.metrics import brier_score_loss


def compute_brier_score(
    y_true: Union[np.ndarray, list],
    y_prob: Union[np.ndarray, list],
) -> float:
    """Calculate the Brier Score for probabilistic binary predictions.
    
    BS = (1/N) * sum((y_prob - y_true)^2)
    Bounded in [0.0, 1.0]. Lower values indicate superior probabilistic calibration.
    """
    y_t = np.asarray(y_true, dtype=int)
    y_p = np.asarray(y_prob, dtype=float)
    if len(y_t) == 0:
        return 0.0
    return round(float(brier_score_loss(y_t, y_p)), 6)


def compute_ece(
    y_true: Union[np.ndarray, list],
    y_prob: Union[np.ndarray, list],
    n_bins: int = 10,
) -> float:
    """Calculate Expected Calibration Error (ECE) across uniform probability bins.
    
    ECE = sum_{m=1}^M (|B_m| / N) * |acc(B_m) - conf(B_m)|
    """
    y_t = np.asarray(y_true, dtype=int)
    y_p = np.asarray(y_prob, dtype=float)
    n = len(y_t)
    if n == 0:
        return 0.0

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        bin_lower = bins[i]
        bin_upper = bins[i + 1]
        
        if i == n_bins - 1:
            in_bin = (y_p >= bin_lower) & (y_p <= bin_upper)
        else:
            in_bin = (y_p >= bin_lower) & (y_p < bin_upper)

        bin_count = int(np.sum(in_bin))
        if bin_count > 0:
            bin_acc = float(np.mean(y_t[in_bin]))
            bin_conf = float(np.mean(y_p[in_bin]))
            ece += (bin_count / n) * abs(bin_acc - bin_conf)

    return round(float(ece), 6)


def compute_reliability_curve(
    y_true: Union[np.ndarray, list],
    y_prob: Union[np.ndarray, list],
    n_bins: int = 10,
) -> List[Dict[str, Any]]:
    """Generate reliability diagram coordinates across uniform probability bins."""
    y_t = np.asarray(y_true, dtype=int)
    y_p = np.asarray(y_prob, dtype=float)
    n = len(y_t)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    curve_points = []

    for i in range(n_bins):
        bin_lower = float(bins[i])
        bin_upper = float(bins[i + 1])
        
        if i == n_bins - 1:
            in_bin = (y_p >= bin_lower) & (y_p <= bin_upper)
        else:
            in_bin = (y_p >= bin_lower) & (y_p < bin_upper)

        bin_count = int(np.sum(in_bin))
        if bin_count > 0:
            bin_acc = round(float(np.mean(y_t[in_bin])), 4)
            bin_conf = round(float(np.mean(y_p[in_bin])), 4)
        else:
            bin_acc = 0.0
            bin_conf = round((bin_lower + bin_upper) / 2.0, 4)

        curve_points.append({
            "bin_index": i,
            "bin_lower": round(bin_lower, 2),
            "bin_upper": round(bin_upper, 2),
            "bin_midpoint": round((bin_lower + bin_upper) / 2.0, 2),
            "sample_count": bin_count,
            "mean_predicted_prob": bin_conf,
            "empirical_fraud_rate": bin_acc,
        })

    return curve_points
