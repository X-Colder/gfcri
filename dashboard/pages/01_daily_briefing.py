import streamlit as st
import sys

sys.path.insert(0, "/app")

st.set_page_config(page_title="Daily Briefing — GFCRI", page_icon="", layout="wide")

from dashboard.style import inject_css, metric_card, alert_badge, ALERT_COLOR, COLORS, plotly_layout

inject_css()

st.markdown("# Daily Briefing")

try:
    import pandas as pd
    import plotly.graph_objects as go
    from src.storage.database import get_daily_states, get_latest_risk_index, get_latest_report

    states = get_daily_states(limit=30)
    risk = get_latest_risk_index()
    report = get_latest_report()

    if not states:
        st.info("No data yet.")
        st.stop()

    latest = states[0]

    # --- Header row ---
    if risk:
        gfcri = float(risk.get("gfcri_value", 0))
        alert = risk.get("alert_level", "green")
        color = ALERT_COLOR.get(alert, COLORS["muted"])

        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
        with c1:
            st.markdown(metric_card("GFCRI", f"{gfcri:.1f}", color), unsafe_allow_html=True)
        with c2:
            st.markdown(metric_card("STATUS", alert_badge(alert)), unsafe_allow_html=True)
        with c3:
            anomalous = latest.get("anomalous_nodes", [])
            st.markdown(metric_card("ANOMALIES", str(len(anomalous) if anomalous else 0)), unsafe_allow_html=True)
        with c4:
            st.markdown(metric_card("DATE", str(latest.get("state_date", ""))), unsafe_allow_html=True)
        with c5:
            coherence = float(risk.get("coherence_multiplier", 1.0))
            st.markdown(metric_card("COHERENCE", f"{coherence:.2f}x"), unsafe_allow_html=True)

    st.markdown("---")

    # --- Sub-indices from JSONB ---
    si_details = risk.get("sub_index_details") or {} if risk else {}
    if si_details:
        st.markdown("### Sub-Index Breakdown")
        si_names = {
            "SI_RATES": "Rates", "SI_FX": "FX", "SI_EQUITY": "Equity",
            "SI_CREDIT": "Credit", "SI_BANKING": "Banking", "SI_CONSUMER": "Consumer",
            "SI_SENTIMENT": "Sentiment",
        }
        cols = st.columns(len(si_details))
        for col, (si_id, si_data) in zip(cols, si_details.items()):
            with col:
                s = si_data.get("score", 0)
                c = COLORS["red"] if s >= 50 else COLORS["orange"] if s >= 30 else COLORS["yellow"] if s >= 15 else COLORS["green"]
                st.markdown(metric_card(si_names.get(si_id, si_id), f"{s:.0f}", c), unsafe_allow_html=True)

    st.markdown("---")

    # --- Z-Score heatmap ---
    zscores = latest.get("node_zscores", {})
    if zscores:
        st.markdown("### Z-Score Monitor")
        sorted_z = sorted(zscores.items(), key=lambda x: abs(x[1]), reverse=True)
        names = [k for k, v in sorted_z]
        values = [v for k, v in sorted_z]
        bar_colors = [COLORS["red"] if abs(v) > 3 else COLORS["orange"] if abs(v) > 2 else COLORS["muted"] for v in values]

        fig = go.Figure(go.Bar(
            x=values, y=names, orientation="h",
            marker=dict(color=bar_colors, line=dict(width=0)),
            text=[f"{v:+.1f}" for v in values], textposition="outside",
            textfont=dict(size=10, color="#8b949e"),
        ))
        fig.update_layout(**plotly_layout(height=max(200, len(names) * 22)))
        fig.add_vline(x=2, line_dash="dash", line_color=COLORS["orange"], opacity=0.5)
        fig.add_vline(x=-2, line_dash="dash", line_color=COLORS["orange"], opacity=0.5)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")

    # --- Full report ---
    if report and report.get("report_markdown"):
        st.markdown("### Analysis Report")
        with st.expander("Full Report", expanded=True):
            st.markdown(report["report_markdown"])

    # --- 7-day trend ---
    if len(states) > 1:
        st.markdown("---")
        st.markdown("### GFCRI Trend")
        trend_dates = [str(s["state_date"]) for s in reversed(states)]
        trend_values = [
            float(s.get("alert_level", "green") == "red") * 3 +
            float(s.get("alert_level", "green") == "orange") * 2 +
            float(s.get("alert_level", "green") == "yellow") * 1
            for s in reversed(states)
        ]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_dates, y=trend_values, mode="lines+markers",
            line=dict(color=COLORS["blue"], width=2),
            marker=dict(size=6),
        ))
        fig.update_layout(**plotly_layout(height=200))
        fig.update_yaxes(tickvals=[0, 1, 2, 3], ticktext=["LOW", "MOD", "ELEV", "CRIT"])
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

except Exception as e:
    st.error(f"Error: {e}")
