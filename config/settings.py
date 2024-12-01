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

    # Database
    DATABASE_URL: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Scraping Configuration
    RETRY_BACKOFF_FACTOR: float = 2.0

    # Path Configuration - Set as properties for better testing
    @property
    def BASE_DATA_DIR(self) -> Path:
        return Path(os.getenv("BASE_DATA_DIR", "data"))

    @property
    def RAW_DATA_DIR(self) -> Path:
        return self.BASE_DATA_DIR / "raw"

    @property
    def PROCESSED_DATA_DIR(self) -> Path:
        return self.BASE_DATA_DIR / "processed"

    @property
    def LOG_DIR(self) -> Path:
        return self.BASE_DATA_DIR / "logs"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
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


# Global settings instance
_settings: Optional[Settings] = None


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        env_file = "test.env" if os.getenv("TESTING") else ".env"
        _settings = Settings(_env_file=env_file)
        _settings.create_directories()
    return _settings


def reset_settings() -> None:
    """Reset settings - useful for testing."""
    global _settings
    _settings = None
    get_settings.cache_clear()
