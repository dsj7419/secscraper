"""
Base models with common functionality for all domain models.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BaseModelWithTimestamp(BaseModel):
    """Base model with timestamp tracking."""
    
    model_config = ConfigDict(
        frozen=True,  # Immutable objects
        validate_assignment=True,  # Validate on attribute assignment
        arbitrary_types_allowed=True,  # Allow custom types
        json_encoders={  # Custom JSON encoders
            datetime: lambda v: v.isoformat()
        }
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        object.__setattr__(self, "updated_at", datetime.utcnow())
        

class AuditableModel(BaseModelWithTimestamp):
    """Model with audit trail capabilities."""
    
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    version: int = 1
    
    def update_audit_trail(self, user: Optional[str] = None) -> None:
        """
        Update audit trail information.
        
        Args:
            user: User making the change
        """
        self.update_timestamp()
        if user:
            object.__setattr__(self, "updated_by", user)
        object.__setattr__(self, "version", self.version + 1)