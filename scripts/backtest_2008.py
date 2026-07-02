"""2008 crisis backtest for GFCRI model validation."""
import yfinance as yf
import pandas as pd
import numpy as np

tickers = {"vix": "^VIX", "spx": "^GSPC", "gold": "GC=F", "oil_wti": "CL=F", "eem": "EEM"}
raw = yf.download(list(tickers.values()), start="2006-01-01", end="2009-12-31", progress=False, auto_adjust=True)

data = {}
for nid, ticker in tickers.items():
    try:
        if isinstance(raw.columns, pd.MultiIndex):
            close = raw[("Close", ticker)].dropna()
        else:
            close = raw["Close"].dropna()
        data[nid] = close.resample("ME").last().dropna()
    except:
        pass

print("Indicators:", list(data.keys()))
print()
print("{:<10} {:>6} {:>6} {:>7} {:>6} {:>6} {}".format("Date", "VIX", "VIX_z", "SPX", "SPX_z", "GFCRI", "Alert"))
print("-" * 65)

results = []
for date in pd.date_range("2007-01-31", "2009-06-30", freq="ME"):
    scores = {}
    for nid, series in data.items():
        hist = series[series.index <= date]
        if len(hist) < 13:
            continue
        current = hist.iloc[-1]
        lb = hist.iloc[-13:-1]
        mean, std = lb.mean(), lb.std()
        if std > 0:
            z = (current - mean) / std
            scores[nid] = {"v": current, "z": z, "a": min(1.0, abs(z) / 4.0)}

    if not scores:
        continue
    weights = {"vix": 0.30, "spx": 0.25, "gold": 0.15, "oil_wti": 0.15, "eem": 0.15}
    gfcri = sum(scores.get(n, {}).get("a", 0) * w for n, w in weights.items()) * 100

    vv = scores.get("vix", {}).get("v", 0)
    vz = scores.get("vix", {}).get("z", 0)
    sv = scores.get("spx", {}).get("v", 0)
    sz = scores.get("spx", {}).get("z", 0)
    alert = "GREEN" if gfcri < 25 else "YELLOW" if gfcri < 50 else "ORANGE" if gfcri < 75 else "RED"
    mark = " <<<" if gfcri > 35 else ""

    ds = date.strftime("%Y-%m")
    print("{:<10} {:>6.1f} {:>+6.1f} {:>7.0f} {:>+6.1f} {:>6.1f} {}{}".format(ds, vv, vz, sv, sz, gfcri, alert, mark))
    results.append((ds, gfcri, alert, vv, sv))

print()
print("=== 2008 关键事件验证 ===")
events = [
    ("2007-02", "汇丰次贷减值（最早信号）"),
    ("2007-08", "BNP Paribas冻结基金（次贷危机公开化）"),
    ("2008-03", "Bear Stearns被收购"),
    ("2008-09", "雷曼兄弟破产（全球恐慌）"),
    ("2008-10", "恐慌顶点 VIX=80"),
    ("2008-11", "美联储首次QE"),
    ("2009-03", "标普500见底 666点"),
]
for ed, ev in events:
    r = [x for x in results if x[0] == ed]
    if r:
        print("  {}: GFCRI={:.1f} ({}) VIX={:.0f} SPX={:.0f} | {}".format(ed, r[0][1], r[0][2], r[0][3], r[0][4], ev))
    else:
        print("  {}: 无数据 | {}".format(ed, ev))

print()
print("=== 模型预警能力评估 ===")
first_yellow = next(((d, g) for d, g, a, _, _ in results if a != "GREEN"), None)
first_orange = next(((d, g) for d, g, a, _, _ in results if a in ("ORANGE", "RED")), None)
peak = max(results, key=lambda x: x[1])
if first_yellow:
    print("  首次黄色预警: {} (GFCRI={:.1f})".format(first_yellow[0], first_yellow[1]))
if first_orange:
    print("  首次橙色预警: {} (GFCRI={:.1f})".format(first_orange[0], first_orange[1]))
print("  风险峰值: {} (GFCRI={:.1f})".format(peak[0], peak[1]))
print("  雷曼破产: 2008-09")
if first_yellow:
    print("  模型提前预警: 比雷曼破产早 {} 个月".format(
        (pd.Timestamp("2008-09-01") - pd.Timestamp(first_yellow[0] + "-01")).days // 30
    ))
