# GFCRI Personal Subscription Legal and Compliance Content Pack

Date: 2026-07-10

Audience: GFCRI product, growth, support, checkout, and launch operations.

Status: operational copy for an overseas personal subscription soft launch. This document is not legal advice, does not replace counsel review, and should not be published as final legal terms without review by qualified counsel in the launch jurisdictions.

Use this pack to prepare practical public-facing pages, checkout language, footer language, email footers, and support macros for GFCRI Personal Pro. Replace every bracketed placeholder before launch.

## 1. Soft Launch Operating Assumptions

GFCRI Personal Pro is positioned as a personal macro-financial risk monitoring product.

Operational assumptions:

- The product provides market, macro, stress, hidden-risk, historical-analogy, and risk-transmission information.
- The product does not provide personalized investment advice, trading signals, portfolio recommendations, suitability analysis, fiduciary advice, legal advice, tax advice, or accounting advice.
- The personal subscription is for individual use only, not institutional use, client reporting, resale, raw data redistribution, or professional advisory workflows.
- The subscription may include a free tier, a 7-day Pro trial, monthly Pro, and annual Pro.
- GFCRI should prefer a no-card free trial for the first soft launch. If a trial converts automatically to paid billing, counsel must review the checkout flow, reminder cadence, cancellation flow, and jurisdiction-specific renewal rules before launch.
- GFCRI should not store full card numbers. Use a payment provider or merchant-of-record service for card handling, taxes, invoices, chargebacks, and payment security.
- GFCRI should not collect brokerage credentials, portfolio holdings, account balances, national IDs, health data, biometric data, precise location, or other sensitive personal information unless a later product scope has counsel and security review.
- GFCRI should not offer paid personal subscriptions in embargoed, sanctioned, or otherwise prohibited jurisdictions.

Baseline launch posture:

- Clear recurring-billing terms before payment.
- Affirmative agreement to subscription terms.
- Online cancellation that is at least as easy as sign-up.
- No dark-pattern save flows.
- Plain-English refund and cancellation policy.
- Visible risk and non-advisory disclaimer in pricing, checkout, reports, alerts, footer, and email.
- Privacy, cookie, data source, and email unsubscribe controls visible from the footer.
- Separate counsel review before expanding into EU/UK consumer sales, California-heavy acquisition, paid marketing pixels, affiliate marketing, or personalized portfolio features.

## 2. Required Public Pages and Links

Minimum footer links for soft launch:

- Terms of Service
- Privacy Policy
- Cookie Notice
- Refund and Cancellation Policy
- Data Sources and Limitations
- Contact / Support
- Manage Subscription
- Unsubscribe, for email footer only
- Do Not Sell or Share My Personal Information / Your Privacy Choices, if advertising cookies, cross-context behavioral ads, or California coverage thresholds apply

Recommended URL placeholders:

- `/terms`
- `/privacy`
- `/cookies`
- `/refunds`
- `/data-sources`
- `/support`
- `/account/billing`
- `/privacy-choices`

## 3. Terms of Service Outline

Page title:

```text
GFCRI Terms of Service
```

Top notice:

```text
These Terms govern your use of GFCRI Personal and GFCRI Personal Pro. GFCRI is an informational macro-financial risk monitoring service. It is not investment advice, trading advice, asset-allocation advice, legal advice, tax advice, accounting advice, fiduciary advice, or a recommendation to buy, sell, hold, hedge, or avoid any security, instrument, strategy, or financial product.
```

### 3.1 Parties and Acceptance

Operational copy:

```text
These Terms are between you and [Legal Entity Name] ("GFCRI", "we", "us", or "our"). By creating an account, starting a trial, purchasing a subscription, or using GFCRI, you agree to these Terms and the policies linked from them, including our Privacy Policy, Cookie Notice, Refund and Cancellation Policy, and Data Sources and Limitations notice.
```

Checklist:

- Insert legal entity name, address, and support email.
- Confirm whether the contracting party is the app owner, a merchant of record, or another entity.
- If the merchant of record has separate terms, disclose them during checkout.

### 3.2 Eligibility and Account Responsibility

Operational copy:

```text
You must be at least 18 years old, or the age of majority in your jurisdiction, to use a paid GFCRI subscription. You are responsible for maintaining the confidentiality of your login credentials and for all activity under your account. You may not use GFCRI where prohibited by law, sanctions, export controls, or these Terms.
```

Implementation notes:

- Add age gate or account checkbox if required for launch jurisdiction.
- Add support flow for account compromise.

### 3.3 Description of the Service

Operational copy:

```text
GFCRI provides macro-financial risk monitoring, risk-index readings, explanatory risk drivers, transmission-channel context, hidden-risk scans, historical stress context, stress scenarios, alerts, and related educational content. Features may vary by plan, jurisdiction, device, data availability, and launch phase.
```

Soft launch clause:

```text
GFCRI Personal Pro is offered during a soft launch. Features, data coverage, update cadence, alert logic, plan packaging, and pricing may change as we improve the service. We will not materially reduce paid access during your then-current billing period without providing a reasonable remedy, such as continued access, credit, or refund where appropriate.
```

### 3.4 Personal Use License

Operational copy:

```text
Subject to these Terms, we grant you a limited, revocable, non-exclusive, non-transferable license to access and use GFCRI for your own personal, non-commercial research and risk-monitoring purposes.
```

Restrictions:

```text
You may not resell, sublicense, publish, redistribute, scrape, bulk download, reverse engineer, frame, or use GFCRI to create a competing service. You may not use a personal subscription to provide investment advice, client reports, institutional research, paid advisory services, or professional financial services to third parties. Institutional, client-facing, advisory, or commercial use requires a separate written agreement.
```

### 3.5 No Professional Advice

Operational copy:

```text
GFCRI content is general information only. It is not based on your personal financial situation, investment objectives, risk tolerance, tax status, liquidity needs, portfolio holdings, or legal obligations. You are solely responsible for your financial, investment, trading, tax, legal, and business decisions. Before acting on financial information, consult a qualified professional.
```

### 3.6 Subscription, Trial, Renewal, and Billing

Operational copy for no-card trial:

```text
If you start a free trial without adding a payment method, your trial will end automatically unless you choose a paid plan. You will not be charged unless you separately complete checkout for a paid subscription.
```

Operational copy for card trial, only if approved:

```text
If you start a trial that requires a payment method, the checkout screen will show the trial length, renewal date, renewal price, billing frequency, taxes where applicable, and cancellation method before you submit payment information. Unless you cancel before the trial ends, your subscription will automatically renew and your payment method will be charged at the displayed price and billing frequency.
```

Paid subscription copy:

```text
Paid subscriptions renew automatically until canceled. You authorize us and our payment provider to charge your payment method for the subscription price, applicable taxes, and any disclosed fees at the billing frequency shown at checkout. You can cancel through your account billing page or by contacting [support email].
```

Price change copy:

```text
If we change the price of your paid plan, we will provide advance notice where required and will apply the change no earlier than your next renewal date unless you agree otherwise.
```

Implementation checklist:

- Show plan name, price, billing frequency, renewal date, trial end date, taxes, cancellation method, refund link, Terms link, Privacy link, and non-advisory disclaimer before payment.
- Record affirmative consent timestamp, plan, price, currency, trial terms, renewal terms, IP/country if collected, and version of terms accepted.
- Send purchase confirmation and renewal reminder where required or prudent.
- Provide self-serve cancellation from account settings.

### 3.7 Refunds and Cancellations

Operational copy:

```text
Refunds and cancellations are governed by the Refund and Cancellation Policy linked at checkout and in your account billing page. Canceling stops future renewals but does not automatically refund previous charges unless the policy, applicable law, or our support team provides otherwise.
```

### 3.8 Data Sources, Availability, and Delays

Operational copy:

```text
GFCRI uses third-party and public market, macroeconomic, and reference data sources. Data may be delayed, revised, incomplete, unavailable, subject to licensing limits, or affected by provider outages. GFCRI may hold or pause an official index update when critical data quality checks fail. A held index is a data-quality control, not a statement that risk is unchanged.
```

### 3.9 Alerts and Notifications

Operational copy:

```text
GFCRI alerts are informational notifications, not emergency warnings, investment instructions, or guaranteed real-time messages. Alerts may be delayed, missed, filtered by email providers, or unavailable because of data, provider, system, or user-device issues. Do not rely on GFCRI alerts as your sole source for market, financial, or risk decisions.
```

### 3.10 User Feedback and Submitted Content

Operational copy:

```text
If you send feedback, suggestions, support messages, or other submissions, you grant us permission to use them to operate, troubleshoot, improve, and market GFCRI without compensation to you, subject to our Privacy Policy. Do not send confidential, regulated, or sensitive information through support channels unless we specifically request it through a secure process.
```

### 3.11 Intellectual Property

Operational copy:

```text
GFCRI, including its software, design, reports, scoring methods, charts, text, trademarks, and product experience, is owned by [Legal Entity Name] or its licensors. Except for the limited license expressly granted in these Terms, no rights are transferred to you.
```

### 3.12 Third-Party Services

Operational copy:

```text
GFCRI may rely on third-party services for hosting, authentication, payments, analytics, email delivery, market data, and customer support. Third-party services may have their own terms and privacy practices. We are not responsible for third-party services that we do not control.
```

### 3.13 Warranties and Service Limits

Operational copy:

```text
GFCRI is provided on an "as is" and "as available" basis to the maximum extent permitted by law. We do not guarantee that GFCRI will be uninterrupted, error-free, current, complete, secure, or suitable for any financial, investment, legal, tax, operational, or business purpose. We do not guarantee market outcomes, crisis detection, lead time, data accuracy, model accuracy, or alert delivery.
```

### 3.14 Liability Limit

Counsel must tailor this section. Operational placeholder:

```text
To the maximum extent permitted by law, [Legal Entity Name] and its affiliates, officers, employees, contractors, suppliers, and licensors will not be liable for indirect, incidental, consequential, special, exemplary, punitive, lost-profit, trading-loss, investment-loss, data-loss, or business-interruption damages arising from or related to GFCRI. Our aggregate liability for claims relating to GFCRI will not exceed the amount you paid for the service during the [3/6/12] months before the event giving rise to the claim, or [USD amount], whichever is greater.
```

Counsel checklist:

- Review consumer-law enforceability.
- Some jurisdictions restrict liability caps, warranty exclusions, and mandatory rights waivers.
- Do not exclude liability that cannot legally be excluded.

### 3.15 Termination and Suspension

Operational copy:

```text
We may suspend or terminate access if you violate these Terms, create security risk, misuse data, attempt unauthorized access, fail to pay, use the service in a prohibited jurisdiction, or use a personal account for commercial or advisory purposes. If we terminate without cause during a paid term, we will provide a reasonable remedy such as continued access, credit, or refund where appropriate.
```

### 3.16 Changes to Terms

Operational copy:

```text
We may update these Terms from time to time. If changes materially affect your rights or paid subscription, we will provide reasonable notice. Your continued use after the effective date means you accept the updated Terms. If you do not agree, you may cancel your subscription.
```

### 3.17 Governing Law and Disputes

Counsel placeholder:

```text
These Terms are governed by the laws of [jurisdiction], without regard to conflict-of-law rules. Disputes will be resolved in [courts/arbitration/forum], except where consumer law gives you mandatory rights in your country or state of residence.
```

Counsel checklist:

- Decide whether to use courts, arbitration, class waiver, informal dispute resolution, or no arbitration.
- Review enforceability for consumer users, EU/UK users, California users, and other target markets.

### 3.18 Contact

Operational copy:

```text
For support or legal notices, contact us at [support email] or [legal email]. Our mailing address is [registered physical address].
```

## 4. Privacy Policy Outline

Page title:

```text
GFCRI Privacy Policy
```

Top notice:

```text
This Privacy Policy explains how [Legal Entity Name] collects, uses, shares, and protects personal information when you use GFCRI. It is operational copy for transparency and must be reviewed by counsel before publication.
```

### 4.1 Controller / Business Identity

Operational copy:

```text
[Legal Entity Name] is responsible for the personal information described in this Privacy Policy. Contact us at [privacy email] or [mailing address].
```

### 4.2 Personal Information Collected

Recommended table:

| Category | Examples | Source | Launch posture |
|---|---|---|---|
| Account information | Email, display name, password hash or auth provider ID, account status, plan tier | User, auth provider | Required |
| Subscription and billing information | Plan, renewal date, invoices, payment status, billing country, tax metadata, payment provider customer ID | User, payment provider | Required for paid plans |
| Payment card data | Full card number, CVV | Payment provider | GFCRI should not store this |
| Product usage data | Pages viewed, features used, risk-watch settings, alert preferences, session events | User activity | Use for service operation and product improvement |
| Device and log data | IP address, browser, device type, timestamps, error logs, security logs | Service systems | Required for security and reliability |
| Analytics data | Aggregated or pseudonymous usage events, referrer, conversion funnel data | Analytics provider | Optional; consent where required |
| Communications | Support requests, feedback, survey responses, email engagement | User, email provider | Required for support and lifecycle emails |
| Marketing preferences | Newsletter signup, unsubscribe status, consent records | User, email provider | Optional |

Sensitive-data boundary:

```text
GFCRI is not designed to collect brokerage account credentials, portfolio holdings, account balances, government identification numbers, health information, biometric information, precise geolocation, or other sensitive personal information. Please do not submit that information unless we introduce a specific feature that requests it and provides additional notice.
```

### 4.3 How GFCRI Uses Personal Information

Operational copy:

```text
We use personal information to provide and secure GFCRI, create and manage accounts, process subscriptions, deliver alerts and service messages, respond to support requests, improve product reliability, understand feature usage, prevent fraud and abuse, comply with legal obligations, and communicate about product updates where permitted.
```

Purpose table:

| Purpose | Data used | Suggested legal basis where EU/UK law applies |
|---|---|---|
| Account creation and login | Account, device, log data | Contract, legitimate interests |
| Subscription billing | Account, billing, payment provider IDs | Contract, legal obligation |
| Product delivery | Account, usage, preferences | Contract |
| Alerts and service emails | Account, preferences, risk-watch settings | Contract, legitimate interests |
| Security and fraud prevention | Device, logs, account events | Legitimate interests, legal obligation |
| Analytics and product improvement | Usage, device, analytics events | Consent or legitimate interests depending on jurisdiction/tool |
| Marketing emails | Email, consent, preferences | Consent or applicable soft opt-in where available |
| Legal compliance | Account, billing, logs | Legal obligation |

### 4.4 Sharing Personal Information

Operational copy:

```text
We share personal information with service providers that help us operate GFCRI, such as hosting, authentication, payment processing, email delivery, analytics, customer support, security, and error monitoring providers. We may also share information if required by law, to protect rights and safety, in connection with a corporate transaction, or with your direction or consent.
```

Launch checklist:

- List actual vendors before publication.
- Name payment processor or merchant of record.
- Name analytics provider if used.
- Name email provider if used.
- Add data processing agreements for vendors handling personal information.

### 4.5 Cookies and Similar Technologies

Operational copy:

```text
We use essential cookies and similar technologies to run GFCRI, keep you signed in, secure the service, remember preferences, and process subscriptions. With your permission where required, we may use analytics cookies to understand product usage and improve reliability. See our Cookie Notice for details and choices.
```

### 4.6 International Transfers

Operational copy:

```text
GFCRI may process personal information in countries other than where you live. Those countries may have different data protection laws. Where required, we use appropriate safeguards for international transfers, such as data processing agreements or other approved transfer mechanisms.
```

Counsel checklist:

- If serving EU/UK users, confirm transfer mechanism and vendor data locations.
- Do not publish "adequacy" or specific transfer mechanism claims unless verified.

### 4.7 Retention

Operational copy:

```text
We keep personal information only as long as reasonably necessary for the purposes described in this Privacy Policy, including to provide GFCRI, maintain account records, comply with legal obligations, resolve disputes, prevent abuse, and enforce agreements. Retention periods vary by data type.
```

Suggested retention table:

| Data | Suggested retention |
|---|---|
| Account profile | Life of account plus [30-180 days] after deletion request, unless legally required |
| Billing records | [7 years] or local tax/accounting period |
| Support messages | [2-3 years] after last interaction |
| Security logs | [90-365 days], longer for investigated abuse |
| Analytics events | [13-25 months] or provider default approved by privacy owner |
| Marketing consent and unsubscribe records | As long as needed to honor preference and prove compliance |

### 4.8 User Rights and Choices

Operational copy:

```text
Depending on where you live, you may have rights to access, correct, delete, restrict, object to, or receive a copy of your personal information, and to withdraw consent where processing is based on consent. You may also unsubscribe from marketing emails at any time. To make a request, contact [privacy email].
```

California add-on if applicable:

```text
California residents may have rights to know, access, correct, delete, opt out of sale or sharing, limit use of sensitive personal information, and not be discriminated against for exercising privacy rights. GFCRI does not sell personal information for money. If GFCRI uses advertising cookies or cross-context behavioral advertising, add a "Do Not Sell or Share My Personal Information" or "Your Privacy Choices" link before launch.
```

EEA/UK add-on if applicable:

```text
EEA and UK users may also have the right to complain to a local data protection authority. Contact us first at [privacy email] so we can try to resolve the issue.
```

### 4.9 Security

Operational copy:

```text
We use reasonable technical and organizational measures designed to protect personal information. No online service can guarantee complete security. You are responsible for using a strong password, keeping account credentials confidential, and notifying us if you suspect unauthorized access.
```

### 4.10 Children

Operational copy:

```text
GFCRI is not intended for children or users under 18. We do not knowingly collect personal information from children. If you believe a child has provided personal information to GFCRI, contact [privacy email].
```

### 4.11 Automated Decisions

Operational copy:

```text
GFCRI models generate macro-financial risk readings about markets and risk conditions. They do not make legal, employment, credit, insurance, housing, or similarly significant decisions about individual users.
```

### 4.12 Privacy Policy Updates

Operational copy:

```text
We may update this Privacy Policy from time to time. If we make material changes, we will provide reasonable notice through the service, email, or another appropriate method.
```

## 5. Risk and Non-Advisory Disclaimer

Use this disclaimer consistently across pricing, checkout, reports, alerts, account pages, onboarding, and email.

### 5.1 Long Version

```text
GFCRI is provided for informational, educational, and macro-financial risk-monitoring purposes only. GFCRI does not provide investment advice, trading advice, asset-allocation advice, legal advice, tax advice, accounting advice, fiduciary advice, or personalized financial planning. GFCRI does not recommend that you buy, sell, hold, hedge, or avoid any security, instrument, asset class, portfolio, fund, strategy, or financial product.

GFCRI readings, alerts, historical analogies, stress scenarios, risk drivers, and transmission paths are decision-support context, not predictions, guarantees, instructions, or statements of future performance. They are not based on your personal financial situation, objectives, risk tolerance, tax status, liquidity needs, or portfolio holdings. You are responsible for your own decisions and should consult qualified professionals before making financial, investment, legal, or tax decisions.
```

### 5.2 Short Version

```text
GFCRI is informational macro-risk monitoring, not investment advice, trading advice, asset-allocation advice, or a recommendation to buy or sell any financial product.
```

### 5.3 Checkout Checkbox Version

```text
I understand that GFCRI is informational risk monitoring only and is not investment advice, trading advice, asset-allocation advice, or a recommendation to buy or sell any financial product.
```

### 5.4 Alert Footer Version

```text
This alert is informational risk-monitoring context only. It is not investment advice or a trading instruction.
```

### 5.5 Report Footer Version

```text
GFCRI reports are informational and educational. Historical similarity, stress scenarios, and risk-transmission analysis do not guarantee future outcomes and should not be used as the sole basis for any financial decision.
```

### 5.6 Product Copy Rules

Allowed language:

- "risk monitoring"
- "risk pressure"
- "risk transmission"
- "stress context"
- "watch points"
- "drivers"
- "scenario analysis"
- "historical analogy"
- "data-quality gate"
- "informational"
- "educational"

Avoid language:

- "trade signal"
- "buy"
- "sell"
- "profit"
- "guaranteed"
- "predicts the next crisis"
- "beat the market"
- "protect your portfolio"
- "personalized advice"
- "suitable for you"
- "act now"
- "risk-free"
- "proven to forecast"

## 6. Refund and Cancellation Policy

Page title:

```text
GFCRI Refund and Cancellation Policy
```

Top notice:

```text
This policy explains how personal subscriptions renew, cancel, and qualify for refunds. It is operational copy and must be reviewed by counsel before publication.
```

### 6.1 Recommended Soft Launch Policy

```text
You can cancel your GFCRI Personal Pro subscription at any time through your account billing page or by contacting [support email]. Cancellation stops future renewals. Unless required by law or expressly stated below, cancellation does not automatically refund charges already paid, and access continues until the end of the current paid billing period.
```

### 6.2 No-Card Free Trial

```text
If your free trial does not require a payment method, it will end automatically. You will not be charged unless you separately choose a paid plan and complete checkout.
```

### 6.3 Card Trial, Only If Used

```text
If your trial requires a payment method, the checkout page will show the trial end date, renewal price, billing frequency, and cancellation method before you submit payment information. You can cancel before the trial ends to avoid the first charge.
```

Soft launch recommendation:

- Prefer no-card trials until checkout, tax, renewal, and cancellation flows are counsel-reviewed.
- If card trials are used, send a reminder before conversion where required or prudent.

### 6.4 Monthly Plan

```text
Monthly subscriptions renew each month until canceled. If you cancel, you keep access until the end of the current monthly period. Monthly payments are generally non-refundable, except where required by law, where there is a duplicate charge, or where GFCRI approves a refund because of a billing error or extended service outage.
```

### 6.5 Annual Plan

```text
Annual subscriptions renew each year until canceled. If you cancel, you keep access until the end of the current annual period. Annual payments are generally non-refundable after purchase, except where required by law, where there is a duplicate charge, where there is a billing error, or where GFCRI approves a goodwill refund.
```

Optional user-friendly annual refund rule:

```text
For the soft launch, GFCRI may offer a one-time refund for a first annual purchase if you contact [support email] within 14 days of purchase and have not made substantial use of the paid features. This goodwill policy does not limit any mandatory rights you may have under applicable law.
```

Counsel note:

- If selling to EU/UK consumers, review withdrawal/cooling-off rights and required checkout wording before launch.
- If selling to California consumers, review automatic-renewal disclosures, affirmative consent, reminder, and cancellation requirements before launch.
- If using a merchant of record, align refund language with the merchant's required policy.

### 6.6 Service Outage Credit

```text
If a paid user cannot access paid GFCRI features for an extended period because of a GFCRI-controlled outage, GFCRI may provide a refund, credit, or extension at its discretion unless applicable law requires a different remedy.
```

### 6.7 Data Unavailability

```text
Market data outages, provider delays, holidays, revised data, stale source feeds, or data-quality gates may affect GFCRI updates. These events are part of the disclosed service limitations and do not automatically qualify for refunds unless they create extended unavailability of paid features.
```

### 6.8 How to Cancel

```text
To cancel, go to Account > Billing > Manage Subscription > Cancel Plan. You may also contact [support email]. We will process cancellation requests as quickly as reasonably possible. To avoid a renewal charge, cancel before your renewal date.
```

### 6.9 Support Macro

```text
Subject: Your GFCRI cancellation request

We have received your cancellation request for [account email]. Your subscription will remain active until [period end date], and you will not be charged again unless you restart a paid plan. GFCRI is informational risk monitoring only and not investment advice. You can review our Refund and Cancellation Policy here: [refund policy URL].
```

## 7. Cookie and Analytics Notice

Page title:

```text
GFCRI Cookie Notice
```

Top notice:

```text
This Cookie Notice explains how GFCRI uses cookies and similar technologies. It is operational copy and must be configured to match the actual tools deployed.
```

### 7.1 Cookie Categories

| Category | Purpose | Consent posture |
|---|---|---|
| Essential cookies | Login, session, security, fraud prevention, billing flow, cookie preferences | Always on |
| Functional cookies | Remember language, region, display, and product preferences | Consent or legitimate-interest assessment by jurisdiction |
| Analytics cookies | Understand page usage, feature adoption, errors, conversion, and reliability | Ask consent in EEA/UK and any jurisdiction where required |
| Marketing cookies | Paid ads, retargeting, affiliate attribution, cross-site tracking | Off by default until separately approved and consented |

### 7.2 Cookie Banner Copy

```text
GFCRI uses essential cookies to run and secure the service. With your permission, we also use analytics cookies to understand product usage and improve reliability. You can accept, reject, or manage analytics cookies at any time. GFCRI does not use cookies to provide investment advice or make decisions about you.
```

Buttons:

```text
Accept Analytics
Reject Non-Essential
Manage Choices
```

### 7.3 Cookie Preferences Copy

```text
Essential cookies are required for login, security, billing, and service operation. Analytics cookies help us understand which features are used and where the product needs improvement. Marketing cookies are not used unless listed here and enabled with your consent.
```

Preference labels:

- Essential: Always on
- Analytics: On / Off
- Marketing: On / Off

### 7.4 Cookie Table Template

| Name | Provider | Category | Purpose | Duration |
|---|---|---|---|---|
| `[session_cookie]` | GFCRI | Essential | Keeps you signed in and protects the session | `[duration]` |
| `[csrf_cookie]` | GFCRI | Essential | Helps prevent request forgery | `[duration]` |
| `[cookie_consent]` | GFCRI | Essential | Stores cookie preference choice | `[duration]` |
| `[payment_cookie]` | `[payment provider]` | Essential | Supports checkout and fraud prevention | `[duration]` |
| `[analytics_cookie]` | `[analytics provider]` | Analytics | Measures product usage and reliability | `[duration]` |

Implementation checklist:

- Do not load analytics cookies before consent where consent is required.
- Store consent version, timestamp, region, and categories selected.
- Provide a persistent "Cookie Preferences" footer link.
- Avoid pre-checked consent boxes.
- Avoid cookie walls for basic access unless counsel approves.
- Do not introduce advertising pixels until privacy, consent, CCPA/CPRA, and marketing claims are reviewed.

## 8. Email and CAN-SPAM Footer Requirements

This section is operational guidance, not legal advice. Apply it to lifecycle, marketing, newsletter, and risk-alert emails. Transactional emails should still identify GFCRI clearly but should avoid unnecessary promotional content.

### 8.1 Operational Requirements for Commercial Email

For commercial emails sent to US recipients, the footer and sending practices should include:

- Accurate "From", "To", "Reply-To", routing, and sender information.
- Subject line that is not deceptive or misleading.
- Clear identification that the email is from GFCRI.
- A valid physical postal address for the sender. This may be a current street address, a properly registered post office box, or a properly registered private mailbox.
- A clear unsubscribe link or mechanism.
- Unsubscribe mechanism that remains available for at least 30 days after the email is sent.
- Opt-out requests honored within 10 business days.
- No fees, login requirement, or unnecessary personal information required to unsubscribe.
- Vendor monitoring if an email service provider, contractor, or affiliate sends on GFCRI's behalf.
- Suppression list maintained so unsubscribed users do not receive further marketing emails.

For EU/UK recipients:

- Do not send marketing emails unless the user has consented or a valid local soft-opt-in basis has been confirmed.
- Include sender identity and unsubscribe in every marketing email.
- Keep evidence of consent or applicable soft opt-in.

### 8.2 Email Footer Template

```text
GFCRI - Global Financial Crisis Risk Index
Informational macro-risk monitoring only. Not investment advice.

You are receiving this email because you created a GFCRI account, subscribed to GFCRI updates, or requested product notifications.

Manage preferences: [preferences URL]
Unsubscribe: [unsubscribe URL]
Privacy Policy: [privacy URL]
Terms: [terms URL]

[Legal Entity Name]
[Physical Postal Address]
[City, State/Region, Postal Code, Country]
Contact: [support email]
```

### 8.3 Risk Alert Email Footer

```text
This GFCRI alert is informational risk-monitoring context only. It is not investment advice, trading advice, asset-allocation advice, or a recommendation to buy or sell any financial product. Market and macro data may be delayed, revised, incomplete, or unavailable.

Manage alert settings: [preferences URL]
Unsubscribe from marketing emails: [unsubscribe URL]
[Legal Entity Name], [Physical Postal Address]
```

### 8.4 Subscription Confirmation Email

```text
Subject: Your GFCRI Personal Pro subscription is active

Your GFCRI Personal Pro subscription is active.

Plan: [plan name]
Price: [price and currency]
Billing frequency: [monthly/annual]
Renewal date: [date]
Cancellation: You can cancel anytime from Account > Billing > Manage Subscription.

GFCRI is informational macro-risk monitoring only. It is not investment advice, trading advice, asset-allocation advice, or a recommendation to buy or sell any financial product.

Terms: [terms URL]
Refund and Cancellation Policy: [refund URL]
Privacy Policy: [privacy URL]
Support: [support email]
```

### 8.5 Renewal Reminder Email

Use where required or prudent, especially annual plans and trial-to-paid conversion.

```text
Subject: Your GFCRI Personal Pro subscription renews on [date]

Your GFCRI Personal Pro [monthly/annual] subscription is scheduled to renew on [date] at [price and currency] plus applicable taxes. You can cancel before renewal from Account > Billing > Manage Subscription.

Manage subscription: [billing URL]
Refund and Cancellation Policy: [refund URL]
Support: [support email]
```

## 9. Data Source Notice

Page title:

```text
GFCRI Data Sources and Limitations
```

Top notice:

```text
GFCRI combines market, macroeconomic, and reference data to monitor macro-financial risk pressure and transmission conditions. This page explains source categories, limitations, and how to read GFCRI outputs responsibly.
```

### 9.1 Source Families

Operational copy:

```text
GFCRI may use source families such as FRED, yfinance, OECD, AKShare, Tushare, public market data, official public metadata, and other public or third-party sources. Source coverage varies by asset, region, indicator, and date.
```

### 9.2 Data Limitations

Operational copy:

```text
Data can be delayed, revised, stale, incomplete, unavailable, incorrectly mapped, affected by market holidays, or subject to provider limits. Some indicators are direct measures; others are proxies used when direct data is unavailable. Historical coverage can differ across indicators, which may affect backtests, trend views, and historical analogies.
```

### 9.3 Licensing and Redistribution

Operational copy:

```text
GFCRI provides derived risk-monitoring views and explanatory analysis. Your personal subscription does not grant rights to redistribute, resell, bulk download, republish, or commercially exploit raw third-party data or GFCRI-derived datasets. Third-party source names belong to their respective owners. GFCRI is not endorsed by those providers unless expressly stated.
```

### 9.4 Data Quality Gate

Operational copy:

```text
GFCRI may pause or hold an official daily risk-index update when critical market data is missing, stale, or fails quality checks. A held index is a data-quality control, not a model view that risk is unchanged. Always review the displayed data freshness and quality status before interpreting a reading.
```

### 9.5 Model Limitations

Operational copy:

```text
GFCRI is an explainable risk-monitoring system, not a black-box crisis predictor. Historical analogies do not mean history will repeat. Stress scenarios are hypothetical, not probability forecasts. Risk-transmission paths are monitored mechanisms and explanatory assumptions, not proof of causality. GFCRI cannot capture every policy event, geopolitical shock, liquidity event, data error, or market discontinuity.
```

### 9.6 Data Source Footer

```text
Data may be delayed, revised, incomplete, unavailable, or subject to licensing limits. GFCRI readings are informational risk-monitoring context only and not investment advice.
```

## 10. User-Facing Checkout, Pricing, and Footer Wording

### 10.1 Pricing Page Header

```text
GFCRI Personal Subscription
See macro-financial risk pressure, drivers, and watch points with a personal risk-monitoring workflow.
```

Subtitle:

```text
GFCRI Personal plans provide global macro-risk monitoring, daily briefs, hidden-risk scans, historical stress context, and watch points. GFCRI is informational risk monitoring only, not investment advice.
```

### 10.2 Plan Card Copy

Free:

```text
Starter
Free
Current GFCRI risk level, one core risk theme, and basic methodology access.
```

Monthly:

```text
Pro Monthly
[USD price] / month
For users who want flexible daily macro-risk tracking, drivers, hidden-risk scans, and watch points.
```

Annual:

```text
Pro Annual
[USD price] / year
For users who want longer-cycle macro-risk monitoring with annual pricing.
```

Feature labels:

- Full Daily Risk Brief
- 1Y GFCRI trend
- Hidden Risk Scan
- Top Drivers and Watch Next
- Email Risk Alerts
- Historical Stress Context
- Data Source and Freshness Status

### 10.3 Pricing Page Disclaimer Block

```text
Not Investment Advice

GFCRI is for informational and risk-monitoring purposes only. It is not investment advice, trading advice, asset-allocation advice, fiduciary advice, or a recommendation to buy or sell any financial product. Market and macro data may be delayed, revised, incomplete, or unavailable.
```

### 10.4 Checkout Summary

```text
Plan: [GFCRI Personal Pro Monthly/Annual]
Price: [price and currency] plus applicable taxes
Billing: Renews [monthly/annually] until canceled
Next charge: [date]
Cancel: Anytime from Account > Billing > Manage Subscription
Refunds: See Refund and Cancellation Policy
```

### 10.5 Checkout Consent Checkbox

Use separate checkboxes for billing consent and non-advisory acknowledgment.

Recurring billing:

```text
I agree that my GFCRI Personal Pro subscription renews automatically at [price] [monthly/annually] until I cancel, and I authorize GFCRI or its payment provider to charge my payment method on each renewal date.
```

Terms:

```text
I agree to the Terms of Service, Privacy Policy, Cookie Notice, Data Sources and Limitations notice, and Refund and Cancellation Policy.
```

Risk acknowledgment:

```text
I understand GFCRI is informational macro-risk monitoring only and is not investment advice, trading advice, asset-allocation advice, or a recommendation to buy or sell any financial product.
```

### 10.6 Trial Checkout Copy

No-card trial:

```text
Start your 7-day Pro trial. No payment method required. Your trial ends automatically unless you choose a paid plan.
```

Card trial, only if used:

```text
Start your 7-day Pro trial. Unless you cancel before [date/time], your subscription will renew at [price] [monthly/annually] plus applicable taxes. You can cancel anytime from Account > Billing > Manage Subscription.
```

### 10.7 Account Billing Page Copy

```text
Your subscription renews on [date] at [price]. You can cancel future renewals at any time. If you cancel, you keep Pro access until [period end date].
```

Cancel button:

```text
Cancel Plan
```

Cancellation confirmation:

```text
Your plan is canceled. You will not be charged again unless you restart a paid plan. Your Pro access remains active until [period end date].
```

### 10.8 Footer Copy

```text
GFCRI is informational macro-financial risk monitoring only. It is not investment advice, trading advice, asset-allocation advice, fiduciary advice, or a recommendation to buy or sell any financial product. Data may be delayed, revised, incomplete, or unavailable.
```

Footer links:

```text
Terms | Privacy | Cookies | Refunds | Data Sources | Contact | Manage Subscription
```

### 10.9 Methodology / Report Footer

```text
GFCRI readings, drivers, historical analogies, and stress scenarios are explanatory risk context. They are not predictions, guarantees, or instructions. Review data freshness and source limitations before interpreting results.
```

### 10.10 Support Page Copy

```text
Need help with your account, billing, cancellation, privacy request, or data-source question? Contact [support email]. Do not send brokerage credentials, portfolio holdings, account balances, national IDs, or other sensitive information through support messages.
```

## 11. Operational Launch Checklist

Legal and policy:

- Counsel reviews Terms, Privacy, Cookie Notice, Refund Policy, Data Source Notice, and disclaimers.
- Legal entity, address, support email, privacy email, and tax/billing provider are confirmed.
- Launch countries are approved.
- Sanctions/prohibited jurisdiction handling is documented.
- EU/UK consumer withdrawal/cooling-off and privacy requirements are reviewed before accepting those users for paid subscriptions.
- California automatic-renewal, privacy, and opt-out requirements are reviewed before targeted acquisition or material California user base.

Checkout:

- Plan name, price, currency, billing frequency, renewal date, trial terms, taxes, cancellation method, refund policy, Terms, Privacy, and non-advisory disclaimer are visible before purchase.
- Billing consent is affirmative and logged.
- No pre-checked paid add-ons.
- Cancellation is self-serve and available from account settings.
- Purchase confirmation email includes plan, price, renewal date, cancellation method, policy links, and support contact.

Privacy and cookies:

- Actual vendors are listed in Privacy Policy.
- Cookie banner blocks analytics until consent where required.
- Cookie preferences are accessible from the footer.
- Marketing pixels are disabled unless privacy choices and consent flows are complete.
- Privacy requests route to [privacy email] with an owner and SLA.

Email:

- Marketing emails include physical postal address and unsubscribe.
- Unsubscribe is one-click or otherwise simple.
- Suppression list works across all marketing templates.
- Risk alerts include non-advisory footer.
- Trial-to-paid and annual renewal reminders are configured where required or prudent.

Product and copy:

- Avoid prediction, profit, recommendation, and "act now" language.
- Display data freshness and quality status near risk readings where possible.
- Show data source and limitation link in methodology/report surfaces.
- Do not enable user portfolio upload, personalized allocation suggestions, or client report exports on personal plan without separate review.

Support:

- Support team has cancellation, refund, privacy, and data-source macros.
- Escalation path exists for chargebacks, privacy requests, legal notices, source-data disputes, and investment-advice complaints.
- Refund exceptions are logged consistently.

## 12. Counsel Review Questions

Before publication, counsel should answer:

- What legal entity contracts with users?
- Which countries and US states are included in the soft launch?
- Is GFCRI using a merchant of record, and whose terms control payment disputes?
- Is a no-card trial required for launch simplicity?
- If a card trial is used, what reminders and renewal disclosures are required?
- What refund/cooling-off rights apply in each launch jurisdiction?
- Does the personal product create investment adviser, publisher, research, or regulated financial promotion issues in any launch jurisdiction?
- Are liability caps, arbitration, class waivers, governing law, and warranty disclaimers enforceable for target users?
- Do the selected analytics tools require consent before loading?
- Does GFCRI sell or share personal information under California privacy law because of ad tech or analytics configuration?
- Are data source licenses sufficient for a paid personal subscription and the displayed outputs?
- Are email flows compliant for US, EU, UK, Canada, and any other target recipients?

## 13. Reference Sources for Review

These references are for operational orientation and counsel review. They are not a substitute for legal advice.

- FTC CAN-SPAM compliance guide: https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business
- FTC Restore Online Shoppers' Confidence Act page: https://www.ftc.gov/legal-library/browse/statutes/restore-online-shoppers-confidence-act
- FTC Negative Option Rule page: https://www.ftc.gov/legal-library/browse/rules/negative-option-rule
- California Attorney General CCPA page: https://oag.ca.gov/privacy/ccpa
- California Privacy Protection Agency regulations page: https://cppa.ca.gov/regulations/
- California Attorney General automatic renewal consumer alert: https://oag.ca.gov/news/press-releases/attorney-general-bonta-issues-consumer-alert-california%E2%80%99s-automatic-renewal-law
- ICO cookies and similar technologies guidance: https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guide-to-pecr/cookies-and-similar-technologies/
- ICO UK GDPR guidance and resources: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/
- European Commission Consumer Rights Directive page: https://commission.europa.eu/law/law-topic/consumer-protection-law/consumer-contract-law/consumer-rights-directive_en
- Your Europe right of withdrawal overview: https://europa.eu/youreurope/citizens/consumers/shopping/returns/index_en.htm
- GDPR text via EUR-Lex: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679
- SEC Investor.gov investment adviser overview: https://www.investor.gov/introduction-investing/investing-basics/glossary/investment-adviser
