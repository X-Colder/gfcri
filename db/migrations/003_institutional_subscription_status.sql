ALTER TABLE institutional_organizations
    ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(30) NOT NULL DEFAULT 'active';

ALTER TABLE institutional_organizations
    ADD COLUMN IF NOT EXISTS subscription_plan VARCHAR(40) NOT NULL DEFAULT 'team';

ALTER TABLE institutional_organizations
    ADD COLUMN IF NOT EXISTS subscription_current_period_end TIMESTAMPTZ;
