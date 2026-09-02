"""RingGuard AI — Graph-Enhanced XGBoost Model (Model B).

Stage 7: Graph-Enhanced XGBoost.
Trains a binary XGBoost classifier using Transaction + Behavior + Point-in-Time Graph features (58 features).
Uses the exact same prediction unit, chronological split, target, seed, and configuration as Model A.
"""

import json
from pathlib import Path
from typing import Dict, Tuple, List, Optional, Any
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb

from ml.models.baseline import DEFAULT_XGB_CONFIG


class GraphEnhancedXGBoostModel:
    """Manages data preparation, chronological splitting, training, and inference for Model B."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        data_dir: Optional[str] = None,
    ):
        self.config = config or DEFAULT_XGB_CONFIG.copy()
        self.data_dir = Path(data_dir) if data_dir else Path("ml/data/features")
        self.model: Optional[xgb.XGBClassifier] = None
        self.feature_names: List[str] = []
        self.scale_pos_weight: Optional[float] = None
        self.split_info: Dict[str, Any] = {}

    def load_dataset(self) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
        """Load Model B features and target metadata, enforcing strict alignment.
        
        Returns:
            (X, y, metadata) sorted chronologically.
        """
        features_path = self.data_dir / "model_b_features.csv"
        meta_path = self.data_dir / "target_metadata.csv"

        if not features_path.exists():
            raise FileNotFoundError(f"Model B features file not found: {features_path}")
        if not meta_path.exists():
            raise FileNotFoundError(f"Target metadata file not found: {meta_path}")

        X = pd.read_csv(features_path, index_col=0)
        meta = pd.read_csv(meta_path, index_col=0)

        # Integrity assertions
        if len(X) != 2000 or len(meta) != 2000:
            raise ValueError(f"Expected 2000 rows, got X={len(X)}, meta={len(meta)}")
        if not (X.index == meta.index).all():
            raise ValueError("Row index mismatch between Model B features and target metadata.")

        # Ensure exactly 58 features (37 Model A + 21 graph features)
        if X.shape[1] != 58:
            raise ValueError(f"Expected exactly 58 features in Model B, got {X.shape[1]}")

        # Ensure exactly 21 graph features exist in Model B
        graph_cols = [c for c in X.columns if c.startswith("g_")]
        if len(graph_cols) != 21:
            raise ValueError(f"Expected exactly 21 graph features in Model B, got {len(graph_cols)}")

        # Ensure no target or scenario leakage columns exist in X
        leakage_cols = [c for c in X.columns if c.lower() in [
            "ground_truth_label", "scenario_type", "scenario_id", "is_ring", "is_fraud"
        ]]
        if leakage_cols:
            raise ValueError(f"Target leakage columns found in Model B: {leakage_cols}")

        # Sort chronologically by timestamp, then transaction_id (identical to Stage 6)
        meta["dt_timestamp"] = pd.to_datetime(meta["timestamp"], utc=True)
        sorted_indices = meta.sort_values(by=["dt_timestamp", "transaction_id"]).index

        X = X.loc[sorted_indices]
        meta = meta.loc[sorted_indices]

        # Extract target variable (1 for ring, 0 for legitimate)
        y = meta["is_ring"].astype(int)
        self.feature_names = list(X.columns)

        return X, y, meta

    def chronological_split(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        meta: pd.DataFrame,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
    ) -> Tuple[
        Tuple[pd.DataFrame, pd.Series, pd.DataFrame],
        Tuple[pd.DataFrame, pd.Series, pd.DataFrame],
        Tuple[pd.DataFrame, pd.Series, pd.DataFrame],
    ]:
        """Partition dataset into chronological Train (70%), Validation (15%), and Test (15%)."""
        total_rows = len(X)
        train_end = int(total_rows * train_ratio)
        val_end = train_end + int(total_rows * val_ratio)

        X_train, y_train, meta_train = X.iloc[:train_end], y.iloc[:train_end], meta.iloc[:train_end]
        X_val, y_val, meta_val = X.iloc[train_end:val_end], y.iloc[train_end:val_end], meta.iloc[train_end:val_end]
        X_test, y_test, meta_test = X.iloc[val_end:], y.iloc[val_end:], meta.iloc[val_end:]

        # Record split boundaries and class distributions
        self.split_info = {
            "train": {
                "count": len(X_train),
                "ring_count": int(y_train.sum()),
                "legit_count": int((y_train == 0).sum()),
                "ring_rate": round(float(y_train.mean()), 4),
                "start_timestamp": str(meta_train["dt_timestamp"].min()),
                "end_timestamp": str(meta_train["dt_timestamp"].max()),
            },
            "validation": {
                "count": len(X_val),
                "ring_count": int(y_val.sum()),
                "legit_count": int((y_val == 0).sum()),
                "ring_rate": round(float(y_val.mean()), 4),
                "start_timestamp": str(meta_val["dt_timestamp"].min()),
                "end_timestamp": str(meta_val["dt_timestamp"].max()),
            },
            "test": {
                "count": len(X_test),
                "ring_count": int(y_test.sum()),
                "legit_count": int((y_test == 0).sum()),
                "ring_rate": round(float(y_test.mean()), 4),
                "start_timestamp": str(meta_test["dt_timestamp"].min()),
                "end_timestamp": str(meta_test["dt_timestamp"].max()),
            },
        }

        return (X_train, y_train, meta_train), (X_val, y_val, meta_val), (X_test, y_test, meta_test)

    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        """Fit conservative XGBoost model on the training set only."""
        n_pos = int(y_train.sum())
        n_neg = int((y_train == 0).sum())
        if n_pos == 0:
            raise ValueError("Training set has 0 positive/ring samples.")
        
        self.scale_pos_weight = float(n_neg / n_pos)

        train_config = self.config.copy()
        train_config["scale_pos_weight"] = self.scale_pos_weight

        self.model = xgb.XGBClassifier(**train_config)
        self.model.fit(X_train, y_train)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probabilities for the positive/ring class [0, 1]."""
        if self.model is None:
            raise RuntimeError("Model has not been trained yet.")
        return self.model.predict_proba(X)[:, 1]

    def get_feature_importances(self) -> pd.DataFrame:
        """Return feature importances with feature group annotations."""
        if self.model is None:
            raise RuntimeError("Model has not been trained yet.")

        importances = self.model.feature_importances_
        groups = []
        for name in self.feature_names:
            if name.startswith("g_"):
                groups.append("graph")
            elif name.startswith("tx_"):
                groups.append("transaction")
            elif name.startswith("beh_"):
                groups.append("behavior")
            else:
                groups.append("unknown")

        df_imp = pd.DataFrame({
            "feature_name": self.feature_names,
            "importance": importances,
            "feature_group": groups,
        }).sort_values(by="importance", ascending=False).reset_index(drop=True)
        df_imp["rank"] = df_imp.index + 1
        return df_imp

    def save_artifacts(
        self,
        model_path: str = "models/ringguard_graph_xgb_v1.joblib",
        metadata_path: str = "models/ringguard_graph_xgb_v1_metadata.json",
        metrics_dict: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist trained model binary and metadata artifact."""
        if self.model is None:
            raise RuntimeError("Cannot save untrained model.")

        m_path = Path(model_path)
        meta_path = Path(metadata_path)
        m_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.model, m_path)

        tx_count = sum(1 for f in self.feature_names if f.startswith("tx_"))
        beh_count = sum(1 for f in self.feature_names if f.startswith("beh_"))
        graph_count = sum(1 for f in self.feature_names if f.startswith("g_"))

        metadata = {
            "model_name": "ringguard_graph_xgb_v1",
            "model_type": "XGBClassifier",
            "prediction_unit": "TRANSACTION",
            "feature_count": len(self.feature_names),
            "transaction_feature_count": tx_count,
            "behavioral_feature_count": beh_count,
            "graph_feature_count": graph_count,
            "feature_names": self.feature_names,
            "scale_pos_weight": self.scale_pos_weight,
            "xgboost_version": xgb.__version__,
            "configuration": self.config,
            "split_info": self.split_info,
            "baseline_model_reference": "models/ringguard_baseline_xgb_v1.joblib",
            "evaluation_metrics": metrics_dict or {},
        }

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    @classmethod
    def load(cls, model_path: str = "models/ringguard_graph_xgb_v1.joblib") -> "GraphEnhancedXGBoostModel":
        """Load a persisted Model B artifact."""
        instance = cls()
        instance.model = joblib.load(model_path)
        instance.feature_names = list(instance.model.feature_names_in_)
        return instance
