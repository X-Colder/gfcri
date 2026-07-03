"""Machine-readable data dictionary for GFCRI nodes.

This file makes model data provenance explicit. It is intentionally lightweight:
the node registry remains the source of truth for canonical node definitions,
while this dictionary records data-source quality, raw formulas, and known
limitations needed for institutional-grade auditability.
"""

from __future__ import annotations

from typing import Any

from src.models.nodes import CORE_NODES


SOURCE_TIERS: dict[str, str] = {
    "A": "Official or primary index/provider data suitable for core scoring.",
    "B": "Liquid market proxy or broad ETF suitable as fallback/core supplement.",
    "C": "Equity/ETF inverse or narrow proxy; temporary fallback only.",
    "D": "Synthetic or narrative proxy; research-only unless validated.",
}


NODE_DATA_OVERRIDES: dict[str, dict[str, Any]] = {
    # Rates / policy
    "fed_funds": {
        "source_tier": "A",
        "raw_formula": "FRED EFFR latest observation when available; otherwise yfinance ^IRX as temporary proxy.",
        "stress_direction": "higher_is_tightening_pressure",
        "absolute_threshold": "not scored directly; policy-space and rates context",
        "known_limitations": "Policy rate is not itself financial stress; impact depends on inflation, growth, and refinancing needs.",
        "upgrade_plan": "Use EFFR/SOFR/OIS curve and central-bank policy rates across major economies.",
    },
    "ust_10y": {
        "source_tier": "A",
        "raw_formula": "FRED DGS10 latest observation and history, 10-year Treasury constant maturity rate in percent.",
        "stress_direction": "higher_is_worse_for_duration_and_funding",
        "absolute_threshold": "normal=3.5, crisis=5.2",
        "known_limitations": "Nominal yield mixes real rates, inflation expectations, term premium, and growth expectations.",
        "upgrade_plan": "Add real yield, term premium, Treasury volatility, and cross-country long-rate comparison.",
    },
    "ust_2y": {
        "source_tier": "A",
        "raw_formula": "FRED DGS2 latest observation and history, 2-year Treasury constant maturity rate in percent.",
        "stress_direction": "higher_is_policy_tightness",
        "absolute_threshold": "normal=3.5, crisis=5.5",
        "known_limitations": "2Y yield reflects expected policy path, not direct credit stress; can fall during recession fear.",
        "upgrade_plan": "Add SOFR/OIS curve, Fed funds futures, and rate-cut expectation decomposition.",
    },
    "global_liqd": {
        "source_tier": "A",
        "raw_formula": "FRED WALCL latest observation and history, Federal Reserve total assets in USD millions.",
        "stress_direction": "lower_liquidity_or_fast_balance_sheet_contraction_can_tighten_conditions",
        "absolute_threshold": "not yet defined",
        "known_limitations": "Fed balance sheet is US dollar liquidity proxy, not full global liquidity; ECB, BOJ, PBOC and offshore dollar funding are missing.",
        "upgrade_plan": "Add ECB/BOJ/PBOC balance sheets, cross-currency basis, dollar swap lines, reserve balances, and global credit impulse data.",
    },

    # FX
    "dxy": {
        "source_tier": "B",
        "raw_formula": "DX-Y.NYB adjusted close from yfinance.",
        "stress_direction": "higher_is_worse_for_global_dollar_funding",
        "absolute_threshold": "normal=100, crisis=114",
        "known_limitations": "DXY is developed-market currency basket; misses broader dollar funding basis and EM FX stress.",
        "upgrade_plan": "Add BIS broad dollar index, cross-currency basis, and EM dollar funding measures.",
    },
    "krw_usd": {
        "source_tier": "B",
        "raw_formula": "KRW=X adjusted close from yfinance.",
        "stress_direction": "higher_is_won_depreciation_pressure",
        "absolute_threshold": "normal=1250, crisis=1550",
        "known_limitations": "Single Asian FX pair; can reflect Korea-specific factors and not global FX stress alone.",
        "upgrade_plan": "Add CNH, TWD, JPY, broad Asia FX basket and dollar funding basis.",
    },
    "eurusd": {
        "source_tier": "B",
        "raw_formula": "EURUSD=X adjusted close from yfinance.",
        "stress_direction": "lower_is_euro_area_or_dollar_stress",
        "absolute_threshold": "normal=1.10, crisis=0.95",
        "known_limitations": "FX level mixes growth, rates, and policy expectations.",
        "upgrade_plan": "Add EUR cross-currency basis and Eurozone sovereign spreads.",
    },
    "cny_usd": {
        "source_tier": "B",
        "raw_formula": "CNY=X adjusted close from yfinance.",
        "stress_direction": "higher_is_renminbi_depreciation_pressure",
        "absolute_threshold": "not yet defined",
        "known_limitations": "Onshore CNY is managed; offshore CNH and fixing pressure are not captured.",
        "upgrade_plan": "Add USD/CNH, fixing deviation, China FX reserves and capital-flow proxies.",
    },
    "jpy_usd": {
        "source_tier": "B",
        "raw_formula": "JPY=X adjusted close from yfinance.",
        "stress_direction": "higher_is_yen_depreciation_carry_pressure",
        "absolute_threshold": "normal=130, crisis=160",
        "known_limitations": "JPY weakness can be policy-driven and not always crisis stress; carry unwind risk needs positioning data.",
        "upgrade_plan": "Add JPY basis, CFTC positioning, rate differential, and BOJ policy stress indicators.",
    },

    # Equity / risk appetite
    "vix": {
        "source_tier": "A",
        "raw_formula": "^VIX adjusted close from yfinance / CBOE index level.",
        "stress_direction": "higher_is_worse",
        "absolute_threshold": "normal=15, crisis=45",
        "known_limitations": "VIX can be suppressed by policy/liquidity and misses slow credit deterioration.",
        "upgrade_plan": "Add MOVE, skew, credit volatility and realized volatility cross-checks.",
    },
    "spx": {
        "source_tier": "B",
        "raw_formula": "^GSPC adjusted close from yfinance.",
        "stress_direction": "lower_is_equity_damage; high levels can also indicate bubble risk separately",
        "absolute_threshold": "normal=5000, crisis=3500",
        "known_limitations": "Index level alone does not distinguish healthy earnings growth from bubble valuation.",
        "upgrade_plan": "Add drawdown, valuation, earnings revisions and breadth metrics.",
    },
    "sox": {
        "source_tier": "B",
        "raw_formula": "^SOX adjusted close from yfinance.",
        "stress_direction": "lower_is_sector_damage; high positive anomaly can indicate speculative overextension",
        "absolute_threshold": "normal=4000, crisis=2500",
        "known_limitations": "Semiconductor index is not a macro variable; AI cycle can dominate signal.",
        "upgrade_plan": "Add valuation, earnings revisions, capex orders, and memory-price data.",
    },
    "kospi": {
        "source_tier": "B",
        "raw_formula": "^KS11 adjusted close from yfinance.",
        "stress_direction": "lower_is_korea_equity_damage; high levels can imply crowding",
        "absolute_threshold": "normal=2600, crisis=1800",
        "known_limitations": "KOSPI is affected by semiconductors and local policy; not a pure global-risk proxy.",
        "upgrade_plan": "Add foreign flows, KRW hedging pressure, Korea exports and CDS.",
    },
    "hsi": {
        "source_tier": "B",
        "raw_formula": "^HSI adjusted close from yfinance.",
        "stress_direction": "lower_is_hong_kong_china_equity_stress",
        "absolute_threshold": "normal=22000, crisis=14000",
        "known_limitations": "Captures offshore China equity but not full China credit/property stress.",
        "upgrade_plan": "Add HSCEI, China property bonds, CNH, and north/southbound flows.",
    },
    "nikkei": {
        "source_tier": "B",
        "raw_formula": "^N225 adjusted close from yfinance.",
        "stress_direction": "lower_is_japan_equity_damage; high level with weak yen can indicate carry/crowding risk",
        "absolute_threshold": "not yet defined",
        "known_limitations": "Equity level can rise because of yen weakness; not direct financial stress.",
        "upgrade_plan": "Add TOPIX banks, JGB yields, JPY basis and foreign-flow data.",
    },
    "stoxx50": {
        "source_tier": "B",
        "raw_formula": "^STOXX50E adjusted close from yfinance.",
        "stress_direction": "lower_is_euro_equity_damage",
        "absolute_threshold": "normal=4200, crisis=3200",
        "known_limitations": "Large-cap equity index can miss sovereign/bank stress until late.",
        "upgrade_plan": "Add Euro bank equity, sovereign spreads, and iTraxx indicators.",
    },
    "italy_etf": {
        "source_tier": "B",
        "raw_formula": "EWI adjusted close from yfinance as Italy sovereign/equity stress proxy.",
        "stress_direction": "lower_is_italy_stress",
        "absolute_threshold": "not yet defined",
        "known_limitations": "Equity ETF is a proxy; actual Italy-Germany spread is more direct.",
        "upgrade_plan": "Replace/supplement with Italy-Germany 10Y spread and Italian bank CDS/equity.",
    },
    "eem": {
        "source_tier": "B",
        "raw_formula": "EEM adjusted close from yfinance.",
        "stress_direction": "lower_is_em_risk_off",
        "absolute_threshold": "normal=42, crisis=30",
        "known_limitations": "ETF mixes China/Taiwan/India composition, FX, and equity risk.",
        "upgrade_plan": "Add EM FX basket, EM credit spread and regional equity baskets.",
    },

    # Credit
    "fred_hy_spread": {
        "source_tier": "A",
        "raw_formula": "FRED BAMLH0A0HYM2 latest observation; level in percentage points.",
        "stress_direction": "higher_is_worse",
        "absolute_threshold": "normal=3.5, crisis=10.0",
        "known_limitations": "US high-yield credit only; does not cover Europe, China, private credit, or bank funding.",
        "upgrade_plan": "Add CDX HY and global HY spread composites when data access is available.",
    },
    "fred_bbb_spread": {
        "source_tier": "A",
        "raw_formula": "FRED BAMLC0A4CBBB latest observation; BBB option-adjusted spread in percentage points.",
        "stress_direction": "higher_is_worse",
        "absolute_threshold": "normal=1.2, crisis=4.0",
        "known_limitations": "US BBB credit only; misses non-US investment-grade stress.",
        "upgrade_plan": "Add CDX IG, US IG OAS, and Europe IG spread indices.",
    },
    "fred_ic_spread": {
        "source_tier": "A",
        "raw_formula": "FRED BAMLC0A1CAAAEY latest observation; AAA corporate effective yield.",
        "stress_direction": "higher_is_worse",
        "absolute_threshold": "normal=4.0, crisis=7.0",
        "known_limitations": "Effective yield mixes risk-free rates and credit premium; not a pure spread.",
        "upgrade_plan": "Replace or supplement with pure AAA/IG option-adjusted spread series.",
    },
    "fred_euro_hy_spread": {
        "source_tier": "A",
        "raw_formula": "FRED BAMLHE00EHYIOAS latest observation; ICE BofA Euro High Yield OAS in percentage points.",
        "stress_direction": "higher_is_worse",
        "absolute_threshold": "normal=3.5, crisis=12.0",
        "known_limitations": "European high-yield credit only; does not cover European investment-grade credit, bank funding, or sovereign-bank feedback.",
        "upgrade_plan": "Add iTraxx Crossover, iTraxx Europe, European IG OAS, and bank CDS/bond spreads.",
    },
    "fred_sofr": {
        "source_tier": "A",
        "raw_formula": "FRED SOFR latest observation; secured overnight financing rate in percent.",
        "stress_direction": "higher_is_tighter_repo_funding",
        "absolute_threshold": "normal=3.5, crisis=5.5",
        "known_limitations": "SOFR level includes policy-rate regime; level alone is not pure funding stress.",
        "upgrade_plan": "Use SOFR-EFFR, SOFR-IORB, repo specials, and funding-market dispersion indicators.",
    },
    "sofr_effr_spread": {
        "source_tier": "A",
        "raw_formula": "(FRED SOFR - FRED EFFR) * 100, computed in basis points.",
        "stress_direction": "higher_is_repo_funding_pressure",
        "absolute_threshold": "normal=0 bps, crisis=75 bps",
        "known_limitations": "SOFR-EFFR spread is a narrow US overnight funding proxy; bank credit, term funding, and cross-currency funding are not captured.",
        "upgrade_plan": "Add SOFR-IORB, FRA/OIS-like proxies, cross-currency basis, bank CDS, and senior financial bond spreads.",
    },
    "fred_all_loan_delinquency": {
        "source_tier": "A",
        "raw_formula": "FRED DRALACBS latest observation; delinquency rate on all loans and leases at US commercial banks.",
        "stress_direction": "higher_is_realized_credit_damage",
        "absolute_threshold": "normal=1.5, crisis=6.0",
        "known_limitations": "Quarterly and US banking-system focused; lags market stress and misses non-bank/private credit defaults.",
        "upgrade_plan": "Add leveraged-loan default rates, HY default rates, bankruptcy filings, and rating downgrade ratios.",
    },
    "fred_baa10y_spread": {
        "source_tier": "A",
        "raw_formula": "FRED BAA10Y latest observation; Moody's seasoned Baa corporate bond yield minus 10-year Treasury yield.",
        "stress_direction": "higher_is_downgrade_default_pricing_pressure",
        "absolute_threshold": "normal=1.5, crisis=5.0",
        "known_limitations": "Market-implied spread, not realized default rate; US Baa focus only.",
        "upgrade_plan": "Add rating downgrade counts, distressed debt ratios, and issuer-level default baskets.",
    },
    "hyg": {
        "source_tier": "B",
        "raw_formula": "HYG adjusted close from yfinance.",
        "stress_direction": "lower_is_worse",
        "absolute_threshold": "normal=82, crisis=60",
        "known_limitations": "ETF price mixes credit spread, duration, liquidity, and ETF flow effects.",
        "upgrade_plan": "Keep as liquid market confirmation; reduce weight when direct HY OAS/CDX HY are available.",
    },
    "lqd": {
        "source_tier": "B",
        "raw_formula": "LQD adjusted close from yfinance.",
        "stress_direction": "lower_is_worse",
        "absolute_threshold": "normal=110, crisis=90",
        "known_limitations": "ETF price is duration-sensitive and not a pure credit spread.",
        "upgrade_plan": "Keep as market confirmation; add direct IG OAS/CDX IG data.",
    },
    "emb": {
        "source_tier": "B",
        "raw_formula": "EMB adjusted close from yfinance.",
        "stress_direction": "lower_is_worse",
        "absolute_threshold": "not yet defined",
        "known_limitations": "ETF proxy; does not decompose sovereign spread, duration, and FX effects.",
        "upgrade_plan": "Add EMBI Global spread, sovereign CDS basket, and country-level EM stress.",
    },
    "kr_cds_5y": {
        "source_tier": "C",
        "raw_formula": "-EWY adjusted close from yfinance as temporary inverse proxy.",
        "stress_direction": "higher_is_worse after inversion",
        "absolute_threshold": "not yet defined",
        "known_limitations": "Not actual Korea CDS; equity proxy can move for non-credit reasons and should be treated as Korea credit/equity stress proxy only.",
        "upgrade_plan": "Replace with actual Korea 5Y sovereign CDS or official sovereign spread proxy.",
    },
    "orcl_cds": {
        "source_tier": "C",
        "raw_formula": "Negative equal-weight normalized basket of ORCL, MSFT, AMZN, GOOGL, and META adjusted closes from yfinance.",
        "stress_direction": "higher_is_worse after inversion",
        "absolute_threshold": "not yet defined",
        "known_limitations": "Not actual CDS or bond spread data; equity-basket proxy can move for valuation, earnings, and positioning reasons unrelated to credit.",
        "upgrade_plan": "Replace with actual AI/cloud issuer CDS, bond OAS, or a cloud infrastructure credit spread basket.",
    },

    # Banking / real estate / consumer
    "kre": {
        "source_tier": "B",
        "raw_formula": "KRE adjusted close from yfinance.",
        "stress_direction": "lower_is_regional_bank_stress",
        "absolute_threshold": "normal=50, crisis=30",
        "known_limitations": "Equity ETF reflects bank profitability and rates, not direct funding/default risk.",
        "upgrade_plan": "Add bank CDS, deposit-flow data, CRE exposure and funding spreads.",
    },
    "vnq": {
        "source_tier": "B",
        "raw_formula": "VNQ adjusted close from yfinance.",
        "stress_direction": "lower_is_real_estate_stress",
        "absolute_threshold": "normal=85, crisis=55",
        "known_limitations": "REIT ETF is market price, not direct property valuation or loan delinquency data.",
        "upgrade_plan": "Add CRE delinquency, REIT credit spreads, property prices and cap rates.",
    },
    "consumer_stress": {
        "source_tier": "B",
        "raw_formula": "XLY adjusted close divided by XLP adjusted close from yfinance.",
        "stress_direction": "lower_ratio_is_consumer_defensiveness",
        "absolute_threshold": "not yet defined",
        "known_limitations": "Equity-sector ratio is a proxy and can be valuation-driven.",
        "upgrade_plan": "Add real consumer delinquency, confidence, unemployment and retail-sales stress.",
    },
    "us_recession_prob": {
        "source_tier": "A",
        "raw_formula": "FRED RECPROUSM156N latest observation and history, smoothed US recession probability in percent.",
        "stress_direction": "higher_is_recession_probability",
        "absolute_threshold": "normal=5, crisis=50",
        "known_limitations": "Monthly recession-probability model updates slowly and can lag fast market breaks.",
        "upgrade_plan": "Add NY Fed yield-curve recession probability, Sahm-rule signal, labor deterioration, and PMI nowcast.",
    },

    # Commodities / real economy / safe haven
    "oil_wti": {
        "source_tier": "B",
        "raw_formula": "CL=F adjusted close from yfinance.",
        "stress_direction": "higher_is_energy_inflation_supply_shock",
        "absolute_threshold": "normal=70, crisis=120",
        "known_limitations": "Oil price can rise on growth demand or supply shock; direction depends on context.",
        "upgrade_plan": "Add inventories, term structure, energy credit and geopolitical supply indicators.",
    },
    "copper": {
        "source_tier": "B",
        "raw_formula": "HG=F adjusted close from yfinance.",
        "stress_direction": "lower_is_growth_stress; sharp high moves can indicate inflation/supply stress",
        "absolute_threshold": "normal=4.0, crisis=3.0",
        "known_limitations": "Copper mixes China demand, supply constraints and dollar effects.",
        "upgrade_plan": "Add LME inventories, China PMI/credit impulse and industrial production.",
    },
    "gold": {
        "source_tier": "B",
        "raw_formula": "GC=F adjusted close from yfinance.",
        "stress_direction": "higher_is_safe_haven_or_inflation_hedge_stress",
        "absolute_threshold": "normal=1900, crisis=3000",
        "known_limitations": "Gold can rise on inflation, real rates, central-bank demand or crisis hedging; not a standalone crisis signal.",
        "upgrade_plan": "Add real yields, ETF flows, central-bank demand and USD regime context.",
    },
    "natgas": {
        "source_tier": "B",
        "raw_formula": "NG=F adjusted close from yfinance.",
        "stress_direction": "higher_is_energy_cost_stress",
        "absolute_threshold": "not yet defined",
        "known_limitations": "US Henry Hub proxy misses European/Asian gas stress and storage constraints.",
        "upgrade_plan": "Add TTF/J-Korea Marker gas prices and storage data.",
    },
    "wheat": {
        "source_tier": "B",
        "raw_formula": "ZW=F adjusted close from yfinance.",
        "stress_direction": "higher_is_food_security_inflation_stress",
        "absolute_threshold": "not yet defined",
        "known_limitations": "Front-month futures can be weather/supply specific and not broad food inflation.",
        "upgrade_plan": "Add FAO food index, inventories and regional grain export stress.",
    },
    "bdry": {
        "source_tier": "B",
        "raw_formula": "BDRY adjusted close from yfinance.",
        "stress_direction": "context_dependent_shipping_cost_or_trade_volume_proxy",
        "absolute_threshold": "not yet defined",
        "known_limitations": "ETF proxy is affected by futures roll and freight market structure.",
        "upgrade_plan": "Add Baltic Dry Index and container freight indices directly.",
    },
    "dram_spot": {
        "source_tier": "C",
        "raw_formula": "Equal-weight normalized basket of MU, 005930.KS, and 000660.KS adjusted closes from yfinance.",
        "stress_direction": "higher_can_indicate_memory_cycle_heat; lower_can_indicate_dram_cycle_downturn",
        "absolute_threshold": "not yet defined",
        "known_limitations": "Equity basket is not DRAM spot/contract price; it mixes memory pricing, equity valuation, FX, and company-specific factors.",
        "upgrade_plan": "Replace with DRAMeXchange/TrendForce spot and contract prices.",
    },
    "nand_spot": {
        "source_tier": "C",
        "raw_formula": "Equal-weight normalized basket of WDC, STX, MU, and 005930.KS adjusted closes from yfinance.",
        "stress_direction": "higher_can_indicate_storage_cycle_heat; lower_can_indicate_nand_storage_downturn",
        "absolute_threshold": "not yet defined",
        "known_limitations": "Equity basket is not NAND flash spot/contract price; storage-cycle equities can be affected by non-NAND earnings and valuation factors.",
        "upgrade_plan": "Replace with NAND spot/contract prices from memory-market data provider.",
    },
    "ai_capex": {
        "source_tier": "C",
        "raw_formula": "Equal-weight normalized basket of CLOU, SMH, MSFT, AMZN, GOOGL, META, and NVDA adjusted closes from yfinance.",
        "stress_direction": "higher_can_indicate_crowding_or_capex_cycle_heat",
        "absolute_threshold": "not yet defined",
        "known_limitations": "Equity basket is not actual hyperscaler capex; sentiment, valuation, and earnings expectations contaminate the signal.",
        "upgrade_plan": "Use company filings for capex guidance and aggregate hyperscaler capex data.",
    },
    "btc": {
        "source_tier": "B",
        "raw_formula": "BTC-USD adjusted close from yfinance.",
        "stress_direction": "lower_is_risk_off; extreme_high_can_indicate_speculation",
        "absolute_threshold": "normal=60000, crisis=20000",
        "known_limitations": "Crypto-specific liquidity and regulatory events can dominate macro signal.",
        "upgrade_plan": "Add stablecoin flows, crypto credit stress, and cross-asset risk appetite confirmation.",
    },
    "kr_ca": {
        "source_tier": "A",
        "raw_formula": "FRED KORB6BLTT02STSAQ latest observation and history; Korea current account balance as percent of GDP.",
        "stress_direction": "lower_current_account_balance_is_worse",
        "absolute_threshold": "normal=4.0, crisis=-3.0",
        "known_limitations": "Quarterly macro series updates slowly and may lag market FX pressure.",
        "upgrade_plan": "Add Bank of Korea monthly current account value, export growth, semiconductor exports, and FX reserve change.",
    },
}

def build_node_data_dictionary() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for node_id, node in CORE_NODES.items():
        override = NODE_DATA_OVERRIDES.get(node_id, {})
        result[node_id] = {
            "node_id": node_id,
            "display_name": node.display_name,
            "economic_meaning": node.description,
            "asset_class": node.asset_class.value,
            "geography": node.geography,
            "declared_data_source": node.data_source,
            "update_frequency": node.update_frequency,
            "unit": node.unit,
            "source_tier": override.get("source_tier", "B" if node.data_source == "yfinance" else "D"),
            "raw_formula": override.get("raw_formula", "Direct latest value from declared data source."),
            "stress_direction": override.get("stress_direction", "see model configuration"),
            "absolute_threshold": override.get("absolute_threshold", "not yet defined"),
            "known_limitations": override.get("known_limitations", "Requires formal review."),
            "upgrade_plan": override.get("upgrade_plan", "Document source quality and add replacement plan."),
        }
    return result


NODE_DATA_DICTIONARY = build_node_data_dictionary()
