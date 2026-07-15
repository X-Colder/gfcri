from loguru import logger

from src.config import settings
from src.data.collector import MarketDataCollector


def refresh_market_data_cache(period: str | None = None) -> dict:
    """Refresh historical market data cache without publishing a risk index."""
    refresh_period = period or settings.market_data_refresh_period
    logger.info("=== Starting market data cache refresh ===")
    summary = MarketDataCollector().refresh_market_data_cache(refresh_period)
    logger.info(
        "Market data cache refresh completed: "
        f"period={summary['period']}, rows={summary['rows']}, "
        f"tickers={summary['tickers']}, "
        f"range={summary['start_date']}..{summary['end_date']}"
    )
    return summary
