"""RingGuard AI — Stage 16: AI Forensic Explanation API Endpoints.

Provides endpoints to generate, validate, and retrieve evidence-grounded
structured forensic case explanations with prompt-injection defense and audit logging.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.llm.schemas import LLMExplanationResponse, GenerateExplanationRequest
from app.llm.service import LLMExplanationService

router = APIRouter()


@router.post(
    "/generate",
    response_model=LLMExplanationResponse,
    summary="Generate Grounded Forensic AI Explanation",
    description=(
        "Synthesize evidence-grounded structured forensic explanation with strict claim validation, "
        "prompt-injection defense, immutable model risk scores, and hash-chained audit logging."
    ),
)
def generate_explanation(
    payload: GenerateExplanationRequest,
    db: Session = Depends(get_db),
) -> LLMExplanationResponse:
    """Generate structured, auditable explanation for a transaction."""
    service = LLMExplanationService()
    try:
        explanation = service.generate_explanation(
            db=db,
            transaction_id=payload.transaction_id,
            provider_override=payload.provider,
            force_fallback=payload.force_fallback or False,
        )
        return explanation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate forensic explanation: {str(e)}",
        )


@router.get(
    "/{transaction_id}",
    response_model=LLMExplanationResponse,
    summary="Get Grounded Forensic Explanation by Transaction ID (Retrieval-Only)",
    description=(
        "Retrieve a previously generated grounded forensic explanation for an investigated transaction. "
        "Strictly retrieval-only: does NOT invoke Gemini, generate explanations, or mutate audit storage."
    ),
)
def get_explanation(
    transaction_id: str,
) -> LLMExplanationResponse:
    """Retrieve saved explanation for a specific transaction.
    
    Strictly retrieval-only: returns HTTP 404 if no explanation has been generated yet.
    """
    service = LLMExplanationService()
    saved = service.get_saved_explanation(transaction_id)
    if not saved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No forensic explanation found for transaction '{transaction_id}'. "
                f"Please generate an explanation first via POST /api/investigation/explanation/generate"
            ),
        )
    return saved

