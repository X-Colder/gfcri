import time
from typing import Optional

import pandas as pd
from loguru import logger

from src.config import settings
from src.models.graph import MacroRiskCausalGraph, build_initial_causal_graph
from src.data.collector import MarketDataCollector
from src.engines.reasoning import CausalReasoningEngine


_graph: Optional[MacroRiskCausalGraph] = None
_historical_data: Optional[pd.DataFrame] = None
_historical_data_ts: float = 0
_CACHE_TTL = 3600


def init_cache():
    global _graph
    _graph = build_initial_causal_graph()
    logger.info(f"Graph cached: {_graph.node_count} nodes, {_graph.edge_count} edges")


def shutdown_cache():
    pass


def get_graph() -> MacroRiskCausalGraph:
    global _graph
    if _graph is None:
        _graph = build_initial_causal_graph()
    return _graph


def get_historical_data() -> pd.DataFrame:
    global _historical_data, _historical_data_ts
    now = time.time()
    if _historical_data is None or (now - _historical_data_ts) > _CACHE_TTL:
        logger.info("Fetching historical data from yfinance (cached for 1h)...")
        collector = MarketDataCollector()
        _historical_data = collector.fetch_historical_data(period="2y")
        _historical_data_ts = now
        logger.info(f"Historical data cached: {_historical_data.shape}")
    return _historical_data


def get_reasoning_engine() -> CausalReasoningEngine:
    graph = get_graph()
    data = get_historical_data()
    return CausalReasoningEngine(graph, data)
