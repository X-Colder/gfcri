"""
Chinese localization for all node IDs, display names, and descriptions.
Single source of truth — import this module wherever Chinese names are needed.
"""

NODE_CN: dict[str, dict[str, str]] = {
    "fed_funds": {"name": "美联储利率", "short": "联储利率", "desc": "美联储联邦基金目标利率"},
    "ust_10y": {"name": "美国10年期国债", "short": "10年美债", "desc": "10年期美国国债收益率"},
    "ust_2y": {"name": "美国2年期国债", "short": "2年美债", "desc": "2年期美国国债收益率"},
    "dxy": {"name": "美元指数", "short": "美元", "desc": "美元对六种主要货币的综合强弱指数"},
    "krw_usd": {"name": "韩元汇率", "short": "韩元", "desc": "韩元兑美元汇率"},
    "kospi": {"name": "韩国股指", "short": "韩股", "desc": "韩国综合股价指数"},
    "vix": {"name": "恐慌指数", "short": "VIX", "desc": "标普500预期波动率，衡量市场恐惧程度"},
    "sox": {"name": "半导体指数", "short": "半导体", "desc": "费城半导体行业指数"},
    "oil_wti": {"name": "原油价格", "short": "原油", "desc": "WTI原油期货价格"},
    "kr_cds_5y": {"name": "韩国国家信用", "short": "韩国CDS", "desc": "韩国5年期主权信用违约互换价差"},
    "orcl_cds": {"name": "Oracle信用", "short": "甲骨文CDS", "desc": "Oracle公司信用违约互换价差"},
    "dram_spot": {"name": "内存芯片价格", "short": "DRAM", "desc": "DRAM内存芯片现货价格"},
    "nand_spot": {"name": "闪存芯片价格", "short": "NAND", "desc": "NAND闪存芯片现货价格"},
    "kr_ca": {"name": "韩国贸易收支", "short": "韩国贸易", "desc": "韩国经常账户余额"},
    "ai_capex": {"name": "AI基建投资", "short": "AI投资", "desc": "科技巨头AI基础设施资本支出"},
    "global_liqd": {"name": "全球流动性", "short": "流动性", "desc": "全球央行流动性综合指标"},
    "us_recession_prob": {"name": "美国衰退概率", "short": "衰退概率", "desc": "美国12个月内经济衰退的模型概率"},
    "hyg": {"name": "垃圾债市场", "short": "垃圾债", "desc": "美国高收益企业债ETF，反映信用风险"},
    "kre": {"name": "区域银行", "short": "银行股", "desc": "美国区域银行ETF，反映银行体系健康"},
    "vnq": {"name": "房地产市场", "short": "房地产", "desc": "美国房地产ETF，反映房价和REIT估值"},
    "consumer_stress": {"name": "消费压力指标", "short": "消费压力", "desc": "消费品/必需品比值，反映消费者信心"},
    "copper": {"name": "铜价", "short": "铜", "desc": "铜期货价格，被称为'铜博士'，反映全球经济活力"},
    "gold": {"name": "黄金价格", "short": "黄金", "desc": "黄金期货价格，经典避险资产"},
    "eurusd": {"name": "欧元汇率", "short": "欧元", "desc": "欧元兑美元汇率"},
    "stoxx50": {"name": "欧洲股指", "short": "欧股", "desc": "欧元区斯托克50蓝筹股指数"},
    "italy_etf": {"name": "意大利股市", "short": "意大利", "desc": "意大利ETF，欧债危机风暴眼代理指标"},
    "cny_usd": {"name": "人民币汇率", "short": "人民币", "desc": "美元兑人民币汇率"},
    "hsi": {"name": "恒生指数", "short": "恒生", "desc": "香港恒生指数，离岸中国资产定价锚"},
    "jpy_usd": {"name": "日元汇率", "short": "日元", "desc": "美元兑日元汇率"},
    "nikkei": {"name": "日经指数", "short": "日经", "desc": "日本日经225股指"},
    "eem": {"name": "新兴市场股票", "short": "新兴股", "desc": "新兴市场股票ETF"},
    "emb": {"name": "新兴市场债券", "short": "新兴债", "desc": "新兴市场美元主权债券ETF"},
    "btc": {"name": "比特币", "short": "BTC", "desc": "比特币价格，风险偏好风向标"},
    "spx": {"name": "标普500", "short": "标普", "desc": "美国标普500股票指数"},
    "lqd": {"name": "投资级债券", "short": "投资债", "desc": "美国投资级企业债ETF"},
    "natgas": {"name": "天然气", "short": "天然气", "desc": "亨利港天然气期货"},
    "wheat": {"name": "小麦", "short": "小麦", "desc": "芝加哥小麦期货，粮食安全指标"},
    "bdry": {"name": "航运指数", "short": "航运", "desc": "干散货航运ETF，全球贸易量温度计"},
}

CHAIN_CN: dict[str, dict[str, str]] = {
    "fed_cascade": {
        "name": "央行加息冲击波",
        "desc": "美联储加息引发连锁反应",
    },
    "dollar_squeeze": {
        "name": "强美元挤压",
        "desc": "美元走强导致新兴市场资金外逃",
    },
    "credit_contagion": {
        "name": "信用危机传染",
        "desc": "企业违约恐慌蔓延到国家层面",
    },
    "housing_bank_doom": {
        "name": "房地产银行危机",
        "desc": "房价下跌拖垮银行系统",
    },
    "consumer_recession": {
        "name": "消费崩塌衰退",
        "desc": "消费者不敢花钱引发经济衰退",
    },
    "ai_semi_cycle": {
        "name": "AI芯片周期",
        "desc": "AI投资驱动芯片涨跌周期",
    },
    "safe_haven_flight": {
        "name": "避险资金逃亡",
        "desc": "资金涌向黄金等避风港",
    },
    "europe_contagion": {"name": "欧债危机传染", "desc": "意大利风险→欧元走弱→美元走强→新兴市场承压"},
    "china_shockwave": {"name": "中国冲击波", "desc": "人民币贬值→港股暴跌→韩国出口受创"},
    "yen_carry_unwind": {"name": "日元套利平仓", "desc": "日元急升→套利交易被迫平仓→全球波动率飙升"},
    "crypto_contagion": {"name": "加密货币传染", "desc": "比特币崩盘→风险偏好崩塌→波动率飙升"},
    "food_energy_shock": {"name": "粮食能源冲击", "desc": "粮食/能源价格飙升→通胀恐慌→市场避险"},
}

SI_CN: dict[str, str] = {
    "SI_RATES": "利率与央行",
    "SI_FX": "全球汇率",
    "SI_US_EQUITY": "美国股市",
    "SI_ASIA_EQUITY": "亚洲股市",
    "SI_EUROPE": "欧洲市场",
    "SI_CREDIT": "信用与违约",
    "SI_BANKING": "银行与房产",
    "SI_COMMODITY": "商品与贸易",
    "SI_SENTIMENT": "情绪与避险",
}

ALERT_CN: dict[str, str] = {
    "green": "平静",
    "yellow": "关注",
    "orange": "警惕",
    "red": "危险",
}


def cn_name(node_id: str) -> str:
    return NODE_CN.get(node_id, {}).get("name", node_id)


def cn_short(node_id: str) -> str:
    return NODE_CN.get(node_id, {}).get("short", node_id)
