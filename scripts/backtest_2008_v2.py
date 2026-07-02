"""2008 crisis backtest v2 — dual-track scoring: z-score + absolute level."""
import yfinance as yf
import pandas as pd
import numpy as np
import requests

FRED_KEY = "25abae195da5a4815248927909aefa98"

# Absolute-level thresholds: (normal, crisis) — "high" means rising is bad
ABS_THRESHOLDS = {
    "vix":             ("high", 15, 45),
    "spx":             ("low", 1500, 800),
    "baa_spread":      ("high", 1.8, 5.5),
    "baa_aaa_spread":  ("high", 0.9, 3.0),
    "ted_spread":      ("high", 0.3, 2.5),
    "t10y2y":          ("low", 1.0, -0.5),
    "gold":            ("high", 650, 1000),
    "oil_wti":         ("high", 65, 140),
    "eem":             ("low", 45, 20),
}

def fetch_fred(series_id, start="2005-01-01", end="2009-12-31"):
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

def score_absolute(nid, value):
    """Score 0-1 based on where value sits between normal and crisis thresholds."""
    if nid not in ABS_THRESHOLDS:
        return 0.0
    direction, normal, crisis = ABS_THRESHOLDS[nid]
    if direction == "high":
        rng = crisis - normal
        if rng <= 0:
            return 0.0
        return max(0.0, min(1.0, (value - normal) / rng))
    else:
        rng = normal - crisis
        if rng <= 0:
            return 0.0
        return max(0.0, min(1.0, (normal - value) / rng))

# ── Data collection ──
print("Downloading market data...")
tickers = {"vix": "^VIX", "spx": "^GSPC", "gold": "GC=F", "oil_wti": "CL=F", "eem": "EEM"}
raw = yf.download(list(tickers.values()), start="2005-01-01", end="2009-12-31", progress=False, auto_adjust=True)

data = {}
for nid, ticker in tickers.items():
    try:
        if isinstance(raw.columns, pd.MultiIndex):
            close = raw[("Close", ticker)].dropna()
        else:
            close = raw["Close"].dropna()
        data[nid] = close.resample("M").last().dropna()
    except:
        pass

print("Downloading FRED credit/macro data...")
fred_series = {
    "baa_spread": ("BAA10Y", "BAA对国债利差(信用风险)"),
    "ted_spread": ("TEDRATE", "TED利差(银行间信任)"),
    "t10y2y": ("T10Y2Y", "收益率曲线"),
}
for nid, (sid, name) in fred_series.items():
    series = fetch_fred(sid)
    if not series.empty:
        data[nid] = series
        print("  {} ({}): {} pts, latest={:.2f}".format(name, sid, len(series), series.iloc[-1]))
    else:
        print("  {} ({}): NO DATA".format(name, sid))

baa_y = fetch_fred("DBAA")
aaa_y = fetch_fred("DAAA")
if not baa_y.empty and not aaa_y.empty:
    baa_aaa = (baa_y - aaa_y).dropna()
    if not baa_aaa.empty:
        data["baa_aaa_spread"] = baa_aaa
        print("  BAA-AAA利差 (DBAA-DAAA): {} pts, latest={:.2f}".format(len(baa_aaa), baa_aaa.iloc[-1]))

print("\nTotal indicators:", len(data))

# ── Weights ──
BASE_WEIGHTS = {
    "vix": 0.25,
    "spx": 0.20,
    "baa_spread": 0.14,
    "baa_aaa_spread": 0.10,
    "ted_spread": 0.10,
    "gold": 0.05,
    "oil_wti": 0.05,
    "eem": 0.06,
    "t10y2y": 0.05,
}

Z_WEIGHT = 0.4
ABS_WEIGHT = 0.6

# ── Backtest ──
print()
print("{:<8} {:>5} {:>5} {:>6} {:>5} {:>5} {:>5} {:>5}  {:>5} {:>5} {:>5}  {}".format(
    "Date", "VIX", "VIXz", "SPX", "BAA", "BA-A", "TED", "10-2",
    "Zsco", "Abso", "GFCRI", "Alert"))
print("-" * 100)

results = []
for date in pd.date_range("2007-01-31", "2009-06-30", freq="M"):
    z_scores = {}
    abs_scores = {}

    for nid, series in data.items():
        hist = series[series.index <= date]
        if len(hist) < 13:
            continue
        current = hist.iloc[-1]

        # z-score track
        lb = hist.iloc[-13:-1]
        mean, std = lb.mean(), lb.std()
        if std > 0:
            z = (current - mean) / std
            z_scores[nid] = {"v": current, "z": z, "a": min(1.0, abs(z) / 4.0)}

        # absolute level track
        a_score = score_absolute(nid, current)
        abs_scores[nid] = {"v": current, "a": a_score}

    available = set(z_scores.keys()) | set(abs_scores.keys())
    if not available:
        continue

    active_weights = {k: v for k, v in BASE_WEIGHTS.items() if k in available}
    total_w = sum(active_weights.values())
    if total_w > 0:
        active_weights = {k: v / total_w for k, v in active_weights.items()}

    z_composite = sum(z_scores.get(n, {}).get("a", 0) * w for n, w in active_weights.items()) * 100
    abs_composite = sum(abs_scores.get(n, {}).get("a", 0) * w for n, w in active_weights.items()) * 100
    gfcri = Z_WEIGHT * z_composite + ABS_WEIGHT * abs_composite

    vv = z_scores.get("vix", {}).get("v", 0)
    vz = z_scores.get("vix", {}).get("z", 0)
    sv = z_scores.get("spx", {}).get("v", 0)
    baa_v = z_scores.get("baa_spread", {}).get("v", 0)
    ba_a = z_scores.get("baa_aaa_spread", {}).get("v", 0)
    ted_v = z_scores.get("ted_spread", {}).get("v", 0)
    t10y2y_v = z_scores.get("t10y2y", {}).get("v", 0)

    alert = "GREEN" if gfcri < 25 else "YELLOW" if gfcri < 50 else "ORANGE" if gfcri < 75 else "RED"
    mark = " <<<" if gfcri > 35 else ""
    ds = date.strftime("%Y-%m")

    print("{:<8} {:>5.1f} {:>+5.1f} {:>6.0f} {:>5.2f} {:>5.2f} {:>5.2f} {:>+5.2f}  {:>5.1f} {:>5.1f} {:>5.1f}  {}{}".format(
        ds, vv, vz, sv, baa_v, ba_a, ted_v, t10y2y_v,
        z_composite, abs_composite, gfcri, alert, mark))
    results.append({
        "date": ds, "gfcri": gfcri, "z_comp": z_composite, "abs_comp": abs_composite,
        "alert": alert, "vix": vv, "spx": sv, "baa": baa_v, "baa_aaa": ba_a, "ted": ted_v,
    })

# ── Validation ──
print()
print("=== 关键事件验证（v2: z-score 40% + 绝对水平 60%）===")
events = [
    ("2007-02", "汇丰次贷减值"),
    ("2007-08", "BNP冻结基金"),
    ("2007-10", "次贷危机扩散"),
    ("2008-01", "全球股市暴跌"),
    ("2008-03", "Bear Stearns倒闭"),
    ("2008-04", "市场反弹（v1假阴性）"),
    ("2008-08", "雷曼前夕（v1假阴性）"),
    ("2008-09", "雷曼破产"),
    ("2008-10", "恐慌顶点"),
    ("2008-11", "美联储QE"),
    ("2009-03", "SPX见底"),
]
for ed, ev in events:
    r = [x for x in results if x["date"] == ed]
    if r:
        r = r[0]
        print("  {}: GFCRI={:>5.1f} ({:6s}) [Z={:.1f} Abs={:.1f}] VIX={:.1f} BAA={:.2f} TED={:.2f} | {}".format(
            ed, r["gfcri"], r["alert"], r["z_comp"], r["abs_comp"], r["vix"], r["baa"], r["ted"], ev))

print()
print("=== v1 vs v2 假阴性对比 ===")
v1_false_neg = {"2008-04": 19.5, "2008-08": 23.8}
for date_str, v1_score in v1_false_neg.items():
    r = [x for x in results if x["date"] == date_str]
    if r:
        v2 = r[0]
        fixed = "FIXED" if v2["alert"] != "GREEN" else "STILL FALSE NEG"
        print("  {}: v1={:.1f}(GREEN) -> v2={:.1f}({}) [Z={:.1f} Abs={:.1f}] [{}]".format(
            date_str, v1_score, v2["gfcri"], v2["alert"], v2["z_comp"], v2["abs_comp"], fixed))

print()
print("=== 预警能力评估 ===")
first_yellow = next(((r["date"], r["gfcri"]) for r in results if r["alert"] != "GREEN"), None)
first_orange = next(((r["date"], r["gfcri"]) for r in results if r["alert"] in ("ORANGE", "RED")), None)
peak = max(results, key=lambda x: x["gfcri"])
if first_yellow:
    m = (pd.Timestamp("2008-09-01") - pd.Timestamp(first_yellow[0] + "-01")).days // 30
    print("  首次预警: {} (GFCRI={:.1f}), 比雷曼早{}个月".format(first_yellow[0], first_yellow[1], m))
if first_orange:
    m = (pd.Timestamp("2008-09-01") - pd.Timestamp(first_orange[0] + "-01")).days // 30
    print("  首次橙色: {} (GFCRI={:.1f}), 比雷曼早{}个月".format(first_orange[0], first_orange[1], m))
print("  风险峰值: {} (GFCRI={:.1f})".format(peak["date"], peak["gfcri"]))

# No GREEN months during the crisis?
crisis_window = [r for r in results if "2008-03" <= r["date"] <= "2008-11"]
greens = [r for r in crisis_window if r["alert"] == "GREEN"]
print()
if greens:
    print("  ⚠ 2008-03~11仍有{}个月误判为GREEN: {}".format(len(greens), [r["date"] for r in greens]))
else:
    print("  ✓ 2008-03~11期间无假阴性（GREEN）")
