"""RingGuard AI — Controlled Investigation Endpoints.

Stage 10: Controlled Investigation Tools.
Exposes bounded, deterministic, read-only investigation tools via REST APIs.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.investigation.schemas import (
    ToolExecutionResult,
    ToolExecutionStatus,
    InvestigatorDossierResponse,
    InvestigationStateResponse,
    RunInvestigationRequest,
    CasePrioritizationResponse,
    InvestigationEfficiencyResponse,
    AdaptiveInvestigationResponse,
    AdaptiveBenchmarkResponse,
)
from app.investigation.service import InvestigationService
from app.investigation.agent import InvestigationAgent
from app.investigation.adaptive import AdaptiveInvestigationEngine
from app.investigation.prioritization import CasePrioritizationService
from app.investigation.efficiency import InvestigationEfficiencyService
from app.services.dossier_service import get_dossier_service, DossierService
from app.services.feature_service import TransactionNotFoundError

router = APIRouter()


def _handle_result(res: ToolExecutionResult) -> ToolExecutionResult:
    """Translate internal tool status into proper HTTP response codes."""
    if res.status == ToolExecutionStatus.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=res.error_details or f"Target '{res.target}' not found.",
        )
    if res.status == ToolExecutionStatus.INVALID_INPUT:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=res.error_details or "Invalid input parameter.",
        )
    if res.status == ToolExecutionStatus.UNAVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=res.error_details or "Service temporarily unavailable.",
        )
    return res


# ==============================================================================
# ACCOUNT INVESTIGATION ENDPOINTS
# ==============================================================================

@router.get(
    "/account/{account_id}",
    response_model=ToolExecutionResult,
    summary="Get Account Details",
    description="Tool: get_account — Retrieves factual operational metadata for an account.",
)
def api_get_account(
    account_id: str = Path(..., min_length=3, max_length=64, description="Account ID"),
    as_of: Optional[str] = Query(None, description="Optional ISO timestamp for point-in-time boundary"),
    db: Session = Depends(get_db),
) -> ToolExecutionResult:
    clean_id = account_id.strip()
    if not clean_id:
        raise HTTPException(status_code=422, detail="Account ID cannot be empty or whitespace.")
    service = InvestigationService(db)
    return _handle_result(service.get_account(clean_id, as_of=as_of))


@router.get(
    "/account/{account_id}/transactions",
    response_model=ToolExecutionResult,
    summary="Get Account Transactions",
    description="Tool: get_transactions — Retrieves bounded, chronologically sorted transactions for an account.",
)
def api_get_transactions(
    account_id: str = Path(..., min_length=3, max_length=64, description="Account ID"),
    start_time: Optional[str] = Query(None, description="Optional ISO start timestamp"),
    end_time: Optional[str] = Query(None, description="Optional ISO end timestamp"),
    limit: int = Query(50, ge=1, le=100, description="Max transaction records to return (1-100)"),
    db: Session = Depends(get_db),
) -> ToolExecutionResult:
    clean_id = account_id.strip()
    if not clean_id:
        raise HTTPException(status_code=422, detail="Account ID cannot be empty or whitespace.")
    service = InvestigationService(db)
    return _handle_result(
        service.get_transactions(clean_id, start_time=start_time, end_time=end_time, limit=limit)
    )


@router.get(
    "/account/{account_id}/related",
    response_model=ToolExecutionResult,
    summary="Find Related Accounts",
    description="Tool: find_related_accounts — Discovers accounts linked via shared devices, IPs, or common beneficiaries.",
)
def api_find_related_accounts(
    account_id: str = Path(..., min_length=3, max_length=64, description="Account ID"),
    as_of: Optional[str] = Query(None, description="Optional point-in-time boundary"),
    limit: int = Query(20, ge=1, le=50, description="Max related accounts to return (1-50)"),
    db: Session = Depends(get_db),
) -> ToolExecutionResult:
    clean_id = account_id.strip()
    if not clean_id:
        raise HTTPException(status_code=422, detail="Account ID cannot be empty or whitespace.")
    service = InvestigationService(db)
    return _handle_result(service.find_related_accounts(clean_id, as_of=as_of, limit=limit))


@router.get(
    "/account/{account_id}/devices",
    response_model=ToolExecutionResult,
    summary="Find Shared Devices",
    description="Tool: find_shared_devices — Discovers hardware endpoints co-used by this account and other accounts.",
)
def api_find_shared_devices(
    account_id: str = Path(..., min_length=3, max_length=64, description="Account ID"),
    as_of: Optional[str] = Query(None, description="Optional point-in-time boundary"),
    db: Session = Depends(get_db),
) -> ToolExecutionResult:
    clean_id = account_id.strip()
    if not clean_id:
        raise HTTPException(status_code=422, detail="Account ID cannot be empty or whitespace.")
    service = InvestigationService(db)
    return _handle_result(service.find_shared_devices(clean_id, as_of=as_of))


@router.get(
    "/account/{account_id}/ips",
    response_model=ToolExecutionResult,
    summary="Find Shared IPs",
    description="Tool: find_shared_ips — Discovers network IP addresses co-used by this account and other accounts.",
)
def api_find_shared_ips(
    account_id: str = Path(..., min_length=3, max_length=64, description="Account ID"),
    as_of: Optional[str] = Query(None, description="Optional point-in-time boundary"),
    db: Session = Depends(get_db),
) -> ToolExecutionResult:
    clean_id = account_id.strip()
    if not clean_id:
        raise HTTPException(status_code=422, detail="Account ID cannot be empty or whitespace.")
    service = InvestigationService(db)
    return _handle_result(service.find_shared_ips(clean_id, as_of=as_of))


@router.get(
    "/account/{account_id}/beneficiaries",
    response_model=ToolExecutionResult,
    summary="Find Common Beneficiaries",
    description="Tool: find_common_beneficiaries — Discovers recipients shared between this account and other accounts.",
)
def api_find_common_beneficiaries(
    account_id: str = Path(..., min_length=3, max_length=64, description="Account ID"),
    as_of: Optional[str] = Query(None, description="Optional point-in-time boundary"),
    db: Session = Depends(get_db),
) -> ToolExecutionResult:
    clean_id = account_id.strip()
    if not clean_id:
        raise HTTPException(status_code=422, detail="Account ID cannot be empty or whitespace.")
    service = InvestigationService(db)
    return _handle_result(service.find_common_beneficiaries(clean_id, as_of=as_of))


@router.get(
    "/account/{account_id}/fund-flow",
    response_model=ToolExecutionResult,
    summary="Trace Fund Flow from Account",
    description="Tool: trace_fund_flow — Traces verified transaction transfers originating from this account.",
)
def api_trace_account_fund_flow(
    account_id: str = Path(..., min_length=3, max_length=64, description="Account ID"),
    as_of: Optional[str] = Query(None, description="Optional point-in-time boundary"),
    max_depth: int = Query(2, ge=1, le=3, description="Max traversal depth (1-3 hops)"),
    max_results: int = Query(50, ge=1, le=100, description="Max transfer records (1-100)"),
    db: Session = Depends(get_db),
) -> ToolExecutionResult:
    clean_id = account_id.strip()
    if not clean_id:
        raise HTTPException(status_code=422, detail="Account ID cannot be empty or whitespace.")
    service = InvestigationService(db)
    return _handle_result(
        service.trace_fund_flow(clean_id, as_of=as_of, max_depth=max_depth, max_results=max_results)
    )


@router.get(
    "/account/{account_id}/timeline",
    response_model=ToolExecutionResult,
    summary="Reconstruct Timeline for Account",
    description="Tool: reconstruct_timeline — Reconstructs chronological event sequence for this account.",
)
def api_reconstruct_account_timeline(
    account_id: str = Path(..., min_length=3, max_length=64, description="Account ID"),
    as_of: Optional[str] = Query(None, description="Optional point-in-time boundary"),
    db: Session = Depends(get_db),
) -> ToolExecutionResult:
    clean_id = account_id.strip()
    if not clean_id:
        raise HTTPException(status_code=422, detail="Account ID cannot be empty or whitespace.")
    service = InvestigationService(db)
    return _handle_result(service.reconstruct_timeline(clean_id, as_of=as_of))


# ==============================================================================
# TRANSACTION INVESTIGATION ENDPOINTS
# ==============================================================================

@router.get(
    "/transaction/{transaction_id}/fund-flow",
    response_model=ToolExecutionResult,
    summary="Trace Fund Flow from Transaction",
    description="Tool: trace_fund_flow — Traces verified transaction transfers linked to this payment.",
)
def api_trace_transaction_fund_flow(
    transaction_id: str = Path(..., min_length=3, max_length=64, description="Transaction ID"),
    as_of: Optional[str] = Query(None, description="Optional point-in-time boundary"),
    max_depth: int = Query(2, ge=1, le=3, description="Max traversal depth (1-3 hops)"),
    max_results: int = Query(50, ge=1, le=100, description="Max transfer records (1-100)"),
    db: Session = Depends(get_db),
) -> ToolExecutionResult:
    clean_id = transaction_id.strip()
    if not clean_id:
        raise HTTPException(status_code=422, detail="Transaction ID cannot be empty or whitespace.")
    service = InvestigationService(db)
    return _handle_result(
        service.trace_fund_flow(clean_id, as_of=as_of, max_depth=max_depth, max_results=max_results)
    )


@router.get(
    "/transaction/{transaction_id}/timeline",
    response_model=ToolExecutionResult,
    summary="Reconstruct Timeline for Transaction",
    description="Tool: reconstruct_timeline — Reconstructs chronological event sequence for this transaction context.",
)
def api_reconstruct_transaction_timeline(
    transaction_id: str = Path(..., min_length=3, max_length=64, description="Transaction ID"),
    as_of: Optional[str] = Query(None, description="Optional point-in-time boundary"),
    db: Session = Depends(get_db),
) -> ToolExecutionResult:
    clean_id = transaction_id.strip()
    if not clean_id:
        raise HTTPException(status_code=422, detail="Transaction ID cannot be empty or whitespace.")
    service = InvestigationService(db)
    return _handle_result(service.reconstruct_timeline(clean_id, as_of=as_of))


@router.get(
    "/transaction/{transaction_id}/risk-features",
    response_model=ToolExecutionResult,
    summary="Get Risk Features and Model Output",
    description="Tool: get_risk_features — Retrieves Stage 8 feature values and derived model risk assessment.",
)
def api_get_risk_features(
    transaction_id: str = Path(..., min_length=3, max_length=64, description="Transaction ID"),
    model_type: str = Query("graph", description="'graph' (58 features) or 'baseline' (37 features)"),
    db: Session = Depends(get_db),
) -> ToolExecutionResult:
    clean_id = transaction_id.strip()
    if not clean_id:
        raise HTTPException(status_code=422, detail="Transaction ID cannot be empty or whitespace.")
    service = InvestigationService(db)
    return _handle_result(service.get_risk_features(clean_id, model_type=model_type))


@router.get(
    "/transaction/{transaction_id}/dossier",
    response_model=InvestigatorDossierResponse,
    summary="Generate Investigator Dossier",
    description="Synthesizes a deterministic post-hoc case brief, corroborating evidence chain, potential benign explanations, and recommended inquiries.",
)
def api_get_transaction_dossier(
    transaction_id: str = Path(..., min_length=3, max_length=64, description="Transaction ID"),
    db: Session = Depends(get_db),
    dossier_service: DossierService = Depends(get_dossier_service),
) -> InvestigatorDossierResponse:
    """Generates structured deterministic case brief for human risk investigators."""
    clean_id = transaction_id.strip() if transaction_id else ""
    if not clean_id:
        raise HTTPException(status_code=422, detail="Transaction ID cannot be empty or whitespace.")

    try:
        return dossier_service.generate_dossier(db, clean_id)
    except TransactionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{clean_id}' not found in database.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dossier generation failed: {str(e)}",
        )


# ==============================================================================
# STAGE 15: BOUNDED UNCERTAINTY INVESTIGATION AGENT & EFFICIENCY ENDPOINTS
# ==============================================================================

efficiency_service = InvestigationEfficiencyService()


@router.post(
    "/agent/run",
    response_model=InvestigationStateResponse,
    summary="Run Bounded Uncertainty Investigation",
    description="Executes bounded deterministic investigation based on Expected Information Gain and explicit stopping criteria.",
)
def api_run_investigation(
    req: RunInvestigationRequest,
    db: Session = Depends(get_db),
) -> InvestigationStateResponse:
    clean_id = req.transaction_id.strip()
    if not clean_id:
        raise HTTPException(status_code=422, detail="Transaction ID cannot be empty or whitespace.")

    try:
        agent = InvestigationAgent(db)
        return agent.run_investigation(
            clean_id,
            max_steps=req.max_steps or 5,
            tool_budget=req.tool_budget or 150.0,
            interception_rate=req.interception_rate or 0.85,
        )
    except TransactionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{clean_id}' not found in database.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investigation execution failed: {str(e)}",
        )


@router.get(
    "/agent/prioritization",
    response_model=CasePrioritizationResponse,
    summary="Get Prioritized Case Triage Queue",
    description="Deterministic triage queue ordered by Calibrated Risk (35%), Exposure (30%), Uncertainty (20%), and Network Leverage (15%).",
)
def api_get_case_prioritization(
    limit: int = Query(20, ge=1, le=100, description="Max cases to return"),
    db: Session = Depends(get_db),
) -> CasePrioritizationResponse:
    try:
        prio = CasePrioritizationService(db)
        return prio.prioritize_cases(limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prioritization query failed: {str(e)}",
        )


@router.get(
    "/agent/efficiency",
    response_model=InvestigationEfficiencyResponse,
    summary="Get Sliced Investigation Efficiency Metrics",
    description="Returns verified offline benchmark metrics on step compression, tool costs, uncertainty reduction, and stopping reason distributions across evaluation slices.",
)
def api_get_investigation_efficiency() -> Dict[str, Any]:
    metrics = efficiency_service.get_efficiency_metrics()
    return metrics


@router.get(
    "/agent/{transaction_id}/state",
    response_model=InvestigationStateResponse,
    summary="Get Investigation State & Trace",
    description="Retrieves cached investigation state or executes bounded investigation on the fly.",
)
def api_get_investigation_state(
    transaction_id: str = Path(..., min_length=3, max_length=64, description="Transaction ID"),
    db: Session = Depends(get_db),
) -> InvestigationStateResponse:
    clean_id = transaction_id.strip()
    if not clean_id:
        raise HTTPException(status_code=422, detail="Transaction ID cannot be empty or whitespace.")

    try:
        agent = InvestigationAgent(db)
        return agent.get_investigation_state(clean_id)
    except TransactionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{clean_id}' not found in database.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve investigation state: {str(e)}",
        )


# ==============================================================================
# STAGE 17: ADAPTIVE UNCERTAINTY-DRIVEN INVESTIGATION ENDPOINTS
# ==============================================================================

@router.get(
    "/transaction/{transaction_id}/adaptive",
    response_model=AdaptiveInvestigationResponse,
    summary="Run Stage 17 Adaptive Uncertainty Investigation",
    description="Executes deterministic uncertainty-driven investigation tracking EIG, tool cost, and explicit stopping criteria.",
)
def api_get_adaptive_investigation(
    transaction_id: str = Path(..., min_length=3, max_length=64, description="Transaction ID"),
    max_steps: int = Query(5, ge=1, le=9, description="Maximum investigation steps"),
    tool_budget: float = Query(150.0, ge=15.0, le=500.0, description="Maximum tool budget in INR"),
    db: Session = Depends(get_db),
) -> AdaptiveInvestigationResponse:
    clean_id = transaction_id.strip()
    if not clean_id:
        raise HTTPException(status_code=422, detail="Transaction ID cannot be empty or whitespace.")

    try:
        engine = AdaptiveInvestigationEngine(db)
        return engine.run_investigation(clean_id, max_steps=max_steps, tool_budget=tool_budget)
    except TransactionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{clean_id}' not found in database.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Adaptive investigation failed: {str(e)}",
        )


@router.get(
    "/adaptive/benchmark",
    response_model=AdaptiveBenchmarkResponse,
    summary="Get Stage 17 Adaptive Investigation Benchmark",
    description="Returns held-out test evaluation metrics across slices comparing V1 historical and Stage 17 performance.",
)
def api_get_adaptive_benchmark() -> Dict[str, Any]:
    import json
    from pathlib import Path
    bench_file = Path(__file__).resolve().parents[3] / "ml" / "data" / "evaluation" / "stage17_investigation_benchmark.json"
    if not bench_file.exists():
        return {
            "status": "Unavailable",
            "metadata": {},
            "slices": {},
            "comparison_with_v1": {},
            "methodology_notes": "Benchmark evaluation not yet executed. Run scripts/run_stage17_evaluation.py.",
            "disclaimer": "Stage 17 benchmark evaluated on held-out test partition.",
        }
    try:
        with open(bench_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load Stage 17 benchmark: {str(e)}",
        )



