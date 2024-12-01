"""Tests for CIK service."""
import pytest
from src.clients.sec_client import SECClient
from src.models.company import Company
from src.repositories.csv_repository import CSVRepository
from src.services.cik_service import CIKService

@pytest.mark.asyncio
async def test_cik_service(mock_sec_response, tmp_path):
    """Test CIK service operations."""
    repository = CSVRepository(
        file_path=tmp_path / "companies.csv",
        model_class=Company,
        key_field="cik"
    )
    service = CIKService(SECClient(), repository)
    
    # Test updating company list
    new_symbols = await service.update_company_list()
    assert len(new_symbols) > 0
    assert "AAPL" in new_symbols
    
    # Test getting company
    company = await service.get_company("AAPL")
    assert company is not None
    assert company.cik == "0000320193"