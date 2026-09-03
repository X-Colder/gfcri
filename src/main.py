import signal
import sys
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger

from src.config import settings
from src.storage.database import wait_for_db
from src.scheduler.daily_job import run_daily_analysis
from src.scheduler.market_data_job import refresh_market_data_cache
from src.notifications.outbox import process_email_outbox, queue_scheduled_emails


def main():
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )

    logger.info("Macro Risk Monitoring Agent starting...")
    logger.info(f"Environment: {settings.app_env}")

    wait_for_db()

    if settings.market_data_refresh_enabled and settings.market_data_refresh_on_startup:
        logger.info("Running initial market data cache refresh on startup...")
        try:
            refresh_market_data_cache()
        except Exception as e:
            logger.error(f"Initial market data refresh failed (non-fatal): {e}")

    logger.info("Running initial analysis on startup...")
    try:
        run_daily_analysis()
    except Exception as e:
        logger.error(f"Initial analysis failed (non-fatal): {e}")

    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    if settings.market_data_refresh_enabled:
        scheduler.add_job(
            refresh_market_data_cache,
            "cron",
            hour=settings.market_data_refresh_hour,
            minute=settings.market_data_refresh_minute,
            id="market_data_refresh",
            name="Historical Market Data Cache Refresh",
            misfire_grace_time=3600,
            max_instances=1,
        )
        logger.info(
            "Market data refresh configured: daily run at "
            f"{settings.market_data_refresh_hour:02d}:"
            f"{settings.market_data_refresh_minute:02d}"
        )

    scheduler.add_job(
        process_email_outbox,
        "interval",
        minutes=1,
        id="email_outbox",
        name="Email Outbox Delivery",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        queue_scheduled_emails,
        "cron",
        hour=6,
        minute=15,
        id="email_schedule_queue",
        name="Queue Scheduled GFCRI Emails",
        misfire_grace_time=3600,
        max_instances=1,
    )
    scheduler.add_job(
        run_daily_analysis,
        "cron",
        hour=settings.daily_run_hour,
        minute=settings.daily_run_minute,
        id="daily_analysis",
        name="Daily Macro Risk Analysis",
        misfire_grace_time=3600,
    )

    logger.info(
        f"Scheduler configured: daily run at {settings.daily_run_hour:02d}:{settings.daily_run_minute:02d}"
    )

    def shutdown(signum, frame):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    logger.info("Scheduler started. Waiting for next run...")
    scheduler.start()


if __name__ == "__main__":
    main()
