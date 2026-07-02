"""
GFCRI Historical Backtest

Simulates the GFCRI risk index across major financial crises using real
market data from yfinance to validate whether the index correctly flags
crisis periods.

Crises tested:
  1. 1997-98 Asian Financial Crisis
  2. 2000-01 Dot-com Bust
  3. 2008-09 Global Financial Crisis (GFC)
  4. 2011    European Debt Crisis
  5. 2015-16 China Devaluation + Oil Crash
  6. 2018 Q4 Fed Tightening Tantrum
  7. 2020    COVID-19 Crash
  8. 2022    Fed Hiking Cycle + Crypto Winter
  9. 2025-26 Current Period (baseline)
"""

import sys
import json
from datetime import date, timedelta

import numpy as np
import pandas as pd
import yfinance as yf

TICKERS = {
    "dxy": "DX-Y.NYB",
    "ust_10y": "^TNX",
    "ust_2y": "^IRX",
    "vix": "^VIX",
    "kospi": "^KS11",
    "sox": "^SOX",
    "oil_wti": "CL=F",
    "krw_usd": "KRW=X",
}

CRISES = [
    {"name": "亚洲金融危机", "peak": "1998-01-12", "window": ("1997-06-01", "1998-12-31"),
     "description": "泰铢崩盘→韩元暴跌→KOSPI腰斩→IMF救助"},
    {"name": "互联网泡沫破裂", "peak": "2002-10-09", "window": ("2000-03-01", "2003-03-31"),
     "description": "纳斯达克崩盘→科技股全线暴跌→半导体寒冬"},
    {"name": "全球金融危机(GFC)", "peak": "2008-10-27", "window": ("2007-07-01", "2009-06-30"),
     "description": "次贷危机→雷曼倒闭→全球信贷冻结→VIX飙至80"},
    {"name": "欧债危机", "peak": "2011-09-22", "window": ("2011-06-01", "2012-06-30"),
     "description": "希腊/意大利主权债务→全球避险→美元走强→EM承压"},
    {"name": "中国汇率贬值+油价暴跌", "peak": "2016-01-20", "window": ("2015-06-01", "2016-06-30"),
     "description": "人民币意外贬值→新兴市场恐慌→油价跌破$30"},
    {"name": "Fed缩表恐慌(Q4 2018)", "peak": "2018-12-24", "window": ("2018-09-01", "2019-03-31"),
     "description": "美联储加息缩表→美股圣诞大跌→韩元暴跌"},
    {"name": "COVID-19市场崩盘", "peak": "2020-03-23", "window": ("2020-01-01", "2020-12-31"),
     "description": "全球停摆→VIX飙至82→美股熔断4次→韩元暴跌"},
    {"name": "Fed激进加息周期", "peak": "2022-10-13", "window": ("2022-01-01", "2023-03-31"),
     "description": "通胀失控→美联储加息425bp→美元飙升→全球股债双杀"},
    {"name": "当前时期(基准)", "peak": "2026-06-28", "window": ("2025-06-01", "2026-06-28"),
     "description": "正常对照期——验证非危机时期指数应保持低位"},
]

SUB_INDEX_CONFIG = {
    "SI_RATES": {"nodes": ["ust_10y", "ust_2y"], "weight": 0.25},
    "SI_FX": {"nodes": ["dxy", "krw_usd"], "weight": 0.20},
    "SI_EQUITY": {"nodes": ["kospi", "sox"], "weight": 0.20},
    "SI_CREDIT": {"weight": 0.15, "nodes": []},
    "SI_SENTIMENT": {"nodes": ["vix"], "weight": 0.20},
}

RISK_CHAINS = [
    {"id": "fed_cascade", "path": ["ust_10y", "dxy", "krw_usd"]},
    {"id": "dollar_squeeze", "path": ["dxy", "krw_usd", "kospi"]},
    {"id": "credit_deteri", "path": ["ust_10y", "kospi"]},
    {"id": "ai_semi_cycle", "path": ["kospi", "sox"]},
    {"id": "vol_contagion", "path": ["vix", "krw_usd"]},
]


def fetch_all_data():
    print("Downloading historical data from yfinance...")
    tickers_str = " ".join(TICKERS.values())
    raw = yf.download(tickers_str, start="1996-01-01", end="2026-07-01",
                      interval="1d", auto_adjust=True, progress=False, threads=True)
    close = raw["Close"] if "Close" in raw.columns else raw

    df = pd.DataFrame()
    for node_id, ticker in TICKERS.items():
        if ticker in close.columns:
            df[node_id] = close[ticker]

    df = df.ffill().dropna(how="all")
    print(f"Data loaded: {len(df)} rows, {len(df.columns)} columns")
    print(f"Date range: {df.index[0].date()} ~ {df.index[-1].date()}")
    print(f"Columns: {list(df.columns)}")
    return df


def compute_gfcri_for_date(df, target_date, lookback=252):
    idx = df.index.get_indexer([pd.Timestamp(target_date)], method="ffill")[0]
    if idx < lookback:
        return None

    window = df.iloc[idx - lookback:idx]
    current = df.iloc[idx]

    zscores = {}
    anomaly_scores = {}
    for col in df.columns:
        if col in window.columns and window[col].notna().sum() >= 20:
            mean = window[col].mean()
            std = window[col].std()
            if std > 0:
                z = (current[col] - mean) / std
                zscores[col] = z
                anomaly_scores[col] = min(1.0, abs(z) / 4.0)

    sub_indices = {}
    for si_id, config in SUB_INDEX_CONFIG.items():
        nodes = config["nodes"]
        scores = [anomaly_scores.get(n, 0) for n in nodes if n in anomaly_scores]
        mean_stress = sum(scores) / len(scores) if scores else 0
        si_score = 100 * (0.7 * mean_stress + 0.3 * 0)
        sub_indices[si_id] = min(100, si_score)

    gfcri_base = sum(
        sub_indices.get(si_id, 0) * config["weight"]
        for si_id, config in SUB_INDEX_CONFIG.items()
    )

    chain_stresses = []
    for chain in RISK_CHAINS:
        path = chain["path"]
        scores = [anomaly_scores.get(n, 0) for n in path if n in anomaly_scores]
        stress = 100 * sum(scores) / len(scores) if scores else 0
        chain_stresses.append(stress)

    active_count = sum(1 for s in chain_stresses if s > 40)
    coherence = 1.0 + 0.05 * max(0, active_count - 1)
    gfcri = min(100, gfcri_base * coherence)

    alert = "red" if gfcri >= 75 else "orange" if gfcri >= 50 else "yellow" if gfcri >= 25 else "green"

    return {
        "gfcri": round(gfcri, 1),
        "alert": alert,
        "sub_indices": {k: round(v, 1) for k, v in sub_indices.items()},
        "zscores": {k: round(v, 2) for k, v in zscores.items()},
        "active_chains": active_count,
        "coherence": round(coherence, 2),
    }


def compute_gfcri_timeseries(df, start, end, step_days=5):
    results = []
    current = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    while current <= end_ts:
        r = compute_gfcri_for_date(df, current)
        if r:
            results.append({"date": current.strftime("%Y-%m-%d"), **r})
        current += timedelta(days=step_days)
    return results


def main():
    df = fetch_all_data()

    print("\n" + "=" * 100)
    print("GFCRI 历史回测 — 主要金融危机模拟分析")
    print("=" * 100)

    all_results = {}

    for crisis in CRISES:
        name = crisis["name"]
        peak = crisis["peak"]
        w_start, w_end = crisis["window"]

        print(f"\n{'─' * 80}")
        print(f"📌 {name}")
        print(f"   时间窗口: {w_start} ~ {w_end} | 危机峰值: {peak}")
        print(f"   描述: {crisis['description']}")
        print(f"{'─' * 80}")

        peak_result = compute_gfcri_for_date(df, peak)
        if peak_result is None:
            print(f"   ⚠️ 数据不足，跳过")
            continue

        alert_emoji = {"green": "🟢", "yellow": "🟡", "orange": "🟠", "red": "🔴"}
        ae = alert_emoji.get(peak_result["alert"], "")

        print(f"\n   危机峰值日 GFCRI: {peak_result['gfcri']}/100  {ae} {peak_result['alert'].upper()}")
        print(f"   活跃传导链: {peak_result['active_chains']} 条 | 相干性乘数: {peak_result['coherence']}")

        print(f"\n   子指数:")
        si_names = {"SI_RATES": "利率", "SI_FX": "汇率", "SI_EQUITY": "股市",
                    "SI_CREDIT": "信用", "SI_SENTIMENT": "情绪"}
        for si_id, score in peak_result["sub_indices"].items():
            bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
            print(f"     {si_names.get(si_id, si_id):>4}: {score:5.1f}/100  {bar}")

        print(f"\n   关键指标 Z-Score (峰值日):")
        z_names = {"dxy": "美元指数", "ust_10y": "10年美债", "ust_2y": "2年美债",
                   "vix": "VIX恐慌", "kospi": "KOSPI", "sox": "半导体SOX",
                   "oil_wti": "原油WTI", "krw_usd": "韩元/美元"}
        for nid, z in sorted(peak_result["zscores"].items(), key=lambda x: abs(x[1]), reverse=True):
            label = z_names.get(nid, nid)
            marker = " ⚠️ 异常" if abs(z) > 2 else ""
            print(f"     {label:>12}: {z:+6.2f}{marker}")

        ts = compute_gfcri_timeseries(df, w_start, w_end, step_days=10)
        if ts:
            gfcri_values = [t["gfcri"] for t in ts]
            max_gfcri = max(gfcri_values)
            max_date = ts[gfcri_values.index(max_gfcri)]["date"]
            min_gfcri = min(gfcri_values)
            avg_gfcri = sum(gfcri_values) / len(gfcri_values)

            red_days = sum(1 for v in gfcri_values if v >= 75)
            orange_days = sum(1 for v in gfcri_values if 50 <= v < 75)
            yellow_days = sum(1 for v in gfcri_values if 25 <= v < 50)
            green_days = sum(1 for v in gfcri_values if v < 25)

            print(f"\n   时序统计 ({len(ts)} 个采样点):")
            print(f"     最高 GFCRI: {max_gfcri:.1f} ({max_date})")
            print(f"     最低 GFCRI: {min_gfcri:.1f}")
            print(f"     平均 GFCRI: {avg_gfcri:.1f}")
            print(f"     🔴 危险: {red_days}次 | 🟠 警惕: {orange_days}次 | 🟡 关注: {yellow_days}次 | 🟢 平静: {green_days}次")

            all_results[name] = {
                "peak_gfcri": peak_result["gfcri"],
                "max_gfcri": max_gfcri,
                "max_date": max_date,
                "avg_gfcri": avg_gfcri,
                "peak_alert": peak_result["alert"],
                "red_pct": red_days / len(ts) * 100 if ts else 0,
            }

    # Summary table
    print(f"\n\n{'=' * 100}")
    print("汇总对比表")
    print(f"{'=' * 100}")
    print(f"\n{'危机事件':<25} {'峰值日GFCRI':>10} {'窗口最高':>8} {'窗口均值':>8} {'预警级别':>8} {'红色占比':>8}")
    print("─" * 75)

    for name, r in all_results.items():
        ae = alert_emoji.get(r["peak_alert"], "")
        print(f"{name:<24} {r['peak_gfcri']:>9.1f} {r['max_gfcri']:>8.1f} "
              f"{r['avg_gfcri']:>8.1f} {ae:>6} {r['red_pct']:>7.1f}%")

    print(f"\n{'=' * 100}")
    print("验证标准:")
    print("  ✅ 2008 GFC / 2020 COVID 应触发 🔴 红色预警 (GFCRI > 75)")
    print("  ✅ 1997/2011/2022 应至少触发 🟠 橙色预警 (GFCRI > 50)")
    print("  ✅ 2025-26 当前时期应为 🟢 绿色 (GFCRI < 25)")
    print("  ✅ 危机期间 GFCRI 应显著高于非危机期间")
    print(f"{'=' * 100}")


if __name__ == "__main__":
    main()
