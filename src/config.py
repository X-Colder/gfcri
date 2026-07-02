import os
from dataclasses import dataclass


@dataclass
class Settings:
    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://modelservice.jdcloud.com/anthropic"
    anthropic_model: str = "Claude-Sonnet-4.6"

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "macro_risk_db"
    postgres_user: str = "macro_risk"
    postgres_password: str = "changeme"

    app_env: str = "development"
    log_level: str = "INFO"
    daily_run_hour: int = 6
    daily_run_minute: int = 0

    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    wechat_auto_publish: bool = False

    fred_api_key: str = ""

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
            wechat_app_id=os.getenv("WECHAT_APP_ID", cls.wechat_app_id),
            wechat_app_secret=os.getenv("WECHAT_APP_SECRET", cls.wechat_app_secret),
            wechat_auto_publish=os.getenv("WECHAT_AUTO_PUBLISH", "").lower() in ("true", "1", "yes"),
            fred_api_key=os.getenv("FRED_API_KEY", cls.fred_api_key),
        )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings.from_env()
