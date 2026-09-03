# GFCRI Institutional Value Layer

Date: 2026-09-03

Status: Implemented on `feature/institutional-value-layer`

## Purpose

The institutional product does not sell raw market observations. Raw
observations are governed inputs used inside the analysis boundary.

The customer-facing value is the derived evidence chain:

```text
source observations
-> directional anomaly
-> absolute stress
-> risk-domain contribution
-> transmission channel
-> hidden-risk divergence
-> confidence and data quality
-> workflow watch-next
```

## Product Tiers

| Tier | Customer value | Visible output |
|---|---|---|
| Research | Understand the current risk state | Score, risk level, top derived contributors, hidden-risk summary, limited transmission summary, watch-next |
| Team | Run a recurring institutional review | Full derived contributors, source-tier classes, transmission paths, quality breakdown, formula receipt, workflow guidance |
| Private | Deploy a governed institution-specific workflow | Team output plus private delivery flag, customer-derived overlays, expanded evidence and future licensed connectors |

All tiers set:

```text
raw_observations_exposed = false
derived_evidence_exposed = true
```

Higher tiers expose more derived evidence and delivery governance. They do not
create a different risk truth or return raw source datasets.

## Algorithmic Evidence

### Directional anomaly

Measures whether the current observation is moving in a risk-increasing
direction for the node.

### Absolute stress

Measures whether the current level is close to a configured normal/crisis
range. This prevents recent-history normalization from hiding persistent
stress.

### Risk-domain contribution

Aggregates node-level evidence into rates, FX, equities, credit, banking,
commodities, sentiment, and other configured domains. Each domain exposes a
score, contribution share, transmission component, and evidence count.

### Transmission channel

Maps related stress across a monitored path such as credit contagion, dollar
squeeze, rate shock, trade spillover, or yen carry unwind. These are monitored
linkages and hypotheses, not proven causal truth.

### Hidden risk

Compares surface conditions with deeper or structural pressure and includes
undercurrent and active-chain context. The result is a review prompt, not a
guaranteed early-warning claim.

### Confidence and quality

The value layer combines data-quality status, coverage, source-tier mix,
derived evidence count, and risk-domain coverage into a confidence summary.
It preserves degraded/empty conditions rather than presenting incomplete data
as a clean current signal.

### Watch Next

Converts the analysis into workflow questions:

- Can critical inputs be refreshed and verified?
- Does hidden pressure normalize or broaden?
- Does the top contributor confirm or reverse?
- Does the monitored transmission channel become more active?

## API Contract

### Analysis request

`POST /api/v1/institutional/analysis-runs`

```json
{
  "entity_type": "economy",
  "entity_id": "US",
  "snapshot_id": "tenant:daily-2026-09-03",
  "product_tier": "team",
  "parameters": {
    "workflow": "investment_committee_review"
  }
}
```

The existing `product_tier` defaults to `research`, preserving compatibility
with older clients.

### Manifest

`GET /api/v1/institutional/value-layer-manifest`

The manifest describes the tier limits and confirms that raw observations are
not part of the customer-facing output.

## Output Fields

The enriched analysis result includes:

- `risk_score`
- `risk_level`
- `dimensions.risk_domains`
- `contributors`
- `transmission_paths`
- `hidden_risk`
- `watch_next`
- `confidence`
- `data_quality`
- `algorithm`
- `formula_receipt` for Team and Private tiers
- `delivery.raw_observations_exposed = false`

The output intentionally excludes raw observation values. Derived pressure
scores, normalized stress, contribution shares, quality status, and source
classes are the product surface.

## Commercial Boundaries

The current implementation is appropriate for an explainable pilot workflow.
Production institutional commercialization still requires:

- licensed or customer-provided data connectors;
- point-in-time/vintage backtest evidence;
- full tenant RBAC and audit logs;
- export governance;
- source-specific redistribution review;
- SLA-backed data refresh and alerting.

