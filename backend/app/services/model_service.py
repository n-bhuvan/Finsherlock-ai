"""Model loading and inference service for RingGuard AI.

Stage 8: FastAPI Risk APIs.
Manages lazy/cached loading of trained Model A (Baseline) and Model B (Graph-Enhanced)
artifacts, enforces feature ordering against model metadata, and runs prediction.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import joblib
import xgboost as xgb

from app.schemas.risk import RiskBand, ModelHealthDetail


class ModelServiceError(Exception):
    """Base exception for model service failures."""
    pass


class ModelArtifactNotFoundError(ModelServiceError):
    """Raised when a model file is missing."""
    pass


class FeatureOrderMismatchError(ModelServiceError):
    """Raised when input feature ordering does not match model expectations."""
    pass


class ModelService:
    """Service to load, cache, and query RingGuard XGBoost models."""

    def __init__(self, models_dir: Optional[Path] = None):
        # Resolve repo root directory: if running from backend, repo root is parent
        if models_dir:
            self.models_dir = Path(models_dir)
        else:
            current_dir = Path(__file__).resolve().parent
            repo_root = current_dir.parents[2]  # backend/app/services -> backend -> repo_root
            self.models_dir = repo_root / "models"

        self.model_a: Optional[xgb.XGBClassifier] = None
        self.meta_a: Optional[Dict[str, Any]] = None
        self.features_a: List[str] = []

        self.model_b: Optional[xgb.XGBClassifier] = None
        self.meta_b: Optional[Dict[str, Any]] = None
        self.features_b: List[str] = []

        self._load_models()

    def _load_models(self) -> None:
        """Load Model A and Model B artifacts and metadata."""
        # 1. Load Model A (Baseline)
        model_a_path = self.models_dir / "ringguard_baseline_xgb_v1.joblib"
        meta_a_path = self.models_dir / "ringguard_baseline_xgb_v1_metadata.json"

        if not model_a_path.exists():
            raise ModelArtifactNotFoundError(f"Model A artifact not found: {model_a_path}")
        if not meta_a_path.exists():
            raise ModelArtifactNotFoundError(f"Model A metadata not found: {meta_a_path}")

        self.model_a = joblib.load(model_a_path)
        with open(meta_a_path, "r", encoding="utf-8") as f:
            self.meta_a = json.load(f)

        self.features_a = list(self.meta_a.get("feature_names", []))
        if len(self.features_a) != 37:
            raise ModelServiceError(f"Model A expected 37 features, found {len(self.features_a)}")

        # 2. Load Model B (Graph-Enhanced)
        model_b_path = self.models_dir / "ringguard_graph_xgb_v1.joblib"
        meta_b_path = self.models_dir / "ringguard_graph_xgb_v1_metadata.json"

        if not model_b_path.exists():
            raise ModelArtifactNotFoundError(f"Model B artifact not found: {model_b_path}")
        if not meta_b_path.exists():
            raise ModelArtifactNotFoundError(f"Model B metadata not found: {meta_b_path}")

        self.model_b = joblib.load(model_b_path)
        with open(meta_b_path, "r", encoding="utf-8") as f:
            self.meta_b = json.load(f)

        self.features_b = list(self.meta_b.get("feature_names", []))
        if len(self.features_b) != 58:
            raise ModelServiceError(f"Model B expected 58 features, found {len(self.features_b)}")

    def predict_baseline(self, features_df: pd.DataFrame) -> float:
        """Execute inference using Model A (Baseline, 37 features)."""
        if self.model_a is None:
            raise ModelServiceError("Model A is not loaded.")

        if list(features_df.columns) != self.features_a:
            raise FeatureOrderMismatchError(
                f"Feature columns mismatch for Model A. Expected {len(self.features_a)} columns."
            )

        prob = float(self.model_a.predict_proba(features_df)[0, 1])
        return max(0.0, min(1.0, prob))

    def predict_graph(self, features_df: pd.DataFrame) -> float:
        """Execute inference using Model B (Graph-Enhanced, 58 features)."""
        if self.model_b is None:
            raise ModelServiceError("Model B is not loaded.")

        if list(features_df.columns) != self.features_b:
            raise FeatureOrderMismatchError(
                f"Feature columns mismatch for Model B. Expected {len(self.features_b)} columns."
            )

        prob = float(self.model_b.predict_proba(features_df)[0, 1])
        return max(0.0, min(1.0, prob))

    @staticmethod
    def determine_risk_band(probability: float) -> RiskBand:
        """Map raw model probability to deterministic presentation risk band."""
        if probability < 0.20:
            return RiskBand.LOW
        elif probability < 0.50:
            return RiskBand.MEDIUM
        else:
            return RiskBand.HIGH

    def get_health_details(self) -> Dict[str, ModelHealthDetail]:
        """Return health details for loaded models."""
        return {
            "baseline": ModelHealthDetail(
                model_name=self.meta_a.get("model_name", "ringguard_baseline_xgb_v1") if self.meta_a else "unknown",
                model_version="v1",
                loaded=self.model_a is not None,
                feature_count=len(self.features_a),
                graph_features_count=0,
            ),
            "graph": ModelHealthDetail(
                model_name=self.meta_b.get("model_name", "ringguard_graph_xgb_v1") if self.meta_b else "unknown",
                model_version="v1",
                loaded=self.model_b is not None,
                feature_count=len(self.features_b),
                graph_features_count=21,
            ),
        }


# Global cached singleton instance
_model_service_instance: Optional[ModelService] = None


def get_model_service() -> ModelService:
    """Retrieve or initialize the global ModelService singleton."""
    global _model_service_instance
    if _model_service_instance is None:
        _model_service_instance = ModelService()
    return _model_service_instance
