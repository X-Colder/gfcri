from fastapi import APIRouter, Query

from api.dependencies import get_graph
from api.models.core_themes import CoreThemesResponse
from src.engines.core_themes import latest_core_risk_themes

router = APIRouter(prefix="/core-themes", tags=["core-themes"])


@router.get("/latest", response_model=CoreThemesResponse)
def latest_themes(
    limit: int = Query(default=6, ge=1, le=12),
    include_causal: bool = Query(default=False),
):
    return latest_core_risk_themes(
        limit=limit,
        include_causal=include_causal,
        graph=get_graph() if include_causal else None,
    )
