"""
Lightweight alert checker — runs every 30 minutes.
Checks 5 core indicators for threshold breaches without full GFCRI recalculation.
Generates alert events that can trigger email/push notifications.
"""
import os
import json
import time
from datetime import datetime, date
from typing import Any

import yfinance as yf
from loguru import logger


CORE_TICKERS = {
    "vix": "^VIX",
    "spx": "^GSPC",
    "dxy": "DX-Y.NYB",
    "krw_usd": "KRW=X",
    "gold": "GC=F",
}

ALERT_THRESHOLDS = {
    "vix": {"warning": 25, "danger": 35, "direction": "high"},
    "spx_drop_pct": {"warning": -2.0, "danger": -4.0, "direction": "low"},
    "dxy": {"warning": 107, "danger": 112, "direction": "high"},
    "krw_usd": {"warning": 1450, "danger": 1550, "direction": "high"},
    "gold": {"warning": 3500, "danger": 4000, "direction": "high"},
}


def check_intraday_alerts() -> list[dict[str, Any]]:
    """Check core indicators and return triggered alerts."""
    alerts = []

    try:
        tickers_str = " ".join(CORE_TICKERS.values())
        raw = yf.download(tickers_str, period="2d", interval="1d", progress=False, auto_adjust=True)
        if raw.empty:
            return alerts

        close = raw["Close"] if "Close" in raw.columns else raw

        values = {}
        for nid, ticker in CORE_TICKERS.items():
            try:
                series = close[ticker].dropna()
                if not series.empty:
                    values[nid] = float(series.iloc[-1])
            except (KeyError, IndexError):
                pass

        # Check VIX
        vix = values.get("vix")
        if vix:
            if vix >= 35:
                alerts.append({"type": "danger", "title": f"VIX 恐慌指数飙升至 {vix:.1f}", "indicator": "vix", "value": vix})
            elif vix >= 25:
                alerts.append({"type": "warning", "title": f"VIX 恐慌指数升至 {vix:.1f}", "indicator": "vix", "value": vix})

        # Check KRW
        krw = values.get("krw_usd")
        if krw:
            if krw >= 1550:
                alerts.append({"type": "danger", "title": f"韩元贬至 {krw:.0f}，逼近2008崩盘水平", "indicator": "krw_usd", "value": krw})
            elif krw >= 1450:
                alerts.append({"type": "warning", "title": f"韩元承压至 {krw:.0f}", "indicator": "krw_usd", "value": krw})

        # Check DXY
        dxy = values.get("dxy")
        if dxy:
            if dxy >= 112:
                alerts.append({"type": "danger", "title": f"美元指数 {dxy:.1f}，强美元挤压全球", "indicator": "dxy", "value": dxy})
            elif dxy >= 107:
                alerts.append({"type": "warning", "title": f"美元指数偏强 {dxy:.1f}", "indicator": "dxy", "value": dxy})

        # Check Gold
        gold = values.get("gold")
        if gold:
            if gold >= 4000:
                alerts.append({"type": "warning", "title": f"黄金突破 ${gold:.0f}，避险需求强烈", "indicator": "gold", "value": gold})

        # Save latest values for frontend
        output_dir = os.environ.get("OUTPUT_DIR", "/app/output")
        os.makedirs(output_dir, exist_ok=True)
        intraday_data = {
            "values": values,
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat(),
            "date": date.today().isoformat(),
        }
        with open(os.path.join(output_dir, "intraday_check.json"), "w") as f:
            json.dump(intraday_data, f)

        if alerts:
            logger.info(f"Intraday check: {len(alerts)} alerts triggered")
        else:
            logger.info(f"Intraday check: all clear, VIX={vix:.1f}, KRW={krw:.0f}")

    except Exception as e:
        logger.warning(f"Intraday alert check failed: {e}")

    return alerts


if __name__ == "__main__":
    alerts = check_intraday_alerts()
    for a in alerts:
        print(f"  [{a['type']}] {a['title']}")
    if not alerts:
        print("  All clear.")
