"""
Test configuration and fixtures.
"""
import pytest
import aiohttp
from unittest.mock import AsyncMock, patch
from datetime import datetime

@pytest.fixture
def mock_sec_response():
    """Mock SEC API response."""
    return {
        "0": {
            "cik_str": "320193",
            "ticker": "AAPL",
            "title": "Apple Inc."
        },
        "1": {
            "cik_str": "1018724",
            "ticker": "AMZN",
            "title": "AMAZON.COM, INC."
        }
    }

@pytest.fixture
def mock_nasdaq_response():
    """Mock NASDAQ API response."""
    return {
        "data": {
            "rows": [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "eps_estimate": "1.43",
                    "eps_actual": "1.52",
                    "time": "AMC",
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
            ]
        }
    }

@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp ClientSession."""
    async def mock_json():
        return {"status": "success"}
        
    mock_response = AsyncMock()
    mock_response.json.side_effect = mock_json
    mock_response.status = 200
    
    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_response
    mock_session.get.return_value = mock_context
    mock_session.post.return_value = mock_context
    
    return mock_session

@pytest.fixture(autouse=True)
def mock_apis(monkeypatch, mock_aiohttp_session):
    """Automatically mock API calls."""
    def mock_client_session(*args, **kwargs):
        return mock_aiohttp_session
        
    monkeypatch.setattr("aiohttp.ClientSession", mock_client_session)