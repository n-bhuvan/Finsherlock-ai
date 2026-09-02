from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(default="ok", description="Service status indicator")
    service: str = Field(default="ringguard-backend", description="Service name identifier")
