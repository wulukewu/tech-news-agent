"""
Analytics Event Repository

Concrete repository implementation for AnalyticsEvent entities.
Handles all database operations related to analytics events tracking.

Validates: Requirements 3.2, 3.4, 14.2, 14.3
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from supabase import Client

from app.core.errors import ErrorCode, ValidationError
from app.repositories.base import BaseRepository


class AnalyticsEvent:
    """AnalyticsEvent entity model."""

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        event_type: str,
        event_data: dict[str, Any],
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        modified_by: Optional[str] = None,
        deleted_at: Optional[datetime] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.event_type = event_type
        self.event_data = event_data or {}
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at
        self.modified_by = modified_by
        self.deleted_at = deleted_at

    def __eq__(self, other):
        if not isinstance(other, AnalyticsEvent):
            return False
        return self.id == other.id

    def __repr__(self):
        return f"AnalyticsEvent(id={self.id}, user_id={self.user_id}, event_type={self.event_type})"


class AnalyticsEventRepository(BaseRepository[AnalyticsEvent]):
    """
    Repository for AnalyticsEvent entities.

    Provides data access methods for analytics event operations including
    CRUD operations and event-specific queries.

    Validates: Requirements 3.2, 3.4
    """

    def __init__(self, client: Client):
        """
        Initialize the analytics event repository.

        Args:
            client: Supabase client instance
        """
        super().__init__(
            client, "analytics_events", enable_audit_trail=True, enable_soft_delete=False
        )

    def _map_to_entity(self, row: dict[str, Any]) -> AnalyticsEvent:
        """
        Map a database row to an AnalyticsEvent entity.

        Args:
            row: Dictionary containing database row data

        Returns:
            AnalyticsEvent entity object
        """
        return AnalyticsEvent(
            id=UUID(row["id"]) if isinstance(row["id"], str) else row["id"],
            user_id=UUID(row["user_id"]) if isinstance(row["user_id"], str) else row["user_id"],
            event_type=row["event_type"],
            event_data=row.get("event_data", {}),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            modified_by=row.get("modified_by"),
            deleted_at=row.get("deleted_at"),
        )

    def _validate_create_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before creating an analytics event.

        Args:
            data: Dictionary containing analytics event data

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields
        required_fields = ["user_id", "event_type"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(
                    f"Missing required field: {field}",
                    error_code=ErrorCode.VALIDATION_MISSING_FIELD,
                    details={"field": field},
                )

        # Validate event_type
        event_type = data["event_type"]
        if not isinstance(event_type, str) or not event_type.strip():
            raise ValidationError(
                "Invalid event_type: must be a non-empty string",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "event_type", "value": event_type},
            )

        # Build validated data
        validated_data = {
            "user_id": str(data["user_id"]),
            "event_type": event_type.strip(),
            "event_data": data.get("event_data", {}),
        }

        # Add created_at if provided
        if "created_at" in data:
            validated_data["created_at"] = data["created_at"]

        return validated_data

    def _validate_update_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before updating an analytics event.

        Args:
            data: Dictionary containing fields to update

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        # Analytics events are typically immutable
        # Only audit fields can be updated
        return {}

    async def list_by_user(
        self,
        user_id: UUID,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[AnalyticsEvent]:
        """
        List analytics events for a user with optional filters.

        Args:
            user_id: UUID of the user
            event_type: Optional event type filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of events to return
            offset: Number of events to skip

        Returns:
            List of AnalyticsEvent entities

        Raises:
            DatabaseError: If database operation fails
        """
        self.logger.debug(
            "Listing analytics events for user",
            operation="list_by_user",
            table=self.table_name,
            user_id=str(user_id),
            event_type=event_type,
        )

        try:
            # Build query
            query = self.client.table(self.table_name).select("*")

            # Apply filters
            query = query.eq("user_id", str(user_id))

            if event_type:
                query = query.eq("event_type", event_type)

            if start_date:
                query = query.gte("created_at", start_date.isoformat())

            if end_date:
                query = query.lte("created_at", end_date.isoformat())

            # Apply ordering
            query = query.order("created_at", desc=True)

            # Apply pagination
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)

            response = query.execute()

            events = [self._map_to_entity(row) for row in response.data]

            self.logger.debug(
                f"Successfully listed {len(events)} analytics events",
                operation="list_by_user",
                table=self.table_name,
                count=len(events),
            )

            return events

        except Exception as e:
            self.logger.error(
                "Failed to list analytics events",
                exc_info=True,
                operation="list_by_user",
                table=self.table_name,
                user_id=str(user_id),
                error=str(e),
            )
            self._handle_database_error(
                e, {"operation": "list_by_user", "user_id": str(user_id), "event_type": event_type}
            )

    async def list_by_event_type(
        self,
        event_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[AnalyticsEvent]:
        """
        List analytics events by event type with optional date filters.

        Args:
            event_type: Event type to filter by
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of events to return
            offset: Number of events to skip

        Returns:
            List of AnalyticsEvent entities

        Raises:
            DatabaseError: If database operation fails
        """
        self.logger.debug(
            "Listing analytics events by type",
            operation="list_by_event_type",
            table=self.table_name,
            event_type=event_type,
        )

        try:
            # Build query
            query = self.client.table(self.table_name).select("*")

            # Apply filters
            query = query.eq("event_type", event_type)

            if start_date:
                query = query.gte("created_at", start_date.isoformat())

            if end_date:
                query = query.lte("created_at", end_date.isoformat())

            # Apply ordering
            query = query.order("created_at", desc=True)

            # Apply pagination
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)

            response = query.execute()

            events = [self._map_to_entity(row) for row in response.data]

            self.logger.debug(
                f"Successfully listed {len(events)} analytics events",
                operation="list_by_event_type",
                table=self.table_name,
                count=len(events),
            )

            return events

        except Exception as e:
            self.logger.error(
                "Failed to list analytics events by type",
                exc_info=True,
                operation="list_by_event_type",
                table=self.table_name,
                event_type=event_type,
                error=str(e),
            )
            self._handle_database_error(
                e, {"operation": "list_by_event_type", "event_type": event_type}
            )

    async def count_by_event_type(
        self,
        event_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Count analytics events by event type with optional date filters.

        Args:
            event_type: Event type to filter by
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Count of matching events

        Raises:
            DatabaseError: If database operation fails
        """
        self.logger.debug(
            "Counting analytics events by type",
            operation="count_by_event_type",
            table=self.table_name,
            event_type=event_type,
        )

        try:
            # Build query
            query = self.client.table(self.table_name).select("id", count="exact")

            # Apply filters
            query = query.eq("event_type", event_type)

            if start_date:
                query = query.gte("created_at", start_date.isoformat())

            if end_date:
                query = query.lte("created_at", end_date.isoformat())

            response = query.execute()

            count = response.count if hasattr(response, "count") else 0

            self.logger.debug(
                f"Successfully counted {count} analytics events",
                operation="count_by_event_type",
                table=self.table_name,
                count=count,
            )

            return count

        except Exception as e:
            self.logger.error(
                "Failed to count analytics events by type",
                exc_info=True,
                operation="count_by_event_type",
                table=self.table_name,
                event_type=event_type,
                error=str(e),
            )
            self._handle_database_error(
                e, {"operation": "count_by_event_type", "event_type": event_type}
            )
