import time
import asyncio

from fastapi import APIRouter, Query, HTTPException

from src.engines.ehs.config import ECONOMIES
from src.engines.ehs.scoring import CYCLE_LABELS

router = APIRouter(prefix="/ehs", tags=["ehs"])

_cache: dict = {"results": [], "ts": 0}
_CACHE_TTL = 21600


@router.get("/economies")
def list_economies():
    return [
        {"code": e.code, "name_zh": e.name_zh, "name_en": e.name_en, "region": e.region}
        for e in ECONOMIES.values()
    ]


@router.get("/scores")
async def get_all_scores(refresh: bool = Query(default=False)):
    now = time.time()

    if not refresh and _cache["results"] and (now - _cache["ts"]) < _CACHE_TTL:
        return _cache["results"]

    if not refresh:
        db_results = _read_from_db()
        if db_results:
            _cache["results"] = db_results
            _cache["ts"] = now
            return db_results

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, _compute_all)
    _cache["results"] = results
    _cache["ts"] = time.time()
    return results


@router.get("/scores/{economy_code}")
async def get_economy_score(economy_code: str):
    economy_code = economy_code.upper()
    if economy_code not in ECONOMIES:
        raise HTTPException(404, f"Unknown economy: {economy_code}")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _compute_single, economy_code)
    if not result:
        raise HTTPException(500, "Failed to compute score")
    return result


@router.get("/history/{economy_code}")
def get_economy_history(economy_code: str, limit: int = Query(default=30, ge=1, le=120)):
    economy_code = economy_code.upper()
    if economy_code not in ECONOMIES:
        raise HTTPException(404, f"Unknown economy: {economy_code}")

    from src.engines.ehs.storage import get_ehs_score_history
    return get_ehs_score_history(economy_code, limit=limit)


def _read_from_db():
    try:
        from src.engines.ehs.storage import get_latest_ehs_scores
        rows = get_latest_ehs_scores()
        if not rows:
            return []
        results = []
        for r in rows:
            economy = ECONOMIES.get(r["economy_code"])
            results.append({
                "economy_code": r["economy_code"],
                "economy_name": economy.name_zh if economy else r["economy_code"],
                "score_date": str(r["score_date"]),
                "ehs_score": float(r["ehs_score"]),
                "growth_score": float(r["growth_score"]) if r["growth_score"] else 50.0,
                "labor_score": float(r["labor_score"]) if r["labor_score"] else 50.0,
                "price_score": float(r["price_score"]) if r["price_score"] else 50.0,
                "external_score": float(r["external_score"]) if r["external_score"] else 50.0,
                "financial_score": float(r["financial_score"]) if r["financial_score"] else 50.0,
                "cycle_phase": r["cycle_phase"] or "slowdown",
                "cycle_label": CYCLE_LABELS.get(r["cycle_phase"], r["cycle_phase"] or ""),
                "score_change_1m": float(r["score_change_1m"]) if r.get("score_change_1m") else None,
                "indicator_details": r.get("indicator_details"),
            })
        results.sort(key=lambda x: x["ehs_score"], reverse=True)
        return results
    except Exception:
        return []


def _compute_all():
    from src.engines.ehs.orchestrator import EHSOrchestrator
    from src.config import settings

    orch = EHSOrchestrator(fred_api_key=getattr(settings, "fred_api_key", ""))
    scores = orch.run_all()
    return [
        {**s.to_dict(), "cycle_label": CYCLE_LABELS.get(s.cycle_phase, s.cycle_phase)}
        for s in scores
    ]


def _compute_single(economy_code: str):
    from src.engines.ehs.orchestrator import EHSOrchestrator
    from src.config import settings

    orch = EHSOrchestrator(fred_api_key=getattr(settings, "fred_api_key", ""))
    score = orch.run_single(economy_code)
    if score:
        return {**score.to_dict(), "cycle_label": CYCLE_LABELS.get(score.cycle_phase, score.cycle_phase)}
    return None
