from fastapi import APIRouter, Depends, Query

from api.models.institutional_radar import InstitutionalRadarResponse
from api.routers.auth import require_institutional_user
from src.engines.institutional_radar import latest_institutional_radar

router = APIRouter(prefix="/institutional-radar", tags=["institutional-radar"])


@router.get("/latest", response_model=InstitutionalRadarResponse)
def latest_radar(
    limit: int = Query(default=30, ge=5, le=80),
    refresh: bool = Query(default=False),
    user=Depends(require_institutional_user),
):
    return latest_institutional_radar(limit=limit, force_refresh=refresh)
