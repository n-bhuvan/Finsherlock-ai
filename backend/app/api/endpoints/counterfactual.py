"""RingGuard AI — Counterfactual Attribution and Intervention Simulation Endpoints.

Stage 18: Counterfactual Attribution + Intervention Simulation.
Provides read-only REST endpoints for model sensitivity analysis,
factual feature attributions, and hypothetical intervention simulations.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Path as FastAPIPath
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.counterfactual.service import CounterfactualAttributionService
from app.counterfactual.schemas import (
    CounterfactualAnalysisResponse,
    CounterfactualAttribution,
    CounterfactualIntervention,
    CustomInterventionRequest,
)
from app.services.feature_service import TransactionNotFoundError

router = APIRouter()


def get_counterfactual_service(db: Session = Depends(get_db)) -> CounterfactualAttributionService:
    """Dependency injector for CounterfactualAttributionService."""
    return CounterfactualAttributionService(db)


def _validate_transaction_id(transaction_id: str) -> str:
    """Validate that transaction_id is non-empty and not pure whitespace."""
    clean_id = transaction_id.strip()
    if not clean_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transaction ID cannot be empty or pure whitespace.",
        )
    return clean_id


@router.get(
    "/transaction/{transaction_id}",
    response_model=CounterfactualAnalysisResponse,
    summary="Retrieve complete counterfactual analysis and standard interventions",
    description="Calculates native Model B TreeSHAP feature attributions and simulates standard hypothetical interventions.",
)
def get_counterfactual_analysis(
    transaction_id: str = FastAPIPath(..., description="Unique transaction ID (e.g. TXN_00000203)"),
    service: CounterfactualAttributionService = Depends(get_counterfactual_service),
) -> CounterfactualAnalysisResponse:
    clean_id = _validate_transaction_id(transaction_id)
    try:
        return service.analyze_transaction(clean_id)
    except TransactionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Counterfactual analysis failed: {str(e)}",
        )


@router.get(
    "/transaction/{transaction_id}/attributions",
    response_model=List[CounterfactualAttribution],
    summary="Retrieve ranked Model B feature attributions",
    description="Returns exact TreeSHAP log-odds feature contributions sorted deterministically by absolute magnitude.",
)
def get_feature_attributions(
    transaction_id: str = FastAPIPath(..., description="Unique transaction ID (e.g. TXN_00000203)"),
    service: CounterfactualAttributionService = Depends(get_counterfactual_service),
) -> List[CounterfactualAttribution]:
    clean_id = _validate_transaction_id(transaction_id)
    try:
        attributions, _, _, _, _ = service.compute_attributions(clean_id)
        return attributions
    except TransactionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Attribution calculation failed: {str(e)}",
        )


@router.get(
    "/transaction/{transaction_id}/interventions",
    response_model=List[CounterfactualIntervention],
    summary="Retrieve standard hypothetical intervention simulations",
    description="Returns simulated risk score deltas across pre-computed safe hypothetical feature perturbations.",
)
def get_standard_interventions(
    transaction_id: str = FastAPIPath(..., description="Unique transaction ID (e.g. TXN_00000203)"),
    service: CounterfactualAttributionService = Depends(get_counterfactual_service),
) -> List[CounterfactualIntervention]:
    clean_id = _validate_transaction_id(transaction_id)
    try:
        return service.simulate_interventions(clean_id)
    except TransactionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intervention simulation failed: {str(e)}",
        )


@router.post(
    "/transaction/{transaction_id}/simulate",
    response_model=CounterfactualIntervention,
    summary="Simulate a custom hypothetical feature perturbation",
    description="Evaluates Model B sensitivity under a single whitelisted feature change requested by an analyst.",
)
def simulate_custom_perturbation(
    request: CustomInterventionRequest,
    transaction_id: str = FastAPIPath(..., description="Unique transaction ID (e.g. TXN_00000203)"),
    service: CounterfactualAttributionService = Depends(get_counterfactual_service),
) -> CounterfactualIntervention:
    clean_id = _validate_transaction_id(transaction_id)
    if not request.feature_name or not request.feature_name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="feature_name cannot be empty or whitespace.",
        )
    try:
        return service.simulate_custom_intervention(
            clean_id, request.feature_name.strip(), request.target_value
        )
    except TransactionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Custom simulation failed: {str(e)}",
        )
