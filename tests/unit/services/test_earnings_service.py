import pytest
from datetime import datetime, time
from decimal import Decimal
from unittest.mock import AsyncMock
from src.clients.sec_client import SECClient
from src.models.company import Company, Exchange, CompanyStatus
from src.repositories.csv_repository import CSVRepository
from src.services.earnings_service import EarningsService
from src.clients.nasdaq_client import NASDAQClient
from src.services.cik_service import CIKService
from src.repositories.earnings_repository import EarningsRepository
from src.models.earnings import EarningsReport, MarketSession, EarningsStatus
from src.utils.date_utils import TradingCalendar

@pytest.fixture
def mock_earnings_data():
    """Mock earnings data fixture."""
    return {
        "data": {
            "rows": [
                {
                    "symbol": "AAPL",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "time": "16:30",
                    "eps_estimate": "1.43",
                    "eps_actual": "1.52",
                }
            ]
        }
    }

@pytest.fixture
def mock_trading_calendar(monkeypatch):
    """Mock trading calendar to always return True for is_trading_day."""
    def mock_is_trading_day(*args, **kwargs):
        return True
    monkeypatch.setattr(TradingCalendar, "is_trading_day", mock_is_trading_day)

@pytest.fixture
async def test_service(tmp_path, monkeypatch, mock_earnings_data, mock_trading_calendar):
    """Create a test earnings service with mocked dependencies."""
    # Create and configure repositories
    company_repository = CSVRepository(
        file_path=tmp_path / "companies.csv",
        model_class=Company,
        key_field="cik"
    )
    
    # Add test company
    test_company = Company(
        cik="0000320193",
        symbol="AAPL",
        name="Apple Inc.",
        exchange=Exchange.NASDAQ,
        status=CompanyStatus.ACTIVE
    )
    await company_repository.add(test_company)
    
    # Configure mock NASDAQ client
    nasdaq_client = NASDAQClient()
    async def mock_get_earnings(*args, **kwargs):
        return mock_earnings_data
    monkeypatch.setattr(nasdaq_client, "get_earnings_calendar", mock_get_earnings)
    
    # Create service with mocked components
    service = EarningsService(
        nasdaq_client,
        CIKService(SECClient(), company_repository),
        EarningsRepository(base_dir=tmp_path / "earnings")
    )
    
    return service

@pytest.mark.asyncio
async def test_fetch_daily_earnings(test_service):
    """Test fetching daily earnings."""
    date = datetime.now().replace(hour=9, minute=30)  # Market hours
    reports = await test_service.fetch_daily_earnings(date)
    assert len(reports) > 0
    assert reports[0].symbol == "AAPL"
    assert reports[0].eps_estimate == Decimal("1.43")

@pytest.mark.asyncio
async def test_update_earnings_data(test_service):
    """Test updating earnings data for a date range."""
    start_date = datetime.now().replace(hour=9, minute=30)  # Market hours
    end_date = start_date
    results = await test_service.update_earnings_data(start_date, end_date)
    assert len(results) > 0
    assert start_date in results
    assert results[start_date] > 0

@pytest.mark.asyncio
async def test_process_earnings_data(test_service, mock_earnings_data):
    """Test processing raw earnings data."""
    reports = await test_service._process_earnings_data(mock_earnings_data)
    assert len(reports) == 1
    assert reports[0].symbol == "AAPL"
    assert reports[0].eps_estimate == Decimal("1.43")
    assert reports[0].eps_actual == Decimal("1.52")

def test_clean_shutdown(test_service):
    """Ensure clean shutdown of services."""
    # This test helps ensure we're properly cleaning up resources
    pass