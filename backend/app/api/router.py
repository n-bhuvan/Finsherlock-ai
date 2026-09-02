"""Modular API Router structure for RingGuard AI.

Defines the modular router hierarchy. In Stage 1, only the health endpoint is active.
Domain routers are initialized as empty structures ready for upcoming development stages.
"""

from fastapi import APIRouter

api_router = APIRouter()

# Planned Domain Routers (Empty in Stage 1 — Foundation Only)
risk_router = APIRouter(prefix="/risk", tags=["Risk Analysis"])
cases_router = APIRouter(prefix="/cases", tags=["Case Management"])
accounts_router = APIRouter(prefix="/accounts", tags=["Account Intelligence"])
transactions_router = APIRouter(prefix="/transactions", tags=["Transactions Feed"])
networks_router = APIRouter(prefix="/networks", tags=["Entity Network Graph"])
evidence_router = APIRouter(prefix="/evidence", tags=["Evidence Engine"])
investigation_router = APIRouter(prefix="/investigation", tags=["Investigation AI"])
timeline_router = APIRouter(prefix="/timeline", tags=["Timeline Engine"])
analytics_router = APIRouter(prefix="/analytics", tags=["Business Analytics"])

# Mount routers
api_router.include_router(risk_router)
api_router.include_router(cases_router)
api_router.include_router(accounts_router)
api_router.include_router(transactions_router)
api_router.include_router(networks_router)
api_router.include_router(evidence_router)
api_router.include_router(investigation_router)
api_router.include_router(timeline_router)
api_router.include_router(analytics_router)
