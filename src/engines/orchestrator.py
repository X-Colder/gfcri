"""
LLM-Causal Graph orchestrator.

Coordinates between the LLM (event extraction, narrative generation)
and the formal causal reasoning engine (statistical validation).

The Anthropic client is configured from ``src.config.Settings``:
    api_key        → settings.anthropic_api_key
    base_url       → settings.anthropic_base_url
    model          → settings.anthropic_model

Usage (explicit settings injection, preferred for testing):
    orchestrator = LLMCausalOrchestrator(graph, reasoning, discovery, settings=my_settings)

Usage (implicit global settings, backward-compatible default):
    orchestrator = LLMCausalOrchestrator(graph, reasoning, discovery)
"""

from __future__ import annotations

import json
from typing import Any, Optional, TYPE_CHECKING

from anthropic import Anthropic
from loguru import logger

from src.config import settings as _global_settings
from src.models.graph import MacroRiskCausalGraph
from src.engines.reasoning import CausalReasoningEngine
from src.engines.discovery import CausalDiscoveryEngine

if TYPE_CHECKING:
    from src.config import Settings


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

CAUSAL_EXTRACTION_PROMPT = """你是宏观经济因果关系分析专家。请从以下市场新闻中提取因果关系假设。

已知因果图核心节点：
{node_list}

请提取文本中暗示的因果关系，以JSON格式输出：
{{
  "events": [
    {{
      "event_summary": "事件摘要",
      "affected_nodes": ["节点ID"],
      "causal_hypotheses": [
        {{
          "source_node": "节点ID",
          "target_node": "节点ID",
          "direction": "positive|negative",
          "estimated_magnitude": "small|medium|large",
          "mechanism": "传导机制描述",
          "confidence": "low|medium|high"
        }}
      ]
    }}
  ]
}}

仅输出JSON。"""

NARRATIVE_PROMPT = """你是宏观风险分析师。基于以下因果推理结果，生成一份简洁的风险分析报告。

【今日数据】
{daily_state}

【因果推理结果】
{inference_results}

请生成日报，要求：
1. 用因果语言描述传导链
2. 区分"因果效应"和"相关性"
3. 标注置信度和不确定性
4. 给出预警级别（绿/黄/橙/红）

输出格式：Markdown，500字以内。"""

GFCRI_NARRATIVE_PROMPT = """你是一位顶级宏观风险分析师，为普通投资者写每日风险简报。

要求：主题明确、观点突出、证据链充足、逻辑严谨。不说废话，每句话都要有信息量。

【今日风险指数】
GFCRI: {gfcri_value}/100 ({alert_level})
子指数: {sub_indices_summary}

{delta_section}

【美国经济基本面（FRED实时数据）】
{fred_fundamentals}

【中国经济基本面（国家统计局数据）】
{china_fundamentals}

【异常指标】
{anomalous_nodes_detail}

【正在传导的风险链】
{active_chains_detail}

【因果推理结果】
{path_analysis_summary}

【近期结构性变化】
{structural_breaks}

【即将发生的重要事件】
{upcoming_events}

═══ 输出格式（严格遵循） ═══

## 核心判断

一句话结论。格式："风险指数 XX → XX（+/-N），核心原因是 [具体原因]。"

## 关键证据

用"因为A → 所以B → 导致C"的因果链形式列出 2-3 条关键证据，每条引用具体数据：

1. **[证据标题]**：[具体数据] → [传导逻辑] → [影响]
2. **[证据标题]**：[具体数据] → [传导逻辑] → [影响]

## 下周焦点

列出 1-2 个即将到来的关键事件，说明"如果结果偏X，会怎样；如果偏Y，会怎样"。

## 行动建议

1-2 条明确建议，说清楚"做什么"和"为什么"。

═══ 写作红线 ═══

- 不超过 400 字
- 不用英文变量名，只用中文名称
- 不用"做空/对冲/敞口"等专业术语
- 每个观点必须有数据支撑（引用具体数字）
- 不重复数据本身（读者已经看到了数据面板），聚焦在"为什么"和"接下来"
- 如果变化不大（GFCRI 变动<3 分），全文控制在 150 字内，只写核心判断+行动建议"""


GFCRI_NARRATIVE_EN_PROMPT = """You are a senior institutional macro-risk analyst writing a concise daily risk brief for professional subscribers, research desks, and risk teams.

Requirements: Clear thesis, strong evidence, tight logic, and no investment advice. Every sentence must carry information. If any input labels are Chinese, translate them into natural institutional English and do not output Chinese text.

【Today's Risk Index】
GFCRI: {gfcri_value}/100 ({alert_level})
Sub-indices: {sub_indices_summary}

{delta_section}

【US Economic Fundamentals (FRED)】
{fred_fundamentals}

【China Economic Fundamentals】
{china_fundamentals}

【Anomalous Indicators】
{anomalous_nodes_detail}

【Active Transmission Chains】
{active_chains_detail}

【Transmission Analysis】
{path_analysis_summary}

【Structural Changes】
{structural_breaks}

【Upcoming Events】
{upcoming_events}

═══ Output Format (strict) ═══

## Key Judgment

One sentence: "Risk index XX → XX (+/-N), driven by [specific cause]."

## Critical Evidence

2-3 evidence chains in "Because A → Therefore B → Leading to C" format, each citing specific data:

1. **[Title]**: [data] → [transmission logic] → [impact]
2. **[Title]**: [data] → [transmission logic] → [impact]

## Next Week's Focus

1-2 upcoming events: "If result leans X → consequence; if leans Y → consequence."

## Monitoring Implications

1-2 clear monitoring implications. Frame them as risk-review or scenario-monitoring steps, not trading instructions.

═══ Rules ═══

- Max 400 words
- Use professional but plain institutional language
- Do not provide trading, hedging, portfolio-allocation, buy, or sell recommendations
- Every claim must cite a number
- If change is small (GFCRI delta < 3), keep entire output under 100 words"""


SI_EN: dict[str, str] = {
    "SI_RATES": "Rates and central banks",
    "SI_FX": "Global FX",
    "SI_US_EQUITY": "US equities",
    "SI_ASIA_EQUITY": "Asia equities",
    "SI_EUROPE": "Europe markets",
    "SI_CREDIT": "Credit and default risk",
    "SI_BANKING": "Banks and real estate",
    "SI_COMMODITY": "Commodities and trade",
    "SI_TRADE_SPILLOVER": "Trade-dependency spillover",
    "SI_SENTIMENT": "Sentiment and safe-haven demand",
}

CHAIN_EN: dict[str, str] = {
    "fed_cascade": "Central-bank tightening cascade",
    "dollar_squeeze": "Dollar squeeze",
    "credit_contagion": "Credit contagion",
    "housing_bank_doom": "Real-estate banking stress",
    "consumer_recession": "Consumer recession channel",
    "ai_semi_cycle": "AI and semiconductor cycle",
    "safe_haven_flight": "Safe-haven flight",
    "europe_contagion": "Europe contagion",
    "china_shockwave": "China shockwave",
    "yen_carry_unwind": "Yen carry unwind",
    "crypto_contagion": "Crypto risk-appetite channel",
    "food_energy_shock": "Food and energy shock",
}

FRED_EN: dict[str, tuple[str, str]] = {
    "fred_effr": ("Effective federal funds rate", "%"),
    "fred_t10y2y": ("10Y-2Y Treasury spread", "%"),
    "fred_bbb_spread": ("US BBB OAS", "%"),
    "fred_hy_spread": ("US high-yield OAS", "%"),
    "fred_mortgage30": ("30Y mortgage rate", "%"),
    "fred_unrate": ("US unemployment rate", "%"),
    "fred_cpi": ("US CPI index", ""),
    "fred_pce": ("US core PCE index", ""),
    "fred_indpro": ("US industrial production", ""),
    "fred_m2": ("US M2 money supply", " USD bn"),
    "fred_umcsent": ("US consumer sentiment", ""),
    "fred_house": ("Case-Shiller home price index", ""),
    "fred_walcl": ("Federal Reserve balance sheet", " USD mn"),
    "fred_ic_spread": ("US AAA corporate yield", "%"),
    "fred_sofr": ("SOFR", "%"),
    "sofr_effr_spread": ("SOFR-EFFR spread", " bps"),
    "fred_baa10y_spread": ("Moody's Baa-10Y spread", "%"),
    "fred_euro_hy_spread": ("Euro high-yield OAS", "%"),
    "fred_all_loan_delinquency": ("US bank loan delinquency rate", "%"),
}

CHINA_EN: dict[str, str] = {
    "cn_pmi": "China manufacturing PMI",
    "cn_cpi_yoy": "China CPI YoY",
    "cn_ppi_yoy": "China PPI YoY",
    "cn_m2_yoy": "China M2 YoY",
    "cn_m1_yoy": "China M1 YoY",
    "cn_social_finance": "China total social financing",
    "cn_social_finance_yoy": "China social financing YoY",
    "cn_retail_yoy": "China retail sales YoY",
    "cn_lpr_1y": "China 1Y LPR",
    "cn_lpr_5y": "China 5Y LPR",
}


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class LLMCausalOrchestrator:
    """Coordinates the Anthropic LLM with causal graph engines.

    Args:
        causal_graph: MacroRiskCausalGraph instance.
        reasoning_engine: Instantiated CausalReasoningEngine.
        discovery_engine: Instantiated CausalDiscoveryEngine.
        settings: Optional Settings instance.  When omitted the module-level
            global ``settings`` object (from ``src.config``) is used, which
            preserves backward compatibility.
    """

    def __init__(
        self,
        causal_graph: MacroRiskCausalGraph,
        reasoning_engine: CausalReasoningEngine,
        discovery_engine: CausalDiscoveryEngine,
        settings: "Optional[Settings]" = None,
    ) -> None:
        self.graph = causal_graph
        self.engine = reasoning_engine
        self.discovery = discovery_engine
        self._settings = settings or _global_settings

        # Initialise the Anthropic client eagerly so configuration errors
        # surface at construction time rather than at first API call.
        self._client = Anthropic(
            api_key=self._settings.anthropic_api_key,
            base_url=self._settings.anthropic_base_url,
        )
        logger.info(
            f"LLMCausalOrchestrator initialised "
            f"(model={self._settings.anthropic_model}, "
            f"base_url={self._settings.anthropic_base_url})"
        )

    # ------------------------------------------------------------------
    # 1. Extract causal hypotheses from news text
    # ------------------------------------------------------------------

    def extract_causal_hypotheses(self, news_text: str) -> dict[str, Any]:
        """Parse a news article and extract structured causal hypotheses.

        The LLM returns a JSON object containing an ``events`` list.  Each
        event in turn carries a ``causal_hypotheses`` list of node-level
        causal relationship objects.

        After parsing, every hypothesis is annotated with:
        - ``in_existing_graph`` — whether the (source, target) pair is
          already represented by a non-deprecated edge.
        - ``source_node_known`` / ``target_node_known`` — whether the
          node IDs are present in the graph.

        Args:
            news_text: Raw news text (headline + body, etc.).

        Returns:
            dict with keys ``events`` (list), ``parse_error`` (bool, optional),
            ``error`` (str, optional).
        """
        if not news_text or not news_text.strip():
            logger.warning("extract_causal_hypotheses: empty news_text received")
            return {"events": [], "parse_error": False}

        node_list = "\n".join(
            f"- {nid}: {n.display_name} ({n.asset_class.value}, {n.geography})"
            for nid, n in self.graph.nodes.items()
        )

        prompt_content = (
            CAUSAL_EXTRACTION_PROMPT.format(node_list=node_list)
            + f"\n\n【待分析文本】\n{news_text.strip()}"
        )
        logger.debug(
            f"extract_causal_hypotheses: sending {len(news_text)} chars to LLM"
        )

        try:
            response = self._client.messages.create(
                model=self._settings.anthropic_model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt_content}],
            )
            text = response.content[0].text.strip()
        except Exception as exc:
            logger.error(f"LLM call failed in extract_causal_hypotheses: {exc}")
            return {"events": [], "error": str(exc)}

        try:
            result: dict[str, Any] = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("extract_causal_hypotheses: LLM response was not valid JSON")
            return {"events": [], "parse_error": True, "raw_response": text}

        # Annotate hypotheses with graph cross-check.
        existing_pairs = {
            (e.source_node, e.target_node)
            for e in self.graph.edges.values()
            if not e.is_deprecated
        }
        for event in result.get("events", []):
            for hyp in event.get("causal_hypotheses", []):
                src = hyp.get("source_node", "")
                tgt = hyp.get("target_node", "")
                hyp["in_existing_graph"] = (src, tgt) in existing_pairs
                hyp["source_node_known"] = src in self.graph.nodes
                hyp["target_node_known"] = tgt in self.graph.nodes

        num_hypotheses = sum(
            len(ev.get("causal_hypotheses", [])) for ev in result.get("events", [])
        )
        logger.info(
            f"extract_causal_hypotheses: "
            f"{len(result.get('events', []))} events, "
            f"{num_hypotheses} causal hypotheses extracted"
        )
        return result

    # ------------------------------------------------------------------
    # 2. Generate daily causal narrative
    # ------------------------------------------------------------------

    def generate_daily_narrative(
        self,
        daily_state: dict[str, Any],
        inference_results: list[dict[str, Any]],
    ) -> str:
        """Generate a daily macro-risk causal narrative in Markdown format.

        Args:
            daily_state: Dict describing the current graph state, e.g.:
                {
                  "date": "2026-06-27",
                  "current_regime": "risk_off",
                  "anomalous_nodes": [...],
                  "top_risk_transmissions": [...],
                }
            inference_results: List of inference dicts from
                CausalReasoningEngine (``point_estimate``,
                ``natural_language_summary``, etc.).

        Returns:
            Markdown string.  On LLM failure returns an error notice
            string so callers can always treat the return value as
            displayable text.
        """
        state_str = json.dumps(daily_state, ensure_ascii=False, indent=2, default=str)
        results_str = json.dumps(
            inference_results[:10], ensure_ascii=False, indent=2, default=str
        )

        try:
            response = self._client.messages.create(
                model=self._settings.anthropic_model,
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": NARRATIVE_PROMPT.format(
                            daily_state=state_str[:3000],
                            inference_results=results_str[:3000],
                        ),
                    }
                ],
            )
            narrative = response.content[0].text
            logger.info(
                f"generate_daily_narrative: generated {len(narrative)} chars"
            )
            return narrative
        except Exception as exc:
            logger.error(f"Narrative generation failed: {exc}")
            return (
                f"*报告生成失败: {exc}*\n\n"
                f"异常节点: "
                f"{[n.get('node_id') for n in daily_state.get('anomalous_nodes', [])]}"
            )

    # ------------------------------------------------------------------
    # 3. Generate GFCRI daily report narrative
    # ------------------------------------------------------------------

    def generate_gfcri_report(
        self,
        gfcri_result: dict[str, Any],
        inference_summary: dict[str, Any],
        structural_breaks: list[dict[str, Any]] | None = None,
        upcoming_events: list[dict[str, Any]] | None = None,
        prev_gfcri_result: dict[str, Any] | None = None,
        fred_data: dict[str, float] | None = None,
        china_data: dict[str, float] | None = None,
    ) -> str:
        from src.i18n import cn_name, cn_short, SI_CN, CHAIN_CN

        sub_indices = gfcri_result.get("sub_indices", {})
        si_summary = ", ".join(
            f"{SI_CN.get(si_id, si['name'])}: {si['score']:.1f}"
            for si_id, si in sub_indices.items()
        )
        si_summary_en = ", ".join(
            f"{SI_EN.get(si_id, si_id)}: {si['score']:.1f}"
            for si_id, si in sub_indices.items()
        )

        node_contribs = gfcri_result.get("node_contributions", {})
        anomalous = []
        anomalous_en = []
        for nid, info in node_contribs.items():
            if info.get("is_anomalous"):
                val = info.get("current_value")
                val_str = f"当前值={val:.2f}" if val is not None else ""
                val_str_en = f"current={val:.2f}" if val is not None else ""
                geo = self.graph.nodes[nid].geography if nid in self.graph.nodes else ""
                geo_str = f"[{geo}]" if geo and geo != "GLOBAL" else ""
                display_name = (
                    self.graph.nodes[nid].display_name
                    if nid in self.graph.nodes
                    else info.get("display_name") or nid
                )
                anomalous.append(
                    f"- {cn_name(nid)}{geo_str}: 偏离正常范围 {abs(info['zscore']):.1f} 倍, "
                    f"{val_str}"
                )
                anomalous_en.append(
                    f"- {display_name}{geo_str}: {abs(info['zscore']):.1f} standard deviations from normal, "
                    f"{val_str_en}"
                )
        anomalous_str = "\n".join(anomalous) if anomalous else "无异常节点"
        anomalous_str_en = "\n".join(anomalous_en) if anomalous_en else "No anomalous indicators"

        chains = gfcri_result.get("chains", [])
        active = [c for c in chains if c.get("active")]
        chains_lines = []
        chains_lines_en = []
        for c in active:
            path_nodes = c.get("path", [])
            path_cn = [cn_short(nid) for nid in path_nodes]
            path_en = [
                self.graph.nodes[nid].display_name if nid in self.graph.nodes else nid
                for nid in path_nodes
            ]
            geo_set = set()
            for nid in path_nodes:
                if nid in self.graph.nodes:
                    g = self.graph.nodes[nid].geography
                    if g and g != "GLOBAL":
                        geo_set.add(g)
            geo_tag = f"[涉及: {', '.join(geo_set)}]" if geo_set else ""
            node_vals = []
            node_vals_en = []
            for nid in path_nodes:
                n = self.graph.nodes.get(nid)
                if n and n.current_value is not None:
                    node_vals.append(f"{cn_short(nid)}={n.current_value:.1f}")
                    node_vals_en.append(f"{n.display_name}={n.current_value:.1f}")
            vals_str = f" ({', '.join(node_vals[:3])})" if node_vals else ""
            vals_str_en = f" ({', '.join(node_vals_en[:3])})" if node_vals_en else ""
            chains_lines.append(
                f"- {CHAIN_CN.get(c['id'], {}).get('name', c['name'])}{geo_tag}: "
                f"{' → '.join(path_cn)} "
                f"(压力={c['stress']:.1f}){vals_str}"
            )
            chains_lines_en.append(
                f"- {CHAIN_EN.get(c.get('id'), c.get('id', c.get('name', 'Transmission channel')))}{geo_tag}: "
                f"{' -> '.join(path_en)} "
                f"(stress={c['stress']:.1f}){vals_str_en}"
            )
        chains_str = "\n".join(chains_lines) if chains_lines else "无活跃传导链"
        chains_str_en = "\n".join(chains_lines_en) if chains_lines_en else "No active transmission channels"

        path_str = json.dumps(inference_summary, ensure_ascii=False, default=str)
        path_str_en = json.dumps(inference_summary, ensure_ascii=True, default=str)

        breaks_str = "无"
        breaks_str_en = "None"
        if structural_breaks:
            detected = [b for b in structural_breaks if b.get("break_detected")]
            if detected:
                breaks_str = "\n".join(
                    f"- {cn_name(b['source'])} → {cn_name(b['target'])}: "
                    f"断裂日期={str(b.get('break_date', ''))[:10]}, 不稳定比={b['instability_ratio']:.2f}"
                    for b in detected[:10]
                )
                breaks_str_en = "\n".join(
                    f"- {self.graph.nodes[b['source']].display_name if b['source'] in self.graph.nodes else b['source']} -> "
                    f"{self.graph.nodes[b['target']].display_name if b['target'] in self.graph.nodes else b['target']}: "
                    f"break date={str(b.get('break_date', ''))[:10]}, instability ratio={b['instability_ratio']:.2f}"
                    for b in detected[:10]
                )

        events_str = "无近期重大事件"
        events_str_en = "No major scheduled events in the next window"
        if upcoming_events:
            events_str = "\n".join(
                f"- {e['date']} {e['name']} (影响: {', '.join(cn_name(n) for n in e.get('affected_nodes', []))})"
                for e in upcoming_events
            )
            events_str_en = "\n".join(
                f"- {e['date']} {e['name']} (affected: {', '.join(self.graph.nodes[n].display_name if n in self.graph.nodes else n for n in e.get('affected_nodes', []))})"
                for e in upcoming_events
            )

        # Build delta section
        delta_section = ""
        delta_section_en = ""
        if prev_gfcri_result:
            prev_gfcri_val = prev_gfcri_result.get("gfcri", 0)
            curr_gfcri_val = gfcri_result["gfcri"]
            delta = curr_gfcri_val - prev_gfcri_val
            delta_section = f"【与昨日对比】\n"
            delta_section += f"GFCRI 变化: {prev_gfcri_val:.1f} → {curr_gfcri_val:.1f} ({delta:+.1f})\n"
            delta_section_en = "【Change vs Previous Run】\n"
            delta_section_en += f"GFCRI: {prev_gfcri_val:.1f} -> {curr_gfcri_val:.1f} ({delta:+.1f})\n"

            prev_contribs = prev_gfcri_result.get("node_contributions", {})
            prev_anomalous_set = {nid for nid, info in prev_contribs.items() if info.get("is_anomalous")}
            curr_anomalous_set = {nid for nid, info in node_contribs.items() if info.get("is_anomalous")}
            new_anomalous = curr_anomalous_set - prev_anomalous_set
            recovered = prev_anomalous_set - curr_anomalous_set
            if new_anomalous:
                delta_section += f"新增异常: {', '.join(cn_name(n) for n in new_anomalous)}\n"
                delta_section_en += (
                    "New anomalies: "
                    + ", ".join(self.graph.nodes[n].display_name if n in self.graph.nodes else n for n in new_anomalous)
                    + "\n"
                )
            if recovered:
                delta_section += f"恢复正常: {', '.join(cn_name(n) for n in recovered)}\n"
                delta_section_en += (
                    "Recovered indicators: "
                    + ", ".join(self.graph.nodes[n].display_name if n in self.graph.nodes else n for n in recovered)
                    + "\n"
                )
            if not new_anomalous and not recovered:
                delta_section += "异常指标无变化\n"
                delta_section_en += "No change in anomalous indicators\n"

            prev_chains = prev_gfcri_result.get("chains", [])
            prev_active = {c["id"] for c in prev_chains if c.get("active")}
            curr_active = {c["id"] for c in chains if c.get("active")}
            new_chains = curr_active - prev_active
            deactivated = prev_active - curr_active
            if new_chains:
                delta_section += f"新激活传导链: {', '.join(CHAIN_CN.get(cid, {}).get('name', cid) for cid in new_chains)}\n"
                delta_section_en += f"New active channels: {', '.join(CHAIN_EN.get(cid, cid) for cid in new_chains)}\n"
            if deactivated:
                delta_section += f"转为休眠: {', '.join(CHAIN_CN.get(cid, {}).get('name', cid) for cid in deactivated)}\n"
                delta_section_en += f"Deactivated channels: {', '.join(CHAIN_EN.get(cid, cid) for cid in deactivated)}\n"

            if abs(delta) < 3 and not new_anomalous and not recovered and not new_chains and not deactivated:
                delta_section += "总体判断: 今天市场波动不大，风险格局基本稳定\n"
                delta_section_en += "Overall: market movement is limited and the risk regime is broadly stable\n"
        else:
            delta_section = "【与昨日对比】\n无昨日数据（首次运行或数据缺失）\n"
            delta_section_en = "【Change vs Previous Run】\nNo previous data available\n"

        # Build FRED fundamentals section
        fred_fundamentals = "无FRED数据"
        fred_fundamentals_en = "No FRED data"
        if fred_data:
            lines = []
            lines_en = []
            label_map = {
                "fred_effr": ("联邦基金利率", "%"),
                "fred_t10y2y": ("10Y-2Y收益率利差", "%"),
                "fred_bbb_spread": ("BBB级信用利差", "%"),
                "fred_hy_spread": ("高收益债利差", "%"),
                "fred_mortgage30": ("30年房贷利率", "%"),
                "fred_unrate": ("失业率", "%"),
                "fred_cpi": ("CPI指数", ""),
                "fred_pce": ("核心PCE指数", ""),
                "fred_indpro": ("工业生产指数", ""),
                "fred_m2": ("M2货币供应", "亿美元"),
                "fred_umcsent": ("消费者信心指数", ""),
                "fred_house": ("Case-Shiller房价指数", ""),
                "fred_walcl": ("美联储资产负债表", "百万美元"),
                "fred_ic_spread": ("投资级信用利差", "%"),
            }
            for key, val in fred_data.items():
                label, unit = label_map.get(key, (key, ""))
                lines.append(f"- {label}: {val:.2f}{unit}")
                label_en, unit_en = FRED_EN.get(key, (key, ""))
                lines_en.append(f"- {label_en}: {val:.2f}{unit_en}")
            fred_fundamentals = "\n".join(lines)
            fred_fundamentals_en = "\n".join(lines_en)

        # Build China fundamentals section
        china_fundamentals = "无中国宏观数据"
        china_fundamentals_en = "No China macro data"
        if china_data:
            from src.data.china_macro import CHINA_INDICATOR_LABELS
            lines = []
            lines_en = []
            for key, val in china_data.items():
                if key.endswith("_date"):
                    continue
                label = CHINA_INDICATOR_LABELS.get(key, key)
                lines.append(f"- {label}: {val:.2f}")
                lines_en.append(f"- {CHINA_EN.get(key, key)}: {val:.2f}")
            if lines:
                china_fundamentals = "\n".join(lines)
            if lines_en:
                china_fundamentals_en = "\n".join(lines_en)

        prompt = GFCRI_NARRATIVE_PROMPT.format(
            gfcri_value=gfcri_result["gfcri"],
            alert_level=gfcri_result["alert_level"],
            sub_indices_summary=si_summary,
            delta_section=delta_section,
            fred_fundamentals=fred_fundamentals,
            china_fundamentals=china_fundamentals,
            anomalous_nodes_detail=anomalous_str,
            active_chains_detail=chains_str,
            path_analysis_summary=path_str[:2000],
            structural_breaks=breaks_str,
            upcoming_events=events_str,
        )

        try:
            response = self._client.messages.create(
                model=self._settings.anthropic_model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            narrative = response.content[0].text
            logger.info(
                f"generate_gfcri_report: generated {len(narrative)} chars"
            )

            # Also generate English version
            en_narrative = ""
            try:
                en_prompt = GFCRI_NARRATIVE_EN_PROMPT.format(
                    gfcri_value=gfcri_result["gfcri"],
                    alert_level=gfcri_result["alert_level"],
                    sub_indices_summary=si_summary_en,
                    delta_section=delta_section_en,
                    fred_fundamentals=fred_fundamentals_en,
                    china_fundamentals=china_fundamentals_en,
                    anomalous_nodes_detail=anomalous_str_en,
                    active_chains_detail=chains_str_en,
                    path_analysis_summary=path_str_en[:2000],
                    structural_breaks=breaks_str_en,
                    upcoming_events=events_str_en,
                )
                en_response = self._client.messages.create(
                    model=self._settings.anthropic_model,
                    max_tokens=4000,
                    messages=[{"role": "user", "content": en_prompt}],
                )
                en_narrative = en_response.content[0].text
                logger.info(f"English narrative: {len(en_narrative)} chars")
            except Exception as e:
                logger.warning(f"English narrative generation failed (non-fatal): {e}")

            # Store English version as attribute for daily_job to pick up
            self._last_en_narrative = en_narrative

            return narrative
        except Exception as exc:
            logger.error(f"GFCRI narrative generation failed: {exc}")
            return (
                f"*GFCRI 分析报告生成失败: {exc}*\n\n"
                f"当前 GFCRI: {gfcri_result['gfcri']:.1f}/100\n"
                f"异常节点: {anomalous_str}"
            )
