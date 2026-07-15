# GFCRI Commercial Engineering Gap List

Date: 2026-07-10
Scope: paid pilot first, production commercialization second.

## Current Baseline

The codebase already has:

- API route registration for risk index, reports, institutional radar, core themes, commercial readiness, model foundation, and health.
- Personal/pro trial flow and an institutional account type flag.
- Data quality gate that blocks official risk-index publication when critical market data is incomplete.
- `market_data_daily` persistence and freshness reporting.
- Institutional commercial readiness API and frontend cards.
- Docker Compose stack for Postgres, scheduler app, API, frontend, and dashboard.

## Paid Pilot Must-Haves

| Capability | Current State | Gap | Pilot Decision |
|---|---|---|---|
| Stable demo login | partial | Need seeded demo institutional account or documented admin setup | Required |
| Institution access boundary | partial | Account type exists, but no tenant roles or team seats | Accept with single pilot account |
| Data freshness visibility | partial | API and UI exist; no operator alerting yet | Required for pilot, alerting can be manual |
| Index publication gate | done | Blocking event appears on latest risk index | Required |
| Private deployment config | partial | Compose stack exists; runbook needed | Required |
| Report evidence and limitations | partial | Methodology exists; client review pack needed | Required |
| API integration | partial | REST APIs exist; no API key management | Optional for pilot, required for integration POC |
| Audit log | partial | Reports and daily states persist; user/action audit not present | Document as production gap |

## Engineering Work Packages

### BE-1: Pilot Account Setup

Goal: make it easy to provision one institutional demo account without manual DB editing.

Acceptance:

- Admin/operator can create or mark an account as `institutional`.
- Personal trial flow remains separate from institutional access.
- The operation is documented and does not expose secrets in source.

Suggested implementation:

- Add an operator script or one-off management command.
- Avoid building full admin UI for Phase 1.

### BE-2: API Key Skeleton

Goal: support one client integration POC without full enterprise identity.

Acceptance:

- API key can be issued, revoked, and associated with a label/client.
- API key access is limited to read-only institutional endpoints.
- Requests are logged at least by key id, endpoint, status, and timestamp.

Suggested scope:

- `api_keys` table with hashed token.
- Dependency that accepts either bearer user token or API key for selected endpoints.
- No billing meter in Phase 1.

### BE-3: Job and Data Freshness Status

Goal: make operators aware of data refresh and index-publication failure.

Acceptance:

- Latest market-data refresh summary is queryable.
- Latest blocked risk-index run is queryable.
- Health endpoint or dedicated status endpoint exposes degraded/blocked state.

Suggested scope:

- Persist market data refresh events.
- Expose `/api/commercial-readiness/data-freshness`.
- Add status summary to runbook for manual pilot monitoring.

### BE-4: Report Audit Foundation

Goal: create enough traceability for client review.

Acceptance:

- Each generated report has date, GFCRI value, alert level, metadata, generation time, and source state.
- Exported report includes non-advisory disclaimer.
- Approval workflow is explicitly marked out of scope for Phase 1.

## Production-Grade Backlog

| Area | Requirement | Why It Matters |
|---|---|---|
| Multi-tenant RBAC | Organization, role, seat, permission model | Required for hosted institution customers |
| SSO/SAML | Enterprise identity integration | Common procurement requirement |
| Audit logs | User action, API access, report export, admin change logs | Compliance and support traceability |
| Alerting | Email/webhook/operator alerts for failed data refresh, blocked publication, API errors | Reliability and SLA |
| Vendor data connector | Licensed market data source with SLA | Commercial rights and uptime |
| Signed report export | Watermark, version hash, approval status | Client-facing governance |
| Client data sandbox | Private client indicators without cross-tenant leakage | Enterprise customization |

## Recommended Sequence

1. Build operator demo-account provisioning.
2. Persist market refresh events and expose a status summary.
3. Add API key skeleton only if a pilot requires system integration.
4. Add report audit metadata and export disclaimer.
5. Defer full RBAC/SSO/multi-tenant isolation until after paid pilot validation.
