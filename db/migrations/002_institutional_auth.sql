CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    account_type VARCHAR(20) NOT NULL DEFAULT 'personal',
    plan VARCHAR(20) NOT NULL DEFAULT 'free',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    email_verified_at TIMESTAMPTZ,
    failed_login_count INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ,
    last_login_at TIMESTAMPTZ,
    trial_started_at TIMESTAMPTZ,
    trial_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active';
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS auth_sessions (
    token_hash VARCHAR(128) PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    ip_address VARCHAR(128),
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_user
    ON auth_sessions (user_id, expires_at DESC);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_active
    ON auth_sessions (expires_at, revoked_at);

ALTER TABLE institutional_api_keys
    ADD COLUMN IF NOT EXISTS scopes JSONB NOT NULL
    DEFAULT '["analysis:read", "analysis:run", "data:read"]'::jsonb;

ALTER TABLE institutional_api_keys
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;

ALTER TABLE institutional_api_keys
    ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMPTZ;

ALTER TABLE institutional_api_keys
    ADD COLUMN IF NOT EXISTS revoked_by_user_id BIGINT;

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
);

CREATE INDEX IF NOT EXISTS idx_institutional_invitations_org
    ON institutional_invitations (organization_id, created_at DESC);

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
);

CREATE INDEX IF NOT EXISTS idx_institutional_audit_org_time
    ON institutional_audit_events (organization_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_institutional_audit_actor_time
    ON institutional_audit_events (actor_user_id, occurred_at DESC);

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
);

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
);

CREATE INDEX IF NOT EXISTS idx_external_identities_user
    ON external_identities (user_id);

CREATE TABLE IF NOT EXISTS auth_transactions (
    state_hash VARCHAR(128) PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES institutional_organizations(id) ON DELETE CASCADE,
    provider_id BIGINT NOT NULL REFERENCES institutional_identity_providers(id) ON DELETE CASCADE,
    nonce VARCHAR(255) NOT NULL,
    code_verifier VARCHAR(255) NOT NULL,
    redirect_uri TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auth_transactions_expiry
    ON auth_transactions (expires_at);
