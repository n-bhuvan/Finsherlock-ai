"""Pydantic schemas for RingGuard AI Risk APIs.

Stage 8: FastAPI Risk APIs.
Defines strict request/response data models for analytical risk assessment,
ensuring probability bounds, feature counts, and explicit disclaimers.
"""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class RiskBand(str, Enum):
    """Deterministic presentation risk band based on baseline threshold 0.5."""
    LOW = "LOW"        # Probability < 0.20
    MEDIUM = "MEDIUM"  # 0.20 <= Probability < 0.50
    HIGH = "HIGH"      # Probability >= 0.50


class ModelHealthDetail(BaseModel):
    """Health information for an individual ML model artifact."""
    model_name: str
    model_version: str
    loaded: bool
    feature_count: int
    graph_features_count: int


class RiskHealthResponse(BaseModel):
    """Response schema for GET /api/risk/health."""
    status: str = Field(..., description="Operational status: 'ok' or 'degraded'")
    service: str = Field("ringguard-risk-engine", description="Service identifier")
    baseline_model_loaded: bool
    graph_model_loaded: bool
    database_connected: bool
    models: Dict[str, ModelHealthDetail]


class BaseRiskAssessmentResponse(BaseModel):
    """Base schema for risk predictions."""
    transaction_id: str = Field(..., description="Unique transaction identifier")
    prediction_unit: str = Field("transaction", description="Prediction unit is always transaction")
    model: str = Field(..., description="Model identifier")
    model_version: str = Field(..., description="Model version string")
    predicted_ring_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model output probability of ring/suspicious behavior in range [0.0, 1.0]",
    )
    decision_threshold: float = Field(
        0.5,
        description="Fixed baseline decision threshold (uncalibrated)",
    )
    risk_band: RiskBand = Field(
        ...,
        description="Presentation risk band for analytical visualization (not an enforcement action)",
    )
    feature_count: int = Field(..., description="Total number of features evaluated")
    graph_features_count: int = Field(..., description="Number of graph features evaluated")
    graph_context_available: bool = Field(..., description="Whether point-in-time graph features were included")
    disclaimer: str = Field(
        "Analytical risk assessment output only. Does not constitute an automated payment action or enforcement decision.",
        description="Regulatory/analytical boundary disclaimer",
    )


class BaselineRiskResponse(BaseRiskAssessmentResponse):
    """Response schema for Model A (Transaction + Behavior baseline)."""
    model: str = "ringguard_baseline_xgb_v1"
    model_version: str = "v1"
    feature_count: int = 37
    graph_features_count: int = 0
    graph_context_available: bool = False


class NetworkRiskResponse(BaseRiskAssessmentResponse):
    """Response schema for Model B (Transaction + Behavior + Point-in-Time Graph)."""
    model: str = "ringguard_graph_xgb_v1"
    model_version: str = "v1"
    feature_count: int = 58
    graph_features_count: int = 21
    graph_context_available: bool = True


class RiskResponse(NetworkRiskResponse):
    """Primary risk endpoint response schema (defaults to primary network model)."""
    pass


class RiskErrorResponse(BaseModel):
    """Structured error response schema."""
    error: str
    detail: str
    transaction_id: Optional[str] = None
