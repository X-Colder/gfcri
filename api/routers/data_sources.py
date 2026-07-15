from fastapi import APIRouter

from src.engines.data_source_registry import data_source_overview

router = APIRouter(prefix="/data-sources", tags=["data-sources"])


@router.get("/overview")
def overview():
    return data_source_overview()
