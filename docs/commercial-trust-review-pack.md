# GFCRI Institutional Edition Trust Review Pack

Date: 2026-07-10

Audience: customer procurement, compliance, legal, data governance, model risk, and internal risk/research reviewers.

Status: paid pilot / POC ready. GFCRI Institutional Edition should not be treated as fully production-cleared for broad institutional or client-facing use until the production gates in this pack are reviewed and signed off.

## 1. Scope Of This Pack

This pack summarizes the customer-facing trust position for GFCRI Institutional Edition:

- what data sources are used today;
- what data licensing caveats remain;
- what the model does and does not claim;
- how data freshness and official index publication are gated;
- how causal and predictive language must be controlled;
- what backtest evidence is required before production approval;
- what common compliance questions should receive consistent answers.

GFCRI Institutional Edition is positioned as audit-oriented risk monitoring infrastructure for research, wealth, allocation, risk, and client-service teams. It shares the same core risk index, data-quality gates, and model logic as the broader GFCRI product, with additional disclosure depth, exports, auditability, and private deployment requirements.

## 2. Current Commercial Readiness Position

GFCRI is currently suitable for paid pilot or POC review when deployed with clear methodology, source, limitation, and disclaimer language. It is not yet full institutional production ready.

Current strengths:

- Raw market data is persisted to `market_data_daily` before calculation.
- Official GFCRI index updates are blocked when critical market data quality fails.
- Market data freshness exposes coverage, latest trade date, missing tickers, stale tickers, and critical ticker status.
- Data quality assessment tracks source tiers, low-tier/proxy nodes, upgrade plans, and point-in-time readiness gaps.
- Institutional Radar uses official public metadata and does not ingest copyrighted full text.
- AI-assisted causal expansion is governed as a candidate workflow and does not directly mutate the core graph.

Production gates still required:

- formal data vendor/legal review for yfinance, Tushare, AKShare, FRED, OECD, and any future source;
- approved institutional market-data vendor or customer-approved private data connector for SLA-backed production;
- point-in-time/vintage backtest package for official macro series;
- RBAC, SSO/SAML, audit logs, API key governance, report approval workflow, and export governance;
- signed methodology, data-source notice, model limitation statement, and non-advisory disclaimer for client use.

## 3. Data Source Notice

Current GFCRI source families include:

| Source | Current use | Trust note |
|---|---|---|
| FRED | US macro, rates, and financial stress series | Official/public macro source; vintage and revision handling must be formalized for production backtests. |
| yfinance | Liquid market prices, indexes, ETFs, FX, commodity, and proxy tickers | Operational market-data source for pilot use; licensing and redistribution rights require legal/vendor review. |
| Tushare | Selected index and FX fallback data | China-market fallback/source integration; institutional terms require review. |
| OECD SDMX | Selected macro/rate context | Official/public macro source; revision and redistribution terms require review. |
| AKShare | China macro and market-related series | Public/community data access layer; production use requires licensing and source validation review. |
| Public official metadata | Institutional Radar source metadata and report references | GFCRI should store metadata and links, not copyrighted full-text reports, unless rights are separately cleared. |

Operational data handling:

- Market data is cached before model calculation.
- External market APIs are used to fill cache ranges, not as the final official calculation record.
- Missing or stale critical data must be visible to users through data-quality status.
- Data sources may be delayed, revised, permission-limited, temporarily unavailable, or inconsistent across regions.

## 4. Data Licensing Caveats

Use of public, free, community, or unofficial APIs does not automatically grant institutional commercial use, redistribution, white-label display, caching, export, or client-reporting rights.

Before production institutional deployment, GFCRI and the customer should complete a data-rights review covering:

- internal research use;
- commercial use;
- caching and derived calculation rights;
- display in dashboards;
- PDF/Excel/API export;
- redistribution to the customer's clients;
- white-label or embedded product use;
- record-retention requirements;
- required attribution and source notices;
- SLA, uptime, correction, and support obligations.

Free/public API use should be treated as pilot infrastructure unless counsel and the data owner confirm production suitability. For production, GFCRI should support either an approved institutional data vendor feed or a customer-provided connector that maps licensed data into the GFCRI node dictionary.

Proxy caveat: some current nodes use ETF, equity basket, or inverse-market proxies when direct series are unavailable. These are acceptable as transparent pilot fallbacks, but institution-grade production should reduce low-tier/proxy weight and replace material proxies with direct licensed series where available.

## 5. Model Limitation Statement

GFCRI is a macro-financial risk monitoring and explanation system. It is designed to monitor systemic stress, hidden risk, and risk-transmission conditions across market and macro indicators.

GFCRI does not:

- predict exact crisis timing;
- guarantee future market outcomes;
- estimate a complete probability distribution for crises;
- provide investment, trading, or asset-allocation recommendations;
- cover every policy, geopolitical, liquidity, market-structure, or operational event;
- prove causality between indicators;
- remove the need for human review, client suitability review, investment committee review, or model-risk review.

Historical analogies, stress scenarios, transmission chains, and hidden-risk readings are decision-support context. They are not expected outcomes and should not be presented as forecasts.

## 6. Non-Advisory Disclaimer

Required customer-facing disclaimer:

```text
GFCRI is provided for informational, research, and risk-monitoring purposes only. It does not constitute investment advice, trading advice, asset-allocation advice, legal advice, tax advice, accounting advice, fiduciary advice, or a recommendation to buy, sell, hold, hedge, or avoid any security, instrument, asset class, portfolio, fund, strategy, or financial product. Users remain responsible for independent analysis, suitability review, investment committee approval, and compliance with their own policies and applicable law.
```

Short UI disclaimer:

```text
GFCRI is a macro-risk monitoring tool, not an investment-advice or crisis-prediction engine.
```

Client-reporting rule: any report, export, dashboard, or API response used outside the customer's internal research workflow should include the non-advisory disclaimer and source/limitation notice unless the customer's compliance team approves alternate language.

## 7. Data Freshness Policy

GFCRI currently exposes a market data freshness surface through the commercial readiness workflow, including `/api/commercial-readiness/data-freshness` when served by the FastAPI app. The freshness check reads the persisted `market_data_daily` cache and reports:

- expected ticker count;
- cached ticker count;
- coverage percentage;
- earliest and latest trade date;
- latest collection timestamp;
- missing tickers;
- stale tickers;
- critical tickers;
- critical missing or stale tickers;
- configured maximum stale-day threshold.

Current default stale threshold: 7 calendar days, configurable through `MARKET_DATA_MAX_STALE_DAYS`.

Freshness states:

| State | Meaning | Customer-facing behavior |
|---|---|---|
| `ok` | Expected tickers are cached and fresh under the configured policy. | Publish normal freshness status. |
| `degraded` | Non-critical tickers are missing or stale. | Show degraded data status; report affected sources or tickers. |
| `blocked` | One or more critical market tickers are missing or stale. | Treat official publication as blocked until data is restored or an approved operational procedure is completed. |

Current critical market nodes:

- VIX;
- S&P 500;
- DXY;
- HYG;
- LQD;
- KOSPI;
- US 10Y;
- US 2Y;
- USD/CNY;
- USD/JPY.

Operational note: when an official or approved source such as FRED covers a critical rates node, a stale yfinance rates proxy should not by itself block the freshness gate. The customer-facing status should distinguish licensed/official source freshness from fallback market proxy freshness.

Production requirement: the customer should receive operational visibility into freshness state, latest successful refresh, failed source status, and whether the latest visible GFCRI index is current or held from the last reliable observation.

## 8. Official Index Publication Gate

GFCRI must not publish a new official daily risk index when the critical market-data gate fails.

Current publication behavior:

- The daily job checks critical node values and critical z-score coverage before official index persistence.
- Current gate logic requires at least 80% critical-node value coverage and complete critical z-score coverage.
- When the gate fails, GFCRI records a `risk_index_quality_events` entry with status `blocked`, message, missing critical nodes, missing critical z-scores, and policy metadata.
- A blocked run does not overwrite `daily_risk_index`.
- The application should continue showing the last reliable official index and disclose the blocked data-quality event.
- When data quality recovers, an `ok` quality event is recorded and official publication may resume.

Customer compliance interpretation:

- A held index is a data-quality control, not a model view that risk is unchanged.
- A blocked run should be visible in operational review, client support, and any report generated for that date.
- Backfilled data should be labeled as backfilled if the customer allows restatement or republishing.
- Manual override, if ever allowed for production, should require named approver, reason, affected nodes, timestamp, and customer policy approval.

## 9. Causal Language Policy

GFCRI uses directional graph assumptions and monitored transmission channels to organize macro-financial risk. Institutional-facing language must avoid implying that GFCRI has proven causal truth.

Preferred language:

- transmission channel;
- monitored linkage;
- pressure pathway;
- directional assumption;
- candidate mechanism;
- transmission hypothesis;
- observable test;
- falsification condition;
- graph-supported candidate;
- promotion-ready candidate, subject to human approval.

Avoid or restrict:

- proven causality;
- causal truth;
- guaranteed lead time;
- predicts the next crisis;
- will cause;
- ensures;
- definitive early warning;
- investment signal;
- buy/sell/hedge recommendation.

AI-assisted causal expansion policy:

- AI may propose candidate mechanisms only.
- Every candidate should include observable tests and falsification criteria.
- AI-generated candidates are persisted to a candidate registry for governance review.
- Candidate scoring may consider data coverage, graph support, repeat observation, falsifiability, temporal plausibility, and promotion-gate eligibility.
- The candidate workflow does not directly mutate the core graph.
- Promotion into the core graph requires human review and an approved change process.

## 10. Backtest Evidence Needed Before Production

Existing pilot evidence includes directional stress replay work against modern crisis windows. That evidence is useful for review, but it is not yet a complete production validation package because older windows have uneven production-node coverage and vintage/no-lookahead evidence still needs formalization.

Before full institutional production approval, GFCRI should provide a backtest evidence pack that documents:

- crisis window definitions and event taxonomy;
- realized damage labels separate from forward risk pressure;
- data source used for every node and date;
- observation date, release date, vintage date, and revision policy for official macro series;
- explicit no-lookahead controls;
- missing data, stale data, proxy substitution, and exclusion rules;
- benchmark comparisons against VIX, credit spreads, yield curve, DXY, and other agreed baselines;
- false positives, false negatives, precision/recall, and lead-time distribution;
- sensitivity to weights, thresholds, source tiers, and chain activation rules;
- out-of-sample or walk-forward validation;
- model version, code version, data snapshot, and run command for reproducibility;
- limitations for older periods with sparse market data;
- signoff by model owner, data owner, and customer reviewer.

Backtest communication rule: results may be described as historical replay, stress evidence, or validation evidence. They must not be described as proof that GFCRI will predict future crises.

## 11. Customer Review FAQ

### Is GFCRI investment advice?

No. GFCRI is provided for informational, research, and risk-monitoring purposes only. It is not investment advice, trading advice, asset-allocation advice, fiduciary advice, or a recommendation about any financial product.

### Does GFCRI predict crises?

No. GFCRI monitors systemic macro-financial stress and highlights how risk may transmit across markets. It does not predict exact crisis timing or guarantee future outcomes.

### What happens if market data is stale or missing?

GFCRI reports freshness state. Missing or stale non-critical tickers create a degraded status. Missing or stale critical tickers create a blocked status. The official index publication gate prevents incomplete critical data from overwriting the last reliable official index.

### Can a held index be interpreted as stable risk?

No. A held index means the official update was blocked by data quality controls. It should be presented as "last reliable observation held" with the blocked quality event disclosed.

### Are the current public/free data sources cleared for institutional redistribution?

Not automatically. Formal data licensing review is required before production institutional deployment, especially for caching, dashboards, exports, APIs, white-label use, and client-facing reports.

### Can a customer use its own licensed data vendor?

Yes, that is the preferred production path for many institutional deployments. Customer-approved feeds should be mapped to GFCRI nodes with documented source tier, formula, freshness threshold, and fallback policy.

### Does Institutional Radar store copyrighted reports?

The current position is to use official public metadata and links, not copyrighted full text, unless the customer or GFCRI has separately cleared the required rights.

### Are causal mechanisms validated?

Core graph assumptions and candidate mechanisms are governed separately. AI-assisted mechanisms are candidates only. They require observable tests, falsification criteria, repeat observation, and human approval before any promotion into the core graph.

### What audit evidence can GFCRI provide during a pilot?

Pilot review can include methodology documentation, source-tier disclosure, data freshness output, quality-gate events, current source lists, model limitation language, non-advisory disclaimer language, backtest replay documentation, and private deployment readiness notes.

### What remains before full production approval?

The main remaining gates are data-rights clearance, SLA-backed data operations, point-in-time/vintage backtest evidence, RBAC/SSO/audit-log hardening, API key governance, report approval workflow, export governance, and customer-specific disclaimer approval.

## 12. Customer Signoff Checklist

Customer compliance and procurement should confirm:

- data sources and licensing terms are approved for the intended deployment;
- source attribution and redistribution language are approved;
- the non-advisory disclaimer is approved;
- the model limitation statement is approved;
- freshness and publication-gate behavior is acceptable;
- held-index and blocked-run language is approved;
- report/export/API use cases are approved;
- causal language restrictions are included in customer-facing copy;
- backtest evidence is accepted for the intended stage;
- remaining production gaps are either closed or explicitly accepted for pilot scope.
