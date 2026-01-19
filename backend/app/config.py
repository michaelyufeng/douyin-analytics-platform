"""
Application configuration settings.
"""
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_name: str = "Douyin Analytics Platform"
    app_version: str = "1.0.0"
    debug: bool = True

    # Server
    host: str = "0.0.0.0"
    port: int = 8080

    # Database
    database_url: str = "sqlite+aiosqlite:///./douyin_analytics.db"
    # For PostgreSQL: "postgresql+asyncpg://user:password@localhost:5432/douyin_analytics"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = False  # Set to True when Redis is available

    # Douyin API
    douyin_cookie: str = ""
    douyin_user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Request settings
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds

    # Task scheduler
    scheduler_enabled: bool = True
    default_monitor_interval: int = 3600  # seconds

    # Download settings
    download_dir: str = "./downloads"
    max_concurrent_downloads: int = 5

    # CORS
    cors_origins: list = ["http://localhost:8081", "http://119.28.204.113:8081"]

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
