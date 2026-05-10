from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):

    # ── App ──────────────────────────────────────────────────────
    APP_NAME: str = "INDRA"
    SECRET_KEY: str = "change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./indra.db"

    # ── API Keys ─────────────────────────────────────────────────
    DATA_GOV_IN_API_KEY: str = ""
    WHOISXML_API_KEY: str = ""
    ABUSEIPDB_API_KEY: str = ""
    SHODAN_API_KEY: str = ""
    GNEWS_API_KEY: str = ""

    # ── Scheduler ────────────────────────────────────────────────
    FEED_REFRESH_INTERVAL_MINUTES: int = 30
    RATE_LIMIT_PER_MINUTE: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()