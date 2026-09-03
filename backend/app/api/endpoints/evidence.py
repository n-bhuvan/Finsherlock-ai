"""RingGuard AI — Evidence Engine Endpoints.

Stage 9: Evidence + Timeline Engine.
Exposes read-only endpoints for extracting and ranking structured evidence objects.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.evidence.schemas import EvidenceListResponse
from app.evidence.engine import EvidenceEngine

router = APIRouter()


@router.get(
    "/transaction/{transaction_id}",
    response_model=EvidenceListResponse,
    summary="Extract Evidence for Transaction",
    description="Extracts and deterministically ranks observed evidence signals for a transaction strictly up to its timestamp.",
)
def get_transaction_evidence(
    transaction_id: str = Path(..., min_length=3, max_length=64, description="Transaction ID"),
    db: Session = Depends(get_db),
) -> EvidenceListResponse:
    clean_id = transaction_id.strip()
    if not clean_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transaction ID cannot be empty or whitespace.",
        )

    engine = EvidenceEngine(db)
    try:
        return engine.extract_evidence_for_transaction(clean_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evidence extraction failure: {str(e)}",
        )


@router.get(
    "/account/{account_id}",
    response_model=EvidenceListResponse,
    summary="Extract Evidence for Account",
    description="Extracts and ranks observed evidence signals for an account across historical activity up to its latest transaction.",
)
def get_account_evidence(
    account_id: str = Path(..., min_length=3, max_length=64, description="Account ID"),
    db: Session = Depends(get_db),
) -> EvidenceListResponse:
    clean_id = account_id.strip()
    if not clean_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Account ID cannot be empty or whitespace.",
        )

    engine = EvidenceEngine(db)
    try:
        return engine.extract_evidence_for_account(clean_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evidence extraction failure: {str(e)}",
        )
