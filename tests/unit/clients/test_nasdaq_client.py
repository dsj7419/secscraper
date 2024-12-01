"""Tests for NASDAQ API client."""

import pytest
from datetime import datetime
from src.clients.nasdaq_client import NASDAQClient
from src.utils.date_utils import TradingCalendar


@pytest.mark.asyncio
async def test_get_earnings_calendar(mock_nasdaq_data, monkeypatch):
    """Test fetching earnings calendar."""

    def mock_is_trading_day(*args, **kwargs):
        return True

    monkeypatch.setattr(TradingCalendar, "is_trading_day", mock_is_trading_day)

    async with NASDAQClient() as client:
        date = datetime.now()
        response = await client.get_earnings_calendar(date)
        assert response == mock_nasdaq_data
        assert "data" in response
        assert "rows" in response["data"]
        assert len(response["data"]["rows"]) > 0
        assert response["data"]["rows"][0]["symbol"] == "AAPL"


@pytest.mark.asyncio
async def test_nasdaq_client_validate_symbol(monkeypatch):
    """Test symbol validation."""
    async with NASDAQClient() as client:
        # Updated mock implementation
        async def mock_get_company_info(symbol):
            if symbol == "AAPL":
                return {"status": "Active"}
            return None

        monkeypatch.setattr(client, "get_company_info", mock_get_company_info)
        monkeypatch.setattr(client, "is_test", False)  # Ensure test mode is off

        # Test valid symbol
        assert await client.validate_symbol("AAPL") is True
        # Test invalid symbol
        assert await client.validate_symbol("INVALID") is False
