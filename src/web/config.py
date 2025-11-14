import os

from pydantic_settings import BaseSettings

from functools import lru_cache


#
class Settings(BaseSettings):
    """Application settings using Pydantic"""
    APP_NAME: str = "Admin Management API"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = "../../db/admins.db"
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS:int = 1
    ENVIRONMENT: str = "production"

    class Config:
        env_file = ".env"
        case_sensitive = False


class TestSettings(Settings):
    """Test-specific settings"""
    DATABASE_URL: str = ":memory:"  # SQLite in-memory database
    SECRET_KEY: str = "test-secret-key"
    ENVIRONMENT: str = "testing"

    class Config:
        env_file = ".env.test"
        case_sensitive = False


@lru_cache()
def get_settings(environment: str = "production") -> Settings:
    """Factory function to get settings based on environment"""
    if environment == "testing":
        return TestSettings()
    else:
        return Settings()


# Default instance (for backward compatibility)
#settings = get_settings()
