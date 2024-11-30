"""
NASDAQ API client implementation.
"""
from datetime import datetime, date
from typing import Dict, Any, Optional
import os

from src.clients.base_client import BaseAPIClient
from src.utils.logging_utils import setup_logger, log_api_call
from src.utils.date_utils import TradingCalendar
from config.settings import get_settings

settings = get_settings()
logger = setup_logger(__name__)


class NASDAQClient(BaseAPIClient):
    """Client for interacting with NASDAQ APIs."""
    
    def __init__(self) -> None:
        """Initialize NASDAQ API client."""
        super().__init__(
            base_url="https://api.nasdaq.com/api",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*",
            },
            rate_limit_seconds=settings.NASDAQ_RATE_LIMIT_SECONDS
        )
        self.trading_calendar = TradingCalendar()
        self.is_test = bool(os.getenv('TESTING', False))
        
        if settings.NASDAQ_API_KEY:
            self.headers["Authorization"] = f"Bearer {settings.NASDAQ_API_KEY}"

    def _get_mock_data(self, date_: date) -> Dict[str, Any]:
        """Get mock data for testing."""
        return {
            "data": {
                "rows": [
                    {
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "eps_estimate": "1.43",
                        "eps_actual": "1.52",
                        "time": "AMC",
                        "date": date_.strftime("%Y-%m-%d")
                    }
                ]
            }
        }

    @log_api_call(logger)
    async def get_earnings_calendar(self, date_: date) -> Dict[str, Any]:
        """Fetch earnings calendar data for a specific date."""
        if not self.trading_calendar.is_trading_day(date_):
            logger.warning(f"{date_} is not a trading day")
            return {"data": {"rows": []}}
        
        if self.is_test:
            return self._get_mock_data(date_)
            
        endpoint = f"calendar/earnings"
        params = {"date": date_.strftime("%Y-%m-%d")}
        
        return await self.get(endpoint, params=params)

    async def _process_earnings_response(
        self,
        response: Dict[str, Any]
    ) -> list[Dict[str, Any]]:
        """Process earnings calendar response data."""
        try:
            return response.get("data", {}).get("rows", [])
        except AttributeError as e:
            logger.error("Invalid response format", exc_info=True)
            raise ValueError("Invalid response format") from e

    @log_api_call(logger)
    async def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed company information."""
        if self.is_test:
            return {
                "symbol": symbol,
                "status": "Active"
            }
            
        endpoint = f"quote/{symbol}/info"
        try:
            return await self.get(endpoint)
        except Exception as e:
            logger.warning(f"Could not fetch info for {symbol}: {str(e)}")
            return None

    @log_api_call(logger)
    async def get_historical_earnings(
        self,
        symbol: str,
        limit: int = 4
    ) -> list[Dict[str, Any]]:
        """Fetch historical earnings data for a company."""
        if self.is_test:
            return []
            
        endpoint = f"company/{symbol}/earnings-history"
        params = {"limit": limit}
        
        response = await self.get(endpoint, params=params)
        return await self._process_earnings_response(response)

    async def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol exists and is active."""
        if self.is_test:
            return True
            
        try:
            info = await self.get_company_info(symbol)
            return info is not None and info.get("status") == "Active"
        except Exception:
            return False