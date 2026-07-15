# GFCRI Paid Pilot QA Matrix

Date: 2026-07-10
Scope: 7-10 day paid pilot launch and 30-day pilot operation.

## Release Gates

| Gate | Required For Pilot | Pass Criteria |
|---|---:|---|
| Frontend build | yes | `pnpm build` completes |
| Python compile | yes | `python3 -m compileall -q api src scripts` completes |
| API health | yes | `/api/health` returns success |
| Database migration/idempotency | yes | Existing DB starts without destructive migration |
| Data freshness endpoint | yes | Commercial readiness returns freshness status |
| Risk index quality gate | yes | Blocked data run does not overwrite latest reliable index |
| Institutional page | yes | Page loads data quality, freshness, radar, package sections |
| Methodology/trust page | yes | Source tiers, limitations, disclaimer visible |
| Report API | yes | Latest report or institutional report endpoint returns structured output |
| Private deployment runbook | yes | Operator can follow start, smoke, rollback steps |

## Functional Test Matrix

| Area | Scenario | Steps | Expected Result |
|---|---|---|---|
| Auth | Personal user starts trial | Register/login, start 7-day trial | Plan becomes trial; Pro features unlock; no payment info required |
| Auth | Institutional user does not use trial | Mark account as institutional, open gated features | Institutional access works; personal trial flow is not required |
| Auth | Expired or invalid token | Load app with invalid token | User is treated as logged out or receives 401 without crash |
| Dashboard | Latest index loads | Open dashboard with seeded DB | GFCRI value, alert level, drivers, quality status render |
| Dashboard | Blocked data update | Insert blocked quality event newer than latest index | Dashboard shows data quality alert and keeps last reliable index |
| Commercial readiness | Freshness ok/degraded/blocked | Query `/api/commercial-readiness/latest` under three data states | `data_freshness.status` reflects market data state |
| Institutional | Commercial readiness cards | Open Institutional page | Data depth, market freshness, causal rigor, report quality, private delivery render |
| Institutional radar | Source partial failure | Simulate feed error or use persisted fallback | Page shows partial error without failing whole workspace |
| Methodology | Trust disclosures | Open Methodology page | Source tier mix, limitations, formulas, non-advisory language visible |
| Reports | Institutional report | Call institutional report endpoint | Evidence table and quality controls are present |
| Market data import | Offline CSV import | Run import script with valid gzip CSV | Rows upsert into `market_data_daily` |
| Scheduler | Refresh before analysis | Start scheduler with refresh enabled | Market refresh runs before daily analysis on startup |
| API | Slow external source | Disable online yfinance or block source | System degrades gracefully; publication gate blocks incomplete core data |
| i18n | Chinese/English toggle | Switch language on dashboard/institutional pages | No mixed key names or broken dynamic labels in core flows |
| Mobile layout | Institutional page narrow viewport | Open on mobile width | Cards stack without overlap; long labels wrap |
| Deployment | Compose stack start | Start Postgres + API + frontend | Services healthy; API responds; frontend proxies `/api` |
| Rollback | Source rollback | Follow runbook rollback steps | Previous known-good source/config can be restored |

## Data Failure Cases

| Failure | Expected Behavior | Pilot Severity |
|---|---|---|
| Critical ticker missing | Official index update blocked | Blocking |
| Critical ticker stale | Official index update blocked | Blocking |
| Non-critical ticker missing | Freshness degraded; index may proceed if core z-scores are available | Warning |
| FRED unavailable | Market-derived values still render; FRED overlays absent | Warning |
| Institutional RSS unavailable | Radar uses cached/persisted data or shows partial error | Warning |
| DB unavailable | API health fails; frontend should not show stale success | Blocking |
| LLM unavailable | Structured report still renders without narrative | Warning |

## Pilot Acceptance Criteria

The 30-day paid pilot passes if:

- At least 20 business-day observations are available or blocked runs are explicitly explained.
- No incomplete critical-data run overwrites `daily_risk_index`.
- Dashboard, Institutional page, Methodology, and report endpoints remain usable.
- Operators can identify data freshness and source health status daily.
- Client receives at least one weekly risk brief or walkthrough using the product.
- Client can state whether GFCRI improves research/risk/advisor workflow clarity.
- Any production blockers are logged with owner, severity, and target phase.

## Manual Verification Commands

```bash
python3 -m compileall -q api src scripts
cd frontend && pnpm build
curl -I http://127.0.0.1:5173/
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/commercial-readiness/latest
```

## Known Residual Risks

- Full API route tests are not yet automated.
- Local Python environment may miss `psycopg2`; Docker/API image should install from `requirements.txt`.
- Data vendor/legal approval is not a QA task but is a commercial blocker before production use.
- SSO/SAML, full RBAC, signed exports, and audit logs are production-grade requirements, not Phase 1 launch gates.
