"""
Company-related domain models.
"""
from enum import Enum
from typing import Optional
from pydantic import Field, field_validator
from src.models.base import AuditableModel


class Exchange(str, Enum):
    """Stock exchange enumeration."""
    
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    AMEX = "AMEX"
    OTC = "OTC"
    OTHER = "OTHER"


class CompanyStatus(str, Enum):
    """Company status enumeration."""
    
    ACTIVE = "ACTIVE"
    DELISTED = "DELISTED"
    SUSPENDED = "SUSPENDED"
    ACQUIRED = "ACQUIRED"
    BANKRUPT = "BANKRUPT"


class Company(AuditableModel):
    """Company information model."""
    
    cik: str = Field(
        ...,  # Required field
        description="SEC Central Index Key",
        min_length=10,
        max_length=10,
        pattern="^[0-9]{10}$"
    )
    
    symbol: str = Field(
        ...,
        description="Stock ticker symbol",
        min_length=1,
        max_length=10
    )
    
    name: str = Field(
        ...,
        description="Company legal name",
        min_length=1,
        max_length=200
    )
    
    exchange: Exchange = Field(
        default=Exchange.OTHER,
        description="Stock exchange where company is listed"
    )
    
    status: CompanyStatus = Field(
        default=CompanyStatus.ACTIVE,
        description="Current company status"
    )
    
    description: Optional[str] = Field(
        default=None,
        description="Company business description"
    )
    
    sector: Optional[str] = Field(
        default=None,
        description="Company sector classification"
    )
    
    industry: Optional[str] = Field(
        default=None,
        description="Company industry classification"
    )
    
    website: Optional[str] = Field(
        default=None,
        description="Company website URL"
    )
    
    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """
        Normalize stock symbol format.
        
        Args:
            v: Symbol to normalize
            
        Returns:
            str: Normalized symbol
        """
        return v.upper().replace("-", ".")
    
    @field_validator("cik")
    @classmethod
    def validate_cik(cls, v: str) -> str:
        """
        Validate and format CIK.
        
        Args:
            v: CIK to validate
            
        Returns:
            str: Formatted CIK
            
        Raises:
            ValueError: If CIK format is invalid
        """
        if not v.isdigit() or len(v) != 10:
            raise ValueError("CIK must be 10 digits")
        return v
    
    class Config:
        """Pydantic model configuration."""
        
        json_schema_extra = {
            "example": {
                "cik": "0000320193",
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "exchange": "NASDAQ",
                "status": "ACTIVE",
                "sector": "Technology",
                "industry": "Consumer Electronics"
            }
        }