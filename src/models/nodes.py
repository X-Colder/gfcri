"""
Causal graph node definitions for macro risk analysis.

Defines node types, asset classes, and the canonical set of observable/latent
variables that participate in the global macro causal network.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class NodeType(str, Enum):
    """Ontological role of a node in the causal graph."""

    OBSERVABLE = "OBSERVABLE"
    """Directly measurable market or macro variable."""

    LATENT = "LATENT"
    """Unobservable latent factor inferred from observables."""

    INTERVENTION = "INTERVENTION"
    """Policy or deliberate action that exogenously shifts the system."""

    EXTERNAL_SHOCK = "EXTERNAL_SHOCK"
    """Idiosyncratic shock with no endogenous parent in this graph."""

    STRUCTURAL = "STRUCTURAL"
    """Slow-moving structural variable (e.g. long-run productivity)."""


class AssetClass(str, Enum):
    """Broad asset-class categorization for a node."""

    FX = "FX"
    RATES = "RATES"
    EQUITY = "EQUITY"
    CREDIT = "CREDIT"
    COMMODITY = "COMMODITY"
    MACRO = "MACRO"
    SENTIMENT = "SENTIMENT"


# ---------------------------------------------------------------------------
# Node dataclass
# ---------------------------------------------------------------------------


@dataclass
class CausalNode:
    """A single node (variable) in the macro-risk causal graph.

    Parameters
    ----------
    node_id:
        Unique snake_case identifier used throughout the graph (e.g. ``dxy``).
    display_name:
        Human-readable label shown in dashboards (e.g. ``"DXY Index"``).
    description:
        One-sentence description of what the variable measures.
    node_type:
        Ontological category from :class:`NodeType`.
    asset_class:
        Broad asset class from :class:`AssetClass`.
    geography:
        ISO country / region tag (e.g. ``"US"``, ``"KR"``, ``"GLOBAL"``).
    data_source:
        Primary data feed (e.g. ``"Bloomberg"``, ``"Fed"``, ``"KOFR"``).
    update_frequency:
        Cadence of updates (``"daily"``, ``"weekly"``, ``"monthly"``).
    unit:
        Unit string for display (e.g. ``"%"``, ``"bps"``, ``"index"``).
    current_value:
        Most recent observed value; ``None`` until populated at runtime.
    value_zscore:
        Z-score of *current_value* relative to historical distribution.
    historical_mean:
        Long-run mean used for z-score normalisation.
    historical_std:
        Long-run standard deviation used for z-score normalisation.
    is_anomalous:
        ``True`` when ``|value_zscore| > anomaly_threshold`` (set externally).
    anomaly_score:
        Continuous anomaly score in [0, 1] (higher = more anomalous).
    last_updated:
        Timestamp of the last value update.
    """

    node_id: str
    display_name: str
    description: str
    node_type: NodeType
    asset_class: AssetClass
    geography: str = "GLOBAL"
    data_source: str = "Bloomberg"
    update_frequency: str = "daily"
    unit: str = "index"

    # Runtime state (populated by data pipeline)
    current_value: Optional[float] = field(default=None, compare=False)
    value_zscore: Optional[float] = field(default=None, compare=False)
    historical_mean: Optional[float] = field(default=None, compare=False)
    historical_std: Optional[float] = field(default=None, compare=False)
    is_anomalous: bool = field(default=False, compare=False)
    anomaly_score: float = field(default=0.0, compare=False)
    last_updated: Optional[datetime] = field(default=None, compare=False)

    def __post_init__(self) -> None:
        # Coerce string inputs coming from JSON/config
        if isinstance(self.node_type, str):
            self.node_type = NodeType(self.node_type)
        if isinstance(self.asset_class, str):
            self.asset_class = AssetClass(self.asset_class)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def is_stale(self) -> bool:
        """Return ``True`` if ``last_updated`` is more than 2 days ago."""
        if self.last_updated is None:
            return True
        delta = datetime.utcnow() - self.last_updated
        return delta.days > 2

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary (datetime converted to ISO string)."""
        return {
            "node_id": self.node_id,
            "display_name": self.display_name,
            "description": self.description,
            "node_type": self.node_type.value,
            "asset_class": self.asset_class.value,
            "geography": self.geography,
            "data_source": self.data_source,
            "update_frequency": self.update_frequency,
            "unit": self.unit,
            "current_value": self.current_value,
            "value_zscore": self.value_zscore,
            "historical_mean": self.historical_mean,
            "historical_std": self.historical_std,
            "is_anomalous": self.is_anomalous,
            "anomaly_score": self.anomaly_score,
            "last_updated": (
                self.last_updated.isoformat() if self.last_updated else None
            ),
        }


# ---------------------------------------------------------------------------
# Canonical node registry
# ---------------------------------------------------------------------------

CORE_NODES: dict[str, CausalNode] = {
    # ---- US Rates & Fed Policy ----------------------------------------
    "fed_funds": CausalNode(
        node_id="fed_funds",
        display_name="Fed Funds Rate",
        description="US Federal Reserve effective overnight lending rate.",
        node_type=NodeType.INTERVENTION,
        asset_class=AssetClass.RATES,
        geography="US",
        data_source="Federal Reserve",
        update_frequency="meeting",  # ~8x per year
        unit="%",
    ),
    "ust_10y": CausalNode(
        node_id="ust_10y",
        display_name="US 10Y Treasury Yield",
        description="10-year US Treasury benchmark yield (market-driven term rate).",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.RATES,
        geography="US",
        data_source="FRED",
        update_frequency="daily",
        unit="%",
    ),
    "ust_2y": CausalNode(
        node_id="ust_2y",
        display_name="US 2Y Treasury Yield",
        description="2-year US Treasury yield; sensitive to near-term Fed expectations.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.RATES,
        geography="US",
        data_source="FRED",
        update_frequency="daily",
        unit="%",
    ),
    # ---- Global Liquidity & Dollar ------------------------------------
    "global_liqd": CausalNode(
        node_id="global_liqd",
        display_name="Fed Balance Sheet Liquidity Proxy",
        description="Federal Reserve total assets; official proxy for US dollar liquidity conditions.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.MACRO,
        geography="US",
        data_source="FRED",
        update_frequency="weekly",
        unit="USD mn",
    ),
    "dxy": CausalNode(
        node_id="dxy",
        display_name="DXY Index",
        description="US Dollar Index measuring USD strength against a basket of six major currencies.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.FX,
        geography="US",
        data_source="Bloomberg",
        update_frequency="daily",
        unit="index",
    ),
    # ---- Risk Sentiment -----------------------------------------------
    "vix": CausalNode(
        node_id="vix",
        display_name="VIX Index",
        description="CBOE Volatility Index; measures expected 30-day S&P 500 volatility.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.SENTIMENT,
        geography="US",
        data_source="CBOE",
        update_frequency="daily",
        unit="index",
    ),
    "us_recession_prob": CausalNode(
        node_id="us_recession_prob",
        display_name="US Recession Probability",
        description="FRED smoothed US recession probability series.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.MACRO,
        geography="US",
        data_source="FRED",
        update_frequency="monthly",
        unit="%",
    ),
    # ---- Korean FX & Equity ------------------------------------------
    "krw_usd": CausalNode(
        node_id="krw_usd",
        display_name="KRW/USD Exchange Rate",
        description="Korean Won per US Dollar spot rate.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.FX,
        geography="KR",
        data_source="Bloomberg",
        update_frequency="daily",
        unit="KRW/USD",
    ),
    "kospi": CausalNode(
        node_id="kospi",
        display_name="KOSPI Index",
        description="Korea Composite Stock Price Index (benchmark Korean equity index).",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.EQUITY,
        geography="KR",
        data_source="KRX",
        update_frequency="daily",
        unit="index",
    ),
    # ---- Korean Credit -----------------------------------------------
    "kr_cds_5y": CausalNode(
        node_id="kr_cds_5y",
        display_name="Korea Credit Stress Proxy (EWY Inverted)",
        description="Inverse South Korea ETF proxy used until actual Korea sovereign CDS data is available.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.CREDIT,
        geography="KR",
        data_source="yfinance",
        update_frequency="daily",
        unit="inverted USD",
    ),
    "kr_ca": CausalNode(
        node_id="kr_ca",
        display_name="Korea Current Account Balance / GDP",
        description="South Korea current account balance as a share of GDP.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.MACRO,
        geography="KR",
        data_source="FRED / OECD",
        update_frequency="quarterly",
        unit="% GDP",
    ),
    # ---- Semiconductor / Tech ----------------------------------------
    "sox": CausalNode(
        node_id="sox",
        display_name="Philadelphia Semiconductor Index (SOX)",
        description="US semiconductor sector equity index.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.EQUITY,
        geography="US",
        data_source="PHLX",
        update_frequency="daily",
        unit="index",
    ),
    "dram_spot": CausalNode(
        node_id="dram_spot",
        display_name="DRAM Producer Basket Proxy",
        description="Equal-weight memory-producer equity basket used until direct DRAM spot/contract prices are available.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.EQUITY,
        geography="GLOBAL",
        data_source="yfinance",
        update_frequency="daily",
        unit="USD",
    ),
    "nand_spot": CausalNode(
        node_id="nand_spot",
        display_name="NAND/Storage Producer Basket Proxy",
        description="Equal-weight NAND/storage producer equity basket used until direct NAND spot/contract prices are available.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.EQUITY,
        geography="GLOBAL",
        data_source="yfinance",
        update_frequency="daily",
        unit="USD",
    ),
    # ---- AI / Cloud Capex -------------------------------------------
    "ai_capex": CausalNode(
        node_id="ai_capex",
        display_name="AI/Cloud Capex Basket Proxy",
        description="Equal-weight AI/cloud equity basket proxy for capex-cycle heat until company-filing aggregation is available.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.EQUITY,
        geography="US",
        data_source="yfinance",
        update_frequency="daily",
        unit="USD",
    ),
    "orcl_cds": CausalNode(
        node_id="orcl_cds",
        display_name="AI/Cloud Credit Stress Proxy (Equity Basket Inverted)",
        description="Inverse AI/cloud equity basket proxy used until actual cloud/AI credit spread or CDS data is available.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.CREDIT,
        geography="US",
        data_source="yfinance",
        update_frequency="daily",
        unit="inverted index",
    ),
    # ---- Commodities -------------------------------------------------
    "oil_wti": CausalNode(
        node_id="oil_wti",
        display_name="WTI Crude Oil Price",
        description="West Texas Intermediate crude oil front-month futures price.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.COMMODITY,
        geography="GLOBAL",
        data_source="CME",
        update_frequency="daily",
        unit="USD/bbl",
    ),
    # ---- Credit Stress -----------------------------------------------
    "hyg": CausalNode(
        node_id="hyg",
        display_name="High Yield Corporate Bond ETF",
        description="iShares iBoxx USD High Yield Corporate Bond ETF; proxy for junk bond credit stress.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.CREDIT,
        geography="US",
        data_source="yfinance",
        update_frequency="daily",
        unit="USD",
    ),
    # ---- Banking System -----------------------------------------------
    "kre": CausalNode(
        node_id="kre",
        display_name="Regional Bank ETF (KRE)",
        description="SPDR S&P Regional Banking ETF; monitors US regional bank health.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.EQUITY,
        geography="US",
        data_source="yfinance",
        update_frequency="daily",
        unit="USD",
    ),
    # ---- Real Estate ---------------------------------------------------
    "vnq": CausalNode(
        node_id="vnq",
        display_name="Real Estate ETF (VNQ)",
        description="Vanguard Real Estate ETF; tracks US REIT and property market.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.EQUITY,
        geography="US",
        data_source="yfinance",
        update_frequency="daily",
        unit="USD",
    ),
    # ---- Consumer Health -----------------------------------------------
    "consumer_stress": CausalNode(
        node_id="consumer_stress",
        display_name="Consumer Stress Ratio (XLY/XLP)",
        description="Ratio of Consumer Discretionary to Staples ETF; falling ratio signals consumer distress.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.SENTIMENT,
        geography="US",
        data_source="yfinance (computed)",
        update_frequency="daily",
        unit="ratio",
    ),
    # ---- Industrial / Real Economy ------------------------------------
    "copper": CausalNode(
        node_id="copper",
        display_name="Copper Futures",
        description="CME copper front-month futures; 'Dr. Copper' is a real-time GDP proxy.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.COMMODITY,
        geography="GLOBAL",
        data_source="yfinance",
        update_frequency="daily",
        unit="USD/lb",
    ),
    # ---- Safe Haven ---------------------------------------------------
    "gold": CausalNode(
        node_id="gold",
        display_name="Gold Futures",
        description="CME gold front-month futures; classic safe-haven and inflation hedge.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.COMMODITY,
        geography="GLOBAL",
        data_source="yfinance",
        update_frequency="daily",
        unit="USD/oz",
    ),
    # ---- Eurozone ----------------------------------------------------
    "eurusd": CausalNode(node_id="eurusd", display_name="EUR/USD Exchange Rate", description="Euro to US Dollar exchange rate.", node_type=NodeType.OBSERVABLE, asset_class=AssetClass.FX, geography="EU", data_source="yfinance", update_frequency="daily", unit="EUR/USD"),
    "stoxx50": CausalNode(node_id="stoxx50", display_name="Euro Stoxx 50", description="Eurozone blue-chip equity index.", node_type=NodeType.OBSERVABLE, asset_class=AssetClass.EQUITY, geography="EU", data_source="yfinance", update_frequency="daily", unit="index"),
    "italy_etf": CausalNode(node_id="italy_etf", display_name="Italy ETF (EWI)", description="iShares MSCI Italy ETF; proxy for Italian sovereign stress.", node_type=NodeType.OBSERVABLE, asset_class=AssetClass.EQUITY, geography="EU", data_source="yfinance", update_frequency="daily", unit="USD"),
    # ---- China -------------------------------------------------------
    "cny_usd": CausalNode(node_id="cny_usd", display_name="USD/CNY Exchange Rate", description="US Dollar to Chinese Yuan exchange rate.", node_type=NodeType.OBSERVABLE, asset_class=AssetClass.FX, geography="CN", data_source="yfinance", update_frequency="daily", unit="USD/CNY"),
    "hsi": CausalNode(node_id="hsi", display_name="Hang Seng Index", description="Hong Kong Hang Seng Index; offshore Chinese equity benchmark.", node_type=NodeType.OBSERVABLE, asset_class=AssetClass.EQUITY, geography="CN", data_source="yfinance", update_frequency="daily", unit="index"),
    # ---- Japan -------------------------------------------------------
    "jpy_usd": CausalNode(node_id="jpy_usd", display_name="USD/JPY Exchange Rate", description="US Dollar to Japanese Yen exchange rate.", node_type=NodeType.OBSERVABLE, asset_class=AssetClass.FX, geography="JP", data_source="yfinance", update_frequency="daily", unit="USD/JPY"),
    "nikkei": CausalNode(node_id="nikkei", display_name="Nikkei 225", description="Japan Nikkei 225 equity index.", node_type=NodeType.OBSERVABLE, asset_class=AssetClass.EQUITY, geography="JP", data_source="yfinance", update_frequency="daily", unit="index"),
    # ---- Emerging Markets --------------------------------------------
    "eem": CausalNode(node_id="eem", display_name="EM Equity ETF", description="iShares MSCI Emerging Markets ETF.", node_type=NodeType.OBSERVABLE, asset_class=AssetClass.EQUITY, geography="GLOBAL", data_source="yfinance", update_frequency="daily", unit="USD"),
    "emb": CausalNode(node_id="emb", display_name="EM Bond ETF", description="iShares JP Morgan USD EM Bond ETF; EM sovereign credit risk.", node_type=NodeType.OBSERVABLE, asset_class=AssetClass.CREDIT, geography="GLOBAL", data_source="yfinance", update_frequency="daily", unit="USD"),
    # ---- Crypto & US Equity ------------------------------------------
    "btc": CausalNode(node_id="btc", display_name="Bitcoin", description="Bitcoin price in USD; risk appetite barometer since 2020.", node_type=NodeType.OBSERVABLE, asset_class=AssetClass.SENTIMENT, geography="GLOBAL", data_source="yfinance", update_frequency="daily", unit="USD"),
    "spx": CausalNode(node_id="spx", display_name="S&P 500", description="US S&P 500 equity index.", node_type=NodeType.OBSERVABLE, asset_class=AssetClass.EQUITY, geography="US", data_source="yfinance", update_frequency="daily", unit="index"),
    "lqd": CausalNode(node_id="lqd", display_name="Investment Grade Bond ETF", description="iShares iBoxx USD Investment Grade Corporate Bond ETF.", node_type=NodeType.OBSERVABLE, asset_class=AssetClass.CREDIT, geography="US", data_source="yfinance", update_frequency="daily", unit="USD"),
    "fred_hy_spread": CausalNode(
        node_id="fred_hy_spread",
        display_name="US High Yield OAS",
        description="ICE BofA US High Yield Index option-adjusted spread from FRED; direct market-implied high-yield credit stress.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.CREDIT,
        geography="US",
        data_source="FRED / ICE BofA",
        update_frequency="daily",
        unit="%",
    ),
    "fred_bbb_spread": CausalNode(
        node_id="fred_bbb_spread",
        display_name="US BBB Corporate OAS",
        description="ICE BofA BBB US Corporate Index option-adjusted spread from FRED; direct investment-grade downgrade/default pressure.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.CREDIT,
        geography="US",
        data_source="FRED / ICE BofA",
        update_frequency="daily",
        unit="%",
    ),
    "fred_ic_spread": CausalNode(
        node_id="fred_ic_spread",
        display_name="US AAA Corporate Yield",
        description="ICE BofA AAA US Corporate Index effective yield from FRED; high-quality corporate funding-cost anchor.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.CREDIT,
        geography="US",
        data_source="FRED / ICE BofA",
        update_frequency="daily",
        unit="%",
    ),
    "fred_euro_hy_spread": CausalNode(
        node_id="fred_euro_hy_spread",
        display_name="Euro High Yield OAS",
        description="ICE BofA Euro High Yield Index option-adjusted spread from FRED; direct European high-yield credit stress.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.CREDIT,
        geography="EU",
        data_source="FRED / ICE BofA",
        update_frequency="daily",
        unit="%",
    ),
    "fred_sofr": CausalNode(
        node_id="fred_sofr",
        display_name="SOFR",
        description="Secured Overnight Financing Rate from FRED; core US repo funding rate.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.RATES,
        geography="US",
        data_source="FRED",
        update_frequency="daily",
        unit="%",
    ),
    "sofr_effr_spread": CausalNode(
        node_id="sofr_effr_spread",
        display_name="SOFR - EFFR Spread",
        description="Spread between SOFR and effective fed funds rate in basis points; proxy for repo/overnight funding pressure.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.CREDIT,
        geography="US",
        data_source="FRED computed",
        update_frequency="daily",
        unit="bps",
    ),
    "fred_all_loan_delinquency": CausalNode(
        node_id="fred_all_loan_delinquency",
        display_name="US Bank Loan Delinquency Rate",
        description="Delinquency rate on all loans and leases at US commercial banks from FRED; realized credit damage proxy.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.CREDIT,
        geography="US",
        data_source="FRED",
        update_frequency="quarterly",
        unit="%",
    ),
    "fred_baa10y_spread": CausalNode(
        node_id="fred_baa10y_spread",
        display_name="Moody's Baa - 10Y Treasury Spread",
        description="Moody's seasoned Baa corporate bond yield minus 10-year Treasury yield from FRED; downgrade/default pricing proxy.",
        node_type=NodeType.OBSERVABLE,
        asset_class=AssetClass.CREDIT,
        geography="US",
        data_source="FRED",
        update_frequency="daily",
        unit="%",
    ),
    # ---- Commodities (additional) ------------------------------------
    "natgas": CausalNode(node_id="natgas", display_name="Natural Gas Futures", description="Henry Hub natural gas front-month futures.", node_type=NodeType.OBSERVABLE, asset_class=AssetClass.COMMODITY, geography="GLOBAL", data_source="yfinance", update_frequency="daily", unit="USD/MMBtu"),
    "wheat": CausalNode(node_id="wheat", display_name="Wheat Futures", description="CBOT wheat front-month futures; food security indicator.", node_type=NodeType.OBSERVABLE, asset_class=AssetClass.COMMODITY, geography="GLOBAL", data_source="yfinance", update_frequency="daily", unit="cents/bu"),
    "bdry": CausalNode(node_id="bdry", display_name="Shipping ETF (BDRY)", description="Breakwave Dry Bulk Shipping ETF; global trade volume proxy.", node_type=NodeType.OBSERVABLE, asset_class=AssetClass.MACRO, geography="GLOBAL", data_source="yfinance", update_frequency="daily", unit="USD"),
}
