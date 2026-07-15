# GFCRI Personal Commercial Readiness Progress

Date: 2026-07-10
Scope: overseas personal subscription paid beta.

## Current Status

| Stream | Owner | Status | Output |
|---|---|---|---|
| ORCH | local | active | This progress board |
| BE | local | done | Billing API skeleton, Stripe checkout/webhook, subscription status |
| FE | local | done | Pricing page, checkout CTA, personal/institutional mode separation |
| DOCS | agent | done | `docs/personal-commercial-legal-pack.md` |
| OPS | agent | done | `docs/personal-commercial-ops-checklist.md` |
| QA | agent | done | `docs/personal-commercial-qa-matrix.md` |
| CR | local | queued | Final review and launch recommendation |

## Paid Beta Gates

| Gate | Status | Notes |
|---|---|---|
| Pricing page | done | Free, Pro Monthly, Pro Annual. |
| Checkout API | done_needs_keys | Stripe Checkout skeleton; requires env keys. |
| Webhook idempotency | done | `billing_events` table added. |
| Subscription status refresh | done | Frontend can refresh billing status. |
| Trial flow | existing | 7-day trial remains available. |
| Legal docs | in_progress | Terms/privacy/disclaimer pack delegated. |
| Email compliance | documented | OPS/QA docs include unsubscribe/CAN-SPAM checks. |
| Monitoring/alerts | documented | Still needs provider setup before public launch. |
| Data freshness | existing | Market-data cache and freshness endpoint exist. |
| 1Y trend | done | `daily_risk_index` backfilled on test environments. |

## Remaining Before Full Public Launch

- Configure real Stripe/Paddle product IDs and webhook secret.
- Configure production email provider and unsubscribe handling.
- Publish Terms, Privacy, Risk Disclaimer, Refund/Cancellation, and Cookie notice pages from `docs/personal-commercial-legal-pack.md`.
- Add uptime/error monitoring and data freshness alerts.
- Run checkout/webhook end-to-end in a Stripe test environment.
- Decide launch geography and data-source disclosure language.
