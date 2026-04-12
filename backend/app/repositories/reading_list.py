"""
Reading List Repository

Concrete repository implementation for ReadingList entities.
Handles all database operations related to user reading lists.

Validates: Requirements 3.2, 3.4, 14.2, 14.3, 15.4
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from supabase import Client

from app.core.errors import ErrorCode, ValidationError
from app.core.validators import ReadingListValidator
from app.repositories.article import PaginationMetadata
from app.repositories.base import BaseRepository


class ReadingListItem:
    """Reading list item entity model."""

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        article_id: UUID,
        status: str,
        rating: Optional[int] = None,
        added_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        modified_by: Optional[str] = None,
        deleted_at: Optional[datetime] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.article_id = article_id
        self.status = status
        self.rating = rating
        self.added_at = added_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.modified_by = modified_by
        self.deleted_at = deleted_at

    def __eq__(self, other):
        if not isinstance(other, ReadingListItem):
            return False
        return self.id == other.id

    def __repr__(self):
        return f"ReadingListItem(id={self.id}, user_id={self.user_id}, article_id={self.article_id}, status={self.status})"


class ReadingListRepository(BaseRepository[ReadingListItem]):
    """
    Repository for ReadingList entities.

    Provides data access methods for reading list operations including
    CRUD operations, pagination, and reading list-specific queries.

    Validates: Requirements 3.2, 3.4, 15.4
    """

    # Valid status values
    VALID_STATUSES = {"Unread", "Read", "Archived"}

    def __init__(self, client: Client):
        """
        Initialize the reading list repository.

        Args:
            client: Supabase client instance
        """
        super().__init__(client, "reading_list", enable_audit_trail=True)

    def _validate_business_rules_create(self, data: dict[str, Any]) -> None:
        """
        Validate business rules before creating a reading list item.

        Args:
            data: Dictionary containing reading list item data

        Raises:
            ValidationError: If business rule validation fails
        """
        ReadingListValidator.validate_reading_list_create(data)

    def _validate_business_rules_update(self, data: dict[str, Any]) -> None:
        """
        Validate business rules before updating a reading list item.

        Args:
            data: Dictionary containing fields to update

        Raises:
            ValidationError: If business rule validation fails
        """
        ReadingListValidator.validate_reading_list_update(data)

    def _map_to_entity(self, row: dict[str, Any]) -> ReadingListItem:
        """
        Map a database row to a ReadingListItem entity.

        Args:
            row: Dictionary containing database row data

        Returns:
            ReadingListItem entity object
        """
        return ReadingListItem(
            id=UUID(row["id"]) if isinstance(row["id"], str) else row["id"],
            user_id=UUID(row["user_id"]) if isinstance(row["user_id"], str) else row["user_id"],
            article_id=(
                UUID(row["article_id"]) if isinstance(row["article_id"], str) else row["article_id"]
            ),
            status=row["status"],
            rating=row.get("rating"),
            added_at=row.get("added_at"),
            updated_at=row.get("updated_at"),
            modified_by=row.get("modified_by"),
            deleted_at=row.get("deleted_at"),
        )

    def _validate_create_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before creating a reading list item.

        Args:
            data: Dictionary containing reading list item data

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields
        required_fields = ["user_id", "article_id", "status"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(
                    f"Missing required field: {field}",
                    error_code=ErrorCode.VALIDATION_MISSING_FIELD,
                    details={"field": field},
                )

        # Validate status
        status = data["status"]
        if status not in self.VALID_STATUSES:
            raise ValidationError(
                f"Invalid status: must be one of {', '.join(sorted(self.VALID_STATUSES))}",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={
                    "field": "status",
                    "value": status,
                    "allowed_values": list(self.VALID_STATUSES),
                },
            )

        # Validate rating if provided
        if "rating" in data and data["rating"] is not None:
            rating = data["rating"]
            if not isinstance(rating, int) or not (1 <= rating <= 5):
                raise ValidationError(
                    "Invalid rating: must be an integer between 1 and 5 or null",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "rating", "value": rating},
                )

        # Build validated data
        validated_data = {
            "user_id": str(data["user_id"]),
            "article_id": str(data["article_id"]),
            "status": status,
        }

        # Add optional rating
        if "rating" in data:
            validated_data["rating"] = data["rating"]

        return validated_data

    def _validate_update_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before updating a reading list item.

        Args:
            data: Dictionary containing fields to update

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        validated_data = {}

        # Validate status if provided
        if "status" in data:
            status = data["status"]
            if status not in self.VALID_STATUSES:
                raise ValidationError(
                    f"Invalid status: must be one of {', '.join(sorted(self.VALID_STATUSES))}",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={
                        "field": "status",
                        "value": status,
                        "allowed_values": list(self.VALID_STATUSES),
                    },
                )
            validated_data["status"] = status

        # Validate rating if provided (allow None to clear rating)
        if "rating" in data:
            rating = data["rating"]
            if rating is not None:
                if not isinstance(rating, int) or not (1 <= rating <= 5):
                    raise ValidationError(
                        "Invalid rating: must be an integer between 1 and 5 or null",
                        error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                        details={"field": "rating", "value": rating},
                    )
            validated_data["rating"] = rating

        return validated_data

    async def get_by_user_and_article(
        self, user_id: UUID, article_id: UUID
    ) -> Optional[ReadingListItem]:
        """
        Retrieve a reading list item by user and article.

        Args:
            user_id: UUID of the user
            article_id: UUID of the article

        Returns:
            ReadingListItem if found, None otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        self.logger.debug(
            "Fetching reading list item by user and article",
            operation="get_by_user_and_article",
            table=self.table_name,
            user_id=str(user_id),
            article_id=str(article_id),
        )

        try:
            query = (
                self.client.table(self.table_name)
                .select("*")
                .eq("user_id", str(user_id))
                .eq("article_id", str(article_id))
                .limit(1)
            )
            query = self._apply_soft_delete_filter(query)
            response = query.execute()

            if not response.data or len(response.data) == 0:
                return None

            return self._map_to_entity(response.data[0])

        except Exception as e:
            self.logger.error(
                "Failed to fetch reading list item by user and article",
                exc_info=True,
                operation="get_by_user_and_article",
                table=self.table_name,
                user_id=str(user_id),
                article_id=str(article_id),
                error=str(e),
            )
            self._handle_database_error(
                e,
                {
                    "operation": "get_by_user_and_article",
                    "user_id": str(user_id),
                    "article_id": str(article_id),
                },
            )

    async def list_by_user_with_pagination(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        rating: Optional[int] = None,
        order_by: Optional[str] = None,
        ascending: bool = False,
    ) -> tuple[list[ReadingListItem], PaginationMetadata]:
        """
        List reading list items for a user with pagination.

        Args:
            user_id: UUID of the user
            page: Page number (1-indexed)
            page_size: Number of items per page
            status: Optional status filter
            rating: Optional rating filter
            order_by: Field name to sort by
            ascending: Sort direction

        Returns:
            Tuple of (list of reading list items, pagination metadata)

        Raises:
            DatabaseError: If database operation fails
            ValidationError: If pagination parameters are invalid
        """
        # Validate pagination parameters
        if page < 1:
            raise ValidationError(
                "Invalid page: must be >= 1",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "page", "value": page},
            )

        if page_size < 1 or page_size > 100:
            raise ValidationError(
                "Invalid page_size: must be between 1 and 100",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "page_size", "value": page_size},
            )

        # Validate status filter if provided
        if status is not None and status not in self.VALID_STATUSES:
            raise ValidationError(
                f"Invalid status filter: must be one of {', '.join(sorted(self.VALID_STATUSES))}",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={
                    "field": "status",
                    "value": status,
                    "allowed_values": list(self.VALID_STATUSES),
                },
            )

        # Validate rating filter if provided
        if rating is not None and (not isinstance(rating, int) or not (1 <= rating <= 5)):
            raise ValidationError(
                "Invalid rating filter: must be an integer between 1 and 5",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "rating", "value": rating},
            )

        # Build filters
        filters = {"user_id": str(user_id)}
        if status is not None:
            filters["status"] = status
        if rating is not None:
            filters["rating"] = rating

        # Calculate offset
        offset = (page - 1) * page_size

        # Get total count
        total_count = await self.count(filters)

        # Get items for current page
        items = await self.list(
            filters=filters,
            limit=page_size,
            offset=offset,
            order_by=order_by or "added_at",
            ascending=ascending,
        )

        # Calculate pagination metadata
        has_next_page = (offset + page_size) < total_count
        has_previous_page = page > 1

        metadata = PaginationMetadata(
            page=page,
            page_size=page_size,
            total_count=total_count,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )

        return items, metadata

    async def exists_by_user_and_article(self, user_id: UUID, article_id: UUID) -> bool:
        """
        Check if a reading list item exists for a user and article.

        Args:
            user_id: UUID of the user
            article_id: UUID of the article

        Returns:
            True if item exists, False otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        item = await self.get_by_user_and_article(user_id, article_id)
        return item is not None

    async def update_status(self, user_id: UUID, article_id: UUID, status: str) -> ReadingListItem:
        """
        Update the status of a reading list item.

        Args:
            user_id: UUID of the user
            article_id: UUID of the article
            status: New status value

        Returns:
            Updated reading list item

        Raises:
            NotFoundError: If item not found
            ValidationError: If status is invalid
            DatabaseError: If database operation fails
        """
        # Find the item
        item = await self.get_by_user_and_article(user_id, article_id)
        if item is None:
            from app.core.errors import NotFoundError

            raise NotFoundError(
                f"Reading list item not found for user {user_id} and article {article_id}",
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                details={"user_id": str(user_id), "article_id": str(article_id)},
            )

        # Update the status
        return await self.update(item.id, {"status": status})

    async def update_rating(
        self, user_id: UUID, article_id: UUID, rating: Optional[int]
    ) -> ReadingListItem:
        """
        Update the rating of a reading list item.

        Args:
            user_id: UUID of the user
            article_id: UUID of the article
            rating: New rating value (1-5) or None to clear

        Returns:
            Updated reading list item

        Raises:
            NotFoundError: If item not found
            ValidationError: If rating is invalid
            DatabaseError: If database operation fails
        """
        # Find the item
        item = await self.get_by_user_and_article(user_id, article_id)
        if item is None:
            from app.core.errors import NotFoundError

            raise NotFoundError(
                f"Reading list item not found for user {user_id} and article {article_id}",
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                details={"user_id": str(user_id), "article_id": str(article_id)},
            )

        # Update the rating
        return await self.update(item.id, {"rating": rating})
