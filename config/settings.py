"""
Configuration management for the SEC Earnings Scraper.
Uses environment variables with pydantic for validation.
"""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache
from pydantic import ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # API Configuration
    SEC_USER_AGENT_EMAIL: str
    NASDAQ_API_KEY: Optional[str] = None

    # Rate Limiting
    SEC_RATE_LIMIT_SECONDS: float = 0.1  # 10 requests per second
    NASDAQ_RATE_LIMIT_SECONDS: float = 1.0  # Conservative default
    MAX_CONCURRENT_REQUESTS: int = 5  # Maximum concurrent HTTP requests
    MAX_RETRIES: int = 5  # Maximum number of retry attempts
    REQUEST_TIMEOUT_SECONDS: int = 15  # Request timeout in seconds

    # Paths
    BASE_DATA_DIR: Path = Path("data")
    RAW_DATA_DIR: Path = BASE_DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = BASE_DATA_DIR / "processed"
    LOG_DIR: Path = BASE_DATA_DIR / "logs"

    # Database
    DATABASE_URL: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Scraping Configuration
    RETRY_BACKOFF_FACTOR: float = 2.0

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.RAW_DATA_DIR / "sec",
            self.RAW_DATA_DIR / "nasdaq",
            self.PROCESSED_DATA_DIR / "companies",
            self.PROCESSED_DATA_DIR / "earnings" / "daily",
            self.PROCESSED_DATA_DIR / "earnings" / "master",
            self.LOG_DIR,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    # For testing, use test.env if it exists and we're in test mode
    env_file = "test.env" if os.getenv("TESTING") else ".env"
    settings = Settings(_env_file=env_file)
    settings.create_directories()
    return settings
