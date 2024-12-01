"""
Earnings data repository implementation.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set

import pandas as pd

from config.settings import get_settings
from src.models.earnings import EarningsReport, EarningsSummary
from src.repositories.csv_repository import TimeRangeCSVRepository
from src.utils.exceptions import StorageError

settings = get_settings()


class EarningsRepository(TimeRangeCSVRepository[EarningsReport]):
    """Repository for earnings report data."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        """
        Initialize earnings repository.

        Args:
            base_dir: Optional base directory for CSV files
        """
        self.base_dir = base_dir or settings.PROCESSED_DATA_DIR / "earnings"
        self.base_dir.mkdir(parents=True, exist_ok=True)

        super().__init__(
            file_path=self.base_dir / "earnings_master.csv",
            model_class=EarningsReport,
            key_field="symbol",
            date_field="report_date",
        )

        self.daily_dir = self.base_dir / "daily"
        self.daily_dir.mkdir(exist_ok=True)

    async def add_daily_report(
        self, date: datetime, report: EarningsReport
    ) -> EarningsReport:
        """
        Add earnings report to both daily and master files.

        Args:
            date: Report date
            report: Earnings report

        Returns:
            EarningsReport: Added report

        Raises:
            StorageError: If operation fails
        """
        daily_file = self.daily_dir / f"{date.strftime('%Y-%m-%d')}_earnings.csv"
        daily_repo = TimeRangeCSVRepository(
            file_path=daily_file,
            model_class=EarningsReport,
            key_field="symbol",
            date_field="report_date",
        )

        try:
            await daily_repo.add(report)
            await self.add(report)
            return report
        except Exception as e:
            raise StorageError(f"Failed to add daily report: {str(e)}") from e

    async def get_by_symbol(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[EarningsReport]:
        """
        Get earnings reports for a specific symbol.

        Args:
            symbol: Stock symbol
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            List[EarningsReport]: Matching reports
        """
        if start_date and end_date:
            all_reports = await self.get_by_date_range(start_date, end_date)
        else:
            all_reports = await self.get_all()

        return [r for r in all_reports if r.symbol == symbol]

    async def get_summary(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> Optional[EarningsSummary]:
        """
        Get earnings summary for a symbol and date range.

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date

        Returns:
            Optional[EarningsSummary]: Summary if reports exist
        """
        reports = await self.get_by_symbol(symbol, start_date, end_date)
        if not reports:
            return None

        return EarningsSummary.from_reports(reports, start_date, end_date)

    async def get_latest_report_date(self) -> Optional[datetime]:
        """
        Get the most recent report date in the database.

        Returns:
            Optional[datetime]: Latest report date or None if no reports
        """
        reports = await self.get_all()
        if not reports:
            return None

        return max(r.report_date for r in reports)

    async def get_missing_dates(
        self, start_date: datetime, end_date: datetime
    ) -> List[datetime]:
        """
        Get dates in range with missing reports.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List[datetime]: Dates with no reports
        """
        # Create set of dates as datetime objects
        all_dates: Set[datetime] = {
            datetime.combine(
                (start_date + pd.Timedelta(days=x)).date(), datetime.min.time()
            )
            for x in range((end_date - start_date).days + 1)
        }

        reports = await self.get_by_date_range(start_date, end_date)
        # Ensure consistent datetime format for comparison
        report_dates = {
            datetime.combine(r.report_date.date(), datetime.min.time()) for r in reports
        }

        return sorted(all_dates - report_dates)
