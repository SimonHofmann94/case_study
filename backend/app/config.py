"""
Application configuration module.

Uses Pydantic Settings for type-safe configuration management
from environment variables.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application Configuration
    APP_NAME: str = "Procurement AI MVP"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/procurement_db"

    # JWT Configuration
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # OpenAI Configuration
    OPENAI_API_KEY: str = ""

    # Sentry Configuration
    SENTRY_DSN: str = ""

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True

    # File Upload Configuration
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: List[str] = ["application/pdf", "text/plain"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def max_upload_size_bytes(self) -> int:
        """Convert max upload size from MB to bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


# Global settings instance
settings = Settings()
