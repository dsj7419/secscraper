"""
Base repository pattern implementation with type safety and error handling.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel

from src.utils.logging_utils import setup_logger

logger = setup_logger(__name__)

# Generic type for models
T = TypeVar("T", bound=BaseModel)


class Repository(ABC, Generic[T]):
    """
    Abstract base repository defining interface for data storage operations.

    Generic type T must be a Pydantic model.
    """

    def __init__(self) -> None:
        self._logger = logger

    @abstractmethod
    async def add(self, entity: T) -> T:
        """
        Add a new entity.

        Args:
            entity: Entity to add

        Returns:
            T: Added entity

        Raises:
            StorageError: If operation fails
        """
        pass

    @abstractmethod
    async def add_many(self, entities: List[T]) -> List[T]:
        """
        Add multiple entities.

        Args:
            entities: List of entities to add

        Returns:
            List[T]: Added entities

        Raises:
            StorageError: If operation fails
        """
        pass

    @abstractmethod
    async def get(self, id_: Any) -> Optional[T]:
        """
        Get entity by ID.

        Args:
            id_: Entity identifier

        Returns:
            Optional[T]: Found entity or None

        Raises:
            StorageError: If operation fails
        """
        pass

    @abstractmethod
    async def get_all(self) -> List[T]:
        """
        Get all entities.

        Returns:
            List[T]: All entities

        Raises:
            StorageError: If operation fails
        """
        pass

    @abstractmethod
    async def update(self, entity: T) -> Optional[T]:
        """
        Update an existing entity.

        Args:
            entity: Entity to update

        Returns:
            Optional[T]: Updated entity or None if not found

        Raises:
            StorageError: If operation fails
        """
        pass

    @abstractmethod
    async def delete(self, id_: Any) -> bool:
        """
        Delete an entity.

        Args:
            id_: Entity identifier

        Returns:
            bool: True if deleted, False if not found

        Raises:
            StorageError: If operation fails
        """
        pass

    @abstractmethod
    async def exists(self, id_: Any) -> bool:
        """
        Check if entity exists.

        Args:
            id_: Entity identifier

        Returns:
            bool: True if exists

        Raises:
            StorageError: If operation fails
        """
        pass


class TimeRangeRepository(Repository[T], ABC):
    """Repository with time-range query capabilities."""

    @abstractmethod
    async def get_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[T]:
        """
        Get entities within a date range.

        Args:
            start_date: Range start
            end_date: Range end

        Returns:
            List[T]: Entities in range

        Raises:
            StorageError: If operation fails
        """
        pass


class SearchableRepository(Repository[T], ABC):
    """Repository with search capabilities."""

    @abstractmethod
    async def search(
        self, query: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[T]:
        """
        Search entities.

        Args:
            query: Search query
            limit: Maximum results
            offset: Results offset

        Returns:
            List[T]: Matching entities

        Raises:
            StorageError: If operation fails
        """
        pass
