"""
Economy Health Score (EHS) - Indicator configuration.

Defines 9 economies, their indicators, data sources, and scoring weights.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Indicator:
    code: str
    name_zh: str
    dimension: str
    source: Literal["fred", "yfinance"]
    series_id: str
    direction: int  # 1=positive, -1=negative
    weight: float
    frequency: str = "monthly"
    transform: str = "yoy"  # yoy, level, diff, mom


@dataclass
class Economy:
    code: str
    name_zh: str
    name_en: str
    region: str
    target_inflation: float = 2.0
    indicators: list[Indicator] = field(default_factory=list)


ECONOMIES: dict[str, Economy] = {
    "US": Economy(
        code="US", name_zh="美国", name_en="United States", region="北美",
        target_inflation=2.0,
        indicators=[
            Indicator("us_indpro", "工业生产指数", "growth", "fred", "INDPRO", 1, 0.35, transform="yoy"),
            Indicator("us_retail", "零售销售", "growth", "fred", "RSAFS", 1, 0.35, transform="yoy"),
            Indicator("us_umcsent", "消费者信心", "growth", "fred", "UMCSENT", 1, 0.30, transform="level"),
            Indicator("us_unemp", "失业率", "labor", "fred", "UNRATE", -1, 0.5, transform="level"),
            Indicator("us_payroll", "非农就业", "labor", "fred", "PAYEMS", 1, 0.5, transform="diff"),
            Indicator("us_cpi", "CPI同比", "price", "fred", "CPIAUCSL", 0, 0.5, transform="yoy"),
            Indicator("us_pce", "核心PCE", "price", "fred", "PCEPILFE", 0, 0.5, transform="yoy"),
            Indicator("us_trade", "贸易余额", "external", "fred", "BOPGSTB", 1, 1.0, transform="level"),
            Indicator("us_spread", "10Y-2Y利差", "financial", "fred", "T10Y2Y", 1, 0.4, transform="level"),
            Indicator("us_bbb", "BBB信用利差", "financial", "fred", "BAMLC0A4CBBB", -1, 0.3, transform="level"),
            Indicator("us_mortgage", "30年房贷利率", "financial", "fred", "MORTGAGE30US", -1, 0.3, transform="level"),
        ],
    ),
    "CN": Economy(
        code="CN", name_zh="中国", name_en="China", region="亚太",
        target_inflation=3.0,
        indicators=[
            Indicator("cn_cpi", "CPI同比", "price", "fred", "CHNCPIALLMINMEI", 0, 1.0, transform="yoy"),
            Indicator("cn_equity", "沪深300 ETF", "growth", "yfinance", "FXI", 1, 0.5, transform="mom"),
            Indicator("cn_pmi", "财新PMI代理", "growth", "yfinance", "KWEB", 1, 0.5, transform="mom"),
            Indicator("cn_fx", "人民币汇率", "external", "yfinance", "CNY=X", -1, 1.0, transform="mom"),
            Indicator("cn_bond", "中国国债ETF", "financial", "yfinance", "CBON", 1, 1.0, transform="mom"),
        ],
    ),
    "EU": Economy(
        code="EU", name_zh="欧元区", name_en="Eurozone", region="欧洲",
        target_inflation=2.0,
        indicators=[
            Indicator("eu_cpi", "CPI同比", "price", "fred", "EA19CPIALLMINMEI", 0, 1.0, transform="yoy"),
            Indicator("eu_unemp", "失业率", "labor", "fred", "LRHUTTTTEZM156S", -1, 1.0, transform="level"),
            Indicator("eu_equity", "欧洲股票ETF", "growth", "yfinance", "EZU", 1, 0.5, transform="mom"),
            Indicator("eu_pmi", "欧洲工业代理", "growth", "yfinance", "EWG", 1, 0.5, transform="mom"),
            Indicator("eu_fx", "欧元汇率", "external", "yfinance", "EURUSD=X", 1, 1.0, transform="mom"),
            Indicator("eu_spread", "意德利差代理", "financial", "yfinance", "IGOV", -1, 1.0, transform="mom"),
        ],
    ),
    "JP": Economy(
        code="JP", name_zh="日本", name_en="Japan", region="亚太",
        target_inflation=2.0,
        indicators=[
            Indicator("jp_cpi", "CPI同比", "price", "fred", "JPNCPIALLMINMEI", 0, 1.0, transform="yoy"),
            Indicator("jp_unemp", "失业率", "labor", "fred", "LRHUTTTTJPM156S", -1, 1.0, transform="level"),
            Indicator("jp_equity", "日经ETF", "growth", "yfinance", "EWJ", 1, 1.0, transform="mom"),
            Indicator("jp_fx", "日元汇率", "external", "yfinance", "JPY=X", -1, 1.0, transform="mom"),
            Indicator("jp_bond", "日本国债代理", "financial", "yfinance", "BNDX", 1, 1.0, transform="mom"),
        ],
    ),
    "GB": Economy(
        code="GB", name_zh="英国", name_en="United Kingdom", region="欧洲",
        target_inflation=2.0,
        indicators=[
            Indicator("gb_cpi", "CPI同比", "price", "fred", "GBRCPIALLMINMEI", 0, 1.0, transform="yoy"),
            Indicator("gb_unemp", "失业率", "labor", "fred", "LRHUTTTTGBM156S", -1, 1.0, transform="level"),
            Indicator("gb_equity", "英国ETF", "growth", "yfinance", "EWU", 1, 1.0, transform="mom"),
            Indicator("gb_fx", "英镑汇率", "external", "yfinance", "GBPUSD=X", 1, 1.0, transform="mom"),
            Indicator("gb_bond", "英国国债代理", "financial", "yfinance", "IGLT.L", 1, 1.0, transform="mom"),
        ],
    ),
    "DE": Economy(
        code="DE", name_zh="德国", name_en="Germany", region="欧洲",
        target_inflation=2.0,
        indicators=[
            Indicator("de_cpi", "CPI同比", "price", "fred", "DEUCPIALLMINMEI", 0, 1.0, transform="yoy"),
            Indicator("de_unemp", "失业率", "labor", "fred", "LRHUTTTTDEM156S", -1, 1.0, transform="level"),
            Indicator("de_equity", "DAX ETF", "growth", "yfinance", "EWG", 1, 1.0, transform="mom"),
            Indicator("de_ifo", "德国工业代理", "growth", "yfinance", "HEWG", 1, 0.5, transform="mom"),
            Indicator("de_trade", "出口代理", "external", "yfinance", "DAX", 1, 1.0, transform="mom"),
        ],
    ),
    "IN": Economy(
        code="IN", name_zh="印度", name_en="India", region="亚太",
        target_inflation=4.0,
        indicators=[
            Indicator("in_cpi", "CPI同比", "price", "fred", "INDCPIALLMINMEI", 0, 1.0, transform="yoy"),
            Indicator("in_equity", "印度ETF", "growth", "yfinance", "INDA", 1, 1.0, transform="mom"),
            Indicator("in_fx", "卢比汇率", "external", "yfinance", "INR=X", -1, 1.0, transform="mom"),
            Indicator("in_bond", "新兴债ETF", "financial", "yfinance", "EMB", 1, 1.0, transform="mom"),
        ],
    ),
    "BR": Economy(
        code="BR", name_zh="巴西", name_en="Brazil", region="南美",
        target_inflation=3.0,
        indicators=[
            Indicator("br_cpi", "CPI同比", "price", "fred", "BRACPIALLMINMEI", 0, 1.0, transform="yoy"),
            Indicator("br_equity", "巴西ETF", "growth", "yfinance", "EWZ", 1, 1.0, transform="mom"),
            Indicator("br_fx", "雷亚尔汇率", "external", "yfinance", "BRL=X", -1, 1.0, transform="mom"),
            Indicator("br_commodity", "大宗商品", "growth", "yfinance", "DBC", 1, 0.5, transform="mom"),
        ],
    ),
    "KR": Economy(
        code="KR", name_zh="韩国", name_en="South Korea", region="亚太",
        target_inflation=2.0,
        indicators=[
            Indicator("kr_cpi", "CPI同比", "price", "fred", "KORCPIALLMINMEI", 0, 1.0, transform="yoy"),
            Indicator("kr_equity", "韩国ETF", "growth", "yfinance", "EWY", 1, 0.5, transform="mom"),
            Indicator("kr_kospi", "KOSPI", "growth", "yfinance", "^KS11", 1, 0.5, transform="mom"),
            Indicator("kr_fx", "韩元汇率", "external", "yfinance", "KRW=X", -1, 1.0, transform="mom"),
            Indicator("kr_semi", "半导体代理", "financial", "yfinance", "SOXX", 1, 1.0, transform="mom"),
        ],
    ),
    "AU": Economy(
        code="AU", name_zh="澳大利亚", name_en="Australia", region="亚太",
        target_inflation=2.5,
        indicators=[
            Indicator("au_equity", "澳大利亚ETF", "growth", "yfinance", "EWA", 1, 1.0, transform="mom"),
            Indicator("au_fx", "澳元汇率", "external", "yfinance", "AUDUSD=X", 1, 1.0, transform="mom"),
            Indicator("au_iron", "铁矿石代理", "growth", "yfinance", "PICK", 1, 0.5, transform="mom"),
            Indicator("au_bond", "债券代理", "financial", "yfinance", "GOVT", 1, 1.0, transform="mom"),
        ],
    ),
    "CA": Economy(
        code="CA", name_zh="加拿大", name_en="Canada", region="北美",
        target_inflation=2.0,
        indicators=[
            Indicator("ca_equity", "加拿大ETF", "growth", "yfinance", "EWC", 1, 1.0, transform="mom"),
            Indicator("ca_fx", "加元汇率", "external", "yfinance", "CADUSD=X", 1, 1.0, transform="mom"),
            Indicator("ca_oil", "能源代理", "growth", "yfinance", "XEG.TO", 1, 0.5, transform="mom"),
            Indicator("ca_bond", "债券代理", "financial", "yfinance", "XBB.TO", 1, 1.0, transform="mom"),
        ],
    ),
    "MX": Economy(
        code="MX", name_zh="墨西哥", name_en="Mexico", region="北美",
        target_inflation=3.0,
        indicators=[
            Indicator("mx_equity", "墨西哥ETF", "growth", "yfinance", "EWW", 1, 1.0, transform="mom"),
            Indicator("mx_fx", "比索汇率", "external", "yfinance", "MXN=X", -1, 1.0, transform="mom"),
            Indicator("mx_bond", "新兴债代理", "financial", "yfinance", "EMB", 1, 1.0, transform="mom"),
        ],
    ),
    "RU": Economy(
        code="RU", name_zh="俄罗斯", name_en="Russia", region="欧洲",
        target_inflation=4.0,
        indicators=[
            Indicator("ru_equity", "俄罗斯ETF", "growth", "yfinance", "ERUS", 1, 1.0, transform="mom"),
            Indicator("ru_fx", "卢布汇率", "external", "yfinance", "RUB=X", -1, 1.0, transform="mom"),
            Indicator("ru_oil", "油价", "growth", "yfinance", "CL=F", 1, 0.5, transform="mom"),
        ],
    ),
    "SA": Economy(
        code="SA", name_zh="沙特阿拉伯", name_en="Saudi Arabia", region="中东",
        target_inflation=2.0,
        indicators=[
            Indicator("sa_equity", "沙特ETF", "growth", "yfinance", "KSA", 1, 1.0, transform="mom"),
            Indicator("sa_oil", "油价", "external", "yfinance", "CL=F", 1, 1.0, transform="mom"),
        ],
    ),
    "TR": Economy(
        code="TR", name_zh="土耳其", name_en="Turkey", region="中东",
        target_inflation=5.0,
        indicators=[
            Indicator("tr_equity", "土耳其ETF", "growth", "yfinance", "TUR", 1, 1.0, transform="mom"),
            Indicator("tr_fx", "里拉汇率", "external", "yfinance", "TRY=X", -1, 1.0, transform="mom"),
        ],
    ),
    "ID": Economy(
        code="ID", name_zh="印度尼西亚", name_en="Indonesia", region="亚太",
        target_inflation=3.0,
        indicators=[
            Indicator("id_equity", "印尼ETF", "growth", "yfinance", "EIDO", 1, 1.0, transform="mom"),
            Indicator("id_fx", "印尼盾汇率", "external", "yfinance", "IDR=X", -1, 1.0, transform="mom"),
            Indicator("id_commodity", "商品代理", "growth", "yfinance", "DBC", 1, 0.5, transform="mom"),
        ],
    ),
    "TW": Economy(
        code="TW", name_zh="中国台湾", name_en="Taiwan", region="亚太",
        target_inflation=2.0,
        indicators=[
            Indicator("tw_equity", "台湾ETF", "growth", "yfinance", "EWT", 1, 1.0, transform="mom"),
            Indicator("tw_fx", "台币汇率", "external", "yfinance", "TWD=X", -1, 1.0, transform="mom"),
            Indicator("tw_semi", "半导体", "financial", "yfinance", "SOXX", 1, 1.0, transform="mom"),
        ],
    ),
    "SG": Economy(
        code="SG", name_zh="新加坡", name_en="Singapore", region="亚太",
        target_inflation=2.0,
        indicators=[
            Indicator("sg_equity", "新加坡ETF", "growth", "yfinance", "EWS", 1, 1.0, transform="mom"),
            Indicator("sg_fx", "新元汇率", "external", "yfinance", "SGD=X", -1, 1.0, transform="mom"),
        ],
    ),
    "ZA": Economy(
        code="ZA", name_zh="南非", name_en="South Africa", region="非洲",
        target_inflation=4.5,
        indicators=[
            Indicator("za_equity", "南非ETF", "growth", "yfinance", "EZA", 1, 1.0, transform="mom"),
            Indicator("za_fx", "兰特汇率", "external", "yfinance", "ZAR=X", -1, 1.0, transform="mom"),
            Indicator("za_gold", "黄金", "growth", "yfinance", "GLD", 1, 0.5, transform="mom"),
        ],
    ),
    "FR": Economy(
        code="FR", name_zh="法国", name_en="France", region="欧洲",
        target_inflation=2.0,
        indicators=[
            Indicator("fr_equity", "法国ETF", "growth", "yfinance", "EWQ", 1, 1.0, transform="mom"),
            Indicator("fr_fx", "欧元汇率", "external", "yfinance", "EURUSD=X", 1, 1.0, transform="mom"),
            Indicator("fr_bond", "法国国债代理", "financial", "yfinance", "IGOV", 1, 1.0, transform="mom"),
        ],
    ),
    "IT": Economy(
        code="IT", name_zh="意大利", name_en="Italy", region="欧洲",
        target_inflation=2.0,
        indicators=[
            Indicator("it_equity", "意大利ETF", "growth", "yfinance", "EWI", 1, 1.0, transform="mom"),
            Indicator("it_fx", "欧元汇率", "external", "yfinance", "EURUSD=X", 1, 1.0, transform="mom"),
        ],
    ),
}

DIMENSION_WEIGHTS = {
    "growth": 0.30,
    "labor": 0.25,
    "price": 0.20,
    "external": 0.15,
    "financial": 0.10,
}
