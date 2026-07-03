# GFCRI Model Foundation Audit

Date: 2026-07-03

## Purpose

GFCRI must be able to defend each model reading with:

- What data is used.
- Where the data comes from.
- How raw data becomes node stress.
- How node stress becomes sub-index pressure.
- Why the coverage is broad enough for the label being used.
- Where the current model is incomplete and how it will be improved.

This document records the current implementation and the target standard.

## Current Sub-Index Formula

Current implementation: `src/engines/risk_index.py`.

For each sub-index:

```text
mean_z = average(node anomaly_score)
mean_abs = average(node absolute_stress_score where available)
transmission = inbound transmission pressure from outside this node group

raw_stress = 0.4 * mean_z + 0.6 * mean_abs
sub_index_score = 100 * (0.6 * raw_stress + 0.4 * transmission)
```

Definitions:

- `anomaly_score`: directional stress score. For high-is-worse nodes, `max(zscore, 0) / 4`; for low-is-worse nodes, `max(-zscore, 0) / 4`; for two-sided stress nodes, `abs(zscore) / 4`. Capped at 1.0.
- `zscore`: `(current_value - 1Y historical_mean) / 1Y historical_std`.
- `absolute_stress_score`: stress from hard normal/crisis thresholds.
- `transmission`: average inbound causal pressure from nodes outside the sub-index.

Strength:

- Captures both sudden change and dangerous absolute levels.
- Helps avoid the 2008-style false calm problem where z-score normalizes while absolute stress remains high.

Weakness:

- One-year z-score is too short for slow-moving credit cycles.
- Some nodes use ETF or equity proxies for actual CDS/spread data.
- Absolute thresholds are incomplete.
- Sub-index labels can sound broader than current data coverage.

## Current Credit & Default Implementation

Current sub-index id: `SI_CREDIT`.

Current nodes:

| Node | Current data | Intended meaning | Current weakness |
|---|---|---|---|
| `fred_hy_spread` | FRED `BAMLH0A0HYM2` | US high-yield option-adjusted spread | US-only; needs CDX/global HY confirmation |
| `fred_bbb_spread` | FRED `BAMLC0A4CBBB` | US BBB corporate option-adjusted spread | US-only; misses Europe/Asia IG |
| `fred_ic_spread` | FRED `BAMLC0A1CAAAEY` | AAA corporate funding-cost anchor | Effective yield, not pure spread |
| `hyg` | HYG ETF via yfinance | US high-yield corporate credit stress | ETF price proxy, not direct option-adjusted spread/default risk |
| `lqd` | LQD ETF via yfinance | US investment-grade credit stress | ETF price proxy affected by duration and rates |
| `emb` | EMB ETF via yfinance | EM sovereign/hard-currency debt stress | ETF proxy, not direct EM spread/debt service stress |
| `kr_cds_5y` | EWY inverse proxy | Korea sovereign credit stress | Not actual Korea 5Y CDS |
| `orcl_cds` | ORCL inverse proxy | AI/cloud credit stress proxy | Not actual Oracle CDS spread |

2026-07-03 implementation update:

- FRED high-yield OAS, BBB OAS, and AAA corporate effective-yield nodes are now formal graph nodes.
- `SI_CREDIT` now uses direct FRED credit data first, while retaining ETF/proxy nodes as supplementary market confirmation.
- A machine-readable node data dictionary was added in `src/models/data_dictionary.py`.
- The data dictionary now covers all 41 current graph nodes with source tier, raw formula, stress direction, limitations, and upgrade plan. Remaining work is source replacement/validation, not missing metadata.
- FRED `DGS10`, `DGS2`, and `RECPROUSM156N` now replace yfinance/TLT proxies for `ust_10y`, `ust_2y`, and `us_recession_prob`, including historical series used for z-score calculation.
- FRED `WALCL` now replaces TLT as the `global_liqd` source, making the node an official Fed balance-sheet liquidity proxy. `dram_spot`, `nand_spot`, and `ai_capex` display names were corrected to explicit proxy names until direct memory-price and capex-filing data are added.
- FRED `KORB6BLTT02STSAQ` now replaces EWY as the `kr_ca` source, making Korea current account a real official macro node. `kr_cds_5y` was renamed to an explicit EWY-inverted Korea credit stress proxy until actual Korea CDS data is available.
- `ai_capex` and `orcl_cds` now use normalized multi-name AI/cloud baskets instead of single CLOU/ORCL proxies. They remain Tier C until actual capex filings, CDS, or bond-OAS data are available, but single-name noise is reduced.
- `dram_spot` and `nand_spot` no longer duplicate the same SMH proxy. They now use separate normalized producer baskets for DRAM and NAND/storage cycles, while remaining Tier C until direct memory price data is licensed or integrated.
- `SI_CREDIT` now uses a dimension-weighted formula instead of a flat node average. Current dimensions are US corporate credit, EM/sovereign credit, and AI/cloud credit; Europe credit, bank funding, defaults/downgrades, and China credit remain planned dimensions.
- FRED `BAMLHE00EHYIOAS` has been added as `fred_euro_hy_spread`, starting the Europe Credit dimension with a direct Euro high-yield OAS signal.
- FRED `SOFR` and computed `SOFR - EFFR` have been added as the first Bank Funding dimension signals.
- FRED `DRALACBS` and `BAA10Y` have been added as the first Default / Downgrade Cycle signals, combining realized bank-loan delinquency with Baa credit-risk pricing.
- `anomaly_score` is now directional rather than absolute. Risk-improving anomalies no longer automatically add pressure to sub-indices.

Current online example:

```text
SI_CREDIT score = 14.45

node anomaly scores:
HYG       0.3840
LQD       0.1981
EMB       0.3498
Oracle    0.3560
Korea CDS 0.3744

mean_z = 0.3325
mean_abs = 0.0860
transmission = 0.0843

raw_stress = 0.4 * 0.3325 + 0.6 * 0.0860 = 0.1846
score = 100 * (0.6 * 0.1846 + 0.4 * 0.0843) = 14.45
```

Interpretation:

- Current score says credit pressure is visible but not severe.
- The reading is mostly anomaly-driven.
- Absolute credit stress is low because only HYG and LQD have absolute thresholds today.
- This is not yet a complete global credit/default pressure measure.

## Target: Global Credit & Default Pressure

Keep the product label `Global Credit & Default Pressure`, but make the model worthy of that label by expanding coverage.

### Target Dimensions

| Dimension | Required signals | Purpose |
|---|---|---|
| US corporate credit | HY OAS, IG OAS, BBB OAS, CDX HY, CDX IG | Core global corporate credit cycle |
| Europe corporate credit | Euro HY OAS now implemented; iTraxx Europe, iTraxx Crossover, EUR IG spreads planned | Europe credit stress and bank/sovereign feedback |
| EM sovereign credit | EMB spread, EMBI Global, major sovereign CDS, FX debt stress | Dollar funding and sovereign default pressure |
| Bank funding | SOFR and SOFR-EFFR spread now implemented; SOFR-IORB, bank CDS, senior financial spreads, cross-currency basis planned | Funding market stress |
| Sovereign credit | US, Italy, UK, Japan, China proxy, Korea CDS | Sovereign confidence and refinancing stress |
| Default/downgrade cycle | US bank loan delinquency and Baa-10Y spread now implemented; HY default rates, distressed ratios, rating downgrades, bankruptcy filings planned | Realized credit damage |
| China credit | credit impulse, total social financing, property bond spreads, LGFV stress | Non-US credit channel |

### Target Formula

The implemented formula is now evolving from a flat node average into a dimension-weighted structure. Current implementation covers available dimensions first; target dimensions remain broader:

```text
Global Credit & Default Pressure =
  0.25 * US corporate credit stress
+ 0.15 * Europe corporate credit stress
+ 0.15 * EM sovereign credit stress
+ 0.15 * bank funding stress
+ 0.10 * sovereign credit stress
+ 0.10 * default/downgrade cycle
+ 0.10 * China credit stress

Each dimension =
  0.35 * short-term anomaly
+ 0.45 * absolute stress percentile
+ 0.20 * transmission / deterioration momentum
```

Rationale:

- Credit crises are usually not only price changes.
- A professional credit module must separate market-implied stress, actual default/downgrade damage, funding liquidity, and regional credit systems.
- Absolute stress should use long history percentiles or crisis anchors rather than only one-year z-scores.

## Data Source Standard

Each node must be classified by quality:

| Tier | Source type | Use |
|---|---|---|
| A | Official or primary index provider API | Core model input |
| B | Widely used market data vendor / ETF with liquid history | Proxy when direct data is unavailable |
| C | Equity/ETF inverse proxy for credit/CDS | Temporary fallback only |
| D | Synthetic or narrative proxy | Research-only, not core scoring |

Current credit module has too many Tier B/C proxies. Target state should use mostly Tier A/B, with C only as fallback.

## Full Node Audit Standard

For every node in `src/models/nodes.py`, maintain:

```text
node_id
display_name
economic meaning
raw data source
source tier
raw formula, if computed
z-score lookback
absolute-stress threshold or percentile method
direction of stress
sub-index membership
causal-chain membership
known limitations
replacement / upgrade plan
```

## Immediate Engineering Plan

1. Add a data dictionary table for every node.
2. Replace proxy credit nodes with direct spread/CDS/default-rate series where available.
3. Add dimension-level credit model before calculating final `SI_CREDIT`.
4. Expand absolute thresholds using long-history percentiles and historical crisis anchors.
5. Add UI drilldown:
   - formula receipt,
   - data source,
   - source tier,
   - node-level contribution,
   - dimension-level contribution,
   - limitations.

## Acceptance Criteria

The credit module should not be considered institution-grade until:

- At least 5 credit dimensions are represented.
- At least 70% of credit weight comes from Tier A/B direct credit data.
- ETF inverse proxies contribute less than 15% of total credit score weight.
- Each node has a documented formula and source tier.
- Backtests show whether expanded credit data improves early warning before 2000, 2008, 2010, 2020, and 2022.
