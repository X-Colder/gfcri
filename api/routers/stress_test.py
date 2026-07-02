import os
import json
import time
import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.dependencies import get_graph, get_historical_data

router = APIRouter(prefix="/stress-test", tags=["stress-test"])

_cache: dict = {"results": [], "ts": 0}
_compute_lock = asyncio.Lock()
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/app/output")


class CustomShock(BaseModel):
    name: str = "自定义场景"
    description: str = ""
    shocks: dict[str, float]


@router.get("/scenarios")
def list_scenarios():
    from src.engines.stress_test import PREDEFINED_SCENARIOS
    return [
        {"name": s.name, "description": s.description, "shocks": s.shocks}
        for s in PREDEFINED_SCENARIOS
    ]


@router.get("/run-all")
async def run_all():
    # 1. Try pre-computed cache file (instant, written by daily_job)
    cache_file = os.path.join(OUTPUT_DIR, "stress_test_cache.json")
    if os.path.exists(cache_file):
        try:
            mtime = os.path.getmtime(cache_file)
            if time.time() - mtime < 86400:  # valid for 24h
                with open(cache_file) as f:
                    return json.load(f)
        except Exception:
            pass

    # 2. Try in-memory cache (1h TTL)
    now = time.time()
    if _cache["results"] and (now - _cache["ts"]) < 3600:
        return _cache["results"]

    # 3. Compute on-demand (slow fallback). Single-flight avoids duplicate
    # market-data downloads if users refresh while the first request is running.
    async with _compute_lock:
        cached = _read_file_cache(cache_file)
        if cached is not None:
            return cached
        now = time.time()
        if _cache["results"] and (now - _cache["ts"]) < 3600:
            return _cache["results"]

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, _compute_all)
        _cache["results"] = results
        _cache["ts"] = time.time()
        _write_file_cache(cache_file, results)
        return results


@router.post("/run-custom")
async def run_custom(shock: CustomShock):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _compute_custom, shock)
    return result


def _compute_all():
    from src.engines.stress_test import StressTestEngine
    from src.engines.crisis_distance import CrisisDistanceEngine
    from src.data.collector import MarketDataCollector

    graph = get_graph()
    collector = MarketDataCollector()
    collector.update_node_values(graph)
    hist = get_historical_data()

    extra = {}
    extra.update(getattr(collector, '_fred_current', {}))
    try:
        from src.data.china_macro import fetch_china_macro
        extra.update(fetch_china_macro())
    except Exception:
        pass

    crisis_engine = CrisisDistanceEngine(graph, extra)
    baseline_crisis = crisis_engine.compute()

    engine = StressTestEngine(graph, hist)
    results = []
    for scenario_result in engine.run_all_scenarios():
        result_dict = scenario_result.to_dict()
        result_dict["baseline_crisis_distance"] = baseline_crisis.to_dict()
        results.append(result_dict)

    return results


def _read_file_cache(cache_file: str):
    if os.path.exists(cache_file):
        try:
            mtime = os.path.getmtime(cache_file)
            if time.time() - mtime < 86400:
                with open(cache_file) as f:
                    return json.load(f)
        except Exception:
            return None
    return None


def _write_file_cache(cache_file: str, results: list[dict]):
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(results, f)
    except Exception:
        pass


def _compute_custom(shock: CustomShock):
    from src.engines.stress_test import StressTestEngine, ShockScenario
    graph = get_graph()
    hist = get_historical_data()
    engine = StressTestEngine(graph, hist)
    scenario = ShockScenario(name=shock.name, description=shock.description, shocks=shock.shocks)
    result = engine.run_scenario(scenario)
    return result.to_dict()
