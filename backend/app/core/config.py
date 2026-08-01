from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "TRINETRA OSINT API"
    version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./trinetra.db"

    # Redis (optional for dev)
    redis_url: Optional[str] = None

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Rate limiting
    trust_proxy_headers: bool = False  # Set true behind a known reverse proxy

    # Cache TTLs (seconds)
    cache_ttl_default: int = 3600  # 1 hour
    cache_ttl_long: int = 86400    # 24 hours

    # Plugin timeouts (seconds)
    plugin_timeout: int = 30

    # Authentication settings
    # Auth is always enabled. Users register via POST /api/auth/register
    # and log in via POST /api/auth/login.
    # First registered user becomes admin.

    # External API keys
    hibp_api_key: str = ""  # Have I Been Pwned v3 API key (set via HIBP_API_KEY env var)

    # Telegram OSINT Bot
    telegram_bot_token: str = ""  # Telegram Bot token from @BotFather
    telegram_osint_api_url: str = ""  # OSINT Leak API base URL
    telegram_osint_api_key: str = ""  # API key for OSINT API (sent as X-API-Key header)

    # AI Chatbot (Google Gemini)
    gemini_api_key: str = ""  # set via GEMINI_API_KEY env var
    gemini_model: str = "gemini-flash-latest"

    # Cashfree Payment Gateway
    cashfree_app_id: str = ""       # set via CASHFREE_APP_ID env var
    cashfree_secret_key: str = ""   # set via CASHFREE_SECRET_KEY env var
    cashfree_env: str = "sandbox"   # "sandbox" or "production"
    cashfree_webhook_url: str = "http://localhost:8000/api/payment/webhook"  # set via CASHFREE_WEBHOOK_URL env var

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()