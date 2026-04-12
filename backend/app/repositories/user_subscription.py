"""
User Subscription Repository

Concrete repository implementation for UserSubscription entities.
Handles all database operations related to user feed subscriptions.

Validates: Requirements 3.2, 3.4, 14.2, 14.3
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from supabase import Client

from app.core.errors import ErrorCode, ValidationError
from app.repositories.base import BaseRepository


class UserSubscription:
    """UserSubscription entity model."""

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        feed_id: UUID,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        modified_by: Optional[str] = None,
        deleted_at: Optional[datetime] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.feed_id = feed_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at
        self.modified_by = modified_by
        self.deleted_at = deleted_at

    def __eq__(self, other):
        if not isinstance(other, UserSubscription):
            return False
        return self.id == other.id

    def __repr__(self):
        return f"UserSubscription(id={self.id}, user_id={self.user_id}, feed_id={self.feed_id})"


class UserSubscriptionRepository(BaseRepository[UserSubscription]):
    """
    Repository for UserSubscription entities.

    Provides data access methods for user subscription operations including
    CRUD operations and subscription-specific queries.

    Validates: Requirements 3.2, 3.4
    """

    def __init__(self, client: Client):
        """
        Initialize the user subscription repository.

        Args:
            client: Supabase client instance
        """
        super().__init__(client, "user_subscriptions", enable_audit_trail=True)

    def _map_to_entity(self, row: dict[str, Any]) -> UserSubscription:
        """
        Map a database row to a UserSubscription entity.

        Args:
            row: Dictionary containing database row data

        Returns:
            UserSubscription entity object
        """
        return UserSubscription(
            id=UUID(row["id"]) if isinstance(row["id"], str) else row["id"],
            user_id=UUID(row["user_id"]) if isinstance(row["user_id"], str) else row["user_id"],
            feed_id=UUID(row["feed_id"]) if isinstance(row["feed_id"], str) else row["feed_id"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            modified_by=row.get("modified_by"),
            deleted_at=row.get("deleted_at"),
        )

    def _validate_create_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before creating a user subscription.

        Args:
            data: Dictionary containing user subscription data

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields
        required_fields = ["user_id", "feed_id"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(
                    f"Missing required field: {field}",
                    error_code=ErrorCode.VALIDATION_MISSING_FIELD,
                    details={"field": field},
                )

        # Build validated data
        validated_data = {"user_id": str(data["user_id"]), "feed_id": str(data["feed_id"])}

        return validated_data

    def _validate_update_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before updating a user subscription.

        Args:
            data: Dictionary containing fields to update

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        # User subscriptions typically don't have updatable fields
        # Only audit fields can be updated
        return {}

    async def get_by_user_and_feed(
        self, user_id: UUID, feed_id: UUID
    ) -> Optional[UserSubscription]:
        """
        Retrieve a subscription by user ID and feed ID.

        Args:
            user_id: UUID of the user
            feed_id: UUID of the feed

        Returns:
            UserSubscription if found, None otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        self.logger.debug(
            "Fetching subscription by user and feed",
            operation="get_by_user_and_feed",
            table=self.table_name,
            user_id=str(user_id),
            feed_id=str(feed_id),
        )

        try:
            query = (
                self.client.table(self.table_name)
                .select("*")
                .eq("user_id", str(user_id))
                .eq("feed_id", str(feed_id))
                .limit(1)
            )
            query = self._apply_soft_delete_filter(query)
            response = query.execute()

            if not response.data or len(response.data) == 0:
                return None

            return self._map_to_entity(response.data[0])

        except Exception as e:
            self.logger.error(
                "Failed to fetch subscription by user and feed",
                exc_info=True,
                operation="get_by_user_and_feed",
                table=self.table_name,
                user_id=str(user_id),
                feed_id=str(feed_id),
                error=str(e),
            )
            self._handle_database_error(
                e,
                {
                    "operation": "get_by_user_and_feed",
                    "user_id": str(user_id),
                    "feed_id": str(feed_id),
                },
            )

    async def list_by_user(
        self, user_id: UUID, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> list[UserSubscription]:
        """
        List all subscriptions for a user.

        Args:
            user_id: UUID of the user
            limit: Maximum number of subscriptions to return
            offset: Number of subscriptions to skip

        Returns:
            List of UserSubscription entities

        Raises:
            DatabaseError: If database operation fails
        """
        return await self.list(
            filters={"user_id": str(user_id)},
            limit=limit,
            offset=offset,
            order_by="created_at",
            ascending=False,
        )

    async def list_feed_ids_by_user(self, user_id: UUID) -> list[UUID]:
        """
        Get list of feed IDs that a user is subscribed to.

        Args:
            user_id: UUID of the user

        Returns:
            List of feed UUIDs

        Raises:
            DatabaseError: If database operation fails
        """
        subscriptions = await self.list_by_user(user_id)
        return [sub.feed_id for sub in subscriptions]

    async def exists_by_user_and_feed(self, user_id: UUID, feed_id: UUID) -> bool:
        """
        Check if a subscription exists for a user and feed.

        Args:
            user_id: UUID of the user
            feed_id: UUID of the feed

        Returns:
            True if subscription exists, False otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        subscription = await self.get_by_user_and_feed(user_id, feed_id)
        return subscription is not None

    async def delete_by_user_and_feed(self, user_id: UUID, feed_id: UUID) -> bool:
        """
        Delete a subscription by user ID and feed ID.

        Args:
            user_id: UUID of the user
            feed_id: UUID of the feed

        Returns:
            True if deleted successfully, False if not found

        Raises:
            DatabaseError: If database operation fails
        """
        subscription = await self.get_by_user_and_feed(user_id, feed_id)
        if not subscription:
            return False

        return await self.delete(subscription.id)
