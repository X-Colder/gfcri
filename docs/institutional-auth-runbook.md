# GFCRI Institutional Authentication Runbook

Date: 2026-09-03

## Authentication Modes

GFCRI supports two identity paths:

1. Native GFCRI accounts for standalone/private deployments.
2. External OIDC for institution-managed identity.

Both paths create the same server-side GFCRI session and resolve to the same
organization membership and role model.

## Native Account Controls

- Passwords use per-user salted scrypt hashes.
- New bearer tokens are opaque random session tokens.
- Only the token hash is stored.
- Sessions expire after 12 hours by default.
- Logout revokes the current session.
- Five failed login attempts lock an account for 15 minutes.
- A suspended user cannot resolve an active session.

Existing legacy password hashes may be upgraded after a successful login only
when `JWT_SECRET` is explicitly configured. New deployments must not rely on
the legacy hash path.

## Organization Context

Every institutional request should use:

```text
X-Organization-ID: <organization_id>
```

The header is optional for users with exactly one active membership and
required for users with multiple organizations. The API must reject ambiguous
requests rather than choosing an arbitrary organization.

## Roles

| Role | Scope |
|---|---|
| owner | Organization lifecycle, identity provider, members, keys, data, analysis, export |
| admin | Members, identity provider, workspace, keys, data, analysis, export |
| analyst | Approved data ingest and analysis runs |
| viewer | Derived analysis and approved reports only |

API keys have separate scopes and cannot use raw-data export by default.

## OIDC Setup

1. Register a client with the institution's identity provider.
2. Set a secret in the API environment, for example:

```text
GFCRI_ACME_OIDC_SECRET=<secret>
```

3. Configure the provider through:

```text
POST /api/v1/institutional/identity-provider
```

with `client_secret_env: "GFCRI_ACME_OIDC_SECRET"`.

4. Use:

```text
GET /api/auth/oidc/<organization-org-key>/start
```

The provider must support OIDC Authorization Code flow with PKCE and return a
verified email. Allowed domains are checked before membership is created.

SAML providers should be connected through the customer's identity broker or
through a later SAML adapter. GFCRI does not claim to implement SAML directly
in this release.

## Operational Controls

Before an institutional pilot:

- set a non-default database password;
- configure a strong `JWT_SECRET` for legacy migration only;
- configure the OIDC client secret through the environment;
- enable HTTPS at the reverse proxy;
- verify database backups and restore procedure;
- restrict raw observation export to approved administrators;
- review audit events after member, key, export, and identity changes.

Before production:

- complete SSO/identity-provider security review;
- add MFA policy through the identity provider;
- review data retention and deletion;
- enable centralized audit export and alerting;
- complete penetration testing and incident response procedures;
- complete data-source and report redistribution review;
- obtain customer-specific legal and compliance approval.
