# GFCRI Overseas Personal Subscription Launch Operations Checklist

Scope: overseas personal subscription launch operations for GFCRI. This checklist is grounded in the current repo where possible and calls out external commercialization controls that must be configured outside source control.

## 1. Repo-Backed Runtime Baseline

- [ ] Confirm production host, domain, and deployment path are recorded in the launch ticket.
- [ ] Confirm `docker-compose.yml` is the source of truth for the launch stack:
  - `postgres`: Postgres 15, host port `15432`, persistent `postgres_data`, `pg_isready` healthcheck.
  - `app`: scheduled GFCRI engine process, command `python -m src.main`, `shared_output` mounted at `/app/output`.
  - `api`: FastAPI service on host port `8000`, `OUTPUT_DIR=/app/output`, exposes `/api/health` and product APIs.
  - `frontend`: nginx static frontend on host port `3000`, built from `frontend/Dockerfile`.
  - `dashboard`: Streamlit dashboard on host port `8501`.
- [ ] Confirm only approved ports are publicly reachable. Default public surface should be `80/443`; direct `8000`, `3000`, `8501`, and `15432` exposure should be blocked unless intentionally private/VPN-only.
- [ ] Confirm `postgres_data` and `shared_output` volumes are not removed during deployment or rollback.
- [ ] Confirm `.env` exists on the production host and is not copied into source control or frontend artifacts.

## 2. Environment Variables And Secret Inventory

Repo-backed variables already represented in `.env.example`:

- [ ] `APP_ENV=production`.
- [ ] `LOG_LEVEL=INFO` or stricter production value.
- [ ] `TZ=Asia/Shanghai` unless overseas launch operations require a different canonical timezone.
- [ ] `POSTGRES_HOST=postgres`.
- [ ] `POSTGRES_PORT=5432`.
- [ ] `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` set to production-only values.
- [ ] `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, `ANTHROPIC_MODEL` set if paid features or report generation depend on LLM output.
- [ ] Market refresh controls reviewed:
  - `MARKET_DATA_REFRESH_ENABLED=true`.
  - `MARKET_DATA_REFRESH_PERIOD=2y`.
  - `MARKET_DATA_MAX_STALE_DAYS=7` or stricter launch threshold.
  - `MARKET_DATA_REFRESH_ON_STARTUP` explicitly chosen for launch.
  - `YFINANCE_BATCH_SIZE`, `YFINANCE_SLEEP_SECONDS`, `YFINANCE_DISABLE_ONLINE`, `TUSHARE_TOKEN` set for the production data plan.
- [ ] WeChat variables are either intentionally disabled for overseas launch or validated if still used:
  - `WECHAT_APP_ID`.
  - `WECHAT_APP_SECRET`.
  - `WECHAT_AUTO_PUBLISH=false` unless publication is approved.

Subscription commercialization variables to add to the production secret store before launch:

- [ ] `PUBLIC_APP_BASE_URL`.
- [ ] `PUBLIC_API_BASE_URL`.
- [ ] `PAYMENT_PROVIDER`.
- [ ] `PAYMENT_PUBLIC_KEY`.
- [ ] `PAYMENT_SECRET_KEY`.
- [ ] `PAYMENT_WEBHOOK_SECRET`.
- [ ] `PAYMENT_PRICE_PERSONAL_MONTHLY`.
- [ ] `PAYMENT_PRICE_PERSONAL_ANNUAL`.
- [ ] `PAYMENT_SUCCESS_URL`.
- [ ] `PAYMENT_CANCEL_URL`.
- [ ] `EMAIL_PROVIDER`.
- [ ] `EMAIL_API_KEY`.
- [ ] `EMAIL_FROM_ADDRESS`.
- [ ] `EMAIL_REPLY_TO_ADDRESS`.
- [ ] `EMAIL_UNSUBSCRIBE_SECRET` or provider equivalent.
- [ ] `SUPPORT_EMAIL`.
- [ ] `PRIVACY_POLICY_URL`.
- [ ] `TERMS_URL`.
- [ ] `ERROR_MONITORING_DSN`.
- [ ] `UPTIME_MONITOR_WEBHOOK_URL`.
- [ ] `OPS_ALERT_CHANNEL`.

Secret handling gate:

- [ ] No provider secret appears in git history, frontend `dist`, browser network responses, logs, screenshots, or support exports.
- [ ] Production secrets are rotated from any test values used during launch rehearsal.
- [ ] At least two operators have break-glass read access to production secrets, and access is logged.

## 3. Payment Provider Readiness

- [ ] Overseas payment provider account is approved for the target countries, currency, tax collection model, refunds, and dispute handling.
- [ ] Personal monthly and annual prices are created in the provider dashboard and mapped to `PAYMENT_PRICE_PERSONAL_MONTHLY` and `PAYMENT_PRICE_PERSONAL_ANNUAL`.
- [ ] Checkout success and cancel URLs route back to the production frontend.
- [ ] Webhook endpoint is deployed over HTTPS and receives only signed events.
- [ ] `PAYMENT_WEBHOOK_SECRET` is configured only server-side.
- [ ] Webhook event allowlist is documented, including subscription created, payment succeeded, payment failed, subscription updated, subscription canceled, refund, dispute opened, and dispute closed.
- [ ] Webhook handler is idempotent by provider event ID.
- [ ] Test-mode payment keys cannot be used in production.
- [ ] Launch rehearsal covers:
  - Successful monthly subscription.
  - Successful annual subscription.
  - Failed payment and retry path.
  - Cancellation at period end.
  - Refund path.
  - Duplicate webhook delivery.
- [ ] Customer entitlement state is visible in support tooling or an operator query.
- [ ] No paid entitlement is granted until the payment provider confirms a successful payment or active trial policy.

## 4. Email Provider And Unsubscribe

- [ ] Email provider domain authentication is complete for SPF, DKIM, and DMARC.
- [ ] `EMAIL_FROM_ADDRESS` uses the authenticated domain.
- [ ] Transactional templates exist for signup, payment receipt, failed payment, cancellation, password/account actions if applicable, and support contact.
- [ ] Marketing or product update emails are separated from transactional emails.
- [ ] Every non-transactional email includes a working unsubscribe link.
- [ ] Unsubscribe requests are honored immediately and persisted outside volatile container storage.
- [ ] Bounce and complaint webhooks are configured and monitored.
- [ ] Support inbox ownership and response target are documented.
- [ ] Seed-list test confirms overseas users receive mail in primary inboxes, not spam, before launch.

## 5. Uptime, Error, And Log Monitoring

Required probes:

- [ ] Public frontend HTTPS returns `200`.
- [ ] API health probe returns success from `GET /api/health`.
- [ ] Latest risk probe returns success from `GET /api/risk-index/latest`.
- [ ] Data freshness probe returns success from `GET /api/commercial-readiness/data-freshness`.
- [ ] Payment webhook endpoint returns expected status for signed provider test events.
- [ ] Email provider webhooks return expected status for signed provider test events if implemented.

Alert thresholds:

- [ ] Page on-call when `/api/health` fails twice in 5 minutes or reports `database=error`.
- [ ] Page on-call when frontend HTTPS fails twice in 5 minutes.
- [ ] Page on-call when `/api/risk-index/latest` returns `404` or `5xx` after a successful production data run.
- [ ] Page on-call when payment webhook error rate exceeds 1% over 10 minutes.
- [ ] Notify ops when email bounce or complaint rate exceeds provider safe limits.
- [ ] Capture container logs for `gfcri_api`, `gfcri_app`, `gfcri_frontend`, `gfcri_dashboard`, and `gfcri_postgres`.
- [ ] Error monitoring includes API exceptions, frontend runtime errors, payment webhook failures, and subscription entitlement failures.

Known repo caveat:

- [ ] Add external uptime monitoring because the current Compose file only defines a container healthcheck for `postgres`; `api`, `app`, `frontend`, and `dashboard` rely on restart policy or external probes.

## 6. Data Freshness Alerts

Operational source of truth:

- [ ] Use `GET /api/commercial-readiness/data-freshness` as the launch freshness gate.
- [ ] Use `GET /api/risk-index/latest` to confirm the published GFCRI value, alert level, and index date are current.
- [ ] Treat a healthy `/api/health` response as necessary but not sufficient for launch; it verifies API process and database connectivity, not current market data.

Alert rules:

- [ ] No-go if freshness status is `blocked`.
- [ ] No-go if critical tickers are missing or stale.
- [ ] No-go if latest trade date is older than the accepted market calendar window for launch.
- [ ] Warn but allow operator review if freshness status is `degraded` only because non-critical proxies are stale.
- [ ] Page ops if the scheduled data refresh fails for two consecutive runs.
- [ ] Page ops if `MARKET_DATA_MAX_STALE_DAYS` is exceeded for any critical source.
- [ ] Record daily freshness status, latest trade date, coverage percent, stale tickers, missing tickers, and operator decision.

Daily launch-week check:

```bash
curl -fsS http://localhost:8000/api/commercial-readiness/data-freshness
curl -fsS http://localhost:8000/api/risk-index/latest
```

## 7. Backup And Restore

Pre-launch backup:

- [ ] Confirm the database host, container, database name, and production volume name.
- [ ] Take a logical Postgres backup before payment launch and before every schema-impacting deploy.
- [ ] Store backup outside the Docker volume and outside the app host if possible.
- [ ] Encrypt backup at rest and restrict restore access.
- [ ] Capture backup metadata: timestamp, git commit, image tags, database name, row counts for subscription/account/payment tables if present, and `market_data_daily` latest trade date.

Minimum backup command pattern:

```bash
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "gfcri-prod-$(date +%Y%m%d-%H%M%S).sql"
```

Restore rehearsal:

- [ ] Restore the latest backup into a non-production database before launch.
- [ ] Run post-restore checks:
  - `GET /api/health` returns `status=ok` and `database=connected`.
  - `GET /api/commercial-readiness/data-freshness` returns acceptable status.
  - `GET /api/risk-index/latest` returns the expected latest index.
  - Subscription entitlements, payment records, and unsubscribe state are present if those tables exist.
- [ ] Document expected restore time objective and recovery point objective for launch.
- [ ] Keep at least one known-good backup from before subscription launch until the first billing cycle closes.

## 8. Deployment And Smoke Tests

Build gates:

- [ ] Frontend build passes from `frontend/package.json`: `pnpm build` runs `vue-tsc -b && vite build`.
- [ ] Frontend Docker build completes from `frontend/Dockerfile`.
- [ ] API image builds from `api/Dockerfile`.
- [ ] Root app image builds for `app` and `dashboard` services.
- [ ] No build output contains provider secrets.

Deployment gates:

- [ ] `docker compose config` succeeds with the production `.env`.
- [ ] `docker compose up -d --build` starts required services.
- [ ] `docker compose ps` shows expected containers running.
- [ ] Postgres healthcheck is healthy before `api`, `app`, or `dashboard` validation.
- [ ] Frontend serves the built app on port `3000` or the configured reverse proxy.

Production smoke commands:

```bash
curl -fsS http://localhost:8000/api/health
curl -fsS http://localhost:8000/api/risk-index/latest
curl -fsS http://localhost:8000/api/commercial-readiness/data-freshness
curl -fsSI http://localhost:3000/
```

User-path smoke:

- [ ] Anonymous visitor can load the frontend.
- [ ] Latest GFCRI value renders from `/api/risk-index/latest`.
- [ ] Data freshness state is visible or available to the commercial readiness surface.
- [ ] Subscription checkout opens with the correct personal plan and currency.
- [ ] Payment success grants access or records entitlement.
- [ ] Cancellation or failed payment removes or downgrades entitlement according to policy.
- [ ] Email receipt or welcome message is delivered.
- [ ] Unsubscribe link works for non-transactional mail.
- [ ] Mobile and desktop first screens load without console errors.

## 9. Incident Severity And Response

Severity definitions:

- [ ] SEV1: total frontend or API outage, payment provider charging incorrectly, paid users unable to access subscribed content, data corruption, leaked secret, or materially false public GFCRI value.
- [ ] SEV2: degraded API or frontend, delayed data refresh beyond launch threshold, payment webhook backlog, high email bounce/complaint rate, or partial entitlement failures.
- [ ] SEV3: non-critical stale proxy data, dashboard-only issue, minor copy/config issue, or isolated customer support issue without billing impact.

Response targets:

- [ ] SEV1 acknowledged within 10 minutes, public checkout paused if billing or entitlement integrity is at risk.
- [ ] SEV2 acknowledged within 30 minutes, operator update posted every hour until resolved.
- [ ] SEV3 triaged within one business day.

Incident record must include:

- [ ] Start time, detection source, affected services, affected users, payment impact, data freshness impact, current git commit/image tags, last successful `/api/health`, last successful `/api/risk-index/latest`, last successful `/api/commercial-readiness/data-freshness`, owner, mitigation, rollback decision, and customer communication decision.

## 10. Rollback

Rollback triggers:

- [ ] Any SEV1 caused by the launch deploy.
- [ ] Payment webhook failures that can duplicate, miss, or incorrectly grant entitlements.
- [ ] API returns `5xx` for health or latest risk endpoints after restart.
- [ ] Frontend cannot load the checkout or paid-user path.
- [ ] Data freshness gate moves from acceptable to `blocked` after deploy.

Rollback procedure:

- [ ] Freeze new deploys and assign incident owner.
- [ ] Disable checkout or hide paid upgrade entry points if billing integrity is uncertain.
- [ ] Preserve logs before restart or image rollback.
- [ ] Restore previous application image or previous git commit deployment.
- [ ] Do not delete `postgres_data` or `shared_output`.
- [ ] Re-run smoke tests:
  - `GET /api/health`.
  - `GET /api/risk-index/latest`.
  - `GET /api/commercial-readiness/data-freshness`.
  - Frontend `GET /`.
  - Payment webhook signed test event if checkout remains enabled.
- [ ] If database rollback is required, restore only from an approved backup and reconcile payment provider state before reopening checkout.
- [ ] Record customer communication and refund decisions when payment state was affected.

## 11. Launch / No-Go Gates

Launch is allowed only when all required gates pass:

- [ ] Production `.env` exists, secrets are production values, and no secret is exposed client-side.
- [ ] `docker-compose.yml` production stack starts cleanly.
- [ ] Frontend build passes: `pnpm build`.
- [ ] `GET /api/health` returns `status=ok` and `database=connected`.
- [ ] `GET /api/risk-index/latest` returns a current GFCRI value, index date, and alert level.
- [ ] `GET /api/commercial-readiness/data-freshness` is `ok`, or `degraded` only with written operator acceptance for non-critical stale proxies.
- [ ] Payment provider live keys, prices, success URL, cancel URL, and signed webhook are verified.
- [ ] Email provider domain auth, transactional templates, unsubscribe, bounce, and complaint handling are verified.
- [ ] Uptime and error monitoring alerts reach the operator channel.
- [ ] Latest database backup exists and restore rehearsal has passed.
- [ ] Rollback path is documented with previous image/commit and database restore point.
- [ ] Support email, privacy policy, terms, and refund/cancellation policy are live.
- [ ] At least one full paid subscription rehearsal succeeds in production live mode with a low-value plan or approved test path.

Automatic no-go:

- [ ] Any production secret is missing or exposed.
- [ ] `/api/health` fails or reports database error.
- [ ] `/api/risk-index/latest` fails without an accepted reason.
- [ ] `/api/commercial-readiness/data-freshness` is `blocked`.
- [ ] Payment webhook signature verification is not working.
- [ ] Email unsubscribe is not working for non-transactional mail.
- [ ] No current backup exists.
- [ ] No named rollback owner is available during launch.

Launch sign-off:

- [ ] OPS owner:
- [ ] Product owner:
- [ ] Support owner:
- [ ] Launch date and time:
- [ ] Git commit / image tags:
- [ ] Backup file / location:
- [ ] Final decision: launch / no-go
