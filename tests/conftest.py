"""Test configuration and fixtures."""
import json
import os
import pytest
import aiohttp
from datetime import datetime
from pathlib import Path

# Set test environment variables
os.environ["TESTING"] = "true"
os.environ["SEC_USER_AGENT_EMAIL"] = "test@example.com"


def pytest_configure(config):
    """Configure pytest environment."""
    # Create test.env file if it doesn't exist
    test_env = Path("test.env")
    if not test_env.exists():
        test_env.write_text(
            "SEC_USER_AGENT_EMAIL=test@example.com\n"
            "NASDAQ_API_KEY=test_key\n"
            "LOG_LEVEL=DEBUG\n"
        )


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch, tmp_path):
    """Mock settings for tests."""
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("SEC_USER_AGENT_EMAIL", "test@example.com")
    
    # Set up temp directories for testing
    monkeypatch.setattr("config.settings.Settings.BASE_DATA_DIR", tmp_path)
    monkeypatch.setattr("config.settings.Settings.RAW_DATA_DIR", tmp_path / "raw")
    monkeypatch.setattr("config.settings.Settings.PROCESSED_DATA_DIR", tmp_path / "processed")
    monkeypatch.setattr("config.settings.Settings.LOG_DIR", tmp_path / "logs")


@pytest.fixture
def mock_nasdaq_data():
    """Mock NASDAQ API response data."""
    return {
        "data": {
            "rows": [
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "eps_estimate": "1.43",
                    "eps_actual": "1.52",
                    "time": "AMC",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                }
            ]
        }
    }


@pytest.fixture
def mock_sec_response():
    """Mock SEC API response data."""
    return {
        "0": {"cik_str": "0000320193", "ticker": "AAPL", "title": "Apple Inc."},
        "1": {"cik_str": "0001018724", "ticker": "AMZN", "title": "AMAZON.COM, INC."},
    }


@pytest.fixture(autouse=True)
def mock_apis(monkeypatch, mock_sec_response, mock_nasdaq_data):
    """Mock API clients."""

    class MockResponse:
        def __init__(self, url):
            self.url = url
            self.status = 200
            self.headers = {}

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def json(self):
            if "/files/company_tickers.json" in self.url:
                return mock_sec_response
            elif "nasdaq.com" in self.url:
                return mock_nasdaq_data
            else:
                return {"status": "success"}

        async def text(self):
            return json.dumps(await self.json())

        def release(self):
            pass

    class ErrorResponse:
        def __init__(self, url):
            self.url = url

        async def __aenter__(self):
            raise aiohttp.ClientResponseError(
                request_info=aiohttp.RequestInfo(
                    url=self.url, method="GET", headers={}, real_url=self.url
                ),
                history=(),
                status=404,
                message="Not Found",
                headers={},
            )

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class MockClientSession:
        def __init__(self, *args, **kwargs):
            self.closed = False

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            await self.close()

        def request(self, method, url, **kwargs):
            if "invalid-endpoint" in url:
                return ErrorResponse(url)
            else:
                return MockResponse(url)

        async def close(self):
            self.closed = True

    monkeypatch.setattr("aiohttp.ClientSession", MockClientSession)
    monkeypatch.setattr("src.clients.base_client.ClientSession", MockClientSession)