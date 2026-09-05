"""RingGuard AI — Counterfactual Attribution and Intervention Simulation Schemas.

Stage 18: Counterfactual Attribution + Intervention Simulation.
Defines typed contracts for model sensitivity analysis, hypothetical interventions,
plausibility classifications, and read-only decision support payloads.
"""

from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class AttributionDirection(str, Enum):
    """Direction of a feature's effect on model risk assessment."""
    INCREASES_RISK = "INCREASES_RISK"
    DECREASES_RISK = "DECREASES_RISK"
    NEUTRAL = "NEUTRAL"


class InterventionMode(str, Enum):
    """Mode of hypothetical intervention applied in what-if simulation."""
    REMOVE_RISK_SIGNAL = "REMOVE_RISK_SIGNAL"
    REDUCE_RISK_SIGNAL = "REDUCE_RISK_SIGNAL"
    BASELINE_COMPARISON = "BASELINE_COMPARISON"
    CUSTOM_PERTURBATION = "CUSTOM_PERTURBATION"


class PlausibilityStatus(str, Enum):
    """Feasibility and real-world plausibility classification of an intervention."""
    PLAUSIBLE = "PLAUSIBLE"
    HYPOTHETICAL = "HYPOTHETICAL"
    UNAVAILABLE = "UNAVAILABLE"


class CounterfactualAttribution(BaseModel):
    """Single feature attribution derived from deterministic model-native TreeSHAP."""
    feature_name: str = Field(..., description="Canonical name of the Model B feature.")
    actual_value: float = Field(..., description="Observed point-in-time value of the feature.")
    contribution: float = Field(..., description="Log-odds contribution to the Model B margin.")
    direction: AttributionDirection = Field(..., description="Whether the feature increases or decreases model risk.")
    attribution_rank: int = Field(..., description="Deterministic 1-indexed rank sorted by absolute contribution.")
    explanation: str = Field(..., description="Factual description of the feature's role in the risk assessment.")
    source: str = Field(default="model_b_treeshape", description="Attribution mechanism provenance.")


class CounterfactualIntervention(BaseModel):
    """Simulated hypothetical feature perturbation and resulting model sensitivity."""
    intervention_id: str = Field(..., description="Unique identifier for the hypothetical intervention.")
    feature_name: str = Field(..., description="Name of the primary feature(s) perturbed.")
    original_value: Any = Field(..., description="Original observed value(s).")
    counterfactual_value: Any = Field(..., description="Hypothetical perturbed value(s).")
    original_risk_score: float = Field(..., description="Original production calibrated risk score.")
    counterfactual_risk_score: float = Field(..., description="Simulated calibrated risk score under perturbation.")
    risk_delta: float = Field(..., description="Change in risk score: counterfactual - original.")
    direction: AttributionDirection = Field(..., description="Direction of risk score change.")
    intervention_mode: InterventionMode = Field(..., description="Intervention category.")
    plausibility_status: PlausibilityStatus = Field(..., description="Plausibility classification.")
    assumption: str = Field(..., description="Hypothetical premise and operational assumption.")
    disclaimer: str = Field(
        default="Simulated model sensitivity under hypothetical feature change; not a causal claim or real-world guarantee.",
        description="Mandatory scientific disclaimer.",
    )


class CounterfactualAnalysisResponse(BaseModel):
    """Complete counterfactual attribution and intervention analysis for a transaction."""
    transaction_id: str = Field(..., description="Target transaction identifier.")
    account_id: str = Field(..., description="Associated account identifier.")
    timestamp: str = Field(..., description="Point-in-time ISO timestamp enforced.")
    model_name: str = Field(default="ringguard_graph_xgb_v1", description="Analyzed model binary name.")
    model_version: str = Field(default="v1", description="Analyzed model version.")
    original_risk_score: float = Field(..., description="Original production calibrated risk score (Model B).")
    original_probability_raw: float = Field(..., description="Original uncalibrated Model B probability.")
    attributions: List[CounterfactualAttribution] = Field(
        ..., description="Complete set of feature attributions sorted deterministically."
    )
    interventions: List[CounterfactualIntervention] = Field(
        ..., description="Standard pre-computed hypothetical interventions."
    )
    strongest_model_attribution: Optional[CounterfactualAttribution] = Field(
        None, description="Feature with the largest absolute contribution to risk margin."
    )
    largest_simulated_risk_delta: Optional[CounterfactualIntervention] = Field(
        None, description="Intervention resulting in the largest reduction in simulated risk."
    )
    human_approval_required: bool = Field(default=True, description="Strict human-in-the-loop governance flag.")
    defense_only: bool = Field(default=True, description="Enforces read-only defense-only operation.")
    disclaimer: str = Field(
        default="Counterfactual results are model-sensitivity simulations, not causal claims and not predictions of what would necessarily happen in the real world.",
        description="Mandatory system-level disclaimer.",
    )


class CustomInterventionRequest(BaseModel):
    """Analyst request to simulate a custom hypothetical feature perturbation."""
    feature_name: str = Field(..., min_length=1, description="Target feature name to perturb.")
    target_value: float = Field(..., description="Hypothetical value to inject into feature vector.")
