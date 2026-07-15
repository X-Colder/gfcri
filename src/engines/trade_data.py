"""Standalone global trade data registry and risk-atlas service.

The trade domain is deliberately kept outside the core GFCRI scoring path for
now. This module exposes source metadata, connector health, and a transparent
trade-corridor atlas that can be calibrated with official trade series over
time.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

import requests

from src.storage.database import (
    get_trade_source_health,
    save_trade_source_health,
)


TRADE_DATA_VERSION = "0.1.2-source-registry"


@dataclass(frozen=True)
class TradeDataSource:
    source_id: str
    name: str
    provider: str
    tier: str
    status: str
    source_type: str
    access_mode: str
    update_frequency: str
    url: str
    healthcheck_url: str
    domains: tuple[str, ...]
    used_by: tuple[str, ...]
    affects_core_gfcri: bool
    limitations: str
    next_step: str


TRADE_DATA_SOURCES: tuple[TradeDataSource, ...] = (
    TradeDataSource(
        source_id="us_census_trade_api",
        name="US Census International Trade API",
        provider="US Census Bureau",
        tier="A",
        status="active_probe",
        source_type="official_api",
        access_mode="public_api",
        update_frequency="monthly",
        url="https://www.census.gov/data/developers/data-sets/international-trade.html",
        healthcheck_url="https://api.census.gov/data/timeseries/intltrade/exports/hs/variables.json",
        domains=("US exports", "US imports", "country partner", "HS goods"),
        used_by=("Trade Risk Atlas", "Trade corridor evidence"),
        affects_core_gfcri=False,
        limitations="Connector currently probes metadata and is ready for corridor calibration; it is not yet feeding core GFCRI.",
        next_step="Map HS/country series to US-China, US-Mexico, US-EU and US-ASEAN corridors.",
    ),
    TradeDataSource(
        source_id="eurostat_comext",
        name="Eurostat international trade in goods",
        provider="Eurostat",
        tier="A",
        status="active_probe",
        source_type="official_database",
        access_mode="public_api",
        update_frequency="monthly",
        url="https://ec.europa.eu/eurostat/web/international-trade-in-goods/database",
        healthcheck_url="https://ec.europa.eu/eurostat/web/international-trade-in-goods/database",
        domains=("EU exports", "EU imports", "partner country", "goods categories"),
        used_by=("Trade Risk Atlas", "EU corridor evidence"),
        affects_core_gfcri=False,
        limitations="Registered as an official source; detailed Comext series mapping is staged for the next connector pass.",
        next_step="Attach EU-China, EU-US and EU-energy corridor monthly values.",
    ),
    TradeDataSource(
        source_id="un_comtrade",
        name="UN Comtrade API",
        provider="United Nations",
        tier="A",
        status="registered",
        source_type="official_api",
        access_mode="public_or_keyed_api",
        update_frequency="monthly_or_annual",
        url="https://comtradeapi.un.org/",
        healthcheck_url="https://comtradeapi.un.org/",
        domains=("global bilateral trade", "commodity categories", "reporter partner flows"),
        used_by=("Global trade network calibration", "Trade dependency model"),
        affects_core_gfcri=False,
        limitations="API quota/key policy must be finalized before automated production pulls.",
        next_step="Add API key/config support and cache normalized reporter-partner monthly records.",
    ),
    TradeDataSource(
        source_id="wto_stats_api",
        name="WTO Stats API",
        provider="World Trade Organization",
        tier="A",
        status="registered",
        source_type="official_api",
        access_mode="api_portal",
        update_frequency="monthly_quarterly_annual",
        url="https://apiportal.wto.org/",
        healthcheck_url="https://apiportal.wto.org/",
        domains=("world trade indicators", "merchandise trade", "services trade"),
        used_by=("Global trade regime context", "Trade source registry"),
        affects_core_gfcri=False,
        limitations="API portal access and selected indicators need explicit configuration.",
        next_step="Register selected WTO timeseries indicators and add freshness checks.",
    ),
    TradeDataSource(
        source_id="china_customs_manual",
        name="China Customs trade releases",
        provider="General Administration of Customs of China",
        tier="A",
        status="manual_release",
        source_type="official_release",
        access_mode="manual_or_scraped_release",
        update_frequency="monthly",
        url="https://www.customs.gov.cn/",
        healthcheck_url="https://www.customs.gov.cn/",
        domains=("China exports", "China imports", "partner regions", "product groups"),
        used_by=("China corridor narrative", "Trade Risk Atlas"),
        affects_core_gfcri=False,
        limitations="Official release metadata is registered, but automated structured ingestion is not yet implemented.",
        next_step="Add normalized monthly release parser or manually reviewed import workflow.",
    ),
)


TRADE_NODES: list[dict[str, Any]] = [
    {
        "id": "us",
        "name": "美国",
        "short": "美国",
        "role": "终端需求 / 关税规则制定者",
        "x": 160,
        "y": 220,
        "risk": 86,
        "importance": 98,
        "tags": ["tariff", "demand", "tech"],
        "summary": "美国仍是全球制造品和高端设备的关键终端需求端，也是关税、原产地审查和技术管制的主要变量来源。",
        "exposure": "进口依赖分散到墨西哥、加拿大、中国、越南、台湾和韩国，但消费周期与政策冲击会同步影响全球出口链。",
        "watch": "美国关税公告、零售销售、库存周期、科技管制清单和原产地审查。",
        "source_ids": ["us_census_trade_api"],
    },
    {
        "id": "mexico",
        "name": "墨西哥",
        "short": "墨西哥",
        "role": "近岸制造 / 美国入口",
        "x": 135,
        "y": 320,
        "risk": 68,
        "importance": 74,
        "tags": ["tariff", "demand"],
        "summary": "墨西哥是美国近岸制造的主要承接地，受益于供应链重构，也暴露于美国对转口和原产地规则的追溯。",
        "exposure": "汽车、机械、电子组装和跨境供应链对美国终端需求高度敏感。",
        "watch": "USMCA 原产地规则、汽车零部件审查和对美出口异常增速。",
        "source_ids": ["us_census_trade_api", "un_comtrade"],
    },
    {
        "id": "latam",
        "name": "巴西 / 拉美",
        "short": "拉美",
        "role": "农产品 / 金属资源",
        "x": 260,
        "y": 430,
        "risk": 54,
        "importance": 64,
        "tags": ["commodity", "fx"],
        "summary": "拉美向中国、欧盟和美国提供农产品、矿产和能源，是资源价格与美元融资压力的交汇点。",
        "exposure": "大豆、铁矿、铜、原油和食品贸易受中国工业周期、美元和气候扰动影响。",
        "watch": "中国进口量、美元指数、铜价、粮价和本币汇率。",
        "source_ids": ["un_comtrade", "wto_stats_api"],
    },
    {
        "id": "eu",
        "name": "欧盟 / 德国",
        "short": "欧盟",
        "role": "高端工业 / 夹层市场",
        "x": 470,
        "y": 175,
        "risk": 74,
        "importance": 88,
        "tags": ["tariff", "energy", "demand"],
        "summary": "欧盟出口端依赖美国高附加值需求，进口端依赖中国制造，处在中美贸易重构和能源成本之间。",
        "exposure": "汽车、机械、化工和奢侈品出口受美国需求影响；电气机械和消费品进口受中国供应链影响。",
        "watch": "欧盟反补贴调查、对美出口订单、天然气价格和德国工业订单。",
        "source_ids": ["eurostat_comext", "us_census_trade_api"],
    },
    {
        "id": "middle_east",
        "name": "中东",
        "short": "中东",
        "role": "能源 / 航运咽喉",
        "x": 560,
        "y": 315,
        "risk": 78,
        "importance": 82,
        "tags": ["energy", "shipping"],
        "summary": "中东是油气供给和关键航运通道的风险源，冲击会通过能源价格、保险和运费传导到制造链。",
        "exposure": "原油、LNG、化工原料和霍尔木兹/红海航运风险影响欧洲与亚洲进口成本。",
        "watch": "油价、LNG、海运保险费、红海绕航比例和霍尔木兹风险事件。",
        "source_ids": ["un_comtrade", "wto_stats_api"],
    },
    {
        "id": "africa",
        "name": "非洲",
        "short": "非洲",
        "role": "矿产 / 新兴需求",
        "x": 505,
        "y": 410,
        "risk": 58,
        "importance": 56,
        "tags": ["commodity", "fx"],
        "summary": "非洲同时是关键矿产供应地和新兴市场需求端，受美元融资、食品能源价格和中国投资周期影响。",
        "exposure": "铜、钴、铁矿、能源和基建进口形成双向风险。",
        "watch": "关键矿产出口、主权利差、食品能源进口成本和美元融资条件。",
        "source_ids": ["un_comtrade", "wto_stats_api"],
    },
    {
        "id": "india",
        "name": "印度",
        "short": "印度",
        "role": "替代制造 / 内需市场",
        "x": 620,
        "y": 395,
        "risk": 61,
        "importance": 66,
        "tags": ["tariff", "energy", "demand"],
        "summary": "印度受益于部分供应链转移，但能源进口依赖、政策保护和基础设施约束限制承接速度。",
        "exposure": "电子组装、药品、纺织和能源进口对政策与油价敏感。",
        "watch": "电子出口、原油进口成本、卢比汇率和对美贸易政策。",
        "source_ids": ["un_comtrade", "wto_stats_api"],
    },
    {
        "id": "china",
        "name": "中国",
        "short": "中国",
        "role": "制造核心 / 出口升级",
        "x": 690,
        "y": 265,
        "risk": 82,
        "importance": 96,
        "tags": ["tariff", "tech", "ai", "commodity"],
        "summary": "中国仍是全球制造核心，机电、高技术、AI硬件和绿色产品出口增强，同时面临欧美关税和反补贴压力。",
        "exposure": "对欧美终端需求、东亚零部件、资源进口和 ASEAN/墨西哥重路由链条都有系统性影响。",
        "watch": "7-8月出口回落幅度、机电/高技术出口、欧美关税动作和 AI 硬件订单。",
        "source_ids": ["china_customs_manual", "un_comtrade", "eurostat_comext", "us_census_trade_api"],
    },
    {
        "id": "east_asia",
        "name": "台湾 / 韩国 / 日本",
        "short": "东亚",
        "role": "半导体 / 设备链",
        "x": 795,
        "y": 235,
        "risk": 80,
        "importance": 90,
        "tags": ["ai", "tech", "fx"],
        "summary": "东亚半导体和设备链是 AI 硬件周期的核心节点，也暴露于技术管制、库存周期和汇率波动。",
        "exposure": "芯片、存储、半导体设备、汽车零部件和精密机械与全球资本开支周期高度同步。",
        "watch": "台湾与韩国半导体出口、存储价格、日本设备订单和韩元/日元汇率。",
        "source_ids": ["un_comtrade", "wto_stats_api", "us_census_trade_api"],
    },
    {
        "id": "asean",
        "name": "ASEAN",
        "short": "ASEAN",
        "role": "转口 / 组装承接",
        "x": 720,
        "y": 385,
        "risk": 72,
        "importance": 76,
        "tags": ["tariff", "shipping", "tech"],
        "summary": "ASEAN 是供应链转移和转口的重要承接地，但出口异常高增容易被美国和欧盟纳入原产地审查。",
        "exposure": "电子、家具、纺织、机械组装和中国零部件输入形成高弹性的贸易绕行路径。",
        "watch": "越南/泰国/马来西亚对美出口增速、中国零部件进口和原产地审查新闻。",
        "source_ids": ["un_comtrade", "us_census_trade_api"],
    },
    {
        "id": "australia",
        "name": "澳洲",
        "short": "澳洲",
        "role": "矿石 / 能源",
        "x": 830,
        "y": 470,
        "risk": 52,
        "importance": 62,
        "tags": ["commodity", "energy"],
        "summary": "澳洲是铁矿、煤炭、LNG 和农业品供应地，风险主要通过中国工业周期和能源价格传导。",
        "exposure": "资源出口对中国地产/工业周期、全球钢铁需求和 LNG 价格敏感。",
        "watch": "铁矿石价格、中国钢材需求、LNG 价格和澳元。",
        "source_ids": ["un_comtrade", "china_customs_manual"],
    },
]


TRADE_CORRIDORS: list[dict[str, Any]] = [
    {
        "id": "china-us",
        "from": "china",
        "to": "us",
        "label": "中国 → 美国",
        "goods": "电子、机械、消费品、汽车零部件",
        "risk": 88,
        "volume": 95,
        "tags": ["tariff", "demand", "tech"],
        "trigger": "关税与原产地审查",
        "summary": "最核心的贸易摩擦走廊。直接出口受关税影响，间接路径则推高 ASEAN/墨西哥转口审查风险。",
        "exposure": "美国消费和科技管制决定需求弹性，中国制造链决定全球供给弹性。",
        "watch": "美国关税窗口、提前出货后回落、对越南/墨西哥转口审查。",
        "source_ids": ["us_census_trade_api", "china_customs_manual", "un_comtrade"],
    },
    {
        "id": "china-eu",
        "from": "china",
        "to": "eu",
        "label": "中国 → 欧盟",
        "goods": "电气机械、汽车、光伏、消费品",
        "risk": 79,
        "volume": 82,
        "tags": ["tariff", "demand", "tech"],
        "trigger": "反补贴与产业保护",
        "summary": "欧盟需要中国供应链，但在汽车、绿色产品和高端制造上面临本土产业压力。",
        "exposure": "欧盟进口成本、反补贴调查和德国工业竞争力形成拉扯。",
        "watch": "欧盟反补贴调查、汽车关税、德国工业订单和港口库存。",
        "source_ids": ["eurostat_comext", "china_customs_manual", "un_comtrade"],
    },
    {
        "id": "eastasia-china",
        "from": "east_asia",
        "to": "china",
        "label": "东亚 → 中国",
        "goods": "半导体、设备、存储、精密零部件",
        "risk": 84,
        "volume": 88,
        "tags": ["ai", "tech", "fx"],
        "trigger": "AI硬件周期集中",
        "summary": "AI资本开支上行时强化贸易，若订单放缓会同步影响中国组装、韩国/台湾出口和日本设备链。",
        "exposure": "半导体出口、设备订单和存储价格是该链条的领先信号。",
        "watch": "HBM/存储价格、台湾出口订单、韩国芯片出口和日本设备出货。",
        "source_ids": ["un_comtrade", "china_customs_manual"],
    },
    {
        "id": "china-asean-us",
        "from": "china",
        "to": "asean",
        "label": "中国 → ASEAN → 美国",
        "goods": "零部件、电子组装、家具、纺织",
        "risk": 76,
        "volume": 72,
        "tags": ["tariff", "shipping", "tech"],
        "trigger": "转口路径审查",
        "summary": "贸易不是消失，而是重路由。该路径越活跃，越容易触发原产地规则和反规避调查。",
        "exposure": "中国零部件输入和 ASEAN 对美出口的剪刀差是风险识别重点。",
        "watch": "ASEAN 对美出口异常高增、从中国进口中间品增速、美国反规避调查。",
        "reroute": True,
        "source_ids": ["un_comtrade", "us_census_trade_api"],
    },
    {
        "id": "mexico-us",
        "from": "mexico",
        "to": "us",
        "label": "墨西哥 → 美国",
        "goods": "汽车、机械、电子、工业品",
        "risk": 71,
        "volume": 86,
        "tags": ["tariff", "demand"],
        "trigger": "近岸制造拥挤",
        "summary": "墨西哥受益于近岸制造，但也成为美国规则追溯和供应链拥挤的焦点。",
        "exposure": "汽车与工业链条对美国库存周期和 USMCA 规则敏感。",
        "watch": "汽车零部件原产地、边境物流、美国制造订单。",
        "source_ids": ["us_census_trade_api", "un_comtrade"],
    },
    {
        "id": "eu-us",
        "from": "eu",
        "to": "us",
        "label": "欧盟 → 美国",
        "goods": "汽车、机械、药品、化工",
        "risk": 73,
        "volume": 80,
        "tags": ["tariff", "demand"],
        "trigger": "美国需求与关税政策",
        "summary": "欧盟出口端高度依赖美国高附加值需求，若美国关税升级，欧洲制造利润率会被压缩。",
        "exposure": "德国汽车、机械和药品出口是主要敏感点。",
        "watch": "美国进口关税、欧元汇率、德国出口订单。",
        "source_ids": ["eurostat_comext", "us_census_trade_api"],
    },
    {
        "id": "middleeast-eu",
        "from": "middle_east",
        "to": "eu",
        "label": "中东 → 欧盟",
        "goods": "原油、LNG、化工原料",
        "risk": 77,
        "volume": 66,
        "tags": ["energy", "shipping"],
        "trigger": "能源与航运成本",
        "summary": "能源和航运冲击会直接抬升欧洲制造成本，并影响通胀回落路径。",
        "exposure": "油气价格、保险费和绕航成本共同决定输入型通胀。",
        "watch": "布油、TTF天然气、红海绕航比例、海运保险费。",
        "source_ids": ["eurostat_comext", "un_comtrade"],
    },
    {
        "id": "australia-china",
        "from": "australia",
        "to": "china",
        "label": "澳洲 → 中国",
        "goods": "铁矿、LNG、煤炭、农产品",
        "risk": 57,
        "volume": 70,
        "tags": ["commodity", "energy"],
        "trigger": "中国工业周期",
        "summary": "该走廊更多反映中国工业需求和资源价格，而不是贸易摩擦本身。",
        "exposure": "铁矿石与 LNG 对中国工业、地产和能源需求变化敏感。",
        "watch": "铁矿、钢材开工、LNG价格、中国进口量。",
        "source_ids": ["china_customs_manual", "un_comtrade"],
    },
    {
        "id": "latam-china",
        "from": "latam",
        "to": "china",
        "label": "拉美 → 中国",
        "goods": "大豆、铁矿、铜、原油",
        "risk": 62,
        "volume": 64,
        "tags": ["commodity", "fx"],
        "trigger": "资源价格与美元",
        "summary": "资源贸易强度受中国需求、美元和气候扰动影响，新兴市场货币会放大冲击。",
        "exposure": "铜、粮食和能源价格会向新兴市场外部压力传导。",
        "watch": "铜价、粮价、美元指数、巴西雷亚尔和中国进口量。",
        "source_ids": ["china_customs_manual", "un_comtrade"],
    },
]


RISK_FILTERS = [
    {"id": "all", "label": "全部", "color": "#58a6ff"},
    {"id": "tariff", "label": "关税", "color": "#ef4444"},
    {"id": "shipping", "label": "航运", "color": "#f97316"},
    {"id": "energy", "label": "能源", "color": "#f59e0b"},
    {"id": "fx", "label": "汇率", "color": "#22c55e"},
    {"id": "demand", "label": "需求", "color": "#38bdf8"},
    {"id": "tech", "label": "技术管制", "color": "#a78bfa"},
    {"id": "ai", "label": "AI硬件", "color": "#14b8a6"},
    {"id": "commodity", "label": "大宗商品", "color": "#eab308"},
]


SHOCK_SCENARIOS = [
    {
        "id": "us-tariff",
        "label": "美国关税冲击",
        "title": "美国关税上调与原产地追溯",
        "risk": 88,
        "summary": "冲击先压缩中国直达美国的出口利润，再推高 ASEAN/墨西哥转口，最终触发更广泛的反规避审查。",
        "steps": ["中国直达美国订单提前出货后回落", "ASEAN/墨西哥承接转口和组装需求", "原产地审查覆盖中间品来源", "全球制造利润率与库存周转承压"],
    },
    {
        "id": "ai-slowdown",
        "label": "AI硬件降温",
        "title": "AI资本开支放缓",
        "risk": 84,
        "summary": "若云厂商资本开支降温，东亚半导体、中国组装和美国科技设备需求会同步收缩。",
        "steps": ["芯片和存储订单增速下滑", "东亚出口与设备订单走弱", "中国高技术出口降温", "铜、能源和航运需求同步回落"],
    },
    {
        "id": "shipping-energy",
        "label": "能源航运扰动",
        "title": "中东航运与能源成本上行",
        "risk": 78,
        "summary": "能源和海运冲击会以成本形式穿透到欧洲、亚洲制造链，并重新推高通胀预期。",
        "steps": ["红海/霍尔木兹风险抬升保险费", "油气与化工原料价格上行", "欧洲和亚洲进口成本上升", "终端需求和利润率同时受压"],
    },
]


EVIDENCE_BLOCKS = [
    {
        "kicker": "Source Tier",
        "title": "数据源已经纳入统一注册表",
        "body": "v0.1.2 接入官方贸易源注册和健康探测，贸易风险图谱仍作为独立分析域运行，暂不影响 GFCRI 核心评分。",
    },
    {
        "kicker": "Formula Receipt",
        "title": "风险分数用于排序，不是投资建议",
        "body": "节点和走廊风险分数由系统重要性、近期政策风险、贸易集中度、替代路径脆弱性和对 GFCRI 子指数的传导强度综合给出，当前不作为交易信号。",
    },
    {
        "kicker": "Data Limits",
        "title": "转口和原产地风险需要进一步验证",
        "body": "转口路径使用虚线展示，表示需要以中间品进口、对美出口、行业订单和原产地审查新闻进行交叉验证。",
    },
    {
        "kicker": "Disclaimer",
        "title": "风险监测用途",
        "body": "该模块用于宏观贸易风险监测和机构研究沟通，不构成投资建议、贸易建议、法律建议或任何证券买卖建议。",
    },
]


def trade_sources() -> list[dict[str, Any]]:
    return [asdict(source) for source in TRADE_DATA_SOURCES]


def refresh_trade_source_health() -> list[dict[str, Any]]:
    """Probe registered trade sources without requiring full series downloads."""
    results: list[dict[str, Any]] = []
    for source in TRADE_DATA_SOURCES:
        started = datetime.now(timezone.utc)
        status = "registered"
        error = None
        record_count = 0
        try:
            if source.status in {"active_probe", "manual_release"}:
                resp = requests.get(
                    source.healthcheck_url,
                    timeout=8,
                    headers={"User-Agent": "GFCRI/0.1.2 trade-source-probe"},
                )
                resp.raise_for_status()
                status = "ok"
                record_count = 1
            else:
                status = source.status
        except Exception as exc:  # best-effort health probe
            status = "degraded"
            error = str(exc)[:500]

        latency_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        results.append({
            "source_id": source.source_id,
            "source_name": source.name,
            "source_tier": source.tier,
            "status": status,
            "last_checked_at": datetime.now(timezone.utc).isoformat(),
            "last_success_at": datetime.now(timezone.utc).isoformat() if status == "ok" else None,
            "last_error": error,
            "record_count": record_count,
            "latency_ms": latency_ms,
            "latest_period": None,
        })
    try:
        save_trade_source_health(results)
    except Exception as exc:
        for item in results:
            if not item.get("last_error"):
                item["last_error"] = f"Could not persist source health: {exc}"
    return results


def trade_source_health(refresh: bool = False) -> list[dict[str, Any]]:
    if refresh:
        return refresh_trade_source_health()
    try:
        persisted = get_trade_source_health()
    except Exception:
        persisted = []
    if persisted:
        return persisted
    return [
        {
            "source_id": source.source_id,
            "source_name": source.name,
            "source_tier": source.tier,
            "status": source.status,
            "last_checked_at": None,
            "last_success_at": None,
            "last_error": None,
            "record_count": 0,
            "latency_ms": 0,
            "latest_period": None,
        }
        for source in TRADE_DATA_SOURCES
    ]


def trade_risk_atlas(refresh_sources: bool = False) -> dict[str, Any]:
    health = trade_source_health(refresh=refresh_sources)
    ok_sources = sum(1 for item in health if item.get("status") == "ok")
    degraded_sources = sum(1 for item in health if item.get("status") == "degraded")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_version": TRADE_DATA_VERSION,
        "standalone": True,
        "affects_core_gfcri": False,
        "status": "ok" if ok_sources else "source_registry_only",
        "summary": {
            "node_count": len(TRADE_NODES),
            "corridor_count": len(TRADE_CORRIDORS),
            "source_count": len(TRADE_DATA_SOURCES),
            "ok_sources": ok_sources,
            "degraded_sources": degraded_sources,
            "high_risk_corridors": sum(1 for item in TRADE_CORRIDORS if item["risk"] >= 75),
        },
        "sources": trade_sources(),
        "source_health": health,
        "risk_filters": RISK_FILTERS,
        "nodes": TRADE_NODES,
        "corridors": TRADE_CORRIDORS,
        "shock_scenarios": SHOCK_SCENARIOS,
        "evidence_blocks": EVIDENCE_BLOCKS,
        "methodology": "Standalone trade-risk analysis. Official sources are registered and probed where public access allows; corridor risk scores are not included in GFCRI core scoring.",
    }
