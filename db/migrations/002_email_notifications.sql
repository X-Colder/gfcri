CREATE TABLE IF NOT EXISTS email_subscriptions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(24) NOT NULL DEFAULT 'unverified',
    verified_at TIMESTAMPTZ,
    verification_token_hash VARCHAR(128),
    verification_expires_at TIMESTAMPTZ,
    unsubscribe_token_hash VARCHAR(128) NOT NULL,
    daily_brief BOOLEAN NOT NULL DEFAULT FALSE,
    risk_alerts BOOLEAN NOT NULL DEFAULT FALSE,
    weekly_digest BOOLEAN NOT NULL DEFAULT FALSE,
    institutional_data_quality BOOLEAN NOT NULL DEFAULT FALSE,
    product_updates BOOLEAN NOT NULL DEFAULT FALSE,
    frequency VARCHAR(16) NOT NULL DEFAULT 'daily',
    risk_alert_level VARCHAR(16) NOT NULL DEFAULT 'orange',
    language VARCHAR(8) NOT NULL DEFAULT 'en',
    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS email_outbox (
    id BIGSERIAL PRIMARY KEY,
    subscription_id BIGINT NOT NULL REFERENCES email_subscriptions(id) ON DELETE CASCADE,
    kind VARCHAR(40) NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL UNIQUE,
    to_email VARCHAR(255) NOT NULL,
    subject TEXT NOT NULL,
    text_body TEXT NOT NULL,
    html_body TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_outbox_pending
    ON email_outbox (status, next_attempt_at);
