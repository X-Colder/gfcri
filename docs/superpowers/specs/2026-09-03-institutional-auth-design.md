# GFCRI Institutional Identity and Access Design

Date: 2026-09-03

Status: Approved implementation direction

## Goal

Give GFCRI a secure native account system while supporting external enterprise
identity through a generic OIDC integration. Both paths must resolve to the
same organization, membership, role, tenant, session, and audit model.

## Current Problems

- Passwords use a global SHA-256 construction instead of a password KDF.
- The custom bearer token embeds authorization claims that can remain stale.
- Institutional access checks account type but not organization membership role.
- Organization context chooses the first active membership and cannot safely
  represent multiple organizations.
- Member lifecycle has no invite, accept, suspend, or remove flow.
- API keys have no scopes, expiry, last-used record, or access audit.
- Authentication, membership, export, and administrative changes are not
  recorded in an append-only audit stream.
- No external identity provider callback or identity-linking model exists.

## Architecture

### Native authentication

Keep `/api/auth/register`, `/api/auth/login`, and bearer authentication as
public API shapes. Replace the credential/token internals with:

- per-user scrypt password hashes with random salts;
- server-side sessions stored as token hashes;
- short-lived access sessions with explicit revocation;
- account status, email verification, failed-login, and lockout fields;
- authorization resolved from the database, not trusted token claims.

### External authentication

Implement generic OIDC authorization-code flow:

1. Institution configures an OIDC issuer, client ID, redirect URI, and allowed
   email domains.
2. GFCRI generates state, nonce, and PKCE values and stores a short-lived
   login transaction.
3. Provider callback exchanges the code, validates issuer/audience/nonce and
   obtains a stable subject and verified email.
4. GFCRI links the external identity to an existing user or creates a pending
   invited user inside the configured organization.
5. GFCRI issues the same server-side session used by native login.

SAML is represented by an identity-provider interface but is not claimed as
implemented in this slice. A SAML broker can be connected later without
changing organization or permission contracts.

### Organization and permissions

The request context must carry an explicit organization ID. Every protected
query must use that context. Roles are fixed:

- `owner`: organization lifecycle, billing, identity provider, all members;
- `admin`: members, workspace, data sources, API keys, exports;
- `analyst`: ingest approved observations and run analyses;
- `viewer`: read derived analysis and approved reports only.

Membership status is checked on every request. Invitations are scoped to an
organization and expire.

### Audit

Write append-only events for login, logout, failed login, SSO callback,
invitation, membership change, role change, API-key lifecycle, data ingest,
analysis run, report export, and organization configuration changes.

Audit records must include organization, actor, action, target, outcome,
request ID, IP/user-agent metadata where available, and event time.

## Data Model Changes

- `users`: status, email verification, lockout, password version and timestamps.
- `auth_sessions`: hashed token, user, expiry, revocation, last seen.
- `external_identities`: provider, issuer, subject, email, user, organization.
- `identity_providers`: organization-scoped OIDC metadata and status.
- `auth_transactions`: state, nonce, PKCE verifier, expiry, provider context.
- `institutional_invitations`: organization, email, role, inviter, token hash,
  expiry, accepted/revoked timestamps.
- `institutional_audit_events`: append-only organization activity trail.
- `institutional_api_keys`: scopes, expiry, last used, revoked-by metadata.

## Non-Goals

- No custom SAML protocol implementation in this slice.
- No claim of SOC 2, ISO 27001, SEC, FINRA, or customer-specific compliance.
- No authorization based solely on email domain.
- No raw-data export as a normal product feature.

## Acceptance Criteria

- A native login creates a revocable server-side session.
- Wrong passwords are rate-limited and repeated failures lock the account.
- A revoked session cannot access institutional endpoints.
- A viewer cannot ingest observations, manage members, create API keys, or
  export raw observations.
- A member with two organizations must receive an explicit organization context;
  no endpoint may silently choose the first organization.
- An invitation can be created, accepted once, expired, and revoked.
- OIDC identity resolution produces the same organization session as native login.
- Security-relevant events are queryable by organization administrators.

