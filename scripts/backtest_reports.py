"""Backtest script: generate daily reports for Mon-Fri last week and push to WeChat drafts."""
import os, time
from datetime import date
import pandas as pd
import yfinance as yf
from loguru import logger

from src.models.graph import build_initial_causal_graph
from src.engines.risk_index import GFCRIEngine
from src.engines.orchestrator import LLMCausalOrchestrator
from src.engines.risk_monitor import RiskMonitor
from src.engines.social_content import generate_wechat_html
from src.engines.report_generator import get_upcoming_events
from src.publishers.wechat import WechatPublisher, _thumb_cache
from src.config import settings
from src.data.collector import MarketDataCollector, YFINANCE_TICKER_MAP, PROXY_TICKER_MAP
from src.engines.reasoning import CausalReasoningEngine
from src.engines.discovery import CausalDiscoveryEngine

_thumb_cache['media_id'] = 'uiA3-Av38Ejoh0esEKLa4J8UR-SviM6Mk0Vzg4BEK3H_RkiC8B-QLvAGAMw18V_T'
publisher = WechatPublisher(settings)
collector = MarketDataCollector()

# Download 1 month of data
all_tickers = list(YFINANCE_TICKER_MAP.values()) + [v['ticker'] for v in PROXY_TICKER_MAP.values()]
print(f'Downloading {len(all_tickers)} tickers...')
raw_data = yf.download(all_tickers, period='1mo', progress=False, auto_adjust=True)
print(f'Downloaded: {raw_data.shape}')

hist_data = collector.fetch_historical_data(period='2y')

target_dates = ['2026-06-23', '2026-06-24', '2026-06-25', '2026-06-26', '2026-06-27']
prev_result = None

for target_date in target_dates:
    print(f'\n=== {target_date} ===')
    target_ts = pd.Timestamp(target_date)

    graph = build_initial_causal_graph()

    # Update nodes with that day's data
    for nid, ticker in YFINANCE_TICKER_MAP.items():
        try:
            if isinstance(raw_data.columns, pd.MultiIndex):
                cs = raw_data[('Close', ticker)].dropna()
            else:
                continue
            available = cs[cs.index <= target_ts]
            if available.empty:
                continue
            val = float(available.iloc[-1])
            node = graph.nodes.get(nid)
            if node:
                node.current_value = val
                last20 = cs.iloc[max(0, len(available)-20):len(available)]
                if len(last20) >= 5:
                    mean, std = last20.mean(), last20.std()
                    if std > 0:
                        node.value_zscore = (val - mean) / std
                        node.is_anomalous = abs(node.value_zscore) > 2.0
                        node.anomaly_score = min(1.0, abs(node.value_zscore) / 4.0)
                        node.historical_mean = mean
                        node.historical_std = std
        except Exception:
            pass

    for nid, proxy in PROXY_TICKER_MAP.items():
        try:
            ticker = proxy['ticker']
            if isinstance(raw_data.columns, pd.MultiIndex):
                cs = raw_data[('Close', ticker)].dropna()
            else:
                continue
            available = cs[cs.index <= target_ts]
            if available.empty:
                continue
            val = float(available.iloc[-1])
            node = graph.nodes.get(nid)
            if node:
                node.current_value = val
                last20 = cs.iloc[max(0, len(available)-20):len(available)]
                if len(last20) >= 5:
                    mean, std = last20.mean(), last20.std()
                    if std > 0:
                        z = (val - mean) / std
                        if proxy.get('invert'):
                            z = -z
                        node.value_zscore = z
                        node.is_anomalous = abs(z) > 2.0
                        node.anomaly_score = min(1.0, abs(z) / 4.0)
        except Exception:
            pass

    engine = GFCRIEngine(graph)
    result = engine.compute()
    gfcri = result['gfcri']

    monitor = RiskMonitor(graph=graph, gfcri_result=result)
    alerts = [a.to_dict() for a in monitor.run_all_checks()]

    # Generate narrative
    try:
        reasoning = CausalReasoningEngine(graph, hist_data)
        discovery = CausalDiscoveryEngine(graph, hist_data)
        orchestrator = LLMCausalOrchestrator(graph, reasoning, discovery)
        narrative = orchestrator.generate_gfcri_report(
            gfcri_result=result,
            inference_summary={},
            upcoming_events=get_upcoming_events(days=7),
            prev_gfcri_result=prev_result,
        )
        print(f'  Narrative: {len(narrative)} chars')
    except Exception as e:
        narrative = ''
        print(f'  Narrative FAILED: {e}')

    prev_val = prev_result['gfcri'] if prev_result else None
    html = generate_wechat_html(result, alerts=alerts, llm_narrative=narrative, report_date=target_date, prev_gfcri=prev_val)

    title = f'GFCRI 风险日报 | {target_date}'
    draft_id = publisher.publish_article(title=title, content=html)
    print(f'  GFCRI={gfcri:.1f}, Draft={draft_id}')

    prev_result = result
    time.sleep(2)

print('\n=== DONE ===')
