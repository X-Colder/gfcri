import streamlit as st
import sys

sys.path.insert(0, "/app")

st.set_page_config(page_title="Risk Index — GFCRI", page_icon="", layout="wide")

from dashboard.style import inject_css, metric_card, alert_badge, ALERT_COLOR, COLORS, plotly_layout

inject_css()

st.markdown("# Risk Index Detail")

try:
    import pandas as pd
    import plotly.graph_objects as go
    from src.storage.database import get_risk_index_history, get_latest_risk_index

    risk = get_latest_risk_index()
    history = get_risk_index_history(limit=30)

    if not risk:
        st.info("No risk index data yet.")
        st.stop()

    gfcri = float(risk.get("gfcri_value", 0))
    alert = risk.get("alert_level", "green")
    color = ALERT_COLOR.get(alert, COLORS["muted"])

    # --- Gauge ---
    c1, c2 = st.columns([1, 2])
    with c1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=gfcri,
            number=dict(font=dict(size=48, color=color)),
            gauge=dict(
                axis=dict(range=[0, 100], tickwidth=1, tickcolor="#2d333b", dtick=25),
                bar=dict(color=color, thickness=0.3),
                bgcolor="#1a1d24",
                borderwidth=0,
                steps=[
                    dict(range=[0, 25], color="rgba(46,160,67,0.13)"),
                    dict(range=[25, 50], color="rgba(210,153,34,0.13)"),
                    dict(range=[50, 75], color="rgba(219,109,40,0.13)"),
                    dict(range=[75, 100], color="rgba(248,81,73,0.13)"),
                ],
                threshold=dict(line=dict(color=color, width=3), thickness=0.8, value=gfcri),
            ),
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=250, margin=dict(l=30, r=30, t=30, b=10),
            font=dict(color="#8b949e"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        # Sub-index cards
        si_details = risk.get("sub_index_details") or {}
        si_names = {
            "SI_RATES": "Rates", "SI_FX": "FX", "SI_EQUITY": "Equity",
            "SI_CREDIT": "Credit", "SI_BANKING": "Banking", "SI_CONSUMER": "Consumer",
            "SI_SENTIMENT": "Sentiment",
        }
        if si_details:
            items = list(si_details.items())
            row1 = items[:4]
            row2 = items[4:]
            cols1 = st.columns(len(row1))
            for col, (si_id, si_data) in zip(cols1, row1):
                with col:
                    s = si_data.get("score", 0)
                    c = COLORS["red"] if s >= 50 else COLORS["orange"] if s >= 30 else COLORS["yellow"] if s >= 15 else COLORS["green"]
                    driver = si_data.get("top_driver", "")
                    st.markdown(metric_card(si_names.get(si_id, si_id), f"{s:.0f}"), unsafe_allow_html=True)
                    st.caption(f"Driver: {driver}" if driver else "")
            if row2:
                cols2 = st.columns(len(row2))
                for col, (si_id, si_data) in zip(cols2, row2):
                    with col:
                        s = si_data.get("score", 0)
                        st.markdown(metric_card(si_names.get(si_id, si_id), f"{s:.0f}"), unsafe_allow_html=True)
                        driver = si_data.get("top_driver", "")
                        st.caption(f"Driver: {driver}" if driver else "")

    st.markdown("---")

    # --- Transmission chains ---
    st.markdown("### Transmission Chains")
    chain_details = risk.get("chain_details") or []
    if chain_details:
        chains_data = []
        for c in chain_details:
            stress = c.get("stress", 0)
            active = c.get("active", False)
            status_color = COLORS["red"] if active else COLORS["green"]
            chains_data.append({
                "Chain": c.get("name", ""),
                "Path": " → ".join(c.get("path", [])),
                "Stress": stress,
                "Strength": c.get("path_strength", 0),
                "Status": "ACTIVE" if active else "dormant",
            })
        df = pd.DataFrame(chains_data)
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={
                         "Stress": st.column_config.ProgressColumn("Stress", min_value=0, max_value=100, format="%d"),
                     })

    # --- Historical trend ---
    if len(history) > 1:
        st.markdown("---")
        st.markdown("### Historical Trend")

        dates = [str(h["index_date"]) for h in reversed(history)]
        values = [float(h["gfcri_value"]) for h in reversed(history)]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=values, mode="lines+markers",
            line=dict(color=COLORS["blue"], width=2),
            marker=dict(size=5),
            fill="tozeroy", fillcolor="rgba(88,166,255,0.07)",
        ))
        fig.add_hline(y=25, line_dash="dash", line_color=COLORS["yellow"], opacity=0.4)
        fig.add_hline(y=50, line_dash="dash", line_color=COLORS["orange"], opacity=0.4)
        fig.add_hline(y=75, line_dash="dash", line_color=COLORS["red"], opacity=0.4)
        fig.update_layout(**plotly_layout("GFCRI", height=280))
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # --- Node detail table ---
    st.markdown("---")
    st.markdown("### Node Detail")
    node_contribs = risk.get("node_contributions") or {}
    if node_contribs:
        rows = []
        for nid, info in node_contribs.items():
            rows.append({
                "Node": nid,
                "Name": info.get("display_name", ""),
                "Value": info.get("current_value"),
                "Z-Score": round(info.get("zscore", 0), 2),
                "Anomaly": round(info.get("anomaly_score", 0), 2),
                "Flag": "ANOMALY" if info.get("is_anomalous") else "",
            })
        df = pd.DataFrame(rows).sort_values("Anomaly", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
