"""RingGuard AI — Counterfactual Attribution and Intervention Simulation Service.

Stage 18: Counterfactual Attribution + Intervention Simulation.
Provides deterministic, model-native What-If analytical capabilities:
1. Counterfactual Attribution: Identifies which observed features contribute most
   to the current Model B risk assessment using native XGBoost TreeSHAP contributions.
2. Intervention Simulation: Simulates hypothetical feature perturbations across
   explicitly whitelisted, semantically safe risk dimensions.

INVARIANTS:
- Model Immutability: Model B artifact is strictly read-only; never retrained or mutated.
- Risk Immutability: Production database records and stored risk scores are never overwritten.
- Defense-Only: Zero autonomous financial action; human approval required.
- Point-in-Time Safety: Source feature vectors respect historical timestamp boundary.
- Zero Causal Claims: Results represent model-sensitivity simulations, not causal proofs.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
import xgboost as xgb
from sqlalchemy.orm import Session

from app.services.model_service import get_model_service, ModelService
from app.services.feature_service import get_feature_service, FeatureService, TransactionNotFoundError
from ml.calibration.calibrator import RiskCalibrator
from app.counterfactual.schemas import (
    AttributionDirection,
    InterventionMode,
    PlausibilityStatus,
    CounterfactualAttribution,
    CounterfactualIntervention,
    CounterfactualAnalysisResponse,
    CustomInterventionRequest,
)

# ------------------------------------------------------------------------------
# 1. FEATURE WHITELIST & FORBIDDEN ATTRIBUTES
# ------------------------------------------------------------------------------

# Strict blacklist of attributes that must NEVER be perturbed
FORBIDDEN_PERTURBATION_FIELDS = {
    "transaction_id",
    "account_id",
    "customer_id",
    "user_id",
    "target",
    "is_ring",
    "is_fraud",
    "ground_truth_label",
    "scenario_type",
    "scenario_id",
    "timestamp",
    "dt_timestamp",
}

# Pre-computed legitimate training set medians (derived strictly from training split)
LEGITIMATE_MEDIANS: Dict[str, float] = {
    "tx_amount": 942.175,
    "tx_log_amount": 6.849247,
    "tx_hour": 11.0,
    "tx_day_of_week": 3.0,
    "tx_day_of_month": 11.0,
    "tx_is_weekend": 0.0,
    "tx_is_night": 0.0,
    "tx_is_transfer_p2p": 0.0,
    "tx_is_payment_p2m": 1.0,
    "tx_channel_upi": 0.0,
    "tx_channel_imps": 0.0,
    "tx_channel_card": 0.0,
    "tx_channel_netbanking": 0.0,
    "tx_has_beneficiary": 0.0,
    "tx_has_merchant": 1.0,
    "beh_account_age_days": 102.205,
    "beh_tx_sequence_num": 2.0,
    "beh_time_since_last_tx_sec": 256299.5,
    "beh_is_first_tx": 0.0,
    "beh_hist_tx_count": 1.0,
    "beh_hist_total_amount": 1018.035,
    "beh_hist_avg_amount": 660.695,
    "beh_hist_max_amount": 828.365,
    "beh_hist_std_amount": 0.0,
    "beh_amount_to_hist_avg_ratio": 1.0,
    "beh_rolling_tx_count_1h": 0.0,
    "beh_rolling_amount_1h": 0.0,
    "beh_rolling_tx_count_24h": 0.0,
    "beh_rolling_amount_24h": 0.0,
    "beh_rolling_tx_count_7d": 0.0,
    "beh_rolling_amount_7d": 0.0,
    "beh_hist_unique_devices": 1.0,
    "beh_hist_unique_ips": 1.0,
    "beh_hist_unique_beneficiaries": 0.0,
    "beh_is_new_device": 0.0,
    "beh_is_new_ip": 0.0,
    "beh_is_new_beneficiary": 0.0,
    "g_degree": 8.0,
    "g_in_degree": 1.0,
    "g_out_degree": 7.0,
    "g_device_count": 1.0,
    "g_ip_count": 1.0,
    "g_beneficiary_count": 1.0,
    "g_merchant_count": 1.0,
    "g_connected_accounts_count": 9.0,
    "g_shared_device_accounts_count": 4.0,
    "g_shared_ip_accounts_count": 3.0,
    "g_shared_beneficiary_accounts_count": 0.0,
    "g_has_shared_device": 1.0,
    "g_has_shared_ip": 1.0,
    "g_has_common_beneficiary": 0.0,
    "g_max_device_sharing_degree": 5.0,
    "g_max_ip_sharing_degree": 4.0,
    "g_max_beneficiary_sharing_degree": 1.0,
    "g_tx_count": 2.0,
    "g_total_tx_amount": 2445.46,
    "g_avg_tx_amount": 1119.005,
    "g_component_size": 1804.5,
}


class CounterfactualAttributionService:
    """Deterministic What-If analytical service for Model B risk assessments."""

    def __init__(
        self,
        db: Session,
        model_service: Optional[ModelService] = None,
        feature_service: Optional[FeatureService] = None,
        models_dir: Optional[Path] = None,
    ):
        self.db = db
        self.model_service = model_service or get_model_service()
        self.feature_service = feature_service or get_feature_service()

        if models_dir:
            self.models_dir = Path(models_dir)
        else:
            current_dir = Path(__file__).resolve().parent
            self.models_dir = current_dir.parents[2] / "models"

        self._calibrator_b: Optional[RiskCalibrator] = None
        self._load_calibrator()

    def _load_calibrator(self) -> None:
        """Load frozen post-hoc Model B calibrator if available."""
        calib_b_path = self.models_dir / "calibrator_model_b.joblib"
        if calib_b_path.exists():
            try:
                self._calibrator_b = RiskCalibrator.load(calib_b_path)
            except Exception:
                self._calibrator_b = None

    def _calibrate(self, raw_p: float) -> float:
        """Apply frozen calibrator to raw probability."""
        if self._calibrator_b is not None:
            calib = float(self._calibrator_b.predict_calibrated_proba([raw_p])[0])
            return round(max(0.0, min(1.0, calib)), 4)
        return round(max(0.0, min(1.0, raw_p)), 4)

    # --------------------------------------------------------------------------
    # 2. DETERMINISTIC COUNTERFACTUAL ATTRIBUTION
    # --------------------------------------------------------------------------

    def compute_attributions(
        self,
        transaction_id: str,
    ) -> Tuple[List[CounterfactualAttribution], float, float, pd.DataFrame, Any]:
        """Compute exact TreeSHAP log-odds feature contributions for Model B.

        Deterministic tie-breaking rule:
        1. Absolute contribution descending: -abs(contribution)
        2. Feature name ascending: feature_name
        """
        clean_id = transaction_id.strip()
        feats_df, tx = self.feature_service.get_features(self.db, clean_id, "graph")

        booster = self.model_service.model_b.get_booster()
        dmat = xgb.DMatrix(feats_df)

        # Exact native TreeSHAP in XGBoost: shape (1, 59) where last col is bias/intercept
        contribs = booster.predict(dmat, pred_contribs=True)[0]
        feat_contribs = contribs[:-1]
        feature_names = self.model_service.features_b

        raw_prob = float(self.model_service.model_b.predict_proba(feats_df)[0, 1])
        calibrated_risk = self._calibrate(raw_prob)

        # Construct raw attributions
        raw_attributions = []
        for name, c in zip(feature_names, feat_contribs):
            val = float(feats_df[name].iloc[0])
            c_float = float(c)

            if abs(c_float) < 1e-5:
                direction = AttributionDirection.NEUTRAL
            elif c_float > 0:
                direction = AttributionDirection.INCREASES_RISK
            else:
                direction = AttributionDirection.DECREASES_RISK

            # Factual domain explanation
            explanation = self._generate_feature_explanation(name, val, c_float, direction)

            raw_attributions.append({
                "feature_name": name,
                "actual_value": round(val, 4),
                "contribution": round(c_float, 4),
                "direction": direction,
                "explanation": explanation,
                "source": "model_b_treeshape",
            })

        # Deterministic sorting: highest absolute contribution first, then alphabetical tie-breaker
        raw_attributions.sort(key=lambda x: (-abs(x["contribution"]), x["feature_name"]))

        attributions = [
            CounterfactualAttribution(
                feature_name=item["feature_name"],
                actual_value=item["actual_value"],
                contribution=item["contribution"],
                direction=item["direction"],
                attribution_rank=idx + 1,
                explanation=item["explanation"],
                source=item["source"],
            )
            for idx, item in enumerate(raw_attributions)
        ]

        return attributions, calibrated_risk, raw_prob, feats_df, tx

    def _generate_feature_explanation(
        self,
        feature_name: str,
        value: float,
        contribution: float,
        direction: AttributionDirection,
    ) -> str:
        """Generate factual, neutral explanation for feature attribution."""
        direction_phrase = (
            "elevates model risk assessment"
            if direction == AttributionDirection.INCREASES_RISK
            else "moderates model risk assessment"
            if direction == AttributionDirection.DECREASES_RISK
            else "has neutral sensitivity in this context"
        )

        if feature_name == "tx_amount":
            return f"Observed transaction amount of ₹{value:,.2f} {direction_phrase} (margin impact: {contribution:+.4f})."
        elif feature_name == "tx_log_amount":
            return f"Log-transformed transaction scale ({value:.2f}) {direction_phrase}."
        elif feature_name.startswith("g_shared_device"):
            return f"Account connected to {int(value)} other accounts via shared device endpoints ({direction_phrase})."
        elif feature_name == "g_has_shared_device":
            status = "present" if value > 0.5 else "absent"
            return f"Device sharing relationship is {status} ({direction_phrase})."
        elif feature_name.startswith("g_shared_ip"):
            return f"Account shares IP infrastructure with {int(value)} other accounts ({direction_phrase})."
        elif feature_name.startswith("g_shared_beneficiary"):
            return f"Account shares common beneficiaries with {int(value)} other accounts ({direction_phrase})."
        elif feature_name == "g_component_size":
            return f"Entity cluster spans {int(value)} connected nodes in historical graph ({direction_phrase})."
        elif feature_name.startswith("beh_rolling"):
            return f"Recent activity window shows {value:.1f} volume/count intensity ({direction_phrase})."
        else:
            return f"Observed feature value of {value:.4f} {direction_phrase} (log-odds contribution: {contribution:+.4f})."

    # --------------------------------------------------------------------------
    # 3. INTERVENTION SIMULATION (WHAT-IF SENSITIVITY)
    # --------------------------------------------------------------------------

    def simulate_interventions(
        self,
        transaction_id: str,
        feats_df: Optional[pd.DataFrame] = None,
        original_risk_score: Optional[float] = None,
    ) -> List[CounterfactualIntervention]:
        """Simulate standard suite of 7 semantically safe hypothetical interventions."""
        clean_id = transaction_id.strip()
        if feats_df is None or original_risk_score is None:
            feats_df, tx = self.feature_service.get_features(self.db, clean_id, "graph")
            raw_p = float(self.model_service.model_b.predict_proba(feats_df)[0, 1])
            original_risk_score = self._calibrate(raw_p)

        interventions: List[CounterfactualIntervention] = []

        # 1. Remove Shared Devices
        cf_dev = feats_df.copy()
        cf_dev["g_shared_device_accounts_count"] = 0.0
        cf_dev["g_has_shared_device"] = 0.0
        cf_dev["g_max_device_sharing_degree"] = 0.0
        cf_dev["beh_hist_unique_devices"] = 1.0
        cf_dev["beh_is_new_device"] = 0.0
        p_cf_dev = self._calibrate(float(self.model_service.model_b.predict_proba(cf_dev)[0, 1]))
        interventions.append(self._build_intervention_record(
            intervention_id="INT_REMOVE_SHARED_DEVICES",
            feature_name="g_shared_device_accounts_count",
            original_val=float(feats_df["g_shared_device_accounts_count"].iloc[0]),
            counterfactual_val=0.0,
            orig_risk=original_risk_score,
            cf_risk=p_cf_dev,
            mode=InterventionMode.REMOVE_RISK_SIGNAL,
            plausibility=PlausibilityStatus.PLAUSIBLE,
            assumption="Simulates hypothetical removal of all device-sharing links and device hops associated with this account.",
        ))

        # 2. Remove Shared IPs
        cf_ip = feats_df.copy()
        cf_ip["g_shared_ip_accounts_count"] = 0.0
        cf_ip["g_has_shared_ip"] = 0.0
        cf_ip["g_max_ip_sharing_degree"] = 0.0
        cf_ip["beh_hist_unique_ips"] = 1.0
        cf_ip["beh_is_new_ip"] = 0.0
        p_cf_ip = self._calibrate(float(self.model_service.model_b.predict_proba(cf_ip)[0, 1]))
        interventions.append(self._build_intervention_record(
            intervention_id="INT_REMOVE_SHARED_IPS",
            feature_name="g_shared_ip_accounts_count",
            original_val=float(feats_df["g_shared_ip_accounts_count"].iloc[0]),
            counterfactual_val=0.0,
            mode=InterventionMode.REMOVE_RISK_SIGNAL,
            plausibility=PlausibilityStatus.PLAUSIBLE,
            orig_risk=original_risk_score,
            cf_risk=p_cf_ip,
            assumption="Simulates hypothetical removal of shared IP infrastructure and multi-account proxy reuse.",
        ))

        # 3. Remove Common Beneficiaries
        cf_ben = feats_df.copy()
        cf_ben["g_shared_beneficiary_accounts_count"] = 0.0
        cf_ben["g_has_common_beneficiary"] = 0.0
        cf_ben["g_max_beneficiary_sharing_degree"] = 0.0
        cf_ben["beh_is_new_beneficiary"] = 0.0
        p_cf_ben = self._calibrate(float(self.model_service.model_b.predict_proba(cf_ben)[0, 1]))
        interventions.append(self._build_intervention_record(
            intervention_id="INT_REMOVE_COMMON_BENEFICIARIES",
            feature_name="g_shared_beneficiary_accounts_count",
            original_val=float(feats_df["g_shared_beneficiary_accounts_count"].iloc[0]),
            counterfactual_val=0.0,
            orig_risk=original_risk_score,
            cf_risk=p_cf_ben,
            mode=InterventionMode.REMOVE_RISK_SIGNAL,
            plausibility=PlausibilityStatus.PLAUSIBLE,
            assumption="Simulates hypothetical removal of shared beneficiary links connecting to other flagged ring entities.",
        ))

        # 4. Reduce Transaction Amount to Median (₹942.00)
        cf_amt = feats_df.copy()
        cf_amt["tx_amount"] = 942.0
        cf_amt["tx_log_amount"] = float(np.log1p(942.0))
        cf_amt["beh_amount_to_hist_avg_ratio"] = 1.0
        p_cf_amt = self._calibrate(float(self.model_service.model_b.predict_proba(cf_amt)[0, 1]))
        interventions.append(self._build_intervention_record(
            intervention_id="INT_REDUCE_AMOUNT_TO_MEDIAN",
            feature_name="tx_amount",
            original_val=float(feats_df["tx_amount"].iloc[0]),
            counterfactual_val=942.0,
            orig_risk=original_risk_score,
            cf_risk=p_cf_amt,
            mode=InterventionMode.REDUCE_RISK_SIGNAL,
            plausibility=PlausibilityStatus.PLAUSIBLE,
            assumption="Simulates hypothetical reduction of transaction exposure to legitimate portfolio median (₹942.00) while maintaining log-amount consistency.",
        ))

        # 5. Reduce Velocity Burst
        cf_vel = feats_df.copy()
        cf_vel["beh_rolling_tx_count_1h"] = 0.0
        cf_vel["beh_rolling_amount_1h"] = 0.0
        cf_vel["beh_rolling_tx_count_24h"] = 0.0
        cf_vel["beh_rolling_amount_24h"] = 0.0
        cf_vel["beh_time_since_last_tx_sec"] = 86400.0
        p_cf_vel = self._calibrate(float(self.model_service.model_b.predict_proba(cf_vel)[0, 1]))
        interventions.append(self._build_intervention_record(
            intervention_id="INT_REDUCE_VELOCITY_BURST",
            feature_name="beh_rolling_tx_count_1h",
            original_val=float(feats_df["beh_rolling_tx_count_1h"].iloc[0]),
            counterfactual_val=0.0,
            orig_risk=original_risk_score,
            cf_risk=p_cf_vel,
            mode=InterventionMode.REDUCE_RISK_SIGNAL,
            plausibility=PlausibilityStatus.PLAUSIBLE,
            assumption="Simulates hypothetical absence of rapid transaction bursts in rolling 1h and 24h activity windows.",
        ))

        # 6. Isolate Network Connectivity
        cf_iso = feats_df.copy()
        cf_iso["g_degree"] = 1.0
        cf_iso["g_in_degree"] = 0.0
        cf_iso["g_out_degree"] = 1.0
        cf_iso["g_connected_accounts_count"] = 1.0
        cf_iso["g_component_size"] = 2.0
        cf_iso["g_shared_device_accounts_count"] = 0.0
        cf_iso["g_shared_ip_accounts_count"] = 0.0
        cf_iso["g_shared_beneficiary_accounts_count"] = 0.0
        cf_iso["g_has_shared_device"] = 0.0
        cf_iso["g_has_shared_ip"] = 0.0
        cf_iso["g_has_common_beneficiary"] = 0.0
        p_cf_iso = self._calibrate(float(self.model_service.model_b.predict_proba(cf_iso)[0, 1]))
        interventions.append(self._build_intervention_record(
            intervention_id="INT_ISOLATE_NETWORK",
            feature_name="g_connected_accounts_count",
            original_val=float(feats_df["g_connected_accounts_count"].iloc[0]),
            counterfactual_val=1.0,
            orig_risk=original_risk_score,
            cf_risk=p_cf_iso,
            mode=InterventionMode.REMOVE_RISK_SIGNAL,
            plausibility=PlausibilityStatus.HYPOTHETICAL,
            assumption="Simulates hypothetical complete severance of multi-party cluster connections, collapsing graph to isolated bilateral edge.",
        ))

        # 7. Full Legitimate Baseline Comparison
        cf_base = feats_df.copy()
        for col, med_val in LEGITIMATE_MEDIANS.items():
            if col in cf_base.columns:
                cf_base[col] = med_val
        p_cf_base = self._calibrate(float(self.model_service.model_b.predict_proba(cf_base)[0, 1]))
        interventions.append(self._build_intervention_record(
            intervention_id="INT_BASELINE_COMPARISON",
            feature_name="full_feature_vector",
            original_val="observed_vector",
            counterfactual_val="legitimate_portfolio_medians",
            orig_risk=original_risk_score,
            cf_risk=p_cf_base,
            mode=InterventionMode.BASELINE_COMPARISON,
            plausibility=PlausibilityStatus.HYPOTHETICAL,
            assumption="Synthesizes an idealized reference profile from training-set medians to evaluate aggregate anomaly distance.",
        ))

        return interventions

    def _build_intervention_record(
        self,
        intervention_id: str,
        feature_name: str,
        original_val: Any,
        counterfactual_val: Any,
        orig_risk: float,
        cf_risk: float,
        mode: InterventionMode,
        plausibility: PlausibilityStatus,
        assumption: str,
    ) -> CounterfactualIntervention:
        """Construct validated CounterfactualIntervention record."""
        delta = round(cf_risk - orig_risk, 4)
        if abs(delta) < 1e-4:
            direction = AttributionDirection.NEUTRAL
        elif delta > 0:
            direction = AttributionDirection.INCREASES_RISK
        else:
            direction = AttributionDirection.DECREASES_RISK

        return CounterfactualIntervention(
            intervention_id=intervention_id,
            feature_name=feature_name,
            original_value=original_val,
            counterfactual_value=counterfactual_val,
            original_risk_score=orig_risk,
            counterfactual_risk_score=cf_risk,
            risk_delta=delta,
            direction=direction,
            intervention_mode=mode,
            plausibility_status=plausibility,
            assumption=assumption,
            disclaimer="Simulated model sensitivity under hypothetical feature change; not a causal claim or real-world guarantee.",
        )

    # --------------------------------------------------------------------------
    # 4. CUSTOM PERTURBATION SIMULATION
    # --------------------------------------------------------------------------

    def simulate_custom_intervention(
        self,
        transaction_id: str,
        feature_name: str,
        target_value: float,
    ) -> CounterfactualIntervention:
        """Simulate custom single-feature perturbation requested by analyst."""
        clean_id = transaction_id.strip()
        clean_feat = feature_name.strip()

        feats_df, tx = self.feature_service.get_features(self.db, clean_id, "graph")
        raw_p = float(self.model_service.model_b.predict_proba(feats_df)[0, 1])
        original_risk_score = self._calibrate(raw_p)

        # 1. Security check: Reject forbidden identifiers, labels, and timestamps
        if clean_feat in FORBIDDEN_PERTURBATION_FIELDS:
            return CounterfactualIntervention(
                intervention_id=f"INT_CUSTOM_{clean_feat.upper()}_BLOCKED",
                feature_name=clean_feat,
                original_value="RESTRICTED",
                counterfactual_value=target_value,
                original_risk_score=original_risk_score,
                counterfactual_risk_score=original_risk_score,
                risk_delta=0.0,
                direction=AttributionDirection.NEUTRAL,
                intervention_mode=InterventionMode.CUSTOM_PERTURBATION,
                plausibility_status=PlausibilityStatus.UNAVAILABLE,
                assumption=f"Feature '{clean_feat}' is an immutable identifier, label, or metadata field and cannot be safely perturbed.",
                disclaimer="Perturbation unavailable due to feature security constraints.",
            )

        # 2. Check if feature exists in Model B feature space
        if clean_feat not in self.model_service.features_b:
            return CounterfactualIntervention(
                intervention_id=f"INT_CUSTOM_{clean_feat.upper()}_UNKNOWN",
                feature_name=clean_feat,
                original_value="NOT_FOUND",
                counterfactual_value=target_value,
                original_risk_score=original_risk_score,
                counterfactual_risk_score=original_risk_score,
                risk_delta=0.0,
                direction=AttributionDirection.NEUTRAL,
                intervention_mode=InterventionMode.CUSTOM_PERTURBATION,
                plausibility_status=PlausibilityStatus.UNAVAILABLE,
                assumption=f"Feature '{clean_feat}' is not a recognized feature in Model B (58 features).",
                disclaimer="Perturbation unavailable because feature does not exist in model architecture.",
            )

        # 3. Apply perturbation while preserving coupled mathematical consistency
        cf_df = feats_df.copy()
        orig_val = float(cf_df[clean_feat].iloc[0])
        cf_df[clean_feat] = float(target_value)

        # Coupled feature integrity: tx_amount and tx_log_amount
        if clean_feat == "tx_amount":
            cf_df["tx_log_amount"] = float(np.log1p(max(0.0, target_value)))
        elif clean_feat == "tx_log_amount":
            cf_df["tx_amount"] = float(np.expm1(target_value))

        # Binary consistency for shared flags
        if clean_feat == "g_shared_device_accounts_count":
            cf_df["g_has_shared_device"] = 1.0 if target_value > 0 else 0.0
        elif clean_feat == "g_shared_ip_accounts_count":
            cf_df["g_has_shared_ip"] = 1.0 if target_value > 0 else 0.0
        elif clean_feat == "g_shared_beneficiary_accounts_count":
            cf_df["g_has_common_beneficiary"] = 1.0 if target_value > 0 else 0.0

        p_cf = self._calibrate(float(self.model_service.model_b.predict_proba(cf_df)[0, 1]))

        return self._build_intervention_record(
            intervention_id=f"INT_CUSTOM_{clean_feat.upper()}",
            feature_name=clean_feat,
            original_val=orig_val,
            counterfactual_val=target_value,
            orig_risk=original_risk_score,
            cf_risk=p_cf,
            mode=InterventionMode.CUSTOM_PERTURBATION,
            plausibility=PlausibilityStatus.HYPOTHETICAL,
            assumption=f"Custom analyst perturbation: hypothetically set '{clean_feat}' to {target_value}.",
        )

    # --------------------------------------------------------------------------
    # 5. COMPLETE COUNTERFACTUAL ANALYSIS SESSION
    # --------------------------------------------------------------------------

    def analyze_transaction(
        self,
        transaction_id: str,
    ) -> CounterfactualAnalysisResponse:
        """Run complete Counterfactual Attribution and Intervention session."""
        clean_id = transaction_id.strip()

        attributions, calibrated_risk, raw_prob, feats_df, tx = self.compute_attributions(clean_id)
        interventions = self.simulate_interventions(clean_id, feats_df, calibrated_risk)

        strongest_attribution = attributions[0] if attributions else None

        # Identify intervention resulting in largest downward risk delta
        reducing_interventions = [
            i for i in interventions if i.direction == AttributionDirection.DECREASES_RISK
        ]
        if reducing_interventions:
            largest_reducing_delta = min(reducing_interventions, key=lambda x: x.risk_delta)
        else:
            largest_reducing_delta = interventions[0] if interventions else None

        return CounterfactualAnalysisResponse(
            transaction_id=clean_id,
            account_id=tx.account_id,
            timestamp=tx.timestamp.isoformat(),
            model_name="ringguard_graph_xgb_v1",
            model_version="v1",
            original_risk_score=calibrated_risk,
            original_probability_raw=round(raw_prob, 4),
            attributions=attributions,
            interventions=interventions,
            strongest_model_attribution=strongest_attribution,
            largest_simulated_risk_delta=largest_reducing_delta,
            human_approval_required=True,
            defense_only=True,
            disclaimer="Counterfactual results are model-sensitivity simulations, not causal claims and not predictions of what would necessarily happen in the real world.",
        )
