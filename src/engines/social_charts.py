"""
Chart generator for social content.

Generates matplotlib charts optimized for mobile viewing:
  - Sub-index radar chart
  - Z-score heatmap
  - Transmission chain flow diagram
  - Historical GFCRI trend (if data available)

All charts use AIS color scheme (#071018 bg, #5de4c7 primary).
"""

from __future__ import annotations

import os
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch
import numpy as np
from loguru import logger

from src.i18n import cn_name, cn_short, SI_CN, CHAIN_CN, ALERT_CN

_BG = "#071018"
_SURFACE = "#0d1822"
_BORDER = "#87a3b830"
_TEXT = "#eff8ff"
_MUTED = "#627588"
_GREEN = "#5de4c7"
_YELLOW = "#ffd66b"
_ORANGE = "#ffb86b"
_RED = "#ff7a8a"
_BLUE = "#7aa7ff"


def _get_font():
    for fn in ["PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", "WenQuanYi Micro Hei", "SimHei"]:
        try:
            fp = fm.FontProperties(family=fn)
            if fm.findfont(fp) != fm.findfont(fm.FontProperties()):
                return fp
        except Exception:
            continue
    return fm.FontProperties()


def _score_color(s: float) -> str:
    if s >= 75: return _RED
    if s >= 50: return _ORANGE
    if s >= 25: return _YELLOW
    return _GREEN


def generate_subindex_chart(
    sub_indices: dict[str, Any],
    output_path: str,
) -> str:
    fp = _get_font()
    si_order = list(sub_indices.keys())
    names = [SI_CN.get(sid, sid) for sid in si_order]
    scores = [sub_indices[sid].get("score", 0) for sid in si_order]
    colors = [_score_color(s) for s in scores]

    fig, ax = plt.subplots(figsize=(6, 3.2), dpi=150)
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)

    y_pos = range(len(names) - 1, -1, -1)
    bars = ax.barh(y_pos, scores, height=0.6, color=colors, edgecolor="none")

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels([names[len(names) - 1 - i] for i in range(len(names))],
                        fontproperties=fp, fontsize=9, color=_TEXT)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.tick_params(axis="x", colors=_MUTED, labelsize=8)

    ax.axvline(x=25, color=_YELLOW, linestyle="--", alpha=0.3, linewidth=0.8)
    ax.axvline(x=50, color=_ORANGE, linestyle="--", alpha=0.3, linewidth=0.8)
    ax.axvline(x=75, color=_RED, linestyle="--", alpha=0.3, linewidth=0.8)

    for i, (bar, score) in enumerate(zip(bars, [scores[len(scores) - 1 - j] for j in range(len(scores))])):
        ax.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height() / 2,
                f"{score:.0f}", va="center", ha="left", fontsize=9,
                color=_score_color(score), fontweight="bold")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(_MUTED)
    ax.spines["left"].set_visible(False)

    plt.tight_layout(pad=0.5)
    plt.savefig(output_path, dpi=150, facecolor=_BG, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    logger.info(f"Sub-index chart saved: {output_path}")
    return output_path


def generate_zscore_chart(
    node_contributions: dict[str, Any],
    output_path: str,
    top_n: int = 15,
) -> str:
    fp = _get_font()

    items = sorted(node_contributions.items(), key=lambda x: abs(x[1].get("zscore", 0)), reverse=True)[:top_n]

    names = [cn_short(nid) for nid, _ in items]
    zscores = [info.get("zscore", 0) for _, info in items]
    colors = [_RED if abs(z) > 3 else _ORANGE if abs(z) > 2 else _MUTED for z in zscores]

    fig, ax = plt.subplots(figsize=(6, max(2.5, len(items) * 0.28)), dpi=150)
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)

    y_pos = range(len(names) - 1, -1, -1)
    ax.barh(list(y_pos), [zscores[len(zscores) - 1 - i] for i in range(len(zscores))],
            height=0.55,
            color=[colors[len(colors) - 1 - i] for i in range(len(colors))],
            edgecolor="none")

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels([names[len(names) - 1 - i] for i in range(len(names))],
                        fontproperties=fp, fontsize=8, color=_TEXT)
    ax.tick_params(axis="x", colors=_MUTED, labelsize=8)

    ax.axvline(x=2, color=_ORANGE, linestyle="--", alpha=0.4, linewidth=0.8)
    ax.axvline(x=-2, color=_ORANGE, linestyle="--", alpha=0.4, linewidth=0.8)
    ax.axvline(x=0, color=_MUTED, linestyle="-", alpha=0.3, linewidth=0.5)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(_MUTED)
    ax.spines["left"].set_visible(False)

    plt.tight_layout(pad=0.5)
    plt.savefig(output_path, dpi=150, facecolor=_BG, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    logger.info(f"Z-score chart saved: {output_path}")
    return output_path


def generate_chain_chart(
    chains: list[dict[str, Any]],
    output_path: str,
) -> str:
    fp = _get_font()
    active = [c for c in chains if c.get("active")]
    if not active:
        active = chains[:3]

    n_chains = min(len(active), 6)
    fig, ax = plt.subplots(figsize=(6, n_chains * 0.9 + 0.5), dpi=150)
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    y_start = 0.92
    row_h = 0.85 / n_chains

    for i, ch in enumerate(active[:n_chains]):
        y = y_start - i * row_h
        ci = CHAIN_CN.get(ch["id"], {})
        cname = ci.get("name", ch.get("name", ""))
        stress = ch.get("stress", 0)
        path = ch.get("path", [])
        sc = _score_color(stress)

        ax.text(0.02, y, f"{cname}", fontproperties=fp, fontsize=9,
                color=sc, fontweight="bold", va="center", transform=ax.transAxes)
        ax.text(0.98, y, f"{stress:.0f}", fontsize=10, color=sc,
                fontweight="bold", ha="right", va="center", transform=ax.transAxes)

        path_cn = [cn_short(nid) for nid in path]
        n_nodes = len(path_cn)
        node_w = 0.12
        gap = 0.04
        total_w = n_nodes * node_w + (n_nodes - 1) * gap
        x_start = 0.5 - total_w / 2
        node_y = y - row_h * 0.45

        for j, label in enumerate(path_cn):
            nx = x_start + j * (node_w + gap)
            ax.add_patch(FancyBboxPatch(
                (nx, node_y - 0.025), node_w, 0.05,
                boxstyle="round,pad=0.008", facecolor=_SURFACE, edgecolor=sc,
                linewidth=1, transform=ax.transAxes,
            ))
            ax.text(nx + node_w / 2, node_y, label, fontproperties=fp,
                    fontsize=7, color=_TEXT, ha="center", va="center",
                    transform=ax.transAxes)

            if j < n_nodes - 1:
                arrow_x = nx + node_w + 0.005
                ax.annotate("", xy=(arrow_x + gap - 0.01, node_y),
                           xytext=(arrow_x, node_y),
                           arrowprops=dict(arrowstyle="->", color=sc, lw=1.2),
                           transform=ax.transAxes)

    plt.savefig(output_path, dpi=150, facecolor=_BG, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    logger.info(f"Chain chart saved: {output_path}")
    return output_path


def generate_data_table_image(
    node_contributions: dict[str, Any],
    output_path: str,
    top_n: int = 15,
) -> str:
    fp = _get_font()

    items = sorted(node_contributions.items(),
                   key=lambda x: abs(x[1].get("zscore", 0)), reverse=True)[:top_n]

    fig, ax = plt.subplots(figsize=(6, max(3, len(items) * 0.32 + 1)), dpi=150)
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)
    ax.axis("off")

    headers = ["指标", "当前值", "偏离(σ)", "状态"]
    col_x = [0.02, 0.30, 0.58, 0.80]
    y_start = 0.95
    row_h = 0.85 / (len(items) + 1)

    for j, h in enumerate(headers):
        ax.text(col_x[j], y_start, h, fontproperties=fp, fontsize=8,
                color=_MUTED, fontweight="bold", va="center", transform=ax.transAxes)

    ax.plot([0.01, 0.99], [y_start - row_h * 0.4, y_start - row_h * 0.4],
            color=_MUTED, linewidth=0.5, alpha=0.5, transform=ax.transAxes)

    for i, (nid, info) in enumerate(items):
        y = y_start - (i + 1) * row_h
        name = cn_short(nid)
        val = info.get("current_value")
        z = info.get("zscore", 0)
        anomalous = info.get("is_anomalous", False)

        val_str = f"{val:.2f}" if val is not None and abs(val) < 10000 else (f"{val:.0f}" if val is not None else "—")
        z_str = f"{z:+.1f}"
        status = "异常" if anomalous else "正常"
        z_color = _RED if abs(z) > 3 else _ORANGE if abs(z) > 2 else _GREEN
        status_color = _RED if anomalous else _GREEN

        ax.text(col_x[0], y, name, fontproperties=fp, fontsize=8, color=_TEXT, va="center", transform=ax.transAxes)
        ax.text(col_x[1], y, val_str, fontsize=8, color=_TEXT, va="center", transform=ax.transAxes)
        ax.text(col_x[2], y, z_str, fontsize=8, color=z_color, fontweight="bold", va="center", transform=ax.transAxes)
        ax.text(col_x[3], y, status, fontproperties=fp, fontsize=8, color=status_color, va="center", transform=ax.transAxes)

        if i < len(items) - 1:
            ax.plot([0.01, 0.99], [y - row_h * 0.4, y - row_h * 0.4],
                    color=_MUTED, linewidth=0.3, alpha=0.3, transform=ax.transAxes)

    plt.savefig(output_path, dpi=150, facecolor=_BG, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    logger.info(f"Data table image saved: {output_path}")
    return output_path


def generate_all_charts(
    gfcri_result: dict[str, Any],
    output_dir: str = "/app/output",
    report_date: str | None = None,
) -> dict[str, str]:
    from datetime import date as _date
    report_date = report_date or _date.today().isoformat()
    os.makedirs(output_dir, exist_ok=True)

    paths = {}

    sub_indices = gfcri_result.get("sub_indices", {})
    if sub_indices:
        p = os.path.join(output_dir, f"chart_subindex_{report_date}.png")
        generate_subindex_chart(sub_indices, p)
        paths["subindex"] = p

    contribs = gfcri_result.get("node_contributions", {})
    if contribs:
        p = os.path.join(output_dir, f"chart_zscore_{report_date}.png")
        generate_zscore_chart(contribs, p)
        paths["zscore"] = p

        p2 = os.path.join(output_dir, f"chart_datatable_{report_date}.png")
        generate_data_table_image(contribs, p2)
        paths["datatable"] = p2

    chains = gfcri_result.get("chains", [])
    if chains:
        p = os.path.join(output_dir, f"chart_chains_{report_date}.png")
        generate_chain_chart(chains, p)
        paths["chains"] = p

    logger.info(f"Generated {len(paths)} charts for {report_date}")
    return paths
