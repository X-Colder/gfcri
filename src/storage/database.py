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
    divergence: Optional[dict] = None,
    undercurrent_boost: float = 0.0,
    trade_spillover: Optional[dict] = None,
    trade_spillover_boost: float = 0.0,
):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE daily_risk_index ADD COLUMN IF NOT EXISTS divergence JSONB")
            cur.execute("ALTER TABLE daily_risk_index ADD COLUMN IF NOT EXISTS undercurrent_boost NUMERIC(6, 2)")
            cur.execute("ALTER TABLE daily_risk_index ADD COLUMN IF NOT EXISTS trade_spillover JSONB")
            cur.execute("ALTER TABLE daily_risk_index ADD COLUMN IF NOT EXISTS trade_spillover_boost NUMERIC(6, 2)")
            cur.execute(
                """
                INSERT INTO daily_risk_index
                    (index_date, gfcri_value, alert_level,
                     si_rates, si_fx, si_equity, si_credit, si_sentiment,
                     sub_index_details, active_chains, chain_details,
                     coherence_multiplier, node_contributions, divergence,
                     undercurrent_boost, trade_spillover, trade_spillover_boost)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    node_contributions = EXCLUDED.node_contributions,
                    divergence = EXCLUDED.divergence,
                    undercurrent_boost = EXCLUDED.undercurrent_boost,
                    trade_spillover = EXCLUDED.trade_spillover,
                    trade_spillover_boost = EXCLUDED.trade_spillover_boost
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
                    Json(divergence),
                    undercurrent_boost,
                    Json(trade_spillover),
                    trade_spillover_boost,
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


def _ensure_institutional_radar_tables(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS institutional_radar_items (
            item_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            source_name TEXT NOT NULL,
            source_tier TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT,
            url TEXT NOT NULL,
            published_at TIMESTAMPTZ,
            risk_themes JSONB,
            affected_nodes JSONB,
            affected_chains JSONB,
            risk_direction TEXT,
            confidence NUMERIC(5, 4),
            importance_score NUMERIC(6, 2),
            importance_reasons JSONB,
            first_seen TIMESTAMPTZ DEFAULT NOW(),
            last_seen TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS institutional_radar_source_health (
            source_id TEXT PRIMARY KEY,
            source_name TEXT NOT NULL,
            source_tier TEXT NOT NULL,
            url TEXT NOT NULL,
            status TEXT NOT NULL,
            last_checked_at TIMESTAMPTZ DEFAULT NOW(),
            last_success_at TIMESTAMPTZ,
            last_error TEXT,
            item_count INTEGER DEFAULT 0,
            latency_ms INTEGER DEFAULT 0
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_institutional_radar_published ON institutional_radar_items (published_at DESC NULLS LAST)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_institutional_radar_importance ON institutional_radar_items (importance_score DESC NULLS LAST)")


def save_institutional_radar_snapshot(data: dict) -> None:
    """Persist institutional radar metadata and source health.

    The radar stores public metadata and GFCRI mapping only; it does not store
    copyrighted full report bodies.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            _ensure_institutional_radar_tables(cur)
            sources = {s.get("id"): s for s in data.get("sources") or []}
            error_by_source = {e.get("source"): e.get("error") for e in data.get("errors") or []}
            source_item_counts: dict[str, int] = {}
            for item in data.get("items") or []:
                source_item_counts[item.get("source_id")] = source_item_counts.get(item.get("source_id"), 0) + 1
                cur.execute(
                    """
                    INSERT INTO institutional_radar_items
                        (item_id, source_id, source_name, source_tier, title, summary, url,
                         published_at, risk_themes, affected_nodes, affected_chains,
                         risk_direction, confidence, importance_score, importance_reasons,
                         first_seen, last_seen)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (item_id) DO UPDATE SET
                        source_id = EXCLUDED.source_id,
                        source_name = EXCLUDED.source_name,
                        source_tier = EXCLUDED.source_tier,
                        title = EXCLUDED.title,
                        summary = EXCLUDED.summary,
                        url = EXCLUDED.url,
                        published_at = EXCLUDED.published_at,
                        risk_themes = EXCLUDED.risk_themes,
                        affected_nodes = EXCLUDED.affected_nodes,
                        affected_chains = EXCLUDED.affected_chains,
                        risk_direction = EXCLUDED.risk_direction,
                        confidence = EXCLUDED.confidence,
                        importance_score = EXCLUDED.importance_score,
                        importance_reasons = EXCLUDED.importance_reasons,
                        last_seen = NOW()
                    """,
                    (
                        item.get("id"),
                        item.get("source_id"),
                        item.get("source"),
                        item.get("source_tier"),
                        item.get("title"),
                        item.get("summary", ""),
                        item.get("url"),
                        item.get("published_at"),
                        Json(item.get("risk_themes") or []),
                        Json(item.get("affected_nodes") or []),
                        Json(item.get("affected_chains") or []),
                        item.get("risk_direction"),
                        item.get("confidence", 0),
                        item.get("importance_score", 0),
                        Json(item.get("importance_reasons") or []),
                    ),
                )

            for source_id, source in sources.items():
                error = error_by_source.get(source.get("name"))
                status = "error" if error else "ok"
                item_count = source_item_counts.get(source_id, 0)
                cur.execute(
                    """
                    INSERT INTO institutional_radar_source_health
                        (source_id, source_name, source_tier, url, status, last_checked_at,
                         last_success_at, last_error, item_count, latency_ms)
                    VALUES (%s, %s, %s, %s, %s, NOW(), CASE WHEN %s THEN NOW() ELSE NULL END, %s, %s, %s)
                    ON CONFLICT (source_id) DO UPDATE SET
                        source_name = EXCLUDED.source_name,
                        source_tier = EXCLUDED.source_tier,
                        url = EXCLUDED.url,
                        status = EXCLUDED.status,
                        last_checked_at = NOW(),
                        last_success_at = CASE WHEN EXCLUDED.status = 'ok' THEN NOW() ELSE institutional_radar_source_health.last_success_at END,
                        last_error = EXCLUDED.last_error,
                        item_count = EXCLUDED.item_count,
                        latency_ms = EXCLUDED.latency_ms
                    """,
                    (
                        source_id,
                        source.get("name"),
                        source.get("tier"),
                        source.get("url"),
                        status,
                        status == "ok",
                        error,
                        item_count,
                        int((data.get("source_latency_ms") or {}).get(source_id, 0)),
                    ),
                )
        conn.commit()
    finally:
        conn.close()


def get_institutional_radar_items(limit: int = 50) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _ensure_institutional_radar_tables(cur)
            cur.execute(
                """
                SELECT *
                FROM institutional_radar_items
                ORDER BY published_at DESC NULLS LAST, importance_score DESC NULLS LAST, last_seen DESC
                LIMIT %s
                """,
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_institutional_radar_source_health() -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            _ensure_institutional_radar_tables(cur)
            cur.execute(
                """
                SELECT *
                FROM institutional_radar_source_health
                ORDER BY source_tier, source_name
                """
            )
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def save_causal_candidates(
    run_date: str,
    trigger: dict,
    candidates: list[dict],
):
    """Persist AI/rule-generated causal graph expansion candidates.

    Candidates are not promoted into the core graph here. This table is the
    governance registry for watchlist/candidate/promotion review.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS causal_candidate_edges (
                    candidate_id TEXT PRIMARY KEY,
                    first_seen DATE NOT NULL,
                    last_seen DATE NOT NULL,
                    trigger JSONB,
                    title TEXT NOT NULL,
                    cause_node TEXT,
                    effect_node TEXT,
                    mechanism TEXT,
                    observable_tests JSONB,
                    falsification JSONB,
                    scores JSONB,
                    overall_confidence NUMERIC(5, 4),
                    decision TEXT,
                    graph_status TEXT,
                    validation_note TEXT,
                    seen_count INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """
            )
            for c in candidates:
                cur.execute(
                    """
                    INSERT INTO causal_candidate_edges
                        (candidate_id, first_seen, last_seen, trigger, title,
                         cause_node, effect_node, mechanism, observable_tests,
                         falsification, scores, overall_confidence, decision,
                         graph_status, validation_note, seen_count, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, NOW())
                    ON CONFLICT (candidate_id) DO UPDATE SET
                        last_seen = EXCLUDED.last_seen,
                        trigger = EXCLUDED.trigger,
                        title = EXCLUDED.title,
                        cause_node = EXCLUDED.cause_node,
                        effect_node = EXCLUDED.effect_node,
                        mechanism = EXCLUDED.mechanism,
                        observable_tests = EXCLUDED.observable_tests,
                        falsification = EXCLUDED.falsification,
                        scores = EXCLUDED.scores,
                        overall_confidence = EXCLUDED.overall_confidence,
                        decision = EXCLUDED.decision,
                        graph_status = EXCLUDED.graph_status,
                        validation_note = EXCLUDED.validation_note,
                        seen_count = causal_candidate_edges.seen_count + 1,
                        updated_at = NOW()
                    """,
                    (
                        c.get("id"),
                        run_date,
                        run_date,
                        Json(trigger),
                        c.get("title", ""),
                        c.get("cause_node"),
                        c.get("effect_node"),
                        c.get("mechanism", ""),
                        Json(c.get("observable_tests") or []),
                        Json(c.get("falsification") or []),
                        Json(c.get("scores") or {}),
                        c.get("overall_confidence", 0),
                        c.get("decision"),
                        c.get("graph_status"),
                        c.get("validation_note", ""),
                    ),
                )
        conn.commit()
    finally:
        conn.close()


def get_causal_candidates(limit: int = 50) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS causal_candidate_edges (
                    candidate_id TEXT PRIMARY KEY,
                    first_seen DATE NOT NULL,
                    last_seen DATE NOT NULL,
                    trigger JSONB,
                    title TEXT NOT NULL,
                    cause_node TEXT,
                    effect_node TEXT,
                    mechanism TEXT,
                    observable_tests JSONB,
                    falsification JSONB,
                    scores JSONB,
                    overall_confidence NUMERIC(5, 4),
                    decision TEXT,
                    graph_status TEXT,
                    validation_note TEXT,
                    seen_count INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                SELECT *
                FROM causal_candidate_edges
                ORDER BY overall_confidence DESC NULLS LAST, updated_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def update_causal_candidate_review(
    candidate_id: str,
    review_status: str,
    review_note: str = "",
    reviewed_by: str = "local",
) -> Optional[dict]:
    allowed = {"watchlist", "candidate_graph", "eligible_for_promotion", "rejected"}
    if review_status not in allowed:
        raise ValueError(f"Invalid review_status: {review_status}")

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS causal_candidate_edges (
                    candidate_id TEXT PRIMARY KEY,
                    first_seen DATE NOT NULL,
                    last_seen DATE NOT NULL,
                    trigger JSONB,
                    title TEXT NOT NULL,
                    cause_node TEXT,
                    effect_node TEXT,
                    mechanism TEXT,
                    observable_tests JSONB,
                    falsification JSONB,
                    scores JSONB,
                    overall_confidence NUMERIC(5, 4),
                    decision TEXT,
                    graph_status TEXT,
                    validation_note TEXT,
                    seen_count INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """
            )
            cur.execute("ALTER TABLE causal_candidate_edges ADD COLUMN IF NOT EXISTS review_status TEXT")
            cur.execute("ALTER TABLE causal_candidate_edges ADD COLUMN IF NOT EXISTS review_note TEXT")
            cur.execute("ALTER TABLE causal_candidate_edges ADD COLUMN IF NOT EXISTS reviewed_by TEXT")
            cur.execute("ALTER TABLE causal_candidate_edges ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP")
            cur.execute(
                """
                UPDATE causal_candidate_edges
                SET review_status = %s,
                    review_note = %s,
                    reviewed_by = %s,
                    reviewed_at = NOW(),
                    graph_status = %s,
                    updated_at = NOW()
                WHERE candidate_id = %s
                RETURNING *
                """,
                (review_status, review_note, reviewed_by, review_status, candidate_id),
            )
            row = cur.fetchone()
        conn.commit()
        return dict(row) if row else None
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
