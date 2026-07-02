import time
import asyncio

from fastapi import APIRouter, Query, HTTPException

from src.engines.industry import INDUSTRIES, INDUSTRY_CATEGORIES
from src.engines.industry.supply_chain import SupplyChainNetwork

router = APIRouter(prefix="/industry", tags=["industry"])

_cache: dict = {"scores": [], "ts": 0}
_CACHE_TTL = 21600
_network = SupplyChainNetwork()


@router.get("/categories")
def list_categories():
    return INDUSTRY_CATEGORIES


@router.get("/list")
def list_industries(category: str = Query(default=None)):
    results = []
    for code, ind in INDUSTRIES.items():
        if category and ind.category != category:
            continue
        results.append({
            "code": code,
            "name_zh": ind.name_zh,
            "name_en": ind.name_en,
            "category": ind.category,
            "key_economies": ind.key_economies,
            "upstream": ind.upstream,
            "downstream": ind.downstream,
        })
    return results


@router.get("/scores")
async def get_scores(refresh: bool = Query(default=False)):
    now = time.time()
    if not refresh and _cache["scores"] and (now - _cache["ts"]) < _CACHE_TTL:
        return _cache["scores"]

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, _compute_scores)
    _cache["scores"] = results
    _cache["ts"] = time.time()
    return results


@router.get("/scores/{industry_code}")
async def get_industry_score(industry_code: str):
    if industry_code not in INDUSTRIES:
        raise HTTPException(404, f"Unknown industry: {industry_code}")

    now = time.time()
    if _cache["scores"] and (now - _cache["ts"]) < _CACHE_TTL:
        for s in _cache["scores"]:
            if s["code"] == industry_code:
                return s
    raise HTTPException(404, "Score not cached, call /scores?refresh=true first")


@router.get("/supply-chain/graph")
def get_supply_chain_graph():
    return _network.get_full_graph()


@router.get("/supply-chain/{industry_code}")
def get_supply_chain(industry_code: str, direction: str = Query(default="both")):
    if industry_code not in INDUSTRIES:
        raise HTTPException(404, f"Unknown industry: {industry_code}")

    result = {
        "industry": industry_code,
        "name_zh": INDUSTRIES[industry_code].name_zh,
    }

    if direction in ("upstream", "both"):
        result["upstream"] = _network.get_upstream(industry_code)
    if direction in ("downstream", "both"):
        result["downstream"] = _network.get_downstream(industry_code)
    if direction in ("downstream", "both"):
        result["impact_paths"] = [
            {"path": p.path_names, "depth": p.depth}
            for p in _network.trace_impact(industry_code, "downstream", max_depth=3)
        ]

    return result


def _compute_scores():
    from src.engines.industry.scoring import IndustryScoringEngine
    engine = IndustryScoringEngine()
    scores = engine.score_all()
    return [s.to_dict() for s in scores]
