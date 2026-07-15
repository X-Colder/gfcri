# GFCRI Commercialization Progress Board

Date: 2026-07-10
Owner: GFCRI commercialization pod

## Objective

Move GFCRI Institutional Edition from technical readiness to a sellable paid pilot package, while keeping production-grade gaps visible and explicitly staged.

## Live Status

| Stream | Owner | Status | Current Output | Acceptance Gate |
|---|---|---|---|---|
| ORCH | local | done | This progress board and integration checklist | All workstreams mapped, verified, and sequenced |
| PM | agent | done | `docs/commercial-pilot-package.md` | SKU, POC scope, pricing assumptions, demo script, pilot metrics |
| DOCS | agent | done | `docs/commercial-trust-review-pack.md` | Data source notice, model limits, disclaimer, publication gate, FAQ |
| OPS | agent | done | `docs/commercial-delivery-runbook.md` | Deploy, refresh, smoke test, rollback, monitoring checklist |
| BE | local | done | `docs/commercial-engineering-gap-list.md` | API Key/RBAC/monitoring gaps scoped without overbuilding |
| QA | local | done | `docs/commercial-pilot-qa-matrix.md` | Happy path, data failure, auth, refresh, report, deployment checks |
| CR | local | done | Build/static checks completed | Blocking defects and residual risks documented |

## Phase 1: Paid Pilot Readiness

Target: make the product credible enough for paid POC conversations in 7-10 days.

| Deliverable | Status | Notes |
|---|---|---|
| Institutional SKU and paid pilot offer | done | PM workstream |
| Buyer demo script | done | PM workstream |
| 30-day pilot acceptance criteria | done | PM + QA |
| Data source and licensing caveat | done | DOCS workstream |
| Model limitation and non-advisory statement | done | DOCS workstream |
| Private deployment runbook | done | OPS workstream |
| Paid pilot launch sequence | done | `docs/commercial-paid-pilot-launch-sequence.md` |
| API/data freshness smoke checks | done_degraded | 192.168.139.51 frontend/API/Postgres healthy; market cache loaded; freshness is `degraded` due stale non-critical yfinance rate proxies |
| Build verification | done | `python3 -m compileall`, `pnpm build`, and `git diff --check` passed |

## Phase 2: Institution Beta Hardening

Target: allow a small number of institution users to rely on the pilot environment.

| Capability | Status | Notes |
|---|---|---|
| Data freshness monitoring surface | partial | API and institutional page now expose freshness; operations dashboard still needed |
| Job failure alerting | not_started | Needed for daily refresh and index publication failures |
| API key management | not_started | Needed before external client integration |
| RBAC and team seats | partial | Current auth has personal/institutional account type, not full tenant roles |
| Report audit trail | partial | Daily reports are persisted; approval/signature flow still missing |
| Report export governance | not_started | Needed for client-facing institutional use |

## Phase 3: Production Commercialization

Target: production institutional deployment with legal, operational, and support readiness.

| Gate | Status | Notes |
|---|---|---|
| Data vendor/legal review | not_started | Required for yfinance/Tushare/AKShare/OECD/FRED commercial use |
| SLA-backed market data source | not_started | Needed for scaled institutional deployment |
| SSO/SAML | not_started | Enterprise identity requirement |
| Multi-tenant isolation | not_started | Required for hosted multi-client service |
| Full backtest white paper | partial | Existing backtest docs exist; point-in-time/vintage policy still needed |
| Support and escalation process | partial | Pilot process is in the runbook; production SLA still needs customer agreement |

## Immediate Critical Path

1. Use the launch sequence for paid pilot conversations.
2. Select the first buyer workflow and confirm the 30-day acceptance criteria.
3. Decide whether to accept `degraded` freshness for pilot because stale `^IRX/^TNX` are FRED-covered rate proxies.
4. Implement only buyer-required engineering items from the gap list.

## Target Environment Smoke: 192.168.139.51

Run date: 2026-07-10

| Check | Result | Notes |
|---|---|---|
| SSH access | pass | Root passwordless access works. |
| Compose project | pass_for_pilot | `/opt/GFCRI` runs `postgres`, `api`, and `frontend`; `app` scheduler and `dashboard` are defined but not running. |
| Backup before sync | pass | Remote backup: `/opt/GFCRI-backup-20260710-remote-smoke.tar.gz`. |
| DB backup before import | pass | Postgres dump created inside container at `/tmp/gfcri-db-before-market-import-20260710.sql`. |
| API restart | pass | Restarted only `api`; scheduler/app was not started. |
| Market data import | pass | Imported 22,744 rows into `market_data_daily`; 45/45 expected tickers cached. |
| `/api/health` | pass | `status=ok`, `database=connected`. |
| `/api/risk-index/latest` | pass | Latest index: `2026-07-04`, GFCRI `41.34`, alert `yellow`. |
| `/api/commercial-readiness/data-freshness` | degraded | `coverage_pct=100.0`, latest trade date `2026-07-07`, no critical missing/stale tickers; stale non-critical proxies: `^IRX`, `^TNX`. |
| `/api/commercial-readiness/latest` | pass | Returns `data_freshness.status=degraded`; readiness score `90`, stage `pilot_ready`. |
| Frontend on `:3000` | pass | Nginx returns `200 OK`; frontend `/api/health` proxy returns API health. |

## Completion Log

- 2026-07-10: Started commercialization execution board and delegated PM/DOCS/OPS workstreams.
- 2026-07-10: Added engineering gap list and paid pilot QA matrix.
- 2026-07-10: PM workstream completed paid pilot package.
- 2026-07-10: DOCS workstream completed customer trust review pack.
- 2026-07-10: OPS workstream completed commercial delivery runbook.
- 2026-07-10: Added paid pilot launch sequence and completed static/build verification.
- 2026-07-10: Ran target-environment smoke on 192.168.139.51; API is healthy but pilot launch was initially blocked by empty market data cache.
- 2026-07-10: Imported offline market data cache, adjusted FRED-covered rate freshness logic, started frontend, and re-ran smoke; environment is pilot-ready with degraded freshness.
- 2026-07-10: Synced the 192.168.139.51 market data cache to openfs-meta2 (`116.196.107.195`) to avoid yfinance rate limiting. openfs-meta2 now has 23,452 `market_data_daily` rows across 45 tickers, latest trade date `2026-07-07`; API health is ok, frontend `:13000` returns 200, and commercial readiness reports `freshness=ok`, score `100`, stage `pilot_ready`. Target DB backup before import: `/tmp/gfcri-db-before-market-sync-20260710.sql`.
