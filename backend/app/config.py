"""
Application configuration module.

Uses Pydantic Settings for type-safe configuration management
from environment variables.

Security notes:
- Sensitive values (DATABASE_URL, JWT_SECRET_KEY) have development defaults
  but will raise errors in production if not properly configured
- All secrets should be set via environment variables, never in code
- The .env file should never be committed to version control
"""

import logging
from typing import List, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Default values that are NOT safe for production
# Used to detect if secrets haven't been properly configured
UNSAFE_DEFAULT_JWT_SECRET = "your-secret-key-change-in-production"
UNSAFE_DEFAULT_DB_URL = "postgresql://postgres:postgres@localhost:5432/procurement_db"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Security:
    - In production (ENVIRONMENT != 'development'), the application will
      fail to start if sensitive settings still have their default values.
    - This prevents accidental deployment with weak/exposed secrets.
    """

    # Application Configuration
    APP_NAME: str = "Procurement AI MVP"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Database Configuration
    # WARNING: Default is for local development only
    DATABASE_URL: str = UNSAFE_DEFAULT_DB_URL

    # JWT Configuration
    # WARNING: Default secret is for local development only
    # In production, use a strong random secret (min 32 chars)
    JWT_SECRET_KEY: str = UNSAFE_DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """
        Validate that production deployments have proper secrets configured.

        Why: Prevents deploying with default/weak secrets that are:
        - Known publicly (in source code)
        - Too weak for production security
        - Could lead to complete system compromise

        This validator runs after all fields are loaded and checks:
        1. JWT_SECRET_KEY is not the default value
        2. DATABASE_URL is not using default credentials
        """
        if self.ENVIRONMENT != "development":
            errors = []

            # Check JWT secret
            if self.JWT_SECRET_KEY == UNSAFE_DEFAULT_JWT_SECRET:
                errors.append(
                    "JWT_SECRET_KEY is using the default development value. "
                    "Set a strong random secret (min 32 chars) for production."
                )

            # Check JWT secret length (should be at least 32 chars for security)
            if len(self.JWT_SECRET_KEY) < 32:
                errors.append(
                    f"JWT_SECRET_KEY is too short ({len(self.JWT_SECRET_KEY)} chars). "
                    "Use at least 32 characters for production security."
                )

            # Check database URL for default credentials
            if "postgres:postgres@" in self.DATABASE_URL:
                errors.append(
                    "DATABASE_URL contains default credentials (postgres:postgres). "
                    "Use strong, unique credentials for production."
                )

            if errors:
                error_msg = "SECURITY ERROR - Unsafe configuration for production:\n" + "\n".join(f"  - {e}" for e in errors)
                logger.critical(error_msg)
                raise ValueError(error_msg)

        return self

    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("CORS_ORIGINS", "ALLOWED_FILE_TYPES", mode="before")
    @classmethod
    def parse_list_fields(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse list fields from comma-separated string or list."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TEMPERATURE: float = 0.1
    OPENAI_MAX_TOKENS: int = 2000

    # AI Feature Flags
    AI_USE_TOON_FORMAT: bool = True
    AI_FALLBACK_TO_JSON: bool = True

    # Sentry Configuration
    SENTRY_DSN: str = ""

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True

    # Account Lockout Configuration
    # Why: Prevents brute-force password attacks
    # After MAX_LOGIN_ATTEMPTS failures within LOCKOUT_WINDOW_MINUTES,
    # the account is locked for LOCKOUT_DURATION_MINUTES
    MAX_LOGIN_ATTEMPTS: int = 5  # Failed attempts before lockout
    LOCKOUT_DURATION_MINUTES: int = 15  # How long to lock the account
    LOCKOUT_WINDOW_MINUTES: int = 15  # Time window to count attempts

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
