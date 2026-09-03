# Institutional Auth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add secure native authentication, organization-aware permissions, auditability, and a generic OIDC external identity path to GFCRI.

**Architecture:** Keep the existing auth route shapes but replace trust-in-token authorization with server-side session lookup. Add explicit organization context and role checks to institutional routes. Implement OIDC as an adapter that links external identities into the same local user/session model.

**Tech Stack:** Python 3.11, FastAPI, PostgreSQL, psycopg2, standard-library `hashlib.scrypt`, `secrets`, `hmac`, and existing `cryptography` dependency for OIDC JWT verification.

## Global Constraints

- Native credentials remain available for private deployments.
- External identity is implemented through OIDC first; SAML remains an adapter boundary.
- Raw observations are not a normal customer-facing output.
- All membership and organization decisions must be server-side.
- Database migrations must be idempotent and must not drop existing data.
- Existing auth endpoint paths remain compatible.

### Task 1: Auth primitives and session storage

**Files:**
- Create: `src/security/passwords.py`
- Create: `src/security/sessions.py`
- Modify: `api/routers/auth.py`
- Modify: `src/storage/institutional_schema.py`
- Test: `tests/test_auth_security.py`

- [ ] Write failing tests for scrypt hash verification, wrong-password rejection,
  session creation, expiry, and revocation.
- [ ] Add idempotent `users` columns and `auth_sessions`.
- [ ] Replace global SHA-256 with salted scrypt while accepting only the new
  storage format for newly created passwords.
- [ ] Issue random opaque bearer tokens and store only their hashes.
- [ ] Resolve bearer requests through the session table and reject revoked or
  expired sessions.
- [ ] Run `pytest -q tests/test_auth_security.py`.

### Task 2: Organization context and RBAC

**Files:**
- Create: `src/security/authorization.py`
- Modify: `src/storage/institutional_tenancy.py`
- Modify: `api/routers/auth.py`
- Modify: `api/routers/institutional_data.py`
- Modify: `api/routers/institutional_analysis.py`
- Modify: `api/routers/institutional_workspace.py`
- Test: `tests/test_institutional_authorization.py`

- [ ] Write failing tests for viewer read-only access, analyst analysis access,
  admin member management, and explicit multi-organization context.
- [ ] Add `OrganizationContext` resolution from session/API key plus requested
  organization header.
- [ ] Require active membership and fixed role for each protected operation.
- [ ] Make data ingest analyst/admin-only and raw export admin-only.
- [ ] Reject ambiguous multi-organization requests instead of selecting the
  first organization.
- [ ] Run the authorization test file.

### Task 3: Invitations, API-key governance, and audit

**Files:**
- Create: `src/security/audit.py`
- Modify: `src/storage/institutional_schema.py`
- Modify: `api/routers/institutional_workspace.py`
- Modify: `api/models/institutional_workspace.py`
- Test: `tests/test_institutional_governance.py`

- [ ] Write failing tests for invitation expiry/revocation, API-key scopes and
  expiry, and audit-event payloads.
- [ ] Add invitation and audit tables.
- [ ] Add create/list/accept/revoke invitation operations.
- [ ] Add API-key scope, expiry, last-used, and revocation metadata.
- [ ] Record membership, key, export, and analysis lifecycle events.
- [ ] Run the governance test file.

### Task 4: OIDC provider and identity linking

**Files:**
- Create: `src/security/oidc.py`
- Modify: `src/storage/institutional_schema.py`
- Modify: `api/models/auth.py`
- Modify: `api/routers/auth.py`
- Create: `api/routers/oidc.py` if route separation is required
- Test: `tests/test_oidc_identity.py`

- [ ] Write failing tests for issuer allowlisting, state/nonce/PKCE transaction
  validation, verified-email domain matching, and identity linking.
- [ ] Add provider, identity, and login-transaction tables.
- [ ] Implement provider discovery, authorization URL generation, callback
  exchange, issuer/audience/nonce validation, and session issuance.
- [ ] Link a stable `(issuer, subject)` identity to a local user and organization.
- [ ] Reject unverified or disallowed identities.
- [ ] Run the OIDC test file with network calls replaced by deterministic
  provider responses.

### Task 5: Migration and verification

**Files:**
- Create: `db/migrations/002_institutional_auth.sql`
- Modify: `.env.example`
- Modify: `docs/institutional-value-layer.md`
- Create: `docs/institutional-auth-runbook.md`

- [ ] Add idempotent production migration.
- [ ] Document required secrets, OIDC configuration, emergency owner recovery,
  session revocation, and audit review.
- [ ] Run focused tests, touched-file compilation, and API import checks in the
  dependency-complete environment.
- [ ] Run `git diff --check` and review tenant/auth data flows before release.

