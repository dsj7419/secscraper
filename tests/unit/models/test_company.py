import pytest
from src.models.company import Company, Exchange, CompanyStatus

def test_company_model_validation():
    """Test company model validation."""
    # Valid company data
    valid_data = {
        "cik": "0000320193",
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "exchange": Exchange.NASDAQ,
        "status": CompanyStatus.ACTIVE
    }
    company = Company(**valid_data)
    assert company.cik == "0000320193"
    assert company.symbol == "AAPL"

    # Test symbol normalization
    company = Company(**{**valid_data, "symbol": "AAPL-B"})
    assert company.symbol == "AAPL.B"

    # Invalid CIK should raise error
    with pytest.raises(ValueError):
        Company(**{**valid_data, "cik": "123"})