from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime


class PaginationParams(BaseModel):
    limit: int = Field(default=30, ge=1, le=365)
