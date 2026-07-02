"""
Causal reasoning engine (simplified).

Provides observational inference, interventional inference (do-calculus
via backdoor adjustment), path analysis, and confounding detection.

Dependencies: scipy, scikit-learn, numpy, pandas.
The module is deliberately kept free of the `dowhy` library so it can
run in constrained environments; the public API mirrors the interface
that a future `dowhy`-backed implementation would expose, making the
upgrade path straightforward.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import numpy as np
import pandas as pd
from loguru import logger
from scipy import stats
from sklearn.linear_model import LinearRegression

if TYPE_CHECKING:
    from src.models.graph import MacroRiskCausalGraph

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _align_series(
    df: pd.DataFrame, col_a: str, col_b: str, lag: int = 0
) -> tuple[pd.Series, pd.Series]:
    """Return two aligned series (X, Y), optionally shifting X back by `lag` days.

    Args:
        df: DataFrame with node columns.
        col_a: Source column name.
        col_b: Target column name.
        lag: Number of periods to lag the source (positive = source leads target).

    Returns:
        Tuple of (X, Y) pd.Series with NaNs dropped.
    """
    if col_a not in df.columns or col_b not in df.columns:
        raise KeyError(f"Columns {col_a!r} or {col_b!r} not found in DataFrame")
    x = df[col_a].shift(lag)
    y = df[col_b]
    valid = x.notna() & y.notna()
    return x[valid], y[valid]


def _ols_fit(
    X: np.ndarray, y: np.ndarray
) -> tuple[np.ndarray, float, float, np.ndarray]:
    """Fit OLS and return (coefficients, r_squared, p_value_f, residuals)."""
    reg = LinearRegression(fit_intercept=True)
    reg.fit(X, y)
    y_hat = reg.predict(X)
    residuals = y - y_hat
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # F-statistic p-value (overall fit significance)
    n, k = X.shape
    if n > k + 1 and ss_res > 0:
        f_stat = (ss_tot - ss_res) / k / (ss_res / (n - k - 1))
        p_f = float(1.0 - stats.f.cdf(f_stat, k, n - k - 1))
    else:
        p_f = 1.0

    return reg.coef_, r2, p_f, residuals


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------


class CausalReasoningEngine:
    """Simplified causal reasoning engine backed by linear regression and
    partial correlation techniques.

    This class intentionally does not use the `dowhy` library so that it
    runs without heavy optional dependencies.  The public method signatures
    are designed to be drop-in compatible with a future `dowhy`-backed
    implementation: each method returns a dictionary with the same keys
    (``point_estimate``, ``confidence``, ``natural_language_summary``,
    ``warnings``) so callers need not change.

    Args:
        causal_graph: An instance of MacroRiskCausalGraph supplying the
            graph topology (parents, paths, etc.).
        historical_data: DataFrame with one column per node_id, indexed
            by date (daily frequency).
    """

    def __init__(
        self,
        causal_graph: "MacroRiskCausalGraph",
        historical_data: pd.DataFrame,
    ) -> None:
        self.graph = causal_graph
        self.data = historical_data.copy()
        # Pre-compute z-score normalised data for regression stability.
        self._norm_data = (self.data - self.data.mean()) / self.data.std().replace(
            0, 1
        )

    # ------------------------------------------------------------------
    # 1. Observational inference — P(Y | X = x)
    # ------------------------------------------------------------------

    def observational_inference(
        self,
        source: str,
        target: str,
        source_value: float,
        conditioning_on: list[str] | None = None,
    ) -> dict[str, Any]:
        """Estimate P(Y | X = x) using ordinary least squares.

        When `conditioning_on` is provided the regression includes those
        variables as additional covariates, yielding a conditional estimate
        E[Y | X = x, Z = obs(Z)].

        Args:
            source: Node ID of the cause variable (X).
            target: Node ID of the outcome variable (Y).
            source_value: The value at which to evaluate X.
            conditioning_on: Optional list of node IDs to condition on.

        Returns:
            dict with keys:
                ``point_estimate`` (float),
                ``confidence`` (float in [0, 1]),
                ``r_squared`` (float),
                ``p_value`` (float),
                ``natural_language_summary`` (str),
                ``warnings`` (list[str]).
        """
        warnings: list[str] = []
        conditioning_on = conditioning_on or []

        # Validate columns
        for col in [source, target] + conditioning_on:
            if col not in self._norm_data.columns:
                warnings.append(f"Column '{col}' missing from historical data")

        available = [
            c
            for c in [source] + conditioning_on
            if c in self._norm_data.columns
        ]
        if target not in self._norm_data.columns or not available:
            return self._empty_result(
                f"Insufficient data for {source} → {target}", warnings
            )

        # Determine optimal lag from graph edge if available
        lag = self._get_peak_lag(source, target)

        try:
            # Build design matrix
            cols_X: list[pd.Series] = []
            for col in available:
                s = self._norm_data[col].shift(lag if col == source else 0)
                cols_X.append(s)
            X_df = pd.concat(cols_X, axis=1).dropna()
            y_series = self._norm_data[target].reindex(X_df.index).dropna()
            common_idx = X_df.index.intersection(y_series.index)
            X_arr = X_df.loc[common_idx].values
            y_arr = y_series.loc[common_idx].values

            if len(y_arr) < 20:
                warnings.append(
                    f"Only {len(y_arr)} observations after alignment; "
                    "estimates may be unreliable"
                )

            coefs, r2, p_f, _ = _ols_fit(X_arr, y_arr)
            beta_source = float(coefs[0])

            # Normalise source_value to z-score space for prediction.
            src_mean = float(self.data[source].mean())
            src_std = float(self.data[source].std()) or 1.0
            source_z = (source_value - src_mean) / src_std

            # Point estimate of Y in z-score space, then convert back.
            tgt_mean = float(self.data[target].mean())
            tgt_std = float(self.data[target].std()) or 1.0
            y_hat_z = beta_source * source_z
            point_estimate = tgt_mean + y_hat_z * tgt_std

            confidence = min(0.99, max(0.01, 1.0 - p_f)) * min(1.0, r2 + 0.1)

            summary = (
                f"Observational estimate: when {source} is {source_value:.3f}, "
                f"the expected value of {target} is {point_estimate:.3f} "
                f"(R²={r2:.3f}, lag={lag}d). "
                f"This is a correlational, not causal, estimate."
            )
            if conditioning_on:
                summary += (
                    f" Conditioned on: {', '.join(conditioning_on)}."
                )

            return {
                "point_estimate": point_estimate,
                "confidence": confidence,
                "r_squared": r2,
                "p_value": p_f,
                "beta": beta_source,
                "lag_days": lag,
                "natural_language_summary": summary,
                "warnings": warnings,
                "method": "OLS_observational",
            }
        except Exception as exc:
            logger.exception(f"observational_inference failed: {exc}")
            warnings.append(str(exc))
            return self._empty_result("Computation error", warnings)

    # ------------------------------------------------------------------
    # 2. Interventional inference — P(Y | do(X = x))
    # ------------------------------------------------------------------

    def interventional_inference(
        self,
        source: str,
        target: str,
        intervention_value: float,
    ) -> dict[str, Any]:
        """Estimate P(Y | do(X = x)) via the backdoor adjustment formula.

        The adjustment set is approximated as the set of graph-level
        parents of `source` that are also observed in the historical data.
        This satisfies the backdoor criterion for DAGs with no hidden
        confounders — a simplifying assumption noted in the output warnings.

        Args:
            source: Node ID of the intervened variable (X).
            target: Node ID of the outcome variable (Y).
            intervention_value: The value forced onto X by the intervention.

        Returns:
            dict with keys analogous to :meth:`observational_inference`,
            plus ``adjustment_set`` (list[str]) and ``backdoor_used`` (bool).
        """
        warnings: list[str] = [
            "Backdoor adjustment assumes no unmeasured confounders. "
            "Treat interventional estimates with caution."
        ]

        # Find backdoor adjustment set: parents of source that are in data.
        try:
            parents = self.graph.get_causal_parents(source)
        except Exception:
            parents = []

        adjustment_set = [
            p for p in parents if p in self._norm_data.columns and p != target
        ]
        if not adjustment_set:
            warnings.append(
                f"No observed parents found for '{source}'; "
                "falling back to observational estimate (do-calculus unapplicable)"
            )
            obs = self.observational_inference(source, target, intervention_value)
            obs["method"] = "OLS_fallback_no_adjustment_set"
            obs["adjustment_set"] = []
            obs["backdoor_used"] = False
            obs["warnings"] = warnings + obs.get("warnings", [])
            return obs

        # Backdoor adjustment: regress Y on (X, Z) where Z = adjustment set,
        # then evaluate at the intervention value of X while integrating out Z
        # (which here means evaluating at the observed mean of Z — a valid
        # approximation when X and Z are uncorrelated after do(X)).
        try:
            lag = self._get_peak_lag(source, target)
            feature_cols = [source] + adjustment_set
            series_list = [
                self._norm_data[source].shift(lag)
            ] + [self._norm_data[z] for z in adjustment_set]
            X_df = pd.concat(series_list, axis=1, keys=feature_cols).dropna()
            y_series = self._norm_data[target].reindex(X_df.index).dropna()
            common_idx = X_df.index.intersection(y_series.index)
            X_arr = X_df.loc[common_idx].values
            y_arr = y_series.loc[common_idx].values

            if len(y_arr) < 20:
                warnings.append(
                    f"Only {len(y_arr)} observations; adjustment estimate unreliable"
                )

            coefs, r2, p_f, _ = _ols_fit(X_arr, y_arr)
            beta_x = float(coefs[0])  # coefficient on source (post-adjustment)

            # Convert intervention value to z-score.
            src_mean = float(self.data[source].mean())
            src_std = float(self.data[source].std()) or 1.0
            x_z = (intervention_value - src_mean) / src_std

            # Adjustment set vars evaluated at their sample means (≈ 0 in z-score).
            y_hat_z = beta_x * x_z  # Z terms vanish at their own means

            tgt_mean = float(self.data[target].mean())
            tgt_std = float(self.data[target].std()) or 1.0
            point_estimate = tgt_mean + y_hat_z * tgt_std

            confidence = min(0.99, max(0.01, 1.0 - p_f)) * min(1.0, r2 + 0.1)

            summary = (
                f"Interventional estimate do({source}={intervention_value:.3f}): "
                f"expected {target} ≈ {point_estimate:.3f}. "
                f"Adjustment set: {adjustment_set}. "
                f"Causal coefficient β={beta_x:.4f}, R²={r2:.3f}."
            )

            return {
                "point_estimate": point_estimate,
                "confidence": confidence,
                "r_squared": r2,
                "p_value": p_f,
                "beta": beta_x,
                "lag_days": lag,
                "adjustment_set": adjustment_set,
                "backdoor_used": True,
                "natural_language_summary": summary,
                "warnings": warnings,
                "method": "backdoor_OLS",
            }
        except Exception as exc:
            logger.exception(f"interventional_inference failed: {exc}")
            warnings.append(str(exc))
            return self._empty_result("Computation error", warnings)

    # ------------------------------------------------------------------
    # 3. Path analysis
    # ------------------------------------------------------------------

    def path_analysis(self, source: str, target: str) -> dict[str, Any]:
        """Enumerate all directed paths from source to target and compute
        path-level transmission strength.

        Path strength is computed as the product of edge-level causal
        strengths along the path.  Paths are ranked by absolute strength.

        Args:
            source: Origin node ID.
            target: Destination node ID.

        Returns:
            dict with keys:
                ``paths`` (list[dict]) — ranked path descriptions,
                ``total_paths`` (int),
                ``dominant_path`` (list[str] | None),
                ``natural_language_summary`` (str),
                ``warnings`` (list[str]).
        """
        warnings: list[str] = []

        try:
            all_paths: list[list[str]] = self.graph.find_all_causal_paths(
                source, target, max_depth=6
            )
        except Exception as exc:
            warnings.append(f"Path enumeration error: {exc}")
            all_paths = []

        if not all_paths:
            summary = f"No directed paths found from {source} to {target}."
            return {
                "paths": [],
                "total_paths": 0,
                "dominant_path": None,
                "natural_language_summary": summary,
                "warnings": warnings,
            }

        path_records: list[dict[str, Any]] = []
        for path in all_paths:
            strength = 1.0
            total_lag = 0
            edge_details: list[str] = []
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                edge = self._find_edge(u, v)
                if edge is not None:
                    strength *= edge.causal_strength
                    total_lag += edge.peak_lag_days
                    edge_details.append(
                        f"{u}→{v}(β={edge.causal_strength:.3f}, "
                        f"lag={edge.peak_lag_days}d)"
                    )
                else:
                    # Edge not in graph — estimate from data correlation.
                    r = self._pearson_corr(u, v)
                    strength *= r
                    edge_details.append(f"{u}→{v}(r={r:.3f}, estimated)")

            path_records.append(
                {
                    "path": path,
                    "strength": round(strength, 4),
                    "abs_strength": round(abs(strength), 4),
                    "total_lag_days": total_lag,
                    "edge_details": edge_details,
                    "path_str": " → ".join(path),
                }
            )

        path_records.sort(key=lambda p: p["abs_strength"], reverse=True)
        dominant = path_records[0] if path_records else None

        summary_parts = [
            f"Found {len(path_records)} path(s) from {source} to {target}."
        ]
        if dominant:
            summary_parts.append(
                f"Dominant path: {dominant['path_str']} "
                f"(cumulative strength={dominant['strength']:.4f}, "
                f"total lag≈{dominant['total_lag_days']}d)."
            )
        if len(path_records) > 1:
            secondary = path_records[1]
            summary_parts.append(
                f"Secondary path: {secondary['path_str']} "
                f"(strength={secondary['strength']:.4f})."
            )

        return {
            "paths": path_records,
            "total_paths": len(path_records),
            "dominant_path": dominant["path"] if dominant else None,
            "natural_language_summary": " ".join(summary_parts),
            "warnings": warnings,
        }

    # ------------------------------------------------------------------
    # 4. Confounding detection
    # ------------------------------------------------------------------

    def confounding_detection(self, source: str, target: str) -> dict[str, Any]:
        """Detect confounding by comparing raw vs. partial correlations.

        For each node in the graph that is a potential common cause
        (has directed paths to both source and target), this method
        computes the partial correlation between source and target
        after controlling for the potential confounder.  A large drop
        in correlation indicates confounding.

        Args:
            source: Node ID of the putative cause.
            target: Node ID of the putative effect.

        Returns:
            dict with keys:
                ``raw_correlation`` (float),
                ``confounders_tested`` (list[dict]),
                ``strongest_confounder`` (str | None),
                ``confounding_detected`` (bool),
                ``natural_language_summary`` (str),
                ``warnings`` (list[str]).
        """
        warnings: list[str] = []

        if source not in self.data.columns or target not in self.data.columns:
            warnings.append("Source or target not in historical data")
            return self._empty_result("Data missing", warnings)

        lag = self._get_peak_lag(source, target)
        x_raw, y_raw = _align_series(self.data, source, target, lag=lag)
        if len(x_raw) < 10:
            warnings.append("Too few observations for confounding analysis")
            return self._empty_result("Insufficient data", warnings)

        raw_corr, raw_pval = stats.pearsonr(x_raw.values, y_raw.values)

        # Candidate confounders: graph parents of both source and target,
        # plus any node with |correlation| > 0.4 with both.
        candidates = self._find_common_causes(source, target)
        confounder_results: list[dict[str, Any]] = []

        for cand in candidates:
            if cand not in self.data.columns:
                continue
            try:
                partial_corr = self._partial_correlation(source, target, cand, lag)
                drop = raw_corr - partial_corr
                confounder_results.append(
                    {
                        "confounder": cand,
                        "raw_correlation": round(raw_corr, 4),
                        "partial_correlation": round(partial_corr, 4),
                        "correlation_drop": round(drop, 4),
                        "confounding_strength": round(abs(drop) / (abs(raw_corr) + 1e-9), 4),
                    }
                )
            except Exception as exc:
                warnings.append(f"Partial corr failed for {cand}: {exc}")

        confounder_results.sort(
            key=lambda r: r["confounding_strength"], reverse=True
        )

        confounding_detected = bool(
            confounder_results and confounder_results[0]["confounding_strength"] > 0.2
        )
        strongest = (
            confounder_results[0]["confounder"] if confounder_results else None
        )

        if confounding_detected and strongest:
            summary = (
                f"Confounding detected. Raw correlation {source}↔{target}: "
                f"{raw_corr:.3f}. After controlling for '{strongest}', "
                f"partial correlation drops to "
                f"{confounder_results[0]['partial_correlation']:.3f} "
                f"(reduction={confounder_results[0]['confounding_strength']:.1%}). "
                f"Recommend using backdoor-adjusted estimates."
            )
        elif confounder_results:
            summary = (
                f"No significant confounding detected. Raw correlation: {raw_corr:.3f}. "
                f"Tested {len(confounder_results)} candidate confounder(s)."
            )
        else:
            summary = (
                f"Raw correlation {source}↔{target}: {raw_corr:.3f}. "
                f"No candidate confounders identified in the graph."
            )

        return {
            "raw_correlation": round(raw_corr, 4),
            "raw_p_value": round(raw_pval, 4),
            "confounders_tested": confounder_results,
            "strongest_confounder": strongest,
            "confounding_detected": confounding_detected,
            "natural_language_summary": summary,
            "warnings": warnings,
        }

    # ------------------------------------------------------------------
    # Private utility methods
    # ------------------------------------------------------------------

    def _get_peak_lag(self, source: str, target: str) -> int:
        """Return the peak_lag_days from the graph edge, or 0 if unknown."""
        edge = self._find_edge(source, target)
        return edge.peak_lag_days if edge is not None else 0

    def _find_edge(self, source: str, target: str):
        """Return the CausalEdge from source to target, or None."""
        for edge in self.graph.edges.values():
            if edge.source_node == source and edge.target_node == target:
                return edge
        return None

    def _pearson_corr(self, col_a: str, col_b: str, lag: int = 0) -> float:
        """Return Pearson r between two columns (0.0 if data insufficient)."""
        try:
            x, y = _align_series(self.data, col_a, col_b, lag=lag)
            if len(x) < 5:
                return 0.0
            r, _ = stats.pearsonr(x.values, y.values)
            return float(r)
        except Exception:
            return 0.0

    def _partial_correlation(
        self,
        source: str,
        target: str,
        control: str,
        lag: int = 0,
    ) -> float:
        """Compute partial correlation of source and target controlling for control.

        Uses the residual-on-residual approach.
        """
        common_idx = (
            self.data[[source, target, control]].shift(
                {source: lag} if lag else 0
            )
        ).dropna().index

        # Shift source by lag if needed
        df_aligned = pd.concat(
            [
                self.data[source].shift(lag).rename(source),
                self.data[target],
                self.data[control],
            ],
            axis=1,
        ).loc[common_idx]

        x = df_aligned[source].values.reshape(-1, 1)
        y = df_aligned[target].values
        z = df_aligned[control].values.reshape(-1, 1)

        # Residuals of X ~ Z and Y ~ Z
        res_x = x.ravel() - LinearRegression().fit(z, x.ravel()).predict(z)
        res_y = y - LinearRegression().fit(z, y).predict(z)

        if len(res_x) < 5:
            return 0.0
        r, _ = stats.pearsonr(res_x, res_y)
        return float(r)

    def _find_common_causes(self, source: str, target: str) -> list[str]:
        """Return node IDs that could be common causes of source and target."""
        try:
            all_nodes = list(self.graph.nodes.keys())
        except Exception:
            all_nodes = list(self.data.columns)

        common: list[str] = []
        for node in all_nodes:
            if node in (source, target):
                continue
            # Check if node has any path to both source and target in the graph.
            try:
                paths_to_src = self.graph.find_all_causal_paths(node, source, max_depth=3)
                paths_to_tgt = self.graph.find_all_causal_paths(node, target, max_depth=3)
                if paths_to_src and paths_to_tgt:
                    common.append(node)
                    continue
            except Exception:
                pass
            # Fallback: purely data-driven — high correlation with both.
            if node in self.data.columns:
                r_src = abs(self._pearson_corr(node, source))
                r_tgt = abs(self._pearson_corr(node, target))
                if r_src > 0.4 and r_tgt > 0.4:
                    common.append(node)
        return common

    @staticmethod
    def _empty_result(reason: str, warnings: list[str]) -> dict[str, Any]:
        return {
            "point_estimate": None,
            "confidence": 0.0,
            "r_squared": None,
            "p_value": None,
            "natural_language_summary": reason,
            "warnings": warnings,
            "method": "none",
        }
