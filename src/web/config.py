
from pydantic import model_validator
from pydantic_settings import BaseSettings

from functools import lru_cache
from pathlib import Path
from typing import Literal


#
class Settings(BaseSettings):
    """Application settings using Pydantic"""
    APP_NAME: str = "Admin Management API"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = "db/admins.db"
    SECRET_KEY: str = "19d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7" #0
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5
    REFRESH_TOKEN_EXPIRE_DAYS:int = 7
    ENVIRONMENT: str = "production"
    JWT_ISSUER:str="simple - tickets"
    JWT_AUDIENCE:str="simple - tickets - api"
    # Accepted for deployment compatibility. FastAPI uses DATABASE_URL.
    REFRESH_TOKEN_BACKEND: Literal["memory", "sqlite"] = "memory"
    REFRESH_TOKEN_SQLITE_PATH: Path | None = None

    @model_validator(mode="after")
    def require_configured_signing_key(self):
        if (
            "SECRET_KEY" not in self.model_fields_set
            or len(self.SECRET_KEY.encode()) < 32
            or self.SECRET_KEY == Settings.model_fields["SECRET_KEY"].default
        ):
            raise ValueError("Configure SECRET_KEY with a new, random key of at least 32 bytes")
        return self

    class Config:
        env_file = ".env"
        case_sensitive = False
        hide_input_in_errors = True


class TestSettings(Settings):
    """Test-specific settings"""
    DATABASE_URL: str = ":memory:"  # SQLite in-memory database
    SECRET_KEY: str = "test-secret-key"
    ENVIRONMENT: str = "testing"

    @model_validator(mode="after")
    def require_configured_signing_key(self):
        # Explicit test configuration can use the built-in test fixture key.
        return self

    class Config:
        env_file = ".env.test"
        case_sensitive = False
        hide_input_in_errors = True


@lru_cache()
def get_settings(environment: str = "production") -> Settings:
    """Factory function to get settings based on environment"""
    if environment == "testing":
        return TestSettings()
    else:
        return Settings()


# Default instance (for backward compatibility)
#settings = get_settings()
