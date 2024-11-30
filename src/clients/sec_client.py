"""
SEC API client implementation.
"""
from typing import Dict, Any
from src.clients.base_client import BaseAPIClient
from src.utils.logging_utils import setup_logger, log_api_call
from config.settings import get_settings

settings = get_settings()
logger = setup_logger(__name__)


class SECClient(BaseAPIClient):
    """Client for interacting with SEC APIs."""
    
    def __init__(self) -> None:
        """Initialize SEC API client with required headers."""
        super().__init__(
            base_url="https://www.sec.gov/",
            headers={
                "User-Agent": f"ResearchProject {settings.SEC_USER_AGENT_EMAIL}",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "Host": "www.sec.gov"
            },
            rate_limit_seconds=settings.SEC_RATE_LIMIT_SECONDS
        )

    @log_api_call(logger)
    async def get_company_tickers(self) -> Dict[str, Any]:
        """
        Fetch company tickers and CIK numbers from SEC.
        
        Returns:
            Dict[str, Any]: Mapping of company data including CIK numbers and tickers
            
        Raises:
            APIError: If the request fails
        """
        return await self.get("files/company_tickers.json")

    @log_api_call(logger)
    async def get_company_facts(self, cik: str) -> Dict[str, Any]:
        """
        Fetch company facts for a specific CIK.
        
        Args:
            cik: Company CIK number (10 digits, zero-padded)
            
        Returns:
            Dict[str, Any]: Company facts data
            
        Raises:
            APIError: If the request fails
            ValueError: If CIK format is invalid
        """
        if not (len(cik) == 10 and cik.isdigit()):
            raise ValueError("CIK must be 10 digits")
            
        return await self.get(f"api/xbrl/companyfacts/CIK{cik}.json")

    async def validate_cik(self, cik: str) -> bool:
        """
        Validate if a CIK exists and is active.
        
        Args:
            cik: Company CIK number to validate
            
        Returns:
            bool: True if CIK is valid and active
        """
        try:
            await self.get_company_facts(cik)
            return True
        except Exception:
            return False

    def format_cik(self, cik: str) -> str:
        """
        Format CIK to 10-digit format required by SEC.
        
        Args:
            cik: CIK number to format
            
        Returns:
            str: Formatted 10-digit CIK
            
        Raises:
            ValueError: If CIK cannot be formatted correctly
        """
        try:
            return str(int(cik)).zfill(10)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid CIK format: {cik}") from e