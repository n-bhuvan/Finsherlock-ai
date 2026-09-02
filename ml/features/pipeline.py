"""RingGuard AI — Feature Engineering Pipeline.

Stage 5: Feature Engineering.
Orchestrates point-in-time extraction for transaction, behavioral, and graph features.
Builds strictly aligned contracts for Model A (Transaction + Behavior) and
Model B (Transaction + Behavior + Point-in-Time Graph), while isolating target labels.
"""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from ml.features.transaction import TransactionFeatureExtractor, TRANSACTION_FEATURE_COLUMNS
from ml.features.behavior import PointInTimeBehaviorExtractor, BEHAVIORAL_FEATURE_COLUMNS
from ml.features.graph import PointInTimeGraphExtractor, POINT_IN_TIME_GRAPH_FEATURE_COLUMNS
from ml.features.validator import FeatureValidator


class FeaturePipeline:
    """Full Feature Engineering Pipeline enforcing point-in-time safety and target isolation."""

    def __init__(self, session: Optional[Session] = None, data_dir: Optional[str] = None):
        """Initialize pipeline with PostgreSQL session or CSV directory."""
        self.session = session
        self.data_dir = Path(data_dir) if data_dir else None

    def _load_data_from_db(self) -> Dict[str, pd.DataFrame]:
        """Load entity tables from PostgreSQL."""
        if not self.session:
            raise ValueError("No database session provided.")

        tables = ["customers", "accounts", "devices", "ips", "beneficiaries", "merchants", "transactions"]
        dfs = {}
        for tbl in tables:
            q = f"SELECT * FROM {tbl} ORDER BY 1 ASC;"
            res = self.session.execute(text(q))
            dfs[tbl] = pd.DataFrame(res.fetchall(), columns=res.keys())
        return dfs

    def _load_data_from_csv(self) -> Dict[str, pd.DataFrame]:
        """Load entity tables from Stage 2 CSVs."""
        if not self.data_dir:
            raise ValueError("No data directory provided.")

        tables = ["customers", "accounts", "devices", "ips", "beneficiaries", "merchants", "transactions"]
        dfs = {}
        for tbl in tables:
            fpath = self.data_dir / f"{tbl}.csv"
            dfs[tbl] = pd.read_csv(fpath, keep_default_na=False)
        return dfs

    def load_data(self) -> Dict[str, pd.DataFrame]:
        """Load raw relational data from DB or CSV fallback."""
        if self.session:
            return self._load_data_from_db()
        elif self.data_dir:
            return self._load_data_from_csv()
        else:
            raise ValueError("Neither DB session nor data_dir provided.")

    def run_pipeline(
        self,
        output_dir: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """Execute full feature engineering pipeline.
        
        Returns:
            (X_model_a, X_model_b, target_metadata, manifest_dict)
        """
        dfs = self.load_data()
        df_tx = dfs["transactions"].copy()
        df_acc = dfs["accounts"].copy()

        # Sort transactions chronologically for deterministic processing
        df_tx["dt_timestamp"] = pd.to_datetime(df_tx["timestamp"], utc=True)
        df_tx = df_tx.sort_values(by=["dt_timestamp", "transaction_id"]).reset_index(drop=True)

        # 1. Extract Transaction Features (Instantaneous)
        tx_extractor = TransactionFeatureExtractor()
        df_feats_tx = tx_extractor.extract_features(df_tx)

        # 2. Extract Behavioral Features (Point-in-Time Historical & Velocity)
        beh_extractor = PointInTimeBehaviorExtractor(df_acc)
        df_feats_beh = beh_extractor.extract_features(df_tx)

        # 3. Extract Graph Features (Point-in-Time Graph Topology)
        graph_extractor = PointInTimeGraphExtractor(dfs)
        df_feats_graph = graph_extractor.extract_features(df_tx)

        # 4. Construct Model A & Model B Feature Matrices
        # Model A: Transaction + Behavior
        X_model_a = pd.concat([df_feats_tx, df_feats_beh], axis=1)

        # Model B: Transaction + Behavior + Point-in-Time Graph
        X_model_b = pd.concat([df_feats_tx, df_feats_beh, df_feats_graph], axis=1)

        # 5. Construct Isolated Target and Metadata Contract
        target_records = []
        for _, r in df_tx.iterrows():
            txid = str(r["transaction_id"])
            aid = str(r["account_id"])
            lbl = str(r["ground_truth_label"]).lower().strip()
            is_ring = 1 if lbl == "ring" else 0
            ts_str = r["dt_timestamp"].isoformat()

            target_records.append({
                "transaction_id": txid,
                "account_id": aid,
                "timestamp": ts_str,
                "scenario_type": str(r["scenario_type"]),
                "ground_truth_label": str(r["ground_truth_label"]),
                "is_ring": is_ring,
            })
        target_metadata = pd.DataFrame(target_records).set_index("transaction_id")

        # 6. Audit for Leakage and Integrity
        leakage_a = FeatureValidator.audit_target_leakage(X_model_a, "Model A (Tx+Behavior)")
        leakage_b = FeatureValidator.audit_target_leakage(X_model_b, "Model B (Tx+Behavior+Graph)")
        if leakage_a:
            raise RuntimeError(f"Leakage in Model A: {leakage_a}")
        if leakage_b:
            raise RuntimeError(f"Leakage in Model B: {leakage_b}")

        audit_a = FeatureValidator.audit_data_integrity(X_model_a, "Model A")
        audit_b = FeatureValidator.audit_data_integrity(X_model_b, "Model B")

        # 7. Generate Manifest Summary
        summaries_tx = FeatureValidator.generate_feature_summary(df_feats_tx, "transaction")
        summaries_beh = FeatureValidator.generate_feature_summary(df_feats_beh, "behavioral")
        summaries_graph = FeatureValidator.generate_feature_summary(df_feats_graph, "graph_point_in_time")

        manifest = {
            "dataset_name": "ringguard_mvp_v1_features",
            "row_count": len(df_tx),
            "model_a_feature_count": len(X_model_a.columns),
            "model_b_feature_count": len(X_model_b.columns),
            "feature_counts_by_group": {
                "transaction": len(TRANSACTION_FEATURE_COLUMNS),
                "behavioral": len(BEHAVIORAL_FEATURE_COLUMNS),
                "graph": len(POINT_IN_TIME_GRAPH_FEATURE_COLUMNS),
            },
            "model_a_columns": list(X_model_a.columns),
            "model_b_columns": list(X_model_b.columns),
            "target_metadata_columns": list(target_metadata.columns),
            "data_integrity": {
                "model_a": audit_a,
                "model_b": audit_b,
            },
            "feature_dictionary": summaries_tx + summaries_beh + summaries_graph,
        }

        # 8. Save Artifacts if output_dir provided
        if output_dir:
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            X_model_a.to_csv(out_path / "model_a_features.csv")
            X_model_b.to_csv(out_path / "model_b_features.csv")
            target_metadata.to_csv(out_path / "target_metadata.csv")
            with open(out_path / "feature_manifest.json", "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

        return X_model_a, X_model_b, target_metadata, manifest
