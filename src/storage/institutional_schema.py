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
        "ALTER TABLE institutional_organizations ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(30) NOT NULL DEFAULT 'active'",
        "ALTER TABLE institutional_organizations ADD COLUMN IF NOT EXISTS subscription_plan VARCHAR(40) NOT NULL DEFAULT 'team'",
        "ALTER TABLE institutional_organizations ADD COLUMN IF NOT EXISTS subscription_current_period_end TIMESTAMPTZ",
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
        '''ALTER TABLE institutional_api_keys ADD COLUMN IF NOT EXISTS scopes JSONB NOT NULL DEFAULT '[\"analysis:read\", \"analysis:run\", \"data:read\"]'::jsonb''',
        "ALTER TABLE institutional_api_keys ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ",
        "ALTER TABLE institutional_api_keys ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMPTZ",
        "ALTER TABLE institutional_api_keys ADD COLUMN IF NOT EXISTS revoked_by_user_id BIGINT",
        """
        CREATE TABLE IF NOT EXISTS institutional_invitations (
            id BIGSERIAL PRIMARY KEY,
            organization_id BIGINT NOT NULL REFERENCES institutional_organizations(id) ON DELETE CASCADE,
            email VARCHAR(255) NOT NULL,
            role VARCHAR(30) NOT NULL,
            token_hash VARCHAR(128) NOT NULL UNIQUE,
            invited_by_user_id BIGINT NOT NULL REFERENCES users(id),
            expires_at TIMESTAMPTZ NOT NULL,
            accepted_at TIMESTAMPTZ,
            revoked_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_institutional_invitations_org ON institutional_invitations (organization_id, created_at DESC)",
        """
        CREATE TABLE IF NOT EXISTS institutional_audit_events (
            id BIGSERIAL PRIMARY KEY,
            organization_id BIGINT,
            actor_user_id BIGINT,
            actor_type VARCHAR(30) NOT NULL,
            action VARCHAR(120) NOT NULL,
            target_type VARCHAR(80) NOT NULL,
            target_id VARCHAR(255),
            outcome VARCHAR(30) NOT NULL,
            request_id VARCHAR(160),
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_institutional_audit_org_time ON institutional_audit_events (organization_id, occurred_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_institutional_audit_actor_time ON institutional_audit_events (actor_user_id, occurred_at DESC)",
        """
        CREATE TABLE IF NOT EXISTS institutional_identity_providers (
            id BIGSERIAL PRIMARY KEY,
            organization_id BIGINT NOT NULL UNIQUE REFERENCES institutional_organizations(id) ON DELETE CASCADE,
            protocol VARCHAR(20) NOT NULL DEFAULT 'oidc',
            issuer TEXT NOT NULL,
            client_id TEXT NOT NULL,
            client_secret_env VARCHAR(160) NOT NULL,
            redirect_uri TEXT NOT NULL,
            scopes JSONB NOT NULL DEFAULT '["openid", "email", "profile"]'::jsonb,
            allowed_domains JSONB NOT NULL DEFAULT '[]'::jsonb,
            default_role VARCHAR(30) NOT NULL DEFAULT 'viewer',
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS external_identities (
            id BIGSERIAL PRIMARY KEY,
            organization_id BIGINT NOT NULL REFERENCES institutional_organizations(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            issuer TEXT NOT NULL,
            subject TEXT NOT NULL,
            email VARCHAR(255) NOT NULL,
            claims JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_login_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (issuer, subject)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_external_identities_user ON external_identities (user_id)",
        """
        CREATE TABLE IF NOT EXISTS auth_transactions (
            state_hash VARCHAR(128) PRIMARY KEY,
            organization_id BIGINT NOT NULL REFERENCES institutional_organizations(id) ON DELETE CASCADE,
            provider_id BIGINT NOT NULL REFERENCES institutional_identity_providers(id) ON DELETE CASCADE,
            nonce VARCHAR(255) NOT NULL,
            code_verifier VARCHAR(255) NOT NULL,
            redirect_uri TEXT NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_auth_transactions_expiry ON auth_transactions (expires_at)",
    )
    with conn.cursor() as cur:
        for statement in statements:
            cur.execute(statement)
    conn.commit()
