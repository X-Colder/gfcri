"""
Crisis Distance Engine (v2).

Three-tier indicator system:
  Tier 1: Global systemic — these reaching crisis = worldwide impact
  Tier 2: US core — US market breakdown
  Tier 3: Regional stress — local pressure, may transmit but not root cause

Direction-aware: some indicators are "high=danger" (VIX), others "low=danger" (SPX).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from loguru import logger
from src.models.graph import MacroRiskCausalGraph
from src.i18n import cn_name


@dataclass
class CrisisBenchmark:
    node_id: str
    tier: int  # 1=global systemic, 2=US core, 3=regional
    tier_label: str
    danger_direction: str  # "high" = rising is bad, "low" = falling is bad
    normal: float
    warning: float
    crisis: float
    crises: list[dict]  # historical events


BENCHMARKS = [
    # ===== Tier 1: Global Systemic =====
    CrisisBenchmark("vix", 1, "全球系统性", "high", normal=15, warning=25, crisis=40,
        crises=[{"event": "2008金融危机", "value": 80.9}, {"event": "2020疫情恐慌", "value": 82.7}, {"event": "2022加息冲击", "value": 34.5}]),
    CrisisBenchmark("hyg", 1, "全球系统性", "low", normal=82, warning=72, crisis=60,
        crises=[{"event": "2008信用冻结", "value": 44.1}, {"event": "2020流动性危机", "value": 65.5}]),
    CrisisBenchmark("dxy", 1, "全球系统性", "high", normal=100, warning=107, crisis=114,
        crises=[{"event": "2022强美元危机", "value": 114.8}]),

    # ===== Tier 2: US Core =====
    CrisisBenchmark("spx", 2, "美国核心", "low", normal=5000, warning=4200, crisis=3500,
        crises=[{"event": "2020疫情暴跌", "value": 2237}, {"event": "2022熊市底", "value": 3577}]),
    CrisisBenchmark("ust_10y", 2, "美国核心", "high", normal=3.5, warning=4.5, crisis=5.2,
        crises=[{"event": "2023利率顶", "value": 5.0}, {"event": "2007危机前", "value": 5.3}]),
    CrisisBenchmark("oil_wti", 2, "美国核心", "high", normal=70, warning=95, crisis=120,
        crises=[{"event": "2008油价泡沫", "value": 147}, {"event": "2022俄乌冲击", "value": 130}]),
    CrisisBenchmark("gold", 2, "美国核心", "high", normal=1900, warning=2500, crisis=3000,
        crises=[{"event": "2024避险新高", "value": 2450}]),

    # ===== Tier 3: Regional =====
    CrisisBenchmark("krw_usd", 3, "区域传导", "high", normal=1250, warning=1400, crisis=1550,
        crises=[{"event": "2008韩元崩盘", "value": 1570}, {"event": "2022强美元", "value": 1440}]),
    CrisisBenchmark("kospi", 3, "区域传导", "low", normal=2600, warning=2200, crisis=1800,
        crises=[{"event": "2020暴跌", "value": 1457}, {"event": "2022熊市", "value": 2155}]),
    CrisisBenchmark("hsi", 3, "区域传导", "low", normal=22000, warning=18000, crisis=14000,
        crises=[{"event": "2022中概暴跌", "value": 14597}]),
    CrisisBenchmark("eurusd", 3, "区域传导", "low", normal=1.10, warning=1.02, crisis=0.95,
        crises=[{"event": "2022欧元跌破平价", "value": 0.9536}]),
]

TIER_WEIGHTS = {1: 0.50, 2: 0.30, 3: 0.20}

POLICY_FACTORS = [
    {"name": "美联储降息空间", "description": "利率越高，降息救市空间越大",
     "indicator": "fed_funds", "logic": "buffer", "good": 4.0, "bad": 1.0,
     "interpret": lambda v, s: f"当前利率{v:.2f}%，可降息约{max(0,v-0.5):.0f}次（每次25bp）{'，空间充足' if s>60 else '，空间有限' if s>30 else '，几乎没有降息空间'}"},
    {"name": "美联储扩表空间", "description": "资产负债表越小，QE空间越大",
     "indicator": "fred_walcl", "logic": "buffer_inverse", "good": 4000000, "bad": 9000000,
     "interpret": lambda v, s: f"当前{v/1e6:.1f}万亿美元{'，扩表空间充足' if s>60 else '，扩表空间有限' if s>30 else '，已经很臃肿'}"},
    {"name": "收益率曲线", "description": "倒挂是衰退领先6-18个月的信号",
     "indicator": "fred_t10y2y", "logic": "warning_low", "good": 1.0, "bad": -0.5,
     "interpret": lambda v, s: f"当前利差{v:.2f}%{'，正常' if v>0.3 else '，接近平坦' if v>0 else '，已倒挂——衰退预警信号'}"},
    {"name": "企业信用压力", "description": "BBB利差扩大=企业融资变贵",
     "indicator": "fred_bbb_spread", "logic": "warning_high", "good": 1.2, "bad": 4.0,
     "interpret": lambda v, s: f"当前{v:.2f}%{'，信用市场平静' if s>60 else '，略有压力' if s>30 else '，信用压力显著'}"},
    {"name": "中国货币政策空间", "description": "LPR越高，中国央行降息空间越大",
     "indicator": "cn_lpr_1y", "logic": "buffer", "good": 4.0, "bad": 2.0,
     "interpret": lambda v, s: f"1年期LPR {v:.2f}%{'，降息空间较大' if s>60 else '，空间一般' if s>30 else '，降息空间有限'}"},
    {"name": "消费者信心", "description": "信心崩塌→消费断崖→经济衰退",
     "indicator": "fred_umcsent", "logic": "warning_low", "good": 80, "bad": 50,
     "interpret": lambda v, s: f"当前{v:.1f}{'，消费意愿健康' if s>60 else '，消费者谨慎' if s>30 else '，消费者极度悲观，历史低位'}"},
]


@dataclass
class CrisisDistance:
    node_id: str
    name: str
    tier: int
    tier_label: str
    current_value: float
    warning_value: float
    crisis_value: float
    worst_event: str
    worst_value: float
    distance_pct: float  # 0=normal, 100=at crisis
    status: str  # normal/warning/crisis
    unit: str

    def to_dict(self):
        return {k: round(v, 2) if isinstance(v, float) else v for k, v in self.__dict__.items()}


@dataclass
class PolicyAssessment:
    name: str
    description: str
    status: str
    score: float
    detail: str

    def to_dict(self):
        return {"name": self.name, "description": self.description, "status": self.status, "score": round(self.score), "detail": self.detail}


@dataclass
class CrisisReport:
    overall_distance: float
    overall_probability: str
    tier1_distance: float
    tier2_distance: float
    tier3_distance: float
    distances: list[CrisisDistance]
    policies: list[PolicyAssessment]
    closest_indicators: list[dict]

    def to_dict(self):
        return {
            "overall_distance": round(self.overall_distance, 1),
            "overall_probability": self.overall_probability,
            "tier1_distance": round(self.tier1_distance, 1),
            "tier2_distance": round(self.tier2_distance, 1),
            "tier3_distance": round(self.tier3_distance, 1),
            "distances": [d.to_dict() for d in self.distances],
            "policies": [p.to_dict() for p in self.policies],
            "closest_indicators": self.closest_indicators,
        }


class CrisisDistanceEngine:

    def __init__(self, graph: MacroRiskCausalGraph, extra_data: dict[str, float] | None = None):
        self.graph = graph
        self.extra = extra_data or {}

    def compute(self) -> CrisisReport:
        distances = []

        for bench in BENCHMARKS:
            node = self.graph.nodes.get(bench.node_id)
            current = node.current_value if node and node.current_value else self.extra.get(bench.node_id)
            if current is None:
                continue

            unit = node.unit if node else ""

            if bench.danger_direction == "high":
                # Higher is worse (VIX, DXY, oil, rates, KRW)
                range_total = bench.crisis - bench.normal
                if range_total > 0:
                    pct = max(0, min(100, (current - bench.normal) / range_total * 100))
                else:
                    pct = 0
            else:
                # Lower is worse (SPX, HYG, KOSPI, HSI, EURUSD)
                range_total = bench.normal - bench.crisis
                if range_total > 0:
                    pct = max(0, min(100, (bench.normal - current) / range_total * 100))
                else:
                    pct = 0

            if pct >= 80:
                status = "crisis"
            elif pct >= 40:
                status = "warning"
            else:
                status = "normal"

            worst = max(bench.crises, key=lambda c: c["value"] if bench.danger_direction == "high" else -c["value"])

            distances.append(CrisisDistance(
                node_id=bench.node_id, name=cn_name(bench.node_id),
                tier=bench.tier, tier_label=bench.tier_label,
                current_value=current,
                warning_value=bench.warning, crisis_value=bench.crisis,
                worst_event=worst["event"], worst_value=worst["value"],
                distance_pct=pct, status=status, unit=unit,
            ))

        # Tier averages
        tier_avgs = {}
        for t in [1, 2, 3]:
            tier_dists = [d.distance_pct for d in distances if d.tier == t]
            tier_avgs[t] = sum(tier_dists) / len(tier_dists) if tier_dists else 0

        overall = sum(tier_avgs.get(t, 0) * w for t, w in TIER_WEIGHTS.items())

        if overall > 70: prob = "critical"
        elif overall > 45: prob = "high"
        elif overall > 25: prob = "medium"
        else: prob = "low"

        # Policy assessment
        policies = []
        for pf in POLICY_FACTORS:
            val = None
            node = self.graph.nodes.get(pf["indicator"])
            if node and node.current_value:
                val = node.current_value
            else:
                val = self.extra.get(pf["indicator"])
            if val is None:
                continue

            good, bad = pf["good"], pf["bad"]
            logic = pf["logic"]

            if logic == "buffer":
                score = max(0, min(100, (val - bad) / (good - bad) * 100))
            elif logic == "buffer_inverse":
                score = max(0, min(100, (bad - val) / (bad - good) * 100))
            elif logic == "warning_low":
                score = max(0, min(100, (val - bad) / (good - bad) * 100))
            elif logic == "warning_high":
                score = max(0, min(100, (bad - val) / (bad - good) * 100))
            else:
                score = 50

            status = "buffer" if score > 60 else "neutral" if score > 30 else "warning"
            detail = pf["interpret"](val, score)
            policies.append(PolicyAssessment(name=pf["name"], description=pf["description"], status=status, score=score, detail=detail))

        distances.sort(key=lambda d: (d.tier, -d.distance_pct))
        closest = [{"name": d.name, "tier_label": d.tier_label, "distance": d.distance_pct, "status": d.status}
                   for d in sorted(distances, key=lambda d: -d.distance_pct)[:5]]

        return CrisisReport(
            overall_distance=overall, overall_probability=prob,
            tier1_distance=tier_avgs.get(1, 0), tier2_distance=tier_avgs.get(2, 0), tier3_distance=tier_avgs.get(3, 0),
            distances=distances, policies=policies, closest_indicators=closest,
        )
