import streamlit as st
import sys

sys.path.insert(0, "/app")

st.set_page_config(page_title="Inference — GFCRI", page_icon="", layout="wide")

from dashboard.style import inject_css, metric_card, COLORS, plotly_layout

inject_css()

st.markdown("# Causal Inference")

try:
    import pandas as pd
    from src.models.graph import build_initial_causal_graph
    from src.data.collector import MarketDataCollector
    from src.engines.reasoning import CausalReasoningEngine

    graph = build_initial_causal_graph()
    node_ids = sorted(graph.nodes.keys())
    node_labels = {nid: f"{nid} ({graph.nodes[nid].display_name})" for nid in node_ids}

    with st.sidebar:
        st.markdown("### Parameters")
        source = st.selectbox("Source (cause)", node_ids, index=node_ids.index("dxy") if "dxy" in node_ids else 0)
        target = st.selectbox("Target (effect)", node_ids, index=node_ids.index("krw_usd") if "krw_usd" in node_ids else 1)
        inference_type = st.radio("Type", ["Path Analysis", "Observational", "Interventional", "Confounding"])
        run = st.button("Run Inference", type="primary", use_container_width=True)

    if run:
        with st.spinner("Fetching data..."):
            collector = MarketDataCollector()
            historical_data = collector.fetch_historical_data(period="2y")

            if historical_data.empty:
                st.error("No historical data available.")
                st.stop()

            engine = CausalReasoningEngine(graph, historical_data)

            if inference_type == "Path Analysis":
                result = engine.path_analysis(source, target)
                paths = result.get("paths", [])

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(metric_card("PATHS FOUND", str(len(paths))), unsafe_allow_html=True)
                with c2:
                    net = sum(p["strength"] for p in paths) if paths else 0
                    c = COLORS["red"] if net < -0.2 else COLORS["green"] if net > 0.2 else COLORS["muted"]
                    st.markdown(metric_card("NET STRENGTH", f"{net:.4f}", c), unsafe_allow_html=True)
                with c3:
                    dom = paths[0]["path_str"] if paths else "—"
                    st.markdown(metric_card("DOMINANT PATH", dom), unsafe_allow_html=True)

                if paths:
                    st.markdown("---")
                    df = pd.DataFrame([{
                        "Path": p["path_str"],
                        "Strength": p["strength"],
                        "Lag (d)": p["total_lag_days"],
                        "Hops": len(p["path"]) - 1,
                    } for p in paths])
                    st.dataframe(df, use_container_width=True, hide_index=True)

            elif inference_type == "Observational":
                current_val = historical_data[source].iloc[-1] if source in historical_data.columns else 100
                with st.sidebar:
                    shock_pct = st.slider("Shock (%)", -20, 20, 5)
                shocked_val = current_val * (1 + shock_pct / 100)
                result = engine.observational_inference(source, target, shocked_val)

                c1, c2, c3 = st.columns(3)
                with c1:
                    pe = result.get("point_estimate")
                    st.markdown(metric_card("ESTIMATE", f"{pe:.4f}" if pe else "N/A"), unsafe_allow_html=True)
                with c2:
                    st.markdown(metric_card("R-SQUARED", f"{result.get('r_squared', 0):.3f}"), unsafe_allow_html=True)
                with c3:
                    st.markdown(metric_card("CONFIDENCE", f"{result.get('confidence', 0):.2f}"), unsafe_allow_html=True)

                st.markdown("---")
                st.caption(result.get("natural_language_summary", ""))

            elif inference_type == "Interventional":
                current_val = historical_data[source].iloc[-1] if source in historical_data.columns else 100
                with st.sidebar:
                    intervention_val = st.number_input("do(X) value", value=float(current_val))
                result = engine.interventional_inference(source, target, intervention_val)

                c1, c2, c3 = st.columns(3)
                with c1:
                    pe = result.get("point_estimate")
                    st.markdown(metric_card("CAUSAL ESTIMATE", f"{pe:.4f}" if pe else "N/A"), unsafe_allow_html=True)
                with c2:
                    st.markdown(metric_card("BACKDOOR", "Yes" if result.get("backdoor_used") else "No"), unsafe_allow_html=True)
                with c3:
                    adj = result.get("adjustment_set", [])
                    st.markdown(metric_card("ADJUSTMENT SET", ", ".join(adj) if adj else "None"), unsafe_allow_html=True)

                st.markdown("---")
                st.caption(result.get("natural_language_summary", ""))

            elif inference_type == "Confounding":
                result = engine.confounding_detection(source, target)

                c1, c2, c3 = st.columns(3)
                with c1:
                    raw = result.get("raw_correlation", 0)
                    st.markdown(metric_card("RAW CORRELATION", f"{raw:.4f}"), unsafe_allow_html=True)
                with c2:
                    tested = result.get("confounders_tested", [])
                    partial = tested[0].get("partial_correlation", raw) if tested else raw
                    st.markdown(metric_card("PARTIAL CORR", f"{partial:.4f}"), unsafe_allow_html=True)
                with c3:
                    detected = result.get("confounding_detected", False)
                    c = COLORS["red"] if detected else COLORS["green"]
                    st.markdown(metric_card("CONFOUNDING", "DETECTED" if detected else "NOT FOUND", c), unsafe_allow_html=True)

                strongest = result.get("strongest_confounder")
                if strongest:
                    st.caption(f"Strongest confounder: {strongest}")

    else:
        st.caption("Select source/target nodes and inference type, then click Run Inference.")

        st.markdown("---")
        st.markdown("### Inference History")
        try:
            from src.storage.database import get_inference_history
            history = get_inference_history(limit=20)
            if history:
                df = pd.DataFrame(history)[["inference_date", "inference_type", "source_node", "target_node", "point_estimate", "confidence"]]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.caption("No inference history.")
        except Exception:
            st.caption("Database not connected.")

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
