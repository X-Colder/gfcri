# GFCRI Commercial Delivery Runbook

This runbook covers private deployment and pilot operation of GFCRI from the
current repository Docker Compose stack. It is grounded in the active Compose
services, `.env.example`, the market-data export/import scripts, the scheduler
entrypoint, and the market-data refresh job.

## Scope

Use this runbook for:

- Single-host private pilots using `docker-compose.yml`.
- Private-network deployments where all GFCRI services run behind a customer
  firewall, VPN, or reverse proxy.
- Offline or restricted-egress pilots that refresh market data through CSV
  export/import instead of direct yfinance access.
- Operational readiness checks before moving a pilot into paid production use.

Do not use this runbook as a substitute for customer-specific security review,
legal review, backup policy, or market-data licensing review.

## Deployment Modes

| Mode | Use Case | Services | Data Refresh | Notes |
| --- | --- | --- | --- | --- |
| Full private pilot | Default commercial pilot on one host | `postgres`, `app`, `api`, `frontend`, `dashboard` | Scheduled online refresh through `app` | Exposes host ports `15432`, `8000`, `3000`, and `8501`; protect with firewall/VPN. |
| Offline market-data pilot | Private host has no Yahoo/yfinance egress | All services, usually with manual imports | CSV export on connected host, CSV import on private host | Set `YFINANCE_DISABLE_ONLINE=true`; consider `MARKET_DATA_REFRESH_ENABLED=false` and operate imports on a fixed cadence. |
| Read-only demo | Show existing seeded data without running scheduled analysis | `postgres`, `api`, `frontend`, `dashboard` | None unless app is started manually | Only valid if the database is already seeded with market data and latest GFCRI outputs. |
| API/dashboard internal deployment | Internal users consume API and Streamlit only | `postgres`, `app`, `api`, `dashboard` | Scheduled or manual | Frontend can be omitted if a customer integrates directly with the API. |

The stock Compose file is PostgreSQL-local by default. `app`, `api`, and
`dashboard` set `POSTGRES_HOST=postgres` in Compose, so an external database
requires a Compose override or code/config change.

## Service Topology

| Service | Purpose | Port/Volume | Runtime Notes |
| --- | --- | --- | --- |
| `postgres` | Persistent GFCRI database | Host `15432` to container `5432`; volume `postgres_data` | Uses `postgres:15-alpine`; runs `db/init.sql` on a new volume; health check is `pg_isready`. |
| `app` | Scheduler and batch worker | No host port; volume `shared_output` at `/app/output` | Runs `python -m src.main`; waits for DB; optionally refreshes market cache on startup; runs initial daily analysis; schedules market refresh and daily analysis. |
| `api` | FastAPI service | Host `8000`; `shared_output` at `/app/output` | Exposes `/api/health` and product/commercial endpoints; API health checks DB connectivity. |
| `frontend` | Web frontend | Host `3000` to nginx `80` | Depends on `api`; no healthcheck or restart policy is defined in the current Compose file. |
| `dashboard` | Streamlit operations/research dashboard | Host `8501`; `shared_output` at `/app/output` | Runs `streamlit run dashboard/app.py`; depends on healthy Postgres. |

The `postgres_data` volume is the critical persistent state. Never use
`docker compose down -v` during normal deployment, rollback, or troubleshooting
unless the explicit goal is to destroy the database.

## Environment Variables

Create `.env` from `.env.example` on each private host and keep it outside
source control.

```bash
cp .env.example .env
```

Required commercial settings:

| Variable | Purpose | Pilot Guidance |
| --- | --- | --- |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Database name and credentials | Replace `changeme` before any customer pilot. |
| `APP_ENV` | Runtime label logged by `src.main` | Use `pilot`, `staging`, or `production`; avoid `development` in customer environments. |
| `LOG_LEVEL` | Python service log level | Start with `INFO`; temporarily use `DEBUG` only for active troubleshooting. |
| `TZ` | Container timezone convention | Keep `Asia/Shanghai` unless the customer operating window requires a documented change. |
| `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, `ANTHROPIC_MODEL` | LLM provider configuration | Required for full daily analysis/report generation. Validate provider reachability before launch. |

Scheduler settings:

| Variable | Purpose | Current Default |
| --- | --- | --- |
| `DAILY_RUN_HOUR`, `DAILY_RUN_MINUTE` | Daily GFCRI analysis cron time | `06:00` Asia/Shanghai |
| `MARKET_DATA_REFRESH_ENABLED` | Enables scheduled historical market-data cache refresh | `true` |
| `MARKET_DATA_REFRESH_HOUR`, `MARKET_DATA_REFRESH_MINUTE` | Market-data refresh cron time | `03:00` Asia/Shanghai |
| `MARKET_DATA_REFRESH_PERIOD` | Historical window passed to refresh | `2y` |
| `MARKET_DATA_REFRESH_ON_STARTUP` | Runs cache refresh before startup analysis | `true` |

Market-data settings:

| Variable | Purpose | Pilot Guidance |
| --- | --- | --- |
| `MARKET_DATA_MAX_STALE_DAYS` | Maximum tolerated cache staleness before missing tickers are refetched | Keep `7` for pilots unless data source latency is agreed. |
| `YFINANCE_BATCH_SIZE` | yfinance download batch size | `.env.example` uses `5`; lower if provider throttles. |
| `YFINANCE_SLEEP_SECONDS` | Delay between yfinance batches | `.env.example` uses `10`; increase for restricted networks. |
| `YFINANCE_DISABLE_ONLINE` | Prevents online yfinance fetches during collection | Set `true` for offline/private-import mode. |
| `TUSHARE_TOKEN` | Optional Tushare fallback token for supported tickers | Use only when the deployment is licensed and allowed to call Tushare. |
| `FRED_API_KEY` | Optional FRED API key consumed by the collector | Supported by code; add to `.env` when FRED access is part of the deployment. |

Publishing settings:

| Variable | Purpose | Pilot Guidance |
| --- | --- | --- |
| `WECHAT_APP_ID`, `WECHAT_APP_SECRET` | WeChat publishing credentials | Leave blank unless the pilot includes approved publishing. |
| `WECHAT_AUTO_PUBLISH` | Enables automatic WeChat publishing | Keep `false` for private pilots unless explicitly approved. |

## Initial Deployment

Run these commands from the GFCRI repository root on the private target host.

1. Confirm host prerequisites:

```bash
docker version
docker compose version
git rev-parse --short HEAD
```

2. Configure `.env`:

```bash
cp .env.example .env
```

Edit `.env` with customer-specific secrets and deployment mode. Minimum pilot
changes are a strong `POSTGRES_PASSWORD`, a non-development `APP_ENV`, data
source mode, and valid LLM settings if daily reports are expected.

3. Validate Compose configuration:

```bash
docker compose config
```

4. Start or upgrade the stack:

```bash
docker compose up -d --build
```

5. Confirm containers are running:

```bash
docker compose ps
```

Expected private-pilot ports:

- Frontend: `http://localhost:3000`
- API health: `http://localhost:8000/api/health`
- Streamlit dashboard: `http://localhost:8501`
- PostgreSQL host port: `15432`, for local admin access only

For production-like pilots, place the frontend/API/dashboard behind customer
TLS and access control. The Compose file publishes ports directly on the host;
host firewall rules must prevent public Postgres access.

## Scheduler Behavior

The `app` service runs `python -m src.main`.

Startup sequence:

1. Configure loguru logging with `LOG_LEVEL`.
2. Log the current `APP_ENV`.
3. Wait for PostgreSQL using `wait_for_db()`.
4. If `MARKET_DATA_REFRESH_ENABLED=true` and
   `MARKET_DATA_REFRESH_ON_STARTUP=true`, run
   `refresh_market_data_cache()` before analysis. Startup refresh failures are
   logged as non-fatal.
5. Run initial `run_daily_analysis()`. Startup analysis failures are logged as
   non-fatal.
6. Start APScheduler in the `Asia/Shanghai` timezone.
7. If enabled, schedule `refresh_market_data_cache()` daily at
   `MARKET_DATA_REFRESH_HOUR:MARKET_DATA_REFRESH_MINUTE` with job id
   `market_data_refresh` and `max_instances=1`.
8. Schedule `run_daily_analysis()` daily at
   `DAILY_RUN_HOUR:DAILY_RUN_MINUTE` with job id `daily_analysis`.

Operational implication: the container can be "running" even if startup refresh
or startup analysis failed. Always check logs, data freshness, and latest risk
outputs after deployment.

## Market Data Refresh and Import Flow

GFCRI stores canonical raw market closes in `market_data_daily` with unique
`(ticker, trade_date)` rows. Imports and refreshes upsert `close_price`,
`volume`, and `collected_at`, so re-importing the same date range is safe but
will overwrite matching prices.

### Online Scheduled Refresh

Use this mode when the private host is allowed to reach yfinance and any
configured fallback data providers.

Relevant settings:

```text
MARKET_DATA_REFRESH_ENABLED=true
MARKET_DATA_REFRESH_ON_STARTUP=true
MARKET_DATA_REFRESH_PERIOD=2y
YFINANCE_DISABLE_ONLINE=false
```

Manual refresh without publishing a risk index:

```bash
docker compose exec app python -c 'from src.scheduler.market_data_job import refresh_market_data_cache; print(refresh_market_data_cache("2y"))'
```

This calls `MarketDataCollector().refresh_market_data_cache()` through
`src/scheduler/market_data_job.py`. It fills the market-data cache only; it does
not publish a GFCRI risk index.

### Offline CSV Export

Run the export on a connected host where yfinance egress is healthy. The script
does not write to the database.

Host Python option:

```bash
python scripts/export_yfinance_market_data.py \
  --period 2y \
  --output /tmp/gfcri_market_data_2y.csv.gz \
  --batch-size 45
```

Container option on a connected GFCRI checkout:

```bash
mkdir -p output
docker compose run --rm --no-deps -v "$PWD/output:/app/output" app \
  python scripts/export_yfinance_market_data.py \
  --period 2y \
  --output /app/output/gfcri_market_data_2y.csv.gz \
  --batch-size 45
```

Expected CSV columns are:

```text
ticker,trade_date,close_price,volume
```

The export script prints `tickers_total`, `tickers_ok`, `rows`, `missing`, and
`output`. Treat a non-empty `missing` list or exit code `2` as an import gate:
review with the pilot owner before using that file for production analysis.

### Offline CSV Import

Transfer the `.csv.gz` to the private target host, then import it through the
`app` environment so the script uses Compose database settings.

```bash
docker cp /tmp/gfcri_market_data_2y.csv.gz gfcri_app:/tmp/gfcri_market_data_2y.csv.gz
docker compose exec app python scripts/import_market_data_csv.py \
  /tmp/gfcri_market_data_2y.csv.gz \
  --batch-size 5000
```

Expected output:

```text
imported_rows=<number>
```

Post-import database check:

```bash
docker compose exec -T postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT count(*) AS rows, max(trade_date) AS latest_trade_date FROM market_data_daily;"'
```

In offline pilots, use:

```text
YFINANCE_DISABLE_ONLINE=true
MARKET_DATA_REFRESH_ENABLED=false
MARKET_DATA_REFRESH_ON_STARTUP=false
```

Then operate CSV export/import on the agreed cadence. Re-enable scheduled
refresh only when the target network has approved egress and licensing.

## Health Checks

Run these after every deployment, rollback, import, or environment change.

Container state:

```bash
docker compose ps
docker compose logs --tail=100 postgres app api
```

PostgreSQL readiness:

```bash
docker compose exec -T postgres sh -lc 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

API health:

```bash
curl -fsS http://localhost:8000/api/health
```

Expected API health shape:

```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "..."
}
```

Frontend and dashboard HTTP checks:

```bash
curl -fsSI http://localhost:3000
curl -fsSI http://localhost:8501
```

Market-data freshness:

```bash
curl -fsS http://localhost:8000/api/commercial-readiness/data-freshness
```

Latest model outputs:

```bash
curl -fsS http://localhost:8000/api/risk-index/latest
curl -fsS http://localhost:8000/api/reports/latest
curl -fsS http://localhost:8000/api/commercial-readiness/private-deployment
```

If `/api/risk-index/latest` or `/api/reports/latest` returns `404`, the API may
be healthy but no successful analysis has been persisted. Check `app` logs and
run the full smoke test when appropriate.

Scheduler evidence:

```bash
docker compose logs app --tail=200
```

Look for:

- `Database connection established`
- `Market data refresh configured`
- `Scheduler configured`
- `Scheduler started`
- `Market data cache refresh completed`
- `Daily risk index saved` or equivalent successful analysis log

## Smoke Tests

Use the limited smoke for every deploy. Use the full smoke before pilot launch,
after data imports, and after changing data-source or LLM settings.

### Limited Smoke

```bash
docker compose config
docker compose up -d --build
docker compose ps
curl -fsS http://localhost:8000/api/health
curl -fsS http://localhost:8000/api/commercial-readiness/data-freshness
curl -fsS http://localhost:8000/api/commercial-readiness/private-deployment
curl -fsSI http://localhost:3000
curl -fsSI http://localhost:8501
```

Pass criteria:

- All expected containers are `running`.
- API health returns `status=ok` and `database=connected`.
- Data freshness endpoint responds without a server error.
- Frontend and dashboard return HTTP success or redirect.
- No fresh traceback appears in `docker compose logs --tail=200 app api`.

### Market-Data Smoke

```bash
docker compose exec app python -c 'from src.scheduler.market_data_job import refresh_market_data_cache; print(refresh_market_data_cache("2y"))'
docker compose exec -T postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT count(*) AS rows, min(trade_date) AS first_trade_date, max(trade_date) AS latest_trade_date FROM market_data_daily;"'
curl -fsS http://localhost:8000/api/commercial-readiness/data-freshness
```

Pass criteria:

- Refresh prints a non-zero `rows` count and non-zero `tickers` count, or the
  offline mode has a documented imported dataset.
- `latest_trade_date` is within the agreed pilot staleness threshold.
- Data-freshness response does not report a launch-blocking cache gap.

### Full Analysis Smoke

Avoid running this during the scheduled daily analysis window.

```bash
docker compose exec app python -c 'from src.scheduler.daily_job import run_daily_analysis; run_daily_analysis()'
curl -fsS http://localhost:8000/api/risk-index/latest
curl -fsS http://localhost:8000/api/reports/latest
curl -fsS http://localhost:8000/api/commercial-readiness/latest
```

Pass criteria:

- Manual daily analysis exits successfully.
- Latest risk index endpoint returns a current `index_date`, `gfcri_value`, and
  `alert_level`.
- Latest report endpoint returns the current report.
- Commercial readiness endpoint has no newly introduced blocker.

## Backup Plan

Back up before every upgrade, rollback, data import, or destructive admin task.

Database backup:

```bash
mkdir -p backups
docker compose exec -T postgres sh -lc 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  > "backups/gfcri_$(date +%Y%m%d_%H%M%S).sql"
```

Record release metadata:

```bash
git rev-parse HEAD
docker compose images
docker compose ps
```

Operational backup requirements:

- Store production backups outside the application host or in customer-approved
  durable storage.
- Test restore before commercial launch.
- Keep the previous deployable source revision or image artifact available.
- Keep `.env` backup in a secret store, not in Git.

## Rollback Plan

Rollback target depends on the failure mode.

### Config-Only Rollback

Use when a bad `.env` change broke startup, provider access, schedule timing, or
publishing.

1. Restore the previous `.env` from the secret store.
2. Restart only services that consume the changed variables:

```bash
docker compose up -d app api dashboard
```

3. Re-run health checks and limited smoke.

### Application Rollback

Use when a code/image deployment introduced API, frontend, scheduler, or report
generation regressions.

1. Confirm a database backup exists.
2. Check out the previous approved revision or redeploy the previous image
   artifact.
3. Rebuild and restart application services:

```bash
docker compose up -d --build app api frontend dashboard
```

4. Do not recreate `postgres_data`.
5. Run limited smoke, then full analysis smoke if the incident touched data,
   scheduler, or report generation.

### Data Import Rollback

CSV import upserts `market_data_daily`; it does not retain old row versions.
Use the pre-import database backup if imported prices, dates, or tickers are
wrong.

Restore only during a maintenance window:

```bash
docker compose stop app api dashboard frontend
docker compose exec -T postgres sh -lc 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  < backups/<pre_import_backup>.sql
docker compose up -d app api frontend dashboard
```

After restore, rerun the post-import database check and API health checks.

## Monitoring Gaps

Current repository gaps to close or explicitly accept before production:

- Only `postgres` has a Compose healthcheck. `app`, `api`, `frontend`, and
  `dashboard` do not define container healthchecks.
- `/api/health` verifies API process and database connectivity, but not
  scheduler recency, last successful analysis, market-data freshness, LLM
  provider status, or report generation.
- Startup refresh and startup analysis failures are logged as non-fatal; they
  do not make the `app` container unhealthy.
- Logs remain in Docker logs unless the deployment adds centralized log
  shipping.
- No built-in alerting exists for failed scheduled jobs, stale market data,
  provider throttling, LLM errors, disk pressure, or backup failure.
- No automated backup or restore verification is defined in Compose.
- Database schema initialization uses `db/init.sql` only for a fresh
  `postgres_data` volume. Existing production schema changes need an explicit
  migration process.
- API CORS currently allows localhost frontend origins in code. A customer
  domain needs reverse-proxy same-origin routing or a reviewed API CORS change.
- Postgres is published on host port `15432`; production hosts need firewall or
  network policy that blocks external access.

Minimum pilot monitoring to add externally:

- Container uptime and restart count for all services.
- HTTP probe for `/api/health`.
- HTTP probe for `/api/commercial-readiness/data-freshness`.
- Daily check that `daily_risk_index.index_date` and `daily_reports.report_date`
  are current.
- Alert on `app` logs containing scheduler failure, market-data refresh failure,
  LLM/provider failure, or import failure.
- Disk usage alert for Docker volumes and host filesystem.
- Backup job success and restore-drill evidence.

## Support Process

Pilot support owner:

- Maintain the private host inventory, Git revision, `.env` owner, backup
  location, customer contact, and allowed maintenance windows.
- Keep a deployment log with timestamp, operator, Git SHA, data-refresh mode,
  commands run, smoke-test result, and rollback artifact.

Severity guide:

| Severity | Definition | First Response |
| --- | --- | --- |
| SEV-1 | Customer cannot access GFCRI, database is unavailable, or wrong/stale data is being shown as current | Acknowledge immediately, freeze deployments, preserve logs, start rollback or restore path. |
| SEV-2 | Daily analysis/report failed, market data is stale beyond threshold, or API partially degraded | Triage same business day, run data and full-analysis smoke after fix. |
| SEV-3 | UI issue, non-critical endpoint issue, dashboard issue, or pilot feedback | Batch into next maintenance window unless customer impact escalates. |

Support intake checklist:

- Customer, environment, public/private URL, and affected user path.
- Timestamp and timezone.
- Screenshot or API response body.
- Current Git SHA and `docker compose ps`.
- Last successful `/api/health`, data freshness response, and latest risk
  endpoint response.
- Relevant `docker compose logs --tail=300 app api postgres`.
- Whether market data is online refresh or offline import mode.

Escalation path:

1. OPS checks host, containers, logs, backups, and rollback readiness.
2. Backend owner checks API, scheduler, database queries, and provider errors.
3. Data/model owner checks market-data freshness, missing tickers, and GFCRI
   output plausibility.
4. Product owner communicates pilot impact, customer-facing status, and any
   analysis caveats.

Pilot communications:

- State whether the issue is availability, data freshness, report generation, or
  presentation.
- Include the latest trustworthy `index_date` and data freshness state.
- Avoid investment advice language. GFCRI is a risk-monitoring product, not a
  trading recommendation engine.

## Production Readiness Checklist

Complete before a paid production rollout:

- [ ] `.env` contains no default `changeme` values.
- [ ] LLM provider credentials are valid and scoped to the deployment.
- [ ] Market-data source mode is documented: online scheduled refresh or offline
      CSV import.
- [ ] Market-data licensing and customer egress approvals are documented.
- [ ] `YFINANCE_DISABLE_ONLINE` and `MARKET_DATA_REFRESH_ENABLED` match the
      deployment mode.
- [ ] `WECHAT_AUTO_PUBLISH=false` unless customer publishing is explicitly in
      scope.
- [ ] Host firewall blocks public access to Postgres port `15432`.
- [ ] Frontend, API, and dashboard are behind customer-approved TLS and access
      control.
- [ ] API CORS/domain behavior is validated for the customer access path.
- [ ] Database backup job exists, runs automatically, and has a tested restore.
- [ ] Previous release artifact or Git SHA is available for rollback.
- [ ] `docker compose config` passes on the target host.
- [ ] Limited smoke passes.
- [ ] Market-data smoke passes.
- [ ] Full analysis smoke passes after valid data and LLM settings are present.
- [ ] `/api/commercial-readiness/latest` and
      `/api/commercial-readiness/private-deployment` are reviewed with the pilot
      owner.
- [ ] External monitoring covers API health, data freshness, latest analysis
      date, container restarts, disk, logs, and backups.
- [ ] Support roster, severity guide, and maintenance window are agreed with the
      customer.
- [ ] Deployment log records host, Git SHA, `.env` owner, backup location,
      service versions, smoke-test evidence, and rollback command.

## Quick Command Reference

Start or upgrade:

```bash
docker compose up -d --build
```

Status:

```bash
docker compose ps
docker compose logs --tail=100 app api postgres
```

API health:

```bash
curl -fsS http://localhost:8000/api/health
```

Manual market-data refresh:

```bash
docker compose exec app python -c 'from src.scheduler.market_data_job import refresh_market_data_cache; print(refresh_market_data_cache("2y"))'
```

Manual daily analysis:

```bash
docker compose exec app python -c 'from src.scheduler.daily_job import run_daily_analysis; run_daily_analysis()'
```

Data freshness:

```bash
curl -fsS http://localhost:8000/api/commercial-readiness/data-freshness
```

Database backup:

```bash
mkdir -p backups
docker compose exec -T postgres sh -lc 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  > "backups/gfcri_$(date +%Y%m%d_%H%M%S).sql"
```
