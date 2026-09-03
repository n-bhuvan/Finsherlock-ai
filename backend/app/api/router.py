"""Modular API Router structure for RingGuard AI.

Defines the modular router hierarchy. In Stage 1, only the health endpoint is active.
Domain routers are initialized as empty structures ready for upcoming development stages.
"""

from fastapi import APIRouter
from app.api.endpoints.risk import router as risk_endpoints

api_router = APIRouter()

# Domain Routers
cases_router = APIRouter(prefix="/cases", tags=["Case Management"])
accounts_router = APIRouter(prefix="/accounts", tags=["Account Intelligence"])
transactions_router = APIRouter(prefix="/transactions", tags=["Transactions Feed"])
networks_router = APIRouter(prefix="/networks", tags=["Entity Network Graph"])
evidence_router = APIRouter(prefix="/evidence", tags=["Evidence Engine"])
investigation_router = APIRouter(prefix="/investigation", tags=["Investigation AI"])
timeline_router = APIRouter(prefix="/timeline", tags=["Timeline Engine"])
analytics_router = APIRouter(prefix="/analytics", tags=["Business Analytics"])

# Mount routers
api_router.include_router(risk_endpoints, prefix="/risk", tags=["Risk Analysis"])
api_router.include_router(cases_router)
api_router.include_router(accounts_router)
api_router.include_router(transactions_router)
api_router.include_router(networks_router)
api_router.include_router(evidence_router)
api_router.include_router(investigation_router)
api_router.include_router(timeline_router)
api_router.include_router(analytics_router)
