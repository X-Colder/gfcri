"""
Social content generator for WeChat, Zsxq, and Share Card.

All three outputs share the same content structure:
  1. LLM narrative analysis (summary first)
  2. Risk panorama (sub-indices)
  3. Anomalous indicators
  4. Active transmission chains
  5. Alerts

All output is in Chinese. Transmission chains use SVG flow diagrams
in HTML and ASCII boxes in plain text.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any

from loguru import logger
from src.i18n import NODE_CN, CHAIN_CN, SI_CN, ALERT_CN, cn_name, cn_short


import re


def _color(score: float) -> str:
    if score >= 60: return "#ff7a8a"
    if score >= 45: return "#ffb86b"
    if score >= 25: return "#ffd66b"
    return "#5de4c7"


def _md_to_html(text: str) -> str:
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    return text


def _md_strip(text: str) -> str:
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    return text


def _bar_html(score: float, w: int = 180) -> str:
    c = _color(score)
    f = int(score / 100 * w)
    return (
        f'<div style="background:#1a2332;border-radius:4px;height:8px;width:{w}px;display:inline-block;vertical-align:middle">'
        f'<div style="background:{c};border-radius:4px;height:8px;width:{f}px"></div></div>'
    )


def _chain_svg(path: list[str], stress: float, strength: float) -> str:
    n = len(path)
    node_w = 72
    arrow_w = 36
    total_w = n * node_w + (n - 1) * arrow_w
    h = 52
    c = _color(stress)

    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {h}" style="width:100%;max-width:{total_w}px;height:{h}px">'
    svg += f'<defs><marker id="ah" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{c}"/></marker></defs>'

    for i, nid in enumerate(path):
        x = i * (node_w + arrow_w)
        label = cn_short(nid)
        svg += f'<rect x="{x}" y="8" width="{node_w}" height="34" rx="6" fill="#0d1822" stroke="{c}" stroke-width="1.5"/>'
        svg += f'<text x="{x + node_w/2}" y="30" text-anchor="middle" fill="#e0e8f0" font-size="11" font-family="-apple-system,PingFang SC,Microsoft YaHei,sans-serif">{label}</text>'

        if i < n - 1:
            ax1 = x + node_w + 3
            ax2 = x + node_w + arrow_w - 3
            svg += f'<line x1="{ax1}" y1="25" x2="{ax2}" y2="25" stroke="{c}" stroke-width="2" marker-end="url(#ah)"/>'

    svg += '</svg>'
    return svg


# =========================================================================
# WeChat HTML
# =========================================================================

def generate_wechat_html(
    gfcri_result: dict[str, Any],
    alerts: list[dict[str, Any]] | None = None,
    llm_narrative: str | None = None,
    inference_summary: dict[str, Any] | None = None,
    report_date: str | None = None,
    prev_gfcri: float | None = None,
) -> str:
    report_date = report_date or date.today().isoformat()
    gfcri = gfcri_result["gfcri"]
    alert = gfcri_result["alert_level"]
    alert_label = ALERT_CN.get(alert, alert)
    color = _color(gfcri)
    sub_indices = gfcri_result.get("sub_indices", {})
    chains = gfcri_result.get("chains", [])
    contribs = gfcri_result.get("node_contributions", {})

    anomalous = sorted(
        [(nid, info) for nid, info in contribs.items() if info.get("is_anomalous")],
        key=lambda x: abs(x[1].get("zscore", 0)), reverse=True,
    )
    active_chains = [c for c in chains if c.get("active")]

    # Build change indicator
    change_html = ""
    if prev_gfcri is not None:
        delta = gfcri - prev_gfcri
        arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
        delta_color = "#ff4d4f" if delta > 0 else "#52c41a" if delta < 0 else "#999"
        change_html = f'<p style="font-size:13px;color:#888;margin-top:8px">昨日 {prev_gfcri:.1f} <span style="color:{delta_color};font-weight:700">{arrow} {abs(delta):.1f}</span></p>'

    # Risk level context
    if gfcri < 25:
        level_desc = "安全区间"
        level_color = "#52c41a"
    elif gfcri < 45:
        level_desc = "关注区间"
        level_color = "#faad14"
    elif gfcri < 60:
        level_desc = "警告区间"
        level_color = "#fa8c16"
    else:
        level_desc = "危险区间"
        level_color = "#ff4d4f"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,"PingFang SC","Microsoft YaHei","Helvetica Neue",sans-serif; background:#ffffff; color:#1a1a1a; line-height:1.8; font-size:15px; }}
.w {{ max-width:640px; margin:0 auto; padding:24px 16px; }}
</style></head><body><div class="w">

<div style="text-align:center;padding:30px 0 20px;border-bottom:1px solid #f0f0f0">
  <p style="font-size:12px;color:#888;letter-spacing:2px">GFCRI 全球金融风险指数</p>
  <p style="font-size:56px;font-weight:800;color:{color};margin:8px 0;line-height:1">{gfcri:.1f}</p>
  {change_html}
  <div style="margin-top:12px">
    <span style="display:inline-block;font-size:12px;margin:0 3px;padding:3px 10px;border-radius:3px;background:#f6ffed;color:#52c41a;{'font-weight:700;border:1px solid #52c41a' if gfcri < 25 else ''}">0-25 安全</span>
    <span style="display:inline-block;font-size:12px;margin:0 3px;padding:3px 10px;border-radius:3px;background:#fffbe6;color:#faad14;{'font-weight:700;border:1px solid #faad14' if 25 <= gfcri < 45 else ''}">25-45 关注</span>
    <span style="display:inline-block;font-size:12px;margin:0 3px;padding:3px 10px;border-radius:3px;background:#fff7e6;color:#fa8c16;{'font-weight:700;border:1px solid #fa8c16' if 45 <= gfcri < 60 else ''}">45-60 警告</span>
    <span style="display:inline-block;font-size:12px;margin:0 3px;padding:3px 10px;border-radius:3px;background:#fff1f0;color:#ff4d4f;{'font-weight:700;border:1px solid #ff4d4f' if gfcri >= 60 else ''}">60-100 危险</span>
  </div>
</div>
"""

    # Narrative analysis FIRST
    if llm_narrative:
        html += '<div style="padding:24px 0;border-bottom:1px solid #f0f0f0">\n'
        html += '<p style="font-size:14px;font-weight:700;color:#333;letter-spacing:1px;margin-bottom:16px"><span style="display:inline-block;width:3px;height:14px;background:#1a1a1a;border-radius:1px;margin-right:8px;vertical-align:middle"></span>分析观点</p>\n'
        for p in llm_narrative.strip().split("\n\n"):
            clean = p.strip()
            if clean and not clean.startswith("#") and not clean.startswith("|") and not clean.startswith("---"):
                converted = _md_to_html(clean)
                converted = converted.replace("\n", "<br/>")
                html += f'<p style="font-size:15px;color:#333;line-height:2;margin-bottom:14px">{converted}</p>\n'
        html += f'<p style="font-size:11px;color:#bbb;margin-top:16px;padding-top:12px;border-top:1px solid #f5f5f5">以上分析由 GFCRI 因果推理引擎生成，基于 {len(contribs)} 个实时市场指标的因果链路计算与偏离度检测，数据源为 yfinance 全球实时行情。</p>\n'
        html += '</div>\n'

    # Alerts
    if alerts:
        html += '<div style="padding:24px 0;border-bottom:1px solid #f0f0f0">\n'
        html += '<p style="font-size:14px;font-weight:700;color:#333;letter-spacing:1px;margin-bottom:16px"><span style="display:inline-block;width:3px;height:14px;background:#ff4d4f;border-radius:1px;margin-right:8px;vertical-align:middle"></span>风险预警</p>\n'
        for a in alerts:
            border_c = "#ff4d4f" if a.get("level") != "warning" else "#faad14"
            html += f'<div style="background:#fffbe6;border-left:3px solid {border_c};border-radius:4px;padding:12px 14px;margin-bottom:10px">'
            html += f'<p style="font-size:14px;font-weight:700;color:{border_c};margin-bottom:4px">{a["title"]}</p>'
            html += f'<p style="font-size:13px;color:#666;line-height:1.6">{a["detail"]}</p></div>\n'
        html += '</div>\n'

    # Divergence warning (calm before the storm)
    divergence = gfcri_result.get("divergence", {})
    div_status = divergence.get("status", "none")
    div_details = divergence.get("details", [])
    if div_status != "none" and div_details:
        severity_colors = {"mild": "#faad14", "significant": "#fa8c16", "critical": "#ff4d4f"}
        severity_labels = {"mild": "轻度背离", "significant": "显著背离", "critical": "严重背离"}
        sc = severity_colors.get(div_status, "#faad14")
        sl = severity_labels.get(div_status, "背离")
        surface_pct = divergence.get("surface_avg", 0) * 100
        deep_pct = divergence.get("deep_avg", 0) * 100

        html += '<div style="padding:24px 0;border-bottom:1px solid #f0f0f0">\n'
        html += f'<p style="font-size:14px;font-weight:700;color:{sc};letter-spacing:1px;margin-bottom:12px"><span style="display:inline-block;width:3px;height:14px;background:{sc};border-radius:1px;margin-right:8px;vertical-align:middle"></span>⚡ 暴风雨前的平静 — {sl}</p>\n'

        html += f'<div style="display:flex;gap:12px;margin-bottom:16px">'
        html += f'<div style="flex:1;background:#f6ffed;border-radius:8px;padding:12px;text-align:center"><p style="font-size:11px;color:#888;margin-bottom:4px">表面指标</p><p style="font-size:24px;font-weight:800;color:#52c41a">{surface_pct:.0f}%</p></div>'
        html += f'<div style="flex:1;background:#fff1f0;border-radius:8px;padding:12px;text-align:center"><p style="font-size:11px;color:#888;margin-bottom:4px">底层指标</p><p style="font-size:24px;font-weight:800;color:#ff4d4f">{deep_pct:.0f}%</p></div>'
        html += f'</div>\n'

        for d in div_details:
            dtype = d.get("type", "")
            title = d.get("title", "")
            detail = d.get("detail", "")
            icon = "🌊" if dtype == "surface_calm_deep_stress" else "🐸"
            html += f'<div style="background:#fffbe6;border-left:3px solid {sc};border-radius:4px;padding:12px 14px;margin-bottom:10px">'
            html += f'<p style="font-size:14px;font-weight:700;color:#333;margin-bottom:6px">{icon} {title}</p>'
            html += f'<p style="font-size:13px;color:#666;line-height:1.7">{_md_to_html(detail)}</p></div>\n'

        html += '</div>\n'

    # Policy mask — "fever chart"
    divergence = gfcri_result.get("divergence", {})
    policy_mask = None
    for d in divergence.get("details", []):
        if d.get("type") == "policy_mask":
            policy_mask = d
            break

    if policy_mask:
        pr_avg = policy_mask["policy_responsive_avg"]
        st_avg = policy_mask["structural_avg"]
        ld_avg = policy_mask.get("leading_avg", 0)

        html += '<div style="padding:24px 0;border-bottom:1px solid #f0f0f0">\n'
        html += '<p style="font-size:14px;font-weight:700;color:#333;letter-spacing:1px;margin-bottom:12px"><span style="display:inline-block;width:3px;height:14px;background:#fa8c16;border-radius:1px;margin-right:8px;vertical-align:middle"></span>🌡️ 政策退烧 vs 病根未除</p>\n'

        html += f'<div style="display:flex;gap:8px;margin-bottom:16px">'
        html += f'<div style="flex:1;background:#f6ffed;border-radius:8px;padding:10px;text-align:center"><p style="font-size:11px;color:#888;margin-bottom:2px">💊 政策敏感</p><p style="font-size:22px;font-weight:800;color:#52c41a">{pr_avg}%</p></div>'
        html += f'<div style="flex:1;background:#fff1f0;border-radius:8px;padding:10px;text-align:center"><p style="font-size:11px;color:#888;margin-bottom:2px">🦠 结构性</p><p style="font-size:22px;font-weight:800;color:#ff4d4f">{st_avg}%</p></div>'
        if ld_avg:
            html += f'<div style="flex:1;background:#fff7e6;border-radius:8px;padding:10px;text-align:center"><p style="font-size:11px;color:#888;margin-bottom:2px">🔮 领先信号</p><p style="font-size:22px;font-weight:800;color:#fa8c16">{ld_avg}%</p></div>'
        html += f'</div>\n'

        for item in policy_mask.get("healed", [])[:3]:
            html += f'<div style="display:flex;align-items:center;padding:6px 0;border-bottom:1px solid #f5f5f5"><span style="font-size:13px;color:#52c41a;width:20px">✅</span><span style="flex:1;font-size:13px;color:#333">{item["label"]}</span><span style="font-size:12px;color:#52c41a;font-weight:700">{item["score"]}%</span></div>\n'
        for item in policy_mask.get("unhealed", [])[:4]:
            html += f'<div style="display:flex;align-items:center;padding:6px 0;border-bottom:1px solid #f5f5f5"><span style="font-size:13px;color:#ff4d4f;width:20px">⚠️</span><span style="flex:1;font-size:13px;color:#333">{item["label"]}</span><span style="font-size:12px;color:#ff4d4f;font-weight:700">{item["score"]}%</span></div>\n'
        for item in policy_mask.get("leading_warnings", [])[:3]:
            html += f'<div style="display:flex;align-items:center;padding:6px 0;border-bottom:1px solid #f5f5f5"><span style="font-size:13px;color:#fa8c16;width:20px">🔮</span><span style="flex:1;font-size:13px;color:#333">{item["label"]}</span><span style="font-size:12px;color:#fa8c16;font-weight:700">{item["score"]}%</span></div>\n'

        html += '<p style="font-size:12px;color:#999;margin-top:12px;line-height:1.6">💡 政策敏感型好转只说明央行止血了，结构性指标才决定危机会不会爆发。2008年4-8月：VIX和股市反弹（退烧药见效），但信用利差从未好转（病根还在），5个月后雷曼倒闭。</p>\n'
        html += '</div>\n'

    # Sub-indices
    html += '<div style="padding:24px 0;border-bottom:1px solid #f0f0f0">\n'
    html += '<p style="font-size:14px;font-weight:700;color:#333;letter-spacing:1px;margin-bottom:16px"><span style="display:inline-block;width:3px;height:14px;background:#1890ff;border-radius:1px;margin-right:8px;vertical-align:middle"></span>风险全景</p>\n'
    for si_id, si in sub_indices.items():
        s = si.get("score", 0)
        name = SI_CN.get(si_id, si.get("name", si_id))
        c = _color(s)
        bar_w = int(s / 100 * 160)
        html += f'<div style="display:flex;align-items:center;padding:6px 0;border-bottom:1px solid #f5f5f5">'
        html += f'<span style="width:75px;font-size:13px;color:#666;flex-shrink:0">{name}</span>'
        html += f'<span style="flex:1;padding:0 10px"><span style="display:inline-block;background:#f0f0f0;border-radius:4px;height:8px;width:160px;vertical-align:middle"><span style="display:inline-block;background:{c};border-radius:4px;height:8px;width:{bar_w}px"></span></span></span>'
        html += f'<span style="width:30px;text-align:right;font-size:14px;font-weight:700;color:{c}">{s:.0f}</span></div>\n'
    html += '</div>\n'

    # Anomalous nodes
    if anomalous:
        html += '<div style="padding:24px 0;border-bottom:1px solid #f0f0f0">\n'
        html += f'<p style="font-size:14px;font-weight:700;color:#333;letter-spacing:1px;margin-bottom:16px"><span style="display:inline-block;width:3px;height:14px;background:#faad14;border-radius:1px;margin-right:8px;vertical-align:middle"></span>异常指标（{len(anomalous)}个）</p>\n'
        for nid, info in anomalous[:10]:
            z = info.get("zscore", 0)
            c = "#ff4d4f" if abs(z) > 3 else "#faad14"
            name = cn_name(nid)
            direction = "偏高" if z > 0 else "偏低"
            html += f'<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #fafafa">'
            html += f'<span style="font-size:14px;color:#333">{name}</span>'
            html += f'<span style="font-size:13px;font-weight:700;color:{c}">{direction} {abs(z):.1f}倍</span></div>\n'
        html += '</div>\n'

    # Chains
    if active_chains:
        html += '<div style="padding:24px 0;border-bottom:1px solid #f0f0f0">\n'
        html += f'<p style="font-size:14px;font-weight:700;color:#333;letter-spacing:1px;margin-bottom:16px"><span style="display:inline-block;width:3px;height:14px;background:#722ed1;border-radius:1px;margin-right:8px;vertical-align:middle"></span>活跃传导链（{len(active_chains)}条）</p>\n'
        for ch in active_chains:
            cid = ch["id"]
            ci = CHAIN_CN.get(cid, {})
            cname = ci.get("name", ch.get("name", ""))
            cdesc = ci.get("desc", "")
            stress = ch.get("stress", 0)
            c = _color(stress)
            path_cn = [cn_short(nid) for nid in ch.get("path", [])]
            html += f'<div style="background:#fafafa;border-radius:8px;padding:14px;margin-bottom:10px">'
            html += f'<p style="font-size:14px;font-weight:700;color:{c};margin-bottom:6px">{cname} <span style="font-size:12px;color:#999;font-weight:400">压力 {stress:.0f}/100</span></p>'
            html += f'<p style="font-size:13px;color:#333;margin-bottom:4px">{" → ".join(path_cn)}</p>'
            if cdesc:
                html += f'<p style="font-size:12px;color:#888">{cdesc}</p>'
            html += '</div>\n'
        html += '</div>\n'

    ts = datetime.utcnow().strftime("%H:%M UTC")
    html += f'<div style="text-align:center;font-size:11px;color:#bbb;padding:20px 0">GFCRI · {report_date} {ts}</div>\n</div></body></html>'

    logger.info(f"WeChat HTML generated: {len(html)} chars")
    return html


# =========================================================================
# Zsxq Post
# =========================================================================

def generate_zsxq_post(
    gfcri_result: dict[str, Any],
    alerts: list[dict[str, Any]] | None = None,
    llm_narrative: str | None = None,
    report_date: str | None = None,
) -> str:
    report_date = report_date or date.today().isoformat()
    gfcri = gfcri_result["gfcri"]
    alert = gfcri_result["alert_level"]
    alert_label = ALERT_CN.get(alert, alert)
    sub_indices = gfcri_result.get("sub_indices", {})
    chains = gfcri_result.get("chains", [])
    contribs = gfcri_result.get("node_contributions", {})
    coherence = gfcri_result.get("coherence_multiplier", 1.0)

    anomalous = sorted(
        [(nid, info) for nid, info in contribs.items() if info.get("is_anomalous")],
        key=lambda x: abs(x[1].get("zscore", 0)), reverse=True,
    )
    active_chains = [c for c in chains if c.get("active")]
    dormant_chains = [c for c in chains if not c.get("active")]

    L = []

    # ── Header ──
    L.append(f"┌─────────────────────────────────────┐")
    L.append(f"│  GFCRI 全球金融风险指数              │")
    L.append(f"│  {report_date}                       │")
    L.append(f"│                                     │")
    L.append(f"│  风险指数: {gfcri:5.1f} / 100   【{alert_label}】     │")
    L.append(f"│  传导链共振系数: {coherence:.2f}x               │")
    L.append(f"└─────────────────────────────────────┘")
    L.append("")

    # ── 1. Narrative analysis FIRST ──
    if llm_narrative:
        L.append("━━ 1. 分析观点 ━━")
        L.append("")
        clean = llm_narrative.strip()
        char_count = 0
        for line in clean.split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("|") or line.startswith("---"):
                continue
            stripped = _md_strip(line)
            if stripped:
                L.append(f"  {stripped}")
        L.append("")

    # ── 2. Sub-indices ──
    n_si = len(sub_indices)
    section_num = 2 if llm_narrative else 1
    L.append(f"━━ {section_num}. {n_si}维风险全景 ━━")
    L.append("")
    for si_id, si in sub_indices.items():
        s = si.get("score", 0)
        name = SI_CN.get(si_id, si.get("name", si_id))
        driver_id = si.get("top_driver", "")
        driver_cn = cn_name(driver_id) if driver_id else "—"
        bar = "■" * int(s / 10) + "□" * (10 - int(s / 10))
        status = "▲" if s >= 30 else "—"
        L.append(f"  {name}  {bar}  {s:4.0f}  {status}")
        L.append(f"    └ 主因: {driver_cn}")
    L.append("")

    # ── 3. Anomalous nodes ──
    section_num += 1
    if anomalous:
        L.append(f"━━ {section_num}. 异常指标详情（{len(anomalous)}个偏离正常范围）━━")
        L.append("")
        for nid, info in anomalous:
            z = info.get("zscore", 0)
            val = info.get("current_value")
            name = cn_name(nid)
            direction = "偏高" if z > 0 else "偏低"
            severity = "严重" if abs(z) > 3 else "显著"
            val_str = f"{val:.2f}" if val is not None else "—"
            from src.data.collector import DATA_SOURCE_LABELS
            source = DATA_SOURCE_LABELS.get(nid, "yfinance")
            L.append(f"  ● {name}")
            L.append(f"    当前值: {val_str} | {direction} {abs(z):.1f}倍（{severity}偏离）")
            L.append(f"    数据源: {source}")
        L.append("")
    else:
        L.append(f"━━ {section_num}. 异常指标 ━━")
        L.append("  ✓ 全部指标均在正常范围内")
        L.append("")

    # ── Divergence (calm before the storm) ──
    divergence = gfcri_result.get("divergence", {})
    div_status = divergence.get("status", "none")
    div_details = divergence.get("details", [])
    if div_status != "none" and div_details:
        section_num += 1
        severity_labels = {"mild": "轻度", "significant": "显著", "critical": "严重"}
        sl = severity_labels.get(div_status, "")
        surface_pct = divergence.get("surface_avg", 0) * 100
        deep_pct = divergence.get("deep_avg", 0) * 100
        L.append(f"━━ {section_num}. ⚡ 暴风雨前的平静（{sl}背离）━━")
        L.append("")
        L.append(f"  表面指标压力: {surface_pct:.0f}%  vs  底层指标压力: {deep_pct:.0f}%")
        L.append(f"  底层比表面高出 {deep_pct - surface_pct:.0f} 个百分点")
        L.append("")
        for d in div_details:
            title = d.get("title", "")
            detail = _md_strip(d.get("detail", ""))
            dtype = d.get("type", "")
            icon = "🌊" if dtype == "surface_calm_deep_stress" else "🐸"
            L.append(f"  {icon} {title}")
            L.append(f"    {detail}")
            L.append("")

    # ── 4. Chains ──
    section_num += 1
    L.append(f"━━ {section_num}. 风险传导链（{len(active_chains)}条活跃 / {len(dormant_chains)}条休眠）━━")
    L.append("")

    for ch in active_chains:
        ci = CHAIN_CN.get(ch["id"], {})
        cname = ci.get("name", ch.get("name", ""))
        cdesc = ci.get("desc", "")
        stress = ch.get("stress", 0)
        strength = ch.get("path_strength", 0)
        path_cn = [cn_short(nid) for nid in ch.get("path", [])]

        L.append(f"  ▶ {cname}【活跃】")
        L.append(f"    ┌{'─' * (len('  →  '.join(path_cn)) + 2)}┐")
        L.append(f"    │ {'  →  '.join(path_cn)} │")
        L.append(f"    └{'─' * (len('  →  '.join(path_cn)) + 2)}┘")
        L.append(f"    压力: {stress:.0f}/100 | 传导强度: {strength:.3f}")
        if cdesc:
            L.append(f"    解读: {cdesc}")
        L.append("")

    if dormant_chains:
        for ch in dormant_chains:
            ci = CHAIN_CN.get(ch["id"], {})
            cname = ci.get("name", ch.get("name", ""))
            stress = ch.get("stress", 0)
            L.append(f"  ○ {cname}【休眠 压力{stress:.0f}】")
        L.append("")

    # ── 5. Alerts ──
    if alerts:
        section_num += 1
        critical = [a for a in alerts if a.get("level") in ("critical", "danger")]
        warnings = [a for a in alerts if a.get("level") == "warning"]
        L.append(f"━━ {section_num}. 风险预警（{len(critical)}条重要 + {len(warnings)}条关注）━━")
        L.append("")
        for a in critical:
            L.append(f"  ‼ {a['title']}")
            L.append(f"    {a.get('detail', '')}")
            L.append("")
        for a in warnings:
            L.append(f"  △ {a['title']}")
            L.append(f"    {a.get('detail', '')}")
            L.append("")

    # ── Footer ──
    L.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    L.append("GFCRI · 全球金融风险指数")
    n_nodes = len(contribs)
    n_chains = len(chains)
    L.append(f"{n_nodes}个实时市场指标 · {n_chains}条风险传导链")
    L.append(f"数据源: yfinance 实时行情（零模拟数据）")
    L.append(f"更新时间: {report_date}")
    L.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    text = "\n".join(L)
    logger.info(f"Zsxq post generated: {len(text)} chars")
    return text


# =========================================================================
# Share Card Image (Long-form, same content as WeChat/Zsxq)
# =========================================================================

def generate_share_card(
    gfcri_result: dict[str, Any],
    alerts: list[dict[str, Any]] | None = None,
    llm_narrative: str | None = None,
    output_path: str | None = None,
    report_date: str | None = None,
) -> str:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyBboxPatch
        import matplotlib.font_manager as fm
        import textwrap
    except ImportError:
        logger.error("matplotlib not installed")
        return ""

    report_date = report_date or date.today().isoformat()
    gfcri = gfcri_result["gfcri"]
    alert = gfcri_result["alert_level"]
    alert_label = ALERT_CN.get(alert, alert)
    sub_indices = gfcri_result.get("sub_indices", {})
    contribs = gfcri_result.get("node_contributions", {})
    chains = gfcri_result.get("chains", [])

    anomalous = sorted(
        [(nid, info) for nid, info in contribs.items() if info.get("is_anomalous")],
        key=lambda x: abs(x[1].get("zscore", 0)), reverse=True,
    )
    active_chains = [c for c in chains if c.get("active")]
    color_map = {"green": "#5de4c7", "yellow": "#ffd266", "orange": "#ff9f43", "red": "#ff5b6c"}
    main_color = color_map.get(alert, "#5de4c7")

    # Estimate figure height based on content
    h_base = 4.0  # header + sub-indices
    h_narrative = 5.0 if llm_narrative else 0
    h_alerts = 0.8 * len(alerts) if alerts else 0
    h_anomalies = 0.22 * len(anomalous)
    h_chains = 0.5 * len(active_chains)
    h_footer = 0.6
    total_h = h_base + h_narrative + h_alerts + h_anomalies + h_chains + h_footer
    total_h = max(total_h, 9.6)

    fig, ax = plt.subplots(1, 1, figsize=(5.4, total_h), dpi=200)
    fig.patch.set_facecolor("#071018")
    ax.set_facecolor("#071018")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    cjk_fonts = ["PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", "WenQuanYi Micro Hei", "SimHei"]
    fp = None
    for fn in cjk_fonts:
        try:
            test_fp = fm.FontProperties(family=fn)
            if fm.findfont(test_fp) != fm.findfont(fm.FontProperties()):
                fp = test_fp
                break
        except Exception:
            continue

    step = 1.0 / total_h * 0.28  # normalized step per line

    def t(x, y, s, size=12, color="#e0e8f0", weight="normal", ha="center"):
        props = dict(fontsize=size, color=color, fontweight=weight, ha=ha, va="center", transform=ax.transAxes)
        if fp:
            props["fontproperties"] = fp
        ax.text(x, y, s, **props)

    y = 0.97

    # Header
    t(0.5, y, "GFCRI 全球金融风险指数", size=9, color="#627588")
    y -= step * 0.7
    t(0.5, y, report_date, size=7, color="#627588")
    y -= step * 2.5
    t(0.5, y, f"{gfcri:.0f}", size=44, color=main_color, weight="bold")
    y -= step * 1.5
    t(0.5, y, alert_label, size=10, color=main_color, weight="bold")
    y -= step * 2

    # Narrative (analysis summary)
    if llm_narrative:
        t(0.5, y, "— 分析观点 —", size=8, color="#627588", weight="bold")
        y -= step * 1.2
        clean = _md_strip(llm_narrative.strip())
        lines_text = []
        for line in clean.split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("|") or line.startswith("---"):
                continue
            wrapped = textwrap.wrap(line, width=32)
            lines_text.extend(wrapped)
        for tl in lines_text:
            t(0.08, y, tl, size=6.5, color="#c8d4de", ha="left")
            y -= step * 0.8
        y -= step * 0.5

    # Sub-indices
    t(0.5, y, "— 风险全景 —", size=8, color="#627588", weight="bold")
    y -= step * 1.2
    for si_id, si in sub_indices.items():
        s = si.get("score", 0)
        name = SI_CN.get(si_id, si_id)
        c = _color(s)
        t(0.14, y, name, size=7.5, color="#627588", ha="left")
        bx, bw, bh = 0.30, 0.48, 0.006
        ax.add_patch(FancyBboxPatch((bx, y - bh/2), bw, bh, boxstyle="round,pad=0.002",
                                     facecolor="#1a2332", edgecolor="none", transform=ax.transAxes))
        fw = bw * s / 100
        if fw > 0:
            ax.add_patch(FancyBboxPatch((bx, y - bh/2), fw, bh, boxstyle="round,pad=0.002",
                                         facecolor=c, edgecolor="none", transform=ax.transAxes))
        t(0.83, y, f"{s:.0f}", size=8, color=c, ha="right")
        y -= step * 1.1
    y -= step * 0.5

    # Anomalous
    if anomalous:
        t(0.5, y, f"— 异常指标（{len(anomalous)}个）—", size=8, color="#627588", weight="bold")
        y -= step * 1.2
        for nid, info in anomalous:
            z = info.get("zscore", 0)
            c = "#ff5b6c" if abs(z) > 3 else "#ffd66b"
            name = cn_name(nid)
            if len(name) > 10:
                name = name[:9] + ".."
            direction = "偏高" if z > 0 else "偏低"
            t(0.14, y, name, size=7, color="#a9bac8", ha="left")
            t(0.85, y, f"{direction} {abs(z):.1f}倍", size=7.5, color=c, ha="right")
            y -= step * 0.9
        y -= step * 0.5

    # Chains
    if active_chains:
        t(0.5, y, f"— 活跃传导链（{len(active_chains)}条）—", size=8, color="#627588", weight="bold")
        y -= step * 1.2
        for ch in active_chains:
            ci = CHAIN_CN.get(ch["id"], {})
            cname = ci.get("name", ch.get("name", ""))
            stress = ch.get("stress", 0)
            sc = _color(stress)
            path_cn = [cn_short(nid) for nid in ch.get("path", [])]
            t(0.14, y, cname, size=7.5, color="#e0e8f0", ha="left")
            t(0.85, y, f"{stress:.0f}", size=8, color=sc, ha="right", weight="bold")
            y -= step * 0.8
            t(0.14, y, " → ".join(path_cn), size=6.5, color="#627588", ha="left")
            y -= step * 1.0
        y -= step * 0.5

    # Alerts
    if alerts:
        t(0.5, y, "— 风险预警 —", size=8, color="#627588", weight="bold")
        y -= step * 1.2
        for a in alerts:
            icon = "‼" if a.get("level") in ("critical", "danger") else "△"
            ac = "#ff5b6c" if a.get("level") in ("critical", "danger") else "#ffd66b"
            t(0.08, y, f"{icon} {a['title']}", size=7, color=ac, ha="left")
            y -= step * 0.8
            detail = a.get("detail", "")
            wrapped = textwrap.wrap(detail, width=34)
            for dl in wrapped[:3]:
                t(0.10, y, dl, size=6, color="#a9bac8", ha="left")
                y -= step * 0.7
            y -= step * 0.3

    # Footer
    n_nodes = len(contribs)
    t(0.5, max(y - step, 0.02), f"GFCRI · {n_nodes}个实时指标 · yfinance · {report_date}", size=6, color="#627588")

    if output_path is None:
        os.makedirs("/app/output", exist_ok=True)
        output_path = f"/app/output/gfcri_card_{report_date}.png"

    plt.savefig(output_path, dpi=200, bbox_inches="tight", pad_inches=0.1, facecolor="#071018")
    plt.close(fig)
    logger.info(f"Share card generated: {output_path}")
    return output_path
