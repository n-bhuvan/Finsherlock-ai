"""RingGuard AI — Portfolio Prioritization Schemas.

V2 Stage 16: Portfolio Risk Prioritization + Expected Value.
Strict Pydantic data contracts for deterministic case ordering,
decision-theoretic expected value accounting, and synthetic monetary disclaimers.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EconomicAssumptions(BaseModel):
    """Predeclared economic and operational parameters governing expected value."""
    interception_rate: float = Field(
        default=0.85,
        description="Simulated fraud prevention/interception efficiency rate (85%)."
    )
    cost_per_investigation_cinv: float = Field(
        default=350.0,
        description="Operational human case review cost in INR (₹350.00)."
    )
    friction_cost_per_false_positive_cfp: float = Field(
        default=1200.0,
        description="Simulated customer friction cost per false positive review in INR (₹1,200.00)."
    )
    ev_cap: float = Field(
        default=85000.0,
        description="Global deterministic EV normalization cap (₹100,000 max exposure * 0.85 interception rate)."
    )
    monetary_unit: str = Field(
        default="INR (₹)",
        description="Currency unit for monetary calculations."
    )
    simulated_estimate: bool = Field(
        default=True,
        description="Explicit indicator that monetary figures are simulated estimates."
    )


class PrioritizedCaseItem(BaseModel):
    """Deterministic, auditable prioritization breakdown for a single case."""
    transaction_id: str = Field(..., description="Unique transaction identifier.")
    account_id: str = Field(..., description="Transacting source account identifier.")
    timestamp: str = Field(..., description="Point-in-time transaction timestamp (ISO 8601).")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Model B post-hoc Platt-calibrated risk probability.")
    exposure: float = Field(..., ge=0.0, description="Transaction monetary exposure in INR.")
    
    # Input signals
    network_leverage: float = Field(..., ge=0.0, le=1.0, description="Normalized network leverage from entity graph (0.0 to 1.0).")
    systemic_anomaly_score: float = Field(..., ge=0.0, le=1.0, description="Stage 15 deterministic systemic anomaly score.")
    investigative_uncertainty: float = Field(..., ge=0.0, le=1.0, description="Deterministic investigative uncertainty heuristic (u0 in [0.05, 0.95]).")
    
    # Decision-Theoretic Expected Value Breakdown
    expected_loss_avoided: float = Field(..., description="calibrated_risk * exposure * interception_rate (INR).")
    friction_cost: float = Field(..., description="(1 - calibrated_risk) * CFP (INR).")
    investigation_cost: float = Field(..., description="Fixed human investigation cost Cinv (INR).")
    expected_value: float = Field(..., description="Net expected value saved = Loss Avoided - Friction - Investigation Cost (INR).")
    ev_normalized: float = Field(..., ge=0.0, le=1.0, description="Global deterministic normalized EV = clip(expected_value / 85000.0, 0.0, 1.0).")
    
    # Priority Ranking & Rationale
    priority_score: float = Field(..., ge=0.0, le=1.0, description="Deterministic composite priority score in [0.0, 1.0].")
    priority_rank: int = Field(..., ge=1, description="1-indexed rank within evaluated portfolio ordering.")
    recommended_action: str = Field(
        ...,
        description="Investigation queue priority: PRIORITIZE_INVESTIGATION, HIGH_PRIORITY_REVIEW, REVIEW_NEXT, LOW_PRIORITY, NO_IMMEDIATE_INVESTIGATION."
    )
    priority_reason: str = Field(..., description="Interpretable narrative answering 'Why investigate this case before another?'.")
    
    # Governance & Disclaimers
    economic_assumptions: EconomicAssumptions = Field(default_factory=EconomicAssumptions)
    synthetic_monetary_value_disclaimer: str = Field(
        default="SIMULATED / SYNTHETIC ESTIMATE: Monetary values reflect risk modeling heuristics on synthetic benchmark data and do not represent real Razorpay customer data, merchant balances, or actual financial recovery."
    )
    human_approval_required: bool = Field(
        default=True,
        description="Defense-only invariant: human review remains mandatory before taking action."
    )


class PortfolioPrioritizationResponse(BaseModel):
    """Portfolio-level prioritization response sorting all evaluated cases."""
    total_cases_evaluated: int = Field(..., description="Total count of candidate cases scored and ordered.")
    portfolio_expected_value_sum: float = Field(..., description="Sum of expected values across all evaluated cases in INR.")
    portfolio_total_exposure: float = Field(..., description="Sum of transaction amounts across all evaluated cases in INR.")
    cases: List[PrioritizedCaseItem] = Field(..., description="Cases sorted descending by deterministic priority score.")
    
    scoring_formula: str = Field(
        default="Priority Score = 0.25 * p_calibrated + 0.25 * EVnorm + 0.15 * Expnorm + 0.15 * NetworkLeverage + 0.10 * SystemicAnomaly + 0.10 * u0",
        description="Explicit documentation of the deterministic weighted prioritization formula."
    )
    economic_formula: str = Field(
        default="Expected Value = Expected Loss Avoided - Expected Friction Cost - Expected Investigation Cost",
        description="Explicit documentation of the decision-theoretic expected-value formula."
    )
    economic_assumptions: EconomicAssumptions = Field(default_factory=EconomicAssumptions)
    synthetic_monetary_value_disclaimer: str = Field(
        default="SIMULATED / SYNTHETIC ESTIMATE: Monetary values reflect risk modeling heuristics on synthetic benchmark data and do not represent real Razorpay customer data, merchant balances, or actual financial recovery."
    )
    human_approval_required: bool = Field(
        default=True,
        description="Defense-only non-enforcement boundary."
    )
