"""
Base Repository Interface and Implementation

This module provides generic repository interfaces and base classes for data access.
The repository pattern abstracts database operations and provides a clean interface
for services to interact with data without coupling to specific database implementations.

Validates: Requirements 3.1, 3.2, 3.4
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from uuid import UUID

from app.core.logger import get_logger

logger = get_logger(__name__)

# Generic type variable for entity models
T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """
    Generic repository interface defining CRUD operations.

    This interface establishes the contract that all repositories must implement,
    ensuring consistent data access patterns across the application.

    Type parameter T represents the entity type (e.g., User, Article, Feed).

    Validates: Requirements 3.1, 3.2
    """

    @abstractmethod
    async def create(self, data: dict[str, Any]) -> T:
        """
        Create a new entity.

        Args:
            data: Dictionary containing entity data

        Returns:
            Created entity

        Raises:
            ValidationError: If data validation fails
            DatabaseError: If database operation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> T | None:
        """
        Retrieve an entity by its ID.

        Args:
            entity_id: UUID of the entity

        Returns:
            Entity if found, None otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        pass

    @abstractmethod
    async def get_by_field(self, field: str, value: Any) -> T | None:
        """
        Retrieve an entity by a specific field value.

        Args:
            field: Field name to search by
            value: Value to match

        Returns:
            Entity if found, None otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        pass

    @abstractmethod
    async def list(
        self,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
        ascending: bool = True,
    ) -> list[T]:
        """
        List entities with optional filtering, pagination, and sorting.

        Args:
            filters: Dictionary of field-value pairs to filter by
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            order_by: Field name to sort by
            ascending: Sort direction (True for ascending, False for descending)

        Returns:
            List of entities matching the criteria

        Raises:
            DatabaseError: If database operation fails
        """
        pass

    @abstractmethod
    async def update(self, entity_id: UUID, data: dict[str, Any]) -> T:
        """
        Update an existing entity.

        Args:
            entity_id: UUID of the entity to update
            data: Dictionary containing fields to update

        Returns:
            Updated entity

        Raises:
            NotFoundError: If entity not found
            ValidationError: If data validation fails
            DatabaseError: If database operation fails
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """
        Delete an entity by its ID.

        Args:
            entity_id: UUID of the entity to delete

        Returns:
            True if deleted successfully, False if not found

        Raises:
            DatabaseError: If database operation fails
        """
        pass

    @abstractmethod
    async def exists(self, entity_id: UUID) -> bool:
        """
        Check if an entity exists by its ID.

        Args:
            entity_id: UUID of the entity

        Returns:
            True if entity exists, False otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        pass

    @abstractmethod
    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """
        Count entities matching the given filters.

        Args:
            filters: Dictionary of field-value pairs to filter by

        Returns:
            Count of matching entities

        Raises:
            DatabaseError: If database operation fails
        """
        pass
