"""Risk Analysis Endpoints for RingGuard AI.

Stage 8: FastAPI Risk APIs.
Provides read-only, validated HTTP endpoints exposing Model A (Baseline)
and Model B (Graph-Enhanced) risk assessment probabilities.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.services.model_service import get_model_service, ModelService
from app.services.feature_service import get_feature_service, FeatureService, TransactionNotFoundError
from app.schemas.risk import (
    RiskHealthResponse,
    RiskResponse,
    BaselineRiskResponse,
    NetworkRiskResponse,
    RiskBand,
)

router = APIRouter()


@router.get(
    "/health",
    response_model=RiskHealthResponse,
    summary="Risk Service Health Check",
    description="Reports the operational status of the risk engine, ML model artifacts, and database connectivity.",
)
def get_risk_health(
    db: Session = Depends(get_db),
    model_service: ModelService = Depends(get_model_service),
) -> RiskHealthResponse:
    """Lightweight health check validating database connectivity and model artifact caching."""
    db_connected = False
    try:
        # Lightweight connection ping
        db.execute(text("SELECT 1;"))
        db_connected = True
    except Exception:
        db_connected = False

    models_health = model_service.get_health_details()
    baseline_loaded = models_health.get("baseline", None) is not None and models_health["baseline"].loaded
    graph_loaded = models_health.get("graph", None) is not None and models_health["graph"].loaded

    overall_status = "ok" if (db_connected and baseline_loaded and graph_loaded) else "degraded"

    return RiskHealthResponse(
        status=overall_status,
        service="ringguard-risk-engine",
        baseline_model_loaded=baseline_loaded,
        graph_model_loaded=graph_loaded,
        database_connected=db_connected,
        models=models_health,
    )


@router.get(
    "/transaction/{transaction_id}",
    response_model=RiskResponse,
    summary="Primary Transaction Risk Assessment",
    description="Evaluates a transaction using the primary network-aware model (Model B) and returns an analytical risk probability.",
)
def get_transaction_risk(
    transaction_id: str,
    db: Session = Depends(get_db),
    model_service: ModelService = Depends(get_model_service),
    feature_service: FeatureService = Depends(get_feature_service),
) -> RiskResponse:
    """Primary risk endpoint defaulting to the full network model (Model B, 58 features)."""
    if not transaction_id or not transaction_id.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid transaction ID")

    try:
        feats_df, _ = feature_service.get_features(db, transaction_id.strip(), model_type="graph")
    except TransactionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found in database.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feature extraction failed: {str(e)}",
        )

    prob = model_service.predict_graph(feats_df)
    band = model_service.determine_risk_band(prob)

    return RiskResponse(
        transaction_id=transaction_id.strip(),
        prediction_unit="transaction",
        model="ringguard_graph_xgb_v1",
        model_version="v1",
        predicted_ring_probability=prob,
        decision_threshold=0.5,
        risk_band=band,
        feature_count=58,
        graph_features_count=21,
        graph_context_available=True,
    )


@router.get(
    "/transaction/{transaction_id}/baseline",
    response_model=BaselineRiskResponse,
    summary="Baseline Model Risk Assessment",
    description="Evaluates a transaction using Model A (Transaction + Behavior baseline, 37 features, 0 graph features).",
)
def get_transaction_baseline_risk(
    transaction_id: str,
    db: Session = Depends(get_db),
    model_service: ModelService = Depends(get_model_service),
    feature_service: FeatureService = Depends(get_feature_service),
) -> BaselineRiskResponse:
    """Evaluates transaction risk using Model A (37 features only, zero graph features)."""
    if not transaction_id or not transaction_id.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid transaction ID")

    try:
        feats_df, _ = feature_service.get_features(db, transaction_id.strip(), model_type="baseline")
    except TransactionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found in database.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feature extraction failed: {str(e)}",
        )

    prob = model_service.predict_baseline(feats_df)
    band = model_service.determine_risk_band(prob)

    return BaselineRiskResponse(
        transaction_id=transaction_id.strip(),
        prediction_unit="transaction",
        model="ringguard_baseline_xgb_v1",
        model_version="v1",
        predicted_ring_probability=prob,
        decision_threshold=0.5,
        risk_band=band,
        feature_count=37,
        graph_features_count=0,
        graph_context_available=False,
    )


@router.get(
    "/transaction/{transaction_id}/network",
    response_model=NetworkRiskResponse,
    summary="Network Model Risk Assessment",
    description="Evaluates a transaction using Model B (Transaction + Behavior + Point-in-Time Graph, 58 features).",
)
def get_transaction_network_risk(
    transaction_id: str,
    db: Session = Depends(get_db),
    model_service: ModelService = Depends(get_model_service),
    feature_service: FeatureService = Depends(get_feature_service),
) -> NetworkRiskResponse:
    """Evaluates transaction risk using Model B (58 features, 21 graph features)."""
    if not transaction_id or not transaction_id.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid transaction ID")

    try:
        feats_df, _ = feature_service.get_features(db, transaction_id.strip(), model_type="graph")
    except TransactionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found in database.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feature extraction failed: {str(e)}",
        )

    prob = model_service.predict_graph(feats_df)
    band = model_service.determine_risk_band(prob)

    return NetworkRiskResponse(
        transaction_id=transaction_id.strip(),
        prediction_unit="transaction",
        model="ringguard_graph_xgb_v1",
        model_version="v1",
        predicted_ring_probability=prob,
        decision_threshold=0.5,
        risk_band=band,
        feature_count=58,
        graph_features_count=21,
        graph_context_available=True,
    )
