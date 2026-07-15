from fastapi import APIRouter

from src.engines.trade_data import (
    refresh_trade_source_health,
    trade_risk_atlas,
    trade_source_health,
    trade_sources,
)

router = APIRouter(prefix="/trade-risk", tags=["trade-risk"])


@router.get("/atlas")
def latest_trade_risk_atlas(refresh_sources: bool = False):
    return trade_risk_atlas(refresh_sources=refresh_sources)


@router.get("/sources")
def latest_trade_sources():
    return {
        "sources": trade_sources(),
        "source_health": trade_source_health(refresh=False),
    }


@router.post("/refresh")
def refresh_trade_sources():
    return {
        "source_health": refresh_trade_source_health(),
        "note": "Trade-source refresh updates standalone trade metadata only; it does not modify core GFCRI scoring.",
    }
