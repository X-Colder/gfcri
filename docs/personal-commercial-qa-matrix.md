# GFCRI Personal Paid Beta QA Matrix

## Scope

This matrix covers overseas personal subscription commercialization readiness for the paid beta. It is focused on user-visible billing, access control, email consent, product disclaimers, data trust signals, and launch smoke validation.

Assumptions:

- All payment tests run in payment-provider test mode unless beta operations explicitly approves a live low-value transaction.
- "Pro" means the paid personal subscription entitlement.
- "Institutional" means an organization, team, enterprise, research, or managed-account entitlement that must not be confused with a personal paid account.
- Dates, timestamps, invoice periods, trial periods, and cancellation deadlines must be displayed with clear timezone behavior for overseas users.

## Readiness Gate

| Gate | Required Result |
| --- | --- |
| P0 coverage | Every P0 case below is executed and passed before overseas paid beta launch. |
| Billing safety | Checkout, webhook, cancellation, refund, and subscription-state tests are verified in test mode with saved evidence. |
| Access safety | Pro-only functionality is inaccessible to free, expired, canceled, and failed-payment users. |
| Trust safety | Disclaimers, data freshness, and 1Y trend limitations are visible before users can rely on paid outputs. |
| Operational safety | Launch smoke commands complete against staging and production health endpoints before traffic is opened. |

## Test Data

| Persona | Required State |
| --- | --- |
| Anonymous overseas visitor | No session, non-China IP/VPN path if available, browser locale `en-US`. |
| New personal user | Verified email, no trial, no subscription. |
| Trial user | Trial active, trial ending within 24 hours, and trial expired variants. |
| Active Pro user | Personal paid subscription active with current period end. |
| Past-due user | Payment failed, subscription status `past_due` or equivalent. |
| Canceled user | Canceled immediately and canceled-at-period-end variants. |
| Refunded user | Refund issued with entitlement behavior verified. |
| Institutional user | Organization-managed entitlement, no personal subscription. |
| Email-only lead | Signed up for updates, not a product account. |

## Functional Matrix

| ID | Area | Scenario | Steps | Expected Result | Priority | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| PC-001 | Pricing page | Overseas visitor can understand the paid beta offer | Open pricing while logged out from desktop and mobile using `en-US`; review plan name, price, billing interval, trial terms, Pro features, limits, disclaimer link, cancellation/refund policy link. | Page renders without auth errors; price and interval are unambiguous; paid beta and personal-use scope are clear; no institutional claims are shown for personal plan. | P0 | Screenshot desktop/mobile. |
| PC-002 | Pricing page | Price formatting is overseas-ready | Change browser locale/timezone where feasible; verify currency symbol, decimal formatting, tax/VAT wording, and billing interval. | Price display is stable and does not imply unsupported tax handling; currency and billing interval match checkout. | P0 | Screenshot plus checkout comparison. |
| PC-003 | Pricing page | CTA routing is correct for anonymous and logged-in users | Click primary pricing CTA while logged out, then logged in as free user. | Logged-out users are prompted to sign in or create account; logged-in users proceed to checkout/trial path; return URL preserves intent. | P0 | URL trace. |
| PC-004 | Trial | Eligible personal user starts trial once | Create new personal account; start trial; refresh; sign out/in. | Trial is created once; trial dates persist; Pro entitlement is active during trial; duplicate starts are blocked. | P0 | Account state before/after. |
| PC-005 | Trial | Trial ineligible user cannot restart trial | Use user with prior expired trial or canceled paid account; attempt trial start from pricing and account settings. | UI explains ineligibility; no new free trial is created; checkout path remains available. | P0 | Screenshot and server state. |
| PC-006 | Trial | Trial expiry transitions access correctly | Simulate or use fixture with expired trial. | User loses Pro access at expected time unless paid subscription is active; status text shows expired trial and next action. | P0 | Entitlement state. |
| PC-007 | Checkout redirect | Checkout session is created for correct plan | From pricing, start checkout for personal Pro. | Redirect reaches payment provider checkout for the personal beta price; plan ID, amount, interval, trial behavior, and customer email match expected values. | P0 | Checkout session details. |
| PC-008 | Checkout redirect | Checkout success return updates UI safely | Complete checkout with test card; land on success URL; refresh dashboard and account settings. | Subscription status becomes active or trialing as configured; Pro features unlock without requiring manual support. | P0 | Screenshot plus subscription record. |
| PC-009 | Checkout redirect | Checkout cancel return is non-destructive | Start checkout, cancel at provider, return to app. | User remains free/trial state as before; no Pro entitlement is granted; pricing page offers retry. | P0 | Account state before/after. |
| PC-010 | Checkout redirect | Checkout failure and abandoned sessions are handled | Trigger card decline and close provider page without payment. | UI shows retry path; no duplicate subscription; no stale "processing" lock that blocks future checkout. | P0 | Provider event log. |
| PC-011 | Webhook idempotency | Duplicate payment success webhook is safe | Replay the same checkout/subscription-created webhook at least twice. | One subscription record or entitlement update is created; duplicate events are logged as already processed; no double invoice/account mutation. | P0 | Webhook event IDs and DB record count. |
| PC-012 | Webhook idempotency | Out-of-order webhook delivery is safe | Deliver subscription update before checkout completion, then completion event. | Final account state is correct; handler tolerates missing intermediate records or reconciles by provider customer/subscription ID. | P0 | Event sequence log. |
| PC-013 | Webhook idempotency | Webhook signature validation rejects spoofed events | Send event with invalid signature and valid-looking payload. | Request is rejected; no account, subscription, or entitlement mutation occurs; security log is recorded. | P0 | HTTP status and audit log. |
| PC-014 | Subscription status | Active subscription displays correctly | Visit account settings as active Pro. | Status shows active plan, renewal date, billing interval, management link, and cancellation policy. | P0 | Screenshot. |
| PC-015 | Subscription status | Past-due subscription degrades access predictably | Use failed-payment fixture or test card event. | User sees payment issue and update-payment CTA; Pro access follows product policy; no silent paid access after final grace period. | P0 | State transition notes. |
| PC-016 | Subscription status | Canceled-at-period-end remains understandable | Cancel renewal but keep access until current period end. | Account page shows cancellation date and access end date; Pro remains available until the stated date. | P0 | Screenshot plus provider state. |
| PC-017 | Subscription status | Immediate cancellation removes access | Use support/admin/provider action to end subscription immediately. | User sees canceled status; Pro gating closes on next session refresh or entitlement sync. | P0 | Entitlement state. |
| PC-018 | Pro gating | Free user cannot access paid-only features | As free user, attempt every Pro entry point, direct URL, API call, saved link, and browser refresh. | UI shows upgrade path; API returns authorization failure; no paid data/export/action is returned. | P0 | Endpoint responses. |
| PC-019 | Pro gating | Trial/active Pro user can access paid features | As trial and active Pro users, execute core paid workflows. | Paid flows work without false upgrade prompts; usage limits and disclaimers remain visible. | P0 | Workflow screenshots. |
| PC-020 | Pro gating | Expired/canceled users cannot use cached Pro state | Keep a tab open as active Pro; change subscription to expired/canceled; refresh and call APIs. | Client and server both enforce current entitlement; stale local state cannot bypass gating. | P0 | Before/after responses. |
| PC-021 | Personal vs institutional mode | Personal user remains in personal mode | Log in as personal Pro; inspect navigation, billing, dashboard labels, and exports. | No institutional workflows, organization billing, shared seats, or enterprise-only claims are exposed. | P0 | Screenshot set. |
| PC-022 | Personal vs institutional mode | Institutional user is not pushed into personal checkout | Log in with institutional entitlement; open pricing and account billing. | Existing institutional mode remains available; personal upgrade CTA is suppressed or clearly separated; no double-billing trap. | P0 | Account state. |
| PC-023 | Personal vs institutional mode | Mode switching preserves access boundaries | If user has both personal and institutional contexts, switch modes and use Pro/institutional features. | Entitlements are scoped to the active mode; data, billing, and permissions do not bleed across contexts. | P1 | Mode-switch recording. |
| PC-024 | Email signup | Email-only signup captures consent | Submit overseas email from marketing/pricing form; verify opt-in text, success state, and backend record. | Email is stored once with source, timestamp, consent basis, and locale if collected; user is not auto-created as paid account. | P0 | Email record. |
| PC-025 | Email signup | Duplicate signup is idempotent | Submit same email multiple times with case variation. | No duplicate rows or repeated welcome emails beyond policy; user gets stable success message. | P1 | Record count and outbound email log. |
| PC-026 | Email unsubscribe | Unsubscribe works without login | Use unsubscribe link from email. | Link opens without authentication; email is suppressed from future marketing; transactional billing emails remain policy-compliant. | P0 | Suppression record. |
| PC-027 | Email unsubscribe | Unsubscribe token is safe | Try expired, malformed, reused, and another user's unsubscribe token. | Valid token is idempotent; invalid tokens do not expose subscriber data; clear failure state is shown. | P1 | Response screenshots. |
| PC-028 | Disclaimers | Paid pages show investment/data limitations | Review pricing, signup, checkout return, dashboard, report, 1Y trend, and export surfaces. | Relevant disclaimers are visible before reliance on results; wording does not promise investment advice, guaranteed returns, or real-time completeness. | P0 | Screenshot set. |
| PC-029 | Disclaimers | Disclaimer acceptance or acknowledgement is recorded if required | Trigger any required paid beta acknowledgement. | Acceptance is versioned with timestamp, user ID, and disclaimer version; changed disclaimer can be re-presented. | P1 | Acceptance record. |
| PC-030 | Data freshness | Freshness timestamp is visible near paid outputs | Open paid dashboard, search results, market data views, and reports. | Each data-dependent view shows last updated time, source or methodology link where applicable, and timezone. | P0 | Screenshot. |
| PC-031 | Data freshness | Stale data is clearly marked | Simulate delayed or stale data source beyond allowed freshness threshold. | UI shows stale/limited state; paid outputs are not presented as current; exports include freshness metadata. | P0 | Stale-state screenshot. |
| PC-032 | Data freshness | Missing data does not produce misleading output | Use symbol/company/asset with no data or partial data. | UI shows empty/partial-data state with explanation; no fabricated trend, score, or recommendation appears. | P0 | Test fixture notes. |
| PC-033 | 1Y trend | 1Y trend renders correctly for complete data | Open entity with complete 1Y history. | Chart/metric uses correct date range, labels, units, timezone, and data points; export matches on-screen values. | P0 | Screenshot plus exported data sample. |
| PC-034 | 1Y trend | 1Y trend handles incomplete history | Open entity with less than 1Y of history or data gaps. | UI labels the range actually available; trend calculation does not imply full-year coverage. | P0 | Screenshot. |
| PC-035 | 1Y trend | 1Y trend respects Pro gating | Directly call 1Y trend API and page as free user. | Free user cannot retrieve paid 1Y trend data through UI or API; upgrade path is shown. | P0 | HTTP response. |
| PC-036 | API failures | Pricing and checkout APIs fail closed | Force pricing config, checkout session, or entitlement API failure. | User sees retry/support path; no incorrect free/paid state is displayed; checkout cannot proceed with unknown price. | P0 | Error-state screenshot. |
| PC-037 | API failures | Paid dashboard APIs fail gracefully | Force timeout, 500, 401, 403, and 429 on paid data endpoints. | UI distinguishes retryable failure, unauthorized access, and rate limit; no blank paid surface without explanation. | P0 | Response matrix. |
| PC-038 | API failures | Webhook processing failure is recoverable | Force a transient webhook handler failure, then retry same provider event. | Event can be retried safely; final state converges; support can identify failed event and customer. | P0 | Event retry log. |
| PC-039 | Cancellation/refund policy | Policy is visible before purchase | Review pricing, checkout-adjacent copy, account billing, and help/footer links. | Cancellation timing, refund limitations, renewal behavior, and support contact are findable before payment. | P0 | Screenshot set. |
| PC-040 | Cancellation/refund policy | User can cancel through supported flow | From active Pro account, open billing management or in-app cancellation. | Cancellation completes or clearly redirects to provider portal; account status and renewal/access end date update. | P0 | Provider portal/account screenshot. |
| PC-041 | Cancellation/refund policy | Refund behavior matches policy | Issue test refund for active subscription. | Entitlement, invoice status, user messaging, and support/audit record match stated policy. | P0 | Refund event and account state. |
| PC-042 | Cancellation/refund policy | Chargeback/dispute does not leave paid access incorrectly active | Simulate dispute if provider test mode supports it. | Access follows risk policy; account is flagged for review; user messaging avoids legal/financial ambiguity. | P1 | Provider event log. |

## Cross-Cut Checks

| ID | Check | Expected Result | Priority |
| --- | --- | --- | --- |
| CC-001 | Mobile pricing, checkout return, account billing, and Pro gating at 375px width | No clipped text, hidden CTAs, or unreadable policy links. | P0 |
| CC-002 | Desktop Chrome, Safari, Firefox, and one mobile browser | Core paid path works consistently across supported browsers. | P1 |
| CC-003 | Browser locale `en-US`, timezone UTC-8/UTC+1/UTC+8 | Renewal dates, freshness dates, and trial deadlines remain understandable. | P1 |
| CC-004 | Slow network and offline retry | Checkout creation, paid dashboard, and email forms show non-destructive loading/error states. | P1 |
| CC-005 | Observability | Checkout session ID, provider customer ID, subscription ID, webhook event ID, and user ID are traceable without exposing secrets. | P0 |
| CC-006 | Security | Client-side hidden buttons or direct API calls cannot bypass server-side entitlement checks. | P0 |

## Launch Smoke Commands

Run these with staging first, then production immediately before opening the overseas paid beta. Replace paths only where the deployed service uses different route names.

```bash
export BASE_URL="https://example.gfcri.com"
export QA_EMAIL="qa+personal-beta-$(date +%s)@example.com"

# 1. Basic app and pricing availability.
curl -fsS "$BASE_URL/" >/dev/null
curl -fsS "$BASE_URL/pricing" >/tmp/gfcri-pricing.html
grep -Ei "Pro|personal|trial|cancel|refund|disclaimer" /tmp/gfcri-pricing.html

# 2. Health/readiness endpoint, if exposed by the deployment.
curl -fsS "$BASE_URL/health" || curl -fsS "$BASE_URL/api/health"

# 3. Pricing must not expose placeholder price text.
! grep -Ei "TODO|TBD|placeholder|lorem|coming soon" /tmp/gfcri-pricing.html

# 4. Email signup smoke. Use the actual route name if it differs.
curl -fsS -X POST "$BASE_URL/api/email/signup" \
  -H "content-type: application/json" \
  -d "{\"email\":\"$QA_EMAIL\",\"source\":\"personal_paid_beta_smoke\"}"

# 5. Pro API must fail closed for anonymous users. Use the actual paid endpoint if it differs.
PRO_STATUS="$(curl -sS -o /tmp/gfcri-pro-anon.out -w "%{http_code}" "$BASE_URL/api/pro/status")"
case "$PRO_STATUS" in
  401|403) ;;
  *) echo "Expected anonymous Pro status 401/403, got $PRO_STATUS"; exit 1 ;;
esac

# 6. Data freshness surface should include freshness language on paid/data pages.
curl -fsS "$BASE_URL/" | grep -Ei "updated|freshness|as of|data"
```

Provider-side smoke checks:

| Check | Expected Result |
| --- | --- |
| Test checkout session creation | Session uses personal beta price and success/cancel URLs for the target environment. |
| Test webhook delivery | Signed test event is accepted; duplicate test event is idempotent. |
| Test subscription sync | Active, trialing, canceled, and past-due test subscriptions map to expected app status. |
| Test refund event | Refund event updates billing/support state according to policy. |

## Exit Criteria

- All P0 cases pass with screenshots, logs, or provider event IDs attached to the release checklist.
- Any P1 failures are explicitly accepted by product, engineering, and operations with user-facing risk documented.
- Paid beta launch is blocked if pricing, checkout, webhook idempotency, entitlement gating, cancellation/refund policy, disclaimers, or data freshness cannot be verified.
