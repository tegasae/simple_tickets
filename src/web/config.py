import os

from pydantic_settings import BaseSettings

from functools import lru_cache


#
class Settings(BaseSettings):
    """Application settings using Pydantic"""
    APP_NAME: str = "Admin Management API"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = "../../db/admins.db"
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
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
    environment='testing'
    """Factory function to get settings based on environment"""
    if environment == "testing":
        return TestSettings()
    else:
        return Settings()


# Default instance (for backward compatibility)
#settings = get_settings()
