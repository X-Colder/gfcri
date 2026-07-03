# 全球宏观风险传导监测Agent — 因果图深度融合设计方案

## 目录

1. 核心概念映射
2. 因果图数据结构设计
3. 因果推理引擎设计
4. 动态因果发现机制
5. LLM与因果图引擎的协同设计
6. 存储层升级方案
7. 输出层升级方案
8. Python实现方案与库选型
9. 完整架构图

---

## 一、核心概念映射

### 1.1 SCM概念到金融风险场景的映射表

| SCM概念 | 形式化定义 | 金融风险场景映射 | 具体示例 |
|---------|-----------|----------------|---------|
| **节点（Node）** | 随机变量 $V_i$ | 可观测金融变量 / 宏观指标 | DXY指数、10Y美债收益率、KOSPI、三星CDS |
| **有向边（Edge）** | $V_i \rightarrow V_j$，$V_j = f_j(V_i, \epsilon_j)$ | 因果传导关系 + 时滞 | 美元升值→韩元贬值（滞后1-5日） |
| **结构方程（SEM）** | $V_j := f_j(\text{Pa}(V_j), \epsilon_j)$ | 变量的生成机制 | $\text{KRW} := \alpha \cdot \text{DXY} + \beta \cdot \text{CA\_Balance} + \epsilon$ |
| **外生噪声（$\epsilon$）** | 独立噪声项 | 不可观测的随机冲击 | 突发地缘政治事件、黑天鹅 |
| **do算子（do-calculus）** | $P(Y \| \text{do}(X=x))$ | 政策干预 / 人工压力测试 | 美联储加息100bp对新兴市场的净因果效应 |
| **反事实（Counterfactual）** | $Y_{x'}$ | 历史复盘 / 情景分析 | "如果2024年6月没有降息，今日资产价格如何？" |
| **混淆变量（Confounder）** | 同时影响X和Y的变量Z | 虚假相关检测 | 全球流动性同时影响美元和新兴市场，制造虚假相关 |
| **d-separation** | 图中的条件独立性判断 | 传导路径的阻断检测 | 当控制美元指数后，美债收益率对韩元的直接效应消失 |
| **后门准则（Backdoor）** | 识别有效调整集 | 净因果效应估计 | 剔除VIX混淆后，计算韩元贬值对半导体股的真实效应 |
| **工具变量（IV）** | 满足排他性约束的变量 | 因果识别策略 | 用OPEC产量决定作为油价的工具变量 |
| **潜变量（Latent）** | 不可观测的隐变量 | 市场情绪、系统性风险因子 | "全球风险厌恶度"（无法直接观测，通过VIX/CDX推断） |
| **结构断裂（Regime）** | 结构方程参数突变 | 市场制度转换 | 2022年俄乌冲突后，能源→欧元的结构方程发生突变 |

### 1.2 五条线性链的局限性分析

现有设计将传导关系建模为独立的线性链，存在以下根本性问题：

```
【现有设计问题】

链1: DXY → KRW → 资本外流          (忽略：CA顺差对KRW的对冲效应)
链2: KOSPI → 保证金强平              (忽略：KOSPI下跌的原因可能是链1触发)
链3: ORCL_CDS → AI企业债            (忽略：利率水平是共同混淆变量)
链4: 苹果/微软砍单 → 存储芯片价格    (忽略：NAND供给侧的独立冲击)
链5: 10Y_UST → 全球资产重定价        (忽略：反馈环：全球抛售→美债上行)

核心缺陷：
- 链与链之间的交叉效应被完全忽略
- 无法识别共同驱动因子（混淆变量）
- 无法量化干预效果 vs 相关效果
- 无法处理反馈环（金融系统天然存在）
- 阈值是静态的，不随结构变化更新
```

---

## 二、因果图数据结构设计

### 2.1 图类型选择：有向循环因果图（DCG）+ 时间展开（SVAR）

金融系统存在反馈环（如：美债上行→美元走强→新兴市场抛售美债→美债进一步上行），纯DAG无法表达。采用以下混合策略：

```
【图类型策略】

当前时点内：有向无环图（DAG）— 同一时刻内变量有明确先后顺序
跨时滞关系：时间展开DAG（SVAR）— X_{t-k} → Y_t 天然无环
反馈环处理：虚拟拆分 — X_t → Y_t → X_{t+1}（时间轴展开消除环路）

最终形态：TDAG（Temporal DAG）
每条边携带时滞参数 lag ∈ {0, 1, 2, ..., 30} 天
```

### 2.2 节点分类体系

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
import numpy as np

class NodeType(Enum):
    """节点类型分类"""
    OBSERVABLE     = "observable"      # 可直接观测的市场变量
    LATENT         = "latent"          # 潜变量（需从观测变量推断）
    INTERVENTION   = "intervention"    # 干预变量（政策变量）
    EXTERNAL_SHOCK = "external_shock"  # 外生冲击（地缘、自然灾害）
    STRUCTURAL     = "structural"      # 结构性变量（制度、监管）

class AssetClass(Enum):
    FX         = "fx"
    RATES      = "rates"
    EQUITY     = "equity"
    CREDIT     = "credit"
    COMMODITY  = "commodity"
    MACRO      = "macro"
    SENTIMENT  = "sentiment"

@dataclass
class CausalNode:
    """因果图节点定义"""
    # 标识
    node_id: str                    # 唯一标识符，如 "DXY", "KRW_USD"
    display_name: str               # 展示名称
    description: str                # 含义描述
    
    # 分类
    node_type: NodeType
    asset_class: AssetClass
    geography: str                  # "US", "KR", "GLOBAL", "EM"
    
    # 观测属性
    data_source: str                # 数据来源，如 "bloomberg:DXY Index"
    update_frequency: str           # "1d", "1h", "1w"
    unit: str                       # "index", "bps", "pct_change"
    
    # 统计属性（动态更新）
    current_value: Optional[float] = None
    value_zscore: Optional[float] = None        # 标准化偏差
    historical_mean: Optional[float] = None
    historical_std: Optional[float] = None
    
    # 状态标志
    is_anomalous: bool = False       # 是否处于异常状态
    anomaly_score: float = 0.0       # 异常程度 [0, 1]
    last_updated: Optional[str] = None
    
    # 因果属性
    is_root_cause_candidate: bool = False  # 是否为潜在根因节点
    intervention_cost: Optional[float] = None  # 政策干预的"成本"估计

# 预定义核心节点集
CORE_NODES = {
    # 美元体系
    "DXY":          CausalNode("DXY", "美元指数", "美元对一篮子货币", 
                               NodeType.OBSERVABLE, AssetClass.FX, "US",
                               "bloomberg:DXY Index", "1d", "index"),
    "UST_10Y":      CausalNode("UST_10Y", "美国10年期国债收益率", "美债基准利率",
                               NodeType.OBSERVABLE, AssetClass.RATES, "US",
                               "bloomberg:USGG10YR Index", "1d", "pct"),
    "UST_2Y":       CausalNode("UST_2Y", "美国2年期国债收益率", "美债短端利率",
                               NodeType.OBSERVABLE, AssetClass.RATES, "US",
                               "bloomberg:USGG2YR Index", "1d", "pct"),
    "FED_FUNDS":    CausalNode("FED_FUNDS", "联邦基金利率", "美联储政策利率",
                               NodeType.INTERVENTION, AssetClass.RATES, "US",
                               "bloomberg:FDTR Index", "event", "pct"),
    
    # 全球流动性
    "VIX":          CausalNode("VIX", "VIX恐慌指数", "市场隐含波动率",
                               NodeType.OBSERVABLE, AssetClass.SENTIMENT, "GLOBAL",
                               "bloomberg:VIX Index", "1d", "index"),
    "GLOBAL_LIQD":  CausalNode("GLOBAL_LIQD", "全球流动性条件", "潜在流动性因子",
                               NodeType.LATENT, AssetClass.MACRO, "GLOBAL",
                               "derived:pca(m2_us, m2_eu, m2_cn)", "1w", "zscore"),
    
    # 韩国/新兴市场
    "KRW_USD":      CausalNode("KRW_USD", "韩元/美元汇率", "韩元兑美元",
                               NodeType.OBSERVABLE, AssetClass.FX, "KR",
                               "bloomberg:USDKRW Curncy", "1d", "rate"),
    "KOSPI":        CausalNode("KOSPI", "韩国综合指数", "韩国股票市场",
                               NodeType.OBSERVABLE, AssetClass.EQUITY, "KR",
                               "bloomberg:KOSPI Index", "1d", "index"),
    "KR_CDS_5Y":    CausalNode("KR_CDS_5Y", "韩国主权CDS(5Y)", "韩国主权信用风险",
                               NodeType.OBSERVABLE, AssetClass.CREDIT, "KR",
                               "bloomberg:CKOREA CDS USD SR 5Y", "1d", "bps"),
    "KR_CA":        CausalNode("KR_CA", "韩国经常账户余额", "贸易顺差/逆差",
                               NodeType.OBSERVABLE, AssetClass.MACRO, "KR",
                               "bloomberg:KOCABAL Index", "1m", "usd_bn"),
    
    # 半导体/科技
    "SOX":          CausalNode("SOX", "费城半导体指数", "全球半导体股票",
                               NodeType.OBSERVABLE, AssetClass.EQUITY, "US",
                               "bloomberg:SOX Index", "1d", "index"),
    "DRAM_SPOT":    CausalNode("DRAM_SPOT", "DRAM现货价格", "DDR5 32GB现货",
                               NodeType.OBSERVABLE, AssetClass.COMMODITY, "GLOBAL",
                               "dramexchange:DDR5_32GB_SPOT", "1w", "usd"),
    "NAND_SPOT":    CausalNode("NAND_SPOT", "NAND闪存现货价格", "TLC 256Gb现货",
                               NodeType.OBSERVABLE, AssetClass.COMMODITY, "GLOBAL",
                               "dramexchange:TLC_256GB_SPOT", "1w", "usd"),
    
    # AI/科技信贷
    "ORCL_CDS":     CausalNode("ORCL_CDS", "甲骨文CDS(5Y)", "AI基础设施代表企业信用",
                               NodeType.OBSERVABLE, AssetClass.CREDIT, "US",
                               "bloomberg:ORCL CDS USD SR 5Y", "1d", "bps"),
    "AI_CAPEX":     CausalNode("AI_CAPEX", "AI资本开支意愿", "大科技AI投入潜变量",
                               NodeType.LATENT, AssetClass.MACRO, "US",
                               "derived:nlp(earnings_call)", "1q", "zscore"),
    
    # 大宗商品
    "OIL_WTI":      CausalNode("OIL_WTI", "WTI原油价格", "原油基准价格",
                               NodeType.OBSERVABLE, AssetClass.COMMODITY, "GLOBAL",
                               "bloomberg:CL1 Comdty", "1d", "usd"),
    
    # 宏观结构
    "US_RECESSION_PROB": CausalNode("US_RECESSION_PROB", "美国衰退概率", "12个月衰退概率",
                                     NodeType.LATENT, AssetClass.MACRO, "US",
                                     "derived:yield_curve+leading_idx", "1w", "prob"),
}
```

### 2.3 边（因果关系）定义

```python
from typing import Callable, Tuple
from scipy import stats

class EdgeMechanism(Enum):
    """传导机制类型"""
    DIRECT_PRICING  = "direct_pricing"    # 直接定价关系（套利驱动）
    FLOW_CHANNEL    = "flow_channel"      # 资本流动渠道
    CREDIT_CHANNEL  = "credit_channel"    # 信贷收缩/扩张渠道
    CONFIDENCE      = "confidence"        # 情绪/信心渠道
    FUNDAMENTAL     = "fundamental"       # 基本面传导
    REGULATORY      = "regulatory"        # 监管政策渠道
    SUPPLY_CHAIN    = "supply_chain"      # 供应链渠道

class ActivationCondition(Enum):
    """激活条件类型"""
    ALWAYS          = "always"            # 始终激活
    THRESHOLD       = "threshold"         # 阈值激活
    REGIME          = "regime"            # 制度条件激活
    CONJUNCTION     = "conjunction"       # 多条件同时满足

@dataclass
class ActivationRule:
    """边激活规则"""
    condition_type: ActivationCondition
    
    # 阈值条件
    threshold_node_id: Optional[str] = None   # 监控哪个节点
    threshold_value: Optional[float] = None
    threshold_direction: Optional[str] = None  # "above", "below"
    
    # 制度条件
    regime_name: Optional[str] = None         # 如 "risk_off", "dollar_squeeze"
    
    # 复合条件（conjunction）
    sub_conditions: List['ActivationRule'] = field(default_factory=list)
    
    def evaluate(self, graph_state: Dict[str, Any]) -> bool:
        """评估激活条件是否满足"""
        if self.condition_type == ActivationCondition.ALWAYS:
            return True
        elif self.condition_type == ActivationCondition.THRESHOLD:
            val = graph_state.get(self.threshold_node_id, {}).get("current_value")
            if val is None:
                return False
            if self.threshold_direction == "above":
                return val > self.threshold_value
            else:
                return val < self.threshold_value
        elif self.condition_type == ActivationCondition.CONJUNCTION:
            return all(c.evaluate(graph_state) for c in self.sub_conditions)
        return False

@dataclass
class CausalEdge:
    """因果图边定义"""
    # 标识
    edge_id: str
    source_node: str           # 原因节点ID
    target_node: str           # 结果节点ID
    
    # 因果强度（结构方程系数）
    causal_strength: float     # [-1, 1]，正值=同向，负值=反向
    strength_confidence: float # 估计置信度 [0, 1]
    strength_ci_lower: float   # 95% CI下界
    strength_ci_upper: float   # 95% CI上界
    
    # 时间属性
    min_lag_days: int          # 最短传导时滞（天）
    max_lag_days: int          # 最长传导时滞（天）
    peak_lag_days: int         # 效应最强的时滞
    effect_decay: str          # 效应衰减模式: "exponential", "step", "sustained"
    
    # 机制描述
    mechanism: EdgeMechanism
    mechanism_description: str  # 自然语言描述传导机制
    
    # 非线性属性
    is_nonlinear: bool = False
    nonlinear_type: Optional[str] = None  # "threshold", "asymmetric", "regime_switch"
    # 非线性函数：输入(source_value, regime) → 输出传导强度修正因子
    nonlinear_modifier: Optional[Callable] = None
    
    # 激活条件
    activation_rule: ActivationRule = field(
        default_factory=lambda: ActivationRule(ActivationCondition.ALWAYS)
    )
    
    # 混淆控制
    known_confounders: List[str] = field(default_factory=list)  # 已知混淆变量ID
    is_backdoor_adjusted: bool = False     # 是否已做后门调整
    
    # 置信度与验证
    evidence_type: str = "theoretical"    # "theoretical", "statistical", "llm_inferred"
    last_validated_date: Optional[str] = None
    validation_p_value: Optional[float] = None
    num_supporting_events: int = 0        # 历史事件验证次数
    
    # 图谱版本
    created_version: str = "v1.0"
    last_modified_version: str = "v1.0"
    is_deprecated: bool = False
    
    @property
    def is_active(self) -> bool:
        """当前边是否有效"""
        return not self.is_deprecated and self.strength_confidence > 0.3
    
    def adjusted_strength(self, source_value: float, regime: str) -> float:
        """考虑非线性后的有效传导强度"""
        base = self.causal_strength
        if self.is_nonlinear and self.nonlinear_modifier:
            modifier = self.nonlinear_modifier(source_value, regime)
            return base * modifier
        return base
```

### 2.4 完整因果图定义与预定义边

```python
import networkx as nx
import json
from datetime import datetime

@dataclass 
class MacroRiskCausalGraph:
    """宏观风险因果图（主图结构）"""
    graph_id: str
    version: str
    created_at: str
    description: str
    
    # 核心存储
    nodes: Dict[str, CausalNode] = field(default_factory=dict)
    edges: Dict[str, CausalEdge] = field(default_factory=dict)
    
    # NetworkX后端（用于图算法）
    _nx_graph: nx.DiGraph = field(default_factory=nx.DiGraph, repr=False)
    
    # 当前图状态
    current_regime: str = "normal"        # 当前市场制度
    regime_history: List[Dict] = field(default_factory=list)
    
    def add_node(self, node: CausalNode) -> None:
        self.nodes[node.node_id] = node
        self._nx_graph.add_node(
            node.node_id,
            node_type=node.node_type.value,
            asset_class=node.asset_class.value,
            geo=node.geography
        )
    
    def add_edge(self, edge: CausalEdge) -> None:
        self.edges[edge.edge_id] = edge
        self._nx_graph.add_edge(
            edge.source_node,
            edge.target_node,
            edge_id=edge.edge_id,
            strength=edge.causal_strength,
            confidence=edge.strength_confidence,
            lag=edge.peak_lag_days,
            mechanism=edge.mechanism.value
        )
    
    def get_causal_parents(self, node_id: str) -> List[str]:
        """获取直接因果父节点"""
        return list(self._nx_graph.predecessors(node_id))
    
    def get_causal_children(self, node_id: str) -> List[str]:
        """获取直接因果子节点"""
        return list(self._nx_graph.successors(node_id))
    
    def find_all_causal_paths(
        self, source: str, target: str, max_length: int = 6
    ) -> List[List[str]]:
        """查找所有从source到target的有向路径"""
        return list(nx.all_simple_paths(
            self._nx_graph, source, target, cutoff=max_length
        ))
    
    def are_d_separated(
        self, x: str, y: str, conditioning_set: List[str]
    ) -> bool:
        """d-separation检验：给定条件集，X和Y是否条件独立"""
        return nx.d_separated(
            self._nx_graph, {x}, {y}, set(conditioning_set)
        )
    
    def to_dict(self) -> Dict:
        """序列化为字典（用于存储）"""
        return {
            "graph_id": self.graph_id,
            "version": self.version,
            "created_at": self.created_at,
            "nodes": {k: vars(v) for k, v in self.nodes.items()},
            "edges": {k: self._edge_to_dict(v) for k, v in self.edges.items()},
            "current_regime": self.current_regime,
        }
    
    def _edge_to_dict(self, edge: CausalEdge) -> Dict:
        d = vars(edge).copy()
        d["mechanism"] = edge.mechanism.value
        d["activation_rule"] = vars(edge.activation_rule)
        d.pop("nonlinear_modifier", None)  # 函数不序列化
        return d


def build_initial_causal_graph() -> MacroRiskCausalGraph:
    """构建初始宏观风险因果图（替代原5条线性链）"""
    
    graph = MacroRiskCausalGraph(
        graph_id="gfcri_v1",
        version="v1.0",
        created_at=datetime.now().isoformat(),
        description="全球宏观风险传导因果图——初始版本"
    )
    
    # 添加所有节点
    for node in CORE_NODES.values():
        graph.add_node(node)
    
    # ----------------------------------------------------------------
    # 定义因果边（替代5条线性链，构建完整DAG）
    # ----------------------------------------------------------------
    
    edges_to_add = [
        
        # === 层1：美联储政策 → 利率结构 ===
        CausalEdge(
            edge_id="fed_ust10y",
            source_node="FED_FUNDS", target_node="UST_10Y",
            causal_strength=0.65, strength_confidence=0.85,
            strength_ci_lower=0.50, strength_ci_upper=0.78,
            min_lag_days=0, max_lag_days=5, peak_lag_days=1,
            effect_decay="exponential",
            mechanism=EdgeMechanism.DIRECT_PRICING,
            mechanism_description="联邦基金利率直接锚定短端，通过预期传导至10年期",
            known_confounders=["GLOBAL_LIQD"],
        ),
        CausalEdge(
            edge_id="fed_ust2y",
            source_node="FED_FUNDS", target_node="UST_2Y",
            causal_strength=0.90, strength_confidence=0.95,
            strength_ci_lower=0.85, strength_ci_upper=0.95,
            min_lag_days=0, max_lag_days=2, peak_lag_days=0,
            effect_decay="sustained",
            mechanism=EdgeMechanism.DIRECT_PRICING,
            mechanism_description="政策利率直接决定2年期国债定价",
            known_confounders=[],
        ),
        
        # === 层2：利率/美元互动 ===
        CausalEdge(
            edge_id="ust10y_dxy",
            source_node="UST_10Y", target_node="DXY",
            causal_strength=0.55, strength_confidence=0.75,
            strength_ci_lower=0.40, strength_ci_upper=0.68,
            min_lag_days=0, max_lag_days=3, peak_lag_days=1,
            effect_decay="exponential",
            mechanism=EdgeMechanism.FLOW_CHANNEL,
            mechanism_description="美债实际收益率上行吸引全球资本流入，推升美元",
            known_confounders=["GLOBAL_LIQD", "VIX"],
        ),
        CausalEdge(
            edge_id="vix_dxy",
            source_node="VIX", target_node="DXY",
            causal_strength=0.45, strength_confidence=0.70,
            strength_ci_lower=0.30, strength_ci_upper=0.60,
            min_lag_days=0, max_lag_days=2, peak_lag_days=0,
            effect_decay="step",
            mechanism=EdgeMechanism.CONFIDENCE,
            mechanism_description="风险厌恶上升触发美元避险需求（美元微笑理论右端）",
            is_nonlinear=True,
            nonlinear_type="threshold",
            # VIX>30时效应翻倍
            nonlinear_modifier=lambda v, r: 2.0 if v > 30 else 1.0,
            activation_rule=ActivationRule(ActivationCondition.ALWAYS),
        ),
        
        # === 层3：美元 → 新兴市场（核心传导，原链1升级） ===
        CausalEdge(
            edge_id="dxy_krw",
            source_node="DXY", target_node="KRW_USD",
            causal_strength=-0.72, strength_confidence=0.88,
            strength_ci_lower=-0.82, strength_ci_upper=-0.60,
            min_lag_days=0, max_lag_days=5, peak_lag_days=1,
            effect_decay="exponential",
            mechanism=EdgeMechanism.DIRECT_PRICING,
            mechanism_description="美元升值直接压低韩元（DXY与KRW负相关）",
            known_confounders=["KR_CA"],
            is_nonlinear=True,
            nonlinear_type="asymmetric",
            # 韩元贬值期（DXY上行）效应比升值期更强（外汇市场不对称性）
            nonlinear_modifier=lambda v, r: 1.3 if r == "dollar_squeeze" else 1.0,
            activation_rule=ActivationRule(ActivationCondition.ALWAYS),
        ),
        CausalEdge(
            edge_id="kr_ca_krw",
            source_node="KR_CA", target_node="KRW_USD",
            causal_strength=-0.35, strength_confidence=0.65,
            strength_ci_lower=-0.50, strength_ci_upper=-0.18,
            min_lag_days=20, max_lag_days=60, peak_lag_days=30,
            effect_decay="sustained",
            mechanism=EdgeMechanism.FUNDAMENTAL,
            mechanism_description="经常账户顺差提供韩元支撑，对冲美元压力（混淆变量）",
            known_confounders=[],
        ),
        
        # === 层4：韩元/KOSPI互动（原链2升级） ===
        CausalEdge(
            edge_id="krw_kospi",
            source_node="KRW_USD", target_node="KOSPI",
            causal_strength=-0.50, strength_confidence=0.78,
            strength_ci_lower=-0.65, strength_ci_upper=-0.33,
            min_lag_days=0, max_lag_days=3, peak_lag_days=1,
            effect_decay="exponential",
            mechanism=EdgeMechanism.FLOW_CHANNEL,
            mechanism_description="韩元贬值触发外资撤离韩国股市（反向流动）",
            known_confounders=["VIX", "GLOBAL_LIQD"],
            is_nonlinear=True,
            nonlinear_type="threshold",
            # 韩元跌破1550时，外资抛售加速（原链1的阈值在此体现）
            nonlinear_modifier=lambda v, r: 2.5 if v > 1550 else 1.0,
            activation_rule=ActivationRule(ActivationCondition.ALWAYS),
        ),
        CausalEdge(
            edge_id="dxy_kospi",  # 美元对KOSPI的直接效应（非经KRW）
            source_node="DXY", target_node="KOSPI",
            causal_strength=-0.30, strength_confidence=0.60,
            strength_ci_lower=-0.45, strength_ci_upper=-0.12,
            min_lag_days=1, max_lag_days=5, peak_lag_days=2,
            effect_decay="exponential",
            mechanism=EdgeMechanism.FLOW_CHANNEL,
            mechanism_description="美元走强直接影响韩国出口前景预期，独立于汇率渠道",
            known_confounders=["KRW_USD"],  # KRW是中介变量，需要区分直接/间接效应
        ),
        
        # === 层5：KOSPI → 半导体（原链2的下游） ===
        CausalEdge(
            edge_id="kospi_sox",
            source_node="KOSPI", target_node="SOX",
            causal_strength=0.45, strength_confidence=0.70,
            strength_ci_lower=0.28, strength_ci_upper=0.60,
            min_lag_days=0, max_lag_days=2, peak_lag_days=0,
            effect_decay="exponential",
            mechanism=EdgeMechanism.CONFIDENCE,
            mechanism_description="KOSPI崩跌（三星等权重股）直接拖累SOX",
            known_confounders=["VIX"],
            is_nonlinear=True,
            nonlinear_type="threshold",
            # KOSPI跌15%触发保证金强平级联（原链2阈值）
            nonlinear_modifier=lambda v, r: 3.0 if r == "margin_call_cascade" else 1.0,
        ),
        CausalEdge(
            edge_id="sox_dram",
            source_node="SOX", target_node="DRAM_SPOT",
            causal_strength=0.55, strength_confidence=0.68,
            strength_ci_lower=0.38, strength_ci_upper=0.70,
            min_lag_days=30, max_lag_days=180, peak_lag_days=90,
            effect_decay="sustained",
            mechanism=EdgeMechanism.SUPPLY_CHAIN,
            mechanism_description="半导体股崩跌反映需求端预期恶化，先行于现货价格6个月",
            known_confounders=["AI_CAPEX"],
        ),
        
        # === 层6：AI信贷渠道（原链3升级） ===
        CausalEdge(
            edge_id="ust10y_orcl_cds",
            source_node="UST_10Y", target_node="ORCL_CDS",
            causal_strength=0.60, strength_confidence=0.80,
            strength_ci_lower=0.45, strength_ci_upper=0.73,
            min_lag_days=1, max_lag_days=10, peak_lag_days=3,
            effect_decay="exponential",
            mechanism=EdgeMechanism.CREDIT_CHANNEL,
            mechanism_description="无风险利率上行直接压缩企业信用利差，推升CDS",
            known_confounders=["GLOBAL_LIQD"],
            # 这里揭示原链3的混淆：利率是CDS变化的共同驱动！
        ),
        CausalEdge(
            edge_id="orcl_cds_ai_capex",
            source_node="ORCL_CDS", target_node="AI_CAPEX",
            causal_strength=-0.65, strength_confidence=0.72,
            strength_ci_lower=-0.78, strength_ci_upper=-0.50,
            min_lag_days=30, max_lag_days=120, peak_lag_days=60,
            effect_decay="sustained",
            mechanism=EdgeMechanism.CREDIT_CHANNEL,
            mechanism_description="AI基础设施融资成本上升压制资本开支意愿",
            known_confounders=["FED_FUNDS"],
            activation_rule=ActivationRule(
                condition_type=ActivationCondition.THRESHOLD,
                threshold_node_id="ORCL_CDS",
                threshold_value=400,
                threshold_direction="above"  # 原链3的400bp阈值
            ),
        ),
        CausalEdge(
            edge_id="ai_capex_dram",
            source_node="AI_CAPEX", target_node="DRAM_SPOT",
            causal_strength=0.70, strength_confidence=0.75,
            strength_ci_lower=0.55, strength_ci_upper=0.83,
            min_lag_days=60, max_lag_days=180, peak_lag_days=90,
            effect_decay="sustained",
            mechanism=EdgeMechanism.SUPPLY_CHAIN,
            mechanism_description="AI训练集群扩张是DRAM/HBM需求的主要驱动",
            known_confounders=["SOX"],
        ),
        
        # === 层7：终端需求砍单渠道（原链4升级） ===
        CausalEdge(
            edge_id="ai_capex_nand",
            source_node="AI_CAPEX", target_node="NAND_SPOT",
            causal_strength=0.50, strength_confidence=0.65,
            strength_ci_lower=0.32, strength_ci_upper=0.65,
            min_lag_days=60, max_lag_days=180, peak_lag_days=120,
            effect_decay="sustained",
            mechanism=EdgeMechanism.SUPPLY_CHAIN,
            mechanism_description="AI服务器扩张驱动企业SSD需求",
            known_confounders=["SOX"],
        ),
        
        # === 层8：美债 → 全球资产（原链5升级） ===
        CausalEdge(
            edge_id="ust10y_vix",
            source_node="UST_10Y", target_node="VIX",
            causal_strength=0.50, strength_confidence=0.72,
            strength_ci_lower=0.35, strength_ci_upper=0.63,
            min_lag_days=0, max_lag_days=5, peak_lag_days=1,
            effect_decay="exponential",
            mechanism=EdgeMechanism.CONFIDENCE,
            mechanism_description="美债急速上行触发全球资产组合调整恐慌",
            is_nonlinear=True,
            nonlinear_type="threshold",
            nonlinear_modifier=lambda v, r: 3.0 if v > 5.0 else 1.0,  # 5%阈值
            activation_rule=ActivationRule(ActivationCondition.ALWAYS),
        ),
        CausalEdge(
            edge_id="ust10y_kr_cds",
            source_node="UST_10Y", target_node="KR_CDS_5Y",
            causal_strength=0.55, strength_confidence=0.75,
            strength_ci_lower=0.40, strength_ci_upper=0.68,
            min_lag_days=1, max_lag_days=7, peak_lag_days=2,
            effect_decay="exponential",
            mechanism=EdgeMechanism.CREDIT_CHANNEL,
            mechanism_description="全球基准利率上行推升所有主权CDS",
            known_confounders=["VIX", "DXY"],
        ),
        
        # === 反馈环（时间展开后的跨期边） ===
        CausalEdge(
            edge_id="vix_ust10y_feedback",
            source_node="VIX", target_node="UST_10Y",
            causal_strength=-0.30, strength_confidence=0.60,
            strength_ci_lower=-0.45, strength_ci_upper=-0.12,
            min_lag_days=1, max_lag_days=10, peak_lag_days=3,
            effect_decay="exponential",
            mechanism=EdgeMechanism.FLOW_CHANNEL,
            mechanism_description="恐慌时资金涌入美债避险，压低10Y收益率（负反馈）",
            # 注：这是跨期t → t+3的边，不构成同期循环
        ),
    ]
    
    for edge in edges_to_add:
        graph.add_edge(edge)
    
    return graph
```

---

## 三、因果推理引擎设计

### 3.1 引擎总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    因果推理引擎 (CausalReasoningEngine)           │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  观察推理模块    │  │  干预推理模块    │  │  反事实推理模块  │ │
│  │ ObservationalR  │  │ InterventionalR │  │ CounterfactualR │ │
│  │                 │  │                 │  │                 │ │
│  │ P(Y|X=x)        │  │ P(Y|do(X=x))   │  │ P(Y_x'|X=x,Y=y)│ │
│  │ 条件概率        │  │ do-calculus     │  │ 孪生网络法      │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│           │                    │                    │           │
│           └────────────────────┼────────────────────┘           │
│                                │                                 │
│  ┌─────────────────────────────▼──────────────────────────────┐ │
│  │                   路径分析模块 (PathAnalyzer)                │ │
│  │  - 枚举所有因果路径                                          │ │
│  │  - 计算路径强度（边权重乘积）                                 │ │
│  │  - 识别主路径 vs 次路径                                      │ │
│  │  - d-separation检验                                         │ │
│  └─────────────────────────────┬──────────────────────────────┘ │
│                                │                                 │
│  ┌─────────────────────────────▼──────────────────────────────┐ │
│  │                混淆检测模块 (ConfoundingDetector)            │ │
│  │  - 后门路径识别                                              │ │
│  │  - 有效调整集计算                                            │ │
│  │  - 虚假相关警告                                              │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 四种推理模块实现

```python
import dowhy
from dowhy import CausalModel
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class InferenceResult:
    """推理结果统一数据结构"""
    inference_type: str            # "observational", "interventional", "counterfactual"
    query: str                     # 自然语言查询描述
    source_node: str
    target_node: str
    
    # 数值结果
    point_estimate: float          # 点估计
    ci_lower: float                # 置信区间下界
    ci_upper: float                # 置信区间上界
    p_value: Optional[float]
    
    # 推理质量
    confidence: float              # [0, 1]
    confounders_adjusted: List[str]
    active_paths: List[List[str]]  # 传导路径
    
    # 解释性
    natural_language_summary: str  # 自然语言摘要
    warnings: List[str]            # 潜在问题警告
    
    # 元数据
    inference_date: str
    graph_version: str
    method_used: str


class CausalReasoningEngine:
    """因果推理引擎主类"""
    
    def __init__(
        self,
        causal_graph: MacroRiskCausalGraph,
        historical_data: pd.DataFrame,
    ):
        self.graph = causal_graph
        self.data = historical_data
        self._dowhy_model_cache: Dict[Tuple, CausalModel] = {}
    
    # ================================================================
    # 模块1：观察推理 — P(Y|X=x)
    # ================================================================
    
    def observational_inference(
        self,
        source: str,
        target: str,
        source_value: float,
        conditioning_on: Optional[Dict[str, float]] = None
    ) -> InferenceResult:
        """
        观察推理：给定X=x（观察到），预测Y的分布
        注意：这是相关性，不是因果性
        """
        conditioning_on = conditioning_on or {}
        
        # 1. 找到相关路径
        paths = self.graph.find_all_causal_paths(source, target)
        
        # 2. 检查d-separation（给定conditioning_on，source和target是否仍然相关）
        conditioning_vars = list(conditioning_on.keys())
        is_conditionally_independent = self.graph.are_d_separated(
            source, target, conditioning_vars
        )
        
        if is_conditionally_independent:
            return InferenceResult(
                inference_type="observational",
                query=f"P({target}|{source}={source_value:.4f}, controls={conditioning_vars})",
                source_node=source, target_node=target,
                point_estimate=0.0, ci_lower=0.0, ci_upper=0.0,
                p_value=1.0, confidence=0.95,
                confounders_adjusted=conditioning_vars,
                active_paths=[],
                natural_language_summary=(
                    f"在控制{conditioning_vars}后，{source}与{target}条件独立，"
                    f"观察到的相关性可能由混淆变量驱动。"
                ),
                warnings=["d-separation indicates conditional independence"],
                inference_date=datetime.now().isoformat(),
                graph_version=self.graph.version,
                method_used="d-separation + linear regression"
            )
        
        # 3. 计算条件相关系数（简化版：线性回归）
        filter_mask = pd.Series([True] * len(self.data))
        control_data = self.data.copy()
        
        for cvar, cval in conditioning_on.items():
            if cvar in self.data.columns:
                # 仅使用conditioning变量在均值±1std范围内的数据（近似条件化）
                mean_c = self.data[cvar].mean()
                std_c = self.data[cvar].std()
                filter_mask &= abs(self.data[cvar] - cval) < std_c
        
        filtered = self.data[filter_mask].dropna(subset=[source, target])
        
        if len(filtered) < 30:
            return self._insufficient_data_result(source, target, "observational")
        
        from scipy import stats
        corr, pval = stats.pearsonr(filtered[source], filtered[target])
        
        # 估计目标变量的变化
        source_current = self.data[source].iloc[-1]
        source_delta = source_value - source_current
        
        # 使用简单线性回归估计效应
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            filtered[source], filtered[target]
        )
        predicted_delta_y = slope * source_delta
        target_current = self.data[target].iloc[-1]
        predicted_y = target_current + predicted_delta_y
        
        # 置信区间（基于回归标准误）
        n = len(filtered)
        t_critical = stats.t.ppf(0.975, df=n-2)
        ci_range = t_critical * std_err * abs(source_delta)
        
        return InferenceResult(
            inference_type="observational",
            query=f"P({target}|{source}={source_value:.4f})",
            source_node=source, target_node=target,
            point_estimate=predicted_y,
            ci_lower=predicted_y - ci_range,
            ci_upper=predicted_y + ci_range,
            p_value=p_value,
            confidence=min(0.9, abs(r_value)),
            confounders_adjusted=conditioning_vars,
            active_paths=paths,
            natural_language_summary=(
                f"观察推理（相关性）：若{source}达到{source_value:.4f}，"
                f"{target}预测为{predicted_y:.4f}（Δ={predicted_delta_y:+.4f}），"
                f"警告：此估计未做因果调整，包含混淆效应。"
            ),
            warnings=["Observational estimate includes confounding effects"],
            inference_date=datetime.now().isoformat(),
            graph_version=self.graph.version,
            method_used="OLS regression (observational)"
        )
    
    # ================================================================
    # 模块2：干预推理 — P(Y|do(X=x))
    # ================================================================
    
    def interventional_inference(
        self,
        source: str,
        target: str,
        intervention_value: float,
        method: str = "backdoor"
    ) -> InferenceResult:
        """
        干预推理：如果人为将X固定为x，Y如何变化
        这才是真正的因果效应（ATE：平均处理效应）
        
        method: "backdoor" | "frontdoor" | "iv" | "regression_discontinuity"
        """
        
        # 1. 构建DoWhy模型
        model = self._get_or_build_dowhy_model(source, target)
        
        # 2. 识别因果效应（do-calculus自动化）
        identified_estimand = model.identify_effect(
            proceed_when_unidentifiable=True
        )
        
        # 3. 估计效应
        estimate = model.estimate_effect(
            identified_estimand,
            method_name=f"backdoor.linear_regression",
            control_value=self.data[source].mean(),
            treatment_value=intervention_value,
            confidence_intervals=True,
        )
        
        # 4. 反驳测试（验证估计可靠性）
        refutation_results = {}
        for refute_method in [
            "placebo_treatment_refuter",
            "random_common_cause",
        ]:
            try:
                refuter = model.refute_estimate(
                    identified_estimand, estimate,
                    method_name=refute_method
                )
                refutation_results[refute_method] = {
                    "new_effect": refuter.new_effect,
                    "p_value": refuter.refutation_result.get("p_value", None)
                }
            except Exception:
                pass
        
        # 5. 分解直接效应 vs 间接效应
        direct_effect = self._compute_direct_effect(source, target, intervention_value)
        mediated_effects = self._compute_mediated_effects(source, target, intervention_value)
        
        causal_effect = estimate.value
        warnings = []
        
        # 检查反驳测试
        for method_name, result in refutation_results.items():
            if result.get("p_value") and result["p_value"] < 0.05:
                warnings.append(
                    f"Refutation test '{method_name}' suggests estimate may be unreliable"
                )
        
        # 与观察效应对比，量化混淆偏差
        obs_result = self.observational_inference(source, target, intervention_value)
        confounding_bias = obs_result.point_estimate - causal_effect
        
        path_details = self._format_path_effects(source, target, mediated_effects)
        
        return InferenceResult(
            inference_type="interventional",
            query=f"P({target}|do({source}={intervention_value:.4f}))",
            source_node=source, target_node=target,
            point_estimate=causal_effect,
            ci_lower=estimate.get_confidence_intervals()[0] if hasattr(estimate, 'get_confidence_intervals') else causal_effect * 0.8,
            ci_upper=estimate.get_confidence_intervals()[1] if hasattr(estimate, 'get_confidence_intervals') else causal_effect * 1.2,
            p_value=None,  # ATE不直接输出p值
            confidence=0.75 if not warnings else 0.50,
            confounders_adjusted=identified_estimand.backdoor_variables or [],
            active_paths=self.graph.find_all_causal_paths(source, target),
            natural_language_summary=(
                f"干预推理（因果效应）：若强制将{source}设为{intervention_value:.4f}，"
                f"{target}的因果效应为{causal_effect:+.4f}。"
                f"纯相关估计为{obs_result.point_estimate:+.4f}，"
                f"混淆偏差={confounding_bias:+.4f}。"
                f"路径分解：{path_details}"
            ),
            warnings=warnings,
            inference_date=datetime.now().isoformat(),
            graph_version=self.graph.version,
            method_used=f"DoWhy/{identified_estimand.identifier_method}"
        )
    
    # ================================================================
    # 模块3：反事实推理 — P(Y_x' | X=x, Y=y)
    # ================================================================
    
    def counterfactual_inference(
        self,
        source: str,
        target: str,
        factual_source_value: float,    # X实际发生的值
        factual_target_value: float,    # Y实际观测到的值
        counterfactual_source_value: float,  # X假设不同的值
        event_context: Optional[Dict] = None  # 事件发生时的其他变量值
    ) -> InferenceResult:
        """
        反事实推理：给定X=x, Y=y已经发生，
        如果当时X是x'，Y会是多少？
        
        应用场景：
        - 历史复盘："如果2024年美联储没有降息，今日韩元会在哪里？"
        - 政策评估："如果韩国央行干预了，损失能减少多少？"
        """
        
        # 孪生网络法（Pearl的反事实推理标准方法）
        # Step 1: Abduction — 从观测数据推断噪声变量的值
        # Step 2: Action — 在孪生世界中修改X
        # Step 3: Prediction — 预测孪生世界中Y的值
        
        # 简化实现：使用结构方程
        noise_estimates = self._abduct_noise_terms(
            source, target, factual_source_value, factual_target_value, event_context
        )
        
        # 在反事实世界中传播
        cf_target_value = self._propagate_counterfactual(
            source, target, counterfactual_source_value, noise_estimates, event_context
        )
        
        delta_actual = factual_target_value - (event_context or {}).get(f"{target}_baseline", factual_target_value)
        delta_counterfactual = cf_target_value - (event_context or {}).get(f"{target}_baseline", factual_target_value)
        effect_difference = cf_target_value - factual_target_value
        
        # 计算反事实的"责任归因"
        source_contribution_pct = abs(effect_difference) / (abs(delta_actual) + 1e-9) * 100
        
        return InferenceResult(
            inference_type="counterfactual",
            query=(
                f"E[{target}_{counterfactual_source_value:.4f} | "
                f"{source}={factual_source_value:.4f}, {target}={factual_target_value:.4f}]"
            ),
            source_node=source, target_node=target,
            point_estimate=cf_target_value,
            ci_lower=cf_target_value * 0.92,  # 反事实CI更宽（模型不确定性更大）
            ci_upper=cf_target_value * 1.08,
            p_value=None,
            confidence=0.60,  # 反事实推理本身具有更高不确定性
            confounders_adjusted=[],
            active_paths=self.graph.find_all_causal_paths(source, target),
            natural_language_summary=(
                f"反事实分析：{source}实际值={factual_source_value:.4f}，"
                f"{target}实际值={factual_target_value:.4f}。"
                f"若当时{source}为{counterfactual_source_value:.4f}，"
                f"则{target}预计为{cf_target_value:.4f}（差异={effect_difference:+.4f}）。"
                f"{source}变化对{target}结果的贡献约{source_contribution_pct:.1f}%。"
            ),
            warnings=["Counterfactual estimates have higher uncertainty than interventional"],
            inference_date=datetime.now().isoformat(),
            graph_version=self.graph.version,
            method_used="Twin Network / Structural Equation Abduction"
        )
    
    # ================================================================
    # 模块4：路径分析
    # ================================================================
    
    def path_analysis(
        self, source: str, target: str
    ) -> Dict:
        """
        分解从source到target的所有传导路径，
        计算每条路径的强度贡献
        """
        all_paths = self.graph.find_all_causal_paths(source, target)
        
        path_results = []
        total_strength = 0.0
        
        for path in all_paths:
            # 计算路径总强度（各边强度的乘积，考虑时滞衰减）
            path_strength = 1.0
            path_edges = []
            path_lag_total = 0
            
            for i in range(len(path) - 1):
                edge_id = self._find_edge_id(path[i], path[i+1])
                if edge_id:
                    edge = self.graph.edges[edge_id]
                    # 时滞衰减：长链路效应减弱
                    lag_decay = np.exp(-0.1 * edge.peak_lag_days)
                    effective_strength = edge.causal_strength * lag_decay * edge.strength_confidence
                    path_strength *= effective_strength
                    path_lag_total += edge.peak_lag_days
                    path_edges.append({
                        "from": path[i], "to": path[i+1],
                        "mechanism": edge.mechanism.value,
                        "strength": edge.causal_strength,
                        "lag_days": edge.peak_lag_days,
                        "is_nonlinear": edge.is_nonlinear
                    })
            
            path_results.append({
                "path": path,
                "path_str": " → ".join(path),
                "total_strength": abs(path_strength),
                "net_direction": "positive" if path_strength > 0 else "negative",
                "total_lag_days": path_lag_total,
                "num_hops": len(path) - 1,
                "edges": path_edges,
                "is_dominant": False  # 后面标记
            })
            
            total_strength += abs(path_strength)
        
        # 排序并标记主路径
        path_results.sort(key=lambda x: x["total_strength"], reverse=True)
        if path_results:
            path_results[0]["is_dominant"] = True
        
        # 计算相对贡献
        for p in path_results:
            p["strength_pct"] = (
                p["total_strength"] / total_strength * 100 
                if total_strength > 0 else 0
            )
        
        # 检测抵消路径（正负路径同时存在）
        positive_paths = [p for p in path_results if p["net_direction"] == "positive"]
        negative_paths = [p for p in path_results if p["net_direction"] == "negative"]
        has_cancellation = bool(positive_paths and negative_paths)
        
        return {
            "source": source,
            "target": target,
            "all_paths": path_results,
            "dominant_path": path_results[0] if path_results else None,
            "total_paths_count": len(path_results),
            "has_path_cancellation": has_cancellation,
            "cancellation_detail": (
                f"{len(positive_paths)}条同向路径 vs {len(negative_paths)}条反向路径"
                if has_cancellation else None
            ),
            "net_total_strength": sum(
                p["total_strength"] * (1 if p["net_direction"] == "positive" else -1)
                for p in path_results
            )
        }
    
    # ================================================================
    # 模块5：混淆检测
    # ================================================================
    
    def confounding_detection(
        self, source: str, target: str
    ) -> Dict:
        """
        检测source→target的观察相关性中有多少是混淆导致的
        返回：混淆变量列表、偏差估计、是否存在虚假相关
        """
        # 1. 识别所有后门路径（source ← ... → target）
        backdoor_paths = self._find_backdoor_paths(source, target)
        
        # 2. 寻找最小充分调整集
        adjustment_set = self._find_minimum_adjustment_set(source, target)
        
        # 3. 计算粗略相关 vs 调整后相关
        if source in self.data.columns and target in self.data.columns:
            raw_corr = self.data[[source, target]].corr().iloc[0, 1]
            
            # 调整后相关（偏相关）
            if adjustment_set and all(v in self.data.columns for v in adjustment_set):
                from sklearn.linear_model import LinearRegression
                # 从source和target中分别移除adjustment_set的线性影响
                X_ctrl = self.data[list(adjustment_set)].dropna()
                
                reg_s = LinearRegression().fit(X_ctrl, self.data.loc[X_ctrl.index, source])
                reg_t = LinearRegression().fit(X_ctrl, self.data.loc[X_ctrl.index, target])
                
                residual_s = self.data.loc[X_ctrl.index, source] - reg_s.predict(X_ctrl)
                residual_t = self.data.loc[X_ctrl.index, target] - reg_t.predict(X_ctrl)
                
                from scipy.stats import pearsonr
                adjusted_corr, _ = pearsonr(residual_s, residual_t)
                confounding_fraction = (raw_corr - adjusted_corr) / (abs(raw_corr) + 1e-9)
            else:
                adjusted_corr = raw_corr
                confounding_fraction = 0.0
        else:
            raw_corr = None
            adjusted_corr = None
            confounding_fraction = 0.0
        
        is_spurious = (
            confounding_fraction > 0.5 and  # 超过50%相关性来自混淆
            abs(raw_corr or 0) > 0.3          # 相关性不是太小
        )
        
        return {
            "source": source,
            "target": target,
            "backdoor_paths": backdoor_paths,
            "confounders": list(adjustment_set),
            "minimum_adjustment_set": list(adjustment_set),
            "raw_correlation": raw_corr,
            "adjusted_correlation": adjusted_corr,
            "confounding_fraction_pct": confounding_fraction * 100,
            "is_likely_spurious": is_spurious,
            "warning": (
                f"警告：{source}→{target}的相关性中{confounding_fraction*100:.1f}%"
                f"可能由混淆变量{list(adjustment_set)}驱动，存在虚假相关风险！"
                if is_spurious else None
            ),
        }
    
    # ================================================================
    # 私有辅助方法
    # ================================================================
    
    def _get_or_build_dowhy_model(self, treatment: str, outcome: str) -> CausalModel:
        """构建或获取缓存的DoWhy因果模型"""
        cache_key = (treatment, outcome)
        if cache_key in self._dowhy_model_cache:
            return self._dowhy_model_cache[cache_key]
        
        # 构建图的GTML格式（DoWhy需要）
        gtml_edges = []
        for edge in self.graph.edges.values():
            gtml_edges.append(f"{edge.source_node} -> {edge.target_node}")
        graph_str = "digraph { " + "; ".join(gtml_edges) + " }"
        
        # 仅使用可观测变量的数据列
        available_nodes = [
            n for n in self.graph.nodes.keys()
            if n in self.data.columns 
            and self.graph.nodes[n].node_type == NodeType.OBSERVABLE
        ]
        
        model = CausalModel(
            data=self.data[available_nodes].dropna(),
            treatment=treatment,
            outcome=outcome,
            graph=graph_str,
        )
        self._dowhy_model_cache[cache_key] = model
        return model
    
    def _find_backdoor_paths(self, source: str, target: str) -> List[List[str]]:
        """识别后门路径（从source出发，沿反向边到某祖先，再正向到target）"""
        # 简化实现：找所有source的祖先，再看祖先到target是否有路径
        backdoor = []
        reversed_graph = self.graph._nx_graph.reverse()
        source_ancestors = nx.descendants(reversed_graph, source)
        
        for ancestor in source_ancestors:
            paths_to_target = self.graph.find_all_causal_paths(ancestor, target)
            if paths_to_target:
                # 检查ancestor是否同时影响source（构成后门）
                ancestor_to_source = self.graph.find_all_causal_paths(ancestor, source)
                if ancestor_to_source:
                    backdoor.append({
                        "confounder": ancestor,
                        "source_path": ancestor_to_source[0],
                        "target_path": paths_to_target[0]
                    })
        return backdoor
    
    def _find_minimum_adjustment_set(self, source: str, target: str) -> set:
        """寻找最小充分调整集（用于后门调整）"""
        # 使用NetworkX的d-separation和nx工具
        # 简化：返回source的父节点集中，非source后代的节点
        parents_of_source = set(self.graph.get_causal_parents(source))
        descendants_of_source = nx.descendants(self.graph._nx_graph, source)
        
        # 有效调整集：source的父节点（排除source的后代）
        valid_adjustors = parents_of_source - descendants_of_source
        return valid_adjustors
    
    def _compute_direct_effect(self, source, target, intervention_value) -> float:
        """计算直接效应（阻断中介变量后）"""
        edge_id = self._find_edge_id(source, target)
        if edge_id:
            edge = self.graph.edges[edge_id]
            current_val = self.data[source].iloc[-1] if source in self.data.columns else 0
            delta = intervention_value - current_val
            return edge.causal_strength * delta
        return 0.0
    
    def _compute_mediated_effects(self, source, target, intervention_value) -> Dict:
        """计算各中介路径的效应"""
        mediators = {}
        paths = self.graph.find_all_causal_paths(source, target)
        for path in paths:
            if len(path) > 2:
                mediator = path[1]
                path_str = " → ".join(path)
                # 简化计算：乘积链
                effect = 1.0
                for i in range(len(path)-1):
                    eid = self._find_edge_id(path[i], path[i+1])
                    if eid:
                        effect *= self.graph.edges[eid].causal_strength
                mediators[path_str] = effect
        return mediators
    
    def _abduct_noise_terms(self, source, target, x_val, y_val, context) -> Dict:
        """推断结构方程的噪声项（孪生网络法第一步）"""
        noise = {}
        if target in self.data.columns and source in self.data.columns:
            # 用历史数据拟合结构方程，计算残差作为噪声估计
            parents = self.graph.get_causal_parents(target)
            available_parents = [p for p in parents if p in self.data.columns]
            if available_parents:
                from sklearn.linear_model import LinearRegression
                X_train = self.data[available_parents].dropna()
                y_train = self.data.loc[X_train.index, target]
                reg = LinearRegression().fit(X_train, y_train)
                residuals = y_train - reg.predict(X_train)
                # 噪声估计为当前时刻的残差
                noise[target] = residuals.iloc[-1] if len(residuals) > 0 else 0.0
        return noise
    
    def _propagate_counterfactual(
        self, source, target, cf_source_value, noise_estimates, context
    ) -> float:
        """在反事实世界中传播效应（孪生网络法第三步）"""
        # 拓扑排序传播
        try:
            topo_order = list(nx.topological_sort(self.graph._nx_graph))
        except nx.NetworkXUnfeasible:
            # 有环图：使用迭代方法
            topo_order = [source, target]
        
        cf_values = {}
        # 设置反事实的源节点值
        for node_id in topo_order:
            if node_id == source:
                cf_values[node_id] = cf_source_value
            elif node_id in self.graph.nodes:
                parents = self.graph.get_causal_parents(node_id)
                if not parents:
                    cf_values[node_id] = (
                        context.get(node_id) if context else
                        (self.data[node_id].iloc[-1] if node_id in self.data.columns else 0.0)
                    )
                else:
                    # 用结构方程计算
                    cf_val = 0.0
                    for parent in parents:
                        eid = self._find_edge_id(parent, node_id)
                        if eid and parent in cf_values:
                            edge = self.graph.edges[eid]
                            cf_val += edge.causal_strength * cf_values[parent]
                    cf_val += noise_estimates.get(node_id, 0.0)
                    cf_values[node_id] = cf_val
        
        return cf_values.get(target, 0.0)
    
    def _find_edge_id(self, source: str, target: str) -> Optional[str]:
        """根据source和target找到边ID"""
        for eid, edge in self.graph.edges.items():
            if edge.source_node == source and edge.target_node == target:
                return eid
        return None
    
    def _format_path_effects(self, source, target, mediated_effects) -> str:
        if not mediated_effects:
            return "无中介路径"
        lines = []
        for path_str, effect in sorted(mediated_effects.items(), key=lambda x: abs(x[1]), reverse=True):
            lines.append(f"{path_str}（强度={effect:+.3f}）")
        return "；".join(lines[:3])
    
    def _insufficient_data_result(self, source, target, inf_type) -> InferenceResult:
        return InferenceResult(
            inference_type=inf_type,
            query=f"{inf_type}({source}→{target})",
            source_node=source, target_node=target,
            point_estimate=0.0, ci_lower=0.0, ci_upper=0.0,
            p_value=None, confidence=0.0,
            confounders_adjusted=[],
            active_paths=[],
            natural_language_summary="数据不足，无法推理",
            warnings=["Insufficient data (n<30)"],
            inference_date=datetime.now().isoformat(),
            graph_version=self.graph.version,
            method_used="N/A"
        )
```

---

## 四、动态因果发现机制

### 4.1 模块架构

```
┌──────────────────────────────────────────────────────────────────┐
│                  动态因果发现引擎 (CausalDiscoveryEngine)          │
│                                                                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │  统计检验模块     │  │  结构断裂检测     │  │  新关系发现    │  │
│  │ EdgeValidator    │  │ RegimeDetector   │  │ NewEdgeFinder  │  │
│  │                  │  │                  │  │                │  │
│  │ - Granger因果检验 │  │ - CUSUM检验      │  │ - PC算法       │  │
│  │ - 转移熵检验      │  │ - Bai-Perron断点 │  │ - LiNGAM       │  │
│  │ - 偏相关检验      │  │ - HMM状态估计    │  │ - 约束图学习   │  │
│  └──────────────────┘  └──────────────────┘  └────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │               图更新决策模块 (GraphUpdateDecision)             │ │
│  │  - 贝叶斯信念更新（更新边强度和置信度）                         │ │
│  │  - 结构变化是否显著（是否需要创建新版本图）                     │ │
│  │  - 人工审核队列（高置信度自动更新，低置信度待审）               │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 实现代码

```python
from statsmodels.tsa.stattools import grangercausalitytests, ccf
from statsmodels.tsa.vector_ar.vecm import coint_johansen
import ruptures as rpt  # pip install ruptures（结构断裂检测）

@dataclass
class EdgeValidationResult:
    """边验证结果"""
    edge_id: str
    source: str
    target: str
    
    # Granger因果检验
    granger_p_value: Optional[float]
    granger_optimal_lag: Optional[int]
    granger_supports_causality: bool
    
    # 转移熵
    transfer_entropy: Optional[float]
    te_significance: Optional[float]
    
    # 参数稳定性
    is_structurally_stable: bool
    last_breakpoint_date: Optional[str]
    current_regime_coeff: Optional[float]
    
    # 综合评分
    validation_score: float    # [0, 1]
    recommendation: str        # "confirm", "weaken", "strengthen", "deprecate", "review"
    evidence_summary: str


@dataclass
class StructuralBreakResult:
    """结构断裂检测结果"""
    edge_id: str
    detected_breakpoints: List[str]   # 断裂日期
    pre_break_coefficient: float
    post_break_coefficient: float
    significance: float
    regime_interpretation: str         # LLM生成的制度解读
    suggested_regime_name: str


class CausalDiscoveryEngine:
    """动态因果发现引擎"""
    
    def __init__(
        self,
        causal_graph: MacroRiskCausalGraph,
        historical_data: pd.DataFrame,
        llm_client=None,  # LLM客户端（用于新关系解读）
    ):
        self.graph = causal_graph
        self.data = historical_data
        self.llm = llm_client
    
    # ================================================================
    # 1. 验证/证伪已有因果边
    # ================================================================
    
    def validate_existing_edges(
        self, lookback_days: int = 252
    ) -> List[EdgeValidationResult]:
        """
        对图中所有已有边进行统计验证
        使用最近lookback_days天的数据
        """
        recent_data = self.data.tail(lookback_days)
        results = []
        
        for edge_id, edge in self.graph.edges.items():
            if edge.is_deprecated:
                continue
            
            src = edge.source_node
            tgt = edge.target_node
            
            if src not in recent_data.columns or tgt not in recent_data.columns:
                continue
            
            result = self._validate_single_edge(edge, recent_data)
            results.append(result)
        
        return results
    
    def _validate_single_edge(
        self, edge: CausalEdge, data: pd.DataFrame
    ) -> EdgeValidationResult:
        
        src, tgt = edge.source_node, edge.target_node
        
        # --- Granger因果检验 ---
        granger_p = None
        granger_lag = None
        try:
            pair_data = data[[src, tgt]].dropna()
            max_lag = min(edge.max_lag_days, 20, len(pair_data) // 5)
            gc_results = grangercausalitytests(
                pair_data[[tgt, src]], maxlag=max_lag, verbose=False
            )
            # 取最优滞后期（最小p值）
            p_values = {
                lag: res[0]['ssr_ftest'][1]
                for lag, res in gc_results.items()
            }
            granger_lag = min(p_values, key=p_values.get)
            granger_p = p_values[granger_lag]
        except Exception:
            pass
        
        granger_supports = granger_p is not None and granger_p < 0.05
        
        # --- 转移熵（非线性Granger）---
        te_score = None
        te_sig = None
        try:
            te_score = self._compute_transfer_entropy(
                data[src].values, data[tgt].values, lag=edge.peak_lag_days
            )
            # 置换检验获得显著性
            te_sig = self._te_permutation_test(
                data[src].values, data[tgt].values,
                lag=edge.peak_lag_days, n_permutations=200
            )
        except Exception:
            pass
        
        # --- 参数稳定性检验 ---
        is_stable, breakpoint_date, current_coeff = self._test_parameter_stability(
            src, tgt, data
        )
        
        # --- 综合评分 ---
        score_components = []
        if granger_p is not None:
            score_components.append(1.0 - granger_p)  # p值越小分越高
        if te_sig is not None:
            score_components.append(1.0 - te_sig)
        if is_stable:
            score_components.append(0.8)  # 参数稳定加分
        else:
            score_components.append(0.3)  # 参数不稳定减分
        
        validation_score = np.mean(score_components) if score_components else 0.5
        
        # --- 推荐动作 ---
        if validation_score > 0.7:
            rec = "confirm"
        elif validation_score > 0.5:
            rec = "review"
        elif validation_score > 0.3:
            rec = "weaken"
        else:
            rec = "deprecate" if edge.evidence_type == "statistical" else "review"
        
        return EdgeValidationResult(
            edge_id=edge.edge_id,
            source=src, target=tgt,
            granger_p_value=granger_p,
            granger_optimal_lag=granger_lag,
            granger_supports_causality=granger_supports,
            transfer_entropy=te_score,
            te_significance=te_sig,
            is_structurally_stable=is_stable,
            last_breakpoint_date=breakpoint_date,
            current_regime_coeff=current_coeff,
            validation_score=validation_score,
            recommendation=rec,
            evidence_summary=(
                f"Granger: p={granger_p:.4f if granger_p else 'N/A'}, "
                f"lag={granger_lag}d; "
                f"TE={te_score:.4f if te_score else 'N/A'}; "
                f"稳定性={'稳定' if is_stable else f'不稳定(断裂:{breakpoint_date})'}"
            )
        )
    
    # ================================================================
    # 2. 结构断裂检测（Regime Change Detection）
    # ================================================================
    
    def detect_structural_breaks(
        self, min_break_significance: float = 0.01
    ) -> List[StructuralBreakResult]:
        """
        检测图中各边的参数是否发生结构性断裂
        使用CUSUM和Bai-Perron方法
        """
        breaks = []
        
        for edge_id, edge in self.graph.edges.items():
            src, tgt = edge.source_node, edge.target_node
            if src not in self.data.columns or tgt not in self.data.columns:
                continue
            
            result = self._detect_edge_break(edge)
            if result and result.significance < min_break_significance:
                breaks.append(result)
        
        return breaks
    
    def _detect_edge_break(self, edge: CausalEdge) -> Optional[StructuralBreakResult]:
        """检测单条边的结构断裂"""
        src, tgt = edge.source_node, edge.target_node
        
        try:
            pair = self.data[[src, tgt]].dropna()
            if len(pair) < 100:
                return None
            
            y = pair[tgt].values
            X = pair[src].values.reshape(-1, 1)
            
            # 使用ruptures库做断点检测
            # 对回归系数的残差序列做PELT算法
            from sklearn.linear_model import LinearRegression
            
            # 滚动回归系数（21天窗口）
            window = 21
            coeffs = []
            dates = pair.index[window:]
            
            for i in range(window, len(pair)):
                reg = LinearRegression().fit(
                    X[i-window:i], y[i-window:i]
                )
                coeffs.append(reg.coef_[0])
            
            coeff_series = np.array(coeffs)
            
            # PELT算法检测断点
            algo = rpt.Pelt(model="rbf").fit(coeff_series)
            breakpoints_idx = algo.predict(pen=10)
            
            if len(breakpoints_idx) <= 1:
                return None
            
            # 获取断点前后的系数
            last_bp_idx = breakpoints_idx[-2]  # 最后一个断点
            pre_coeff = np.mean(coeff_series[:last_bp_idx])
            post_coeff = np.mean(coeff_series[last_bp_idx:])
            
            # 显著性：t检验
            from scipy.stats import ttest_ind
            _, p_val = ttest_ind(
                coeff_series[:last_bp_idx],
                coeff_series[last_bp_idx:]
            )
            
            if p_val > 0.05:
                return None
            
            bp_date = str(dates[last_bp_idx]) if last_bp_idx < len(dates) else "unknown"
            
            # 解读制度变化
            regime_name = self._infer_regime_name(
                edge, bp_date, pre_coeff, post_coeff
            )
            
            return StructuralBreakResult(
                edge_id=edge.edge_id,
                detected_breakpoints=[bp_date],
                pre_break_coefficient=pre_coeff,
                post_break_coefficient=post_coeff,
                significance=p_val,
                regime_interpretation=(
                    f"边{edge.edge_id}在{bp_date}发生结构断裂，"
                    f"传导系数从{pre_coeff:.3f}变为{post_coeff:.3f}，"
                    f"变化幅度{(post_coeff-pre_coeff)/abs(pre_coeff)*100:.1f}%"
                ),
                suggested_regime_name=regime_name
            )
        except Exception as e:
            return None
    
    def _infer_regime_name(
        self, edge: CausalEdge, bp_date: str,
        pre_coeff: float, post_coeff: float
    ) -> str:
        """基于断裂时间和变化方向推断制度名称"""
        direction = "增强" if abs(post_coeff) > abs(pre_coeff) else "减弱"
        # 与已知宏观事件对比（简化：可接入LLM做智能匹配）
        known_events = {
            "2022-02": "俄乌冲突",
            "2022-06": "美联储激进加息",
            "2023-03": "硅谷银行危机",
            "2024-08": "日元套息交易平仓",
        }
        nearest_event = "未知宏观事件"
        for evt_date, evt_name in known_events.items():
            if bp_date[:7] == evt_date:
                nearest_event = evt_name
        
        return f"{nearest_event}后_{edge.mechanism.value}_{direction}"
    
    # ================================================================
    # 3. 发现新的因果关系
    # ================================================================
    
    def discover_new_edges(
        self, candidate_pairs: Optional[List[Tuple[str, str]]] = None,
        max_new_edges: int = 5
    ) -> List[Dict]:
        """
        从数据中发现尚未在图中的潜在因果关系
        使用PC算法（约束型因果发现）
        """
        if candidate_pairs is None:
            # 对所有节点对运行
            nodes = list(self.graph.nodes.keys())
            candidate_pairs = [
                (n1, n2)
                for i, n1 in enumerate(nodes)
                for n2 in nodes[i+1:]
                if n1 not in [e.source_node for e in self.graph.edges.values()
                               if e.target_node == n2]  # 排除已有边
            ]
        
        new_edge_candidates = []
        
        for src, tgt in candidate_pairs:
            if src not in self.data.columns or tgt not in self.data.columns:
                continue
            
            # Step 1: 检验两者是否显著相关（粗筛）
            pair_data = self.data[[src, tgt]].dropna()
            if len(pair_data) < 60:
                continue
            
            from scipy.stats import pearsonr
            corr, pval = pearsonr(pair_data[src], pair_data[tgt])
            if abs(corr) < 0.25 or pval > 0.01:
                continue
            
            # Step 2: Granger因果检验（方向性筛选）
            try:
                gc_src_to_tgt = grangercausalitytests(
                    pair_data[[tgt, src]], maxlag=5, verbose=False
                )
                gc_tgt_to_src = grangercausalitytests(
                    pair_data[[src, tgt]], maxlag=5, verbose=False
                )
                
                min_p_s2t = min(v[0]['ssr_ftest'][1] for v in gc_src_to_tgt.values())
                min_p_t2s = min(v[0]['ssr_ftest'][1] for v in gc_tgt_to_src.values())
                
                # 方向性判断：哪个方向p值更小
                if min_p_s2t > 0.05:
                    continue
                
                direction_confidence = (min_p_t2s - min_p_s2t) / (min_p_t2s + 1e-9)
                
            except Exception:
                continue
            
            # Step 3: 检验是否能被现有图中的节点解释（避免冗余）
            common_causes = self._find_common_causes(src, tgt)
            if common_causes:
                # 做偏相关检验：控制公共原因后，相关性是否消失
                partial_corr = self._partial_correlation(src, tgt, common_causes)
                if abs(partial_corr) < 0.15:
                    # 相关性被共同原因完全解释，不是新的因果关系
                    continue
            
            new_edge_candidates.append({
                "source": src,
                "target": tgt,
                "correlation": corr,
                "granger_p_value": min_p_s2t,
                "direction_confidence": direction_confidence,
                "partial_correlation": self._partial_correlation(src, tgt, common_causes) if common_causes else corr,
                "common_causes": common_causes,
                "status": "candidate",  # 待LLM审核
            })
        
        # 按显著性排序，取前N个
        new_edge_candidates.sort(key=lambda x: x["granger_p_value"])
        return new_edge_candidates[:max_new_edges]
    
    # ================================================================
    # 4. 贝叶斯更新边权重
    # ================================================================
    
    def bayesian_update_edge_strengths(
        self, validation_results: List[EdgeValidationResult]
    ) -> List[Dict]:
        """
        基于验证结果，用贝叶斯更新规则更新边的因果强度和置信度
        """
        updates = []
        
        for result in validation_results:
            edge = self.graph.edges.get(result.edge_id)
            if not edge:
                continue
            
            # 贝叶斯更新置信度
            # 先验：当前edge.strength_confidence
            # 似然：validation_score
            prior = edge.strength_confidence
            likelihood_support = result.validation_score
            likelihood_contradict = 1 - result.validation_score
            
            # 贝叶斯公式（简化的Beta分布更新）
            # 视历史验证次数为伪样本数
            n_prior = max(edge.num_supporting_events, 5)
            n_new = 1  # 本次验证
            
            posterior_confidence = (
                (prior * n_prior + likelihood_support * n_new) / 
                (n_prior + n_new)
            )
            
            # 更新因果强度（如果Granger检验提供了新的系数估计）
            new_strength = edge.causal_strength
            if result.current_regime_coeff is not None:
                # 指数滑动平均更新（alpha=0.3）
                alpha = 0.3
                new_strength = (
                    alpha * result.current_regime_coeff + 
                    (1 - alpha) * edge.causal_strength
                )
            
            update_action = {
                "edge_id": result.edge_id,
                "old_confidence": prior,
                "new_confidence": posterior_confidence,
                "old_strength": edge.causal_strength,
                "new_strength": new_strength,
                "recommendation": result.recommendation,
                "apply_update": posterior_confidence > 0.3,  # 低于阈值则标记弃用
                "requires_human_review": (
                    abs(new_strength - edge.causal_strength) > 0.2 or
                    result.recommendation in ["deprecate", "review"]
                )
            }
            updates.append(update_action)
        
        return updates
    
    # ================================================================
    # 辅助方法
    # ================================================================
    
    def _compute_transfer_entropy(
        self, x: np.ndarray, y: np.ndarray, lag: int = 1
    ) -> float:
        """计算从x到y的转移熵（离散化近似）"""
        # 使用分位数离散化
        n_bins = 4
        x_binned = pd.qcut(x, q=n_bins, labels=False, duplicates='drop')
        y_binned = pd.qcut(y, q=n_bins, labels=False, duplicates='drop')
        
        if lag >= len(x):
            return 0.0
        
        y_future = y_binned[lag:]
        y_past = y_binned[:-lag]
        x_past = x_binned[:-lag]
        
        min_len = min(len(y_future), len(y_past), len(x_past))
        y_future = y_future[:min_len]
        y_past = y_past[:min_len]
        x_past = x_past[:min_len]
        
        valid_mask = ~(pd.isna(y_future) | pd.isna(y_past) | pd.isna(x_past))
        yf = y_future[valid_mask]
        yp = y_past[valid_mask]
        xp = x_past[valid_mask]
        
        if len(yf) < 20:
            return 0.0
        
        from collections import Counter
        
        def entropy(series):
            counts = Counter(series)
            total = sum(counts.values())
            return -sum((c/total) * np.log2(c/total + 1e-10) for c in counts.values())
        
        def joint_entropy(*series_list):
            combined = list(zip(*series_list))
            counts = Counter(combined)
            total = sum(counts.values())
            return -sum((c/total) * np.log2(c/total + 1e-10) for c in counts.values())
        
        te = (
            joint_entropy(list(yf), list(xp)) +
            joint_entropy(list(yf), list(yp)) -
            joint_entropy(list(yf), list(yp), list(xp)) -
            entropy(list(yf))
        )
        return max(0.0, te)
    
    def _te_permutation_test(
        self, x: np.ndarray, y: np.ndarray,
        lag: int, n_permutations: int = 200
    ) -> float:
        """转移熵的置换显著性检验"""
        observed_te = self._compute_transfer_entropy(x, y, lag)
        null_distribution = []
        
        for _ in range(n_permutations):
            x_permuted = np.random.permutation(x)
            null_te = self._compute_transfer_entropy(x_permuted, y, lag)
            null_distribution.append(null_te)
        
        p_value = np.mean(np.array(null_distribution) >= observed_te)
        return p_value
    
    def _test_parameter_stability(
        self, src: str, tgt: str, data: pd.DataFrame
    ) -> Tuple[bool, Optional[str], Optional[float]]:
        """检验回归系数是否稳定"""
        try:
            pair = data[[src, tgt]].dropna()
            if len(pair) < 60:
                return True, None, None
            
            window = 42
            coeffs = []
            for i in range(window, len(pair)):
                from sklearn.linear_model import LinearRegression
                reg = LinearRegression().fit(
                    pair[src].values[i-window:i].reshape(-1, 1),
                    pair[tgt].values[i-window:i]
                )
                coeffs.append(reg.coef_[0])
            
            coeff_array = np.array(coeffs)
            current_coeff = coeff_array[-1]
            
            # 稳定性：当前系数是否在历史均值的2σ以内
            mean_c = np.mean(coeff_array)
            std_c = np.std(coeff_array)
            is_stable = abs(current_coeff - mean_c) < 2 * std_c
            
            # 找最近一次大幅偏离的时间
            deviation = abs(coeff_array - mean_c)
            recent_breaks = np.where(deviation > 2 * std_c)[0]
            last_break = str(pair.index[recent_breaks[-1] + window]) if len(recent_breaks) > 0 else None
            
            return is_stable, last_break, current_coeff
        except Exception:
            return True, None, None
    
    def _find_common_causes(self, src: str, tgt: str) -> List[str]:
        """找到同时影响src和tgt的公共原因节点"""
        src_ancestors = set(nx.ancestors(self.graph._nx_graph, src))
        tgt_ancestors = set(nx.ancestors(self.graph._nx_graph, tgt))
        return list(src_ancestors & tgt_ancestors)
    
    def _partial_correlation(
        self, src: str, tgt: str, controls: List[str]
    ) -> float:
        """计算偏相关系数"""
        available = [c for c in controls if c in self.data.columns]
        if not available:
            from scipy.stats import pearsonr
            data = self.data[[src, tgt]].dropna()
            corr, _ = pearsonr(data[src], data[tgt])
            return corr
        
        from sklearn.linear_model import LinearRegression
        from scipy.stats import pearsonr
        
        data = self.data[[src, tgt] + available].dropna()
        X_ctrl = data[available]
        
        res_src = data[src] - LinearRegression().fit(X_ctrl, data[src]).predict(X_ctrl)
        res_tgt = data[tgt] - LinearRegression().fit(X_ctrl, data[tgt]).predict(X_ctrl)
        
        corr, _ = pearsonr(res_src, res_tgt)
        return corr
```

---

## 五、LLM与因果图引擎的协同设计

### 5.1 协同架构图

```
  ┌───────────────────────────────────────────────────────────────┐
  │                     协同推理层                                  │
  │                                                               │
  │  ┌─────────────────────────┐   ┌──────────────────────────┐  │
  │  │       LLM层              │   │     因果图引擎层           │  │
  │  │  (Claude / GPT-4o)      │   │  (DoWhy + NetworkX)      │  │
  │  │                         │   │                           │  │
  │  │ 擅长：                   │   │ 擅长：                    │  │
  │  │ - 非结构化文本理解         │   │ - 形式化因果推理           │  │
  │  │ - 事件提取与分类           │   │ - 统计检验与显著性         │  │
  │  │ - 因果假设生成             │   │ - d-separation计算        │  │
  │  │ - 反事实场景构造           │   │ - 路径分析与分解           │  │
  │  │ - 自然语言输出             │   │ - 置信区间估计             │  │
  │  │                         │   │                           │  │
  │  │ 不擅长：                  │   │ 不擅长：                  │  │
  │  │ - 精确统计计算             │   │ - 文本理解                │  │
  │  │ - 大数据集分析             │   │ - 新奇事件识别             │  │
  │  │ - 一致的数值推理           │   │ - 机制解释                │  │
  │  └────────────┬────────────┘   └─────────────┬────────────┘  │
  │               │                              │                │
  │               └──────────────┬───────────────┘                │
  │                              │                                │
  │                   ┌──────────▼──────────┐                     │
  │                   │    协调器            │                     │
  │                   │  (Orchestrator)     │                     │
  │                   │                     │                     │
  │                   │ 1. LLM提取事件       │                     │
  │                   │ 2. 图引擎验证假设    │                     │
  │                   │ 3. 互相校正          │                     │
  │                   │ 4. 输出综合判断      │                     │
  │                   └─────────────────────┘                     │
  └───────────────────────────────────────────────────────────────┘

  数据流：
  
  新闻/财报 ──→ [LLM] ──→ 因果假设列表 ──→ [图引擎] ──→ 统计检验
                                                          │
                                              ┌───────────┘
                                              ▼
                                        验证/证伪结果 ──→ [LLM] ──→ 自然语言报告
                                              │
                                      低置信度假设 ──→ [人工审核队列]
```

### 5.2 实现代码

```python
from anthropic import Anthropic
import json
from typing import List, Dict, Optional

# 系统Prompt模板
CAUSAL_EXTRACTION_PROMPT = """
你是一个宏观经济因果关系分析专家。请从以下市场新闻/事件文本中提取因果关系假设。

已知因果图中的核心节点（变量）：
{node_list}

请提取文本中暗示的因果关系，以JSON格式输出：
{{
  "events": [
    {{
      "event_id": "唯一标识",
      "event_type": "policy_change|market_event|macro_data|geopolitical|corporate",
      "affected_nodes": ["节点ID1", "节点ID2"],
      "causal_hypotheses": [
        {{
          "source_node": "节点ID",
          "target_node": "节点ID",
          "direction": "positive|negative",
          "estimated_magnitude": "small|medium|large",
          "estimated_lag_days": 数字,
          "mechanism": "描述传导机制的一句话",
          "confidence": "low|medium|high",
          "is_new_relationship": true|false  // 是否是图中尚未存在的关系
        }}
      ],
      "regime_change_signal": true|false,  // 是否暗示制度性变化
      "regime_description": "如果是制度变化，描述变化内容"
    }}
  ]
}}

仅输出JSON，不要额外解释。
"""

CAUSAL_NARRATIVE_PROMPT = """
你是宏观风险分析师。请基于以下因果推理结果，生成一份专业的风险传导分析报告。

【因果推理结果】
{inference_results}

【路径分析结果】
{path_analysis}

【反事实分析】
{counterfactual_results}

【混淆检测警告】
{confounding_warnings}

请生成一份{report_type}（日报/月报/预警报告），要求：
1. 用清晰的因果语言（"由于...导致...通过...渠道...最终..."）描述传导链
2. 明确区分"因果效应"和"相关性观察"
3. 标注估计的置信度和不确定性
4. 指出被忽略的混淆变量风险
5. 提供2-3个反事实情景分析
6. 给出可操作的风险预警级别（绿/黄/橙/红）

输出格式：Markdown
"""

HYPOTHESIS_REVIEW_PROMPT = """
你是因果图维护专家。以下是统计引擎发现的潜在新因果关系，请评估其经济学合理性。

候选新边：
{new_edge_candidates}

对每个候选，请评估：
1. 经济学机制是否合理（有无理论支撑）
2. 是否可能是虚假相关（共同驱动因子是什么）
3. 推荐的因果强度方向（正/负）
4. 推荐的时滞范围
5. 置信度评级（低/中/高）
6. 是否建议加入因果图

以JSON格式输出每个候选的评估结果。
"""


class LLMCausalOrchestrator:
    """LLM与因果图引擎的协调器"""
    
    def __init__(
        self,
        causal_graph: MacroRiskCausalGraph,
        reasoning_engine: CausalReasoningEngine,
        discovery_engine: CausalDiscoveryEngine,
        llm_client: Anthropic,
        model: str = "claude-opus-4-5",
    ):
        self.graph = causal_graph
        self.engine = reasoning_engine
        self.discovery = discovery_engine
        self.llm = llm_client
        self.model = model
    
    # ================================================================
    # Step 1: 事件驱动的因果假设提取
    # ================================================================
    
    def extract_causal_hypotheses(self, news_text: str) -> Dict:
        """
        输入：原始新闻/财报文本
        输出：结构化的因果假设列表
        """
        node_list = "\n".join([
            f"- {nid}: {node.display_name} ({node.asset_class.value}, {node.geography})"
            for nid, node in self.graph.nodes.items()
        ])
        
        response = self.llm.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": CAUSAL_EXTRACTION_PROMPT.format(node_list=node_list) 
                           + f"\n\n【待分析文本】\n{news_text}"
            }]
        )
        
        try:
            extracted = json.loads(response.content[0].text)
        except json.JSONDecodeError:
            # 容错：尝试从文本中提取JSON
            extracted = {"events": [], "parse_error": True}
        
        return extracted
    
    # ================================================================
    # Step 2: 形式化验证LLM假设
    # ================================================================
    
    def verify_llm_hypotheses(
        self, hypotheses: Dict, lookback_days: int = 90
    ) -> List[Dict]:
        """
        用统计引擎验证LLM提出的因果假设
        """
        verified = []
        
        for event in hypotheses.get("events", []):
            for hyp in event.get("causal_hypotheses", []):
                src = hyp["source_node"]
                tgt = hyp["target_node"]
                
                # 检查节点是否在图中
                if src not in self.graph.nodes or tgt not in self.graph.nodes:
                    verified.append({
                        **hyp,
                        "verification_status": "unknown_nodes",
                        "stat_result": None,
                    })
                    continue
                
                # 统计验证
                stat_result = None
                
                # 1. 检查图中是否已有此边
                existing_edge = None
                for eid, edge in self.graph.edges.items():
                    if edge.source_node == src and edge.target_node == tgt:
                        existing_edge = edge
                        break
                
                if existing_edge:
                    # 已有边：验证方向是否一致
                    llm_direction = 1 if hyp["direction"] == "positive" else -1
                    graph_direction = 1 if existing_edge.causal_strength > 0 else -1
                    direction_consistent = llm_direction == graph_direction
                    
                    stat_result = {
                        "type": "existing_edge_check",
                        "direction_consistent": direction_consistent,
                        "existing_strength": existing_edge.causal_strength,
                        "existing_confidence": existing_edge.strength_confidence,
                    }
                    
                    status = "confirmed" if direction_consistent else "direction_conflict"
                else:
                    # 新边：运行Granger检验
                    if (src in self.discovery.data.columns and 
                        tgt in self.discovery.data.columns):
                        recent = self.discovery.data.tail(lookback_days)
                        pair = recent[[src, tgt]].dropna()
                        
                        if len(pair) >= 20:
                            try:
                                gc = grangercausalitytests(
                                    pair[[tgt, src]], maxlag=5, verbose=False
                                )
                                min_p = min(v[0]['ssr_ftest'][1] for v in gc.values())
                                stat_result = {
                                    "type": "granger_test",
                                    "p_value": min_p,
                                    "supports_hypothesis": min_p < 0.1,
                                }
                                status = (
                                    "statistically_supported" if min_p < 0.1 
                                    else "not_supported"
                                )
                            except Exception:
                                status = "test_failed"
                                stat_result = {"type": "granger_test", "error": True}
                        else:
                            status = "insufficient_data"
                    else:
                        status = "data_unavailable"
                
                verified.append({
                    **hyp,
                    "verification_status": status,
                    "stat_result": stat_result,
                    "event_context": {
                        "event_id": event["event_id"],
                        "event_type": event["event_type"],
                        "regime_change_signal": event.get("regime_change_signal", False),
                    }
                })
        
        return verified
    
    # ================================================================
    # Step 3: 用LLM审核统计发现的新关系
    # ================================================================
    
    def llm_review_new_edges(
        self, new_edge_candidates: List[Dict]
    ) -> List[Dict]:
        """
        LLM评估统计引擎发现的潜在新因果关系的经济学合理性
        """
        if not new_edge_candidates:
            return []
        
        # 为LLM准备上下文
        candidates_text = json.dumps(new_edge_candidates, ensure_ascii=False, indent=2)
        
        response = self.llm.messages.create(
            model=self.model,
            max_tokens=3000,
            messages=[{
                "role": "user",
                "content": HYPOTHESIS_REVIEW_PROMPT.format(
                    new_edge_candidates=candidates_text
                )
            }]
        )
        
        try:
            reviews = json.loads(response.content[0].text)
        except json.JSONDecodeError:
            reviews = [{"review_error": True, "raw": response.content[0].text}]
        
        # 合并统计结果和LLM评估
        combined = []
        for i, candidate in enumerate(new_edge_candidates):
            llm_review = reviews[i] if i < len(reviews) else {}
            combined.append({
                **candidate,
                "llm_review": llm_review,
                "final_recommendation": self._synthesize_recommendation(
                    candidate, llm_review
                )
            })
        
        return combined
    
    # ================================================================
    # Step 4: 生成自然语言分析报告
    # ================================================================
    
    def generate_causal_narrative(
        self,
        daily_state: Dict,
        inference_results: List[InferenceResult],
        path_analyses: List[Dict],
        counterfactual_results: List[InferenceResult],
        confounding_warnings: List[Dict],
        report_type: str = "日报"
    ) -> str:
        """
        将因果推理结果转化为自然语言分析报告
        """
        # 序列化推理结果
        def format_inference(r: InferenceResult) -> str:
            return (
                f"{r.source_node}→{r.target_node}: "
                f"效应={r.point_estimate:+.4f} "
                f"[{r.ci_lower:+.4f}, {r.ci_upper:+.4f}], "
                f"类型={r.inference_type}, "
                f"置信度={r.confidence:.2f}, "
                f"方法={r.method_used}"
            )
        
        def format_path(p: Dict) -> str:
            dominant = p.get("dominant_path", {})
            return (
                f"{p['source']}→{p['target']}: "
                f"主路径={dominant.get('path_str', 'N/A')}, "
                f"贡献={dominant.get('strength_pct', 0):.1f}%, "
                f"总路径数={p['total_paths_count']}"
            )
        
        inference_text = "\n".join(format_inference(r) for r in inference_results)
        path_text = "\n".join(format_path(p) for p in path_analyses)
        cf_text = "\n".join(format_inference(r) for r in counterfactual_results)
        conf_text = "\n".join(
            w.get("warning", "") for w in confounding_warnings if w.get("warning")
        )
        
        response = self.llm.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": CAUSAL_NARRATIVE_PROMPT.format(
                    inference_results=inference_text,
                    path_analysis=path_text,
                    counterfactual_results=cf_text,
                    confounding_warnings=conf_text,
                    report_type=report_type
                )
            }]
        )
        
        return response.content[0].text
    
    # ================================================================
    # 互相校正机制
    # ================================================================
    
    def mutual_correction_loop(
        self, news_text: str, max_iterations: int = 2
    ) -> Dict:
        """
        LLM和图引擎的互相校正循环：
        1. LLM提取假设
        2. 图引擎统计验证
        3. 将验证结果反馈给LLM，要求修正低置信度假设
        4. LLM重新生成修正后的假设
        """
        # Round 1: 初始提取
        hypotheses = self.extract_causal_hypotheses(news_text)
        verified = self.verify_llm_hypotheses(hypotheses)
        
        # 识别有争议的假设（LLM高置信但统计不支持，或反之）
        controversial = [
            v for v in verified
            if (v["confidence"] == "high" and 
                v["verification_status"] in ["not_supported", "direction_conflict"])
        ]
        
        if not controversial or max_iterations == 0:
            return {
                "hypotheses": hypotheses,
                "verified": verified,
                "iterations": 1,
                "controversial": controversial
            }
        
        # Round 2: LLM基于统计证据重新评估争议假设
        correction_prompt = f"""
        以下因果假设被你认为是高置信度的，但统计检验不支持：
        {json.dumps(controversial, ensure_ascii=False, indent=2)}
        
        请重新评估：
        1. 是否可能存在混淆变量导致虚假相关？
        2. 机制描述是否需要修正？
        3. 是否降低置信度？
        
        以JSON格式输出修正后的假设列表。
        """
        
        correction_response = self.llm.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": correction_prompt}]
        )
        
        try:
            corrected = json.loads(correction_response.content[0].text)
        except json.JSONDecodeError:
            corrected = controversial
        
        return {
            "hypotheses": hypotheses,
            "verified": verified,
            "corrected": corrected,
            "iterations": 2,
            "controversial": controversial
        }
    
    def _synthesize_recommendation(
        self, candidate: Dict, llm_review: Dict
    ) -> str:
        """综合统计结果和LLM评审，给出最终推荐"""
        stat_supports = candidate.get("granger_p_value", 1.0) < 0.05
        llm_supports = llm_review.get("recommend_add", False)
        llm_confidence = llm_review.get("confidence", "low")
        
        if stat_supports and llm_supports and llm_confidence == "high":
            return "add_to_graph"
        elif stat_supports and llm_supports:
            return "add_with_low_confidence"
        elif stat_supports and not llm_supports:
            return "human_review_needed"  # 统计显著但经济学不合理
        elif not stat_supports and llm_supports:
            return "monitor_only"  # 有理论支撑但统计暂不显著
        else:
            return "reject"
```

---

## 六、存储层升级方案

### 6.1 版本化图谱存储设计（PostgreSQL）

```sql
-- ================================================================
-- 因果图版本化存储
-- ================================================================

-- 图版本表
CREATE TABLE causal_graph_versions (
    version_id      VARCHAR(50) PRIMARY KEY,       -- "v1.0", "v1.1_20240815"
    parent_version  VARCHAR(50) REFERENCES causal_graph_versions(version_id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      VARCHAR(100) NOT NULL,          -- "auto_discovery", "human_review", "llm_hypothesis"
    change_type     VARCHAR(50) NOT NULL,           -- "edge_added", "edge_deprecated", "strength_updated", "regime_change"
    change_summary  TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,
    approved_by     VARCHAR(100),                   -- 人工审核通过者
    approved_at     TIMESTAMPTZ,
    graph_snapshot  JSONB NOT NULL,                 -- 完整图的JSON快照
    diff_from_parent JSONB                          -- 与父版本的差异（增量存储）
);

-- 节点历史表
CREATE TABLE causal_nodes_history (
    record_id       BIGSERIAL PRIMARY KEY,
    graph_version   VARCHAR(50) NOT NULL REFERENCES causal_graph_versions(version_id),
    node_id         VARCHAR(100) NOT NULL,
    node_type       VARCHAR(50) NOT NULL,
    asset_class     VARCHAR(50) NOT NULL,
    geography       VARCHAR(20),
    display_name    VARCHAR(200),
    description     TEXT,
    data_source     VARCHAR(500),
    effective_from  TIMESTAMPTZ NOT NULL,
    effective_to    TIMESTAMPTZ,                    -- NULL表示当前有效
    metadata        JSONB
);

-- 边历史表（核心：记录因果强度演化）
CREATE TABLE causal_edges_history (
    record_id           BIGSERIAL PRIMARY KEY,
    graph_version       VARCHAR(50) NOT NULL REFERENCES causal_graph_versions(version_id),
    edge_id             VARCHAR(200) NOT NULL,
    source_node         VARCHAR(100) NOT NULL,
    target_node         VARCHAR(100) NOT NULL,
    
    -- 因果参数（每次更新都记录完整快照）
    causal_strength     NUMERIC(8, 4) NOT NULL,
    strength_confidence NUMERIC(5, 4) NOT NULL,
    strength_ci_lower   NUMERIC(8, 4),
    strength_ci_upper   NUMERIC(8, 4),
    
    -- 时间参数
    min_lag_days        INTEGER,
    max_lag_days        INTEGER,
    peak_lag_days       INTEGER,
    
    -- 元数据
    mechanism           VARCHAR(100),
    evidence_type       VARCHAR(50),               -- "theoretical", "statistical", "llm_inferred"
    validation_p_value  NUMERIC(8, 6),
    num_supporting_events INTEGER DEFAULT 0,
    is_deprecated       BOOLEAN DEFAULT FALSE,
    
    -- 版本时间范围
    effective_from      TIMESTAMPTZ NOT NULL,
    effective_to        TIMESTAMPTZ,
    
    -- 变更记录
    change_reason       TEXT,                      -- 为什么更新这条边
    change_trigger      VARCHAR(100),              -- "daily_validation", "regime_break", "human_edit"
    
    UNIQUE(edge_id, effective_from)
);

-- 推理结果存储
CREATE TABLE causal_inference_log (
    inference_id        BIGSERIAL PRIMARY KEY,
    inference_date      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    graph_version       VARCHAR(50) NOT NULL,
    inference_type      VARCHAR(50) NOT NULL,      -- "observational", "interventional", "counterfactual"
    source_node         VARCHAR(100) NOT NULL,
    target_node         VARCHAR(100) NOT NULL,
    query_description   TEXT,
    
    -- 结果
    point_estimate      NUMERIC(12, 6),
    ci_lower            NUMERIC(12, 6),
    ci_upper            NUMERIC(12, 6),
    confidence          NUMERIC(5, 4),
    confounders_adjusted TEXT[],                   -- 已调整的混淆变量
    active_paths        JSONB,                     -- 激活的传导路径
    
    -- 输入上下文
    input_values        JSONB,                     -- 推理时各节点的值
    intervention_value  NUMERIC(12, 6),
    
    -- 输出
    natural_language_summary TEXT,
    warnings            TEXT[],
    method_used         VARCHAR(200),
    
    -- 触发来源
    triggered_by        VARCHAR(100),              -- "daily_run", "alert_threshold", "manual_query"
    report_id           VARCHAR(100)               -- 关联到哪份报告
);

-- 结构断裂事件记录
CREATE TABLE structural_break_events (
    break_id            BIGSERIAL PRIMARY KEY,
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    edge_id             VARCHAR(200) NOT NULL,
    source_node         VARCHAR(100) NOT NULL,
    target_node         VARCHAR(100) NOT NULL,
    
    break_date          DATE NOT NULL,             -- 断裂发生的估计日期
    pre_break_coeff     NUMERIC(8, 4) NOT NULL,
    post_break_coeff    NUMERIC(8, 4) NOT NULL,
    significance        NUMERIC(8, 6) NOT NULL,    -- p值
    
    regime_name         VARCHAR(200),
    regime_interpretation TEXT,
    
    -- 处理状态
    status              VARCHAR(50) DEFAULT 'detected',  -- detected, reviewed, applied, dismissed
    reviewed_by         VARCHAR(100),
    applied_to_version  VARCHAR(50),
    
    related_events      TEXT[]                     -- 关联的宏观事件
);

-- 每日图状态快照（轻量级，不含完整图结构）
CREATE TABLE daily_graph_state (
    state_id            BIGSERIAL PRIMARY KEY,
    state_date          DATE NOT NULL UNIQUE,
    graph_version       VARCHAR(50) NOT NULL,
    current_regime      VARCHAR(100) NOT NULL,
    
    -- 节点当日值（JSON压缩存储）
    node_values         JSONB NOT NULL,
    node_zscores        JSONB NOT NULL,
    anomalous_nodes     TEXT[],
    
    -- 当日激活的传导路径
    active_paths        JSONB,
    
    -- 当日因果推理摘要
    inference_summary   JSONB,
    
    -- 预警状态
    alert_level         VARCHAR(20) DEFAULT 'green',  -- green, yellow, orange, red
    alert_details       JSONB,
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- 创建关键索引
CREATE INDEX idx_edges_history_edge_id ON causal_edges_history(edge_id, effective_from DESC);
CREATE INDEX idx_edges_history_version ON causal_edges_history(graph_version);
CREATE INDEX idx_inference_log_date ON causal_inference_log(inference_date DESC);
CREATE INDEX idx_inference_log_nodes ON causal_inference_log(source_node, target_node);
CREATE INDEX idx_daily_state_date ON daily_graph_state(state_date DESC);
CREATE INDEX idx_struct_break_edge ON structural_break_events(edge_id, break_date DESC);
```

### 6.2 图版本管理器

```python
import psycopg2
from psycopg2.extras import Json, execute_values
from datetime import datetime, date

class GraphVersionManager:
    """因果图版本化存储管理器"""
    
    def __init__(self, db_conn):
        self.conn = db_conn
    
    def save_new_version(
        self,
        graph: MacroRiskCausalGraph,
        change_type: str,
        change_summary: str,
        created_by: str,
        parent_version: Optional[str] = None,
        auto_activate: bool = False,
    ) -> str:
        """保存新版本图谱"""
        
        version_id = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 计算与父版本的差异
        diff = {}
        if parent_version:
            diff = self._compute_graph_diff(parent_version, graph)
        
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO causal_graph_versions 
                (version_id, parent_version, created_by, change_type, 
                 change_summary, is_active, graph_snapshot, diff_from_parent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                version_id, parent_version, created_by, change_type,
                change_summary, auto_activate,
                Json(graph.to_dict()), Json(diff)
            ))
            
            # 记录边历史
            for edge in graph.edges.values():
                cur.execute("""
                    INSERT INTO causal_edges_history
                    (graph_version, edge_id, source_node, target_node,
                     causal_strength, strength_confidence, strength_ci_lower,
                     strength_ci_upper, min_lag_days, max_lag_days, peak_lag_days,
                     mechanism, evidence_type, is_deprecated,
                     effective_from, change_trigger)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    version_id, edge.edge_id, edge.source_node, edge.target_node,
                    edge.causal_strength, edge.strength_confidence,
                    edge.strength_ci_lower, edge.strength_ci_upper,
                    edge.min_lag_days, edge.max_lag_days, edge.peak_lag_days,
                    edge.mechanism.value, edge.evidence_type, edge.is_deprecated,
                    datetime.now(), created_by
                ))
        
        self.conn.commit()
        return version_id
    
    def get_edge_strength_history(
        self, edge_id: str, from_date: Optional[str] = None
    ) -> pd.DataFrame:
        """查询单条边的强度演化历史"""
        
        query = """
            SELECT 
                e.effective_from::date as update_date,
                e.causal_strength,
                e.strength_confidence,
                e.strength_ci_lower,
                e.strength_ci_upper,
                e.evidence_type,
                v.change_type,
                v.change_summary
            FROM causal_edges_history e
            JOIN causal_graph_versions v ON e.graph_version = v.version_id
            WHERE e.edge_id = %s
            {date_filter}
            ORDER BY e.effective_from
        """.format(
            date_filter=f"AND e.effective_from >= '{from_date}'" if from_date else ""
        )
        
        with self.conn.cursor() as cur:
            cur.execute(query, (edge_id,))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
        
        return pd.DataFrame(rows, columns=cols)
    
    def compare_graph_versions(
        self, version_a: str, version_b: str
    ) -> Dict:
        """对比两个版本的因果图差异"""
        
        query = """
            WITH v_a AS (
                SELECT edge_id, causal_strength, strength_confidence
                FROM causal_edges_history WHERE graph_version = %s
            ),
            v_b AS (
                SELECT edge_id, causal_strength, strength_confidence
                FROM causal_edges_history WHERE graph_version = %s
            )
            SELECT 
                COALESCE(a.edge_id, b.edge_id) as edge_id,
                a.causal_strength as strength_v_a,
                b.causal_strength as strength_v_b,
                a.strength_confidence as conf_v_a,
                b.strength_confidence as conf_v_b,
                CASE 
                    WHEN a.edge_id IS NULL THEN 'added'
                    WHEN b.edge_id IS NULL THEN 'removed'
                    WHEN abs(a.causal_strength - b.causal_strength) > 0.1 THEN 'strength_changed'
                    ELSE 'unchanged'
                END as change_type
            FROM v_a a
            FULL OUTER JOIN v_b b ON a.edge_id = b.edge_id
            ORDER BY change_type, edge_id
        """
        
        with self.conn.cursor() as cur:
            cur.execute(query, (version_a, version_b))
            rows = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
        
        df = pd.DataFrame(rows, columns=cols)
        
        return {
            "version_a": version_a,
            "version_b": version_b,
            "total_edges": len(df),
            "added": df[df.change_type == "added"].to_dict("records"),
            "removed": df[df.change_type == "removed"].to_dict("records"),
            "strength_changed": df[df.change_type == "strength_changed"].to_dict("records"),
            "unchanged_count": len(df[df.change_type == "unchanged"]),
        }
    
    def _compute_graph_diff(
        self, parent_version: str, new_graph: MacroRiskCausalGraph
    ) -> Dict:
        """计算图与父版本的差异"""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT graph_snapshot FROM causal_graph_versions WHERE version_id = %s",
                (parent_version,)
            )
            row = cur.fetchone()
            if not row:
                return {}
            parent_snapshot = row[0]
        
        parent_edges = set(parent_snapshot.get("edges", {}).keys())
        new_edges = set(new_graph.edges.keys())
        
        return {
            "added_edges": list(new_edges - parent_edges),
            "removed_edges": list(parent_edges - new_edges),
            "modified_edges": [
                eid for eid in (parent_edges & new_edges)
                if (parent_snapshot["edges"][eid].get("causal_strength") != 
                    new_graph.edges[eid].causal_strength)
            ]
        }
```

---

## 七、输出层升级方案

### 7.1 因果路径可视化（Streamlit组件）

```python
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from pyvis.network import Network
import tempfile

class CausalGraphVisualizer:
    """因果图可视化组件"""
    
    def __init__(self, graph: MacroRiskCausalGraph):
        self.graph = graph
    
    def render_full_graph(
        self,
        highlight_nodes: Optional[List[str]] = None,
        highlight_paths: Optional[List[List[str]]] = None,
        show_strengths: bool = True
    ) -> None:
        """渲染完整因果图（PyVis交互式）"""
        
        net = Network(
            height="700px", width="100%",
            bgcolor="#0e1117", font_color="white",
            directed=True
        )
        net.toggle_physics(True)
        
        # 节点颜色映射（按资产类别）
        color_map = {
            AssetClass.FX: "#4FC3F7",
            AssetClass.RATES: "#FFB74D",
            AssetClass.EQUITY: "#81C784",
            AssetClass.CREDIT: "#EF9A9A",
            AssetClass.COMMODITY: "#CE93D8",
            AssetClass.MACRO: "#FFCC02",
            AssetClass.SENTIMENT: "#F48FB1",
        }
        
        for node_id, node in self.graph.nodes.items():
            color = color_map.get(node.asset_class, "#888888")
            is_highlighted = highlight_nodes and node_id in highlight_nodes
            is_anomalous = node.is_anomalous
            
            # 节点大小：异常节点放大
            size = 30 if is_anomalous else 20
            border_color = "#FF4444" if is_anomalous else color
            
            zscore_text = f" (Z={node.value_zscore:.2f})" if node.value_zscore else ""
            value_text = f"\n当前={node.current_value:.4f}" if node.current_value else ""
            
            net.add_node(
                node_id,
                label=node.display_name + zscore_text,
                title=(
                    f"{node.description}{value_text}\n"
                    f"类型: {node.asset_class.value}\n"
                    f"地域: {node.geography}\n"
                    f"异常分: {node.anomaly_score:.2f}"
                ),
                color={"background": border_color, "border": "#FFFFFF"},
                size=size,
                borderWidth=3 if is_highlighted else 1,
                font={"size": 14, "color": "white"},
            )
        
        # 高亮路径上的边
        highlight_edge_pairs = set()
        if highlight_paths:
            for path in highlight_paths:
                for i in range(len(path)-1):
                    highlight_edge_pairs.add((path[i], path[i+1]))
        
        for edge_id, edge in self.graph.edges.items():
            if edge.is_deprecated:
                continue
            
            is_path_edge = (edge.source_node, edge.target_node) in highlight_edge_pairs
            
            strength = abs(edge.causal_strength)
            direction = "positive" if edge.causal_strength > 0 else "negative"
            
            edge_color = "#44FF44" if direction == "positive" else "#FF4444"
            if is_path_edge:
                edge_color = "#FFFF00"  # 高亮路径用黄色
            
            label = f"{edge.causal_strength:+.2f}" if show_strengths else ""
            
            net.add_edge(
                edge.source_node, edge.target_node,
                title=(
                    f"强度: {edge.causal_strength:+.3f}\n"
                    f"置信度: {edge.strength_confidence:.2f}\n"
                    f"时滞: {edge.peak_lag_days}天\n"
                    f"机制: {edge.mechanism_description}\n"
                    f"类型: {edge.evidence_type}"
                ),
                label=label,
                color=edge_color,
                width=max(1, strength * 5),
                arrows={"to": {"enabled": True, "scaleFactor": 1.5}},
                dashes=edge.is_nonlinear,  # 非线性边用虚线
            )
        
        # 保存并嵌入
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.html', delete=False, encoding='utf-8'
        ) as f:
            net.save_graph(f.name)
            with open(f.name, 'r', encoding='utf-8') as rf:
                html_content = rf.read()
        
        st.components.v1.html(html_content, height=720, scrolling=True)
    
    def render_path_sankey(
        self, source: str, target: str, path_analysis: Dict
    ) -> None:
        """桑基图展示传导路径的相对贡献"""
        
        paths = path_analysis.get("all_paths", [])
        if not paths:
            st.info(f"未找到从 {source} 到 {target} 的传导路径")
            return
        
        # 构建桑基图数据
        all_nodes = []
        node_index = {}
        
        for path_info in paths[:8]:  # 最多显示8条路径
            for node in path_info["path"]:
                if node not in node_index:
                    node_index[node] = len(all_nodes)
                    all_nodes.append(
                        self.graph.nodes[node].display_name 
                        if node in self.graph.nodes else node
                    )
        
        links_source, links_target, links_value, links_color = [], [], [], []
        
        for path_info in paths[:8]:
            path = path_info["path"]
            contribution = path_info["strength_pct"]
            direction = path_info["net_direction"]
            color = f"rgba(68, 255, 68, {min(0.8, contribution/100*2)})" if direction == "positive" \
                    else f"rgba(255, 68, 68, {min(0.8, contribution/100*2)})"
            
            for i in range(len(path)-1):
                links_source.append(node_index[path[i]])
                links_target.append(node_index[path[i+1]])
                links_value.append(max(0.1, contribution))
                links_color.append(color)
        
        fig = go.Figure(data=[go.Sankey(
            arrangement="snap",
            node=dict(
                pad=15, thickness=20, line=dict(color="black", width=0.5),
                label=all_nodes,
                color=["#4FC3F7"] * len(all_nodes)
            ),
            link=dict(
                source=links_source, target=links_target,
                value=links_value, color=links_color
            )
        )])
        
        fig.update_layout(
            title_text=f"传导路径桑基图：{source} → {target}",
            font_size=12,
            paper_bgcolor="#0e1117",
            font_color="white",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_edge_strength_evolution(
        self, edge_id: str, history_df: pd.DataFrame
    ) -> None:
        """展示单条边因果强度的历史演化"""
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=history_df["update_date"],
            y=history_df["causal_strength"],
            mode="lines+markers",
            name="因果强度",
            line=dict(color="#4FC3F7", width=2),
            marker=dict(size=8),
        ))
        
        # 置信区间
        fig.add_trace(go.Scatter(
            x=pd.concat([history_df["update_date"], history_df["update_date"].iloc[::-1]]),
            y=pd.concat([history_df["strength_ci_upper"], history_df["strength_ci_lower"].iloc[::-1]]),
            fill="toself",
            fillcolor="rgba(79, 195, 247, 0.15)",
            line=dict(color="rgba(255,255,255,0)"),
            name="95% CI"
        ))
        
        # 标注变更事件
        changes = history_df[history_df["change_type"].isin(
            ["regime_change", "edge_deprecated", "structural_break"]
        )]
        for _, row in changes.iterrows():
            fig.add_vline(
                x=row["update_date"],
                line_dash="dash", line_color="#FF4444",
                annotation_text=row["change_summary"][:30] if row["change_summary"] else "",
                annotation_position="top"
            )
        
        fig.update_layout(
            title=f"边 {edge_id} 因果强度演化",
            xaxis_title="日期",
            yaxis_title="因果强度",
            paper_bgcolor="#0e1117",
            plot_bgcolor="#1a1a2e",
            font_color="white",
            hovermode="x unified",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_counterfactual_comparison(
        self,
        factual_result: InferenceResult,
        counterfactual_result: InferenceResult,
        target_node_history: pd.Series
    ) -> None:
        """反事实分析对比图"""
        
        fig = go.Figure()
        
        # 历史实际值
        fig.add_trace(go.Scatter(
            x=target_node_history.index,
            y=target_node_history.values,
            name="实际观测值",
            line=dict(color="#4FC3F7", width=2),
        ))
        
        # 反事实预测（标注时间点之后）
        cf_date = counterfactual_result.inference_date
        fig.add_scatter(
            x=[cf_date],
            y=[factual_result.point_estimate],
            mode="markers",
            name=f"实际结果 ({factual_result.point_estimate:.4f})",
            marker=dict(color="#81C784", size=12, symbol="circle"),
        )
        
        fig.add_scatter(
            x=[cf_date],
            y=[counterfactual_result.point_estimate],
            mode="markers",
            name=f"反事实结果 ({counterfactual_result.point_estimate:.4f})",
            marker=dict(color="#EF9A9A", size=12, symbol="diamond"),
        )
        
        # 添加差异箭头
        fig.add_annotation(
            x=cf_date,
            y=(factual_result.point_estimate + counterfactual_result.point_estimate) / 2,
            text=f"差异: {counterfactual_result.point_estimate - factual_result.point_estimate:+.4f}",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#FFCC02",
            font=dict(color="#FFCC02", size=14),
        )
        
        fig.update_layout(
            title=f"反事实分析：{counterfactual_result.target_node}",
            paper_bgcolor="#0e1117",
            plot_bgcolor="#1a1a2e",
            font_color="white",
            height=450
        )
        
        st.plotly_chart(fig, use_container_width=True)
```

### 7.2 日报输出模板

```python
class DailyBriefingGenerator:
    """日报生成器（含因果推理结果）"""
    
    def generate(
        self,
        daily_state: Dict,
        inference_results: List[InferenceResult],
        path_analyses: List[Dict],
        llm_narrative: str,
        confounding_warnings: List[Dict]
    ) -> str:
        """生成结构化日报"""
        
        alert_emoji = {
            "green": "绿色", "yellow": "黄色",
            "orange": "橙色", "red": "红色"
        }
        level = daily_state.get("alert_level", "green")
        
        # 汇总因果推理关键数字
        key_causal_findings = []
        for result in inference_results:
            if result.inference_type == "interventional" and result.confidence > 0.6:
                key_causal_findings.append(
                    f"- **{result.source_node}→{result.target_node}**："
                    f"因果效应={result.point_estimate:+.4f} "
                    f"[置信区间: {result.ci_lower:+.4f}, {result.ci_upper:+.4f}]，"
                    f"已调整混淆变量：{', '.join(result.confounders_adjusted) or '无'}"
                )
        
        # 混淆警告摘要
        conf_warnings_text = ""
        spurious = [w for w in confounding_warnings if w.get("is_likely_spurious")]
        if spurious:
            conf_warnings_text = "\n### 虚假相关警告\n" + "\n".join(
                f"- {w['warning']}" for w in spurious
            )
        
        # 主路径摘要
        dominant_paths_text = ""
        for pa in path_analyses:
            dp = pa.get("dominant_path")
            if dp:
                dominant_paths_text += (
                    f"- {pa['source']}→{pa['target']}：主路径 `{dp['path_str']}`，"
                    f"贡献{dp['strength_pct']:.1f}%，总时滞{dp['total_lag_days']}天\n"
                )
        
        report = f"""# 全球宏观风险日报 — {daily_state['date']}

## 预警级别：{alert_emoji[level]} {level.upper()}

---

## 因果图状态摘要

**当前市场制度**：{daily_state.get('current_regime', 'normal')}
**异常节点**：{', '.join(daily_state.get('anomalous_nodes', [])) or '无'}

---

## 关键因果推理结果

### 干预推理（净因果效应）
{chr(10).join(key_causal_findings) or '当日无显著因果信号'}

### 主要传导路径
{dominant_paths_text or '无激活路径'}

{conf_warnings_text}

---

## 深度分析（LLM因果叙事）

{llm_narrative}

---

## 数据说明

| 指标 | 说明 |
|------|------|
| 因果效应 | 使用 do-calculus 后门调整估计，非纯相关 |
| 置信区间 | 基于历史数据bootstrapped 95% CI |
| 时滞 | 为峰值效应时滞，非全部效应时滞 |
| 混淆调整 | 使用最小充分调整集（后门准则） |

*本报告由因果图引擎+LLM协同生成，因果效应估计存在不确定性，仅供参考。*
"""
        return report
```

---

## 八、Python实现方案与库选型

### 8.1 核心因果库对比与角色分工

| 库 | 版本 | 定位 | 在本系统中的角色 | 局限性 |
|----|------|------|----------------|--------|
| **DoWhy** | ≥0.11 | 因果推理框架 | 干预推理（do-calculus）、因果效应识别与估计、反驳检验 | 不支持时序数据的原生结构 |
| **NetworkX** | ≥3.0 | 图算法库 | 因果图存储、路径搜索、d-separation计算、拓扑排序 | 纯图结构，无统计推理 |
| **pgmpy** | ≥0.1.25 | 概率图模型 | 贝叶斯网络结构学习（PC算法）、条件概率推理、因果发现 | 离散变量假设，连续变量需离散化 |
| **causal-learn** | ≥0.1.3 | 因果发现 | PC算法、FCI算法用于新边发现，支持连续变量 | 对数据量要求较高（>500样本） |
| **ruptures** | ≥1.1 | 时序断点检测 | 结构断裂检测（CUSUM、PELT算法） | 仅检测断点，不提供因果解释 |
| **statsmodels** | ≥0.14 | 统计模型 | Granger因果检验、协整检验、VECM建模 | 线性假设 |
| **pyvis** | ≥0.3 | 图可视化 | 交互式因果图展示（集成到Streamlit） | 大图（>200节点）性能下降 |

### 8.2 完整依赖配置

```toml
# pyproject.toml（poetry格式）
[tool.poetry.dependencies]
python = "^3.10"

# 因果推理核心
dowhy = "^0.11"
causal-learn = "^0.1.3"
pgmpy = "^0.1.25"

# 图算法
networkx = "^3.2"
pyvis = "^0.3"

# 时序分析
statsmodels = "^0.14"
ruptures = "^1.1"

# 数据处理
pandas = "^2.1"
numpy = "^1.26"
scipy = "^1.11"
scikit-learn = "^1.3"

# 可视化
streamlit = "^1.29"
plotly = "^5.18"

# LLM
anthropic = "^0.20"

# 数据库
psycopg2-binary = "^2.9"
sqlalchemy = "^2.0"

# 调度
apscheduler = "^3.10"
```

### 8.3 完整系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PMS 全球宏观风险传导监测Agent                          │
│                     (因果图增强版 v2.0)                                    │
└─────────────────────────────────────────────────────────────────────────┘

                              每日定时触发
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│ 第零层：初始化引擎                                                          │
│   build_initial_causal_graph() → MacroRiskCausalGraph v1.0              │
│   LLM生成基线白皮书 + 初始因果强度（来自文献/专家知识）                       │
│   GraphVersionManager.save_new_version(created_by="init")               │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│ 第一层：数据采集层                                                          │
│   MarketDataCollector: Bloomberg/Yahoo/DRAMExchange API                 │
│   NewsCollector: Reuters, Bloomberg News, SEC EDGAR                     │
│   → 更新 CORE_NODES 的 current_value / value_zscore                     │
│   → 标记 is_anomalous（Z-score > 2.5）                                   │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│ 第二层：分析引擎层（并行执行）                                                │
│                                                                          │
│  ┌────────────────────┐  ┌────────────────────┐  ┌──────────────────┐   │
│  │  因果发现模块        │  │   因果推理模块       │  │  LLM协同模块      │   │
│  │ CausalDiscovery   │  │ CausalReasoning    │  │ LLMOrchestrator │   │
│  │                    │  │                    │  │                  │   │
│  │ - 验证已有边         │  │ - 观察推理           │  │ - 事件提取        │   │
│  │ - 检测结构断裂       │  │ - 干预推理(do)       │  │ - 假设生成        │   │
│  │ - 发现新关系         │  │ - 反事实推理         │  │ - 统计验证        │   │
│  │ - 贝叶斯更新强度     │  │ - 路径分析           │  │ - 互相校正        │   │
│  │ - 图版本升级决策     │  │ - 混淆检测           │  │ - 报告叙事生成    │   │
│  └────────────────────┘  └────────────────────┘  └──────────────────┘   │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│ 第三层：记忆存储层（PostgreSQL）                                             │
│                                                                          │
│  causal_graph_versions     — 图谱版本快照+diff                            │
│  causal_edges_history      — 边强度演化时序                                │
│  causal_nodes_history      — 节点状态历史                                  │
│  causal_inference_log      — 推理结果记录                                  │
│  structural_break_events   — 结构断裂事件                                  │
│  daily_graph_state         — 每日图状态快照                                │
│  (原有) event_milestones   — 事件里程碑                                    │
│  (原有) logic_log          — 逻辑日志                                      │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────┐
│ 第四层：输出层（Streamlit Dashboard）                                       │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐   │
│  │  每日因果简报      │  │  月度因果复盘     │  │  实时因果预警         │   │
│  │                  │  │                  │  │                      │   │
│  │ - 干预效应摘要    │  │ - 图谱版本对比   │  │ - 激活路径可视化      │   │
│  │ - 主传导路径图    │  │ - 因果强度演化   │  │ - 反事实情景分析      │   │
│  │ - 混淆警告        │  │ - 制度切换分析   │  │ - do-calculus推理     │   │
│  │ - LLM叙事分析     │  │ - 新发现关系     │  │ - 置信区间展示        │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

数据流向：
  市场数据  ───→  节点值更新  ───→  推理引擎  ───→  结果存储  ───→  可视化输出
  新闻文本  ───→  LLM事件提取 ───→  统计验证  ───→  图版本更新 ───→  日报生成
  历史数据  ───→  因果发现    ───→  贝叶斯更新 ───→  人工审核   ───→  图结构演化

因果逻辑流：
  观察到 X 异常
     │
     ├── 观察推理: P(Y|X=x)        ← 相关性，含混淆
     ├── 干预推理: P(Y|do(X=x))    ← 净因果效应
     ├── 路径分析: X→M→Y           ← 传导机制分解
     ├── 混淆检测: 是否有 Z→X,Z→Y  ← 虚假相关识别
     └── 反事实:  若X=x', Y=?     ← 情景分析/政策评估
```

---

## 九、与现有设计的对比总结

| 维度 | 现有设计（5条线性链） | 因果图增强版 |
|------|---------------------|------------|
| **传导建模** | 5条独立线性链 | 完整DAG（17+节点，20+边） |
| **链间交叉效应** | 不支持 | 原生支持（图结构天然包含） |
| **混淆变量** | 未识别 | 自动检测，后门准则调整 |
| **阈值设定** | 静态硬编码（如KRW<1550） | 动态、非线性、激活条件驱动 |
| **政策干预评估** | 无 | do-calculus干预推理 |
| **历史复盘** | 叙述性 | 形式化反事实推理+量化差异 |
| **图结构更新** | 不更新 | 日度贝叶斯更新+结构断裂检测 |
| **版本管理** | 无 | 完整版本历史+diff对比 |
| **相关性 vs 因果性** | 混淆 | 明确区分，标注推理类型 |
| **LLM角色** | 全依赖LLM判断 | LLM+统计引擎互相校正 |
| **不确定性量化** | 无 | 置信区间+p值+置信度分级 |
| **可解释性** | 文字描述 | 因果路径图+贡献度分解 |

---

核心设计原则回顾：**因果图不是替代LLM，而是为LLM的定性判断提供形式化的数学骨架。** LLM负责从非结构化信息中提取"哪里可能有因果"，统计引擎负责回答"这个因果效应有多大、是否可信"，两者通过协调器形成互相校正的闭环，最终输出既有经济学直觉支撑、又有统计可信度的因果推理报告。
