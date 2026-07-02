"""Multi-crisis backtester — validates GFCRI model against historical crises.

Tests: 1992 ERM, 1994 Bond Massacre, 1997 Asian Crisis, 1998 LTCM,
       2000 Dotcom, 2008 GFC (v2), 2010 Euro Debt, 2015 China Crash,
       2018 Fed Tightening, 2020 COVID, 2022 Rate Shock.
"""
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import sys
import os

FRED_KEY = os.getenv("FRED_API_KEY", "")

# ═══════════════════════════════════════════════════════════
# Crisis definitions
# ═══════════════════════════════════════════════════════════

CRISES = [
    {
        "name": "1971 尼克松冲击（美元脱钩黄金）",
        "data_start": "1968-01-01", "data_end": "1974-12-31",
        "backtest_start": "1970-01-01", "backtest_end": "1972-12-31",
        "peak_event": "1971-08", "peak_desc": "美元与黄金脱钩",
        "events": [
            ("1970-06", "美国经济衰退开始"),
            ("1971-05", "西德马克浮动，美元危机"),
            ("1971-08", "尼克松关闭黄金窗口"),
            ("1971-12", "史密森协议，美元贬值8%"),
            ("1972-06", "英镑浮动"),
        ],
    },
    {
        "name": "1973 石油危机+股市崩盘",
        "data_start": "1970-01-01", "data_end": "1976-12-31",
        "backtest_start": "1973-01-01", "backtest_end": "1975-06-30",
        "peak_event": "1974-09", "peak_desc": "SPX见底，跌幅48%",
        "events": [
            ("1973-01", "股市见顶，通胀抬头"),
            ("1973-06", "水门事件升级"),
            ("1973-10", "OPEC石油禁运，油价翻4倍"),
            ("1974-03", "石油禁运解除但油价不降"),
            ("1974-08", "尼克松辞职"),
            ("1974-09", "SPX见底62.28，从高点跌48%"),
            ("1975-03", "经济开始复苏"),
        ],
    },
    {
        "name": "1980 沃尔克加息+大衰退",
        "data_start": "1978-01-01", "data_end": "1983-12-31",
        "backtest_start": "1980-01-01", "backtest_end": "1982-12-31",
        "peak_event": "1982-08", "peak_desc": "失业率10.8%，拉美债务危机",
        "events": [
            ("1980-01", "联邦基金利率升至14%"),
            ("1980-03", "利率达到20%历史纪录"),
            ("1980-06", "短暂衰退，利率暂降"),
            ("1981-01", "利率再升至19%"),
            ("1981-07", "经济二次探底"),
            ("1982-06", "失业率破10%"),
            ("1982-08", "墨西哥债务违约，拉美危机"),
            ("1982-10", "美联储转向宽松，股市反弹"),
        ],
    },
    {
        "name": "1987 黑色星期一",
        "data_start": "1985-01-01", "data_end": "1989-12-31",
        "backtest_start": "1987-01-01", "backtest_end": "1988-06-30",
        "peak_event": "1987-10", "peak_desc": "单日暴跌22.6%",
        "events": [
            ("1987-01", "股市狂热，道指年初至今涨44%"),
            ("1987-08", "道指见顶2722"),
            ("1987-10", "黑色星期一，单日暴跌22.6%"),
            ("1987-11", "美联储紧急注入流动性"),
            ("1988-01", "市场企稳，恢复上涨"),
        ],
    },
    {
        "name": "1992 ERM危机（索罗斯做空英镑）",
        "data_start": "1990-01-01", "data_end": "1994-12-31",
        "backtest_start": "1992-06-01", "backtest_end": "1993-06-30",
        "peak_event": "1992-09", "peak_desc": "黑色星期三，英镑崩盘",
        "events": [
            ("1992-06", "芬兰马克贬值，ERM压力初现"),
            ("1992-09", "黑色星期三，英镑退出ERM"),
            ("1992-11", "瑞典放弃固定汇率"),
            ("1993-01", "爱尔兰镑贬值10%"),
            ("1993-08", "ERM汇率波动带扩大到±15%"),
        ],
    },
    {
        "name": "1994 全球债市大屠杀",
        "data_start": "1992-01-01", "data_end": "1995-12-31",
        "backtest_start": "1994-01-01", "backtest_end": "1995-03-31",
        "peak_event": "1994-11", "peak_desc": "橙县破产，债券抛售高潮",
        "events": [
            ("1994-02", "美联储意外加息25bp"),
            ("1994-04", "美联储再加息，全球债市恐慌"),
            ("1994-06", "墨西哥政治暗杀，比索承压"),
            ("1994-11", "橙县因衍生品亏损破产"),
            ("1994-12", "墨西哥比索危机爆发"),
        ],
    },
    {
        "name": "1997 亚洲金融危机",
        "data_start": "1995-01-01", "data_end": "1999-12-31",
        "backtest_start": "1997-01-01", "backtest_end": "1998-12-31",
        "peak_event": "1998-01", "peak_desc": "韩元崩盘+印尼暴动",
        "events": [
            ("1997-07", "泰铢崩盘，亚洲危机起点"),
            ("1997-08", "马来西亚/印尼货币暴跌"),
            ("1997-10", "港股暴跌，全球传染"),
            ("1997-11", "韩元崩盘，IMF介入"),
            ("1998-01", "印尼暴动，危机顶峰"),
            ("1998-08", "俄罗斯违约→LTCM崩盘"),
            ("1998-10", "美联储紧急降息，恐慌顶点"),
        ],
    },
    {
        "name": "2000 互联网泡沫破裂",
        "data_start": "1998-01-01", "data_end": "2003-12-31",
        "backtest_start": "2000-01-01", "backtest_end": "2002-12-31",
        "peak_event": "2002-10", "peak_desc": "SPX见底，WorldCom破产后",
        "events": [
            ("2000-03", "纳斯达克见顶5048"),
            ("2000-04", "科技股闪崩，纳斯达克单周跌25%"),
            ("2000-12", "纳斯达克已从高点跌50%"),
            ("2001-03", "美国经济正式衰退"),
            ("2001-09", "911恐怖袭击"),
            ("2001-12", "安然破产"),
            ("2002-06", "WorldCom会计丑闻"),
            ("2002-10", "SPX见底777"),
        ],
    },
    {
        "name": "2010 欧洲主权债务危机",
        "data_start": "2008-01-01", "data_end": "2013-12-31",
        "backtest_start": "2010-01-01", "backtest_end": "2012-12-31",
        "peak_event": "2011-11", "peak_desc": "意大利10Y突破7%",
        "events": [
            ("2010-04", "希腊正式求助EU/IMF"),
            ("2010-05", "欧盟7500亿救助机制"),
            ("2010-11", "爱尔兰银行危机"),
            ("2011-07", "意大利/西班牙国债利率飙升"),
            ("2011-08", "美国信用评级下调，全球暴跌"),
            ("2011-11", "意大利10Y突破7%，贝卢斯科尼下台"),
            ("2012-06", "西班牙银行求助"),
            ("2012-07", "德拉吉：Whatever it takes"),
        ],
    },
    {
        "name": "2015 中国股灾+人民币贬值",
        "data_start": "2013-01-01", "data_end": "2016-12-31",
        "backtest_start": "2015-06-01", "backtest_end": "2016-06-30",
        "peak_event": "2016-01", "peak_desc": "熔断机制触发，全球恐慌",
        "events": [
            ("2015-06", "A股见顶5178后暴跌"),
            ("2015-07", "A股三周跌30%，千股跌停"),
            ("2015-08", "811汇改，人民币单日贬值2%，全球恐慌"),
            ("2015-09", "全球股市恐慌性抛售"),
            ("2016-01", "A股熔断，四天触发两次，全球暴跌"),
        ],
    },
    {
        "name": "2018 美联储加息+圣诞暴跌",
        "data_start": "2016-01-01", "data_end": "2019-12-31",
        "backtest_start": "2018-01-01", "backtest_end": "2019-03-31",
        "peak_event": "2018-12", "peak_desc": "圣诞前夕SPX暴跌",
        "events": [
            ("2018-02", "VIX暴涨到50+，闪崩事件"),
            ("2018-03", "中美贸易战开打"),
            ("2018-10", "美股暴跌，科技股领跌"),
            ("2018-12", "SPX进入熊市，圣诞前夕暴跌"),
            ("2019-01", "美联储转鸽，暂停加息"),
        ],
    },
    {
        "name": "2020 新冠疫情全球恐慌",
        "data_start": "2018-01-01", "data_end": "2021-12-31",
        "backtest_start": "2020-01-01", "backtest_end": "2020-12-31",
        "peak_event": "2020-03", "peak_desc": "全球熔断，VIX=82",
        "events": [
            ("2020-01", "武汉封城，市场初步反应"),
            ("2020-02", "疫情全球扩散，恐慌开始"),
            ("2020-03", "全球股市熔断，VIX=82，美联储零利率+无限QE"),
            ("2020-04", "油价跌至负值，但股市开始反弹"),
            ("2020-06", "V型反弹确认"),
        ],
    },
    {
        "name": "2022 美联储暴力加息周期",
        "data_start": "2020-01-01", "data_end": "2023-12-31",
        "backtest_start": "2022-01-01", "backtest_end": "2023-06-30",
        "peak_event": "2022-10", "peak_desc": "SPX见底3577",
        "events": [
            ("2022-01", "美联储释放加息信号，科技股大跌"),
            ("2022-03", "首次加息25bp"),
            ("2022-06", "加息75bp，四十年来最大幅度"),
            ("2022-09", "英国养老金危机"),
            ("2022-10", "SPX见底3577，DXY=114"),
            ("2022-11", "FTX崩盘"),
            ("2023-03", "硅谷银行倒闭"),
        ],
    },
]

# ═══════════════════════════════════════════════════════════
# Data fetching
# ═══════════════════════════════════════════════════════════

def fetch_fred(series_id, start, end):
    resp = requests.get("https://api.stlouisfed.org/fred/series/observations", params={
        "series_id": series_id, "api_key": FRED_KEY, "file_type": "json",
        "observation_start": start, "observation_end": end,
    }, timeout=15)
    obs = resp.json().get("observations", [])
    records = [(r["date"], float(r["value"])) for r in obs if r["value"] != "."]
    if not records:
        return pd.Series(dtype=float)
    df = pd.DataFrame(records, columns=["date", "value"])
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")["value"].resample("M").last().dropna()


def fetch_crisis_data(crisis):
    start, end = crisis["data_start"], crisis["data_end"]
    data = {}

    # yfinance
    tickers = {"vix": "^VIX", "spx": "^GSPC", "hsi": "^HSI", "nikkei": "^N225"}
    if pd.Timestamp(start) >= pd.Timestamp("1996-12-01"):
        tickers["kospi"] = "^KS11"
    if pd.Timestamp(start) >= pd.Timestamp("2000-08-01"):
        tickers["gold"] = "GC=F"
        tickers["oil_wti"] = "CL=F"
    if pd.Timestamp(start) >= pd.Timestamp("2003-04-01"):
        tickers["eem"] = "EEM"
    if pd.Timestamp(start) >= pd.Timestamp("2007-04-01"):
        tickers["hyg"] = "HYG"

    raw = yf.download(list(tickers.values()), start=start, end=end, progress=False, auto_adjust=True)
    for nid, ticker in tickers.items():
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                close = raw[("Close", ticker)].dropna()
            else:
                close = raw["Close"].dropna()
            data[nid] = close.resample("M").last().dropna()
        except:
            pass

    # FRED
    fred_series = {
        "baa_spread": "BAA10Y",
        "ted_spread": "TEDRATE",
        "t10y2y": "T10Y2Y",
        "ust_10y": "GS10",
    }
    for nid, sid in fred_series.items():
        s = fetch_fred(sid, start, end)
        if not s.empty:
            data[nid] = s

    # BAA-AAA spread
    baa = fetch_fred("DBAA", start, end)
    aaa = fetch_fred("DAAA", start, end)
    if not baa.empty and not aaa.empty:
        baa_aaa = (baa - aaa).dropna()
        if not baa_aaa.empty:
            data["baa_aaa_spread"] = baa_aaa

    # DXY (from yfinance, available from 1971)
    try:
        dxy = yf.download("DX-Y.NYB", start=start, end=end, progress=False, auto_adjust=True)
        if not dxy.empty:
            if isinstance(dxy.columns, pd.MultiIndex):
                data["dxy"] = dxy[("Close", "DX-Y.NYB")].dropna().resample("M").last().dropna()
            else:
                data["dxy"] = dxy["Close"].dropna().resample("M").last().dropna()
    except:
        pass

    return data


# ═══════════════════════════════════════════════════════════
# GFCRI scoring (same dual-track as v2)
# ═══════════════════════════════════════════════════════════

# Indicators where higher = more dangerous
HIGH_IS_DANGER = {"vix", "baa_spread", "baa_aaa_spread", "ted_spread", "ust_10y", "dxy", "oil_wti", "unrate"}
# Indicators where lower = more dangerous
LOW_IS_DANGER = {"spx", "hsi", "nikkei", "kospi", "eem", "hyg", "t10y2y"}

Z_WEIGHT, ABS_WEIGHT = 0.5, 0.5

BASE_WEIGHTS = {
    "vix": 0.22, "spx": 0.18, "baa_spread": 0.12, "baa_aaa_spread": 0.08,
    "ted_spread": 0.08, "t10y2y": 0.05, "gold": 0.04, "oil_wti": 0.04,
    "eem": 0.04, "hsi": 0.04, "nikkei": 0.04, "kospi": 0.04, "dxy": 0.03,
    "hyg": 0.05, "ust_10y": 0.03, "unrate": 0.03,
}


def compute_gfcri(data, date, lookback=12):
    """Compute GFCRI using z-score + historical percentile (not fixed thresholds)."""
    z_scores = {}
    pct_scores = {}

    for nid, series in data.items():
        hist = series[series.index <= date]
        if len(hist) < lookback + 1:
            continue
        current = hist.iloc[-1]
        lb = hist.iloc[-(lookback+1):-1]
        mean, std = lb.mean(), lb.std()

        # Z-score track
        if std > 0:
            z = (current - mean) / std
            z_scores[nid] = {"v": current, "z": z, "a": min(1.0, abs(z) / 4.0)}

        # Percentile track: where does current value sit in ALL available history?
        all_hist = series[series.index <= date]
        if len(all_hist) >= 24:
            if nid in HIGH_IS_DANGER:
                pct = (all_hist < current).mean()  # % of history below current = high percentile = danger
            elif nid in LOW_IS_DANGER:
                pct = (all_hist > current).mean()  # % of history above current = low percentile = danger
            else:
                pct = 0.5
            # Convert percentile to 0-1 danger score (above 80th percentile = danger zone)
            danger = max(0.0, min(1.0, (pct - 0.5) / 0.5)) if pct > 0.5 else 0.0
            pct_scores[nid] = {"v": current, "a": danger, "pct": pct}

    available = set(z_scores.keys()) | set(pct_scores.keys())
    if not available:
        return None

    active_weights = {k: v for k, v in BASE_WEIGHTS.items() if k in available}
    total_w = sum(active_weights.values())
    if total_w > 0:
        active_weights = {k: v / total_w for k, v in active_weights.items()}

    z_comp = sum(z_scores.get(n, {}).get("a", 0) * w for n, w in active_weights.items()) * 100
    pct_comp = sum(pct_scores.get(n, {}).get("a", 0) * w for n, w in active_weights.items()) * 100
    gfcri = Z_WEIGHT * z_comp + ABS_WEIGHT * pct_comp

    alert = "GREEN" if gfcri < 25 else "YELLOW" if gfcri < 50 else "ORANGE" if gfcri < 75 else "RED"
    return {
        "gfcri": gfcri, "z_comp": z_comp, "abs_comp": pct_comp, "alert": alert,
        "indicators": len(available),
        "vix": z_scores.get("vix", {}).get("v", 0),
        "spx": z_scores.get("spx", pct_scores.get("spx", {})).get("v", 0),
        "baa": pct_scores.get("baa_spread", z_scores.get("baa_spread", {})).get("v", 0),
    }


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    all_results = []

    for crisis in CRISES:
        if target != "all" and target not in crisis["name"]:
            continue

        print(f"\n{'='*80}")
        print(f"  {crisis['name']}")
        print(f"{'='*80}")

        print("Downloading data...")
        data = fetch_crisis_data(crisis)
        print(f"  Indicators: {len(data)} ({', '.join(data.keys())})")

        bt_start = pd.Timestamp(crisis["backtest_start"])
        bt_end = pd.Timestamp(crisis["backtest_end"])

        results = []
        for date in pd.date_range(bt_start, bt_end, freq="M"):
            r = compute_gfcri(data, date)
            if r:
                ds = date.strftime("%Y-%m")
                r["date"] = ds
                results.append(r)

        if not results:
            print("  No results (insufficient data)")
            continue

        # Print monthly table
        print(f"\n{'Date':<9} {'GFCRI':>6} {'Zsco':>5} {'Abso':>5} {'VIX':>6} {'SPX':>7} {'BAA':>5} {'Ind':>3}  Alert")
        print("-" * 70)
        for r in results:
            mark = " <<<" if r["gfcri"] > 35 else ""
            print(f"{r['date']:<9} {r['gfcri']:>6.1f} {r['z_comp']:>5.1f} {r['abs_comp']:>5.1f} {r['vix']:>6.1f} {r['spx']:>7.0f} {r['baa']:>5.2f} {r['indicators']:>3}  {r['alert']}{mark}")

        # Event validation
        print(f"\n--- 关键事件验证 ---")
        for ed, ev in crisis["events"]:
            match = [x for x in results if x["date"] == ed]
            if match:
                m = match[0]
                print(f"  {ed}: GFCRI={m['gfcri']:>5.1f} ({m['alert']:6}) | {ev}")

        # Summary
        peak = max(results, key=lambda x: x["gfcri"])
        first_yellow = next(((r["date"], r["gfcri"]) for r in results if r["alert"] != "GREEN"), None)
        first_orange = next(((r["date"], r["gfcri"]) for r in results if r["alert"] in ("ORANGE", "RED")), None)

        print(f"\n--- 预警能力评估 ---")
        if first_yellow:
            pe = crisis["peak_event"]
            months_before = (pd.Timestamp(pe + "-01") - pd.Timestamp(first_yellow[0] + "-01")).days // 30
            print(f"  首次预警: {first_yellow[0]} (GFCRI={first_yellow[1]:.1f}), 比峰值事件早{months_before}个月")
        if first_orange:
            pe = crisis["peak_event"]
            months_before = (pd.Timestamp(pe + "-01") - pd.Timestamp(first_orange[0] + "-01")).days // 30
            print(f"  首次橙色: {first_orange[0]} (GFCRI={first_orange[1]:.1f}), 比峰值事件早{months_before}个月")
        print(f"  风险峰值: {peak['date']} (GFCRI={peak['gfcri']:.1f})")

        all_results.append({
            "crisis": crisis["name"],
            "peak_gfcri": peak["gfcri"],
            "peak_date": peak["date"],
            "peak_alert": peak["alert"],
            "first_warning": first_yellow,
            "first_orange": first_orange,
            "peak_event": crisis["peak_event"],
        })

    # Final cross-crisis summary
    if len(all_results) > 1:
        print(f"\n\n{'='*80}")
        print(f"  模型验证总结 — {len(all_results)} 次历史危机")
        print(f"{'='*80}")
        print(f"\n{'危机':<30} {'峰值GFCRI':>8} {'峰值月':>8} {'提前预警':>8} {'首次橙色':>8}")
        print("-" * 75)
        for r in all_results:
            fw = r["first_warning"]
            fo = r["first_orange"]
            pe = r["peak_event"]
            fw_str = "—"
            fo_str = "—"
            if fw:
                m = (pd.Timestamp(pe + "-01") - pd.Timestamp(fw[0] + "-01")).days // 30
                fw_str = f"{m}个月前" if m > 0 else "同月"
            if fo:
                m = (pd.Timestamp(pe + "-01") - pd.Timestamp(fo[0] + "-01")).days // 30
                fo_str = f"{m}个月前" if m > 0 else "同月"
            print(f"{r['crisis']:<30} {r['peak_gfcri']:>8.1f} {r['peak_date']:>8} {fw_str:>8} {fo_str:>8}")
