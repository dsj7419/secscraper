import pytest
from src.clients.sec_client import SECClient
from src.utils.exceptions import APIError
from src.clients.base_client import settings


@pytest.mark.asyncio
async def test_get_company_tickers():
    """Test fetching company tickers from SEC."""
    async with SECClient() as client:
        response = await client.get_company_tickers()
        assert isinstance(response, dict)
        assert "0" in response
        # Convert response CIK to string format for comparison
        response_cik = str(response["0"]["cik_str"]).zfill(10)
        assert response_cik == "0000320193"
        assert response["0"]["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_validate_cik(monkeypatch):
    """Test CIK validation."""
    async with SECClient() as client:

        async def mock_valid_facts(*args, **kwargs):
            return {"valid": "response"}

        async def mock_invalid_facts(*args, **kwargs):
            raise APIError("Invalid CIK")

        monkeypatch.setattr(client, "get_company_facts", mock_valid_facts)
        assert await client.validate_cik("0000320193") == True

        monkeypatch.setattr(client, "get_company_facts", mock_invalid_facts)
        assert await client.validate_cik("invalid") == False


@pytest.mark.asyncio
async def test_format_cik():
    """Test CIK formatting."""
    async with SECClient() as client:
        assert client.format_cik("320193") == "0000320193"
        assert client.format_cik("0000320193") == "0000320193"
        with pytest.raises(ValueError):
            client.format_cik("invalid")


@pytest.mark.asyncio
async def test_client_cleanup():
    """Test proper client session cleanup."""
    client = SECClient()
    async with client:
        assert client._session is not None
        assert not client._session.closed
    assert client._session is None


@pytest.mark.asyncio
async def test_client_error_handling(monkeypatch):
    """Test error handling in client operations."""
    # Reduce retries and backoff for the test
    monkeypatch.setattr(settings, "MAX_RETRIES", 1)
    monkeypatch.setattr(settings, "RETRY_BACKOFF_FACTOR", 0)

    async with SECClient() as client:
        with pytest.raises(APIError) as exc_info:
            await client.get("invalid-endpoint")
        assert "Request to" in str(exc_info.value)
