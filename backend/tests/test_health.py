"""Unit tests for health endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    """Verify that GET /health returns 200 and exact required schema."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ringguard-backend",
    }


def test_api_health_endpoint_not_found() -> None:
    """Verify that GET /api/health is no longer present (returns 404)."""
    response = client.get("/api/health")
    assert response.status_code == 404

