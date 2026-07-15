# GFCRI Institutional Edition Paid Pilot Package

Date: 2026-07-10

## Commercial Positioning

GFCRI Institutional Edition is a private-deployment macro risk intelligence package for teams that need explainable monitoring of systemic financial stress. It is built around the GFCRI macro risk index, Institutional Radar, data quality gates, methodology disclosure, historical stress context, and commercial readiness controls.

Core promise:

```text
GFCRI helps institutional teams monitor whether macro-financial risk pressure is building, where it is coming from, and how it may transmit across markets.
```

Non-goal:

```text
GFCRI is not investment advice, trading advice, asset-allocation advice, or a crisis timing predictor.
```

Chinese note: 对外表达要坚持 "risk monitoring / explanation / transmission" 定位，避免使用 "prediction" 或 "guaranteed lead time"。

## Target Buyer Segments

| Segment | Buyer / Sponsor | Primary job-to-be-done | Best entry point |
|---|---|---|---|
| Multi-family offices and CIO offices | CIO, head of investment strategy, risk lead | Add an independent macro risk pressure layer for investment committee review | 30-day paid pilot with weekly macro risk memo |
| Asset managers and allocators | Portfolio risk, macro strategy, multi-asset PM | Detect cross-market stress synchronization and explain contribution drivers | Private dashboard plus exportable methodology pack |
| Wealth platforms and advisory teams | Investment product, research, client advisory desk | Create client-safe macro risk commentary without making trade calls | Institutional Radar and explainable risk index workflow |
| Banks, insurers, and treasury teams | Enterprise risk, ALM, treasury, strategy | Monitor rates, FX, credit, liquidity, and policy-buffer pressure | Private deployment with data quality gate evidence |
| Research and risk consulting firms | Managing partner, head of research | Package repeatable macro stress analysis for retained clients | White-label or co-branded pilot after data-rights review |

Priority ICP for first commercialization: multi-family offices, macro research desks, and asset allocation teams with fast buying cycles and clear need for explainable risk monitoring.

## SKU / Tier Proposal

| SKU | Target customer | Includes | Deployment | Commercial model |
|---|---|---|---|---|
| Institutional Pilot | 1 team, 3-10 users | GFCRI dashboard, macro risk index, Institutional Radar, methodology pack, data quality status, weekly review call | Private single-tenant Docker deployment or controlled hosted environment | Fixed 30-day paid POC |
| Institutional Team | 1 institution, 10-50 users | Pilot features plus exports, scheduled reports, team onboarding, client-specific disclaimer, support SLA placeholder | Private deployment preferred | Annual subscription |
| Enterprise Private | Bank, insurer, platform, or large allocator | Team features plus API access, approved data connector, SSO/RBAC/audit log roadmap, custom compliance pack | Customer VPC / on-prem / private cloud | Annual subscription plus setup fee |

Recommended launch SKU: **Institutional Pilot**.

Chinese note: 先卖 "paid pilot / POC"，不要承诺完整生产级企业系统。商业语言重点是验证价值、数据治理、私有化部署能力。

## Paid POC Scope

Duration: 30 calendar days after launch readiness sign-off.

Included:

- Private GFCRI Institutional Edition deployment.
- Daily GFCRI macro risk index refresh with visible data quality gate status.
- Institutional Radar view using official public metadata only.
- Risk decomposition across rates, FX, credit, equity, commodities, sentiment, trade spillover, hidden risk, and signal coherence where available.
- Methodology, source-tier, limitation, and non-advisory disclosure pack.
- Historical crisis analogy and stress scenario walkthrough.
- Two buyer-specific use cases configured during onboarding, such as investment committee review or weekly client macro note support.
- One onboarding session, one mid-pilot review, and one acceptance review.

Out of scope for first paid POC:

- Investment recommendations or asset allocation signals.
- Guaranteed crisis prediction, probability forecast, or lead-time commitment.
- Redistribution of raw third-party market data.
- Full SSO/RBAC/audit-log production hardening unless separately contracted.
- Formal client report approval workflow unless scoped as an Enterprise Private add-on.

## Pricing Assumptions

Use placeholders until buyer segment, deployment model, support burden, and data licensing requirements are confirmed.

| Item | Placeholder | Assumption |
|---|---:|---|
| 30-day Institutional Pilot fee | `[USD XX,000]` | Paid POC, credited `[0-100%]` toward annual contract if converted within `[XX]` days |
| Private deployment setup | `[USD X,000-XX,000]` | Depends on customer environment, security review, and data connector work |
| Institutional Team annual subscription | `[USD XXX,000/year]` | Includes named users, standard support, methodology updates, and scheduled refresh |
| Enterprise Private annual subscription | `[USD XXX,000-XXX,000/year]` | Includes private deployment, API roadmap, compliance pack, and enhanced support |
| Data licensing pass-through | `[At cost / TBD]` | Required before production institutional deployment if public/free data APIs are not commercially cleared |
| Professional services | `[USD XXX/hour or fixed scope]` | Custom reports, integration, validation requests, and compliance documentation |

Pricing principle: charge for institutional decision support, explainability, private deployment, and data governance. Do not price as a simple dashboard.

## 7-10 Day Launch Checklist

Day 1:

- Confirm pilot sponsor, success owner, user list, use cases, and procurement path.
- Confirm legal language: informational risk monitoring only, not investment advice.

Day 2:

- Select deployment mode: controlled hosted, customer private cloud, or local Docker Compose.
- Confirm data-source notice and redistribution constraints.

Day 3:

- Deploy GFCRI Institutional Edition in the agreed environment.
- Verify dashboard, API, methodology pages, and Institutional Radar load correctly.

Day 4:

- Run daily refresh and confirm raw market data persistence before calculation.
- Validate that official index updates are blocked when critical data quality gates fail.

Day 5:

- Configure buyer-specific use cases, such as investment committee review, risk meeting, or client commentary.
- Prepare demo dataset, current risk reading, and historical analogy examples.

Day 6:

- Review commercial readiness pack, model limitation statement, data source notice, and escalation path with sponsor.

Day 7:

- Run internal dry-run demo and acceptance checklist.
- Fix critical UX, deployment, or disclosure issues before buyer kickoff.

Days 8-10, if needed:

- Complete buyer security questionnaire, deployment tuning, data connector assessment, or compliance copy review.

## 30-Day Pilot Acceptance Criteria

The pilot is successful when the buyer can independently use GFCRI to support a recurring institutional risk workflow.

Acceptance gates:

| Area | 30-day acceptance criterion |
|---|---|
| Deployment | Private environment remains available during agreed business hours with documented restart and rollback steps |
| Data refresh | Daily refresh runs on schedule for at least `[N]` business days, or failures are visible and explained |
| Data quality gate | Official GFCRI index does not overwrite reliable observations when critical data is incomplete |
| Risk index | Buyer can interpret headline GFCRI score, alert level, sub-index decomposition, and hidden-risk/undercurrent signals |
| Institutional Radar | Buyer can review official public metadata signals without copyrighted full-text ingestion |
| Explainability | Buyer can trace risk movement to domains, indicators, transmission channels, and methodology notes |
| Use-case fit | At least two sponsor-approved workflows are completed, such as risk committee pack input and weekly macro risk review |
| Compliance comfort | Buyer accepts the non-advisory positioning, source-tier disclosure, and production-readiness caveats |
| Commercial conversion | Sponsor agrees on next step: annual Team subscription, Enterprise Private scope, extended pilot, or no-go reason |

Chinese note: 验收标准要强调 "can use in workflow"，不是只看模型分数高低。

## Buyer Demo Script

Target demo length: 25-30 minutes.

1. Opening: "GFCRI is an explainable macro risk monitoring system. It helps teams see whether systemic pressure is building and which channels are contributing."
2. Positioning: contrast GFCRI with price dashboards. GFCRI focuses on risk propagation, hidden stress, and cross-market synchronization.
3. Headline index: show current GFCRI score, alert level, last refresh time, and data quality status.
4. Quality gate: explain that official index updates are blocked when critical data is incomplete. This is a trust feature, not a limitation to hide.
5. Decomposition: walk through rates, FX, credit, equity, commodities, sentiment, trade spillover, hidden risk, and signal coherence.
6. Institutional Radar: show official public metadata signals and explain why the product avoids copyrighted full-text ingestion.
7. Historical context: show crisis analogy or stress scenario view. State clearly that this is context, not prediction.
8. Buyer workflow: map the screen to the buyer's weekly risk meeting, investment committee pack, or client macro note.
9. Commercial readiness: cover private deployment, methodology pack, data source notice, limitation statement, and production upgrade path.
10. Close: ask which workflow should define pilot success and who signs off on the 30-day acceptance review.

Demo language to use:

- "risk pressure"
- "transmission channel"
- "monitored linkage"
- "data quality gate"
- "methodology disclosure"
- "private deployment"

Demo language to avoid:

- "crisis prediction"
- "trade signal"
- "guaranteed early warning"
- "proven causality"
- "investment recommendation"

## Success Metrics

Product value metrics:

- Sponsor uses GFCRI in at least `[N]` recurring risk meetings during the pilot.
- At least `[N]` users complete onboarding and return in week 2 or week 3.
- Buyer can name the top 3 risk contributors without GFCRI team assistance.
- Buyer accepts the methodology and limitation disclosure as sufficient for pilot use.
- Data quality gate events are visible, explainable, and trusted.

Commercial metrics:

- Paid POC converts to Institutional Team or Enterprise Private at target conversion rate `[XX%]`.
- Sales cycle from kickoff to paid pilot is `[X-Y]` weeks.
- Annual contract value target is `[USD XXX,000+]` for Team and `[USD XXX,000+]` for Enterprise Private.
- Champion identifies budget owner, compliance reviewer, and production sponsor by day 15.

Operational metrics:

- Daily refresh success rate meets `[XX%]` during pilot window.
- Critical deployment incidents are resolved within `[X]` business hours.
- Methodology, source notice, and limitation pages are available throughout the pilot.
- No incomplete official index update overwrites `daily_risk_index`.

Decision metric:

```text
Proceed if the buyer confirms GFCRI improves institutional macro risk review quality enough to fund annual private access.
```
