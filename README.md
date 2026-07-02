# GFCRI - Global Financial Crisis Risk Index

GFCRI is a macro-financial risk monitoring platform that tracks systemic stress, risk transmission channels, hidden risk signals, stress-test scenarios, and historical crisis analogies across global markets.

It is designed as an explainable risk-intelligence product, not a black-box crisis predictor. The goal is to help users understand whether macro-financial stress is building, where it is coming from, and how it may transmit across rates, FX, credit, equity, commodities, and sentiment.

## Product Positioning

Most market dashboards show asset prices. GFCRI focuses on risk propagation:

- Which indicators are outside normal ranges?
- Which risk channels are active?
- Is stress isolated or synchronized across markets?
- Are surface indicators calm while structural indicators are deteriorating?
- Which historical crisis regimes look similar to current conditions?
- How would predefined stress scenarios change the aggregate risk index?

## Current Capabilities

### Risk Index

- Daily GFCRI score from 0 to 100
- Alert levels from normal to critical stress
- Sub-index decomposition by risk domain
- Signal coherence multiplier for multi-chain synchronization
- Hidden-risk / undercurrent boost for surface-calm, deep-stress conditions

### Explainability

- Sub-index stress composition chart
- Key indicator contribution table
- Transmission channel pressure table
- Expandable chain-level calculation details
- Node-level current value, z-score, anomaly score, and absolute stress
- Path strength calculation from causal edge weights

### Risk Transmission

The platform models macro-financial stress through predefined transmission channels such as:

- Central bank hike shockwave
- Strong dollar squeeze
- Credit crisis contagion
- Real estate banking crisis
- China shockwave
- Eurozone debt contagion
- Yen carry unwind
- Food and energy shock

### Forward Risk Monitor

- Crisis proximity / distance-to-stress-threshold view
- Predefined stress-test scenarios
- Economy health ranking
- Policy buffer analysis

### Historical Validation

- Historical backtest view across major crisis episodes
- Crisis peak comparison
- Lead-time summary
- Historical analogy panel

### Productization

- Vue-based frontend dashboard
- FastAPI backend
- PostgreSQL persistence
- Docker Compose deployment
- Pro trial flow with 7-day trial state
- Bilingual Chinese / English UI
- Methodology, data, and limitations page

## Technical Stack

- Backend: Python, FastAPI, APScheduler
- Database: PostgreSQL
- Data: yfinance, FRED, OECD, AKShare, public market data
- Modeling: pandas, numpy, scipy, scikit-learn, statsmodels, networkx
- Frontend: Vue 3, TypeScript, Pinia, ECharts, Tailwind CSS
- Deployment: Docker Compose, Nginx

## Model Design

GFCRI combines several layers of risk evidence:

### 1. Indicator Anomaly

Each node can be scored with a standardized deviation:

```text
Z-score = (current value - historical mean) / historical standard deviation
Anomaly Score = min(1.0, abs(Z-score) / 4.0)
```

This captures fast deviations from recent history.

### 2. Absolute Stress

Some indicators have absolute stress thresholds. This helps detect chronic high-pressure conditions that may no longer look unusual by z-score alone.

```text
Absolute Stress = position between normal threshold and crisis threshold
```

### 3. Sub-Index Aggregation

Indicators are grouped into macro risk domains such as rates, FX, equity, credit, commodities, and sentiment. Sub-index scores combine anomaly stress, absolute stress, and transmission amplification.

### 4. Transmission Channels

Each channel contains a path of causally linked indicators. Current chain stress is computed from node anomaly scores.

```text
Chain Stress = average(node anomaly scores) x 100
Path Strength = product(edge causal strengths)
```

### 5. Signal Coherence

When multiple transmission channels are active at the same time, aggregate risk is amplified.

```text
Coherence Multiplier = 1 + 0.05 x max(0, active_chain_count - 1)
```

### 6. Hidden Risk / Undercurrent

GFCRI includes a hidden-risk layer for cases where headline market volatility looks calm but deeper structural indicators are stressed. Examples include elevated credit spreads, banking stress, dollar pressure, or high absolute stress levels that z-score has become desensitized to.

## What GFCRI Is Not

GFCRI is not an investment recommendation engine and does not predict the exact timing of financial crises. It is a monitoring and explanation system.

The correct interpretation is:

```text
GFCRI monitors systemic macro-financial stress and highlights how risk may transmit across markets.
```

Not:

```text
GFCRI predicts the next crisis date.
```

## Current Limitations

- Edge weights currently require stronger statistical validation and confidence scoring.
- Some absolute stress thresholds are still incomplete.
- False-positive analysis needs to be expanded beyond crisis windows.
- Historical backtests need stronger no-lookahead documentation.
- More automated tests are needed for model, API, and frontend behavior.
- Data availability varies across regions and instruments.
- Some data sources may be delayed, revised, or temporarily unavailable.
- The authentication and Pro-trial implementation is MVP-grade and should be hardened before commercial launch.

## Roadmap Toward a Professional Portfolio / Commercial Product

### Model Validation

- Add false-positive and false-negative analysis.
- Compare GFCRI against baseline indicators such as VIX, credit spreads, yield curve, and DXY.
- Add sensitivity analysis for weights, thresholds, and chain activation rules.
- Add sample-out-of-sample validation.
- Document crisis window definitions and lead-time methodology.

### Model Explainability

- Add edge confidence, evidence type, and last validation date.
- Add methodology for causal edge weights.
- Expand absolute stress thresholds for more nodes.
- Add historical references for each absolute threshold.
- Expose divergence and undercurrent components in API and UI.

### Data Engineering

- Persist raw market and macro data snapshots.
- Add data freshness indicators per source.
- Add missing-data and stale-data policies.
- Add data revision tracking.
- Add scheduled refresh status and failure alerts.

### Engineering Quality

- Add pytest coverage for core risk index calculations.
- Add API integration tests.
- Add reproducible backtest tests.
- Add Playwright visual checks for the English product flow.
- Add CI pipeline for backend compile, frontend build, and tests.

### Product Trust

- Improve methodology documentation.
- Add public data-source documentation.
- Add limitations and disclaimer pages.
- Add model versioning.
- Add release notes and changelog.

## Running Locally

Copy the environment template:

```bash
cp .env.example .env
```

Start the stack:

```bash
docker compose up -d --build
```

Frontend:

```text
http://localhost:3000
```

API:

```text
http://localhost:8000/api/health
```

Streamlit dashboard:

```text
http://localhost:8501
```

## Development Checks

Backend syntax check:

```bash
python3 -m compileall api src
```

Frontend build:

```bash
cd frontend
./node_modules/.bin/vite build
```

## Disclaimer

GFCRI is provided for informational and risk-monitoring purposes only. It is not investment advice, trading advice, or a recommendation to buy or sell any financial product. Historical analogies and stress-test scenarios do not guarantee future outcomes.

