"""
China macroeconomic data collector via AKShare.

Fetches real economic indicators from China's National Bureau of Statistics.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
from loguru import logger


def fetch_china_macro() -> dict[str, float]:
    try:
        import akshare as ak
    except ImportError:
        logger.warning("akshare not installed, skipping China macro data")
        return {}

    result = {}

    # PMI
    try:
        df = ak.macro_china_pmi()
        if not df.empty:
            latest = df.iloc[0]
            result["cn_pmi"] = float(latest.get("制造业-指数", 0))
            result["cn_pmi_date"] = str(latest.get("月份", ""))
    except Exception as e:
        logger.debug(f"AKShare PMI failed: {e}")

    # CPI
    try:
        df = ak.macro_china_cpi()
        if not df.empty:
            latest = df.iloc[0]
            result["cn_cpi_yoy"] = float(latest.get("全国-同比增长", 0))
    except Exception as e:
        logger.debug(f"AKShare CPI failed: {e}")

    # PPI
    try:
        df = ak.macro_china_ppi()
        if not df.empty:
            latest = df.iloc[0]
            result["cn_ppi_yoy"] = float(latest.get("当月同比增长", 0))
    except Exception as e:
        logger.debug(f"AKShare PPI failed: {e}")

    # M2
    try:
        df = ak.macro_china_money_supply()
        if not df.empty:
            latest = df.iloc[0]
            result["cn_m2_yoy"] = float(latest.get("货币和准货币(M2)-同比增长", 0))
            result["cn_m1_yoy"] = float(latest.get("货币(M1)-同比增长", 0))
    except Exception as e:
        logger.debug(f"AKShare M2 failed: {e}")

    # Social financing
    try:
        df = ak.macro_china_new_financial_credit()
        if not df.empty:
            latest = df.iloc[0]
            result["cn_social_finance"] = float(latest.get("当月", 0))
            result["cn_social_finance_yoy"] = float(latest.get("当月-同比增长", 0))
    except Exception as e:
        logger.debug(f"AKShare social finance failed: {e}")

    # Retail sales
    try:
        df = ak.macro_china_consumer_goods_retail()
        if not df.empty:
            latest = df.iloc[0]
            result["cn_retail_yoy"] = float(latest.get("同比增长", 0))
    except Exception as e:
        logger.debug(f"AKShare retail failed: {e}")

    # LPR
    try:
        df = ak.macro_china_lpr()
        if not df.empty:
            lpr1y = df["LPR1Y"].dropna()
            lpr5y = df["LPR5Y"].dropna()
            if not lpr1y.empty:
                result["cn_lpr_1y"] = float(lpr1y.iloc[-1])
            if not lpr5y.empty:
                result["cn_lpr_5y"] = float(lpr5y.iloc[-1])
    except Exception as e:
        logger.debug(f"AKShare LPR failed: {e}")

    logger.info(f"AKShare China macro: fetched {len(result)} indicators")
    return result


CHINA_INDICATOR_LABELS = {
    "cn_pmi": "制造业PMI",
    "cn_cpi_yoy": "CPI同比(%)",
    "cn_ppi_yoy": "PPI同比(%)",
    "cn_m2_yoy": "M2同比增速(%)",
    "cn_m1_yoy": "M1同比增速(%)",
    "cn_social_finance": "社融当月(亿元)",
    "cn_social_finance_yoy": "社融同比增长(%)",
    "cn_retail_yoy": "社零同比增长(%)",
    "cn_lpr_1y": "1年期LPR(%)",
    "cn_lpr_5y": "5年期LPR(%)",
}
