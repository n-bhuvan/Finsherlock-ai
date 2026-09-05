"""RingGuard AI — Portfolio Prioritization API Endpoints.

V2 Stage 16: Portfolio Risk Prioritization + Expected Value.
Exposes read-only endpoints for evaluating individual case prioritization
and ranking portfolio queues deterministically.
Defense-only decision support with strict human-in-the-loop governance.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.prioritization.schemas import (
    PrioritizedCaseItem,
    PortfolioPrioritizationResponse,
)
from app.prioritization.service import PortfolioPrioritizationService

router = APIRouter()


@router.get(
    "/health",
    summary="Portfolio Prioritization Health Check",
    description="Returns operational status of the Stage 16 Portfolio Prioritization engine.",
)
def get_prioritization_health():
    return {
        "status": "ok",
        "service": "ringguard-portfolio-prioritization",
        "stage": 16,
        "scoring_formula": "0.25*p_calib + 0.25*EVnorm + 0.15*Expnorm + 0.15*NetLev + 0.10*SysAnom + 0.10*u0",
        "defense_only": True,
        "human_approval_required": True,
    }


@router.get(
    "/transaction/{transaction_id}",
    response_model=PrioritizedCaseItem,
    summary="Get Case Prioritization & Expected Value",
    description="Computes deterministic expected value, input signals, and priority score for a single transaction.",
)
def get_transaction_prioritization(
    transaction_id: str = Path(..., min_length=3, max_length=64, description="Transaction ID"),
    db: Session = Depends(get_db),
) -> PrioritizedCaseItem:
    clean_id = transaction_id.strip()
    if not clean_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transaction ID cannot be empty or whitespace.",
        )

    service = PortfolioPrioritizationService(db)
    try:
        return service.prioritize_transaction(clean_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating prioritization for '{clean_id}': {str(e)}",
        )


@router.get(
    "/portfolio",
    response_model=PortfolioPrioritizationResponse,
    summary="Get Prioritized Portfolio Queue",
    description="Scores and orders candidate cases descending by deterministic priority score.",
)
def get_portfolio_prioritization(
    limit: int = Query(default=20, ge=1, le=100, description="Max cases to return"),
    transaction_ids: Optional[str] = Query(
        default=None,
        description="Optional comma-separated list of transaction IDs to evaluate",
    ),
    db: Session = Depends(get_db),
) -> PortfolioPrioritizationResponse:
    tx_list: Optional[List[str]] = None
    if transaction_ids:
        tx_list = [t.strip().upper() for t in transaction_ids.split(",") if t.strip()]

    service = PortfolioPrioritizationService(db)
    try:
        return service.prioritize_portfolio(transaction_ids=tx_list, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing portfolio prioritization: {str(e)}",
        )
