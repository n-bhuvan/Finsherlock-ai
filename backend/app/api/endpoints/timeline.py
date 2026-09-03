"""RingGuard AI — Timeline Engine Endpoints.

Stage 9: Evidence + Timeline Engine.
Exposes read-only endpoints for reconstructing chronological event sequences.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.timeline.schemas import TimelineResponse
from app.timeline.engine import TimelineEngine

router = APIRouter()


@router.get(
    "/transaction/{transaction_id}",
    response_model=TimelineResponse,
    summary="Reconstruct Timeline for Transaction",
    description="Reconstructs chronological event sequence for a transaction context strictly up to its timestamp.",
)
def get_transaction_timeline(
    transaction_id: str = Path(..., min_length=3, max_length=64, description="Transaction ID"),
    db: Session = Depends(get_db),
) -> TimelineResponse:
    clean_id = transaction_id.strip()
    if not clean_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transaction ID cannot be empty or whitespace.",
        )

    engine = TimelineEngine(db)
    try:
        return engine.reconstruct_timeline_for_transaction(clean_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Timeline reconstruction failure: {str(e)}",
        )


@router.get(
    "/account/{account_id}",
    response_model=TimelineResponse,
    summary="Reconstruct Timeline for Account",
    description="Reconstructs chronological event sequence for an account up to its latest transaction timestamp.",
)
def get_account_timeline(
    account_id: str = Path(..., min_length=3, max_length=64, description="Account ID"),
    db: Session = Depends(get_db),
) -> TimelineResponse:
    clean_id = account_id.strip()
    if not clean_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Account ID cannot be empty or whitespace.",
        )

    engine = TimelineEngine(db)
    try:
        return engine.reconstruct_timeline_for_account(clean_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Timeline reconstruction failure: {str(e)}",
        )
