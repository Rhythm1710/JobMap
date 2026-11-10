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
    google_redirect_uri: str = "http://localhost:8000/gmail/oauth/callback"
    app_url: str = "http://localhost:3000"

    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

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
