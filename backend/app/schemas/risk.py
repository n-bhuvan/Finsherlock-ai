"""Pydantic schemas for RingGuard AI Risk APIs.

Stage 8: FastAPI Risk APIs.
Defines strict request/response data models for analytical risk assessment,
ensuring probability bounds, feature counts, and explicit disclaimers.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
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


class GraphAttributionItem(BaseModel):
    """Mapping between Model B graph feature sensitivity and verified evidence provenance."""
    feature_name: str = Field(..., description="Name of the evaluated graph feature")
    feature_group: str = Field("graph", description="Feature category")
    importance_rank_in_model_b: int = Field(..., description="Global feature importance rank in Model B")
    original_value: float = Field(..., description="Observed point-in-time value in transaction vector")
    isolated_value: float = Field(..., description="Baseline value used for isolated entity simulation")
    corroborating_evidence_id: Optional[str] = Field(
        None, description="Stage 9 deterministic evidence ID if provenance exists"
    )
    corroborating_evidence_type: Optional[str] = Field(
        None, description="Stage 9 evidence type (e.g. SHARED_DEVICE, SHARED_IP)"
    )
    provenance_status: str = Field(
        "VERIFIED", description="'VERIFIED' if corroborating evidence exists, else 'FEATURE_ONLY'"
    )


class FeatureIsolationResponse(BaseModel):
    """Response schema for in-silico model feature-isolation (sensitivity) analysis."""
    transaction_id: str = Field(..., description="Evaluated transaction identifier")
    original_probability: float = Field(
        ..., ge=0.0, le=1.0, description="Model B output with full 58 point-in-time features"
    )
    isolated_probability: float = Field(
        ..., ge=0.0, le=1.0, description="Model B output with 21 graph features replaced by isolated baseline values"
    )
    delta: float = Field(
        ..., description="Raw probability shift: original_probability - isolated_probability"
    )
    percentage_point_delta: float = Field(
        ..., description="Percentage point shift: delta * 100"
    )
    risk_band_original: RiskBand = Field(..., description="Risk band under original features")
    risk_band_isolated: RiskBand = Field(..., description="Risk band under isolated features")
    isolated_features_count: int = Field(21, description="Number of graph topological features isolated")
    isolated_features: List[str] = Field(
        default_factory=list, description="Names of the 21 isolated graph features"
    )
    baseline_values_used: Dict[str, float] = Field(
        default_factory=dict, description="Dictionary of feature baseline values substituted"
    )
    attributions: List[GraphAttributionItem] = Field(
        default_factory=list, description="Top graph features with provenance-grounded evidence mapping"
    )
    methodology: str = Field(
        "In-silico model feature-isolation (ablation sensitivity) analysis. Evaluates frozen Model B (58 features) "
        "against an isolated-entity vector where 21 point-in-time graph features are replaced with verified baseline "
        "values representing a singleton node with zero network sharing, holding all 37 transaction and behavioral features constant.",
        description="Explicit analytical methodology description",
    )
    limitations: List[str] = Field(
        default=[
            "This is an in-silico model sensitivity/ablation analysis, not a causal intervention and not proof that graph features caused fraud.",
            "On the synthetic held-out evaluation benchmark (Stages 6 & 7), Model A and Model B achieved parity (PR-AUC 1.0000, ROC-AUC 1.0000, delta 0.0000).",
            "Ablated feature vectors evaluate the model's learned response but do not alter historical reality.",
            "Does not guarantee identical risk shifts under different data distributions.",
        ],
        description="Mandatory scientific limitation statements",
    )
    disclaimer: str = Field(
        "Analytical evaluation only. Describes model sensitivity to structural features and does not constitute an automated fraud determination or enforcement decision.",
        description="Mandatory defense-only regulatory notice",
    )

