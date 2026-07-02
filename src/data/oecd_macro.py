"""
OECD macroeconomic data collector.

Fetches long-term and short-term interest rates for OECD member countries.
Free API, no key required.

Note: CPI/unemployment dataflows require complex dimension matching.
Interest rates via STES DF_FINMARK are confirmed working.
"""

from __future__ import annotations

from io import StringIO
from typing import Optional

import pandas as pd
import requests
from loguru import logger

_BASE = "https://sdmx.oecd.org/public/rest/data"
_HEADERS = {"User-Agent": "GFCRI/1.0"}

OECD_COUNTRY_MAP = {
    "JP": "JPN", "GB": "GBR", "DE": "DEU", "FR": "FRA", "IT": "ITA",
    "CA": "CAN", "AU": "AUS", "KR": "KOR", "MX": "MEX", "TR": "TUR",
    "BR": "BRA", "EU": "EA20",
}


def fetch_oecd_rates() -> dict[str, dict[str, float]]:
    countries_str = "+".join(OECD_COUNTRY_MAP.values())
    results: dict[str, dict[str, float]] = {}

    queries = {
        "long_rate": f"{_BASE}/OECD.SDD.STES,DSD_STES@DF_FINMARK,4.0/{countries_str}.M.IRLT.PA.....?startPeriod=2025-01&format=csvfilewithlabels",
        "short_rate": f"{_BASE}/OECD.SDD.STES,DSD_STES@DF_FINMARK,4.0/{countries_str}.M.IRSTCI.PA.....?startPeriod=2025-01&format=csvfilewithlabels",
    }

    iso3_to_iso2 = {v: k for k, v in OECD_COUNTRY_MAP.items()}

    for indicator, url in queries.items():
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=20)
            if resp.status_code != 200:
                continue
            df = pd.read_csv(StringIO(resp.text))
            if "OBS_VALUE" not in df.columns or "REF_AREA" not in df.columns:
                continue
            latest = df.groupby("REF_AREA")["OBS_VALUE"].last()
            for iso3, val in latest.items():
                iso2 = iso3_to_iso2.get(str(iso3))
                if iso2:
                    if iso2 not in results:
                        results[iso2] = {}
                    results[iso2][f"oecd_{indicator}"] = float(val)
        except Exception as e:
            logger.debug(f"OECD {indicator} fetch failed: {e}")

    total = sum(len(v) for v in results.values())
    logger.info(f"OECD rates: {len(results)} countries, {total} data points")
    return results


OECD_INDICATOR_LABELS = {
    "oecd_long_rate": "长期利率(%)",
    "oecd_short_rate": "短期利率(%)",
}
