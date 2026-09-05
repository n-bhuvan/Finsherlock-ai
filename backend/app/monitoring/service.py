"""RingGuard AI — Stage 20: Outcome Verification + Drift Monitoring Service.

Implements two deterministic human decision-support services:
1. OutcomeVerificationService: Verifies post-decision outcomes against controlled synthetic metadata.
2. DriftMonitoringService: Measures distribution drift (PSI, JSD, Missingness) across chronological partitions.
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import joblib
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.services.feature_service import get_feature_service
from app.services.model_service import get_model_service
from ml.calibration.calibrator import RiskCalibrator
from app.monitoring.schemas import (
    DriftStatus,
    OutcomeStatus,
    DriftMetric,
    OutcomePerformanceMetric,
    DriftMonitoringResponse,
    OutcomeVerificationResponse,
    MonitoringSummaryResponse,
)

# Global caches for drift monitoring to avoid reloading large artifacts repeatedly
_drift_cache: Dict[str, Any] = {}


def get_drift_service() -> "DriftMonitoringService":
    global _drift_cache
    if "drift_service" not in _drift_cache:
        _drift_cache["drift_service"] = DriftMonitoringService()
    return _drift_cache["drift_service"]


class OutcomeVerificationService:
    """Verifies post-decision outcomes against available evaluation ground truth.

    STRICT SEPARATION:
    Prediction != Policy Recommendation != Observed Outcome
    """

    def __init__(self, db: Session, model_service: Optional[Any] = None):
        self.db = db
        self.model_service = model_service or get_model_service()
        self.feature_service = get_feature_service()

        # Load metadata lookup for ground-truth outcomes
        meta_path = Path("ml/data/features/target_metadata.csv")
        if not meta_path.exists():
            meta_path = Path(__file__).resolve().parents[3] / "ml" / "data" / "features" / "target_metadata.csv"

        if meta_path.exists():
            df = pd.read_csv(meta_path)
            self._metadata_map = df.set_index("transaction_id").to_dict(orient="index")
        else:
            self._metadata_map = {}

        # Load post-hoc Model B calibrator
        self._calibrator_b: Optional[RiskCalibrator] = None
        calib_path = Path("models/calibrator_model_b.joblib")
        if not calib_path.exists():
            calib_path = Path(__file__).resolve().parents[3] / "models" / "calibrator_model_b.joblib"
        if calib_path.exists():
            try:
                self._calibrator_b = RiskCalibrator.load(calib_path)
            except Exception:
                self._calibrator_b = None

    def verify_transaction_outcome(
        self,
        transaction_id: str,
        evaluation_context: str = "SIMULATED_BENCHMARK",
    ) -> OutcomeVerificationResponse:
        """Verify the observed outcome of a transaction given its decision context."""
        # 1. Verify transaction exists in PostgreSQL or controlled evaluation dataset
        tx = None
        if self.db is not None:
            try:
                tx = (
                    self.db.query(Transaction)
                    .filter(Transaction.transaction_id == transaction_id)
                    .first()
                )
            except Exception:
                tx = None

        has_features = (
            self.feature_service._model_b_df is not None
            and transaction_id in self.feature_service._model_b_df.index
        )

        if not tx:
            if transaction_id in self._metadata_map or has_features:
                tx_status = "SUCCESS"
            else:
                raise KeyError(f"Transaction '{transaction_id}' not found in database or evaluation dataset.")
        else:
            tx_status = tx.status

        # 2. Query Model B calibrated prediction directly
        prediction_at_decision = 0.50
        try:
            if has_features:
                feats = self.feature_service._model_b_df.loc[[transaction_id]]
                p_raw = self.model_service.predict_graph(feats)
                if self._calibrator_b is not None:
                    prediction_at_decision = float(self._calibrator_b.predict_calibrated_proba([p_raw])[0])
                else:
                    prediction_at_decision = float(p_raw)
        except Exception:
            prediction_at_decision = 0.50
        prediction_at_decision = round(prediction_at_decision, 4)
        policy_action_at_decision = None

        now_iso = datetime.now(timezone.utc).isoformat()

        # 3. Handle Operational Context (Ground truth is unavailable in live runtime)
        if evaluation_context == "OPERATIONAL":
            return OutcomeVerificationResponse(
                transaction_id=transaction_id,
                evaluation_context="OPERATIONAL",
                prediction_at_decision=prediction_at_decision,
                policy_action_at_decision=policy_action_at_decision,
                observed_outcome=None,
                outcome_status=OutcomeStatus.OUTCOME_UNAVAILABLE,
                outcome_match=None,
                verification_timestamp=now_iso,
                verification_source="OPERATIONAL_RUNTIME",
                limitations=(
                    "Ground-truth outcome is unavailable in live operational context. "
                    "Operational transactions do not expose future chargeback or confirmation telemetry."
                ),
                human_review_required=True,
                disclaimer=(
                    "SIMULATED / SYNTHETIC BENCHMARK — not real production outcomes. "
                    "Outcome verification is provided strictly for model evaluation and audit."
                ),
            )

        # 4. Handle Simulated Benchmark Context
        meta_record = self._metadata_map.get(transaction_id)
        if not meta_record or "ground_truth_label" not in meta_record:
            return OutcomeVerificationResponse(
                transaction_id=transaction_id,
                evaluation_context="SIMULATED_BENCHMARK",
                prediction_at_decision=prediction_at_decision,
                policy_action_at_decision=policy_action_at_decision,
                observed_outcome=None,
                outcome_status=OutcomeStatus.OUTCOME_UNAVAILABLE,
                outcome_match=None,
                verification_timestamp=now_iso,
                verification_source="SIMULATED_EVALUATION_METADATA",
                limitations="Transaction not present in controlled evaluation benchmark slice.",
                human_review_required=True,
                disclaimer=(
                    "SIMULATED / SYNTHETIC BENCHMARK — not real production outcomes. "
                    "Outcome verification is provided strictly for model evaluation and audit."
                ),
            )

        raw_label = str(meta_record.get("ground_truth_label", "")).lower()
        is_ring = int(meta_record.get("is_ring", 0))

        # Check for pending status or inconclusive states
        if tx_status == "PENDING":
            outcome_status = OutcomeStatus.OUTCOME_PENDING
            outcome_match = None
        elif not raw_label or raw_label not in ["ring", "legitimate"]:
            outcome_status = OutcomeStatus.OUTCOME_INCONCLUSIVE
            outcome_match = None
        else:
            outcome_status = OutcomeStatus.OUTCOME_CONFIRMED
            # Truthful agreement: positive prediction aligns with ring outcome, negative prediction aligns with legitimate
            is_positive_outcome = (is_ring == 1 or raw_label == "ring")
            is_positive_pred = (prediction_at_decision >= 0.50)
            outcome_match = (is_positive_pred == is_positive_outcome)

        return OutcomeVerificationResponse(
            transaction_id=transaction_id,
            evaluation_context="SIMULATED_BENCHMARK",
            prediction_at_decision=prediction_at_decision,
            policy_action_at_decision=policy_action_at_decision,
            observed_outcome=raw_label if outcome_status == OutcomeStatus.OUTCOME_CONFIRMED else None,
            outcome_status=outcome_status,
            outcome_match=outcome_match,
            verification_timestamp=now_iso,
            verification_source="SIMULATED_EVALUATION_METADATA",
            limitations=(
                "Simulated benchmark verification only. Evaluated against synthetic offline labels. "
                "Does not represent real-world bank or Razorpay production fraud outcomes."
            ),
            human_review_required=True,
            disclaimer=(
                "SIMULATED / SYNTHETIC BENCHMARK — not real production outcomes. "
                "Outcome verification is provided strictly for model evaluation and audit."
            ),
        )


class DriftMonitoringService:
    """Deterministic statistical drift monitoring across chronological partitions."""

    def __init__(self):
        self.repo_root = Path(".").resolve()
        if not (self.repo_root / "ml").exists():
            self.repo_root = Path(__file__).resolve().parents[3]

        self._load_datasets_and_models()

    def _load_datasets_and_models(self) -> None:
        """Pre-load and partition features and predictions once to ensure rapid evaluations."""
        feat_path = self.repo_root / "ml" / "data" / "features" / "model_b_features.csv"
        meta_path = self.repo_root / "ml" / "data" / "features" / "target_metadata.csv"
        model_path = self.repo_root / "models" / "ringguard_graph_xgb_v1.joblib"
        calib_path = self.repo_root / "models" / "calibrator_model_b.joblib"

        if not feat_path.exists() or not meta_path.exists():
            raise FileNotFoundError(f"Required features not found at {feat_path} or {meta_path}")

        df_b = pd.read_csv(feat_path, index_col=0)
        df_meta = pd.read_csv(meta_path, index_col=0)

        # Merge labels and metadata
        df_full = df_b.join(df_meta[["ground_truth_label", "is_ring", "timestamp"]], how="inner")

        # Load frozen Model B and Calibrator B for model score drift monitoring
        if model_path.exists() and calib_path.exists():
            model_b = joblib.load(model_path)
            calib_b = joblib.load(calib_path)

            # Extract 58 feature columns matching Model B training schema
            model_cols = [c for c in df_b.columns if c not in ["ground_truth_label", "is_ring", "timestamp", "transaction_id"]]
            X_all = df_b[model_cols]

            raw_preds = model_b.predict_proba(X_all)[:, 1]
            if hasattr(calib_b, "predict_calibrated_proba"):
                cal_preds = calib_b.predict_calibrated_proba(raw_preds)
            else:
                cal_preds = raw_preds

            df_full["model_b_raw_probability"] = raw_preds
            df_full["calibrated_risk_score"] = cal_preds
        else:
            df_full["model_b_raw_probability"] = 0.0
            df_full["calibrated_risk_score"] = 0.0

        # Create reconstructed channel category string from one-hot features
        channel_series = pd.Series("OTHER", index=df_full.index)
        for ch in ["upi", "imps", "card", "netbanking"]:
            col = f"tx_channel_{ch}"
            if col in df_full.columns:
                channel_series[df_full[col] == 1] = ch.upper()
        df_full["tx_channel"] = channel_series

        # Chronological partitions:
        # Train (N=1400, rows 0-1399), Val (N=300, rows 1400-1699), Test (N=300, rows 1700-1999)
        self.partitions = {
            "train": df_full.iloc[:1400].copy(),
            "val": df_full.iloc[1400:1700].copy(),
            "test": df_full.iloc[1700:2000].copy(),
        }

    @staticmethod
    def calculate_psi(
        ref: np.ndarray,
        comp: np.ndarray,
        num_bins: int = 10,
        eps: float = 1e-4,
    ) -> Tuple[float, DriftStatus, Optional[str]]:
        """Compute Population Stability Index (PSI) using deterministic reference quantile bins.

        Thresholds:
        PSI < 0.10 -> NORMAL
        0.10 <= PSI < 0.25 -> WATCH
        PSI >= 0.25 -> SIGNIFICANT_DRIFT
        """
        ref_clean = ref[~np.isnan(ref)]
        comp_clean = comp[~np.isnan(comp)]

        if len(ref_clean) < 10 or len(comp_clean) < 10:
            return 0.0, DriftStatus.UNAVAILABLE, "Insufficient non-null samples to construct stable bins"

        # Check for constant distributions
        if np.all(ref_clean == ref_clean[0]) and np.all(comp_clean == comp_clean[0]):
            if ref_clean[0] == comp_clean[0]:
                return 0.0, DriftStatus.NORMAL, "Identical constant distributions"
            else:
                return 1.0, DriftStatus.SIGNIFICANT_DRIFT, "Non-matching constant distributions"

        # Establish deterministic quantile bin edges on reference distribution
        quantiles = np.linspace(0, 1, num_bins + 1)
        bin_edges = np.percentile(ref_clean, quantiles * 100)
        bin_edges = np.unique(bin_edges)

        if len(bin_edges) < 2:
            return 0.0, DriftStatus.NORMAL, "Reference distribution has zero variance"

        # Extend outer edges to ensure all comparison samples are contained
        bin_edges[0] = min(bin_edges[0], float(np.min(comp_clean))) - 1e-6
        bin_edges[-1] = max(bin_edges[-1], float(np.max(comp_clean))) + 1e-6

        counts_ref, _ = np.histogram(ref_clean, bins=bin_edges)
        counts_comp, _ = np.histogram(comp_clean, bins=bin_edges)

        # Proportions with safe epsilon
        P = np.maximum(counts_ref / len(ref_clean), eps)
        Q = np.maximum(counts_comp / len(comp_clean), eps)
        P /= P.sum()
        Q /= Q.sum()

        psi = float(np.sum((Q - P) * np.log(Q / P)))

        # Precise threshold classification:
        # PSI < 0.10 -> NORMAL
        # 0.10 <= PSI < 0.25 -> WATCH
        # PSI >= 0.25 -> SIGNIFICANT_DRIFT
        if psi < 0.10:
            status = DriftStatus.NORMAL
        elif psi < 0.25:
            status = DriftStatus.WATCH
        else:
            status = DriftStatus.SIGNIFICANT_DRIFT

        return psi, status, None

    @staticmethod
    def calculate_jsd(
        ref_series: pd.Series,
        comp_series: pd.Series,
        eps: float = 1e-6,
    ) -> Tuple[float, DriftStatus, Optional[str]]:
        """Compute base-2 Jensen-Shannon Divergence (JSD) for categorical distributions."""
        ref_counts = ref_series.value_counts(dropna=True)
        comp_counts = comp_series.value_counts(dropna=True)

        categories = sorted(list(set(ref_counts.index).union(set(comp_counts.index))))
        if not categories:
            return 0.0, DriftStatus.UNAVAILABLE, "No discrete categories observed"

        N_ref = len(ref_series.dropna())
        N_comp = len(comp_series.dropna())
        if N_ref == 0 or N_comp == 0:
            return 0.0, DriftStatus.UNAVAILABLE, "Sample size is zero for comparison"

        P = np.array([ref_counts.get(c, 0) / N_ref for c in categories], dtype=float)
        Q = np.array([comp_counts.get(c, 0) / N_comp for c in categories], dtype=float)

        P = np.maximum(P, eps)
        Q = np.maximum(Q, eps)
        P /= P.sum()
        Q /= Q.sum()

        M = 0.5 * (P + Q)

        kl_pm = np.sum(P * np.log2(P / M))
        kl_qm = np.sum(Q * np.log2(Q / M))
        jsd = float(0.5 * kl_pm + 0.5 * kl_qm)

        if jsd < 0.10:
            status = DriftStatus.NORMAL
        elif jsd < 0.25:
            status = DriftStatus.WATCH
        else:
            status = DriftStatus.SIGNIFICANT_DRIFT

        return jsd, status, None

    @staticmethod
    def calculate_missingness_delta(
        ref_df: pd.DataFrame,
        comp_df: pd.DataFrame,
    ) -> Tuple[float, DriftStatus]:
        """Compute absolute delta in missing value rates."""
        ref_missing = float(ref_df.isna().sum().sum() / max(ref_df.size, 1))
        comp_missing = float(comp_df.isna().sum().sum() / max(comp_df.size, 1))
        delta = abs(comp_missing - ref_missing)

        if delta < 0.05:
            status = DriftStatus.NORMAL
        elif delta < 0.15:
            status = DriftStatus.WATCH
        else:
            status = DriftStatus.SIGNIFICANT_DRIFT

        return delta, status

    def evaluate_distribution_drift(
        self,
        reference_window: str = "train",
        comparison_window: str = "test",
    ) -> DriftMonitoringResponse:
        """Evaluate deterministic drift across all 15 monitored features and model context."""
        ref_df = self.partitions.get(reference_window.lower())
        comp_df = self.partitions.get(comparison_window.lower())

        if ref_df is None or comp_df is None:
            raise ValueError(f"Invalid window selection. Available: {list(self.partitions.keys())}")

        N_ref = len(ref_df)
        N_comp = len(comp_df)
        now_iso = datetime.now(timezone.utc).isoformat()

        # Define 15 monitored features:
        numeric_features = [
            ("tx_amount", "Transaction Amount"),
            ("beh_rolling_tx_count_1h", "Velocity (1h Tx Count)"),
            ("beh_rolling_tx_count_24h", "Velocity (24h Tx Count)"),
            ("beh_amount_to_hist_avg_ratio", "Amount to Historical Avg Ratio"),
            ("beh_is_new_device", "New Device Flag"),
            ("g_shared_device_accounts_count", "Shared Device Accounts Count"),
            ("g_shared_ip_accounts_count", "Shared IP Accounts Count"),
            ("g_shared_beneficiary_accounts_count", "Shared Beneficiary Accounts Count"),
            ("g_component_size", "Network Component Size"),
            ("g_degree", "Graph Degree"),
            ("model_b_raw_probability", "Model B Raw Probability"),
            ("calibrated_risk_score", "Calibrated Risk Score"),
        ]

        metrics: List[DriftMetric] = []
        significant_features: List[str] = []
        watch_features: List[str] = []

        # 1-12. Evaluate Numeric Features with PSI
        for col, label in numeric_features:
            if col in ref_df.columns and col in comp_df.columns:
                psi_val, status, limit = self.calculate_psi(
                    ref_df[col].to_numpy(dtype=float),
                    comp_df[col].to_numpy(dtype=float),
                )
                metrics.append(
                    DriftMetric(
                        feature_name=col,
                        metric_name="PSI",
                        metric_value=round(psi_val, 4),
                        threshold_watch=0.10,
                        threshold_significant=0.25,
                        status=status,
                        reference_window=reference_window,
                        comparison_window=comparison_window,
                        sample_size_reference=N_ref,
                        sample_size_comparison=N_comp,
                        limitations=limit,
                    )
                )
                if status == DriftStatus.SIGNIFICANT_DRIFT:
                    significant_features.append(col)
                elif status == DriftStatus.WATCH:
                    watch_features.append(col)

        # 13. Positive Label Rate (Ground truth positive prevalence)
        pos_ref = float(ref_df["is_ring"].mean()) if "is_ring" in ref_df.columns else 0.0
        pos_comp = float(comp_df["is_ring"].mean()) if "is_ring" in comp_df.columns else 0.0
        pos_delta = abs(pos_comp - pos_ref)
        pos_status = (
            DriftStatus.NORMAL if pos_delta < 0.05 else (DriftStatus.WATCH if pos_delta < 0.15 else DriftStatus.SIGNIFICANT_DRIFT)
        )
        metrics.append(
            DriftMetric(
                feature_name="positive_label_rate",
                metric_name="LABEL_PREVALENCE_DELTA",
                metric_value=round(pos_delta, 4),
                threshold_watch=0.05,
                threshold_significant=0.15,
                status=pos_status,
                reference_window=reference_window,
                comparison_window=comparison_window,
                sample_size_reference=N_ref,
                sample_size_comparison=N_comp,
                limitations="Evaluated strictly within controlled synthetic evaluation metadata.",
            )
        )
        if pos_status == DriftStatus.SIGNIFICANT_DRIFT:
            significant_features.append("positive_label_rate")
        elif pos_status == DriftStatus.WATCH:
            watch_features.append("positive_label_rate")

        # 14. Transaction Channel Distribution (JSD)
        jsd_val, jsd_status, jsd_limit = self.calculate_jsd(ref_df["tx_channel"], comp_df["tx_channel"])
        metrics.append(
            DriftMetric(
                feature_name="tx_channel",
                metric_name="JSD",
                metric_value=round(jsd_val, 4),
                threshold_watch=0.10,
                threshold_significant=0.25,
                status=jsd_status,
                reference_window=reference_window,
                comparison_window=comparison_window,
                sample_size_reference=N_ref,
                sample_size_comparison=N_comp,
                limitations=jsd_limit,
            )
        )
        if jsd_status == DriftStatus.SIGNIFICANT_DRIFT:
            significant_features.append("tx_channel")
        elif jsd_status == DriftStatus.WATCH:
            watch_features.append("tx_channel")

        # 15. Feature Missingness Delta
        miss_val, miss_status = self.calculate_missingness_delta(ref_df, comp_df)
        metrics.append(
            DriftMetric(
                feature_name="feature_missingness",
                metric_name="MISSINGNESS_DELTA",
                metric_value=round(miss_val, 4),
                threshold_watch=0.05,
                threshold_significant=0.15,
                status=miss_status,
                reference_window=reference_window,
                comparison_window=comparison_window,
                sample_size_reference=N_ref,
                sample_size_comparison=N_comp,
                limitations=None,
            )
        )
        if miss_status == DriftStatus.SIGNIFICANT_DRIFT:
            significant_features.append("feature_missingness")
        elif miss_status == DriftStatus.WATCH:
            watch_features.append("feature_missingness")

        # Overall Status Resolution by Precedence:
        # SIGNIFICANT_DRIFT > WATCH > NORMAL > UNAVAILABLE
        statuses = [m.status for m in metrics]
        if DriftStatus.SIGNIFICANT_DRIFT in statuses:
            overall_status = DriftStatus.SIGNIFICANT_DRIFT
        elif DriftStatus.WATCH in statuses:
            overall_status = DriftStatus.WATCH
        elif any(s == DriftStatus.NORMAL for s in statuses):
            overall_status = DriftStatus.NORMAL
        else:
            overall_status = DriftStatus.UNAVAILABLE

        # Performance comparison where ground truth exists
        perf_dict = {}
        for name, w_df in [(reference_window, ref_df), (comparison_window, comp_df)]:
            if "is_ring" in w_df.columns and "calibrated_risk_score" in w_df.columns:
                y_true = w_df["is_ring"].to_numpy()
                y_pred = (w_df["calibrated_risk_score"].to_numpy() >= 0.50).astype(int)
                y_prob = w_df["calibrated_risk_score"].to_numpy()

                tp = int(np.sum((y_pred == 1) & (y_true == 1)))
                fp = int(np.sum((y_pred == 1) & (y_true == 0)))
                tn = int(np.sum((y_pred == 0) & (y_true == 0)))
                fn = int(np.sum((y_pred == 0) & (y_true == 1)))

                prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
                rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
                fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
                fnr = float(fn / (tp + fn)) if (tp + fn) > 0 else 0.0
                brier = float(np.mean((y_prob - y_true) ** 2))

                perf_dict[name] = OutcomePerformanceMetric(
                    window_name=name,
                    sample_size=len(w_df),
                    positive_label_rate=round(float(y_true.mean()), 4),
                    precision=round(prec, 4),
                    recall=round(rec, 4),
                    false_positive_rate=round(fpr, 4),
                    false_negative_rate=round(fnr, 4),
                    brier_score=round(brier, 4),
                    status=OutcomeStatus.OUTCOME_CONFIRMED,
                )

        return DriftMonitoringResponse(
            evaluation_timestamp=now_iso,
            reference_window=reference_window,
            comparison_window=comparison_window,
            overall_status=overall_status,
            metrics=metrics,
            significant_features=significant_features,
            watch_features=watch_features,
            performance_comparison=perf_dict if perf_dict else None,
            human_review_required=True,
            disclaimer=(
                "SIMULATED / SYNTHETIC BENCHMARK — not real production outcomes. "
                "Drift telemetry is provided for decision support and monitoring only."
            ),
        )
