"""Validation mixin for BaseRepository."""
from __future__ import annotations

import logging
from typing import Any, Generic, TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)


class ValidationMixin(Generic[T]):
    def _validate_business_rules_create(self, data: dict[str, Any]) -> None:
        """
        Validate business rules before creating an entity.

        Subclasses should override this method to implement specific business rule validation.
        This is called before _validate_create_data to enforce domain-specific rules.

        Args:
            data: Dictionary containing entity data

        Raises:
            ValidationError: If business rule validation fails
        """
        # Default implementation: no additional validation
        # Subclasses should override with specific business rules
        pass

    def _validate_business_rules_update(self, data: dict[str, Any]) -> None:
        """
        Validate business rules before updating an entity.

        Subclasses should override this method to implement specific business rule validation.
        This is called before _validate_update_data to enforce domain-specific rules.

        Args:
            data: Dictionary containing fields to update

        Raises:
            ValidationError: If business rule validation fails
        """
        # Default implementation: no additional validation
        # Subclasses should override with specific business rules
        pass

    def _validate_create_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before creating an entity.

        Subclasses should override this method to implement specific validation logic.

        Args:
            data: Dictionary containing entity data

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        # Default implementation: return data as-is
        # Subclasses should override with specific validation
        return data

    def _validate_update_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before updating an entity.

        Subclasses should override this method to implement specific validation logic.

        Args:
            data: Dictionary containing fields to update

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        # Default implementation: return data as-is
        # Subclasses should override with specific validation
        return data

    def _map_to_entity(self, row: dict[str, Any]) -> T:
        """
        Map a database row to an entity object.

        Subclasses must override this method to implement specific mapping logic.

        Args:
            row: Dictionary containing database row data

        Returns:
            Entity object
        """
        # Default implementation: return row as-is (dict)
        # Subclasses should override to return proper entity objects
        return row  # type: ignore
