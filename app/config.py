from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "app/.env"),
        case_sensitive=False,
        extra="ignore",
    )

    # Runtime configuration
    app_env: str = "development"
    debug: bool = False
    enable_docs: bool = True

    # Database configuration
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/appdb"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    # Security configuration
    SECRET_KEY: str = "asdfghjkl"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS configuration
    cors_origins: List[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["Authorization", "Content-Type", "Accept", "Origin"]

    # Order processing configuration
    enable_strict_idempotency_check: bool = False
    transaction_settlement_window: float = 0.0
    enable_graceful_degradation: bool = False

    # Wallet operation configuration
    wallet_operation_lock_timeout: int = 0

    # Logging configuration
    log_level: str = "INFO"
    log_requests: bool = True
    log_sql_queries: bool = False

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value: str, info):
        app_env = str(info.data.get("app_env", "development")).lower()
        if app_env == "production" and (not value or value == "asdfghjkl" or len(value) < 32):
            raise ValueError("SECRET_KEY must be set to a strong 32+ character value in production")
        return value


settings = Settings()
