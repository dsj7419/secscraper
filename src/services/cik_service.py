"""
Service for managing CIK (Central Index Key) data.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from config.settings import get_settings
from src.clients.sec_client import SECClient
from src.models.company import Company, CompanyStatus
from src.repositories.csv_repository import CSVRepository
from src.utils.exceptions import APIError, StorageError
from src.utils.logging_utils import log_execution_time, setup_logger

settings = get_settings()
logger = setup_logger(__name__)


class CIKService:
    """Service for managing company CIK data."""

    def __init__(
        self, sec_client: SECClient, company_repository: CSVRepository[Company]
    ) -> None:
        """
        Initialize CIK service.

        Args:
            sec_client: SEC API client
            company_repository: Company data repository
        """
        self.sec_client = sec_client
        self.repository = company_repository
        self._cache: Dict[str, Company] = {}
        self._cache_lock = asyncio.Lock()
        self._last_refresh: Optional[datetime] = None

    async def _refresh_cache(self) -> None:
        """Refresh the internal CIK cache."""
        async with self._cache_lock:
            # Check if cache is still fresh
            now = datetime.utcnow()
            if self._last_refresh and now - self._last_refresh < timedelta(hours=24):
                return

            # Clear existing cache
            self._cache.clear()

            # Get all companies
            companies = await self.repository.get_all()
            self._cache = {company.symbol: company for company in companies}

            self._last_refresh = now

    @log_execution_time(logger)
    async def get_company(self, symbol: str) -> Optional[Company]:
        """
        Get company by symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Optional[Company]: Company if found
        """
        await self._refresh_cache()
        normalized_symbol = symbol.upper().replace("-", ".")
        return self._cache.get(normalized_symbol)

    @log_execution_time(logger)
    async def get_cik(self, symbol: str) -> Optional[str]:
        """
        Get CIK for symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Optional[str]: CIK if found
        """
        company = await self.get_company(symbol)
        return company.cik if company else None

    @log_execution_time(logger)
    async def update_company_list(self) -> Set[str]:
        """
        Update company list from SEC.

        Returns:
            Set[str]: Set of new symbols added

        Raises:
            APIError: If SEC API request fails
            StorageError: If storage operation fails
        """
        try:
            # Get current companies
            current_companies = await self.repository.get_all()
            current_symbols = {c.symbol for c in current_companies}

            # Get new data from SEC
            company_data = await self.sec_client.get_company_tickers()

            # Process new companies
            new_companies = []
            new_symbols = set()

            for data in company_data.values():
                symbol = data.get("ticker") or data.get("symbol")
                if not symbol:
                    logger.warning(f"Missing symbol for {data.get('title')}")
                    continue

                symbol = symbol.upper().replace("-", ".")
                if symbol in current_symbols:
                    continue

                try:
                    company = Company(
                        cik=str(data["cik_str"]).zfill(10),
                        symbol=symbol,
                        name=data["title"],
                        status=CompanyStatus.ACTIVE,
                    )
                    new_companies.append(company)
                    new_symbols.add(symbol)
                except ValueError as e:
                    logger.error(f"Invalid company data for {symbol}: {str(e)}")

            # Save new companies
            if new_companies:
                await self.repository.add_many(new_companies)
                logger.info(f"Added {len(new_companies)} new companies")

                # Force cache refresh
                self._last_refresh = None

            return new_symbols

        except APIError:
            logger.error("Failed to fetch company data from SEC", exc_info=True)
            raise
        except StorageError:
            logger.error("Failed to store company data", exc_info=True)
            raise

    @log_execution_time(logger)
    async def validate_symbols(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Validate multiple symbols.

        Args:
            symbols: List of symbols to validate

        Returns:
            Dict[str, bool]: Mapping of symbols to validity
        """
        await self._refresh_cache()
        return {
            symbol: symbol.upper().replace("-", ".") in self._cache
            for symbol in symbols
        }

    async def get_active_companies(self) -> List[Company]:
        """
        Get all active companies.

        Returns:
            List[Company]: Active companies
        """
        await self._refresh_cache()
        return [
            company
            for company in self._cache.values()
            if company.status == CompanyStatus.ACTIVE
        ]
