"""
Industry Research Module - Configuration.

Covers major global industries with yfinance-trackable ETFs and futures.
Based on GICS classification, adapted for data availability.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class IndustryTicker:
    ticker: str
    name_zh: str
    role: str  # sector_etf, commodity, country_proxy, company


@dataclass
class Industry:
    code: str
    name_zh: str
    name_en: str
    category: str  # 大类
    tickers: list[IndustryTicker] = field(default_factory=list)
    upstream: list[str] = field(default_factory=list)  # 上游行业code
    downstream: list[str] = field(default_factory=list)  # 下游行业code
    key_economies: list[str] = field(default_factory=list)  # 关键经济体


INDUSTRIES: dict[str, Industry] = {
    # ═══════════════════════════════════════════
    # 信息技术 & 人工智能
    # ═══════════════════════════════════════════
    "semiconductor": Industry(
        code="semiconductor", name_zh="半导体", name_en="Semiconductors",
        category="信息技术",
        tickers=[
            IndustryTicker("SOXX", "半导体ETF", "sector_etf"),
            IndustryTicker("SMH", "半导体ETF(VanEck)", "sector_etf"),
            IndustryTicker("TSM", "台积电", "company"),
            IndustryTicker("NVDA", "英伟达", "company"),
            IndustryTicker("ASML", "阿斯麦", "company"),
            IndustryTicker("005930.KS", "三星电子", "company"),
        ],
        upstream=["rare_earth", "specialty_chem"],
        downstream=["ai_computing", "consumer_electronics", "auto"],
        key_economies=["TW", "KR", "US", "JP", "CN"],
    ),
    "ai_computing": Industry(
        code="ai_computing", name_zh="人工智能与云计算", name_en="AI & Cloud Computing",
        category="信息技术",
        tickers=[
            IndustryTicker("BOTZ", "AI与机器人ETF", "sector_etf"),
            IndustryTicker("CLOU", "云计算ETF", "sector_etf"),
            IndustryTicker("MSFT", "微软", "company"),
            IndustryTicker("GOOGL", "谷歌", "company"),
            IndustryTicker("META", "Meta", "company"),
        ],
        upstream=["semiconductor"],
        downstream=["software", "internet"],
        key_economies=["US", "CN"],
    ),
    "software": Industry(
        code="software", name_zh="软件与SaaS", name_en="Software & SaaS",
        category="信息技术",
        tickers=[
            IndustryTicker("IGV", "软件ETF", "sector_etf"),
            IndustryTicker("WCLD", "云软件ETF", "sector_etf"),
        ],
        upstream=["ai_computing"],
        downstream=["internet"],
        key_economies=["US", "IN", "CN"],
    ),
    "internet": Industry(
        code="internet", name_zh="互联网与电商", name_en="Internet & E-commerce",
        category="信息技术",
        tickers=[
            IndustryTicker("KWEB", "中国互联网ETF", "country_proxy"),
            IndustryTicker("ARKW", "互联网创新ETF", "sector_etf"),
            IndustryTicker("AMZN", "亚马逊", "company"),
            IndustryTicker("BABA", "阿里巴巴", "company"),
        ],
        upstream=["software", "ai_computing"],
        downstream=["logistics", "consumer_retail"],
        key_economies=["US", "CN", "IN"],
    ),
    "consumer_electronics": Industry(
        code="consumer_electronics", name_zh="消费电子", name_en="Consumer Electronics",
        category="信息技术",
        tickers=[
            IndustryTicker("AAPL", "苹果", "company"),
            IndustryTicker("XLK", "科技ETF", "sector_etf"),
            IndustryTicker("2317.TW", "鸿海精密", "company"),
        ],
        upstream=["semiconductor", "display"],
        downstream=["consumer_retail"],
        key_economies=["US", "CN", "KR", "TW", "JP"],
    ),

    # ═══════════════════════════════════════════
    # 能源
    # ═══════════════════════════════════════════
    "oil_gas": Industry(
        code="oil_gas", name_zh="石油与天然气", name_en="Oil & Gas",
        category="能源",
        tickers=[
            IndustryTicker("XLE", "能源ETF", "sector_etf"),
            IndustryTicker("CL=F", "WTI原油期货", "commodity"),
            IndustryTicker("BZ=F", "布伦特原油", "commodity"),
            IndustryTicker("NG=F", "天然气期货", "commodity"),
            IndustryTicker("XOM", "埃克森美孚", "company"),
            IndustryTicker("2222.SR", "沙特阿美", "company"),
        ],
        upstream=[],
        downstream=["petrochemical", "transport", "power"],
        key_economies=["SA", "US", "RU", "CA", "BR"],
    ),
    "new_energy": Industry(
        code="new_energy", name_zh="新能源与光伏", name_en="Renewable Energy & Solar",
        category="能源",
        tickers=[
            IndustryTicker("ICLN", "清洁能源ETF", "sector_etf"),
            IndustryTicker("TAN", "太阳能ETF", "sector_etf"),
            IndustryTicker("FAN", "风能ETF", "sector_etf"),
            IndustryTicker("ENPH", "Enphase", "company"),
        ],
        upstream=["silicon", "rare_earth"],
        downstream=["power", "ev_battery"],
        key_economies=["CN", "US", "DE", "IN"],
    ),
    "ev_battery": Industry(
        code="ev_battery", name_zh="电动车与电池", name_en="EV & Battery",
        category="能源",
        tickers=[
            IndustryTicker("LIT", "锂电池ETF", "sector_etf"),
            IndustryTicker("DRIV", "电动车ETF", "sector_etf"),
            IndustryTicker("TSLA", "特斯拉", "company"),
            IndustryTicker("CATL", "宁德时代(代理)", "company"),
        ],
        upstream=["lithium", "nickel_cobalt", "rare_earth"],
        downstream=["auto"],
        key_economies=["CN", "KR", "US", "DE", "JP"],
    ),
    "power": Industry(
        code="power", name_zh="电力与公用事业", name_en="Utilities & Power",
        category="能源",
        tickers=[
            IndustryTicker("XLU", "公用事业ETF", "sector_etf"),
            IndustryTicker("URA", "铀能源ETF", "sector_etf"),
        ],
        upstream=["oil_gas", "new_energy"],
        downstream=["semiconductor", "ai_computing"],
        key_economies=["US", "CN", "FR", "JP"],
    ),

    # ═══════════════════════════════════════════
    # 原材料与矿业
    # ═══════════════════════════════════════════
    "iron_steel": Industry(
        code="iron_steel", name_zh="钢铁与铁矿", name_en="Iron & Steel",
        category="原材料",
        tickers=[
            IndustryTicker("SLX", "钢铁ETF", "sector_etf"),
            IndustryTicker("PICK", "金属矿业ETF", "sector_etf"),
            IndustryTicker("BHP", "必和必拓", "company"),
        ],
        upstream=[],
        downstream=["construction", "auto", "machinery"],
        key_economies=["AU", "BR", "CN", "IN"],
    ),
    "copper_aluminum": Industry(
        code="copper_aluminum", name_zh="铜铝有色金属", name_en="Copper & Aluminum",
        category="原材料",
        tickers=[
            IndustryTicker("COPX", "铜矿ETF", "sector_etf"),
            IndustryTicker("HG=F", "铜期货", "commodity"),
            IndustryTicker("ALI=F", "铝期货", "commodity"),
            IndustryTicker("FCX", "自由港麦克莫兰", "company"),
        ],
        upstream=[],
        downstream=["construction", "consumer_electronics", "ev_battery", "power"],
        key_economies=["CL", "CN", "AU", "ID"],
    ),
    "lithium": Industry(
        code="lithium", name_zh="锂矿", name_en="Lithium",
        category="原材料",
        tickers=[
            IndustryTicker("LIT", "锂电池ETF", "sector_etf"),
            IndustryTicker("ALB", "雅保", "company"),
            IndustryTicker("SQM", "智利化工矿业", "company"),
        ],
        upstream=[],
        downstream=["ev_battery"],
        key_economies=["AU", "CL", "CN", "AR"],
    ),
    "nickel_cobalt": Industry(
        code="nickel_cobalt", name_zh="镍钴", name_en="Nickel & Cobalt",
        category="原材料",
        tickers=[
            IndustryTicker("REMX", "稀有金属ETF", "sector_etf"),
            IndustryTicker("NI=F", "镍期货", "commodity"),
        ],
        upstream=[],
        downstream=["ev_battery", "aerospace"],
        key_economies=["ID", "AU", "RU", "CN"],
    ),
    "rare_earth": Industry(
        code="rare_earth", name_zh="稀土", name_en="Rare Earth",
        category="原材料",
        tickers=[
            IndustryTicker("REMX", "稀有金属ETF", "sector_etf"),
            IndustryTicker("MP", "MP Materials", "company"),
        ],
        upstream=[],
        downstream=["semiconductor", "ev_battery", "new_energy", "defense"],
        key_economies=["CN", "AU", "US"],
    ),
    "gold_silver": Industry(
        code="gold_silver", name_zh="贵金属", name_en="Gold & Silver",
        category="原材料",
        tickers=[
            IndustryTicker("GLD", "黄金ETF", "sector_etf"),
            IndustryTicker("SLV", "白银ETF", "sector_etf"),
            IndustryTicker("GC=F", "黄金期货", "commodity"),
            IndustryTicker("GDX", "金矿ETF", "sector_etf"),
        ],
        upstream=[],
        downstream=[],
        key_economies=["AU", "ZA", "RU", "CA", "CN"],
    ),
    "specialty_chem": Industry(
        code="specialty_chem", name_zh="化工与特种材料", name_en="Specialty Chemicals",
        category="原材料",
        tickers=[
            IndustryTicker("XLB", "材料ETF", "sector_etf"),
            IndustryTicker("LIN", "林德", "company"),
            IndustryTicker("BASFY", "巴斯夫", "company"),
        ],
        upstream=["oil_gas"],
        downstream=["semiconductor", "pharma", "agriculture"],
        key_economies=["DE", "US", "CN", "JP"],
    ),

    # ═══════════════════════════════════════════
    # 工业制造
    # ═══════════════════════════════════════════
    "auto": Industry(
        code="auto", name_zh="汽车制造", name_en="Automotive",
        category="工业",
        tickers=[
            IndustryTicker("CARZ", "全球汽车ETF", "sector_etf"),
            IndustryTicker("TSLA", "特斯拉", "company"),
            IndustryTicker("TM", "丰田", "company"),
            IndustryTicker("VOW3.DE", "大众", "company"),
        ],
        upstream=["iron_steel", "semiconductor", "ev_battery"],
        downstream=["consumer_retail"],
        key_economies=["DE", "JP", "CN", "US", "KR"],
    ),
    "aerospace": Industry(
        code="aerospace", name_zh="航空航天与国防", name_en="Aerospace & Defense",
        category="工业",
        tickers=[
            IndustryTicker("ITA", "航空航天ETF", "sector_etf"),
            IndustryTicker("PPA", "国防ETF", "sector_etf"),
            IndustryTicker("BA", "波音", "company"),
            IndustryTicker("LMT", "洛克希德马丁", "company"),
        ],
        upstream=["rare_earth", "nickel_cobalt", "specialty_chem"],
        downstream=[],
        key_economies=["US", "FR", "GB", "CN", "RU"],
    ),
    "machinery": Industry(
        code="machinery", name_zh="机械与工业设备", name_en="Machinery & Industrial",
        category="工业",
        tickers=[
            IndustryTicker("XLI", "工业ETF", "sector_etf"),
            IndustryTicker("CAT", "卡特彼勒", "company"),
            IndustryTicker("DE", "迪尔", "company"),
        ],
        upstream=["iron_steel", "copper_aluminum"],
        downstream=["construction", "agriculture"],
        key_economies=["US", "DE", "JP", "CN"],
    ),
    "construction": Industry(
        code="construction", name_zh="建筑与基建", name_en="Construction & Infrastructure",
        category="工业",
        tickers=[
            IndustryTicker("ITB", "住宅建筑ETF", "sector_etf"),
            IndustryTicker("PAVE", "基建ETF", "sector_etf"),
        ],
        upstream=["iron_steel", "copper_aluminum", "machinery"],
        downstream=["real_estate"],
        key_economies=["CN", "US", "IN", "SA"],
    ),
    "transport": Industry(
        code="transport", name_zh="交通运输与物流", name_en="Transportation & Logistics",
        category="工业",
        tickers=[
            IndustryTicker("IYT", "运输ETF", "sector_etf"),
            IndustryTicker("BDRY", "波罗的海干散货", "sector_etf"),
            IndustryTicker("^BDI", "BDI指数", "commodity"),
        ],
        upstream=["oil_gas"],
        downstream=["consumer_retail", "agriculture"],
        key_economies=["CN", "US", "SG", "DE"],
    ),
    "logistics": Industry(
        code="logistics", name_zh="快递与供应链", name_en="Logistics & Supply Chain",
        category="工业",
        tickers=[
            IndustryTicker("UPS", "UPS", "company"),
            IndustryTicker("FDX", "联邦快递", "company"),
        ],
        upstream=["transport"],
        downstream=["internet", "consumer_retail"],
        key_economies=["US", "CN", "DE"],
    ),

    # ═══════════════════════════════════════════
    # 金融
    # ═══════════════════════════════════════════
    "banking": Industry(
        code="banking", name_zh="银行", name_en="Banking",
        category="金融",
        tickers=[
            IndustryTicker("XLF", "金融ETF", "sector_etf"),
            IndustryTicker("KBE", "银行ETF", "sector_etf"),
            IndustryTicker("KRE", "区域银行ETF", "sector_etf"),
        ],
        upstream=[],
        downstream=["real_estate", "consumer_retail"],
        key_economies=["US", "CN", "GB", "JP", "EU"],
    ),
    "insurance": Industry(
        code="insurance", name_zh="保险", name_en="Insurance",
        category="金融",
        tickers=[
            IndustryTicker("KIE", "保险ETF", "sector_etf"),
        ],
        upstream=[],
        downstream=[],
        key_economies=["US", "GB", "DE", "JP"],
    ),
    "real_estate": Industry(
        code="real_estate", name_zh="房地产", name_en="Real Estate",
        category="金融",
        tickers=[
            IndustryTicker("VNQ", "房地产REITs ETF", "sector_etf"),
            IndustryTicker("XLRE", "房地产ETF", "sector_etf"),
            IndustryTicker("IYR", "房地产ETF(iShares)", "sector_etf"),
        ],
        upstream=["construction", "banking"],
        downstream=[],
        key_economies=["US", "CN", "GB", "AU"],
    ),

    # ═══════════════════════════════════════════
    # 消费
    # ═══════════════════════════════════════════
    "consumer_retail": Industry(
        code="consumer_retail", name_zh="零售与消费", name_en="Consumer & Retail",
        category="消费",
        tickers=[
            IndustryTicker("XLY", "可选消费ETF", "sector_etf"),
            IndustryTicker("XLP", "必需消费ETF", "sector_etf"),
            IndustryTicker("XRT", "零售ETF", "sector_etf"),
        ],
        upstream=["logistics", "internet"],
        downstream=[],
        key_economies=["US", "CN", "JP", "EU"],
    ),
    "luxury": Industry(
        code="luxury", name_zh="奢侈品", name_en="Luxury Goods",
        category="消费",
        tickers=[
            IndustryTicker("MC.PA", "LVMH", "company"),
            IndustryTicker("RMS.PA", "爱马仕", "company"),
        ],
        upstream=["specialty_chem"],
        downstream=[],
        key_economies=["FR", "IT", "CN"],
    ),
    "food_beverage": Industry(
        code="food_beverage", name_zh="食品饮料", name_en="Food & Beverage",
        category="消费",
        tickers=[
            IndustryTicker("PBJ", "食品饮料ETF", "sector_etf"),
            IndustryTicker("KO", "可口可乐", "company"),
            IndustryTicker("NSRGY", "雀巢", "company"),
        ],
        upstream=["agriculture"],
        downstream=[],
        key_economies=["US", "EU", "CN", "BR"],
    ),

    # ═══════════════════════════════════════════
    # 医疗健康
    # ═══════════════════════════════════════════
    "pharma": Industry(
        code="pharma", name_zh="制药与生物科技", name_en="Pharma & Biotech",
        category="医疗健康",
        tickers=[
            IndustryTicker("XLV", "医疗保健ETF", "sector_etf"),
            IndustryTicker("IBB", "生物科技ETF", "sector_etf"),
            IndustryTicker("XBI", "生物科技ETF(SPDR)", "sector_etf"),
        ],
        upstream=["specialty_chem"],
        downstream=[],
        key_economies=["US", "EU", "CN", "IN", "JP"],
    ),
    "medical_device": Industry(
        code="medical_device", name_zh="医疗器械", name_en="Medical Devices",
        category="医疗健康",
        tickers=[
            IndustryTicker("IHI", "医疗器械ETF", "sector_etf"),
        ],
        upstream=["semiconductor", "specialty_chem"],
        downstream=[],
        key_economies=["US", "DE", "JP", "CN"],
    ),

    # ═══════════════════════════════════════════
    # 农业
    # ═══════════════════════════════════════════
    "agriculture": Industry(
        code="agriculture", name_zh="农业与粮食", name_en="Agriculture & Grain",
        category="农业",
        tickers=[
            IndustryTicker("DBA", "农产品ETF", "sector_etf"),
            IndustryTicker("MOO", "农业商业ETF", "sector_etf"),
            IndustryTicker("ZC=F", "玉米期货", "commodity"),
            IndustryTicker("ZW=F", "小麦期货", "commodity"),
            IndustryTicker("ZS=F", "大豆期货", "commodity"),
        ],
        upstream=[],
        downstream=["food_beverage"],
        key_economies=["US", "BR", "CN", "IN", "AU"],
    ),

    # ═══════════════════════════════════════════
    # 通信与媒体
    # ═══════════════════════════════════════════
    "telecom": Industry(
        code="telecom", name_zh="电信", name_en="Telecommunications",
        category="通信",
        tickers=[
            IndustryTicker("XLC", "通信ETF", "sector_etf"),
            IndustryTicker("IXP", "全球通信ETF", "sector_etf"),
        ],
        upstream=["semiconductor"],
        downstream=["internet"],
        key_economies=["US", "CN", "JP", "EU"],
    ),

    # ═══════════════════════════════════════════
    # 显示面板
    # ═══════════════════════════════════════════
    "display": Industry(
        code="display", name_zh="显示面板", name_en="Display & Panels",
        category="信息技术",
        tickers=[
            IndustryTicker("LPL", "LG Display", "company"),
            IndustryTicker("034220.KS", "LG Display(韩)", "company"),
        ],
        upstream=["specialty_chem", "rare_earth"],
        downstream=["consumer_electronics"],
        key_economies=["KR", "CN", "JP"],
    ),
}

INDUSTRY_CATEGORIES = [
    "信息技术", "能源", "原材料", "工业", "金融", "消费", "医疗健康", "农业", "通信",
]
