import os
import json
import time
import asyncio
from fastapi import APIRouter

from api.dependencies import get_graph

router = APIRouter(prefix="/crisis-distance", tags=["crisis-distance"])

_cache: dict = {"result": None, "ts": 0}
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/app/output")


@router.get("")
async def get_crisis_distance():
    # 1. Try pre-computed cache file (instant)
    cache_file = os.path.join(OUTPUT_DIR, "crisis_distance_cache.json")
    if os.path.exists(cache_file):
        try:
            mtime = os.path.getmtime(cache_file)
            if time.time() - mtime < 86400:
                with open(cache_file) as f:
                    return json.load(f)
        except Exception:
            pass

    # 2. Try in-memory cache (1h TTL)
    now = time.time()
    if _cache["result"] and (now - _cache["ts"]) < 3600:
        return _cache["result"]

    # 3. Compute on-demand (slow fallback)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _compute)
    _cache["result"] = result
    _cache["ts"] = time.time()
    return result


def _compute():
    from src.engines.crisis_distance import CrisisDistanceEngine
    from src.data.collector import MarketDataCollector

    graph = get_graph()
    collector = MarketDataCollector()
    collector.update_node_values(graph)

    extra = {}
    extra.update(getattr(collector, '_fred_current', {}))
    try:
        from src.data.china_macro import fetch_china_macro
        extra.update(fetch_china_macro())
    except Exception:
        pass

    engine = CrisisDistanceEngine(graph, extra)
    return engine.compute().to_dict()
