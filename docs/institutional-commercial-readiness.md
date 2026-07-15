# GFCRI Institutional Commercial Readiness Pack

Date: 2026-07-10

## Product Split

GFCRI uses one model core and two product surfaces:

- Personal Pro: simplified risk monitoring for professional individual users.
- Institutional Edition: audit-oriented workflow for research, wealth, allocation, risk, and client-service teams.

The two editions share the same risk index, data-quality gates, and model logic. They differ in information density, disclosure depth, exports, auditability, and deployment requirements.

## Current Commercial Status

Current status: paid pilot / POC ready, not yet full institutional production ready.

Reasons:

- The model now blocks official index updates when critical market data is incomplete.
- Raw market data is persisted to `market_data_daily` before calculation.
- Methodology, source-tier, limitation, and upgrade-path metadata are exposed in the product.
- Institutional Radar uses official public metadata and does not ingest copyrighted full text.

Remaining production gates:

- Formal data vendor/legal review for yfinance, Tushare, AKShare, FRED, OECD, and any future market-data source.
- SLA-backed market-data vendor or approved institutional data connector.
- Full point-in-time/vintage backtest evidence for official macro series.
- RBAC, SSO/SAML, audit logs, API key governance, and report approval workflow.
- Signed methodology, data-source notice, model limitation statement, and non-advisory disclaimer for client review.

## Data Source Notice

Current sources include:

- FRED: US macro and financial stress series.
- yfinance: liquid market prices and ETF proxies.
- Tushare: selected index and FX fallback data.
- OECD SDMX: selected macro/rate context.
- AKShare: China macro series.
- Public official metadata sources for Institutional Radar.

Operational rules:

- Market prices are persisted before model calculation.
- The official risk index is not updated when core data quality gates fail.
- Missing or stale critical nodes trigger a blocked quality event.
- External source failures must be visible to users through data-quality status.

Legal/commercial caveat:

Use of public or free data APIs does not automatically grant institutional redistribution or commercial rights. Formal data licensing review is required before production institutional deployment.

## Model Limitation Statement

GFCRI is a macro-risk monitoring and explanation system. It is not:

- investment advice,
- trading advice,
- asset-allocation advice,
- a probability forecast,
- a crisis timing predictor,
- a recommendation to buy or sell any financial product.

The index measures risk pressure and transmission conditions. Historical analogies and stress scenarios are decision-support context, not expected outcomes.

## Data Quality Gate

The official index update is blocked when critical market data is incomplete.

Current critical nodes include:

- VIX,
- S&P 500,
- DXY,
- HYG,
- LQD,
- KOSPI,
- US 10Y,
- US 2Y,
- USD/CNY,
- USD/JPY.

Policy:

- Official: critical coverage is sufficient and core z-score coverage is available.
- Blocked: official index remains at the last reliable observation; the blocked run is recorded separately.
- No incomplete calculation may overwrite `daily_risk_index`.

## Causal Language Policy

Institutional-facing language should prefer:

- transmission channel,
- monitored linkage,
- transmission hypothesis,
- governed candidate,
- falsification test.

Avoid over-claiming:

- proven causality,
- causal truth,
- prediction,
- guaranteed lead time.

The core graph may contain directional assumptions, but new AI-generated mechanisms remain candidates until validated and approved.

## Backtest Evidence Required Before Production

Before full institutional production use, backtests should document:

- crisis window definitions,
- data availability at the historical date,
- vintage/revision policy,
- false positives and false negatives,
- benchmark comparison against VIX, credit spreads, yield curve, and dollar index,
- sensitivity to model weights and thresholds,
- out-of-sample periods,
- data-source gaps and proxy substitutions.

## Institutional Acceptance Checklist

Pilot-ready if:

- private deployment works,
- daily refresh runs,
- official index update is gated by data quality,
- dashboard/API/methodology pages load,
- rollback plan exists,
- source-tier and model limitation disclosure are available.

Production-ready only when:

- data rights are cleared,
- SLA/monitoring is in place,
- RBAC and audit logs are implemented,
- backtest evidence is signed off,
- report approval and export governance are implemented,
- client-specific disclaimers and operating procedures are reviewed.
