"""
Base HTTP client with advanced error handling and retry logic.
"""
from typing import Any, Dict, Optional
import asyncio
from aiohttp import ClientSession, ClientResponse, TCPConnector, ClientTimeout
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config.settings import get_settings
from src.utils.exceptions import APIError, RateLimitError
from src.utils.logging_utils import setup_logger

settings = get_settings()
logger = setup_logger(__name__)


class BaseAPIClient:
    """Base class for API clients with built-in retry and error handling."""

    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        rate_limit_seconds: float = 1.0,
    ):
        """
        Initialize the API client.

        Args:
            base_url: Base URL for API requests
            headers: Optional headers to include in all requests
            rate_limit_seconds: Minimum time between requests
        """
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.rate_limit_seconds = rate_limit_seconds
        self._last_request_time: float = 0
        self._session: Optional[ClientSession] = None
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "BaseAPIClient":
        """Set up async context manager."""
        await self.setup()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up async context manager."""
        await self.cleanup()

    async def setup(self) -> None:
        """Set up the API client session."""
        if self._session is None:
            timeout = ClientTimeout(total=settings.REQUEST_TIMEOUT_SECONDS)
            connector = TCPConnector(
                limit=settings.MAX_CONCURRENT_REQUESTS,
                force_close=True
            )
            self._session = ClientSession(
                connector=connector,
                headers=self.headers,
                raise_for_status=True,
                timeout=timeout
            )

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(
            multiplier=settings.RETRY_BACKOFF_FACTOR,
            min=1,
            max=60
        ),
        retry=retry_if_exception_type(APIError),
        reraise=True  # Add this line
    )
    async def _make_request(self, method: str, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Make an HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for the request

        Returns:
            Dict[str, Any]: Parsed response data

        Raises:
            APIError: If the request fails
            RateLimitError: If rate limit is exceeded
        """
        if self._session is None:
            await self.setup()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with self._lock:
            # Implement rate limiting
            now = asyncio.get_event_loop().time()
            time_since_last_request = now - self._last_request_time
            if time_since_last_request < self.rate_limit_seconds:
                await asyncio.sleep(self.rate_limit_seconds - time_since_last_request)
            
            try:
                async with self._session.request(
                    method,
                    url,
                    **kwargs,
                ) as response:
                    self._last_request_time = asyncio.get_event_loop().time()
                    
                    if response.status == 429:
                        raise RateLimitError(
                            "Rate limit exceeded",
                            status_code=429,
                            response_body=await response.text(),
                        )
                    
                    return await self._handle_response(response)
                    
            except asyncio.TimeoutError as e:
                logger.error(f"Request timeout: {str(e)}")
                raise APIError(
                    f"Request to {url} timed out",
                    original_error=e
                )
            except Exception as e:
                logger.error(f"Request failed: {str(e)}", exc_info=True)
                raise APIError(
                    f"Request to {url} failed: {str(e)}",
                    original_error=e
                )

    async def _handle_response(self, response: ClientResponse) -> Dict[str, Any]:
        """
        Handle API response and perform necessary validation.

        Args:
            response: API response object

        Returns:
            Dict[str, Any]: Parsed response data

        Raises:
            APIError: If response validation fails
        """
        try:
            data = await response.json()
            # Add any common response validation here
            return data
        except ValueError as e:
            raise APIError(
                "Failed to parse JSON response",
                status_code=response.status,
                response_body=await response.text(),
                original_error=e,
            )

    async def get(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Make a GET request."""
        return await self._make_request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Make a POST request."""
        return await self._make_request("POST", endpoint, **kwargs)