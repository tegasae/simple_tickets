from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Frontend service settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    backend_base_url: str = "http://127.0.0.1:8000"
    request_timeout_seconds: float = 20.0

    access_cookie_name: str = "simple_tickets_admin_access"
    refresh_cookie_name: str = "simple_tickets_admin_refresh"
    access_cookie_max_age_seconds: int = 60 * 60
    refresh_cookie_max_age_seconds: int = 60 * 60 * 24 * 30
    secure_cookies: bool = False


settings = Settings()
