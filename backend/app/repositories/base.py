"""
Base Repository Interface and Implementation

This module provides generic repository interfaces and base classes for data access.
The repository pattern abstracts database operations and provides a clean interface
for services to interact with data without coupling to specific database implementations.

Validates: Requirements 3.1, 3.2, 3.4
"""

from datetime import datetime
from typing import Any, TypeVar
from uuid import UUID

from supabase import Client

from app.core.errors import DatabaseError, ErrorCode, NotFoundError, ValidationError
from app.core.logger import get_logger

logger = get_logger(__name__)

# Generic type variable for entity models
T = TypeVar("T")


from app.repositories._error_mixin import RepositoryErrorMixin
from app.repositories._restore_mixin import RestoreMixin
from app.repositories._validation_mixin import ValidationMixin
from app.repositories.interface import IRepository


class BaseRepository(RestoreMixin[T], ValidationMixin, RepositoryErrorMixin, IRepository[T]):
    """
    Base repository implementation with common query patterns.

    This class provides a concrete implementation of the IRepository interface
    using Supabase as the database client. It includes common patterns like
    error handling, logging, and query building.

    Subclasses should override the table_name property and can extend or
    override methods as needed for specific entity requirements.

    Validates: Requirements 3.1, 3.2, 3.4
    """

    def __init__(
        self,
        client: Client,
        table_name: str,
        enable_audit_trail: bool = True,
        enable_soft_delete: bool = True,
    ):
        """
        Initialize the base repository.

        Args:
            client: Supabase client instance
            table_name: Name of the database table
            enable_audit_trail: Whether to automatically track audit trail fields
            enable_soft_delete: Whether to use soft delete (set deleted_at) instead of hard delete
        """
        self.client = client
        self.table_name = table_name
        self.enable_audit_trail = enable_audit_trail
        self.enable_soft_delete = enable_soft_delete
        self._current_user_id: str | None = None
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def set_current_user(self, user_id: str | None) -> None:
        """
        Set the current user for audit trail tracking.

        This should be called at the start of each request to track which user
        is making modifications. The user_id should be the Discord ID.

        Args:
            user_id: Discord ID of the current user, or None for system operations
        """
        self._current_user_id = user_id

    def get_current_user(self) -> str | None:
        """
        Get the current user for audit trail tracking.

        Returns:
            Discord ID of the current user, or None if not set
        """
        return self._current_user_id

    def _apply_soft_delete_filter(self, query):
        """
        Apply soft delete filter to exclude deleted records from query.

        This method adds a filter to exclude records where deleted_at is not NULL.
        Only applies if soft delete is enabled for this repository.

        Args:
            query: Supabase query builder instance

        Returns:
            Query with soft delete filter applied
        """
        if self.enable_soft_delete:
            query = query.is_("deleted_at", "null")
        return query

    def _add_audit_fields(self, data: dict[str, Any], is_create: bool = False) -> dict[str, Any]:
        """
        Add audit trail fields to data before database operation.

        Args:
            data: Dictionary containing entity data
            is_create: Whether this is a create operation (adds created_at)

        Returns:
            Data with audit trail fields added
        """
        if not self.enable_audit_trail:
            return data

        audit_data = data.copy()

        # Add modified_by if current user is set
        if self._current_user_id is not None:
            audit_data["modified_by"] = self._current_user_id

        # Note: created_at and updated_at are handled by database defaults and triggers
        # We don't need to set them explicitly unless overriding

        return audit_data

    async def create(self, data: dict[str, Any]) -> T:
        """
        Create a new entity in the database.

        Args:
            data: Dictionary containing entity data

        Returns:
            Created entity

        Raises:
            ValidationError: If data validation fails
            DatabaseError: If database operation fails
        """
        self.logger.info(
            f"Creating {self.table_name} entity", operation="create", table=self.table_name
        )

        try:
            # Apply business rule validation first
            self._validate_business_rules_create(data)

            # Validate data before insertion
            validated_data = self._validate_create_data(data)

            # Add audit trail fields
            validated_data = self._add_audit_fields(validated_data, is_create=True)

            # Insert into database
            response = self.client.table(self.table_name).insert(validated_data).execute()

            if not response.data or len(response.data) == 0:
                raise DatabaseError(
                    f"Failed to create {self.table_name}: No data returned",
                    error_code=ErrorCode.DB_QUERY_FAILED,
                    details={"table": self.table_name, "data": data},
                )

            entity = self._map_to_entity(response.data[0])

            self.logger.info(
                f"Successfully created {self.table_name} entity",
                operation="create",
                table=self.table_name,
                entity_id=str(response.data[0].get("id")),
            )

            return entity

        except ValidationError:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            self.logger.error(
                f"Failed to create {self.table_name} entity",
                exc_info=True,
                operation="create",
                table=self.table_name,
                error=str(e),
            )
            self._handle_database_error(e, {"operation": "create", "data": data})

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
        self.logger.debug(
            f"Fetching {self.table_name} by ID",
            operation="get_by_id",
            table=self.table_name,
            entity_id=str(entity_id),
        )

        try:
            query = self.client.table(self.table_name).select("*").eq("id", str(entity_id))
            query = self._apply_soft_delete_filter(query)
            response = query.execute()

            if not response.data or len(response.data) == 0:
                self.logger.debug(
                    f"{self.table_name} not found",
                    operation="get_by_id",
                    table=self.table_name,
                    entity_id=str(entity_id),
                )
                return None

            entity = self._map_to_entity(response.data[0])

            self.logger.debug(
                f"Successfully fetched {self.table_name}",
                operation="get_by_id",
                table=self.table_name,
                entity_id=str(entity_id),
            )

            return entity

        except Exception as e:
            self.logger.error(
                f"Failed to fetch {self.table_name} by ID",
                exc_info=True,
                operation="get_by_id",
                table=self.table_name,
                entity_id=str(entity_id),
                error=str(e),
            )
            self._handle_database_error(e, {"operation": "get_by_id", "entity_id": str(entity_id)})

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
        self.logger.debug(
            f"Fetching {self.table_name} by field",
            operation="get_by_field",
            table=self.table_name,
            field=field,
            value=str(value),
        )

        try:
            query = self.client.table(self.table_name).select("*").eq(field, value).limit(1)
            query = self._apply_soft_delete_filter(query)
            response = query.execute()

            if not response.data or len(response.data) == 0:
                self.logger.debug(
                    f"{self.table_name} not found by field",
                    operation="get_by_field",
                    table=self.table_name,
                    field=field,
                )
                return None

            entity = self._map_to_entity(response.data[0])

            self.logger.debug(
                f"Successfully fetched {self.table_name} by field",
                operation="get_by_field",
                table=self.table_name,
                field=field,
            )

            return entity

        except Exception as e:
            self.logger.error(
                f"Failed to fetch {self.table_name} by field",
                exc_info=True,
                operation="get_by_field",
                table=self.table_name,
                field=field,
                error=str(e),
            )
            self._handle_database_error(
                e, {"operation": "get_by_field", "field": field, "value": str(value)}
            )

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
        self.logger.debug(
            f"Listing {self.table_name} entities",
            operation="list",
            table=self.table_name,
            filters=filters,
            limit=limit,
            offset=offset,
        )

        try:
            # Build query
            query = self.client.table(self.table_name).select("*")

            # Apply soft delete filter first
            query = self._apply_soft_delete_filter(query)

            # Apply filters
            if filters:
                for field, value in filters.items():
                    query = query.eq(field, value)

            # Apply ordering
            if order_by:
                query = query.order(order_by, desc=not ascending)

            # Apply pagination
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)

            response = query.execute()

            entities = [self._map_to_entity(row) for row in response.data]

            self.logger.debug(
                f"Successfully listed {len(entities)} {self.table_name} entities",
                operation="list",
                table=self.table_name,
                count=len(entities),
            )

            return entities

        except Exception as e:
            self.logger.error(
                f"Failed to list {self.table_name} entities",
                exc_info=True,
                operation="list",
                table=self.table_name,
                error=str(e),
            )
            self._handle_database_error(e, {"operation": "list", "filters": filters})

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
        self.logger.info(
            f"Updating {self.table_name} entity",
            operation="update",
            table=self.table_name,
            entity_id=str(entity_id),
        )

        try:
            # Apply business rule validation first
            self._validate_business_rules_update(data)

            # Validate data before update
            validated_data = self._validate_update_data(data)

            # Add audit trail fields
            validated_data = self._add_audit_fields(validated_data, is_create=False)

            # Update in database
            response = (
                self.client.table(self.table_name)
                .update(validated_data)
                .eq("id", str(entity_id))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                raise NotFoundError(
                    f"{self.table_name} not found",
                    error_code=ErrorCode.RESOURCE_NOT_FOUND,
                    details={"table": self.table_name, "entity_id": str(entity_id)},
                )

            entity = self._map_to_entity(response.data[0])

            self.logger.info(
                f"Successfully updated {self.table_name} entity",
                operation="update",
                table=self.table_name,
                entity_id=str(entity_id),
            )

            return entity

        except NotFoundError:
            raise
        except ValidationError:
            raise
        except DatabaseError:
            raise
        except Exception as e:
            self.logger.error(
                f"Failed to update {self.table_name} entity",
                exc_info=True,
                operation="update",
                table=self.table_name,
                entity_id=str(entity_id),
                error=str(e),
            )
            self._handle_database_error(
                e, {"operation": "update", "entity_id": str(entity_id), "data": data}
            )

    async def delete(self, entity_id: UUID) -> bool:
        """
        Delete an entity by its ID.

        If soft delete is enabled, sets deleted_at timestamp instead of removing the record.
        Otherwise, performs a hard delete (permanent removal).

        Args:
            entity_id: UUID of the entity to delete

        Returns:
            True if deleted successfully, False if not found

        Raises:
            DatabaseError: If database operation fails
        """
        self.logger.info(
            f"Deleting {self.table_name} entity",
            operation="delete",
            table=self.table_name,
            entity_id=str(entity_id),
            soft_delete=self.enable_soft_delete,
        )

        try:
            if self.enable_soft_delete:
                # Soft delete: set deleted_at timestamp
                delete_data = {"deleted_at": datetime.utcnow().isoformat()}

                # Add audit trail fields
                delete_data = self._add_audit_fields(delete_data, is_create=False)

                # Check if entity exists and is not already deleted
                query = self.client.table(self.table_name).select("id").eq("id", str(entity_id))
                query = self._apply_soft_delete_filter(query)
                check_response = query.execute()

                if not check_response.data or len(check_response.data) == 0:
                    self.logger.debug(
                        f"{self.table_name} not found or already deleted",
                        operation="delete",
                        table=self.table_name,
                        entity_id=str(entity_id),
                    )
                    return False

                # Update with deleted_at timestamp
                response = (
                    self.client.table(self.table_name)
                    .update(delete_data)
                    .eq("id", str(entity_id))
                    .execute()
                )

                deleted = bool(response.data and len(response.data) > 0)
            else:
                # Hard delete: permanently remove the record
                response = (
                    self.client.table(self.table_name).delete().eq("id", str(entity_id)).execute()
                )

                deleted = bool(response.data and len(response.data) > 0)

            if deleted:
                self.logger.info(
                    f"Successfully deleted {self.table_name} entity",
                    operation="delete",
                    table=self.table_name,
                    entity_id=str(entity_id),
                    soft_delete=self.enable_soft_delete,
                )
            else:
                self.logger.debug(
                    f"{self.table_name} not found for deletion",
                    operation="delete",
                    table=self.table_name,
                    entity_id=str(entity_id),
                )

            return deleted

        except Exception as e:
            self.logger.error(
                f"Failed to delete {self.table_name} entity",
                exc_info=True,
                operation="delete",
                table=self.table_name,
                entity_id=str(entity_id),
                error=str(e),
            )
            self._handle_database_error(e, {"operation": "delete", "entity_id": str(entity_id)})

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
        self.logger.debug(
            f"Checking if {self.table_name} exists",
            operation="exists",
            table=self.table_name,
            entity_id=str(entity_id),
        )

        try:
            query = (
                self.client.table(self.table_name).select("id").eq("id", str(entity_id)).limit(1)
            )
            query = self._apply_soft_delete_filter(query)
            response = query.execute()

            exists = bool(response.data and len(response.data) > 0)

            self.logger.debug(
                f"{self.table_name} exists: {exists}",
                operation="exists",
                table=self.table_name,
                entity_id=str(entity_id),
                exists=exists,
            )

            return exists

        except Exception as e:
            self.logger.error(
                f"Failed to check if {self.table_name} exists",
                exc_info=True,
                operation="exists",
                table=self.table_name,
                entity_id=str(entity_id),
                error=str(e),
            )
            self._handle_database_error(e, {"operation": "exists", "entity_id": str(entity_id)})

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
        self.logger.debug(
            f"Counting {self.table_name} entities",
            operation="count",
            table=self.table_name,
            filters=filters,
        )

        try:
            # Build query
            query = self.client.table(self.table_name).select("id", count="exact")

            # Apply soft delete filter first
            query = self._apply_soft_delete_filter(query)

            # Apply filters
            if filters:
                for field, value in filters.items():
                    query = query.eq(field, value)

            response = query.execute()

            count = response.count if hasattr(response, "count") else 0

            self.logger.debug(
                f"Successfully counted {count} {self.table_name} entities",
                operation="count",
                table=self.table_name,
                count=count,
            )

            return count

        except Exception as e:
            self.logger.error(
                f"Failed to count {self.table_name} entities",
                exc_info=True,
                operation="count",
                table=self.table_name,
                error=str(e),
            )
            self._handle_database_error(e, {"operation": "count", "filters": filters})
