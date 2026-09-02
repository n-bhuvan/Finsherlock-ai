"""RingGuard AI — Backend Application Entrypoint.

Stage 1: Project Foundation.
Provides the primary FastAPI application instance, CORS configuration,
modular API routing, and root health check endpoint.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.schemas.health import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events."""
    # Startup actions (if any in future stages)
    yield
    # Shutdown actions


def get_cors_origins() -> List[str]:
    """Parse allowed CORS origins from environment or use sensible defaults."""
    env_origins = os.getenv("CORS_ORIGINS", "")
    if env_origins:
        return [origin.strip() for origin in env_origins.split(",") if origin.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ]


app = FastAPI(
    title="RingGuard AI — Risk Operations Backend",
    description="Network-Aware Abuse-Ring Detection & Evidence-First Risk Investigation API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Root Health Check",
    description="Returns the operational status and service identifier.",
)
async def health_check() -> HealthResponse:
    """Primary health check endpoint."""
    return HealthResponse(status="ok", service="ringguard-backend")


# Include the modular API router
app.include_router(api_router, prefix="/api")
