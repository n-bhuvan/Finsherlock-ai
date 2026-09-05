"""FastAPI Endpoints for Stage 20: Outcome Verification + Drift Monitoring.

Provides read-only monitoring and verification REST APIs:
- GET /api/monitoring/drift/health
- GET /api/monitoring/drift
- GET /api/monitoring/outcome/{transaction_id}
- GET /api/monitoring/summary
"""

import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.monitoring.schemas import (
    DriftMonitoringResponse,
    OutcomeVerificationResponse,
    MonitoringSummaryResponse,
)
from app.monitoring.service import (
    OutcomeVerificationService,
    DriftMonitoringService,
    get_drift_service,
)

router = APIRouter()

TXN_ID_PATTERN = re.compile(r"^TXN_\d{8}$")


def _validate_transaction_id(transaction_id: str) -> str:
    """Validate strict transaction identifier format."""
    clean_id = transaction_id.strip()
    if not clean_id or clean_id != transaction_id or not TXN_ID_PATTERN.match(clean_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid transaction_id format '{transaction_id}'. "
                f"Must match strict pattern 'TXN_XXXXXXXX' with no leading/trailing whitespace."
            ),
        )
    return clean_id


@router.get("/drift/health", summary="Health check for Drift Monitoring Engine")
def drift_health_check():
    """Returns runtime health status for Stage 20 monitoring engine."""
    return {
        "status": "healthy",
        "stage": 20,
        "name": "outcome_verification_drift_monitoring",
        "version": "v1.0.0-monitoring-verification",
        "defense_only": True,
        "human_review_required": True,
    }


@router.get("/drift", response_model=DriftMonitoringResponse, summary="Get feature distribution drift metrics")
def get_distribution_drift(
    reference_window: str = Query("train", description="Reference partition ('train' or 'val')"),
    comparison_window: str = Query("test", description="Comparison partition ('test' or 'val')"),
    drift_service: DriftMonitoringService = Depends(get_drift_service),
):
    """Calculates deterministic distribution drift (PSI, JSD, Missingness) between windows."""
    try:
        return drift_service.evaluate_distribution_drift(
            reference_window=reference_window,
            comparison_window=comparison_window,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Drift calculation failed: {str(e)}",
        )


@router.get(
    "/outcome/{transaction_id}",
    response_model=OutcomeVerificationResponse,
    summary="Verify post-decision outcome for a transaction",
)
def get_transaction_outcome(
    transaction_id: str,
    evaluation_context: str = Query("SIMULATED_BENCHMARK", description="'SIMULATED_BENCHMARK' or 'OPERATIONAL'"),
    db: Session = Depends(get_db),
):
    """Verifies transaction outcome against controlled synthetic evaluation metadata."""
    clean_id = _validate_transaction_id(transaction_id)
    svc = OutcomeVerificationService(db)

    try:
        return svc.verify_transaction_outcome(
            transaction_id=clean_id,
            evaluation_context=evaluation_context.upper(),
        )
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Outcome verification failed: {str(e)}",
        )


@router.get("/summary", response_model=MonitoringSummaryResponse, summary="High-level monitoring & verification summary")
def get_monitoring_summary(
    drift_service: DriftMonitoringService = Depends(get_drift_service),
):
    """Combined summary of drift and outcome coverage."""
    drift_res = drift_service.evaluate_distribution_drift(reference_window="train", comparison_window="test")
    return MonitoringSummaryResponse(
        overall_drift_status=drift_res.overall_status,
        total_features_monitored=len(drift_res.metrics),
        significant_features_count=len(drift_res.significant_features),
        watch_features_count=len(drift_res.watch_features),
        reference_window=drift_res.reference_window,
        comparison_window=drift_res.comparison_window,
        outcome_verification_coverage_rate=100.0,
        human_review_required=True,
        disclaimer=drift_res.disclaimer,
    )
