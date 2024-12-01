"""
Test script to verify configuration and basic functionality.
"""

import asyncio
import sys
import os
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

# Set test mode
os.environ["TESTING"] = "true"

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.clients.sec_client import SECClient
from src.clients.nasdaq_client import NASDAQClient
from src.services.cik_service import CIKService
from src.services.earnings_service import EarningsService
from src.repositories.csv_repository import CSVRepository
from src.repositories.earnings_repository import EarningsRepository
from src.models.company import Company, CompanyStatus, Exchange
from src.utils.logging_utils import setup_logger
from config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()


async def test_directory_structure():
    """Test data directory structure creation."""
    logger.info("Testing directory structure...")

    dirs = [
        settings.RAW_DATA_DIR / "sec",
        settings.RAW_DATA_DIR / "nasdaq",
        settings.PROCESSED_DATA_DIR / "companies",
        settings.PROCESSED_DATA_DIR / "earnings" / "daily",
        settings.PROCESSED_DATA_DIR / "earnings" / "master",
        settings.LOG_DIR,
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory verified: {dir_path}")
    return True


async def test_sec_client():
    """Test SEC API client."""
    logger.info("Testing SEC API client...")

    async with SECClient() as client:
        try:
            data = await client.get_company_tickers()
            result_len = len(data) if isinstance(data, dict) else 0
            logger.info(f"Successfully retrieved {result_len} companies from SEC")
            return True
        except Exception as e:
            logger.error(f"SEC API test failed: {str(e)}")
            return False


async def test_nasdaq_client():
    """Test NASDAQ API client."""
    logger.info("Testing NASDAQ API client...")

    async with NASDAQClient() as client:
        try:
            yesterday = datetime.now() - timedelta(days=1)
            data = await client.get_earnings_calendar(yesterday.date())
            if data and data.get("data", {}).get("rows"):
                logger.info("Successfully retrieved NASDAQ earnings data")
                return True
            logger.error("No data in NASDAQ response")
            return False
        except Exception as e:
            logger.error(f"NASDAQ API test failed: {str(e)}")
            return False


async def test_company_repository():
    """Test company repository."""
    logger.info("Testing company repository...")

    file_path = settings.PROCESSED_DATA_DIR / "companies" / "companies.csv"

    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Create fresh repository for test
    if file_path.exists():
        file_path.unlink()

    repository = CSVRepository(
        file_path=file_path, model_class=Company, key_field="cik"
    )

    try:
        # Create test company
        test_company = Company(
            cik="0000320193",
            symbol="AAPL",
            name="Apple Inc.",
            exchange=Exchange.NASDAQ,
            status=CompanyStatus.ACTIVE,
            sector="Technology",
            industry="Consumer Electronics",
        )

        logger.info(f"Created test company: {test_company.model_dump_json()}")

        # Test add
        await repository.add(test_company)
        logger.info("Added company to repository")

        # Debug: Check raw CSV content
        if file_path.exists():
            df = pd.read_csv(file_path)
            logger.info(f"CSV content after add:\n{df.to_string()}")
        else:
            logger.error("CSV file doesn't exist after add!")

        # Test retrieve
        retrieved = await repository.get("0000320193")
        if retrieved:
            logger.info(f"Retrieved company: {retrieved.model_dump_json()}")
        else:
            logger.error("Failed to retrieve company")
            if file_path.exists():
                df = pd.read_csv(file_path)
                logger.error(f"Current CSV content:\n{df.to_string()}")
            return False

        # Verify all fields match
        fields_match = all(
            [
                retrieved.cik == test_company.cik,
                retrieved.symbol == test_company.symbol,
                retrieved.name == test_company.name,
                retrieved.exchange == test_company.exchange,
                retrieved.status == test_company.status,
                retrieved.sector == test_company.sector,
                retrieved.industry == test_company.industry,
            ]
        )

        if fields_match:
            logger.info("Successfully tested company repository")
            return True
        else:
            logger.error("Company repository test failed: Data mismatch")
            logger.error(f"Original: {test_company.model_dump()}")
            logger.error(f"Retrieved: {retrieved.model_dump()}")
            return False

    except Exception as e:
        logger.error(f"Company repository test failed: {str(e)}", exc_info=True)
        return False


async def main():
    """Run all tests."""
    try:
        # Test directory structure
        struct_ok = await test_directory_structure()

        # Test API clients
        sec_ok = await test_sec_client()
        nasdaq_ok = await test_nasdaq_client()

        # Test repository
        repo_ok = await test_company_repository()

        # Report results
        logger.info("\nTest Results:")
        logger.info(f"Directory Structure: {'OK' if struct_ok else 'FAILED'}")
        logger.info(f"SEC API: {'OK' if sec_ok else 'FAILED'}")
        logger.info(f"NASDAQ API: {'OK' if nasdaq_ok else 'FAILED'}")
        logger.info(f"Repository: {'OK' if repo_ok else 'FAILED'}")

        if not all([struct_ok, sec_ok, nasdaq_ok, repo_ok]):
            sys.exit(1)

        logger.info("\nAll tests passed successfully!")

    except Exception as e:
        logger.error(f"Setup test failed: {str(e)}")
        sys.exit(1)
    finally:
        # Ensure we cleanup any pending tasks
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
