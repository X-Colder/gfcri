import os
import json
import time
from datetime import date

from loguru import logger

from src.config import settings
from src.storage.database import (
    save_daily_state,
    save_inference_log,
    save_risk_index,
    save_daily_report,
)


def _adapt_prev_risk(prev_risk: dict | None) -> dict | None:
    """Convert DB risk_index row to gfcri_result shape for orchestrator delta comparison."""
    if not prev_risk:
        return None
    return {
        "gfcri": float(prev_risk.get("gfcri_value", 0)),
        "alert_level": prev_risk.get("alert_level", "green"),
        "node_contributions": prev_risk.get("node_contributions") or {},
        "chains": prev_risk.get("chain_details") or [],
        "sub_indices": prev_risk.get("sub_index_details") or {},
    }


def _render_context_story(signals) -> str | None:
    """Render context signals as Markdown without LLM — structured factual output."""
    high_signals = [s for s in signals if s.significance == "high"]
    medium_signals = [s for s in signals if s.significance == "medium"]
    show = high_signals + medium_signals[:3]
    if not show:
        return None

    lines = ["### 🔍 数据背后的故事", ""]
    for s in show:
        lines.append(f"#### {s.title}")
        lines.append("")
        lines.append("| | |")
        lines.append("|---|---|")
        lines.append(f"| 发生了什么 | {s.what_happened} |")
        lines.append(f"| 数据反应 | {s.data_reaction} |")
        if s.deep_meaning:
            lines.append(f"| 深层含义 | {s.deep_meaning} |")
        lines.append("")
    return "\n".join(lines)


def run_daily_analysis():
    logger.info("=== Starting daily analysis job ===")
    today = date.today().isoformat()

    try:
        from src.models.graph import build_initial_causal_graph
        from src.data.collector import MarketDataCollector
        from src.engines.reasoning import CausalReasoningEngine
        from src.engines.risk_index import GFCRIEngine
        from src.engines.report_generator import render_gfcri_report, get_upcoming_events

        graph = build_initial_causal_graph()
        collector = MarketDataCollector()

        # --- Phase 1: Data collection ---
        logger.info("Fetching market data...")
        collector.update_node_values(graph)

        logger.info("Fetching historical data...")
        historical_data = collector.fetch_historical_data(period="2y")

        node_values = {}
        node_zscores = {}
        anomalous_nodes = []
        for nid, node in graph.nodes.items():
            if node.current_value is not None:
                node_values[nid] = node.current_value
            if node.value_zscore is not None:
                node_zscores[nid] = node.value_zscore
            if node.is_anomalous:
                anomalous_nodes.append(nid)

        fred_current = getattr(collector, '_fred_current', {})
        node_values.update(fred_current)

        # --- Phase 2: GFCRI computation ---
        logger.info("Computing GFCRI risk index...")
        gfcri_engine = GFCRIEngine(graph)
        gfcri_result = gfcri_engine.compute()
        alert_level = gfcri_result["alert_level"]

        # --- Phase 2.5: Crisis distance & stress test ---
        crisis_report = None
        stress_results = None
        hidden_risk_report = None
        try:
            from src.engines.crisis_distance import CrisisDistanceEngine

            extra_data = {}
            extra_data.update(getattr(collector, '_fred_current', {}))
            try:
                from src.data.china_macro import fetch_china_macro
                extra_data.update(fetch_china_macro())
            except Exception:
                pass

            crisis_engine = CrisisDistanceEngine(graph, extra_data)
            crisis_report = crisis_engine.compute().to_dict()
            logger.info(f"Crisis distance: overall={crisis_report['overall_distance']:.1f}%")
        except Exception as e:
            logger.warning(f"Crisis distance failed (non-fatal): {e}")

        try:
            from src.engines.stress_test import StressTestEngine
            stress_engine = StressTestEngine(graph, historical_data if not historical_data.empty else None)
            stress_results = [r.to_dict() for r in stress_engine.run_all_scenarios()]
            logger.info(f"Stress test: {len(stress_results)} scenarios computed")
        except Exception as e:
            logger.warning(f"Stress test failed (non-fatal): {e}")

        # Cache results to JSON for fast API reads
        try:
            output_dir = os.environ.get("OUTPUT_DIR", "/app/output")
            os.makedirs(output_dir, exist_ok=True)
            if crisis_report:
                with open(os.path.join(output_dir, "crisis_distance_cache.json"), "w") as f:
                    json.dump(crisis_report, f)
            if stress_results:
                with open(os.path.join(output_dir, "stress_test_cache.json"), "w") as f:
                    json.dump(stress_results, f)
        except Exception as e:
            logger.debug(f"Cache write failed (non-fatal): {e}")

        # --- Phase 3: Path analysis ---
        inference_summary = {}
        structural_breaks = []

        if not historical_data.empty:
            engine = CausalReasoningEngine(graph, historical_data)

            key_pairs = [
                ("dxy", "krw_usd"),
                ("krw_usd", "kospi"),
                ("ust_10y", "dxy"),
                ("vix", "kospi"),
            ]

            for src, tgt in key_pairs:
                try:
                    result = engine.path_analysis(src, tgt)
                    paths = result.get("paths", [])
                    dominant = paths[0] if paths else None
                    net_strength = sum(p["strength"] for p in paths)
                    inference_summary[f"{src}->{tgt}"] = {
                        "total_paths": result.get("total_paths", 0),
                        "dominant_path": dominant["path_str"] if dominant else "N/A",
                        "net_strength": net_strength,
                    }
                    if paths:
                        save_inference_log(
                            graph_version=graph.version,
                            inference_type="path_analysis",
                            source_node=src,
                            target_node=tgt,
                            point_estimate=net_strength,
                            ci_lower=0,
                            ci_upper=0,
                            confidence=0.7,
                            method_used="path_strength_product",
                            triggered_by="daily_run",
                        )
                except Exception as e:
                    logger.warning(f"Inference {src}->{tgt} failed: {e}")

            # --- Phase 4: Structural break detection ---
            try:
                from src.engines.discovery import CausalDiscoveryEngine

                discovery = CausalDiscoveryEngine(graph, historical_data)
                structural_breaks = discovery.detect_structural_breaks()
            except Exception as e:
                logger.warning(f"Structural break detection failed: {e}")

        # --- Phase 5: Event calendar ---
        upcoming_events = get_upcoming_events(days=7)

        # --- Phase 5.5: Risk monitoring & alerts ---
        alerts_markdown = ""
        prev_risk = None
        prev_state = None
        try:
            from src.engines.risk_monitor import RiskMonitor, format_alerts_markdown
            from src.storage.database import get_latest_risk_index, get_latest_daily_state, get_connection
            from psycopg2.extras import RealDictCursor

            # Get PREVIOUS day's data (exclude today to avoid self-comparison)
            conn = get_connection()
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT * FROM daily_risk_index WHERE index_date < %s ORDER BY index_date DESC LIMIT 1",
                        (today,),
                    )
                    row = cur.fetchone()
                    prev_risk = dict(row) if row else None
                    cur.execute(
                        "SELECT * FROM daily_graph_state WHERE state_date < %s ORDER BY state_date DESC LIMIT 1",
                        (today,),
                    )
                    row2 = cur.fetchone()
                    prev_state = dict(row2) if row2 else None
            finally:
                conn.close()

            prev_zscores = prev_state.get("node_zscores", {}) if prev_state else {}

            monitor = RiskMonitor(
                graph=graph,
                gfcri_result=gfcri_result,
                prev_gfcri=prev_risk,
                prev_node_zscores=prev_zscores,
                structural_breaks=structural_breaks,
                upcoming_events=upcoming_events,
            )
            alerts = monitor.run_all_checks()
            if alerts:
                alerts_markdown = format_alerts_markdown(alerts)
                for a in alerts:
                    log_fn = logger.warning if a.level == "warning" else logger.error
                    log_fn(f"ALERT [{a.level}] {a.title}")
        except Exception as e:
            logger.warning(f"Risk monitoring failed (non-fatal): {e}")

        # --- Phase 5.8: Context signal derivation ---
        context_signals = []
        context_story_md = None
        try:
            from src.engines.context_signals import ContextSignalEngine
            from src.engines.hidden_risk import HiddenRiskEngine

            oecd_rates = {}
            try:
                from src.data.oecd_macro import fetch_oecd_rates
                oecd_rates = fetch_oecd_rates()
            except Exception:
                pass

            prev_node_vals = prev_state.get("node_values", {}) if prev_state else None
            prev_fred_vals = {k: v for k, v in (prev_node_vals or {}).items() if k.startswith("fred_")}

            ctx_engine = ContextSignalEngine(
                fred_current=fred_current,
                fred_history=getattr(collector, '_fred_history', {}),
                china_current=getattr(collector, '_china_current', {}),
                oecd_rates=oecd_rates,
                node_values=node_values,
                node_zscores=node_zscores,
                prev_node_values=prev_node_vals,
                prev_fred=prev_fred_vals or None,
                gfcri_value=gfcri_result["gfcri"],
                prev_gfcri_value=float(prev_risk["gfcri_value"]) if prev_risk and prev_risk.get("gfcri_value") else None,
            )
            context_signals = ctx_engine.derive_all_signals()
            high_count = sum(1 for s in context_signals if s.significance == "high")
            logger.info(f"Context signals: {len(context_signals)} derived ({high_count} high)")

            # Hidden risk inference
            hidden_engine = HiddenRiskEngine(
                node_values=node_values,
                node_zscores=node_zscores,
                fred_current=fred_current,
                fred_history=getattr(collector, '_fred_history', {}),
                prev_node_values=prev_node_vals,
                prev_fred=prev_fred_vals or None,
            )
            hidden_risk_report = hidden_engine.compute()
            logger.info(f"Hidden risk: +{hidden_risk_report.total_boost:.1f} boost, {len(hidden_risk_report.signals)} signals")

            context_story_md = _render_context_story(context_signals)
        except Exception as e:
            logger.warning(f"Context signal derivation failed (non-fatal): {e}")

        # --- Phase 6: LLM narrative generation ---
        llm_narrative = None
        report_gen_start = time.time()
        if settings.anthropic_api_key:
            try:
                from src.engines.orchestrator import LLMCausalOrchestrator
                from src.engines.discovery import CausalDiscoveryEngine

                discovery_engine = CausalDiscoveryEngine(graph, historical_data) if not historical_data.empty else None
                reasoning_engine = CausalReasoningEngine(graph, historical_data) if not historical_data.empty else None

                orchestrator = LLMCausalOrchestrator(
                    graph,
                    reasoning_engine,
                    discovery_engine,
                )
                llm_narrative = orchestrator.generate_gfcri_report(
                    gfcri_result=gfcri_result,
                    inference_summary=inference_summary,
                    structural_breaks=structural_breaks,
                    upcoming_events=upcoming_events,
                    fred_data=getattr(collector, '_fred_current', None),
                    china_data=getattr(collector, '_china_current', None),
                    prev_gfcri_result=_adapt_prev_risk(prev_risk),
                )
                logger.info("LLM narrative generated successfully")

                # Save English narrative
                en_narrative = getattr(orchestrator, '_last_en_narrative', '')
                if en_narrative:
                    try:
                        output_dir = os.environ.get("OUTPUT_DIR", "/app/output")
                        os.makedirs(output_dir, exist_ok=True)
                        with open(os.path.join(output_dir, f"narrative_en_{today}.md"), "w", encoding="utf-8") as f:
                            f.write(en_narrative)
                        logger.info(f"English narrative saved: {len(en_narrative)} chars")
                    except Exception as e:
                        logger.debug(f"English narrative save failed: {e}")
            except Exception as e:
                logger.warning(f"LLM narrative generation failed (non-fatal): {e}")

        # --- Phase 7: Render full report ---
        report_markdown = render_gfcri_report(
            gfcri_result=gfcri_result,
            inference_summary=inference_summary,
            structural_breaks=structural_breaks,
            llm_narrative=llm_narrative,
            alerts_markdown=alerts_markdown,
            report_date=today,
            graph_version=graph.version,
            crisis_report=crisis_report,
            stress_results=stress_results,
            context_story=context_story_md,
        )
        report_gen_ms = int((time.time() - report_gen_start) * 1000)

        # --- Phase 8: Persist everything ---
        save_daily_state(
            state_date=today,
            graph_version=graph.version,
            current_regime="normal",
            node_values=node_values,
            node_zscores=node_zscores,
            anomalous_nodes=anomalous_nodes,
            alert_level=alert_level,
            inference_summary=inference_summary,
        )

        sub = gfcri_result["sub_indices"]
        save_risk_index(
            index_date=today,
            gfcri_value=gfcri_result["gfcri"],
            alert_level=alert_level,
            si_rates=sub.get("SI_RATES", {}).get("score", 0),
            si_fx=sub.get("SI_FX", {}).get("score", 0),
            si_equity=sub.get("SI_EQUITY", {}).get("score", 0),
            si_credit=sub.get("SI_CREDIT", {}).get("score", 0),
            si_sentiment=sub.get("SI_SENTIMENT", {}).get("score", 0),
            sub_index_details=sub,
            active_chains=[c for c in gfcri_result["chains"] if c["active"]],
            chain_details=gfcri_result["chains"],
            coherence_multiplier=gfcri_result["coherence_multiplier"],
            node_contributions=gfcri_result.get("node_contributions"),
            divergence=gfcri_result.get("divergence"),
            undercurrent_boost=gfcri_result.get("undercurrent_boost", 0),
            trade_spillover=gfcri_result.get("trade_spillover"),
            trade_spillover_boost=gfcri_result.get("trade_spillover_boost", 0),
        )

        save_daily_report(
            report_date=today,
            gfcri_value=gfcri_result["gfcri"],
            alert_level=alert_level,
            report_markdown=report_markdown,
            report_metadata={
                "upcoming_events": upcoming_events,
                "structural_breaks_count": len(
                    [b for b in structural_breaks if b.get("break_detected")]
                ),
            },
            llm_narrative=llm_narrative,
            generation_time_ms=report_gen_ms,
        )

        # --- Phase 9: Generate social content ---
        try:
            from src.engines.social_content import (
                generate_wechat_html, generate_zsxq_post, generate_share_card,
            )

            alert_dicts = []
            if alerts_markdown:
                from src.engines.risk_monitor import RiskMonitor, format_alerts_markdown
                monitor = RiskMonitor(
                    graph=graph, gfcri_result=gfcri_result,
                    prev_gfcri=None, prev_node_zscores={},
                    structural_breaks=structural_breaks,
                    upcoming_events=upcoming_events,
                )
                raw_alerts = monitor.run_all_checks()
                alert_dicts = [a.to_dict() for a in raw_alerts]

            prev_gfcri_value = float(prev_risk["gfcri_value"]) if prev_risk and prev_risk.get("gfcri_value") else None
            wechat_html = generate_wechat_html(
                gfcri_result, alerts=alert_dicts,
                llm_narrative=llm_narrative, report_date=today,
                prev_gfcri=prev_gfcri_value,
            )
            zsxq_text = generate_zsxq_post(
                gfcri_result, alerts=alert_dicts,
                llm_narrative=llm_narrative, report_date=today,
            )
            card_path = generate_share_card(
                gfcri_result, alerts=alert_dicts,
                llm_narrative=llm_narrative, report_date=today,
            )

            os.makedirs("/app/output", exist_ok=True)
            with open(f"/app/output/wechat_{today}.html", "w", encoding="utf-8") as f:
                f.write(wechat_html)
            with open(f"/app/output/zsxq_{today}.txt", "w", encoding="utf-8") as f:
                f.write(zsxq_text)

            # Generate data analysis charts
            try:
                from src.engines.social_charts import generate_all_charts
                chart_paths = generate_all_charts(gfcri_result, report_date=today)
            except Exception as ce:
                logger.warning(f"Chart generation failed (non-fatal): {ce}")
                chart_paths = {}

            logger.info(
                f"Social content generated: wechat={len(wechat_html)}chars, "
                f"zsxq={len(zsxq_text)}chars, card={card_path}, "
                f"charts={len(chart_paths)}"
            )
        except Exception as e:
            logger.warning(f"Social content generation failed (non-fatal): {e}")

        # --- Phase 10: Auto-publish to WeChat ---
        try:
            if settings.wechat_auto_publish and settings.wechat_app_id:
                from src.publishers.wechat import WechatPublisher

                publisher = WechatPublisher(settings)
                title = f"GFCRI 风险日报 | {today}"
                publish_id = publisher.publish_article(title=title, content=wechat_html)
                if publish_id:
                    logger.info(f"WeChat auto-publish succeeded: {publish_id}")
                else:
                    logger.warning("WeChat auto-publish returned no publish_id")
        except Exception as e:
            logger.warning(f"WeChat auto-publish failed (non-fatal): {e}")

        logger.info(
            f"Daily analysis completed: GFCRI={gfcri_result['gfcri']:.1f}/100, "
            f"alert={alert_level}, anomalous={anomalous_nodes}, "
            f"active_chains={gfcri_result['active_chain_count']}"
        )

    except Exception as e:
        logger.error(f"Daily analysis failed: {e}")
        raise
