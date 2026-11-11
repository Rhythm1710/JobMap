from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment configuration. Secrets come from the process environment, never the repo."""

    model_config = SettingsConfigDict(extra="ignore")

    database_url: str = ""
    service_secret: str = ""
    token_encryption_key: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""
    # Google sends the browser back to the Next.js app so the connect cookie is present.
    google_redirect_uri: str = "http://localhost:3000/api/gmail/callback"
    app_url: str = "http://localhost:3000"

    # Default preset is Groq's free Llama 3.3 endpoint. Any OpenAI-compatible URL works.
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    llm_max_body_chars: int = 1200
    llm_max_calls_per_run: int = 8
    llm_max_retries: int = 3
    llm_retry_base_seconds: float = 1.0

    # Mark applied/assessment jobs ghosted after this many days without an email. 0 disables it.
    ghost_after_days: int = 30

    gmail_lookback_days: int = 180
    gmail_max_messages_per_run: int = 200
    # 0 disables the in-process scheduler. Railway cron can call /internal/cron/sync instead.
    sync_interval_minutes: int = 0

    gmail_scope: str = "https://www.googleapis.com/auth/gmail.readonly"

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key.strip())

    @property
    def google_configured(self) -> bool:
        return bool(self.google_client_id.strip() and self.google_client_secret.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
