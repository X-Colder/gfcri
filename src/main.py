import signal
import sys
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger

from src.config import settings
from src.storage.database import wait_for_db
from src.scheduler.daily_job import run_daily_analysis


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

    logger.info("Running initial analysis on startup...")
    try:
        run_daily_analysis()
    except Exception as e:
        logger.error(f"Initial analysis failed (non-fatal): {e}")

    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
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
