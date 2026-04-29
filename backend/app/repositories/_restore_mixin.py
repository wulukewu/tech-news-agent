"""Restore/hard-delete mixin for BaseRepository."""
import logging
from typing import Generic, TypeVar
from uuid import UUID

from app.core.errors import DatabaseError, ErrorCode, NotFoundError, ValidationError

T = TypeVar("T")
logger = logging.getLogger(__name__)


class RestoreMixin(Generic[T]):
    async def restore(self, entity_id: UUID) -> T:
        """
        Restore a soft-deleted entity by clearing its deleted_at timestamp.

        This method only works if soft delete is enabled. It will restore
        a previously soft-deleted entity by setting deleted_at to NULL.

        Args:
            entity_id: UUID of the entity to restore

        Returns:
            Restored entity

        Raises:
            NotFoundError: If entity not found or not deleted
            DatabaseError: If database operation fails
            ValidationError: If soft delete is not enabled
        """
        if not self.enable_soft_delete:
            raise ValidationError(
                "Restore operation requires soft delete to be enabled",
                error_code=ErrorCode.VALIDATION_BUSINESS_RULE,
                details={"table": self.table_name, "operation": "restore"},
            )

        self.logger.info(
            f"Restoring {self.table_name} entity",
            operation="restore",
            table=self.table_name,
            entity_id=str(entity_id),
        )

        try:
            # Check if entity exists and is deleted
            query = self.client.table(self.table_name).select("*").eq("id", str(entity_id))
            # Don't apply soft delete filter - we want to find deleted entities
            check_response = query.execute()

            if not check_response.data or len(check_response.data) == 0:
                raise NotFoundError(
                    f"{self.table_name} not found",
                    error_code=ErrorCode.RESOURCE_NOT_FOUND,
                    details={"table": self.table_name, "entity_id": str(entity_id)},
                )

            entity_data = check_response.data[0]
            if entity_data.get("deleted_at") is None:
                raise ValidationError(
                    f"{self.table_name} is not deleted",
                    error_code=ErrorCode.VALIDATION_BUSINESS_RULE,
                    details={"table": self.table_name, "entity_id": str(entity_id)},
                )

            # Restore by setting deleted_at to NULL
            restore_data = {"deleted_at": None}
            restore_data = self._add_audit_fields(restore_data, is_create=False)

            response = (
                self.client.table(self.table_name)
                .update(restore_data)
                .eq("id", str(entity_id))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                raise DatabaseError(
                    f"Failed to restore {self.table_name}",
                    error_code=ErrorCode.DB_QUERY_FAILED,
                    details={"table": self.table_name, "entity_id": str(entity_id)},
                )

            entity = self._map_to_entity(response.data[0])

            self.logger.info(
                f"Successfully restored {self.table_name} entity",
                operation="restore",
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
                f"Failed to restore {self.table_name} entity",
                exc_info=True,
                operation="restore",
                table=self.table_name,
                entity_id=str(entity_id),
                error=str(e),
            )
            self._handle_database_error(e, {"operation": "restore", "entity_id": str(entity_id)})

    async def hard_delete(self, entity_id: UUID) -> bool:
        """
        Permanently delete an entity from the database.

        This method performs a hard delete (permanent removal) regardless of
        whether soft delete is enabled. Use with caution as this operation
        cannot be undone.

        Args:
            entity_id: UUID of the entity to permanently delete

        Returns:
            True if deleted successfully, False if not found

        Raises:
            DatabaseError: If database operation fails
        """
        self.logger.warning(
            f"Performing hard delete on {self.table_name} entity",
            operation="hard_delete",
            table=self.table_name,
            entity_id=str(entity_id),
        )

        try:
            response = (
                self.client.table(self.table_name).delete().eq("id", str(entity_id)).execute()
            )

            deleted = bool(response.data and len(response.data) > 0)

            if deleted:
                self.logger.warning(
                    f"Successfully hard deleted {self.table_name} entity",
                    operation="hard_delete",
                    table=self.table_name,
                    entity_id=str(entity_id),
                )
            else:
                self.logger.debug(
                    f"{self.table_name} not found for hard deletion",
                    operation="hard_delete",
                    table=self.table_name,
                    entity_id=str(entity_id),
                )

            return deleted

        except Exception as e:
            self.logger.error(
                f"Failed to hard delete {self.table_name} entity",
                exc_info=True,
                operation="hard_delete",
                table=self.table_name,
                entity_id=str(entity_id),
                error=str(e),
            )
            self._handle_database_error(
                e, {"operation": "hard_delete", "entity_id": str(entity_id)}
            )

    # Protected helper methods for subclasses to override
