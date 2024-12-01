"""Test base client context management."""
import pytest
from src.clients.base_client import BaseAPIClient

class MockClient(BaseAPIClient):
    """Test implementation of BaseAPIClient."""
    def __init__(self):
        super().__init__("https://test.com")

@pytest.mark.asyncio
async def test_client_context_management():
    """Test proper context management of API client."""
    async with MockClient() as client:
        assert client._session is not None
        assert not client._session.closed

    # Session should be closed after context exit
    assert client._session is None

@pytest.mark.asyncio
async def test_multiple_clients():
    """Test multiple clients don't interfere with each other."""
    async with MockClient() as client1:
        async with MockClient() as client2:
            assert client1._session is not None
            assert client2._session is not None
            assert client1._session is not client2._session
