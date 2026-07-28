from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Settings:
    """Runtime settings for the standalone frontend service."""

    backend_base_url: str = os.getenv(
        "BACKEND_BASE_URL",
        "http://127.0.0.1:8000",
    ).rstrip("/")

    request_timeout_seconds: float = float(
        os.getenv("BACKEND_REQUEST_TIMEOUT_SECONDS", "10"),
    )

    secure_cookies: bool = os.getenv(
        "FRONTEND_SECURE_COOKIES",
        "false",
    ).lower() in {"1", "true", "yes", "on"}

    access_cookie_name: str = os.getenv(
        "FRONTEND_ACCESS_COOKIE_NAME",
        "simple_tickets_admin_access_token",
    )

    refresh_cookie_name: str = os.getenv(
        "FRONTEND_REFRESH_COOKIE_NAME",
        "simple_tickets_admin_refresh_token",
    )

    access_cookie_max_age_seconds: int = int(
        os.getenv("FRONTEND_ACCESS_COOKIE_MAX_AGE_SECONDS", "3600"),
    )

    refresh_cookie_max_age_seconds: int = int(
        os.getenv("FRONTEND_REFRESH_COOKIE_MAX_AGE_SECONDS", "1209600"),
    )


settings = Settings()
