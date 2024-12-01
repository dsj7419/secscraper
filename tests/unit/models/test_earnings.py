import pytest
from decimal import Decimal
from datetime import datetime
from src.models.earnings import EarningsReport, MarketSession, EarningsStatus

def test_earnings_report_model():
    """Test earnings report model."""
    data = {
        "company_cik": "0000320193",
        "symbol": "AAPL",
        "report_date": datetime.now(),
        "eps_estimate": Decimal("1.43"),
        "eps_actual": Decimal("1.52"),
        "market_session": MarketSession.AFTER_MARKET,
        "status": EarningsStatus.REPORTED
    }
    report = EarningsReport(**data)
    # Create a copy and calculate surprises
    report.calculate_surprises()
    assert report.company_cik == "0000320193"
    assert report.eps_surprise == Decimal("0.09")