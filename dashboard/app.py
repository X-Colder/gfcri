import streamlit as st
import sys

sys.path.insert(0, "/app")

st.set_page_config(page_title="GFCRI", page_icon="", layout="wide", initial_sidebar_state="expanded")

from dashboard.style import inject_css, metric_card, alert_badge, status_dot, ALERT_COLOR, COLORS, plotly_layout

inject_css()

st.markdown("# GFCRI — Global Financial Crisis Risk Index")

try:
    from src.storage.database import get_latest_daily_state, get_latest_risk_index, get_latest_report

    state = get_latest_daily_state()
    risk = get_latest_risk_index()
    report = get_latest_report()

    if not risk:
        st.info("Awaiting first analysis run.")
        st.stop()

    gfcri = float(risk.get("gfcri_value", 0))
    alert = risk.get("alert_level", "green")
    color = ALERT_COLOR.get(alert, COLORS["muted"])
    index_date = str(risk.get("index_date", ""))

    # --- Hero metrics ---
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        st.markdown(metric_card("RISK INDEX", f"{gfcri:.1f}", color), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("ALERT LEVEL", alert_badge(alert)), unsafe_allow_html=True)
    with c3:
        anomalous = state.get("anomalous_nodes", []) if state else []
        n = len(anomalous) if anomalous else 0
        ac = COLORS["red"] if n >= 3 else COLORS["yellow"] if n >= 1 else COLORS["green"]
        st.markdown(metric_card("ANOMALIES", f"{n}", ac), unsafe_allow_html=True)
    with c4:
        chains = risk.get("chain_details") or []
        active = sum(1 for c in chains if c.get("active"))
        cc = COLORS["red"] if active >= 4 else COLORS["yellow"] if active >= 2 else COLORS["green"]
        st.markdown(metric_card("ACTIVE CHAINS", f"{active}/{len(chains)}", cc), unsafe_allow_html=True)

    st.caption(f"Last updated: {index_date}")

    # --- Sub-indices ---
    st.markdown("---")
    st.markdown("### Sub-Indices")

    import plotly.graph_objects as go

    si_details = risk.get("sub_index_details") or {}
    si_names = {
        "SI_RATES": "Rates", "SI_FX": "FX", "SI_EQUITY": "Equity",
        "SI_CREDIT": "Credit", "SI_BANKING": "Banking", "SI_CONSUMER": "Consumer",
        "SI_SENTIMENT": "Sentiment",
    }

    if si_details:
        names = []
        scores = []
        colors = []
        for si_id in ["SI_SENTIMENT", "SI_CONSUMER", "SI_BANKING", "SI_CREDIT", "SI_EQUITY", "SI_FX", "SI_RATES"]:
            si = si_details.get(si_id)
            if si:
                names.append(si_names.get(si_id, si_id))
                s = si.get("score", 0)
                scores.append(s)
                colors.append(COLORS["red"] if s >= 50 else COLORS["orange"] if s >= 30 else COLORS["yellow"] if s >= 15 else COLORS["green"])

        fig = go.Figure(go.Bar(
            x=scores, y=names, orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=[f"{s:.0f}" for s in scores], textposition="auto",
            textfont=dict(size=11, color="#e6edf3"),
        ))
        fig.update_layout(**plotly_layout(height=250))
        fig.update_xaxes(range=[0, 100], title_text="")
        fig.update_yaxes(title_text="")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # --- Alerts ---
    if report and report.get("report_markdown"):
        markdown_text = report["report_markdown"]
        alert_section = ""
        for line in markdown_text.split("\n"):
            if "风险预警" in line:
                idx = markdown_text.index(line)
                end_idx = markdown_text.find("\n---", idx + 1)
                alert_section = markdown_text[idx:end_idx] if end_idx > 0 else markdown_text[idx:idx+1500]
                break

        if alert_section:
            st.markdown("---")
            with st.expander("Alerts", expanded=True):
                st.markdown(alert_section)

    st.markdown("---")
    st.caption("Navigate via sidebar: Daily Briefing | Causal Graph | Inference | Risk Index")

except Exception as e:
    st.error(f"Connection error: {e}")
