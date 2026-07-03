"""Stress-direction helpers for z-score based pressure scoring."""

from __future__ import annotations


HIGH_IS_WORSE = {
    "fed_funds",
    "ust_10y",
    "ust_2y",
    "dxy",
    "vix",
    "krw_usd",
    "jpy_usd",
    "oil_wti",
    "gold",
    "natgas",
    "wheat",
    "fred_hy_spread",
    "fred_bbb_spread",
    "fred_ic_spread",
    "fred_euro_hy_spread",
    "fred_sofr",
    "sofr_effr_spread",
    "fred_all_loan_delinquency",
    "fred_baa10y_spread",
    "us_recession_prob",
    "kr_cds_5y",
    "orcl_cds",
    "ai_capex",
    "dram_spot",
    "nand_spot",
}

LOW_IS_WORSE = {
    "hyg",
    "lqd",
    "spx",
    "kospi",
    "hsi",
    "eurusd",
    "kr_ca",
    "kre",
    "vnq",
    "sox",
    "stoxx50",
    "copper",
    "eem",
    "emb",
    "btc",
    "consumer_stress",
    "global_liqd",
}

TWO_SIDED = {
    "bdry",
}


def stress_direction_for_node(node_id: str) -> str:
    if node_id in HIGH_IS_WORSE:
        return "high"
    if node_id in LOW_IS_WORSE:
        return "low"
    if node_id in TWO_SIDED:
        return "two_sided"
    return "two_sided"


def stress_score_from_zscore(node_id: str, zscore: float | None) -> float:
    z = float(zscore or 0.0)
    direction = stress_direction_for_node(node_id)
    if direction == "high":
        pressure_z = max(0.0, z)
    elif direction == "low":
        pressure_z = max(0.0, -z)
    else:
        pressure_z = abs(z)
    return min(1.0, pressure_z / 4.0)

