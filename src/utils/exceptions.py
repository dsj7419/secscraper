"""
Custom exceptions for the SEC Earnings Scraper application.
"""

from typing import Optional


class ScraperBaseException(Exception):
    """Base exception for all scraper-related errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class APIError(ScraperBaseException):
    """Raised when an API request fails."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)
        self.status_code = status_code
        self.response_body = response_body


class RateLimitError(APIError):
    """Raised when rate limits are exceeded."""

    pass


class ValidationError(ScraperBaseException):
    """Raised when data validation fails."""

    pass


class StorageError(ScraperBaseException):
    """Raised when data storage operations fail."""

    pass


class ConfigurationError(ScraperBaseException):
    """Raised when there's a configuration-related error."""

    pass
