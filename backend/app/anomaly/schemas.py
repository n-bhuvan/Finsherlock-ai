"""RingGuard AI — Systemic Anomaly Schemas.

V2 Stage 15: Systemic Risk Anomaly Detection.
Strict Pydantic models defining multi-scope anomaly data contracts,
signal provenance, non-causal safety status, and human-in-the-loop flags.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class AnomalyScope(str, Enum):
    """Supported investigation boundaries for anomaly detection."""
    ACCOUNT = "ACCOUNT"
    MERCHANT = "MERCHANT"
    RING_NETWORK = "RING_NETWORK"
    SYSTEMIC_INFRASTRUCTURE = "SYSTEMIC_INFRASTRUCTURE"


class SignalStatus(str, Enum):
    """Availability status of empirical signals in underlying dataset."""
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AnomalySignal(BaseModel):
    """Empirical observed signal evaluated within a specific anomaly scope."""
    name: str = Field(..., description="Canonical signal identifier.")
    status: SignalStatus = Field(..., description="Empirical data availability status.")
    value: Optional[Union[float, int, str, bool]] = Field(
        None, description="Observed point-in-time value if available."
    )
    threshold: Optional[Union[float, int, str]] = Field(
        None, description="Deterministic anomaly detection threshold."
    )
    is_anomalous: bool = Field(
        False, description="True if observed value breaches deterministic threshold."
    )
    description: str = Field(
        ..., description="Factual description of the observed signal."
    )
    source_field: Optional[str] = Field(
        None, description="Underlying database table/column or graph metric source."
    )


class ScopeAnomalyResult(BaseModel):
    """Result of deterministic anomaly evaluation for a single scope."""
    scope: AnomalyScope = Field(..., description="The evaluated anomaly scope.")
    anomaly_detected: bool = Field(..., description="True if scope exhibits anomalous deviation.")
    anomaly_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Deterministic scope anomaly score bounded in [0.0, 1.0]."
    )
    status: str = Field(
        ..., description="Categorical status: ANOMALOUS, NORMAL, INCONCLUSIVE, or NOT_APPLICABLE."
    )
    confidence: str = Field(
        ..., description="Signal confidence level: HIGH, MEDIUM, LOW, or UNAVAILABLE."
    )
    reason: str = Field(
        ..., description="Evidence-grounded, non-causal justification strictly adhering to safety rules."
    )
    signals: List[AnomalySignal] = Field(
        default_factory=list, description="Constituent signals evaluated in this scope."
    )
    evidence_ids: List[str] = Field(
        default_factory=list, description="Grounded EvidenceEngine evidence IDs supporting this scope."
    )
    requires_verification: bool = Field(
        True, description="Always true when anomalous or inconclusive; human-in-the-loop invariant."
    )


class SystemicAnomalyResponse(BaseModel):
    """Comprehensive multi-scope systemic anomaly response for a transaction."""
    transaction_id: str = Field(..., description="Evaluated transaction identifier.")
    account_id: str = Field(..., description="Transacting source account identifier.")
    timestamp: str = Field(..., description="Point-in-time evaluation timestamp (ISO 8601).")
    
    # Deterministic anomaly metrics (strictly separated from calibrated fraud probability)
    systemic_anomaly_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Deterministic composite anomaly score in [0.0, 1.0]. NOT a calibrated fraud probability."
    )
    overall_systemic_risk_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Compatibility alias for systemic_anomaly_score."
    )
    score_interpretation: str = Field(
        default="DETERMINISTIC_HEURISTIC_ANOMALY_SCORE",
        description="Explicit declaration that this metric is an empirical heuristic, not a model probability."
    )
    anomaly_detected: bool = Field(
        ..., description="True if any active scope breaches its deterministic anomaly threshold."
    )
    primary_contributing_scope: Optional[AnomalyScope] = Field(
        None, description="Scope contributing highest weighted anomaly signal, if any."
    )
    
    scopes: Dict[str, ScopeAnomalyResult] = Field(
        ..., description="Evaluation results for all 4 scopes: account, merchant, ring_network, systemic_infrastructure."
    )
    all_evidence_ids: List[str] = Field(
        default_factory=list, description="De-duplicated list of all grounded evidence IDs across scopes."
    )
    requires_verification: bool = Field(
        True, description="Strict human-in-the-loop verification flag."
    )
    human_approval_required: bool = Field(
        default=True, description="Defense-only non-enforcement invariant: human approval mandatory."
    )
    defense_only_disclaimer: str = Field(
        default="Defense-only decision support. Systemic anomaly is an empirical correlation heuristic, NOT calibrated fraud probability, and NOT proof of fraud or causal fault. Human verification is strictly required.",
        description="Prominent non-enforcement and non-causal attribution disclaimer."
    )
