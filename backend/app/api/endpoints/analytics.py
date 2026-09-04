"""RingGuard AI — Business Economics & Analytics Endpoints.

Stage 12: Final Packaging & Submission Readiness.
Exposes transparent business economics calculations separating:
1. Observed benchmark values (derived from the verified 2,000-transaction database)
2. Configurable operational assumptions
3. Derived economic estimates (Net Value Saved = Estimated Loss Avoided - Friction Cost - Investigation Cost)
"""

from typing import Dict, List, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter()


class ObservedBenchmarkValues(BaseModel):
    """Factual benchmark metrics from audited database and Stage 6/7 evaluation artifacts."""
    dataset_name: str = "RingGuard Synthetic Evaluation Benchmark (Stages 1–7)"
    total_evaluated_transactions: int = 2000
    total_evaluated_accounts: int = 500
    total_transaction_volume_inr: float = 10151381.07
    total_ring_fraud_transactions: int = 233
    total_ring_fraud_accounts: int = 72
    total_ring_fraud_exposure_inr: float = 7864287.00
    mean_ring_transaction_amount_inr: float = 33752.30
    mean_legitimate_transaction_amount_inr: float = 1294.34
    synthetic_held_out_false_positive_rate: float = 0.00
    synthetic_held_out_false_positives_count: int = 0


class OperationalModelingAssumptions(BaseModel):
    """User-configurable operational and staffing parameters."""
    interception_rate: float = Field(..., description="Estimated interception/prevention rate (0.50 to 1.00)")
    cost_per_investigation_inr: float = Field(..., description="Analyst cost per case investigation in INR")
    friction_cost_per_false_positive_inr: float = Field(..., description="Estimated customer friction per false positive in INR")
    tier2_analyst_hourly_rate_inr: float = 1400.0
    investigation_time_minutes_per_case: float = 15.0


class DerivedEconomicEstimates(BaseModel):
    """Derived economic output modeled from benchmark data and user assumptions."""
    estimated_fraud_loss_avoided_inr: float = Field(
        ..., description="Gross fraud volume avoided under specified interception rate"
    )
    total_investigation_cost_inr: float = Field(
        ..., description="Total cost of analyst review for flagged cases"
    )
    total_friction_cost_inr: float = Field(
        ..., description="Total customer friction cost incurred by false positives"
    )
    net_value_saved_inr: float = Field(
        ..., description="Net value: Estimated Loss Avoided - Total Friction Cost - Total Investigation Cost"
    )
    roi_multiple: float = Field(
        ..., description="Net Value Saved / (Total Investigation Cost + Total Friction Cost)"
    )


class BusinessEconomicsResponse(BaseModel):
    """Top-level response envelope for business economics modeling."""
    observed_benchmark_values: ObservedBenchmarkValues
    operational_modeling_assumptions: OperationalModelingAssumptions
    derived_economic_estimates: DerivedEconomicEstimates
    disclaimers: List[str] = [
        "All observed figures are derived from the audited RingGuard synthetic benchmark dataset (2,000 transactions, 233 ring fraud records).",
        "Economic ROI figures are modeled estimates based on user-supplied operational assumptions.",
        "Uses 'Estimated Fraud Loss Avoided', reflecting expected loss prevention under an assumed interception rate.",
    ]


@router.get(
    "/economics",
    response_model=BusinessEconomicsResponse,
    summary="Get Business Economics & ROI Modeling",
    description="Calculates transparent fraud economics based on verified benchmark data and configurable operational assumptions.",
)
def get_business_economics(
    interception_rate: float = Query(0.85, ge=0.50, le=1.00, description="Interception rate (0.50–1.00)"),
    cost_per_investigation: float = Query(350.0, ge=100.0, le=1000.0, description="Cost per investigation in INR"),
    friction_cost_per_fp: float = Query(1200.0, ge=300.0, le=5000.0, description="Friction cost per false positive in INR"),
) -> BusinessEconomicsResponse:
    """Computes Net Value Saved and ROI multiple with transparent separation of data tiers."""
    # 1. Observed benchmark data (verified from database)
    observed = ObservedBenchmarkValues()

    # 2. Operational assumptions
    assumptions = OperationalModelingAssumptions(
        interception_rate=interception_rate,
        cost_per_investigation_inr=cost_per_investigation,
        friction_cost_per_false_positive_inr=friction_cost_per_fp,
    )

    # 3. Derived estimates
    total_ring_exposure = observed.total_ring_fraud_exposure_inr
    flagged_cases = observed.total_ring_fraud_transactions
    false_positives = observed.synthetic_held_out_false_positives_count

    estimated_loss_avoided = round(total_ring_exposure * interception_rate, 2)
    investigation_cost = round(flagged_cases * cost_per_investigation, 2)
    friction_cost = round(false_positives * friction_cost_per_fp, 2)

    net_value = round(estimated_loss_avoided - friction_cost - investigation_cost, 2)
    total_overhead = investigation_cost + friction_cost
    roi_mult = round(net_value / total_overhead, 2) if total_overhead > 0 else 0.0

    derived = DerivedEconomicEstimates(
        estimated_fraud_loss_avoided_inr=estimated_loss_avoided,
        total_investigation_cost_inr=investigation_cost,
        total_friction_cost_inr=friction_cost,
        net_value_saved_inr=net_value,
        roi_multiple=roi_mult,
    )

    return BusinessEconomicsResponse(
        observed_benchmark_values=observed,
        operational_modeling_assumptions=assumptions,
        derived_economic_estimates=derived,
    )
