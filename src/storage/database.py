from datetime import datetime
from typing import Optional

import psycopg2
from psycopg2.extras import Json, RealDictCursor
from loguru import logger

from src.config import settings


def get_connection():
    return psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    )


def wait_for_db(max_retries: int = 30, delay: float = 2.0):
    import time

    for i in range(max_retries):
        try:
            conn = get_connection()
            conn.close()
            logger.info("Database connection established")
            return True
        except psycopg2.OperationalError:
            logger.warning(f"Database not ready, retrying ({i + 1}/{max_retries})...")
            time.sleep(delay)
    raise RuntimeError("Could not connect to database")


def save_daily_state(
    state_date: str,
    graph_version: str,
    current_regime: str,
    node_values: dict,
    node_zscores: dict,
    anomalous_nodes: list[str],
    alert_level: str = "green",
    inference_summary: Optional[dict] = None,
    active_paths: Optional[dict] = None,
    alert_details: Optional[dict] = None,
):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO daily_graph_state
                    (state_date, graph_version, current_regime, node_values,
                     node_zscores, anomalous_nodes, active_paths,
                     inference_summary, alert_level, alert_details)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (state_date) DO UPDATE SET
                    graph_version = EXCLUDED.graph_version,
                    current_regime = EXCLUDED.current_regime,
                    node_values = EXCLUDED.node_values,
                    node_zscores = EXCLUDED.node_zscores,
                    anomalous_nodes = EXCLUDED.anomalous_nodes,
                    active_paths = EXCLUDED.active_paths,
                    inference_summary = EXCLUDED.inference_summary,
                    alert_level = EXCLUDED.alert_level,
                    alert_details = EXCLUDED.alert_details
                """,
                (
                    state_date,
                    graph_version,
                    current_regime,
                    Json(node_values),
                    Json(node_zscores),
                    anomalous_nodes,
                    Json(active_paths),
                    Json(inference_summary),
                    alert_level,
                    Json(alert_details),
                ),
            )
        conn.commit()
        logger.info(f"Daily state saved for {state_date}")
    finally:
        conn.close()


def get_latest_daily_state() -> Optional[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM daily_graph_state ORDER BY state_date DESC LIMIT 1"
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def get_daily_states(limit: int = 30) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM daily_graph_state ORDER BY state_date DESC LIMIT %s",
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def save_inference_log(
    graph_version: str,
    inference_type: str,
    source_node: str,
    target_node: str,
    point_estimate: float,
    ci_lower: float,
    ci_upper: float,
    confidence: float,
    method_used: str,
    query_description: str = "",
    natural_language_summary: str = "",
    triggered_by: str = "daily_run",
):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO causal_inference_log
                    (graph_version, inference_type, source_node, target_node,
                     query_description, point_estimate, ci_lower, ci_upper,
                     confidence, natural_language_summary, method_used, triggered_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    graph_version,
                    inference_type,
                    source_node,
                    target_node,
                    query_description,
                    point_estimate,
                    ci_lower,
                    ci_upper,
                    confidence,
                    natural_language_summary,
                    method_used,
                    triggered_by,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def get_inference_history(
    source_node: Optional[str] = None,
    target_node: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            conditions = []
            params = []
            if source_node:
                conditions.append("source_node = %s")
                params.append(source_node)
            if target_node:
                conditions.append("target_node = %s")
                params.append(target_node)
            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            cur.execute(
                f"SELECT * FROM causal_inference_log {where} ORDER BY inference_date DESC LIMIT %s",
                params + [limit],
            )
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def save_risk_index(
    index_date: str,
    gfcri_value: float,
    alert_level: str,
    si_rates: float,
    si_fx: float,
    si_equity: float,
    si_credit: float,
    si_sentiment: float,
    sub_index_details: Optional[dict] = None,
    active_chains: Optional[dict] = None,
    chain_details: Optional[dict] = None,
    coherence_multiplier: float = 1.0,
    node_contributions: Optional[dict] = None,
):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO daily_risk_index
                    (index_date, gfcri_value, alert_level,
                     si_rates, si_fx, si_equity, si_credit, si_sentiment,
                     sub_index_details, active_chains, chain_details,
                     coherence_multiplier, node_contributions)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (index_date) DO UPDATE SET
                    gfcri_value = EXCLUDED.gfcri_value,
                    alert_level = EXCLUDED.alert_level,
                    si_rates = EXCLUDED.si_rates,
                    si_fx = EXCLUDED.si_fx,
                    si_equity = EXCLUDED.si_equity,
                    si_credit = EXCLUDED.si_credit,
                    si_sentiment = EXCLUDED.si_sentiment,
                    sub_index_details = EXCLUDED.sub_index_details,
                    active_chains = EXCLUDED.active_chains,
                    chain_details = EXCLUDED.chain_details,
                    coherence_multiplier = EXCLUDED.coherence_multiplier,
                    node_contributions = EXCLUDED.node_contributions
                """,
                (
                    index_date,
                    gfcri_value,
                    alert_level,
                    si_rates,
                    si_fx,
                    si_equity,
                    si_credit,
                    si_sentiment,
                    Json(sub_index_details),
                    Json(active_chains),
                    Json(chain_details),
                    coherence_multiplier,
                    Json(node_contributions),
                ),
            )
        conn.commit()
        logger.info(f"Risk index saved for {index_date}: GFCRI={gfcri_value:.1f}")
    finally:
        conn.close()


def get_latest_risk_index() -> Optional[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM daily_risk_index ORDER BY index_date DESC LIMIT 1"
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def get_risk_index_history(limit: int = 30) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM daily_risk_index ORDER BY index_date DESC LIMIT %s",
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def save_daily_report(
    report_date: str,
    gfcri_value: float,
    alert_level: str,
    report_markdown: str,
    report_metadata: Optional[dict] = None,
    llm_narrative: Optional[str] = None,
    generation_time_ms: int = 0,
):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO daily_reports
                    (report_date, gfcri_value, alert_level, report_markdown,
                     report_metadata, llm_narrative, generation_time_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (report_date) DO UPDATE SET
                    gfcri_value = EXCLUDED.gfcri_value,
                    alert_level = EXCLUDED.alert_level,
                    report_markdown = EXCLUDED.report_markdown,
                    report_metadata = EXCLUDED.report_metadata,
                    llm_narrative = EXCLUDED.llm_narrative,
                    generation_time_ms = EXCLUDED.generation_time_ms
                """,
                (
                    report_date,
                    gfcri_value,
                    alert_level,
                    report_markdown,
                    Json(report_metadata),
                    llm_narrative,
                    generation_time_ms,
                ),
            )
        conn.commit()
        logger.info(f"Daily report saved for {report_date}")
    finally:
        conn.close()


def get_latest_report() -> Optional[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM daily_reports ORDER BY report_date DESC LIMIT 1"
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()
