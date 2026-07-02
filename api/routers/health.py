from datetime import datetime, timezone
from fastapi import APIRouter

from src.storage.database import get_connection
from api.models.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    db_status = "connected"
    try:
        conn = get_connection()
        conn.close()
    except Exception:
        db_status = "error"
    return HealthResponse(
        status="ok",
        database=db_status,
        timestamp=datetime.now(timezone.utc),
    )
