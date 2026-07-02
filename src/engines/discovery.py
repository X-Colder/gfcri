"""
Causal discovery engine (simplified).

Validates existing graph edges with Granger causality tests, detects
structural breaks via rolling-window regression, and proposes new edge
candidates from data-driven correlation / Granger screening.

Hard dependencies: statsmodels (Granger tests), numpy, pandas, scipy.
The ``ruptures`` library is used when available for more accurate
structural break detection; if absent the engine falls back to a
rolling-standard-deviation approach.
"""

from __future__ import annotations

import warnings as _warnings
from typing import Any, TYPE_CHECKING

import numpy as np
import pandas as pd
from loguru import logger
from scipy import stats
from statsmodels.tsa.stattools import grangercausalitytests

if TYPE_CHECKING:
    from src.models.graph import MacroRiskCausalGraph

# Optional dependency: ruptures
try:
    import ruptures as rpt  # type: ignore

    _RUPTURES_AVAILABLE = True
except ImportError:
    _RUPTURES_AVAILABLE = False
    logger.info(
        "ruptures library not installed; "
        "structural break detection will use rolling-window fallback"
    )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Maximum Granger test lag to evaluate (in trading days).
_GRANGER_MAX_LAG = 10

# Number of observations required to run Granger tests reliably.
_MIN_OBS_GRANGER = 60

# Rolling window size for structural break detection (trading days).
_BREAK_WINDOW = 60

# Minimum significance level for Granger test to flag a relationship.
_GRANGER_P_THRESHOLD = 0.05

# Minimum |correlation| to consider a data-driven edge candidate.
_CORR_CANDIDATE_THRESHOLD = 0.40


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_stationary(series: pd.Series) -> pd.Series:
    """Return first-differenced series to reduce non-stationarity."""
    return series.diff().dropna()


def _safe_granger(
    data_xy: pd.DataFrame, max_lag: int = _GRANGER_MAX_LAG
) -> dict[int, float]:
    """Run Granger causality test and return {lag: p_value} dict.

    Args:
        data_xy: Two-column DataFrame [Y, X] (statsmodels convention: Y first).
        max_lag: Maximum number of lags to test.

    Returns:
        Dict mapping lag → minimum p-value across the four test statistics.
        Returns empty dict on failure.
    """
    result: dict[int, float] = {}
    try:
        with _warnings.catch_warnings():
            _warnings.simplefilter("ignore")
            gc_res = grangercausalitytests(data_xy, maxlag=max_lag, verbose=False)
        for lag, test_dict in gc_res.items():
            test_results = test_dict[0]
            p_values = [test_results[k][1] for k in ("ssr_ftest", "ssr_chi2test", "lrtest", "params_ftest")]
            result[lag] = float(min(p_values))
    except Exception as exc:
        logger.warning(f"Granger test failed: {exc}")
    return result


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------


class CausalDiscoveryEngine:
    """Simplified causal discovery engine for macro-risk graph maintenance.

    Responsibilities:
    - Validate whether existing edges still exhibit Granger causality.
    - Detect structural breaks (regime changes) in edge coefficients.
    - Propose new candidate edges from data-driven screening.

    Args:
        causal_graph: MacroRiskCausalGraph instance providing the graph topology.
        historical_data: DataFrame with one column per node_id (daily frequency,
            descending or ascending date index).
    """

    def __init__(
        self,
        causal_graph: "MacroRiskCausalGraph",
        historical_data: pd.DataFrame,
    ) -> None:
        self.graph = causal_graph
        self.data = historical_data.sort_index().copy()

    # ------------------------------------------------------------------
    # 1. Validate existing edges with Granger causality tests
    # ------------------------------------------------------------------

    def validate_existing_edges(self, lookback_days: int = 252) -> list[dict[str, Any]]:
        """Run Granger causality tests on every active edge in the graph.

        For each edge (source → target), the test asks: "does knowing the
        history of `source` help predict `target` beyond the target's own
        history?"  We use first-differenced series to improve stationarity.

        Args:
            lookback_days: Number of most-recent trading days to include.

        Returns:
            List of dicts, one per edge, with keys:
                ``edge_id``, ``source``, ``target``,
                ``granger_significant`` (bool),
                ``best_lag`` (int), ``best_p_value`` (float),
                ``all_lag_p_values`` (dict),
                ``validation_note`` (str).
        """
        results: list[dict[str, Any]] = []
        subset = self.data.iloc[-lookback_days:] if lookback_days < len(self.data) else self.data

        for edge_id, edge in self.graph.edges.items():
            if edge.is_deprecated:
                continue

            src, tgt = edge.source_node, edge.target_node
            if src not in subset.columns or tgt not in subset.columns:
                results.append(
                    {
                        "edge_id": edge_id,
                        "source": src,
                        "target": tgt,
                        "granger_significant": None,
                        "best_lag": None,
                        "best_p_value": None,
                        "all_lag_p_values": {},
                        "validation_note": "One or both columns missing from historical data",
                    }
                )
                continue

            src_series = _ensure_stationary(subset[src])
            tgt_series = _ensure_stationary(subset[tgt])
            aligned = pd.concat([tgt_series, src_series], axis=1).dropna()
            aligned.columns = ["Y", "X"]

            if len(aligned) < _MIN_OBS_GRANGER:
                results.append(
                    {
                        "edge_id": edge_id,
                        "source": src,
                        "target": tgt,
                        "granger_significant": None,
                        "best_lag": None,
                        "best_p_value": None,
                        "all_lag_p_values": {},
                        "validation_note": (
                            f"Insufficient observations ({len(aligned)} < {_MIN_OBS_GRANGER})"
                        ),
                    }
                )
                continue

            max_lag = min(_GRANGER_MAX_LAG, max(1, edge.max_lag_days))
            lag_p = _safe_granger(aligned, max_lag=max_lag)

            if not lag_p:
                results.append(
                    {
                        "edge_id": edge_id,
                        "source": src,
                        "target": tgt,
                        "granger_significant": False,
                        "best_lag": None,
                        "best_p_value": None,
                        "all_lag_p_values": {},
                        "validation_note": "Granger test returned no results",
                    }
                )
                continue

            best_lag = min(lag_p, key=lag_p.get)  # type: ignore[arg-type]
            best_p = lag_p[best_lag]
            significant = best_p < _GRANGER_P_THRESHOLD

            note = (
                f"Granger test significant at lag={best_lag}d (p={best_p:.4f})."
                if significant
                else f"No Granger causality detected (best p={best_p:.4f} at lag={best_lag}d)."
            )
            if not significant and edge.strength_confidence > 0.7:
                note += " Consider reviewing edge confidence score."

            results.append(
                {
                    "edge_id": edge_id,
                    "source": src,
                    "target": tgt,
                    "granger_significant": significant,
                    "best_lag": best_lag,
                    "best_p_value": round(best_p, 6),
                    "all_lag_p_values": {k: round(v, 6) for k, v in lag_p.items()},
                    "validation_note": note,
                }
            )
            logger.debug(f"Validated edge {edge_id}: significant={significant}, p={best_p:.4f}")

        logger.info(
            f"validate_existing_edges: tested {len(results)} edges, "
            f"significant={sum(1 for r in results if r.get('granger_significant'))}"
        )
        return results

    # ------------------------------------------------------------------
    # 2. Structural break detection
    # ------------------------------------------------------------------

    def detect_structural_breaks(self) -> list[dict[str, Any]]:
        """Detect structural breaks in active edge relationships.

        For each active edge the method fits a rolling OLS regression of
        target on source and monitors the rolling beta coefficient.  A
        large standard deviation of the rolling beta (relative to its
        mean absolute value) signals a structural break.

        If the ``ruptures`` library is available it is used to pinpoint
        the exact break date via PELT change-point detection on the
        rolling beta series; otherwise the date of maximum beta deviation
        is returned.

        Returns:
            List of dicts, one per edge with a potential break, with keys:
                ``edge_id``, ``source``, ``target``,
                ``break_detected`` (bool),
                ``break_date`` (str | None),
                ``instability_ratio`` (float) — std / mean_abs_beta,
                ``rolling_beta_stats`` (dict),
                ``method`` (str),
                ``note`` (str).
        """
        results: list[dict[str, Any]] = []

        for edge_id, edge in self.graph.edges.items():
            if edge.is_deprecated:
                continue

            src, tgt = edge.source_node, edge.target_node
            if src not in self.data.columns or tgt not in self.data.columns:
                continue

            lag = max(0, edge.peak_lag_days)
            x = self.data[src].shift(lag)
            y = self.data[tgt]
            df = pd.concat([x.rename("X"), y.rename("Y")], axis=1).dropna()

            if len(df) < _BREAK_WINDOW * 2:
                continue

            # Rolling OLS beta.
            rolling_betas: list[float] = []
            dates: list[Any] = []
            window = _BREAK_WINDOW

            for start in range(0, len(df) - window, window // 2):
                chunk = df.iloc[start : start + window]
                x_c = chunk["X"].values.reshape(-1, 1)
                y_c = chunk["Y"].values
                from sklearn.linear_model import LinearRegression

                reg = LinearRegression(fit_intercept=True).fit(x_c, y_c)
                rolling_betas.append(float(reg.coef_[0]))
                dates.append(df.index[start + window - 1])

            if len(rolling_betas) < 4:
                continue

            beta_arr = np.array(rolling_betas)
            beta_std = float(np.std(beta_arr))
            beta_mean_abs = float(np.mean(np.abs(beta_arr))) + 1e-9
            instability_ratio = beta_std / beta_mean_abs

            break_detected = instability_ratio > 0.5
            break_date: str | None = None
            method_used = "rolling_std"

            if break_detected:
                if _RUPTURES_AVAILABLE and len(beta_arr) >= 6:
                    try:
                        algo = rpt.Pelt(model="rbf").fit(beta_arr)
                        change_points = algo.predict(pen=1.0)
                        if change_points and change_points[0] < len(dates):
                            break_date = str(dates[min(change_points[0], len(dates) - 1)])
                            method_used = "ruptures_PELT"
                    except Exception as exc:
                        logger.warning(f"ruptures failed for {edge_id}: {exc}")

                if break_date is None:
                    # Fallback: date where beta deviates most from overall mean.
                    idx_max = int(np.argmax(np.abs(beta_arr - beta_arr.mean())))
                    break_date = str(dates[idx_max])
                    method_used = "max_deviation"

            note = (
                f"Structural instability detected (ratio={instability_ratio:.2f}). "
                f"Estimated break: {break_date}."
                if break_detected
                else f"No structural break detected (instability ratio={instability_ratio:.2f})."
            )

            results.append(
                {
                    "edge_id": edge_id,
                    "source": src,
                    "target": tgt,
                    "break_detected": break_detected,
                    "break_date": break_date,
                    "instability_ratio": round(instability_ratio, 4),
                    "rolling_beta_stats": {
                        "mean": round(float(beta_arr.mean()), 4),
                        "std": round(float(beta_std), 4),
                        "min": round(float(beta_arr.min()), 4),
                        "max": round(float(beta_arr.max()), 4),
                    },
                    "method": method_used,
                    "note": note,
                }
            )
            if break_detected:
                logger.info(
                    f"Structural break detected on edge {edge_id}: "
                    f"ratio={instability_ratio:.2f}, break_date={break_date}"
                )

        logger.info(
            f"detect_structural_breaks: analysed {len(results)} edges, "
            f"breaks={sum(1 for r in results if r['break_detected'])}"
        )
        return results

    # ------------------------------------------------------------------
    # 3. Data-driven edge discovery
    # ------------------------------------------------------------------

    def discover_new_edges(self, max_new: int = 5) -> list[dict[str, Any]]:
        """Discover candidate new causal relationships from data.

        Strategy:
        1. Screen all node pairs with |Pearson r| > threshold.
        2. For shortlisted pairs, run Granger test on both directions.
        3. Remove pairs that already exist as graph edges.
        4. Rank by Granger p-value and return top `max_new` candidates.

        Args:
            max_new: Maximum number of new edge candidates to return.

        Returns:
            List of dicts, one per candidate edge, with keys:
                ``source``, ``target``,
                ``granger_p_value`` (float), ``granger_lag`` (int),
                ``pearson_r`` (float),
                ``already_in_graph`` (bool),
                ``recommendation`` (str).
        """
        available_cols = [
            c for c in self.data.columns if self.data[c].notna().sum() >= _MIN_OBS_GRANGER
        ]

        # Build set of existing (source, target) pairs.
        existing_pairs: set[tuple[str, str]] = {
            (e.source_node, e.target_node)
            for e in self.graph.edges.values()
            if not e.is_deprecated
        }

        # --- Phase 1: Pearson correlation screen ---
        candidates: list[dict[str, Any]] = []
        for i, col_a in enumerate(available_cols):
            for col_b in available_cols[i + 1 :]:
                if (col_a, col_b) in existing_pairs or (col_b, col_a) in existing_pairs:
                    continue
                try:
                    diff_a = _ensure_stationary(self.data[col_a])
                    diff_b = _ensure_stationary(self.data[col_b])
                    aligned = pd.concat([diff_a, diff_b], axis=1).dropna()
                    if len(aligned) < _MIN_OBS_GRANGER:
                        continue
                    r, p = stats.pearsonr(aligned.iloc[:, 0], aligned.iloc[:, 1])
                    if abs(r) >= _CORR_CANDIDATE_THRESHOLD:
                        candidates.append(
                            {"col_a": col_a, "col_b": col_b, "r": r, "corr_p": p}
                        )
                except Exception:
                    pass

        # --- Phase 2: Granger test on shortlisted pairs (both directions) ---
        granger_results: list[dict[str, Any]] = []
        for c in candidates:
            col_a, col_b = c["col_a"], c["col_b"]
            diff_a = _ensure_stationary(self.data[col_a])
            diff_b = _ensure_stationary(self.data[col_b])

            for src, tgt in [(col_a, col_b), (col_b, col_a)]:
                if (src, tgt) in existing_pairs:
                    continue
                src_s = diff_a if src == col_a else diff_b
                tgt_s = diff_b if tgt == col_b else diff_a
                aligned = pd.concat(
                    [tgt_s.rename("Y"), src_s.rename("X")], axis=1
                ).dropna()
                if len(aligned) < _MIN_OBS_GRANGER:
                    continue

                lag_p = _safe_granger(aligned, max_lag=5)
                if not lag_p:
                    continue
                best_lag = min(lag_p, key=lag_p.get)  # type: ignore[arg-type]
                best_p = lag_p[best_lag]
                if best_p < _GRANGER_P_THRESHOLD:
                    granger_results.append(
                        {
                            "source": src,
                            "target": tgt,
                            "granger_p_value": round(best_p, 6),
                            "granger_lag": best_lag,
                            "pearson_r": round(c["r"], 4),
                            "already_in_graph": False,
                            "recommendation": (
                                f"Consider adding edge {src} → {tgt} "
                                f"(Granger p={best_p:.4f} at lag={best_lag}d, "
                                f"Pearson r={c['r']:.3f}). "
                                "Verify economic mechanism before adding."
                            ),
                        }
                    )

        # Sort by Granger p-value ascending (most significant first).
        granger_results.sort(key=lambda x: x["granger_p_value"])
        top_results = granger_results[:max_new]

        logger.info(
            f"discover_new_edges: {len(candidates)} correlation candidates screened, "
            f"{len(granger_results)} Granger-significant, returning top {len(top_results)}"
        )
        return top_results
