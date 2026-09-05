"""RingGuard AI — Policy Engine & Next-Best-Action Endpoints.

Stage 19: Deterministic Risk Policy Engine + Next-Best-Action (NBA).
Provides validated, read-only HTTP endpoints exposing deterministic policy decisions,
Next-Best-Action recommendations, rules catalog, and system health.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Path as FastAPIPath, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.policy.schemas import (
    PolicyDecision,
    PolicyRulesCatalogResponse,
)
from app.policy.service import (
    PolicyDecisionEngine,
    POLICY_VERSION,
)

router = APIRouter()


def get_policy_service(db: Session = Depends(get_db)) -> PolicyDecisionEngine:
    """Dependency provider for PolicyDecisionEngine."""
    return PolicyDecisionEngine(db)


def _validate_transaction_id(transaction_id: str) -> str:
    """Validate and clean transaction identifier."""
    if not transaction_id or not transaction_id.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transaction ID cannot be empty or whitespace.",
        )
    return transaction_id.strip().upper()


@router.get(
    "/health",
    summary="Policy Engine Health Check",
    description="Returns the operational status, ruleset version, and active rule count of the policy engine.",
)
def get_policy_health(
    service: PolicyDecisionEngine = Depends(get_policy_service),
) -> Dict[str, Any]:
    """Health check validating policy engine status and ruleset version."""
    catalog = service.get_rules_catalog()
    return {
        "status": "ok",
        "service": "ringguard-policy-engine",
        "policy_version": POLICY_VERSION,
        "rules_count": catalog.rule_count,
        "precedence": catalog.precedence_order,
    }


@router.get(
    "/rules",
    response_model=PolicyRulesCatalogResponse,
    summary="Transparent Policy Rules Catalog",
    description="Exposes all declared deterministic rules, precedence order, conditions, and human roles.",
)
def get_policy_rules(
    service: PolicyDecisionEngine = Depends(get_policy_service),
) -> PolicyRulesCatalogResponse:
    """Return transparent policy rules catalog."""
    return service.get_rules_catalog()


@router.get(
    "/transaction/{transaction_id}",
    response_model=PolicyDecision,
    summary="Evaluate Deterministic Next-Best-Action for a Transaction",
    description="Evaluates all multi-stage risk, evidence, uncertainty, and systemic signals to produce a deterministic Next-Best-Action recommendation.",
)
def get_transaction_policy_decision(
    transaction_id: str = FastAPIPath(..., description="Unique transaction ID (e.g. TXN_00000203)"),
    service: PolicyDecisionEngine = Depends(get_policy_service),
) -> PolicyDecision:
    """Primary Next-Best-Action decision endpoint for human analysts."""
    clean_id = _validate_transaction_id(transaction_id)
    try:
        return service.evaluate_transaction(clean_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Policy decision evaluation failed: {str(e)}",
        )
