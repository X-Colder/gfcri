import os
from dataclasses import dataclass


@dataclass
class Settings:
    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://modelservice.jdcloud.com/anthropic"
    anthropic_model: str = "Claude-Sonnet-4.6"

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "gfcri_db"
    postgres_user: str = "gfcri"
    postgres_password: str = "changeme"

    app_env: str = "development"
    log_level: str = "INFO"
    daily_run_hour: int = 6
    daily_run_minute: int = 0
    market_data_refresh_enabled: bool = True
    market_data_refresh_hour: int = 3
    market_data_refresh_minute: int = 0
    market_data_refresh_period: str = "2y"
    market_data_refresh_on_startup: bool = True

    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    wechat_auto_publish: bool = False

    fred_api_key: str = ""

    public_base_url: str = "http://localhost:3000"
    billing_provider: str = "stripe"
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_monthly_price_id: str = ""
    stripe_annual_price_id: str = ""
    billing_success_url: str = ""
    billing_cancel_url: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            anthropic_base_url=os.getenv("ANTHROPIC_BASE_URL", cls.anthropic_base_url),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", cls.anthropic_model),
            postgres_host=os.getenv("POSTGRES_HOST", cls.postgres_host),
            postgres_port=int(os.getenv("POSTGRES_PORT", str(cls.postgres_port))),
            postgres_db=os.getenv("POSTGRES_DB", cls.postgres_db),
            postgres_user=os.getenv("POSTGRES_USER", cls.postgres_user),
            postgres_password=os.getenv("POSTGRES_PASSWORD", cls.postgres_password),
            app_env=os.getenv("APP_ENV", cls.app_env),
            log_level=os.getenv("LOG_LEVEL", cls.log_level),
            daily_run_hour=int(os.getenv("DAILY_RUN_HOUR", str(cls.daily_run_hour))),
            daily_run_minute=int(os.getenv("DAILY_RUN_MINUTE", str(cls.daily_run_minute))),
            market_data_refresh_enabled=os.getenv(
                "MARKET_DATA_REFRESH_ENABLED", "true"
            ).lower() in ("true", "1", "yes"),
            market_data_refresh_hour=int(
                os.getenv("MARKET_DATA_REFRESH_HOUR", str(cls.market_data_refresh_hour))
            ),
            market_data_refresh_minute=int(
                os.getenv("MARKET_DATA_REFRESH_MINUTE", str(cls.market_data_refresh_minute))
            ),
            market_data_refresh_period=os.getenv(
                "MARKET_DATA_REFRESH_PERIOD", cls.market_data_refresh_period
            ),
            market_data_refresh_on_startup=os.getenv(
                "MARKET_DATA_REFRESH_ON_STARTUP", "true"
            ).lower() in ("true", "1", "yes"),
            wechat_app_id=os.getenv("WECHAT_APP_ID", cls.wechat_app_id),
            wechat_app_secret=os.getenv("WECHAT_APP_SECRET", cls.wechat_app_secret),
            wechat_auto_publish=os.getenv("WECHAT_AUTO_PUBLISH", "").lower() in ("true", "1", "yes"),
            fred_api_key=os.getenv("FRED_API_KEY", cls.fred_api_key),
            public_base_url=os.getenv("PUBLIC_BASE_URL", cls.public_base_url),
            billing_provider=os.getenv("BILLING_PROVIDER", cls.billing_provider),
            stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", cls.stripe_secret_key),
            stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", cls.stripe_webhook_secret),
            stripe_monthly_price_id=os.getenv("STRIPE_MONTHLY_PRICE_ID", cls.stripe_monthly_price_id),
            stripe_annual_price_id=os.getenv("STRIPE_ANNUAL_PRICE_ID", cls.stripe_annual_price_id),
            billing_success_url=os.getenv("BILLING_SUCCESS_URL", cls.billing_success_url),
            billing_cancel_url=os.getenv("BILLING_CANCEL_URL", cls.billing_cancel_url),
        )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings.from_env()
