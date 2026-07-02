"""
Hidden Risk Inference Engine — detects risks that market prices don't show.

Six lateral signals that, when combined, reveal structural risks
hiding beneath calm surface indicators:

1. Policy-Market Mismatch: government acting harder than markets suggest
2. Credit Quality Divergence: BAA-AAA spread widening while VIX calm
3. Banking Sector Skepticism: bank stocks lagging the broader market
4. Stealth Safe-Haven Flight: gold/bonds rising without equity panic
5. Policy Emergency Frequency: unusual/emergency central bank actions
6. Cross-Asset Correlation Breakdown: normally correlated assets decoupling
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import numpy as np
from loguru import logger


@dataclass
class HiddenSignal:
    signal_id: str
    title: str
    score: float       # 0-10 contribution to GFCRI
    severity: str      # "low" | "medium" | "high" | "critical"
    evidence: str      # one-line factual evidence
    interpretation: str # what it means

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "title": self.title,
            "score": round(self.score, 1),
            "severity": self.severity,
            "evidence": self.evidence,
            "interpretation": self.interpretation,
        }


@dataclass
class HiddenRiskReport:
    total_boost: float
    signals: list[HiddenSignal]
    risk_narrative: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_boost": round(self.total_boost, 1),
            "signals": [s.to_dict() for s in self.signals],
            "risk_narrative": self.risk_narrative,
        }


class HiddenRiskEngine:
    """Infers hidden systemic risk from lateral/indirect signals."""

    def __init__(
        self,
        node_values: dict[str, float],
        node_zscores: dict[str, float],
        fred_current: dict[str, float],
        fred_history: dict[str, pd.Series],
        prev_node_values: dict[str, float] | None = None,
        prev_fred: dict[str, float] | None = None,
    ):
        self.vals = node_values or {}
        self.zscores = node_zscores or {}
        self.fred = fred_current or {}
        self.fred_hist = fred_history or {}
        self.prev_vals = prev_node_values or {}
        self.prev_fred = prev_fred or {}

    def compute(self) -> HiddenRiskReport:
        signals = []
        for method in [
            self._policy_market_mismatch,
            self._credit_quality_divergence,
            self._banking_skepticism,
            self._stealth_safe_haven,
            self._policy_emergency,
            self._correlation_breakdown,
        ]:
            try:
                s = method()
                if s and s.score > 0:
                    signals.append(s)
            except Exception as e:
                logger.debug(f"Hidden risk signal {method.__name__} failed: {e}")

        signals.sort(key=lambda s: -s.score)
        total = min(25.0, sum(s.score for s in signals))

        narrative = self._build_narrative(signals, total)

        logger.info(
            f"HiddenRisk: {len(signals)} signals, total_boost=+{total:.1f}, "
            f"top={signals[0].signal_id if signals else 'none'}"
        )

        return HiddenRiskReport(
            total_boost=total,
            signals=signals,
            risk_narrative=narrative,
        )

    def _hist_value(self, key: str, days_ago: int) -> float | None:
        series = self.fred_hist.get(key)
        if series is None or series.empty:
            return None
        cutoff = series.index.max() - pd.Timedelta(days=days_ago)
        older = series[series.index <= cutoff]
        return float(older.iloc[-1]) if not older.empty else None

    # ── Signal 1: Policy-Market Mismatch ──

    def _policy_market_mismatch(self) -> HiddenSignal | None:
        """When policy response is aggressive but market barely reacts,
        it means authorities see worse problems than prices reflect."""

        effr = self.fred.get("fred_effr")
        walcl = self.fred.get("fred_walcl")
        effr_3m = self._hist_value("fred_effr", 90)
        walcl_1m = self._hist_value("fred_walcl", 30)
        vix = self.vals.get("vix")
        spx_z = self.zscores.get("spx", 0)

        if effr is None or vix is None:
            return None

        # Policy intensity: rate cuts + balance sheet expansion
        policy_intensity = 0
        evidence_parts = []

        if effr_3m is not None:
            rate_cut = effr_3m - effr
            if rate_cut > 0.5:
                policy_intensity += min(5, rate_cut * 2)
                evidence_parts.append(f"利率3个月降{rate_cut*100:.0f}bp")

        if walcl is not None and walcl_1m is not None:
            bs_change_pct = (walcl - walcl_1m) / walcl_1m * 100
            if bs_change_pct > 2:  # balance sheet expanding fast
                policy_intensity += min(3, bs_change_pct)
                evidence_parts.append(f"资产负债表月扩{bs_change_pct:.1f}%")

        if policy_intensity < 1:
            return None

        # Market response: VIX should be low, SPX should be recovering
        market_calm = max(0, (25 - vix) / 10)  # VIX < 25 = calm
        mismatch = policy_intensity * (1 + market_calm)

        if mismatch < 2:
            return None

        score = min(8, mismatch * 1.2)
        severity = "critical" if score > 6 else "high" if score > 4 else "medium"
        evidence = "；".join(evidence_parts) + f"，但VIX仅{vix:.1f}"

        return HiddenSignal(
            signal_id="policy_mismatch",
            title="政策力度与市场反应不匹配",
            score=score,
            severity=severity,
            evidence=evidence,
            interpretation=(
                "政府投入了远超常规的政策资源，但市场只做出了轻微反应。"
                "这种不匹配说明决策者看到了比市场价格反映的更严重的问题。"
                "2008年3月美联储紧急安排Bear Stearns收购时就出现过这种信号。"
            ),
        )

    # ── Signal 2: Credit Quality Divergence ──

    def _credit_quality_divergence(self) -> HiddenSignal | None:
        """BAA-AAA spread widening = market quietly sorting good vs bad.
        If this happens while VIX is calm, it's stealth credit stress."""

        baa = self.fred.get("fred_bbb_spread")
        if baa is None:
            # Try BAA yield - AAA yield from node values
            baa_yield = self.vals.get("baa_yield") or self.fred.get("fred_baa")
            aaa_yield = self.vals.get("aaa_yield") or self.fred.get("fred_aaa")
            if baa_yield and aaa_yield:
                baa = baa_yield - aaa_yield
            else:
                return None

        baa_3m = self._hist_value("fred_bbb_spread", 90)
        vix = self.vals.get("vix", 20)

        if baa is None:
            return None

        # Credit widening speed
        widening = 0
        if baa_3m is not None:
            widening = baa - baa_3m

        # Absolute level stress
        level_stress = max(0, (baa - 1.5) / 3)  # 1.5% = normal, 4.5% = crisis

        # Surface calm amplifier
        calm_amplifier = max(0.5, (25 - vix) / 15) if vix < 25 else 0.5

        score_raw = (level_stress * 3 + max(0, widening) * 4) * calm_amplifier

        if score_raw < 1:
            return None

        score = min(7, score_raw)
        severity = "critical" if score > 5 else "high" if score > 3 else "medium"

        return HiddenSignal(
            signal_id="credit_divergence",
            title="信用市场悄然分化",
            score=score,
            severity=severity,
            evidence=(
                f"信用利差{baa:.2f}%"
                + (f"（3个月扩大{widening:.2f}%）" if widening > 0 else "")
                + f"，但VIX仅{vix:.1f}"
            ),
            interpretation=(
                "债券市场正在悄悄区分'好公司'和'差公司'，信用利差走阔意味着"
                "最弱的企业借钱变贵了。当这种分化发生在VIX平静期，"
                "说明信用风险在积累但股市还没反应——这是2008年4-8月的经典形态。"
            ),
        )

    # ── Signal 3: Banking Sector Skepticism ──

    def _banking_skepticism(self) -> HiddenSignal | None:
        """Bank stocks lagging = insiders don't believe the recovery."""

        kre_z = self.zscores.get("kre", 0)
        spx_z = self.zscores.get("spx", 0)
        vnq_z = self.zscores.get("vnq", 0)

        # Bank stocks significantly weaker than broad market
        bank_lag = spx_z - kre_z  # positive = banks lagging

        if bank_lag < 1.0:
            return None

        # Real estate adds to the signal
        re_lag = spx_z - vnq_z
        combined = bank_lag + max(0, re_lag) * 0.5

        score = min(6, combined * 1.5)
        severity = "high" if score > 4 else "medium"

        return HiddenSignal(
            signal_id="banking_skepticism",
            title="银行股与大盘背离——内部人不买账",
            score=score,
            severity=severity,
            evidence=(
                f"大盘偏离{spx_z:+.1f}倍，但银行股偏离{kre_z:+.1f}倍"
                + (f"，房地产{vnq_z:+.1f}倍" if abs(vnq_z) > 1 else "")
            ),
            interpretation=(
                "银行股的投资者（包括银行业内部人）是最了解银行风险的群体。"
                "当大盘反弹但银行股不跟，说明最知情的人对复苏持怀疑态度。"
                "这在2008年Bear Stearns被收购后的'假反弹'中尤为明显。"
            ),
        )

    # ── Signal 4: Stealth Safe-Haven Flight ──

    def _stealth_safe_haven(self) -> HiddenSignal | None:
        """Gold and bonds rising while equities stable = smart money quietly exiting."""

        gold_z = self.zscores.get("gold", 0)
        spx_z = self.zscores.get("spx", 0)
        vix = self.vals.get("vix", 20)

        # Gold rising while stocks aren't falling
        if gold_z < 1.0:
            return None

        equity_calm = abs(spx_z) < 1.5
        vix_calm = vix < 22

        if not (equity_calm or vix_calm):
            return None

        score = min(5, gold_z * 1.5)
        severity = "high" if score > 3 else "medium"

        return HiddenSignal(
            signal_id="stealth_safe_haven",
            title="资金悄然流向避险资产",
            score=score,
            severity=severity,
            evidence=(
                f"黄金偏离正常{gold_z:.1f}倍"
                f"，但VIX={vix:.1f}（平静）、股市波动正常"
            ),
            interpretation=(
                "黄金持续走高而股市平静，说明'聪明钱'（机构投资者、央行）"
                "正在悄悄增持避险资产——他们看到了散户看不到的风险。"
                "这不是恐慌性买入（那样VIX会飙升），而是战略性的风险转移。"
            ),
        )

    # ── Signal 5: Policy Emergency Frequency ──

    def _policy_emergency(self) -> HiddenSignal | None:
        """Rapid policy changes = authorities in crisis mode."""

        effr = self.fred.get("fred_effr")
        effr_1m = self._hist_value("fred_effr", 30)
        effr_3m = self._hist_value("fred_effr", 90)
        walcl = self.fred.get("fred_walcl")
        walcl_1m = self._hist_value("fred_walcl", 30)

        if effr is None:
            return None

        emergency_score = 0
        evidence_parts = []

        # Rapid rate changes (multiple cuts in short period)
        if effr_1m is not None and effr_3m is not None:
            cuts_1m = max(0, effr_1m - effr) * 100  # bp cut in 1 month
            cuts_3m = max(0, effr_3m - effr) * 100  # bp cut in 3 months
            if cuts_1m > 25:
                emergency_score += 2
                evidence_parts.append(f"1个月内降息{cuts_1m:.0f}bp")
            if cuts_3m > 75:
                emergency_score += 3
                evidence_parts.append(f"3个月内降息{cuts_3m:.0f}bp")

        # Balance sheet rapid expansion
        if walcl is not None and walcl_1m is not None:
            bs_change = (walcl - walcl_1m) / walcl_1m * 100
            if bs_change > 5:
                emergency_score += 3
                evidence_parts.append(f"资产负债表月扩{bs_change:.1f}%")

        if emergency_score < 2:
            return None

        score = min(7, emergency_score)
        severity = "critical" if score > 5 else "high" if score > 3 else "medium"

        return HiddenSignal(
            signal_id="policy_emergency",
            title="政策进入紧急模式",
            score=score,
            severity=severity,
            evidence="；".join(evidence_parts),
            interpretation=(
                "央行在短期内密集采取非常规行动，说明其内部评估的风险"
                "远高于市场价格反映的水平。决策者拥有非公开信息渠道，"
                "他们的紧急行动本身就是最强的隐藏风险信号。"
            ),
        )

    # ── Signal 6: Cross-Asset Correlation Breakdown ──

    def _correlation_breakdown(self) -> HiddenSignal | None:
        """Normally correlated assets suddenly decoupling = structural stress."""

        # Check if KRW and KOSPI have decoupled (normally highly correlated)
        krw_z = self.zscores.get("krw_usd", 0)
        kospi_z = self.zscores.get("kospi", 0)
        # Normally: KRW weakens → KOSPI falls (both same direction for z-score)
        # Decoupled: one moves but other doesn't

        hsi_z = self.zscores.get("hsi", 0)
        cny_z = self.zscores.get("cny_usd", 0)

        breakdowns = 0
        pairs = []

        # KRW-KOSPI decoupling
        if abs(krw_z) > 1.5 and abs(kospi_z) < 0.5:
            breakdowns += 1
            pairs.append("韩元-韩股")
        elif abs(kospi_z) > 1.5 and abs(krw_z) < 0.5:
            breakdowns += 1
            pairs.append("韩股-韩元")

        # CNY-HSI decoupling
        if abs(cny_z) > 1.5 and abs(hsi_z) < 0.5:
            breakdowns += 1
            pairs.append("人民币-恒生")

        # VIX-SPX decoupling (normally inverse)
        vix_z = self.zscores.get("vix", 0)
        spx_z = self.zscores.get("spx", 0)
        if vix_z > 1.5 and spx_z > 0.5:  # both up = unusual
            breakdowns += 1
            pairs.append("VIX-标普(同涨异常)")

        if breakdowns == 0:
            return None

        score = min(5, breakdowns * 2.5)
        severity = "high" if breakdowns >= 2 else "medium"

        return HiddenSignal(
            signal_id="correlation_breakdown",
            title="跨资产相关性崩塌",
            score=score,
            severity=severity,
            evidence=f"{'、'.join(pairs)}出现异常脱钩",
            interpretation=(
                "正常情况下高度相关的资产突然脱钩，说明市场微观结构"
                "正在断裂——可能是流动性枯竭、套利机制失效、或者某个"
                "市场参与者被迫非理性抛售。这是系统性压力的早期信号。"
            ),
        )

    def _build_narrative(self, signals: list[HiddenSignal], total: float) -> str:
        if not signals:
            return "未检测到显著的隐藏风险信号。"

        high = [s for s in signals if s.severity in ("critical", "high")]
        if total > 15:
            prefix = "⚠️ 多个侧面信号同时指向隐藏的系统性风险正在积累："
        elif total > 8:
            prefix = "部分侧面信号显示，市场价格可能低估了当前的结构性风险："
        else:
            prefix = "有轻微的隐藏风险信号："

        items = [f"「{s.title}」(+{s.score:.0f}分)" for s in high[:3]]
        return prefix + "、".join(items) + "。"
