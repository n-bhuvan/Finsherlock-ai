"""RingGuard AI — Feature Isolation / Graph Feature Sensitivity Service.

Stage 12: Final Packaging & Submission Readiness.
Evaluates in-silico model sensitivity by replacing Model B's 21 point-in-time graph
features with mathematically verified isolated-entity baseline values, holding
all 37 transaction and behavioral features constant.
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from sqlalchemy.orm import Session

from app.services.model_service import get_model_service, ModelService
from app.services.feature_service import get_feature_service, FeatureService, TransactionNotFoundError
from app.evidence.engine import EvidenceEngine
from app.evidence.schemas import EvidenceType
from app.schemas.risk import FeatureIsolationResponse, GraphAttributionItem, RiskBand

# Top graph features in Model B by Gini importance (from Stage 7 evaluation artifact)
GRAPH_FEATURE_IMPORTANCE_RANKS: Dict[str, Dict[str, Any]] = {
    "g_merchant_count": {"rank": 3, "importance": 0.186906},
    "g_total_tx_amount": {"rank": 4, "importance": 0.102033},
    "g_avg_tx_amount": {"rank": 5, "importance": 0.045146},
    "g_component_size": {"rank": 6, "importance": 0.012204},
    "g_shared_ip_accounts_count": {"rank": 10, "importance": 0.000692},
    "g_connected_accounts_count": {"rank": 11, "importance": 0.000661},
    "g_max_ip_sharing_degree": {"rank": 12, "importance": 0.000571},
    "g_shared_device_accounts_count": {"rank": 14, "importance": 0.000334},
    "g_max_device_sharing_degree": {"rank": 15, "importance": 0.000296},
    "g_degree": {"rank": 47, "importance": 0.0},
    "g_in_degree": {"rank": 46, "importance": 0.0},
    "g_out_degree": {"rank": 45, "importance": 0.0},
    "g_device_count": {"rank": 44, "importance": 0.0},
    "g_ip_count": {"rank": 43, "importance": 0.0},
    "g_shared_beneficiary_accounts_count": {"rank": 53, "importance": 0.0},
    "g_beneficiary_count": {"rank": 54, "importance": 0.0},
    "g_has_shared_device": {"rank": 52, "importance": 0.0},
    "g_has_shared_ip": {"rank": 55, "importance": 0.0},
    "g_has_common_beneficiary": {"rank": 56, "importance": 0.0},
    "g_max_beneficiary_sharing_degree": {"rank": 57, "importance": 0.0},
    "g_tx_count": {"rank": 58, "importance": 0.0},
}

ALL_21_GRAPH_FEATURES: List[str] = [
    "g_degree",
    "g_in_degree",
    "g_out_degree",
    "g_device_count",
    "g_ip_count",
    "g_beneficiary_count",
    "g_merchant_count",
    "g_connected_accounts_count",
    "g_shared_device_accounts_count",
    "g_shared_ip_accounts_count",
    "g_shared_beneficiary_accounts_count",
    "g_has_shared_device",
    "g_has_shared_ip",
    "g_has_common_beneficiary",
    "g_max_device_sharing_degree",
    "g_max_ip_sharing_degree",
    "g_max_beneficiary_sharing_degree",
    "g_tx_count",
    "g_total_tx_amount",
    "g_avg_tx_amount",
    "g_component_size",
]


class FeatureIsolationService:
    """Computes in-silico feature-isolation analysis and evidence provenance mapping."""

    def __init__(
        self,
        model_service: Optional[ModelService] = None,
        feature_service: Optional[FeatureService] = None,
    ):
        self.model_service = model_service or get_model_service()
        self.feature_service = feature_service or get_feature_service()

    def evaluate_feature_isolation(self, db: Session, transaction_id: str) -> FeatureIsolationResponse:
        """Run feature-isolation sensitivity analysis for a verified transaction.
        
        Args:
            db: Active SQLAlchemy session.
            transaction_id: Clean transaction ID string.
            
        Returns:
            FeatureIsolationResponse schema with exact model predictions and metadata.
        """
        # 1. Retrieve verified transaction features from feature store
        feats_df, txn = self.feature_service.get_features(db, transaction_id, model_type="graph")
        orig_prob = self.model_service.predict_graph(feats_df)
        orig_band = self.model_service.determine_risk_band(orig_prob)

        # 2. Derive mathematically plausible isolated-entity baseline values (Stage 5 semantics)
        amt = float(feats_df["tx_amount"].values[0])
        has_ben = int(feats_df["tx_has_beneficiary"].values[0])
        has_mer = int(feats_df["tx_has_merchant"].values[0])

        baseline_values: Dict[str, float] = {
            "g_in_degree": 1.0,  # 1 incoming 'owns' edge from customer
            "g_out_degree": float(3 + has_ben + has_mer),  # participates + device + ip + [ben/mer]
            "g_degree": float(1 + (3 + has_ben + has_mer)),  # in_degree + out_degree
            "g_device_count": 1.0,  # transaction's own hardware device
            "g_ip_count": 1.0,  # transaction's own IP address
            "g_beneficiary_count": float(has_ben),  # transaction's own recipient
            "g_merchant_count": float(has_mer),  # transaction's own merchant
            "g_connected_accounts_count": 0.0,  # zero connected accounts
            "g_shared_device_accounts_count": 0.0,  # zero shared devices
            "g_shared_ip_accounts_count": 0.0,  # zero shared IPs
            "g_shared_beneficiary_accounts_count": 0.0,  # zero shared beneficiaries
            "g_has_shared_device": 0.0,  # flag: false
            "g_has_shared_ip": 0.0,  # flag: false
            "g_has_common_beneficiary": 0.0,  # flag: false
            "g_max_device_sharing_degree": 1.0,  # only 1 account on device (self)
            "g_max_ip_sharing_degree": 1.0,  # only 1 account on IP (self)
            "g_max_beneficiary_sharing_degree": 1.0,  # only 1 account on beneficiary (self)
            "g_tx_count": 1.0,  # isolated transaction count
            "g_total_tx_amount": amt,  # isolated volume equals current tx amount
            "g_avg_tx_amount": amt,  # isolated volume equals current tx amount
            "g_component_size": float(5 + has_ben + has_mer),  # customer+account+tx+dev+ip+[ben/mer]
        }

        # 3. Construct isolated feature vector (holding all 37 transaction/behavior features constant)
        isolated_df = feats_df.copy()
        for feat_name, base_val in baseline_values.items():
            isolated_df[feat_name] = base_val

        # 4. Predict on isolated feature vector
        isolated_prob = self.model_service.predict_graph(isolated_df)
        isolated_band = self.model_service.determine_risk_band(isolated_prob)

        delta = orig_prob - isolated_prob
        pct_point_delta = delta * 100.0

        # 5. Provenance-Grounded Evidence Mapping: link top graph features to Stage 9 evidence
        evidence_engine = EvidenceEngine(db)
        try:
            ev_list = evidence_engine.extract_evidence_for_transaction(transaction_id)
            evidence_items = ev_list.items
        except Exception:
            evidence_items = []

        # Build evidence type lookup
        ev_by_type: Dict[EvidenceType, Any] = {}
        for ev in evidence_items:
            if ev.evidence_type not in ev_by_type:
                ev_by_type[ev.evidence_type] = ev

        attributions: List[GraphAttributionItem] = []
        # Sort graph features by Model B importance rank
        sorted_features = sorted(
            GRAPH_FEATURE_IMPORTANCE_RANKS.items(),
            key=lambda x: x[1]["rank"],
        )

        for feat_name, meta in sorted_features[:9]:  # Top 9 contributing graph features
            orig_val = float(feats_df[feat_name].values[0])
            iso_val = baseline_values.get(feat_name, 0.0)

            # Determine matching Stage 9 evidence type
            matched_ev = None
            if feat_name in ("g_shared_device_accounts_count", "g_max_device_sharing_degree", "g_has_shared_device"):
                matched_ev = ev_by_type.get(EvidenceType.SHARED_DEVICE)
            elif feat_name in ("g_shared_ip_accounts_count", "g_max_ip_sharing_degree", "g_has_shared_ip"):
                matched_ev = ev_by_type.get(EvidenceType.SHARED_IP)
            elif feat_name in ("g_shared_beneficiary_accounts_count", "g_max_beneficiary_sharing_degree", "g_has_common_beneficiary"):
                matched_ev = ev_by_type.get(EvidenceType.COMMON_BENEFICIARY)
            elif feat_name == "g_connected_accounts_count":
                matched_ev = ev_by_type.get(EvidenceType.RELATED_ACCOUNT) or ev_by_type.get(EvidenceType.MULTI_HOP_CONNECTION)
            elif feat_name == "g_component_size":
                matched_ev = ev_by_type.get(EvidenceType.NETWORK_CONTEXT)
            elif feat_name in ("g_total_tx_amount", "g_avg_tx_amount"):
                matched_ev = ev_by_type.get(EvidenceType.RAPID_FUND_FLOW) or ev_by_type.get(EvidenceType.LARGE_INCOMING_TRANSACTION)
            elif feat_name == "g_merchant_count":
                matched_ev = ev_by_type.get(EvidenceType.TRANSACTION_ACTIVITY)

            ev_id = matched_ev.evidence_id if matched_ev else None
            ev_type = matched_ev.evidence_type.value if matched_ev else None
            status = "VERIFIED" if matched_ev else "FEATURE_ONLY"

            attributions.append(
                GraphAttributionItem(
                    feature_name=feat_name,
                    feature_group="graph",
                    importance_rank_in_model_b=meta["rank"],
                    original_value=orig_val,
                    isolated_value=iso_val,
                    corroborating_evidence_id=ev_id,
                    corroborating_evidence_type=ev_type,
                    provenance_status=status,
                )
            )

        return FeatureIsolationResponse(
            transaction_id=transaction_id,
            original_probability=orig_prob,
            isolated_probability=isolated_prob,
            delta=round(delta, 8),
            percentage_point_delta=round(pct_point_delta, 4),
            risk_band_original=orig_band,
            risk_band_isolated=isolated_band,
            isolated_features_count=21,
            isolated_features=ALL_21_GRAPH_FEATURES,
            baseline_values_used=baseline_values,
            attributions=attributions,
        )


_feature_isolation_service: Optional[FeatureIsolationService] = None


def get_feature_isolation_service() -> FeatureIsolationService:
    """Retrieve or initialize global FeatureIsolationService singleton."""
    global _feature_isolation_service
    if _feature_isolation_service is None:
        _feature_isolation_service = FeatureIsolationService()
    return _feature_isolation_service
