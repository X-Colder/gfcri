"""Shared styles and helpers for the GFCRI dashboard."""

import streamlit as st

COLORS = {
    "bg": "#0e1117",
    "card": "#1a1d24",
    "border": "#2d333b",
    "text": "#e6edf3",
    "muted": "#8b949e",
    "green": "#2ea043",
    "yellow": "#d29922",
    "orange": "#db6d28",
    "red": "#f85149",
    "blue": "#58a6ff",
    "purple": "#bc8cff",
}

ALERT_COLOR = {
    "green": COLORS["green"],
    "yellow": COLORS["yellow"],
    "orange": COLORS["orange"],
    "red": COLORS["red"],
}

ALERT_LABEL = {
    "green": "LOW",
    "yellow": "MODERATE",
    "orange": "ELEVATED",
    "red": "CRITICAL",
}


def inject_css():
    st.markdown("""<style>
    [data-testid="stAppViewContainer"] { background: #0e1117; }
    [data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #2d333b; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #8b949e; font-size: 0.85rem; }
    h1 { font-size: 1.6rem !important; font-weight: 600 !important; letter-spacing: -0.02em; color: #e6edf3 !important; }
    h2 { font-size: 1.2rem !important; font-weight: 600 !important; color: #e6edf3 !important; }
    h3 { font-size: 1.0rem !important; font-weight: 600 !important; color: #c9d1d9 !important; text-transform: uppercase; letter-spacing: 0.05em; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.08em; color: #8b949e !important; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; max-width: 1200px; }
    [data-testid="stDataFrame"] { border: 1px solid #2d333b; border-radius: 6px; }
    div[data-testid="stExpander"] { border: 1px solid #2d333b; border-radius: 6px; }
    .metric-card { background: #161b22; border: 1px solid #2d333b; border-radius: 8px; padding: 16px 20px; text-align: center; }
    .metric-card .value { font-size: 2rem; font-weight: 700; color: #e6edf3; line-height: 1.2; }
    .metric-card .label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: #8b949e; margin-bottom: 4px; }
    .alert-badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.05em; }
    .status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
    hr { border-color: #2d333b !important; margin: 1rem 0 !important; }
    </style>""", unsafe_allow_html=True)


def metric_card(label, value, color=None):
    c = color or COLORS["text"]
    return f"""<div class="metric-card">
        <div class="label">{label}</div>
        <div class="value" style="color:{c}">{value}</div>
    </div>"""


def alert_badge(level):
    color = ALERT_COLOR.get(level, COLORS["muted"])
    label = ALERT_LABEL.get(level, level.upper())
    return f'<span class="alert-badge" style="background:{color}22;color:{color};border:1px solid {color}44">{label}</span>'


def status_dot(level):
    color = ALERT_COLOR.get(level, COLORS["muted"])
    return f'<span class="status-dot" style="background:{color}"></span>'


def plotly_layout(title=None, height=300):
    layout = dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=20, t=40 if title else 20, b=30),
        height=height,
        font=dict(family="Inter, -apple-system, sans-serif", size=12, color="#8b949e"),
        xaxis=dict(gridcolor="#2d333b", zerolinecolor="#2d333b"),
        yaxis=dict(gridcolor="#2d333b", zerolinecolor="#2d333b"),
    )
    if title:
        layout["title"] = dict(text=title, font=dict(size=14, color="#c9d1d9"), x=0)
    return layout
