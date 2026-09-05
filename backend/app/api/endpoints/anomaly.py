"""RingGuard AI — Systemic Risk Anomaly Detection API Endpoints.

V2 Stage 15: Systemic Risk Anomaly Detection.
Exposes read-only endpoints for evaluating deterministic multi-scope systemic anomalies.
Defense-only decision support with strict human-in-the-loop governance.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.anomaly.schemas import SystemicAnomalyResponse
from app.anomaly.service import SystemicAnomalyService

router = APIRouter()


@router.get(
    "/health",
    summary="Systemic Anomaly Health Check",
    description="Returns operational health of the Stage 15 Systemic Anomaly engine.",
)
def get_systemic_anomaly_health():
    return {
        "status": "ok",
        "service": "ringguard-systemic-anomaly",
        "stage": 15,
        "scopes": ["ACCOUNT", "MERCHANT", "RING_NETWORK", "SYSTEMIC_INFRASTRUCTURE"],
        "defense_only": True,
        "human_approval_required": True,
    }


@router.get(
    "/transaction/{transaction_id}",
    response_model=SystemicAnomalyResponse,
    summary="Analyze Multi-Scope Systemic Anomaly",
    description=(
        "Performs deterministic multi-scope anomaly evaluation across Account, Merchant, "
        "Ring Network, and Systemic Infrastructure dimensions strictly up to transaction timestamp T."
    ),
)
def get_transaction_systemic_anomaly(
    transaction_id: str = Path(..., min_length=3, max_length=64, description="Transaction ID"),
    db: Session = Depends(get_db),
) -> SystemicAnomalyResponse:
    clean_id = transaction_id.strip()
    if not clean_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transaction ID cannot be empty or whitespace.",
        )

    service = SystemicAnomalyService(db)
    try:
        return service.analyze_transaction(clean_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing systemic anomaly for '{clean_id}': {str(e)}",
        )
