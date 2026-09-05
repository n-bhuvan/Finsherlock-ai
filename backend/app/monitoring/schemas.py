"""RingGuard AI — Stage 20: Monitoring & Verification Schemas.

Defines Pydantic contracts for:
1. Drift Monitoring (PSI, JSD, Missingness, Distribution Shifts)
2. Outcome Verification (Prediction vs Policy vs Observed Ground Truth)
3. Performance Metrics (Precision, Recall, FPR, FNR, Brier score)
"""

from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class DriftStatus(str, Enum):
    """Deterministic drift status taxonomy with strict precedence:
    SIGNIFICANT_DRIFT > WATCH > NORMAL > UNAVAILABLE
    """
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    SIGNIFICANT_DRIFT = "SIGNIFICANT_DRIFT"
    UNAVAILABLE = "UNAVAILABLE"


class OutcomeStatus(str, Enum):
    """Deterministic post-decision outcome verification taxonomy."""
    OUTCOME_CONFIRMED = "OUTCOME_CONFIRMED"
    OUTCOME_UNAVAILABLE = "OUTCOME_UNAVAILABLE"
    OUTCOME_PENDING = "OUTCOME_PENDING"
    OUTCOME_INCONCLUSIVE = "OUTCOME_INCONCLUSIVE"


class DriftMetric(BaseModel):
    """Deterministic drift measurement for an individual feature or signal."""
    feature_name: str
    metric_name: str  # "PSI", "JSD", "MISSINGNESS_DELTA", "MEAN_SHIFT"
    metric_value: float
    threshold_watch: float
    threshold_significant: float
    status: DriftStatus
    reference_window: str
    comparison_window: str
    sample_size_reference: int
    sample_size_comparison: int
    limitations: Optional[str] = None


class OutcomePerformanceMetric(BaseModel):
    """Performance metrics evaluated in controlled synthetic benchmark where labels exist."""
    window_name: str
    sample_size: int
    positive_label_rate: float
    precision: Optional[float] = None
    recall: Optional[float] = None
    false_positive_rate: Optional[float] = None
    false_negative_rate: Optional[float] = None
    brier_score: Optional[float] = None
    status: OutcomeStatus = OutcomeStatus.OUTCOME_CONFIRMED


class DriftMonitoringResponse(BaseModel):
    """Complete drift telemetry response across all 15 monitored features."""
    evaluation_timestamp: str
    reference_window: str
    comparison_window: str
    overall_status: DriftStatus
    metrics: List[DriftMetric]
    significant_features: List[str] = Field(default_factory=list)
    watch_features: List[str] = Field(default_factory=list)
    performance_comparison: Optional[Dict[str, OutcomePerformanceMetric]] = None
    human_review_required: bool = True
    disclaimer: str = (
        "SIMULATED / SYNTHETIC BENCHMARK — not real production outcomes. "
        "Drift telemetry is provided for decision support and monitoring only."
    )


class OutcomeVerificationResponse(BaseModel):
    """Post-decision outcome verification response for an individual transaction."""
    transaction_id: str
    evaluation_context: str
    prediction_at_decision: Optional[float] = None
    policy_action_at_decision: Optional[str] = None
    observed_outcome: Optional[str] = None
    outcome_status: OutcomeStatus
    outcome_match: Optional[bool] = None
    verification_timestamp: str
    verification_source: str
    limitations: str
    human_review_required: bool = True
    disclaimer: str = (
        "SIMULATED / SYNTHETIC BENCHMARK — not real production outcomes. "
        "Outcome verification is provided strictly for model evaluation and audit."
    )


class MonitoringSummaryResponse(BaseModel):
    """Combined high-level monitoring summary for executive dashboards."""
    overall_drift_status: DriftStatus
    total_features_monitored: int
    significant_features_count: int
    watch_features_count: int
    reference_window: str
    comparison_window: str
    outcome_verification_coverage_rate: float
    human_review_required: bool = True
    disclaimer: str = (
        "SIMULATED / SYNTHETIC BENCHMARK — not real production outcomes. "
        "Monitoring and verification outputs are non-autonomous."
    )
