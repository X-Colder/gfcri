import streamlit as st
import sys

sys.path.insert(0, "/app")

st.set_page_config(page_title="Causal Graph — GFCRI", page_icon="", layout="wide")

from dashboard.style import inject_css, COLORS, plotly_layout

inject_css()

st.markdown("# Causal Graph")

try:
    import pandas as pd
    from src.models.graph import build_initial_causal_graph

    graph = build_initial_causal_graph()

    st.caption(f"v{graph.version}  |  {len(graph.nodes)} nodes  |  {len(graph.edges)} edges  |  DAG: {graph.is_dag()}")

    tab1, tab2, tab3 = st.tabs(["Network", "Nodes", "Edges"])

    with tab1:
        try:
            from pyvis.network import Network
            import tempfile

            net = Network(height="550px", width="100%", bgcolor="#0e1117", font_color="#c9d1d9", directed=True)
            net.toggle_physics(True)
            net.set_options("""
            {
                "nodes": {"font": {"size": 11, "face": "Inter, sans-serif"}},
                "edges": {"arrows": {"to": {"scaleFactor": 0.6}}, "smooth": {"type": "curvedCW", "roundness": 0.15}},
                "physics": {"barnesHut": {"gravitationalConstant": -3000, "springLength": 120}}
            }
            """)

            asset_colors = {
                "FX": "#58a6ff", "RATES": "#d29922", "EQUITY": "#2ea043",
                "CREDIT": "#f85149", "COMMODITY": "#bc8cff", "MACRO": "#8b949e",
                "SENTIMENT": "#f778ba",
            }

            for nid, node in graph.nodes.items():
                color = asset_colors.get(node.asset_class.value, "#8b949e")
                net.add_node(nid, label=nid, title=f"{node.display_name}\n{node.asset_class.value} | {node.geography}",
                             color=color, size=16, borderWidth=0)

            for eid, edge in graph.edges.items():
                if edge.is_deprecated:
                    continue
                color = "rgba(46,160,67,0.53)" if edge.causal_strength > 0 else "rgba(248,81,73,0.53)"
                width = max(1, abs(edge.causal_strength) * 4)
                net.add_edge(edge.source_node, edge.target_node,
                             title=f"{edge.causal_strength:+.2f} | {edge.mechanism.value}",
                             color=color, width=width)

            with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
                net.save_graph(f.name)
                with open(f.name, "r", encoding="utf-8") as rf:
                    html = rf.read()
            st.components.v1.html(html, height=570, scrolling=False)
        except ImportError:
            st.warning("pyvis not installed.")

    with tab2:
        nodes_data = []
        for nid, node in graph.nodes.items():
            nodes_data.append({
                "ID": nid, "Name": node.display_name,
                "Type": node.node_type.value, "Class": node.asset_class.value,
                "Geo": node.geography, "Source": node.data_source,
            })
        st.dataframe(pd.DataFrame(nodes_data), use_container_width=True, hide_index=True)

    with tab3:
        edges_data = []
        for eid, edge in graph.edges.items():
            edges_data.append({
                "Source": edge.source_node, "Target": edge.target_node,
                "Strength": f"{edge.causal_strength:+.3f}",
                "Confidence": f"{edge.strength_confidence:.2f}",
                "Lag (d)": edge.peak_lag_days,
                "Mechanism": edge.mechanism.value,
            })
        st.dataframe(pd.DataFrame(edges_data), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")
    import traceback
    st.code(traceback.format_exc())
