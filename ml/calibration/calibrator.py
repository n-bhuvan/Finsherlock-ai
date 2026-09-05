"""RingGuard AI — Post-Hoc Risk Calibrator.

Stage 14: Cold Start + Calibration + Thresholding.
Implements Platt Scaling (Sigmoid) and Isotonic Regression wrappers with
a deterministic selection algorithm and degradation fallback.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Union
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression

from ml.calibration.metrics import compute_brier_score, compute_ece, compute_reliability_curve


class RiskCalibrator:
    """Post-hoc probability calibrator fitted strictly on validation predictions."""

    def __init__(self):
        self.platt_model: Optional[LogisticRegression] = None
        self.isotonic_model: Optional[IsotonicRegression] = None
        self.selected_method: str = "raw"
        self.selection_reason: str = "Uninitialized"
        self.selection_metrics: Dict[str, Any] = {}
        self.is_fitted: bool = False

    def _to_logit(self, p: np.ndarray) -> np.ndarray:
        """Convert probabilities to log-odds margins with numerical clipping."""
        eps = 1e-7
        p_clipped = np.clip(p, eps, 1.0 - eps)
        return np.log(p_clipped / (1.0 - p_clipped)).reshape(-1, 1)

    def fit(
        self,
        y_val_calib: Union[np.ndarray, list],
        p_raw: Union[np.ndarray, list],
    ) -> "RiskCalibrator":
        """Fit Platt and Isotonic calibrators on Val-Calib and execute deterministic selection.
        
        Args:
            y_val_calib: Ground truth binary labels for Val-Calib (N=150).
            p_raw: Uncalibrated model probabilities on Val-Calib (N=150).
        """
        y_true = np.asarray(y_val_calib, dtype=int)
        p_arr = np.asarray(p_raw, dtype=float)

        # 1. Fit Platt Scaling (Logistic Regression on logit margins)
        logits = self._to_logit(p_arr)
        self.platt_model = LogisticRegression(solver="lbfgs", C=1.0, max_iter=1000)
        self.platt_model.fit(logits, y_true)
        p_platt = self.platt_model.predict_proba(logits)[:, 1]

        # 2. Fit Isotonic Regression (monotonic step function on raw probabilities)
        self.isotonic_model = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
        self.isotonic_model.fit(p_arr, y_true)
        p_iso = self.isotonic_model.predict(p_arr)

        # 3. Compute Brier scores and ECE on Val-Calib
        bs_raw = compute_brier_score(y_true, p_arr)
        bs_platt = compute_brier_score(y_true, p_platt)
        bs_iso = compute_brier_score(y_true, p_iso)

        ece_raw = compute_ece(y_true, p_arr)
        ece_platt = compute_ece(y_true, p_platt)
        ece_iso = compute_ece(y_true, p_iso)

        self.selection_metrics = {
            "val_calib_sample_count": int(len(y_true)),
            "val_calib_pos_count": int(np.sum(y_true == 1)),
            "val_calib_neg_count": int(np.sum(y_true == 0)),
            "raw": {"brier_score": bs_raw, "ece": ece_raw},
            "platt": {"brier_score": bs_platt, "ece": ece_platt},
            "isotonic": {"brier_score": bs_iso, "ece": ece_iso},
        }

        # 4. Deterministic Calibrator Selection Algorithm
        # Rule 1: Degradation fallback
        if bs_platt > bs_raw and bs_iso > bs_raw:
            self.selected_method = "raw"
            self.selection_reason = (
                f"Degradation fallback: Both Platt (BS={bs_platt:.4f}) and Isotonic (BS={bs_iso:.4f}) "
                f"produced worse Brier scores than Raw (BS={bs_raw:.4f}). Retaining Raw probabilities."
            )
        else:
            # Rule 2: Evaluate eligible methods (BS <= BS_raw)
            eligible = {}
            if bs_platt <= bs_raw:
                eligible["platt"] = bs_platt
            if bs_iso <= bs_raw:
                eligible["isotonic"] = bs_iso

            if "platt" in eligible and "isotonic" in eligible:
                # Rule 3: Tie-breaker (|BS_platt - BS_iso| <= 0.005 -> prefer Platt)
                if abs(bs_platt - bs_iso) <= 0.005:
                    self.selected_method = "platt"
                    self.selection_reason = (
                        f"Platt tie-breaker preference (|BS_platt ({bs_platt:.4f}) - BS_iso ({bs_iso:.4f})| <= 0.005) "
                        f"for parametric stability on small validation sample."
                    )
                elif bs_iso < bs_platt:
                    self.selected_method = "isotonic"
                    self.selection_reason = f"Isotonic regression strictly lowest Brier score ({bs_iso:.4f} vs {bs_platt:.4f})."
                else:
                    self.selected_method = "platt"
                    self.selection_reason = f"Platt scaling strictly lowest Brier score ({bs_platt:.4f} vs {bs_iso:.4f})."
            elif "platt" in eligible:
                self.selected_method = "platt"
                self.selection_reason = f"Only Platt scaling improved Brier score ({bs_platt:.4f} vs Raw {bs_raw:.4f})."
            else:
                self.selected_method = "isotonic"
                self.selection_reason = f"Only Isotonic regression improved Brier score ({bs_iso:.4f} vs Raw {bs_raw:.4f})."

        self.is_fitted = True
        return self

    def predict_calibrated_proba(
        self,
        p_raw: Union[np.ndarray, list],
        method: Optional[str] = None,
    ) -> np.ndarray:
        """Apply the selected (or explicitly specified) calibrator to raw probabilities.
        
        Args:
            p_raw: Array of raw model probabilities.
            method: 'selected' (default), 'raw', 'platt', or 'isotonic'.
        """
        p_arr = np.asarray(p_raw, dtype=float)
        target_method = method if method is not None else self.selected_method

        if target_method == "raw" or not self.is_fitted:
            return p_arr
        elif target_method == "platt":
            if self.platt_model is None:
                return p_arr
            logits = self._to_logit(p_arr)
            return self.platt_model.predict_proba(logits)[:, 1]
        elif target_method == "isotonic":
            if self.isotonic_model is None:
                return p_arr
            return self.isotonic_model.predict(p_arr)
        else:
            raise ValueError(f"Unknown calibration method: {target_method}")

    def calibrate(
        self,
        p_raw: Union[np.ndarray, list],
        method: Optional[str] = None,
    ) -> np.ndarray:
        """Alias for predict_calibrated_proba()."""
        return self.predict_calibrated_proba(p_raw, method=method)

    def transform(
        self,
        p_raw: Union[np.ndarray, list],
        method: Optional[str] = None,
    ) -> np.ndarray:
        """Alias for predict_calibrated_proba() adhering to scikit-learn transformer protocol."""
        return self.predict_calibrated_proba(p_raw, method=method)

    def save(self, filepath: Union[str, Path]) -> None:
        """Persist fitted calibrator instance."""
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "RiskCalibrator":
        """Load persisted calibrator instance."""
        return joblib.load(filepath)
