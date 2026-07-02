-- Causal Graph Version Store
CREATE TABLE IF NOT EXISTS causal_graph_versions (
    version_id      VARCHAR(50) PRIMARY KEY,
    parent_version  VARCHAR(50) REFERENCES causal_graph_versions(version_id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      VARCHAR(100) NOT NULL,
    change_type     VARCHAR(50) NOT NULL,
    change_summary  TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,
    approved_by     VARCHAR(100),
    approved_at     TIMESTAMPTZ,
    graph_snapshot  JSONB NOT NULL,
    diff_from_parent JSONB
);

-- Node History
CREATE TABLE IF NOT EXISTS causal_nodes_history (
    record_id       BIGSERIAL PRIMARY KEY,
    graph_version   VARCHAR(50) NOT NULL REFERENCES causal_graph_versions(version_id),
    node_id         VARCHAR(100) NOT NULL,
    node_type       VARCHAR(50) NOT NULL,
    asset_class     VARCHAR(50) NOT NULL,
    geography       VARCHAR(20),
    display_name    VARCHAR(200),
    description     TEXT,
    data_source     VARCHAR(500),
    effective_from  TIMESTAMPTZ NOT NULL,
    effective_to    TIMESTAMPTZ,
    metadata        JSONB
);

-- Edge History (core: tracks causal strength evolution)
CREATE TABLE IF NOT EXISTS causal_edges_history (
    record_id           BIGSERIAL PRIMARY KEY,
    graph_version       VARCHAR(50) NOT NULL REFERENCES causal_graph_versions(version_id),
    edge_id             VARCHAR(200) NOT NULL,
    source_node         VARCHAR(100) NOT NULL,
    target_node         VARCHAR(100) NOT NULL,
    causal_strength     NUMERIC(8, 4) NOT NULL,
    strength_confidence NUMERIC(5, 4) NOT NULL,
    strength_ci_lower   NUMERIC(8, 4),
    strength_ci_upper   NUMERIC(8, 4),
    min_lag_days        INTEGER,
    max_lag_days        INTEGER,
    peak_lag_days       INTEGER,
    mechanism           VARCHAR(100),
    evidence_type       VARCHAR(50),
    validation_p_value  NUMERIC(8, 6),
    num_supporting_events INTEGER DEFAULT 0,
    is_deprecated       BOOLEAN DEFAULT FALSE,
    effective_from      TIMESTAMPTZ NOT NULL,
    effective_to        TIMESTAMPTZ,
    change_reason       TEXT,
    change_trigger      VARCHAR(100),
    UNIQUE(edge_id, effective_from)
);

-- Inference Log
CREATE TABLE IF NOT EXISTS causal_inference_log (
    inference_id        BIGSERIAL PRIMARY KEY,
    inference_date      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    graph_version       VARCHAR(50) NOT NULL,
    inference_type      VARCHAR(50) NOT NULL,
    source_node         VARCHAR(100) NOT NULL,
    target_node         VARCHAR(100) NOT NULL,
    query_description   TEXT,
    point_estimate      NUMERIC(12, 6),
    ci_lower            NUMERIC(12, 6),
    ci_upper            NUMERIC(12, 6),
    confidence          NUMERIC(5, 4),
    confounders_adjusted TEXT[],
    active_paths        JSONB,
    natural_language_summary TEXT,
    warnings            TEXT[],
    method_used         VARCHAR(200),
    triggered_by        VARCHAR(100),
    report_id           VARCHAR(100)
);

-- Structural Break Events
CREATE TABLE IF NOT EXISTS structural_break_events (
    break_id            BIGSERIAL PRIMARY KEY,
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    edge_id             VARCHAR(200) NOT NULL,
    source_node         VARCHAR(100) NOT NULL,
    target_node         VARCHAR(100) NOT NULL,
    break_date          DATE NOT NULL,
    pre_break_coeff     NUMERIC(8, 4) NOT NULL,
    post_break_coeff    NUMERIC(8, 4) NOT NULL,
    significance        NUMERIC(8, 6) NOT NULL,
    regime_name         VARCHAR(200),
    regime_interpretation TEXT,
    status              VARCHAR(50) DEFAULT 'detected',
    reviewed_by         VARCHAR(100),
    applied_to_version  VARCHAR(50),
    related_events      TEXT[]
);

-- Daily Graph State Snapshot
CREATE TABLE IF NOT EXISTS daily_graph_state (
    state_id            BIGSERIAL PRIMARY KEY,
    state_date          DATE NOT NULL UNIQUE,
    graph_version       VARCHAR(50) NOT NULL,
    current_regime      VARCHAR(100) NOT NULL DEFAULT 'normal',
    node_values         JSONB NOT NULL,
    node_zscores        JSONB NOT NULL,
    anomalous_nodes     TEXT[],
    active_paths        JSONB,
    inference_summary   JSONB,
    alert_level         VARCHAR(20) DEFAULT 'green',
    alert_details       JSONB,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_edges_history_edge ON causal_edges_history(edge_id, effective_from DESC);
CREATE INDEX IF NOT EXISTS idx_edges_history_version ON causal_edges_history(graph_version);
CREATE INDEX IF NOT EXISTS idx_inference_date ON causal_inference_log(inference_date DESC);
CREATE INDEX IF NOT EXISTS idx_inference_nodes ON causal_inference_log(source_node, target_node);
CREATE INDEX IF NOT EXISTS idx_daily_state_date ON daily_graph_state(state_date DESC);
CREATE INDEX IF NOT EXISTS idx_break_edge ON structural_break_events(edge_id, break_date DESC);

-- Daily Risk Index (GFCRI)
CREATE TABLE IF NOT EXISTS daily_risk_index (
    index_id            BIGSERIAL PRIMARY KEY,
    index_date          DATE NOT NULL UNIQUE,
    gfcri_value         NUMERIC(6, 2) NOT NULL,
    alert_level         VARCHAR(20) NOT NULL,
    si_rates            NUMERIC(6, 2) NOT NULL,
    si_fx               NUMERIC(6, 2) NOT NULL,
    si_equity           NUMERIC(6, 2) NOT NULL,
    si_credit           NUMERIC(6, 2) NOT NULL,
    si_sentiment        NUMERIC(6, 2) NOT NULL,
    sub_index_details   JSONB,
    active_chains       JSONB,
    chain_details       JSONB,
    coherence_multiplier NUMERIC(4, 2),
    node_contributions  JSONB,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_index_date ON daily_risk_index(index_date DESC);

-- Daily Reports (Markdown)
CREATE TABLE IF NOT EXISTS daily_reports (
    report_id           BIGSERIAL PRIMARY KEY,
    report_date         DATE NOT NULL UNIQUE,
    gfcri_value         NUMERIC(6, 2),
    alert_level         VARCHAR(20),
    report_markdown     TEXT NOT NULL,
    report_metadata     JSONB,
    llm_narrative       TEXT,
    generation_time_ms  INTEGER,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reports_date ON daily_reports(report_date DESC);

-- =========================================================================
-- Market Data (raw daily prices from yfinance, shared by GFCRI + EHS)
-- =========================================================================

CREATE TABLE IF NOT EXISTS market_data_daily (
    id              BIGSERIAL PRIMARY KEY,
    ticker          VARCHAR(50) NOT NULL,
    trade_date      DATE NOT NULL,
    close_price     NUMERIC(20, 6) NOT NULL,
    volume          BIGINT,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ticker, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_market_data_ticker_date
    ON market_data_daily(ticker, trade_date DESC);

-- =========================================================================
-- EHS: Economy Health Score tables
-- =========================================================================

-- Raw economic indicator data (IMF, FRED, yfinance-derived monthly)
CREATE TABLE IF NOT EXISTS ehs_indicator_data (
    id                  BIGSERIAL PRIMARY KEY,
    economy_code        CHAR(2) NOT NULL,
    indicator_code      VARCHAR(50) NOT NULL,
    reference_date      DATE NOT NULL,
    raw_value           NUMERIC(20, 6),
    transformed_value   NUMERIC(20, 6),
    z_score             NUMERIC(10, 6),
    data_source         VARCHAR(20),
    collected_at        TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(economy_code, indicator_code, reference_date)
);

CREATE INDEX IF NOT EXISTS idx_ehs_indicator_lookup
    ON ehs_indicator_data(economy_code, indicator_code, reference_date DESC);

-- Monthly/daily EHS scores
CREATE TABLE IF NOT EXISTS ehs_scores (
    id                  BIGSERIAL PRIMARY KEY,
    economy_code        CHAR(2) NOT NULL,
    score_date          DATE NOT NULL,
    ehs_score           NUMERIC(6, 2) NOT NULL,
    growth_score        NUMERIC(6, 2),
    labor_score         NUMERIC(6, 2),
    price_score         NUMERIC(6, 2),
    external_score      NUMERIC(6, 2),
    financial_score     NUMERIC(6, 2),
    cycle_phase         VARCHAR(20),
    score_change_1m     NUMERIC(6, 2),
    indicator_details   JSONB,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(economy_code, score_date)
);

CREATE INDEX IF NOT EXISTS idx_ehs_scores_lookup
    ON ehs_scores(economy_code, score_date DESC);

-- Event Calendar
CREATE TABLE IF NOT EXISTS event_calendar (
    event_id            BIGSERIAL PRIMARY KEY,
    event_date          DATE NOT NULL,
    event_name          VARCHAR(500) NOT NULL,
    event_type          VARCHAR(100),
    affected_nodes      TEXT[],
    expected_impact     VARCHAR(20),
    actual_impact       JSONB,
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_event_date ON event_calendar(event_date);

-- =========================================================================
-- Users / Pro trial
-- =========================================================================

CREATE TABLE IF NOT EXISTS users (
    id                BIGSERIAL PRIMARY KEY,
    email             VARCHAR(255) NOT NULL UNIQUE,
    password_hash     VARCHAR(255) NOT NULL,
    display_name      VARCHAR(100),
    plan              VARCHAR(20) NOT NULL DEFAULT 'free',
    trial_started_at  TIMESTAMPTZ,
    trial_expires_at  TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
