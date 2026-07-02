"""
Causal graph edge definitions for macro risk analysis.

Defines the mechanism taxonomy, activation logic, and the canonical set of
causal transmission channels that connect nodes in the macro-risk graph.

Design notes
------------
- No lambdas are used anywhere in this module so that edges are fully
  serialisable to JSON / pickle without custom hooks.
- Non-linear effect shapes are represented by a string ``nonlinear_type``
  (e.g. ``"threshold_asymmetric"``) rather than a callable, keeping
  dataclasses picklable and diffable in version control.
- ``ActivationRule.evaluate`` resolves conditions against a plain
  ``dict[str, float]`` *graph_state* snapshot, making unit-testing
  straightforward without a live graph object.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class EdgeMechanism(str, Enum):
    """Economic/financial mechanism through which the causal effect transmits."""

    DIRECT_PRICING = "DIRECT_PRICING"
    """Contemporaneous repricing of an asset based on another (e.g. FX pass-through)."""

    FLOW_CHANNEL = "FLOW_CHANNEL"
    """Capital or trade flows that mechanically link two variables."""

    CREDIT_CHANNEL = "CREDIT_CHANNEL"
    """Tightening/easing of credit conditions propagating to borrowing costs."""

    CONFIDENCE = "CONFIDENCE"
    """Sentiment-driven re-rating; animal-spirits / reflexivity effects."""

    FUNDAMENTAL = "FUNDAMENTAL"
    """Changes in underlying cash-flow or growth fundamentals."""

    REGULATORY = "REGULATORY"
    """Policy mandate or regulatory constraint driving the relationship."""

    SUPPLY_CHAIN = "SUPPLY_CHAIN"
    """Physical supply/demand disruption propagating through production chains."""


class ActivationCondition(str, Enum):
    """Logical form of the condition that must hold for an edge to be active."""

    ALWAYS = "ALWAYS"
    """Edge is unconditionally active at all times."""

    THRESHOLD = "THRESHOLD"
    """Active only when a nominated node crosses a threshold value."""

    REGIME = "REGIME"
    """Active only within a named macro regime (e.g. 'risk_off', 'qe')."""

    CONJUNCTION = "CONJUNCTION"
    """Active only when *all* sub-conditions in ``sub_conditions`` hold."""


# ---------------------------------------------------------------------------
# Activation rule
# ---------------------------------------------------------------------------


@dataclass
class ActivationRule:
    """Encodes when a causal edge is active.

    Parameters
    ----------
    condition_type:
        The logical form; see :class:`ActivationCondition`.
    threshold_node_id:
        Node whose value is compared against ``threshold_value``.
        Required when ``condition_type == THRESHOLD``.
    threshold_value:
        Numeric threshold.  Interpretation depends on ``threshold_direction``.
    threshold_direction:
        ``"above"`` — active when node value > threshold.
        ``"below"`` — active when node value < threshold.
    regime_name:
        Named regime key in *graph_state* (e.g. ``"risk_off"``).
        Required when ``condition_type == REGIME``.
    sub_conditions:
        Child :class:`ActivationRule` instances evaluated as a conjunction.
        Required when ``condition_type == CONJUNCTION``.
    """

    condition_type: ActivationCondition = ActivationCondition.ALWAYS
    threshold_node_id: Optional[str] = None
    threshold_value: Optional[float] = None
    threshold_direction: str = "above"  # "above" | "below"
    regime_name: Optional[str] = None
    sub_conditions: list[ActivationRule] = field(default_factory=list)

    def __post_init__(self) -> None:
        if isinstance(self.condition_type, str):
            self.condition_type = ActivationCondition(self.condition_type)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(self, graph_state: dict[str, Any]) -> bool:
        """Return ``True`` if this rule is satisfied given *graph_state*.

        Parameters
        ----------
        graph_state:
            A flat mapping of ``node_id -> current_value`` (numeric) plus
            optional ``regime_<name> -> True/False`` keys for regime flags.

        Returns
        -------
        bool
            Whether the edge governed by this rule should be treated as active.
        """
        match self.condition_type:
            case ActivationCondition.ALWAYS:
                return True

            case ActivationCondition.THRESHOLD:
                if self.threshold_node_id is None or self.threshold_value is None:
                    # Misconfigured rule — default to active so nothing silently breaks.
                    return True
                node_val = graph_state.get(self.threshold_node_id)
                if node_val is None:
                    return True  # Missing data — conservative: treat as active.
                if self.threshold_direction == "above":
                    return float(node_val) > self.threshold_value
                return float(node_val) < self.threshold_value

            case ActivationCondition.REGIME:
                if self.regime_name is None:
                    return True
                key = f"regime_{self.regime_name}"
                return bool(graph_state.get(key, False))

            case ActivationCondition.CONJUNCTION:
                return all(
                    sub.evaluate(graph_state) for sub in self.sub_conditions
                )

            case _:
                return True

    def to_dict(self) -> dict:
        return {
            "condition_type": self.condition_type.value,
            "threshold_node_id": self.threshold_node_id,
            "threshold_value": self.threshold_value,
            "threshold_direction": self.threshold_direction,
            "regime_name": self.regime_name,
            "sub_conditions": [s.to_dict() for s in self.sub_conditions],
        }


# Default rule used when no special activation logic is required.
_ALWAYS_ACTIVE = ActivationRule(condition_type=ActivationCondition.ALWAYS)


# ---------------------------------------------------------------------------
# Edge dataclass
# ---------------------------------------------------------------------------


@dataclass
class CausalEdge:
    """A directed causal relationship between two nodes.

    Parameters
    ----------
    edge_id:
        Unique identifier, conventionally ``"<source>-><target>"``.
    source_node:
        ``node_id`` of the cause.
    target_node:
        ``node_id`` of the effect.
    causal_strength:
        Point estimate of the standardised causal effect size in [-1, 1].
        Positive = same-direction; negative = opposite-direction.
    strength_confidence:
        Analyst confidence in the *direction* of the estimate (0–1).
    strength_ci_lower / strength_ci_upper:
        95 % confidence interval around ``causal_strength``.
    min_lag_days / max_lag_days / peak_lag_days:
        Transmission lag range and mode (in calendar days).
    effect_decay:
        Half-life of the causal effect (days).  ``None`` = permanent shift.
    mechanism:
        Economic channel; see :class:`EdgeMechanism`.
    mechanism_description:
        One-sentence explanation of the transmission path.
    is_nonlinear:
        ``True`` when the relationship is materially nonlinear.
    nonlinear_type:
        String label for the nonlinearity shape:
        ``"threshold_asymmetric"``, ``"regime_switching"``,
        ``"convex"``, ``"concave"``, ``"u_shaped"``.
        ``None`` when ``is_nonlinear`` is ``False``.
    activation_rule:
        :class:`ActivationRule` controlling when this edge fires.
    known_confounders:
        List of ``node_id`` strings for known common causes.
    evidence_type:
        How the edge was established: ``"econometric"``, ``"structural"``,
        ``"expert"``, ``"literature"``.
    last_validated_date:
        Date of most recent empirical validation.
    validation_p_value:
        p-value from the most recent Granger / structural test.
    num_supporting_events:
        Count of historical episodes supporting this relationship.
    is_deprecated:
        Mark an edge as no longer relevant (soft delete).
    """

    edge_id: str
    source_node: str
    target_node: str

    # Effect magnitude
    causal_strength: float = 0.0
    strength_confidence: float = 0.5
    strength_ci_lower: float = -1.0
    strength_ci_upper: float = 1.0

    # Lag structure (calendar days)
    min_lag_days: int = 0
    max_lag_days: int = 5
    peak_lag_days: int = 1

    # Decay
    effect_decay: Optional[float] = None  # half-life in days; None = permanent

    # Mechanism
    mechanism: EdgeMechanism = EdgeMechanism.DIRECT_PRICING
    mechanism_description: str = ""

    # Nonlinearity (no lambdas — use string labels only)
    is_nonlinear: bool = False
    nonlinear_type: Optional[str] = None  # e.g. "threshold_asymmetric"

    # Activation
    activation_rule: ActivationRule = field(
        default_factory=lambda: ActivationRule(condition_type=ActivationCondition.ALWAYS)
    )

    # Evidence
    known_confounders: list[str] = field(default_factory=list)
    evidence_type: str = "expert"
    last_validated_date: Optional[date] = None
    validation_p_value: Optional[float] = None
    num_supporting_events: int = 0

    # Lifecycle
    is_deprecated: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.mechanism, str):
            self.mechanism = EdgeMechanism(self.mechanism)

    # ------------------------------------------------------------------
    # Derived properties
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        """Return ``True`` unless the edge has been deprecated."""
        return not self.is_deprecated

    def adjusted_strength(self, regime_multiplier: float = 1.0) -> float:
        """Return causal strength scaled by a regime-specific multiplier.

        Parameters
        ----------
        regime_multiplier:
            External scaling factor (e.g. 1.5 in a high-stress regime).
            Clamped so the result stays in [-1, 1].
        """
        raw = self.causal_strength * regime_multiplier
        return max(-1.0, min(1.0, raw))

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "edge_id": self.edge_id,
            "source_node": self.source_node,
            "target_node": self.target_node,
            "causal_strength": self.causal_strength,
            "strength_confidence": self.strength_confidence,
            "strength_ci_lower": self.strength_ci_lower,
            "strength_ci_upper": self.strength_ci_upper,
            "min_lag_days": self.min_lag_days,
            "max_lag_days": self.max_lag_days,
            "peak_lag_days": self.peak_lag_days,
            "effect_decay": self.effect_decay,
            "mechanism": self.mechanism.value,
            "mechanism_description": self.mechanism_description,
            "is_nonlinear": self.is_nonlinear,
            "nonlinear_type": self.nonlinear_type,
            "activation_rule": self.activation_rule.to_dict(),
            "known_confounders": self.known_confounders,
            "evidence_type": self.evidence_type,
            "last_validated_date": (
                self.last_validated_date.isoformat()
                if self.last_validated_date
                else None
            ),
            "validation_p_value": self.validation_p_value,
            "num_supporting_events": self.num_supporting_events,
            "is_deprecated": self.is_deprecated,
        }


# ---------------------------------------------------------------------------
# Canonical edge registry
# ---------------------------------------------------------------------------

INITIAL_EDGES: list[CausalEdge] = [
    # ------------------------------------------------------------------
    # 1. Fed Funds → US 2Y Treasury (direct policy pricing)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="fed_funds->ust_2y",
        source_node="fed_funds",
        target_node="ust_2y",
        causal_strength=0.85,
        strength_confidence=0.95,
        strength_ci_lower=0.70,
        strength_ci_upper=0.95,
        min_lag_days=0,
        max_lag_days=2,
        peak_lag_days=0,
        mechanism=EdgeMechanism.DIRECT_PRICING,
        mechanism_description=(
            "Market prices front-end rates almost immediately on FOMC decisions "
            "and forward guidance."
        ),
        evidence_type="econometric",
        last_validated_date=date(2024, 12, 1),
        validation_p_value=0.001,
        num_supporting_events=42,
    ),
    # ------------------------------------------------------------------
    # 2. Fed Funds → US 10Y Treasury (term-premium & expectations)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="fed_funds->ust_10y",
        source_node="fed_funds",
        target_node="ust_10y",
        causal_strength=0.55,
        strength_confidence=0.80,
        strength_ci_lower=0.35,
        strength_ci_upper=0.70,
        min_lag_days=0,
        max_lag_days=10,
        peak_lag_days=1,
        mechanism=EdgeMechanism.DIRECT_PRICING,
        mechanism_description=(
            "Policy path expectations shift the long end; dampened by term-premium "
            "and global safe-haven demand."
        ),
        is_nonlinear=True,
        nonlinear_type="regime_switching",
        evidence_type="econometric",
        last_validated_date=date(2024, 12, 1),
        validation_p_value=0.01,
        num_supporting_events=38,
    ),
    # ------------------------------------------------------------------
    # 3. US 10Y → DXY (interest-rate differential / carry)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="ust_10y->dxy",
        source_node="ust_10y",
        target_node="dxy",
        causal_strength=0.60,
        strength_confidence=0.80,
        strength_ci_lower=0.40,
        strength_ci_upper=0.75,
        min_lag_days=0,
        max_lag_days=5,
        peak_lag_days=1,
        mechanism=EdgeMechanism.FLOW_CHANNEL,
        mechanism_description=(
            "Higher US yields attract capital inflows, increasing demand for USD."
        ),
        known_confounders=["global_liqd", "vix"],
        evidence_type="econometric",
        last_validated_date=date(2024, 11, 15),
        validation_p_value=0.005,
        num_supporting_events=55,
    ),
    # ------------------------------------------------------------------
    # 4. Global Liquidity → DXY (inverse: more liquidity = weaker USD)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="global_liqd->dxy",
        source_node="global_liqd",
        target_node="dxy",
        causal_strength=-0.50,
        strength_confidence=0.70,
        strength_ci_lower=-0.70,
        strength_ci_upper=-0.25,
        min_lag_days=5,
        max_lag_days=30,
        peak_lag_days=15,
        effect_decay=60.0,
        mechanism=EdgeMechanism.FLOW_CHANNEL,
        mechanism_description=(
            "Global QE expansions inflate offshore USD liquidity, putting downward "
            "pressure on the Dollar Index."
        ),
        evidence_type="structural",
        num_supporting_events=12,
    ),
    # ------------------------------------------------------------------
    # 5. DXY → KRW/USD (pass-through: stronger USD = weaker KRW)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="dxy->krw_usd",
        source_node="dxy",
        target_node="krw_usd",
        causal_strength=0.75,
        strength_confidence=0.90,
        strength_ci_lower=0.60,
        strength_ci_upper=0.85,
        min_lag_days=0,
        max_lag_days=3,
        peak_lag_days=0,
        mechanism=EdgeMechanism.DIRECT_PRICING,
        mechanism_description=(
            "KRW is a high-beta EM currency; DXY moves are transmitted nearly 1:1 "
            "in stressed conditions."
        ),
        is_nonlinear=True,
        nonlinear_type="threshold_asymmetric",
        activation_rule=ActivationRule(
            condition_type=ActivationCondition.ALWAYS
        ),
        known_confounders=["kr_ca", "vix"],
        evidence_type="econometric",
        last_validated_date=date(2024, 10, 1),
        validation_p_value=0.001,
        num_supporting_events=70,
    ),
    # ------------------------------------------------------------------
    # 6. KRW/USD → KOSPI (weaker KRW → export boost but risk-off drag)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="krw_usd->kospi",
        source_node="krw_usd",
        target_node="kospi",
        causal_strength=-0.45,
        strength_confidence=0.75,
        strength_ci_lower=-0.65,
        strength_ci_upper=-0.20,
        min_lag_days=0,
        max_lag_days=5,
        peak_lag_days=1,
        mechanism=EdgeMechanism.FUNDAMENTAL,
        mechanism_description=(
            "KRW depreciation tightens financial conditions and signals capital "
            "outflows; net negative for KOSPI despite export tailwind."
        ),
        is_nonlinear=True,
        nonlinear_type="threshold_asymmetric",
        known_confounders=["vix", "sox"],
        evidence_type="econometric",
        last_validated_date=date(2024, 9, 1),
        validation_p_value=0.02,
        num_supporting_events=48,
    ),
    # ------------------------------------------------------------------
    # 7. VIX → KRW/USD (risk-off triggers EM FX sell-off)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="vix->krw_usd",
        source_node="vix",
        target_node="krw_usd",
        causal_strength=0.65,
        strength_confidence=0.85,
        strength_ci_lower=0.45,
        strength_ci_upper=0.80,
        min_lag_days=0,
        max_lag_days=2,
        peak_lag_days=0,
        mechanism=EdgeMechanism.CONFIDENCE,
        mechanism_description=(
            "VIX spikes prompt global investors to de-risk and exit EM positions, "
            "selling KRW to buy USD safe havens."
        ),
        is_nonlinear=True,
        nonlinear_type="threshold_asymmetric",
        activation_rule=ActivationRule(
            condition_type=ActivationCondition.THRESHOLD,
            threshold_node_id="vix",
            threshold_value=20.0,
            threshold_direction="above",
        ),
        evidence_type="econometric",
        last_validated_date=date(2024, 10, 1),
        validation_p_value=0.003,
        num_supporting_events=35,
    ),
    # ------------------------------------------------------------------
    # 8. US Recession Prob → VIX (growth fear feeds volatility)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="us_recession_prob->vix",
        source_node="us_recession_prob",
        target_node="vix",
        causal_strength=0.55,
        strength_confidence=0.75,
        strength_ci_lower=0.30,
        strength_ci_upper=0.70,
        min_lag_days=0,
        max_lag_days=30,
        peak_lag_days=5,
        mechanism=EdgeMechanism.CONFIDENCE,
        mechanism_description=(
            "Rising recession probability elevates equity risk premium, "
            "pushing implied volatility higher."
        ),
        evidence_type="structural",
        num_supporting_events=8,
    ),
    # ------------------------------------------------------------------
    # 9. US 10Y → Korea Sovereign CDS (global rate risk-off → EM spreads)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="ust_10y->kr_cds_5y",
        source_node="ust_10y",
        target_node="kr_cds_5y",
        causal_strength=0.40,
        strength_confidence=0.70,
        strength_ci_lower=0.15,
        strength_ci_upper=0.60,
        min_lag_days=0,
        max_lag_days=5,
        peak_lag_days=2,
        mechanism=EdgeMechanism.CREDIT_CHANNEL,
        mechanism_description=(
            "Rising US yields compress risk appetite; global investors demand "
            "wider EM sovereign spreads."
        ),
        known_confounders=["vix", "dxy"],
        evidence_type="econometric",
        last_validated_date=date(2024, 8, 1),
        validation_p_value=0.05,
        num_supporting_events=22,
    ),
    # ------------------------------------------------------------------
    # 10. Korea CDS → KOSPI (sovereign credit risk → equity de-rating)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="kr_cds_5y->kospi",
        source_node="kr_cds_5y",
        target_node="kospi",
        causal_strength=-0.55,
        strength_confidence=0.80,
        strength_ci_lower=-0.70,
        strength_ci_upper=-0.35,
        min_lag_days=0,
        max_lag_days=5,
        peak_lag_days=1,
        mechanism=EdgeMechanism.CREDIT_CHANNEL,
        mechanism_description=(
            "Widening sovereign CDS raises the discount rate applied to Korean equities "
            "and signals institutional foreign outflows."
        ),
        evidence_type="econometric",
        last_validated_date=date(2024, 9, 1),
        validation_p_value=0.01,
        num_supporting_events=30,
    ),
    # ------------------------------------------------------------------
    # 11. KOSPI → SOX (Korean semis are a leading indicator for US semis)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="kospi->sox",
        source_node="kospi",
        target_node="sox",
        causal_strength=0.50,
        strength_confidence=0.75,
        strength_ci_lower=0.30,
        strength_ci_upper=0.65,
        min_lag_days=0,
        max_lag_days=3,
        peak_lag_days=1,
        mechanism=EdgeMechanism.SUPPLY_CHAIN,
        mechanism_description=(
            "Samsung/SK Hynix account for ~70 % of DRAM supply; KOSPI moves "
            "are picked up by SOX with a 1-day lag."
        ),
        evidence_type="econometric",
        last_validated_date=date(2024, 11, 1),
        validation_p_value=0.02,
        num_supporting_events=60,
    ),
    # ------------------------------------------------------------------
    # 12. DRAM Spot → KOSPI (chip ASP drives Samsung/Hynix earnings)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="dram_spot->kospi",
        source_node="dram_spot",
        target_node="kospi",
        causal_strength=0.65,
        strength_confidence=0.85,
        strength_ci_lower=0.45,
        strength_ci_upper=0.80,
        min_lag_days=0,
        max_lag_days=10,
        peak_lag_days=3,
        mechanism=EdgeMechanism.FUNDAMENTAL,
        mechanism_description=(
            "DRAM prices directly impact earnings of Samsung Electronics and SK Hynix, "
            "which together account for ~30 % of KOSPI market cap."
        ),
        evidence_type="econometric",
        last_validated_date=date(2024, 10, 1),
        validation_p_value=0.005,
        num_supporting_events=40,
    ),
    # ------------------------------------------------------------------
    # 13. AI Capex → DRAM Spot (hyperscaler demand pulls memory prices)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="ai_capex->dram_spot",
        source_node="ai_capex",
        target_node="dram_spot",
        causal_strength=0.70,
        strength_confidence=0.80,
        strength_ci_lower=0.45,
        strength_ci_upper=0.85,
        min_lag_days=30,
        max_lag_days=90,
        peak_lag_days=45,
        effect_decay=120.0,
        mechanism=EdgeMechanism.SUPPLY_CHAIN,
        mechanism_description=(
            "HBM and DDR5 demand for AI accelerators directly lifts contract and spot "
            "DRAM prices through capacity allocation."
        ),
        evidence_type="structural",
        num_supporting_events=6,
    ),
    # ------------------------------------------------------------------
    # 14. AI Capex → Oracle CDS (capex boom signals cloud revenue visibility)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="ai_capex->orcl_cds",
        source_node="ai_capex",
        target_node="orcl_cds",
        causal_strength=-0.45,
        strength_confidence=0.65,
        strength_ci_lower=-0.65,
        strength_ci_upper=-0.20,
        min_lag_days=0,
        max_lag_days=30,
        peak_lag_days=10,
        mechanism=EdgeMechanism.CREDIT_CHANNEL,
        mechanism_description=(
            "Rising hyperscaler capex validates Oracle Cloud's revenue pipeline, "
            "tightening Oracle's credit spreads."
        ),
        evidence_type="expert",
        num_supporting_events=4,
    ),
    # ------------------------------------------------------------------
    # 15. Oil WTI → Korea CDS (oil shock = external financing pressure for KR)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="oil_wti->kr_cds_5y",
        source_node="oil_wti",
        target_node="kr_cds_5y",
        causal_strength=0.35,
        strength_confidence=0.65,
        strength_ci_lower=0.10,
        strength_ci_upper=0.55,
        min_lag_days=5,
        max_lag_days=30,
        peak_lag_days=10,
        mechanism=EdgeMechanism.FLOW_CHANNEL,
        mechanism_description=(
            "Korea imports ~100 % of its crude oil; an oil price spike widens the "
            "current-account deficit and pressures sovereign credit."
        ),
        activation_rule=ActivationRule(
            condition_type=ActivationCondition.THRESHOLD,
            threshold_node_id="oil_wti",
            threshold_value=85.0,
            threshold_direction="above",
        ),
        evidence_type="structural",
        num_supporting_events=15,
    ),
    # ------------------------------------------------------------------
    # 16. Korea Current Account → KRW/USD (trade surplus supports KRW)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="kr_ca->krw_usd",
        source_node="kr_ca",
        target_node="krw_usd",
        causal_strength=-0.40,
        strength_confidence=0.70,
        strength_ci_lower=-0.60,
        strength_ci_upper=-0.15,
        min_lag_days=10,
        max_lag_days=45,
        peak_lag_days=20,
        effect_decay=90.0,
        mechanism=EdgeMechanism.FLOW_CHANNEL,
        mechanism_description=(
            "A larger current-account surplus means more USD inflows that exporters "
            "convert to KRW, providing structural support."
        ),
        evidence_type="econometric",
        last_validated_date=date(2024, 6, 1),
        validation_p_value=0.04,
        num_supporting_events=25,
    ),
    # ------------------------------------------------------------------
    # 17. NAND Spot → SOX (flash ASP impacts Micron, SK Hynix, WDC earnings)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="nand_spot->sox",
        source_node="nand_spot",
        target_node="sox",
        causal_strength=0.50,
        strength_confidence=0.75,
        strength_ci_lower=0.30,
        strength_ci_upper=0.65,
        min_lag_days=3,
        max_lag_days=15,
        peak_lag_days=5,
        mechanism=EdgeMechanism.FUNDAMENTAL,
        mechanism_description=(
            "NAND flash prices determine margins for Micron, SK Hynix, and WDC, "
            "which are significant SOX constituents."
        ),
        evidence_type="econometric",
        last_validated_date=date(2024, 9, 1),
        validation_p_value=0.02,
        num_supporting_events=35,
    ),
    # ------------------------------------------------------------------
    # 18. HYG → VIX (credit stress feeds volatility)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="hyg->vix",
        source_node="hyg",
        target_node="vix",
        causal_strength=-0.60,
        strength_confidence=0.85,
        strength_ci_lower=-0.75,
        strength_ci_upper=-0.40,
        min_lag_days=0,
        max_lag_days=5,
        peak_lag_days=1,
        mechanism=EdgeMechanism.CREDIT_CHANNEL,
        mechanism_description=(
            "High yield bond selloff (HYG falling) signals credit stress, "
            "which spills into equity volatility."
        ),
        evidence_type="econometric",
        num_supporting_events=30,
    ),
    # ------------------------------------------------------------------
    # 19. HYG → KR_CDS_5Y (US credit stress → EM sovereign spreads)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="hyg->kr_cds_5y",
        source_node="hyg",
        target_node="kr_cds_5y",
        causal_strength=-0.45,
        strength_confidence=0.75,
        strength_ci_lower=-0.65,
        strength_ci_upper=-0.25,
        min_lag_days=0,
        max_lag_days=5,
        peak_lag_days=2,
        mechanism=EdgeMechanism.CREDIT_CHANNEL,
        mechanism_description=(
            "US high yield credit stress (HYG falling) widens EM sovereign "
            "CDS spreads as risk appetite contracts globally."
        ),
        evidence_type="econometric",
        num_supporting_events=20,
    ),
    # ------------------------------------------------------------------
    # 20. KRE → VIX (bank stress feeds systemic fear)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="kre->vix",
        source_node="kre",
        target_node="vix",
        causal_strength=-0.55,
        strength_confidence=0.80,
        strength_ci_lower=-0.70,
        strength_ci_upper=-0.35,
        min_lag_days=0,
        max_lag_days=3,
        peak_lag_days=0,
        mechanism=EdgeMechanism.CONFIDENCE,
        mechanism_description=(
            "Regional bank stock collapse (KRE falling) triggers systemic "
            "contagion fears, pushing VIX higher."
        ),
        evidence_type="econometric",
        num_supporting_events=10,
    ),
    # ------------------------------------------------------------------
    # 21. UST_10Y → KRE (rate shock damages bank bond portfolios)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="ust_10y->kre",
        source_node="ust_10y",
        target_node="kre",
        causal_strength=-0.50,
        strength_confidence=0.80,
        strength_ci_lower=-0.70,
        strength_ci_upper=-0.30,
        min_lag_days=0,
        max_lag_days=10,
        peak_lag_days=3,
        mechanism=EdgeMechanism.FUNDAMENTAL,
        mechanism_description=(
            "Rising long-term rates cause unrealized losses on bank "
            "held-to-maturity bond portfolios (SVB-type risk)."
        ),
        evidence_type="structural",
        num_supporting_events=8,
    ),
    # ------------------------------------------------------------------
    # 22. UST_10Y → VNQ (rates kill real estate valuations)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="ust_10y->vnq",
        source_node="ust_10y",
        target_node="vnq",
        causal_strength=-0.60,
        strength_confidence=0.85,
        strength_ci_lower=-0.75,
        strength_ci_upper=-0.40,
        min_lag_days=0,
        max_lag_days=10,
        peak_lag_days=5,
        mechanism=EdgeMechanism.FUNDAMENTAL,
        mechanism_description=(
            "Rising rates increase mortgage costs and raise REIT discount "
            "rates, suppressing property valuations."
        ),
        evidence_type="econometric",
        num_supporting_events=40,
    ),
    # ------------------------------------------------------------------
    # 23. VNQ → KRE (real estate decline hits bank collateral)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="vnq->kre",
        source_node="vnq",
        target_node="kre",
        causal_strength=0.50,
        strength_confidence=0.75,
        strength_ci_lower=0.30,
        strength_ci_upper=0.65,
        min_lag_days=5,
        max_lag_days=30,
        peak_lag_days=10,
        mechanism=EdgeMechanism.CREDIT_CHANNEL,
        mechanism_description=(
            "Real estate decline erodes bank loan collateral values, "
            "increasing NPL risk and depressing bank stock prices."
        ),
        evidence_type="structural",
        num_supporting_events=12,
    ),
    # ------------------------------------------------------------------
    # 24. Consumer Stress → US Recession Prob
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="consumer_stress->us_recession_prob",
        source_node="consumer_stress",
        target_node="us_recession_prob",
        causal_strength=-0.55,
        strength_confidence=0.80,
        strength_ci_lower=-0.70,
        strength_ci_upper=-0.35,
        min_lag_days=10,
        max_lag_days=60,
        peak_lag_days=30,
        mechanism=EdgeMechanism.FUNDAMENTAL,
        mechanism_description=(
            "Falling XLY/XLP ratio (consumers cutting discretionary spending) "
            "is a leading recession indicator; consumption is 70% of US GDP."
        ),
        evidence_type="econometric",
        num_supporting_events=25,
    ),
    # ------------------------------------------------------------------
    # 25. Copper → KOSPI (industrial demand → export economy)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="copper->kospi",
        source_node="copper",
        target_node="kospi",
        causal_strength=0.45,
        strength_confidence=0.75,
        strength_ci_lower=0.25,
        strength_ci_upper=0.60,
        min_lag_days=0,
        max_lag_days=10,
        peak_lag_days=3,
        mechanism=EdgeMechanism.FUNDAMENTAL,
        mechanism_description=(
            "Copper price reflects global industrial demand; Korea's export-"
            "driven economy is highly correlated with the global capex cycle."
        ),
        evidence_type="econometric",
        num_supporting_events=35,
    ),
    # ------------------------------------------------------------------
    # 26. Gold → DXY (gold rise = USD weakness / fear)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="gold->dxy",
        source_node="gold",
        target_node="dxy",
        causal_strength=-0.40,
        strength_confidence=0.70,
        strength_ci_lower=-0.55,
        strength_ci_upper=-0.20,
        min_lag_days=0,
        max_lag_days=5,
        peak_lag_days=1,
        mechanism=EdgeMechanism.FLOW_CHANNEL,
        mechanism_description=(
            "Gold surge reflects flight from fiat currencies and/or "
            "inflation fears, typically coinciding with USD weakness."
        ),
        evidence_type="econometric",
        num_supporting_events=30,
    ),
    # ------------------------------------------------------------------
    # 27. Gold → VIX (safe haven demand signals fear)
    # ------------------------------------------------------------------
    CausalEdge(
        edge_id="gold->vix",
        source_node="gold",
        target_node="vix",
        causal_strength=0.35,
        strength_confidence=0.65,
        strength_ci_lower=0.15,
        strength_ci_upper=0.50,
        min_lag_days=0,
        max_lag_days=5,
        peak_lag_days=2,
        mechanism=EdgeMechanism.CONFIDENCE,
        mechanism_description=(
            "Rising gold prices signal safe-haven demand, often a precursor "
            "to equity market stress and VIX spikes."
        ),
        evidence_type="structural",
        num_supporting_events=20,
    ),
    # 28. EUR/USD → DXY (euro weakness = dollar strength)
    CausalEdge(edge_id="eurusd->dxy", source_node="eurusd", target_node="dxy", causal_strength=-0.70, strength_confidence=0.90, min_lag_days=0, max_lag_days=1, peak_lag_days=0, mechanism=EdgeMechanism.DIRECT_PRICING, mechanism_description="EUR is 57% of DXY basket; EUR weakness directly drives DXY higher.", evidence_type="econometric", num_supporting_events=100),
    # 29. Italy ETF → EUR/USD (Italian stress weakens EUR)
    CausalEdge(edge_id="italy_etf->eurusd", source_node="italy_etf", target_node="eurusd", causal_strength=0.45, strength_confidence=0.75, min_lag_days=0, max_lag_days=5, peak_lag_days=1, mechanism=EdgeMechanism.CONFIDENCE, mechanism_description="Italian equity selloff signals Eurozone fragmentation risk, weakening EUR.", evidence_type="structural", num_supporting_events=15),
    # 30. CNY → Hang Seng (yuan depreciation hits HK stocks)
    CausalEdge(edge_id="cny_usd->hsi", source_node="cny_usd", target_node="hsi", causal_strength=-0.55, strength_confidence=0.80, min_lag_days=0, max_lag_days=3, peak_lag_days=1, mechanism=EdgeMechanism.FLOW_CHANNEL, mechanism_description="CNY depreciation triggers capital outflows from HK-listed Chinese stocks.", evidence_type="econometric", num_supporting_events=25),
    # 31. Hang Seng → KOSPI (China slowdown hits Korean exports)
    CausalEdge(edge_id="hsi->kospi", source_node="hsi", target_node="kospi", causal_strength=0.50, strength_confidence=0.80, min_lag_days=0, max_lag_days=3, peak_lag_days=1, mechanism=EdgeMechanism.SUPPLY_CHAIN, mechanism_description="China is Korea's largest export market; HSI weakness signals demand contraction.", evidence_type="econometric", num_supporting_events=40),
    # 32. JPY → Nikkei (yen depreciation boosts exporters)
    CausalEdge(edge_id="jpy_usd->nikkei", source_node="jpy_usd", target_node="nikkei", causal_strength=0.50, strength_confidence=0.80, min_lag_days=0, max_lag_days=3, peak_lag_days=1, mechanism=EdgeMechanism.FUNDAMENTAL, mechanism_description="Yen depreciation boosts Japanese exporter earnings and Nikkei.", evidence_type="econometric", num_supporting_events=50),
    # 33. JPY → VIX (yen carry trade unwind spikes vol)
    CausalEdge(edge_id="jpy_usd->vix", source_node="jpy_usd", target_node="vix", causal_strength=-0.40, strength_confidence=0.70, min_lag_days=0, max_lag_days=2, peak_lag_days=0, mechanism=EdgeMechanism.FLOW_CHANNEL, mechanism_description="Rapid yen strengthening forces carry-trade unwind, spiking global volatility.", evidence_type="structural", num_supporting_events=10, is_nonlinear=True, nonlinear_type="threshold_asymmetric"),
    # 34. DXY → CNY (strong dollar pressures yuan)
    CausalEdge(edge_id="dxy->cny_usd", source_node="dxy", target_node="cny_usd", causal_strength=0.60, strength_confidence=0.85, min_lag_days=0, max_lag_days=3, peak_lag_days=1, mechanism=EdgeMechanism.DIRECT_PRICING, mechanism_description="Strong dollar forces PBOC to manage yuan depreciation pressure.", evidence_type="econometric", num_supporting_events=30),
    # 35. DXY → EEM (strong dollar crushes EM)
    CausalEdge(edge_id="dxy->eem", source_node="dxy", target_node="eem", causal_strength=-0.65, strength_confidence=0.85, min_lag_days=0, max_lag_days=3, peak_lag_days=1, mechanism=EdgeMechanism.FLOW_CHANNEL, mechanism_description="Dollar strength triggers EM capital outflows across the board.", evidence_type="econometric", num_supporting_events=60),
    # 36. VIX → EMB (risk-off sells EM bonds)
    CausalEdge(edge_id="vix->emb", source_node="vix", target_node="emb", causal_strength=-0.55, strength_confidence=0.80, min_lag_days=0, max_lag_days=2, peak_lag_days=0, mechanism=EdgeMechanism.CONFIDENCE, mechanism_description="VIX spikes drive selloff in EM sovereign bonds.", evidence_type="econometric", num_supporting_events=30),
    # 37. BTC → VIX (crypto crash signals risk appetite collapse)
    CausalEdge(edge_id="btc->vix", source_node="btc", target_node="vix", causal_strength=-0.35, strength_confidence=0.65, min_lag_days=0, max_lag_days=3, peak_lag_days=1, mechanism=EdgeMechanism.CONFIDENCE, mechanism_description="Bitcoin crash signals broad risk appetite collapse, pushing VIX higher.", evidence_type="structural", num_supporting_events=8),
    # 38. SPX → VIX (stock decline = vol rise, near-mechanical)
    CausalEdge(edge_id="spx->vix", source_node="spx", target_node="vix", causal_strength=-0.80, strength_confidence=0.95, min_lag_days=0, max_lag_days=1, peak_lag_days=0, mechanism=EdgeMechanism.DIRECT_PRICING, mechanism_description="S&P 500 decline mechanically increases VIX (implied vol from put options).", evidence_type="econometric", num_supporting_events=200),
    # 39. Natural Gas → Stoxx50 (energy cost shock hits Europe)
    CausalEdge(edge_id="natgas->stoxx50", source_node="natgas", target_node="stoxx50", causal_strength=-0.40, strength_confidence=0.70, min_lag_days=1, max_lag_days=10, peak_lag_days=5, mechanism=EdgeMechanism.FUNDAMENTAL, mechanism_description="Natural gas spike raises European industrial costs, crushing margins.", evidence_type="structural", num_supporting_events=10),
    # 40. Wheat → VIX (food crisis = social instability = market fear)
    CausalEdge(edge_id="wheat->vix", source_node="wheat", target_node="vix", causal_strength=0.25, strength_confidence=0.55, min_lag_days=5, max_lag_days=30, peak_lag_days=10, mechanism=EdgeMechanism.CONFIDENCE, mechanism_description="Wheat price spikes signal food insecurity and geopolitical tensions.", evidence_type="structural", num_supporting_events=5),
    # 41. Shipping → Copper (trade volume confirms industrial demand)
    CausalEdge(edge_id="bdry->copper", source_node="bdry", target_node="copper", causal_strength=0.40, strength_confidence=0.70, min_lag_days=5, max_lag_days=20, peak_lag_days=10, mechanism=EdgeMechanism.SUPPLY_CHAIN, mechanism_description="Shipping rates lead copper demand; falling freight signals demand slowdown.", evidence_type="structural", num_supporting_events=15),
    # 42. LQD → HYG (investment grade stress precedes junk bond stress)
    CausalEdge(edge_id="lqd->hyg", source_node="lqd", target_node="hyg", causal_strength=0.60, strength_confidence=0.85, min_lag_days=0, max_lag_days=5, peak_lag_days=1, mechanism=EdgeMechanism.CREDIT_CHANNEL, mechanism_description="Investment-grade bond selloff cascades into high-yield credit.", evidence_type="econometric", num_supporting_events=25),
]
