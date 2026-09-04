"""Modular API Router structure for RingGuard AI.

Defines the modular router hierarchy.
Active routers: /risk, /evidence, /timeline, /investigation.
Remaining domain routers are initialized as empty structures ready for upcoming development stages.
"""

from fastapi import APIRouter
from app.api.endpoints.risk import router as risk_endpoints
from app.api.endpoints.evidence import router as evidence_endpoints
from app.api.endpoints.timeline import router as timeline_endpoints
from app.api.endpoints.investigation import router as investigation_endpoints
from app.api.endpoints.analytics import router as analytics_endpoints

api_router = APIRouter()

# Domain Routers (Active & Upcoming)
cases_router = APIRouter(prefix="/cases", tags=["Case Management"])
accounts_router = APIRouter(prefix="/accounts", tags=["Account Intelligence"])
transactions_router = APIRouter(prefix="/transactions", tags=["Transactions Feed"])
networks_router = APIRouter(prefix="/networks", tags=["Entity Network Graph"])
analytics_router = APIRouter(prefix="/analytics", tags=["Business Analytics"])
analytics_router.include_router(analytics_endpoints)

# Mount active routers
api_router.include_router(risk_endpoints, prefix="/risk", tags=["Risk Analysis"])
api_router.include_router(evidence_endpoints, prefix="/evidence", tags=["Evidence Engine"])
api_router.include_router(timeline_endpoints, prefix="/timeline", tags=["Timeline Engine"])
api_router.include_router(investigation_endpoints, prefix="/investigation", tags=["Investigation Tools"])

# Mount upcoming domain routers
api_router.include_router(cases_router)
api_router.include_router(accounts_router)
api_router.include_router(transactions_router)
api_router.include_router(networks_router)
api_router.include_router(analytics_router)
