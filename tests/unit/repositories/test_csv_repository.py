import pytest
from pathlib import Path
from src.models.company import Company
from src.repositories.csv_repository import CSVRepository


@pytest.fixture
def temp_repository(tmp_path):
    """Create temporary repository for testing."""
    return CSVRepository(
        file_path=tmp_path / "test.csv", model_class=Company, key_field="cik"
    )


@pytest.mark.asyncio
async def test_csv_repository_operations(temp_repository):
    """Test basic repository operations."""
    # Test adding
    company = Company(cik="0000320193", symbol="AAPL", name="Apple Inc.")
    await temp_repository.add(company)

    # Test retrieval
    retrieved = await temp_repository.get("0000320193")
    assert retrieved is not None
    assert retrieved.symbol == "AAPL"

    # Test deletion
    assert await temp_repository.delete("0000320193") == True
    assert await temp_repository.get("0000320193") is None
