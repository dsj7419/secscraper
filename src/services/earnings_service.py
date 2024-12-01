"""
Service for managing earnings data collection and analysis.
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, cast

from config.settings import get_settings
from src.clients.nasdaq_client import NASDAQClient
from src.models.earnings import (
    EarningsReport,
    EarningsStatus,
    EarningsSummary,
    MarketSession,
)
from src.repositories.earnings_repository import EarningsRepository
from src.services.cik_service import CIKService
from src.utils.date_utils import TradingCalendar
from src.utils.exceptions import APIError, StorageError
from src.utils.logging_utils import log_execution_time, setup_logger

settings = get_settings()
logger = setup_logger(__name__)


class EarningsService:
    """Service for managing earnings data."""

    def __init__(
        self,
        nasdaq_client: NASDAQClient,
        cik_service: CIKService,
        earnings_repository: EarningsRepository,
    ) -> None:
        """
        Initialize earnings service.

        Args:
            nasdaq_client: NASDAQ API client
            cik_service: CIK data service
            earnings_repository: Earnings data repository
        """
        self.nasdaq_client = nasdaq_client
        self.cik_service = cik_service
        self.repository = earnings_repository
        self.trading_calendar = TradingCalendar()
        self._processing_lock = asyncio.Lock()

    async def _process_earnings_data(
        self, raw_data: Dict[str, Any]
    ) -> List[EarningsReport]:
        """
        Process raw earnings data into domain models.

        Args:
            raw_data: Raw earnings data from NASDAQ

        Returns:
            List[EarningsReport]: Processed earnings reports
        """
        reports = []
        rows = raw_data.get("data", {}).get("rows", [])

        for row in rows:
            try:
                # Get CIK for symbol
                symbol = row.get("symbol")
                if not symbol:
                    logger.warning("Missing symbol in earnings data")
                    continue

                cik = await self.cik_service.get_cik(symbol)
                if not cik:
                    logger.warning(f"No CIK found for symbol {symbol}")
                    continue

                # Parse report date and time
                date_str = cast(str, row.get("date", ""))
                report_date = datetime.strptime(date_str, "%Y-%m-%d")

                time_str = row.get("time", "")
                if time_str:
                    try:
                        report_time = datetime.strptime(time_str, "%H:%M").time()
                    except ValueError:
                        report_time = None
                else:
                    report_time = None

                # Determine market session
                market_session = MarketSession.UNSPECIFIED
                if time_str:
                    if "before" in time_str.lower():
                        market_session = MarketSession.PRE_MARKET
                    elif "after" in time_str.lower():
                        market_session = MarketSession.AFTER_MARKET

                # Create report
                report = EarningsReport(
                    company_cik=cik,
                    symbol=symbol,
                    report_date=report_date,
                    report_time=report_time,
                    market_session=market_session,
                    eps_estimate=(
                        Decimal(str(row.get("eps_estimate", 0)))
                        if row.get("eps_estimate")
                        else None
                    ),
                    eps_actual=(
                        Decimal(str(row.get("eps_actual", 0)))
                        if row.get("eps_actual")
                        else None
                    ),
                    revenue_estimate=(
                        Decimal(str(row.get("revenue_estimate", 0)))
                        if row.get("revenue_estimate")
                        else None
                    ),
                    revenue_actual=(
                        Decimal(str(row.get("revenue_actual", 0)))
                        if row.get("revenue_actual")
                        else None
                    ),
                    status=EarningsStatus.CONFIRMED,
                )

                # Calculate surprises
                report.calculate_surprises()
                reports.append(report)

            except Exception as e:
                logger.error(f"Error processing earnings row: {str(e)}", exc_info=True)
                continue

        return reports

    @log_execution_time(logger)
    async def fetch_daily_earnings(self, date_obj: datetime) -> List[EarningsReport]:
        """
        Fetch and store earnings for a specific date.

        Args:
            date_obj: Date to fetch earnings for

        Returns:
            List[EarningsReport]: Processed earnings reports

        Raises:
            APIError: If NASDAQ API request fails
            StorageError: If storage operation fails
        """
        # Convert datetime to date for trading calendar check
        check_date = date_obj.date()
        if not self.trading_calendar.is_trading_day(check_date):
            logger.info(f"{check_date} is not a trading day")
            return []

        async with self._processing_lock:
            try:
                # Get earnings data using date object
                raw_data = await self.nasdaq_client.get_earnings_calendar(check_date)
                reports = await self._process_earnings_data(raw_data)

                # Store reports
                for report in reports:
                    await self.repository.add_daily_report(date_obj, report)

                logger.info(
                    f"Processed {len(reports)} earnings reports for {check_date}"
                )
                return reports

            except APIError as e:
                logger.error(f"Failed to fetch earnings data: {str(e)}", exc_info=True)
                raise
            except StorageError as e:
                logger.error(f"Failed to store earnings data: {str(e)}", exc_info=True)
                raise

    @log_execution_time(logger)
    async def update_earnings_data(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[datetime, int]:
        """
        Update earnings data for date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Dict[datetime, int]: Number of reports processed per date
        """
        results: Dict[datetime, int] = {}
        current_date = start_date

        while current_date <= end_date:
            try:
                reports = await self.fetch_daily_earnings(current_date)
                results[current_date] = len(reports)
            except Exception as e:
                logger.error(f"Failed to process {current_date.date()}: {str(e)}")
                results[current_date] = 0

            # Get next trading day as datetime at start of day
            next_date = self.trading_calendar.next_trading_day(current_date.date())
            current_date = datetime.combine(next_date, datetime.min.time())

        return results

    async def get_earnings_summary(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> Optional[EarningsSummary]:
        """
        Get earnings summary for symbol and date range.

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date

        Returns:
            Optional[EarningsSummary]: Summary if data exists
        """
        return await self.repository.get_summary(symbol, start_date, end_date)

    async def get_missing_dates(
        self, start_date: datetime, end_date: datetime
    ) -> List[datetime]:
        """
        Get dates with missing earnings data.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List[datetime]: Dates with missing data
        """
        all_missing = await self.repository.get_missing_dates(start_date, end_date)
        return [
            date
            for date in all_missing
            if self.trading_calendar.is_trading_day(date.date())
        ]
