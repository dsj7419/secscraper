import json
import pytest
import aiohttp
from datetime import datetime

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
                    "date": datetime.now().strftime("%Y-%m-%d")
                }
            ]
        }
    }

@pytest.fixture
def mock_sec_response():
    """Mock SEC API response data."""
    return {
        "0": {
            "cik_str": "0000320193",
            "ticker": "AAPL",
            "title": "Apple Inc."
        },
        "1": {
            "cik_str": "0001018724",
            "ticker": "AMZN",
            "title": "AMAZON.COM, INC."
        }
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
            if '/files/company_tickers.json' in self.url:
                return mock_sec_response
            elif 'nasdaq.com' in self.url:
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
                request_info=aiohttp.RequestInfo(url=self.url, method='GET', headers={}, real_url=self.url),
                history=(),
                status=404,
                message='Not Found',
                headers={}
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
            if 'invalid-endpoint' in url:
                return ErrorResponse(url)
            else:
                return MockResponse(url)

        async def close(self):
            self.closed = True

    # Patch aiohttp.ClientSession and the ClientSession used in base_client
    monkeypatch.setattr('aiohttp.ClientSession', MockClientSession)
    monkeypatch.setattr('src.clients.base_client.ClientSession', MockClientSession)
