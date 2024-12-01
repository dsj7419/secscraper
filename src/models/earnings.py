"""
Earnings-related domain models.
"""

from datetime import datetime, time
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import ConfigDict, Field, field_validator

from src.models.base import AuditableModel


class MarketSession(str, Enum):
    """Market session when earnings are reported."""

    PRE_MARKET = "PRE"
    AFTER_MARKET = "POST"
    DURING_MARKET = "DURING"
    UNSPECIFIED = "UNSPECIFIED"


class EarningsStatus(str, Enum):
    """Status of earnings report."""

    CONFIRMED = "CONFIRMED"
    TENTATIVE = "TENTATIVE"
    ESTIMATED = "ESTIMATED"
    REPORTED = "REPORTED"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"


class EarningsReport(AuditableModel):
    """Earnings report information model."""

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        json_encoders={Decimal: str, time: lambda t: t.strftime("%H:%M:%S")},
        json_schema_extra={
            "example": {
                "company_cik": "0000320193",
                "symbol": "AAPL",
                "report_date": "2024-11-30T16:30:00Z",
                "eps_estimate": "1.43",
                "eps_actual": "1.52",
                "revenue_estimate": "89700",
                "revenue_actual": "90146",
                "market_session": "POST",
                "status": "REPORTED",
            }
        },
    )

    # Required fields
    company_cik: str = Field(
        ...,
        description="Company CIK",
        min_length=10,
        max_length=10,
        pattern="^[0-9]{10}$",
    )

    symbol: str = Field(..., description="Stock symbol", min_length=1, max_length=10)

    report_date: datetime = Field(..., description="Date of earnings report")

    # Optional financial metrics
    eps_estimate: Optional[Decimal] = Field(
        default=None, description="Estimated earnings per share"
    )

    eps_actual: Optional[Decimal] = Field(
        default=None, description="Actual earnings per share"
    )

    revenue_estimate: Optional[Decimal] = Field(
        default=None, description="Estimated revenue in millions"
    )

    revenue_actual: Optional[Decimal] = Field(
        default=None, description="Actual revenue in millions"
    )

    # Report metadata
    market_session: MarketSession = Field(
        default=MarketSession.UNSPECIFIED, description="Market session for report"
    )

    status: EarningsStatus = Field(
        default=EarningsStatus.TENTATIVE, description="Status of earnings report"
    )

    report_time: Optional[time] = Field(
        default=None, description="Specific time of report"
    )

    conference_call_url: Optional[str] = Field(
        default=None, description="URL for earnings conference call"
    )

    # Computed fields
    eps_surprise: Optional[Decimal] = Field(
        default=None, description="Difference between actual and estimated EPS"
    )

    revenue_surprise: Optional[Decimal] = Field(
        default=None, description="Difference between actual and estimated revenue"
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize stock symbol format."""
        return v.upper().replace("-", ".")

    def calculate_surprises(self) -> None:
        """Calculate EPS and revenue surprises if estimates and actuals exist."""
        if self.eps_estimate is not None and self.eps_actual is not None:
            object.__setattr__(
                self, "eps_surprise", self.eps_actual - self.eps_estimate
            )

        if self.revenue_estimate is not None and self.revenue_actual is not None:
            object.__setattr__(
                self, "revenue_surprise", self.revenue_actual - self.revenue_estimate
            )


class EarningsSummary(AuditableModel):
    """Aggregated earnings summary for analysis."""

    symbol: str = Field(..., description="Stock symbol")

    period_start: datetime = Field(..., description="Start of summary period")

    period_end: datetime = Field(..., description="End of summary period")

    total_reports: int = Field(
        default=0, description="Total number of earnings reports"
    )

    beat_estimates: int = Field(
        default=0, description="Number of times earnings beat estimates"
    )

    missed_estimates: int = Field(
        default=0, description="Number of times earnings missed estimates"
    )

    average_surprise: Optional[Decimal] = Field(
        default=None, description="Average earnings surprise"
    )

    @classmethod
    def from_reports(
        cls, reports: list["EarningsReport"], start_date: datetime, end_date: datetime
    ) -> "EarningsSummary":
        """
        Create summary from list of earnings reports.

        Args:
            reports: List of earnings reports
            start_date: Start date for summary period
            end_date: End date for summary period

        Returns:
            EarningsSummary: Aggregated summary

        Raises:
            ValueError: If reports list is empty
        """
        if not reports:
            raise ValueError("Cannot create summary from empty reports list")

        symbol = reports[0].symbol
        total_reports = len(reports)
        beat_estimates = sum(
            1 for r in reports if r.eps_surprise is not None and r.eps_surprise > 0
        )
        missed_estimates = sum(
            1 for r in reports if r.eps_surprise is not None and r.eps_surprise < 0
        )

        surprises = [r.eps_surprise for r in reports if r.eps_surprise is not None]
        average_surprise = sum(surprises) / len(surprises) if surprises else None

        return cls(
            symbol=symbol,
            period_start=start_date,
            period_end=end_date,
            total_reports=total_reports,
            beat_estimates=beat_estimates,
            missed_estimates=missed_estimates,
            average_surprise=average_surprise,
        )
