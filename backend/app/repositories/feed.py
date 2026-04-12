"""
Feed Repository

Concrete repository implementation for Feed entities.
Handles all database operations related to RSS feeds.

Validates: Requirements 3.2, 3.4, 14.2, 14.3
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from supabase import Client

from app.core.errors import ErrorCode, ValidationError
from app.core.validators import FeedValidator
from app.repositories.base import BaseRepository


class Feed:
    """Feed entity model."""

    def __init__(
        self,
        id: UUID,
        name: str,
        url: str,
        category: str,
        is_active: bool = True,
        description: Optional[str] = None,
        is_recommended: bool = False,
        recommendation_priority: int = 0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        modified_by: Optional[str] = None,
        deleted_at: Optional[datetime] = None,
    ):
        self.id = id
        self.name = name
        self.url = url
        self.category = category
        self.is_active = is_active
        self.description = description
        self.is_recommended = is_recommended
        self.recommendation_priority = recommendation_priority
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at
        self.modified_by = modified_by
        self.deleted_at = deleted_at

    def __eq__(self, other):
        if not isinstance(other, Feed):
            return False
        return self.id == other.id

    def __repr__(self):
        return f"Feed(id={self.id}, name={self.name}, category={self.category})"


class FeedRepository(BaseRepository[Feed]):
    """
    Repository for Feed entities.

    Provides data access methods for feed-related operations including
    CRUD operations and feed-specific queries.

    Validates: Requirements 3.2, 3.4
    """

    def __init__(self, client: Client):
        """
        Initialize the feed repository.

        Args:
            client: Supabase client instance
        """
        super().__init__(client, "feeds", enable_audit_trail=True)

    def _validate_business_rules_create(self, data: dict[str, Any]) -> None:
        """
        Validate business rules before creating a feed.

        Args:
            data: Dictionary containing feed data

        Raises:
            ValidationError: If business rule validation fails
        """
        FeedValidator.validate_feed_create(data)

    def _validate_business_rules_update(self, data: dict[str, Any]) -> None:
        """
        Validate business rules before updating a feed.

        Args:
            data: Dictionary containing fields to update

        Raises:
            ValidationError: If business rule validation fails
        """
        FeedValidator.validate_feed_update(data)

    def _map_to_entity(self, row: dict[str, Any]) -> Feed:
        """
        Map a database row to a Feed entity.

        Args:
            row: Dictionary containing database row data

        Returns:
            Feed entity object
        """
        return Feed(
            id=UUID(row["id"]) if isinstance(row["id"], str) else row["id"],
            name=row["name"],
            url=row["url"],
            category=row["category"],
            is_active=row.get("is_active", True),
            description=row.get("description"),
            is_recommended=row.get("is_recommended", False),
            recommendation_priority=row.get("recommendation_priority", 0),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            modified_by=row.get("modified_by"),
            deleted_at=row.get("deleted_at"),
        )

    def _validate_create_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before creating a feed.

        Args:
            data: Dictionary containing feed data

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields
        required_fields = ["name", "url", "category"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(
                    f"Missing required field: {field}",
                    error_code=ErrorCode.VALIDATION_MISSING_FIELD,
                    details={"field": field},
                )

        # Validate name
        name = data["name"]
        if not isinstance(name, str) or not name.strip():
            raise ValidationError(
                "Invalid name: must be a non-empty string",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "name", "value": name},
            )

        # Validate URL
        url = data["url"]
        if not isinstance(url, str) or not url.strip():
            raise ValidationError(
                "Invalid url: must be a non-empty string",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "url", "value": url},
            )

        # Basic URL format validation
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValidationError(
                "Invalid url: must start with http:// or https://",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "url", "value": url},
            )

        # Validate category
        category = data["category"]
        if not isinstance(category, str) or not category.strip():
            raise ValidationError(
                "Invalid category: must be a non-empty string",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "category", "value": category},
            )

        # Build validated data
        validated_data = {
            "name": name.strip(),
            "url": url.strip(),
            "category": category.strip(),
            "is_active": data.get("is_active", True),
        }

        return validated_data

    def _validate_update_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before updating a feed.

        Args:
            data: Dictionary containing fields to update

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        validated_data = {}

        # Validate name if provided
        if "name" in data:
            name = data["name"]
            if not isinstance(name, str) or not name.strip():
                raise ValidationError(
                    "Invalid name: must be a non-empty string",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "name", "value": name},
                )
            validated_data["name"] = name.strip()

        # Validate URL if provided
        if "url" in data:
            url = data["url"]
            if not isinstance(url, str) or not url.strip():
                raise ValidationError(
                    "Invalid url: must be a non-empty string",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "url", "value": url},
                )
            if not (url.startswith("http://") or url.startswith("https://")):
                raise ValidationError(
                    "Invalid url: must start with http:// or https://",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "url", "value": url},
                )
            validated_data["url"] = url.strip()

        # Validate category if provided
        if "category" in data:
            category = data["category"]
            if not isinstance(category, str) or not category.strip():
                raise ValidationError(
                    "Invalid category: must be a non-empty string",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "category", "value": category},
                )
            validated_data["category"] = category.strip()

        # Validate is_active if provided
        if "is_active" in data:
            is_active = data["is_active"]
            if not isinstance(is_active, bool):
                raise ValidationError(
                    "Invalid is_active: must be a boolean",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "is_active", "value": is_active},
                )
            validated_data["is_active"] = is_active

        return validated_data

    async def get_by_url(self, url: str) -> Optional[Feed]:
        """
        Retrieve a feed by its URL.

        Args:
            url: URL of the feed

        Returns:
            Feed if found, None otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        return await self.get_by_field("url", url)

    async def list_active_feeds(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[Feed]:
        """
        List active feeds, optionally filtered by category.

        Args:
            category: Optional category filter
            limit: Maximum number of feeds to return
            offset: Number of feeds to skip

        Returns:
            List of active feeds

        Raises:
            DatabaseError: If database operation fails
        """
        filters = {"is_active": True}
        if category is not None:
            filters["category"] = category

        return await self.list(
            filters=filters, limit=limit, offset=offset, order_by="name", ascending=True
        )

    async def list_by_category(self, category: str, include_inactive: bool = False) -> list[Feed]:
        """
        List feeds by category.

        Args:
            category: Category to filter by
            include_inactive: Whether to include inactive feeds

        Returns:
            List of feeds in the category

        Raises:
            DatabaseError: If database operation fails
        """
        filters = {"category": category}
        if not include_inactive:
            filters["is_active"] = True

        return await self.list(filters=filters, order_by="name", ascending=True)

    async def list_recommended_feeds(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> list[Feed]:
        """
        List recommended feeds sorted by recommendation_priority.

        Args:
            limit: Maximum number of feeds to return
            offset: Number of feeds to skip

        Returns:
            List of recommended feeds sorted by priority (highest first)

        Raises:
            DatabaseError: If database operation fails
        """
        return await self.list(
            filters={"is_recommended": True},
            limit=limit,
            offset=offset,
            order_by="recommendation_priority",
            ascending=False,
        )

    async def update_recommendation_status(
        self, feed_id: UUID, is_recommended: bool, priority: int
    ) -> Feed:
        """
        Update the recommendation status and priority for a feed.

        Args:
            feed_id: UUID of the feed to update
            is_recommended: Whether the feed should be recommended
            priority: Recommendation priority (0-1000, higher = more important)

        Returns:
            Updated feed

        Raises:
            NotFoundError: If feed not found
            ValidationError: If priority is negative
            DatabaseError: If database operation fails
        """
        if priority < 0:
            raise ValidationError(
                "Priority must be non-negative",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "priority", "value": priority},
            )

        return await self.update(
            feed_id, {"is_recommended": is_recommended, "recommendation_priority": priority}
        )

        """
        Deactivate a feed (soft delete).

        Args:
            feed_id: UUID of the feed to deactivate

        Returns:
            Updated feed with is_active=False

        Raises:
            NotFoundError: If feed not found
            DatabaseError: If database operation fails
        """
        return await self.update(feed_id, {"is_active": False})

    async def activate(self, feed_id: UUID) -> Feed:
        """
        Activate a feed.

        Args:
            feed_id: UUID of the feed to activate

        Returns:
            Updated feed with is_active=True

        Raises:
            NotFoundError: If feed not found
            DatabaseError: If database operation fails
        """
        return await self.update(feed_id, {"is_active": True})
