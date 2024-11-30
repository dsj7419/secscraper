"""
Maintenance script for the SEC earnings scraper database.
"""
import asyncio
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Set, List

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.clients.sec_client import SECClient
from src.clients.nasdaq_client import NASDAQClient
from src.services.cik_service import CIKService
from src.services.earnings_service import EarningsService
from src.repositories.csv_repository import CSVRepository
from src.repositories.earnings_repository import EarningsRepository
from src.models.company import Company
from src.utils.logging_utils import setup_logger
from config.settings import get_settings

settings = get_settings()
logger = setup_logger(__name__)


async def validate_data_integrity(
    cik_service: CIKService,
    earnings_service: EarningsService
) -> List[str]:
    """
    Validate data integrity across the database.
    
    Args:
        cik_service: CIK service instance
        earnings_service: Earnings service instance
        
    Returns:
        List[str]: List of integrity issues found
    """
    issues = []
    
    try:
        # Check company data
        companies = await cik_service.get_active_companies()
        if not companies:
            issues.append("No active companies found in database")
        
        # Validate CIK formats
        invalid_ciks = [
            company.symbol for company in companies
            if not company.cik.isdigit() or len(company.cik) != 10
        ]
        if invalid_ciks:
            issues.append(
                f"Invalid CIK format for symbols: {', '.join(invalid_ciks)}"
            )
        
        # Check for duplicate symbols
        symbols = [company.symbol for company in companies]
        if len(symbols) != len(set(symbols)):
            issues.append("Duplicate symbols found in company database")
        
        # Check earnings data
        latest_date = await earnings_service.repository.get_latest_report_date()
        if not latest_date:
            issues.append("No earnings data found")
        elif latest_date < datetime.now() - timedelta(days=7):
            issues.append(f"Earnings data may be stale. Latest date: {latest_date.date()}")
        
        return issues
        
    except Exception as e:
        logger.error(f"Data validation failed: {str(e)}", exc_info=True)
        issues.append(f"Validation error: {str(e)}")
        return issues


async def clean_duplicate_data(
    earnings_service: EarningsService
) -> int:
    """
    Remove duplicate earnings reports.
    
    Args:
        earnings_service: Earnings service instance
        
    Returns:
        int: Number of duplicates removed
    """
    try:
        repository = earnings_service.repository
        all_reports = await repository.get_all()
        
        # Track unique reports by composite key
        seen_reports = set()
        duplicates = []
        
        for report in all_reports:
            key = (report.symbol, report.report_date)
            if key in seen_reports:
                duplicates.append(report)
            else:
                seen_reports.add(key)
        
        # Remove duplicates
        for report in duplicates:
            await repository.delete(report.symbol)
        
        return len(duplicates)
        
    except Exception as e:
        logger.error(f"Failed to clean duplicate data: {str(e)}", exc_info=True)
        raise


async def rebuild_daily_files(
    earnings_service: EarningsService
) -> int:
    """
    Rebuild daily earnings files from master data.
    
    Args:
        earnings_service: Earnings service instance
        
    Returns:
        int: Number of files rebuilt
    """
    try:
        repository = earnings_service.repository
        all_reports = await repository.get_all()
        
        # Group reports by date
        reports_by_date = {}
        for report in all_reports:
            date = report.report_date.date()
            if date not in reports_by_date:
                reports_by_date[date] = []
            reports_by_date[date].append(report)
        
        # Rebuild daily files
        for date, reports in reports_by_date.items():
            date_datetime = datetime.combine(date, datetime.min.time())
            for report in reports:
                await repository.add_daily_report(date_datetime, report)
        
        return len(reports_by_date)
        
    except Exception as e:
        logger.error(f"Failed to rebuild daily files: {str(e)}", exc_info=True)
        raise


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="SEC Earnings Database Maintenance"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate data integrity"
    )
    
    parser.add_argument(
        "--clean-duplicates",
        action="store_true",
        help="Remove duplicate entries"
    )
    
    parser.add_argument(
        "--rebuild-daily",
        action="store_true",
        help="Rebuild daily earnings files"
    )
    
    return parser.parse_args()


async def main() -> None:
    """Main execution function."""
    args = parse_args()
    
    try:
        # Initialize services
        sec_client = SECClient()
        nasdaq_client = NASDAQClient()
        
        company_repository = CSVRepository(
            file_path=settings.PROCESSED_DATA_DIR / "companies" / "companies.csv",
            model_class=Company,
            key_field="cik"
        )
        
        earnings_repository = EarningsRepository()
        
        cik_service = CIKService(sec_client, company_repository)
        earnings_service = EarningsService(
            nasdaq_client,
            cik_service,
            earnings_repository
        )
        
        # Run requested maintenance tasks
        if args.validate:
            logger.info("Validating data integrity...")
            issues = await validate_data_integrity(cik_service, earnings_service)
            if issues:
                logger.warning("Found data integrity issues:")
                for issue in issues:
                    logger.warning(f"- {issue}")
            else:
                logger.info("No data integrity issues found")
        
        if args.clean_duplicates:
            logger.info("Removing duplicate entries...")
            removed = await clean_duplicate_data(earnings_service)
            logger.info(f"Removed {removed} duplicate entries")
        
        if args.rebuild_daily:
            logger.info("Rebuilding daily earnings files...")
            rebuilt = await rebuild_daily_files(earnings_service)
            logger.info(f"Rebuilt {rebuilt} daily files")
        
        logger.info("Maintenance completed successfully")
        
    except Exception as e:
        logger.error(f"Maintenance failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())