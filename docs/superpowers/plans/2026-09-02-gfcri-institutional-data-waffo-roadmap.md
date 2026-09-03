# GFCRI Institutional Data API and Waffo Billing Roadmap

**Date:** 2026-09-02

**Objective:** Build GFCRI as a governed institutional risk-data and analysis API while adding Waffo as a provider-backed personal subscription payment option.

**Current baseline:** Personal/institutional pricing entry points, institutional lead capture, and server-side institutional radar protection are deployed in `/opt/gfcri/releases/20260902-commercial`.

## Product Decisions

- Personal product exposes interpreted risk signals and limited history.
- Institutional product exposes a governed data contract, quality gates, traceable analysis, custom target universes, exports, and API access.
- The canonical GFCRI core score remains comparable across customers. Customer customization is applied as an overlay, profile, threshold, target universe, or data source; customers do not directly rewrite core weights in v1.
- Waffo is used first for personal monthly and annual hosted subscriptions. Institutional pilots remain assisted-sales or invoice/payment-link transactions.
- Initial institutional analysis scope is `country` and `economy`. `company`, `security`, and `portfolio` are reserved for the next adapter stages.
- SSO/SAML, full multi-tenant RBAC, real-time streaming, portfolio optimization, and arbitrary customer-defined model weights are out of the first release.

## Schedule

| Phase | Dates | Workstream | Exit gate |
|---|---|---|---|
| 0 | Sep 2-4, 2026 | Contract and scope freeze | Data manifest, Waffo credential checklist, and acceptance tests approved |
| 1A | Sep 5-11 | Canonical data model foundation | Synthetic observations validate and persist with source/quality metadata |
| 1B | Sep 5-11 | Waffo sandbox readiness | Merchant sandbox, products, keys, webhook URL, and HTTPS endpoint available |
| 2A | Sep 12-25 | Institutional ingestion and quality pipeline | Batch upload, idempotency, coverage, freshness, and degraded-state output work |
| 2B | Sep 12-18 | Waffo checkout adapter | Personal monthly/annual sandbox checkout returns a hosted URL |
| 3A | Sep 26-Oct 9 | Country/economy analysis API | Internal plus public data produces versioned, traceable risk results |
| 3B | Sep 19-25 | Waffo lifecycle and webhook handling | Payment, renewal, failure, cancellation, refund, replay, and signature tests pass |
| 4 | Oct 10-16 | Institutional target profiles and delivery | Custom universe, API export, report snapshot, and data dictionary usable by a pilot |
| 5 | Oct 17-23 | Production hardening and release | UAT, security review, payment go-live, rollback, and monitoring checks pass |

## Phase 0: Contract Freeze

**Deliverables**

- `model_version`: `gfcri-institutional-v1`
- Entity types: `country`, `economy`, `company`, `security`, `portfolio`
- v1 active types: `country`, `economy`
- Source tiers: `official`, `licensed`, `internal_verified`, `proxy`, `unverified`
- Required observation fields:

```text
tenant_id
entity_type
entity_id
metric_id
value
unit
as_of
frequency
source_id
quality_status
ingested_at
```

- Waffo credentials checklist:

```text
merchant_id
api_key
private_key
public_key
sandbox/production environment
monthly product or price id
annual product or price id
webhook signing configuration
```

**Acceptance**

- Every result can identify its data snapshot and model version.
- No production payment work starts without Waffo Sandbox credentials and webhook access.

## Phase 1A-2A: Institutional Data Plane

**Files/modules**

- Create migrations for `entities`, `metric_definitions`, `data_sources`, `observations`, `data_snapshots`, `analysis_runs`, and `analysis_results`.
- Add `src/data/institutional/normalizer.py`.
- Add `src/data/institutional/quality.py`.
- Add `api/routers/institutional_data.py`.
- Add `api/models/institutional_data.py`.
- Add `tests/test_institutional_data_contract.py`.

**Endpoints**

```text
GET  /api/v1/institutional/model-manifest
POST /api/v1/institutional/entities
POST /api/v1/institutional/data-sources
POST /api/v1/institutional/observations:batch
GET  /api/v1/institutional/data-quality
```

**Required behavior**

- Batch ingestion is idempotent with a request or snapshot ID.
- Every observation is tenant-scoped.
- Invalid unit, frequency, entity, or metric mappings are rejected before analysis.
- Missing or stale inputs produce `degraded` quality, not false precision.
- Raw internal data never appears in application logs.

## Phase 2B-3B: Waffo Billing

**Architecture**

Create a provider-neutral billing boundary:

```text
BillingService
  -> WaffoProvider
  -> StripeProvider (retain only if already configured)
```

**Files/modules**

- Create `api/billing/providers/base.py`.
- Create `api/billing/providers/waffo.py`.
- Modify `api/routers/billing.py`.
- Add provider-neutral tables for customers, subscriptions, checkout sessions, and provider events.
- Add `tests/test_billing_provider_contract.py`.

**Endpoints**

```text
GET  /api/billing/catalog
POST /api/billing/checkout
POST /api/billing/waffo/webhook
GET  /api/billing/status
POST /api/billing/portal
```

**Waffo behavior**

- Backend creates a hosted subscription checkout.
- Frontend receives only a hosted checkout URL.
- Backend verifies Waffo signatures and processes events idempotently.
- Normalized subscription states update `users.plan` and provider metadata.
- Checkout success is not treated as authoritative until a verified webhook arrives.
- Webhook replay and out-of-order events must not downgrade a newer subscription state.

**Acceptance**

- Sandbox monthly checkout succeeds.
- Sandbox annual checkout succeeds.
- Renewal, failed payment, cancellation, refund, duplicate webhook, bad signature, and expired signature are covered.
- Private keys and API keys are never returned by `/api/billing/catalog` or frontend code.

## Phase 3A: Country/Economy Analysis API

**Files/modules**

- Create `src/engines/institutional_analysis.py`.
- Create `src/engines/target_adapters/country.py`.
- Create `src/engines/target_adapters/economy.py`.
- Create `api/routers/institutional_analysis.py`.
- Add typed response models and tests.

**Endpoints**

```text
POST /api/v1/institutional/analysis-runs
GET  /api/v1/institutional/analysis-runs/{run_id}
GET  /api/v1/institutional/entities/{entity_id}/risk
```

**Result contract**

```text
target
risk_score
risk_level
dimensions
drivers
transmission_paths
data_quality
evidence
model_version
data_snapshot_id
generated_at
```

**Acceptance**

- A country/economy result combines public and internal observations.
- Each material driver links to source and observation metadata.
- The same input snapshot and model version produce a reproducible result.
- A degraded data snapshot is visibly marked and cannot be presented as fully covered.

## Phase 4: Institutional Delivery Layer

**Scope**

- Organization and membership tables.
- Workspace and target-universe configuration.
- Roles: `owner`, `admin`, `analyst`, `viewer`.
- API key issuance and revocation.
- CSV/PDF export with model version, data date, source notice, and disclaimer.
- Scheduled weekly report.
- Custom watchlist and threshold overlays.

**Not in scope**

- Direct modification of canonical GFCRI weights.
- Full SSO/SAML.
- Real-time event streaming.
- Portfolio optimization or investment recommendations.

**Acceptance**

- Two users in one organization can access the same workspace according to role.
- One organization cannot read another organization's observations or results.
- A configured target universe changes the analysis scope without changing the canonical core score.
- Exported reports contain source state, model version, data date, and non-advisory language.

## Phase 5: Production Release

**Required checks**

- Migration backup and rollback test.
- Tenant-isolation tests.
- API-key authorization tests.
- Waffo Sandbox evidence attached to release record.
- Waffo production webhook signature verified.
- Personal checkout success and cancellation verified.
- Institutional lead flow remains available.
- `/api/health`, data-quality, analysis, billing catalog, and Waffo webhook probes pass.
- Docker Compose restart and rollback preserve `postgres_data`.

**Release order**

1. Deploy schema and backward-compatible API.
2. Validate data contract and analysis on a staging dataset.
3. Enable Waffo Sandbox.
4. Run personal payment lifecycle tests.
5. Enable production Waffo credentials.
6. Enable institutional pilot API keys for the first approved organization.
7. Keep a previous release under `/opt/gfcri/releases/` for rollback.

## Risks and Decisions

- Waffo merchant approval, settlement countries, refund rules, tax scope, and webhook requirements are external gates.
- Public/official data and customer-provided data need separate source and licensing metadata.
- Company and security analysis requires entity mapping and financial-data semantics that are not present in the current global model; do not expose those target types until the adapter has coverage tests.
- Institutional pricing should be tied to data coverage, refresh cadence, custom connectors, API usage, and deployment mode; seats are a secondary delivery dimension.

