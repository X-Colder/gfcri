from __future__ import annotations


def ensure_institutional_schema(conn) -> None:
    statements = (
        """
        CREATE TABLE IF NOT EXISTS institutional_entities (
            id BIGSERIAL PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            entity_type VARCHAR(40) NOT NULL,
            entity_id VARCHAR(160) NOT NULL,
            name TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, entity_type, entity_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS institutional_data_sources (
            id BIGSERIAL PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            source_id VARCHAR(160) NOT NULL,
            name TEXT NOT NULL,
            source_tier VARCHAR(40) NOT NULL,
            license_status VARCHAR(40) NOT NULL DEFAULT 'review_required',
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, source_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS institutional_data_snapshots (
            snapshot_id VARCHAR(160) PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            observation_count INTEGER NOT NULL DEFAULT 0,
            quality JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS institutional_observations (
            id BIGSERIAL PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            entity_type VARCHAR(40) NOT NULL,
            entity_id VARCHAR(160) NOT NULL,
            metric_id VARCHAR(160) NOT NULL,
            value DOUBLE PRECISION NOT NULL,
            unit VARCHAR(60) NOT NULL,
            as_of DATE NOT NULL,
            frequency VARCHAR(20) NOT NULL,
            source_id VARCHAR(160) NOT NULL,
            source_tier VARCHAR(40) NOT NULL,
            quality_status VARCHAR(30) NOT NULL,
            snapshot_id VARCHAR(160) NOT NULL,
            ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, entity_type, entity_id, metric_id, as_of, source_id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_institutional_observations_tenant_date ON institutional_observations (tenant_id, as_of DESC)",
        "CREATE INDEX IF NOT EXISTS idx_institutional_observations_entity ON institutional_observations (tenant_id, entity_type, entity_id)",
        """
        CREATE TABLE IF NOT EXISTS institutional_organizations (
            id BIGSERIAL PRIMARY KEY,
            org_key VARCHAR(160) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            owner_user_id BIGINT NOT NULL REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS institutional_memberships (
            organization_id BIGINT NOT NULL REFERENCES institutional_organizations(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role VARCHAR(30) NOT NULL DEFAULT 'viewer',
            status VARCHAR(30) NOT NULL DEFAULT 'active',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (organization_id, user_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS institutional_workspaces (
            id BIGSERIAL PRIMARY KEY,
            organization_id BIGINT NOT NULL REFERENCES institutional_organizations(id) ON DELETE CASCADE,
            workspace_key VARCHAR(120) NOT NULL,
            name VARCHAR(255) NOT NULL,
            profile JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (organization_id, workspace_key)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS institutional_api_keys (
            id BIGSERIAL PRIMARY KEY,
            organization_id BIGINT NOT NULL REFERENCES institutional_organizations(id) ON DELETE CASCADE,
            label VARCHAR(120) NOT NULL,
            key_prefix VARCHAR(24) NOT NULL,
            token_hash VARCHAR(128) NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            revoked_at TIMESTAMPTZ
        )
        """,        """
        CREATE TABLE IF NOT EXISTS institutional_analysis_runs (
            run_id VARCHAR(160) PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            target_type VARCHAR(40) NOT NULL,
            target_id VARCHAR(160) NOT NULL,
            model_version VARCHAR(80) NOT NULL,
            snapshot_id VARCHAR(160),
            status VARCHAR(30) NOT NULL DEFAULT 'completed',
            request JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS institutional_analysis_results (
            run_id VARCHAR(160) PRIMARY KEY REFERENCES institutional_analysis_runs(run_id) ON DELETE CASCADE,
            tenant_id TEXT NOT NULL,
            result JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
    )
    with conn.cursor() as cur:
        for statement in statements:
            cur.execute(statement)
    conn.commit()
