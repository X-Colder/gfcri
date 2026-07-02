import json
import os
import threading
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Query, HTTPException

from src.engines.industry import INDUSTRIES, INDUSTRY_CATEGORIES
from src.engines.industry.supply_chain import SupplyChainNetwork

router = APIRouter(prefix="/industry", tags=["industry"])

_cache: dict = {"scores": [], "ts": 0, "updated_at": None, "source": "empty"}
_CACHE_TTL = 21600
_refresh_lock = threading.Lock()
_refreshing = False
_OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/app/output")
_CACHE_FILE = os.path.join(_OUTPUT_DIR, "industry_scores_cache.json")
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
def get_scores(refresh: bool = Query(default=False)):
    _load_snapshot_once()
    now = time.time()
    has_fresh_cache = _cache["scores"] and (now - _cache["ts"]) < _CACHE_TTL

    if refresh:
        _start_refresh()
    elif not has_fresh_cache:
        _start_refresh()

    if not _cache["scores"]:
        _cache.update({
            "scores": _baseline_scores(),
            "ts": 0,
            "updated_at": None,
            "source": "baseline",
        })

    return _scores_payload()


@router.get("/scores/{industry_code}")
async def get_industry_score(industry_code: str):
    if industry_code not in INDUSTRIES:
        raise HTTPException(404, f"Unknown industry: {industry_code}")

    _load_snapshot_once()
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


def _scores_payload() -> dict:
    now = time.time()
    return {
        "scores": _cache["scores"],
        "updated_at": _cache.get("updated_at"),
        "stale": not _cache.get("ts") or (now - _cache["ts"]) >= _CACHE_TTL,
        "refreshing": _refreshing,
        "source": _cache.get("source", "memory"),
        "ttl_seconds": _CACHE_TTL,
    }


def _baseline_scores() -> list[dict]:
    return [
        {
            "code": code,
            "name_zh": ind.name_zh,
            "name_en": ind.name_en,
            "category": ind.category,
            "score": 50.0,
            "trend": "flat",
            "change_1m": 0.0,
            "change_3m": 0.0,
            "volatility": 0.0,
            "key_economies": ind.key_economies,
            "ticker_details": [
                {
                    "ticker": t.ticker,
                    "name": t.name_zh,
                    "role": t.role,
                    "price": "-",
                    "change_1m": 0.0,
                    "change_3m": 0.0,
                    "volatility": 0.0,
                    "momentum": 50.0,
                }
                for t in ind.tickers
            ],
        }
        for code, ind in INDUSTRIES.items()
    ]


def _load_snapshot_once():
    if _cache["scores"] or not os.path.exists(_CACHE_FILE):
        return
    try:
        with open(_CACHE_FILE, encoding="utf-8") as f:
            payload = json.load(f)
        scores = payload.get("scores") if isinstance(payload, dict) else None
        if scores:
            _cache.update({
                "scores": scores,
                "ts": float(payload.get("ts") or 0),
                "updated_at": payload.get("updated_at"),
                "source": "snapshot",
            })
    except Exception:
        pass


def _start_refresh():
    global _refreshing
    with _refresh_lock:
        if _refreshing:
            return
        _refreshing = True
    thread = threading.Thread(target=_refresh_scores, name="industry-score-refresh", daemon=True)
    thread.start()


def _refresh_scores():
    global _refreshing
    try:
        results = _compute_scores()
        if not results:
            return
        ts = time.time()
        updated_at = datetime.now(timezone.utc).isoformat()
        _cache.update({
            "scores": results,
            "ts": ts,
            "updated_at": updated_at,
            "source": "live",
        })
        try:
            os.makedirs(_OUTPUT_DIR, exist_ok=True)
            with open(_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "scores": results,
                    "ts": ts,
                    "updated_at": updated_at,
                }, f)
        except Exception:
            pass
    finally:
        with _refresh_lock:
            _refreshing = False
