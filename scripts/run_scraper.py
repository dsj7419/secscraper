"""
Main script for running the SEC earnings scraper.
"""
import asyncio
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Optional

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.clients.sec_client import SECClient
from src.clients.nasdaq_client import NASDAQClient
from src.services.cik_service import CIKService
from src.services.earnings_service import EarningsService
from src.repositories.csv_repository import CSVRepository
from src.repositories.earnings_repository import EarningsRepository
from src.models.company import Company
from src.utils.date_utils import TradingCalendar
from src.utils.logging_utils import setup_logger
from config.settings import get_settings

settings = get_settings()
logger = setup_logger(__name__)


async def initialize_services() -> tuple[CIKService, EarningsService]:
    """
    Initialize all required services and their dependencies.
    
    Returns:
        tuple[CIKService, EarningsService]: Initialized services
    """
    # Initialize clients
    sec_client = SECClient()
    nasdaq_client = NASDAQClient()
    
    # Initialize repositories
    company_repository = CSVRepository(
        file_path=settings.PROCESSED_DATA_DIR / "companies" / "companies.csv",
        model_class=Company,
        key_field="cik"
    )
    earnings_repository = EarningsRepository()
    
    # Initialize services
    cik_service = CIKService(sec_client, company_repository)
    earnings_service = EarningsService(
        nasdaq_client,
        cik_service,
        earnings_repository
    )
    
    return cik_service, earnings_service


async def update_company_data(cik_service: CIKService) -> None:
    """
    Update company CIK data from SEC.
    
    Args:
        cik_service: CIK service instance
    """
    try:
        new_symbols = await cik_service.update_company_list()
        if new_symbols:
            logger.info(f"Added {len(new_symbols)} new companies: {', '.join(new_symbols)}")
        else:
            logger.info("No new companies found")
    except Exception as e:
        logger.error(f"Failed to update company data: {str(e)}", exc_info=True)
        raise


async def update_earnings_data(
    earnings_service: EarningsService,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    days_back: int = 30
) -> None:
    """
    Update earnings data for specified date range.
    
    Args:
        earnings_service: Earnings service instance
        start_date: Optional start date
        end_date: Optional end date
        days_back: Days to look back if no start date
    """
    # Determine date range
    end_date = end_date or datetime.now()
    start_date = start_date or (end_date - timedelta(days=days_back))
    
    try:
        results = await earnings_service.update_earnings_data(start_date, end_date)
        
        # Log results
        total_reports = sum(results.values())
        processed_dates = len(results)
        logger.info(
            f"Processed {total_reports} earnings reports "
            f"across {processed_dates} dates"
        )
        
        # Log dates with no data
        no_data_dates = [
            date.strftime("%Y-%m-%d")
            for date, count in results.items()
            if count == 0
        ]
        if no_data_dates:
            logger.warning(
                f"No data found for dates: {', '.join(no_data_dates)}"
            )
            
    except Exception as e:
        logger.error(f"Failed to update earnings data: {str(e)}", exc_info=True)
        raise


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="SEC Earnings Data Scraper"
    )
    
    parser.add_argument(
        "--start-date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        help="Start date (YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--end-date",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        help="End date (YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--days-back",
        type=int,
        default=30,
        help="Days to look back if no start date (default: 30)"
    )
    
    parser.add_argument(
        "--skip-company-update",
        action="store_true",
        help="Skip updating company data"
    )
    
    return parser.parse_args()


async def main() -> None:
    """Main execution function."""
    args = parse_args()
    
    try:
        # Initialize services
        cik_service, earnings_service = await initialize_services()
        
        # Update company data if not skipped
        if not args.skip_company_update:
            logger.info("Updating company data...")
            await update_company_data(cik_service)
        
        # Update earnings data
        logger.info("Updating earnings data...")
        await update_earnings_data(
            earnings_service,
            args.start_date,
            args.end_date,
            args.days_back
        )
        
        logger.info("Scraping completed successfully")
        
    except Exception as e:
        logger.error(f"Scraper failed: {str(e)}", exc_info=True)
        sys.exit(1)
    

if __name__ == "__main__":
    asyncio.run(main())