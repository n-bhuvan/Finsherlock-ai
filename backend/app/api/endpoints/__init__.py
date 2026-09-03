"""API endpoints package."""

from app.api.endpoints.risk import router as risk_router
from app.api.endpoints.evidence import router as evidence_router
from app.api.endpoints.timeline import router as timeline_router
from app.api.endpoints.investigation import router as investigation_router

__all__ = ["risk_router", "evidence_router", "timeline_router", "investigation_router"]
