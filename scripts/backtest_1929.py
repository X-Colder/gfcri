"""1929 Great Depression backtester — GFCRI validation with FRED historical data.

Available indicators (1927-1935):
  - DJIA (Dow Jones Industrial Average)
  - BAA-AAA credit spread (Moody's corporate bond yields)
  - Industrial Production Index
  - Unemployment Rate (from 1929-04)
  - CPI (deflation tracking)
  - Monetary Base
"""
import pandas as pd
import numpy as np
import requests

FRED_KEY = "25abae195da5a4815248927909aefa98"


def fetch_fred(series_id, start="1925-01-01", end="1936-12-31"):
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
    return df.set_index("date")["value"]


print("=" * 80)
print("  1929 大萧条 — GFCRI 历史回测")
print("=" * 80)

# Fetch data
print("\n下载数据...")
data = {}

djia = fetch_fred("M1109BUSM293NNBR")
if not djia.empty:
    data["djia"] = djia
    print(f"  道琼斯指数: {len(djia)} points, 1929-09: {djia.get('1929-09-01', 'N/A')}")

baa = fetch_fred("BAA")
aaa = fetch_fred("AAA")
if not baa.empty and not aaa.empty:
    data["baa_yield"] = baa
    data["aaa_yield"] = aaa
    baa_aaa = baa - aaa
    data["credit_spread"] = baa_aaa
    print(f"  BAA-AAA信用利差: {len(baa_aaa)} points, 1929-09: {baa_aaa.get('1929-09-01', 'N/A'):.2f}%")

indpro = fetch_fred("INDPRO")
if not indpro.empty:
    data["indpro"] = indpro
    print(f"  工业生产指数: {len(indpro)} points, 1929-09: {indpro.get('1929-09-01', 'N/A'):.1f}")

unrate = fetch_fred("M0892AUSM156SNBR")
if not unrate.empty:
    data["unrate"] = unrate
    print(f"  失业率: {len(unrate)} points, 1929-10: {unrate.get('1929-10-01', 'N/A'):.1f}%")

cpi = fetch_fred("CPIAUCNS")
if not cpi.empty:
    # Compute YoY deflation rate
    cpi_yoy = cpi.pct_change(12) * 100
    data["cpi"] = cpi
    data["cpi_yoy"] = cpi_yoy.dropna()
    print(f"  CPI: {len(cpi)} points")

monetary_base = fetch_fred("AMBSL")
if not monetary_base.empty:
    mb_yoy = monetary_base.pct_change(12) * 100
    data["monetary_base"] = monetary_base
    data["mb_yoy"] = mb_yoy.dropna()
    print(f"  货币基础: {len(monetary_base)} points")

print(f"\n总计: {len(data)} 个指标系列")


# 1929 era absolute thresholds
ABS_THRESHOLDS_1929 = {
    "djia":           ("low",  300, 60),       # normal~300 (1929 pre-crash), crisis~60 (1932 bottom)
    "credit_spread":  ("high", 1.2, 5.5),      # normal~1.2%, crisis~5.5% (1932 peak was ~5.6%)
    "baa_yield":      ("high", 5.5, 11.0),     # normal~5.5%, crisis~11% (1932)
    "indpro":         ("low",  7.5, 3.8),       # normal~7.5 (1929), crisis~3.8 (1932)
    "unrate":         ("high", 3.0, 25.0),      # normal~3%, crisis~25%
    "cpi_yoy":        ("low",  2.0, -10.0),     # normal~2%, crisis~-10% (deflation)
    "mb_yoy":         ("high", -5.0, 20.0),     # contraction = danger initially, then expansion = panic response
}

WEIGHTS_1929 = {
    "djia": 0.25,
    "credit_spread": 0.20,
    "baa_yield": 0.10,
    "indpro": 0.15,
    "unrate": 0.15,
    "cpi_yoy": 0.10,
    "mb_yoy": 0.05,
}

Z_WEIGHT, ABS_WEIGHT = 0.4, 0.6


def score_abs(nid, value):
    if nid not in ABS_THRESHOLDS_1929:
        return 0.0
    direction, normal, crisis = ABS_THRESHOLDS_1929[nid]
    if direction == "high":
        rng = crisis - normal
        return max(0.0, min(1.0, (value - normal) / rng)) if rng > 0 else 0.0
    else:
        rng = normal - crisis
        return max(0.0, min(1.0, (normal - value) / rng)) if rng > 0 else 0.0


# Run backtest
print(f"\n{'Date':<10} {'GFCRI':>6} {'Zsco':>5} {'Abso':>5} {'DJIA':>7} {'BAAsp':>6} {'IndPr':>6} {'Unemp':>6} {'CPI%':>6} Alert")
print("-" * 80)

results = []
for date in pd.date_range("1928-01-01", "1935-12-31", freq="M"):
    z_scores = {}
    abs_scores = {}

    for nid in ["djia", "credit_spread", "baa_yield", "indpro", "unrate", "cpi_yoy", "mb_yoy"]:
        series = data.get(nid)
        if series is None:
            continue
        hist = series[series.index <= date]
        if len(hist) < 13:
            continue
        current = hist.iloc[-1]
        lb = hist.iloc[-13:-1]
        mean, std = lb.mean(), lb.std()
        if std > 0:
            z = (current - mean) / std
            z_scores[nid] = {"v": current, "z": z, "a": min(1.0, abs(z) / 4.0)}
        abs_scores[nid] = {"v": current, "a": score_abs(nid, current)}

    available = set(z_scores.keys()) | set(abs_scores.keys())
    if not available:
        continue

    active_weights = {k: v for k, v in WEIGHTS_1929.items() if k in available}
    total_w = sum(active_weights.values())
    if total_w > 0:
        active_weights = {k: v / total_w for k, v in active_weights.items()}

    z_comp = sum(z_scores.get(n, {}).get("a", 0) * w for n, w in active_weights.items()) * 100
    abs_comp = sum(abs_scores.get(n, {}).get("a", 0) * w for n, w in active_weights.items()) * 100
    gfcri = Z_WEIGHT * z_comp + ABS_WEIGHT * abs_comp

    alert = "GREEN" if gfcri < 25 else "YELLOW" if gfcri < 50 else "ORANGE" if gfcri < 75 else "RED"

    djia_v = z_scores.get("djia", {}).get("v", abs_scores.get("djia", {}).get("v", 0))
    baa_sp = z_scores.get("credit_spread", {}).get("v", abs_scores.get("credit_spread", {}).get("v", 0))
    indpro_v = z_scores.get("indpro", {}).get("v", abs_scores.get("indpro", {}).get("v", 0))
    unrate_v = z_scores.get("unrate", {}).get("v", abs_scores.get("unrate", {}).get("v", 0))
    cpi_v = z_scores.get("cpi_yoy", {}).get("v", abs_scores.get("cpi_yoy", {}).get("v", 0))

    mark = " <<<" if gfcri > 35 else ""
    ds = date.strftime("%Y-%m")
    print(f"{ds:<10} {gfcri:>6.1f} {z_comp:>5.1f} {abs_comp:>5.1f} {djia_v:>7.1f} {baa_sp:>6.2f} {indpro_v:>6.1f} {unrate_v:>6.1f} {cpi_v:>6.1f}  {alert}{mark}")
    results.append({"date": ds, "gfcri": gfcri, "z_comp": z_comp, "abs_comp": abs_comp,
                     "alert": alert, "djia": djia_v, "baa_spread": baa_sp, "indpro": indpro_v,
                     "unrate": unrate_v, "cpi_yoy": cpi_v})


# Key events validation
print(f"\n{'='*60}")
print("关键事件验证")
print(f"{'='*60}")

events = [
    ("1928-12", "牛市狂热，道琼斯年涨48%"),
    ("1929-09", "道琼斯见顶381"),
    ("1929-10", "黑色星期四+黑色星期二，崩盘开始"),
    ("1929-11", "道琼斯一月跌37%"),
    ("1930-06", "胡佛签署Smoot-Hawley关税法"),
    ("1930-12", "合众国银行倒闭（当时最大银行破产）"),
    ("1931-05", "奥地利信贷银行倒闭，欧洲危机"),
    ("1931-09", "英镑脱离金本位"),
    ("1932-06", "道琼斯见底41.22，失业率25%"),
    ("1933-03", "罗斯福就任，宣布银行假日（全国银行关门）"),
    ("1933-06", "新政启动，经济开始恢复"),
    ("1935-12", "经济部分恢复"),
]
for ed, ev in events:
    match = [r for r in results if r["date"] == ed]
    if match:
        r = match[0]
        print(f"  {ed}: GFCRI={r['gfcri']:>5.1f} ({r['alert']:6}) DJIA={r['djia']:.0f} BAA利差={r['baa_spread']:.2f}% 失业={r['unrate']:.1f}% | {ev}")

# Summary
print(f"\n{'='*60}")
print("预警能力评估")
print(f"{'='*60}")

peak = max(results, key=lambda x: x["gfcri"])
first_yellow = next(((r["date"], r["gfcri"]) for r in results if r["alert"] != "GREEN"), None)
first_orange = next(((r["date"], r["gfcri"]) for r in results if r["alert"] in ("ORANGE", "RED")), None)
first_red = next(((r["date"], r["gfcri"]) for r in results if r["alert"] == "RED"), None)

if first_yellow:
    m = (pd.Timestamp("1929-10-01") - pd.Timestamp(first_yellow[0] + "-01")).days // 30
    print(f"  首次预警(黄色): {first_yellow[0]} (GFCRI={first_yellow[1]:.1f}), {'比崩盘早' + str(m) + '个月' if m > 0 else '崩盘当月'}")
if first_orange:
    m = (pd.Timestamp("1929-10-01") - pd.Timestamp(first_orange[0] + "-01")).days // 30
    print(f"  首次橙色: {first_orange[0]} (GFCRI={first_orange[1]:.1f}), {'比崩盘早' + str(m) + '个月' if m > 0 else '崩盘' + str(abs(m)) + '个月后'}")
if first_red:
    m = (pd.Timestamp("1929-10-01") - pd.Timestamp(first_red[0] + "-01")).days // 30
    print(f"  首次红色: {first_red[0]} (GFCRI={first_red[1]:.1f})")
print(f"  风险峰值: {peak['date']} (GFCRI={peak['gfcri']:.1f})")

# Compare with other crises
print(f"\n{'='*60}")
print("与其他危机对比")
print(f"{'='*60}")
print(f"  1929 大萧条:    GFCRI 峰值 {peak['gfcri']:.1f}")
print(f"  2008 金融危机:   GFCRI 峰值 83.8")
print(f"  2020 新冠恐慌:   GFCRI 峰值 64.4")
print(f"  2000 互联网泡沫:  GFCRI 峰值 59.2")
print(f"  1997 亚洲危机:   GFCRI 峰值 58.1")
