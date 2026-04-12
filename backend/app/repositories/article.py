"""
Article Repository

Concrete repository implementation for Article entities.
Handles all database operations related to articles.

Validates: Requirements 3.2, 3.4, 14.2, 14.3, 15.4
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from supabase import Client

from app.core.errors import ErrorCode, ValidationError
from app.core.validators import ArticleValidator
from app.repositories.base import BaseRepository


class Article:
    """Article entity model."""

    def __init__(
        self,
        id: UUID,
        feed_id: UUID,
        title: str,
        url: str,
        published_at: Optional[datetime] = None,
        tinkering_index: Optional[int] = None,
        ai_summary: Optional[str] = None,
        deep_summary: Optional[str] = None,
        deep_summary_generated_at: Optional[datetime] = None,
        embedding: Optional[list[float]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        modified_by: Optional[str] = None,
        deleted_at: Optional[datetime] = None,
    ):
        self.id = id
        self.feed_id = feed_id
        self.title = title
        self.url = url
        self.published_at = published_at
        self.tinkering_index = tinkering_index
        self.ai_summary = ai_summary
        self.deep_summary = deep_summary
        self.deep_summary_generated_at = deep_summary_generated_at
        self.embedding = embedding
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at
        self.modified_by = modified_by
        self.deleted_at = deleted_at

    def __eq__(self, other):
        if not isinstance(other, Article):
            return False
        return self.id == other.id

    def __repr__(self):
        return f"Article(id={self.id}, title={self.title[:50]}...)"


class PaginationMetadata:
    """Pagination metadata for list responses."""

    def __init__(
        self,
        page: int,
        page_size: int,
        total_count: int,
        has_next_page: bool,
        has_previous_page: bool,
    ):
        self.page = page
        self.page_size = page_size
        self.total_count = total_count
        self.has_next_page = has_next_page
        self.has_previous_page = has_previous_page

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "page": self.page,
            "page_size": self.page_size,
            "total_count": self.total_count,
            "has_next_page": self.has_next_page,
            "has_previous_page": self.has_previous_page,
        }


class ArticleRepository(BaseRepository[Article]):
    """
    Repository for Article entities.

    Provides data access methods for article-related operations including
    CRUD operations, pagination, and article-specific queries.

    Validates: Requirements 3.2, 3.4, 15.4
    """

    def __init__(self, client: Client):
        """
        Initialize the article repository.

        Args:
            client: Supabase client instance
        """
        super().__init__(client, "articles", enable_audit_trail=True)

    def _validate_business_rules_create(self, data: dict[str, Any]) -> None:
        """
        Validate business rules before creating an article.

        Args:
            data: Dictionary containing article data

        Raises:
            ValidationError: If business rule validation fails
        """
        ArticleValidator.validate_article_create(data)

    def _validate_business_rules_update(self, data: dict[str, Any]) -> None:
        """
        Validate business rules before updating an article.

        Args:
            data: Dictionary containing fields to update

        Raises:
            ValidationError: If business rule validation fails
        """
        ArticleValidator.validate_article_update(data)

    def _map_to_entity(self, row: dict[str, Any]) -> Article:
        """
        Map a database row to an Article entity.

        Args:
            row: Dictionary containing database row data

        Returns:
            Article entity object
        """
        return Article(
            id=UUID(row["id"]) if isinstance(row["id"], str) else row["id"],
            feed_id=UUID(row["feed_id"]) if isinstance(row["feed_id"], str) else row["feed_id"],
            title=row["title"],
            url=row["url"],
            published_at=row.get("published_at"),
            tinkering_index=row.get("tinkering_index"),
            ai_summary=row.get("ai_summary"),
            deep_summary=row.get("deep_summary"),
            deep_summary_generated_at=row.get("deep_summary_generated_at"),
            embedding=row.get("embedding"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            modified_by=row.get("modified_by"),
            deleted_at=row.get("deleted_at"),
        )

    def _validate_create_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before creating an article.

        Args:
            data: Dictionary containing article data

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields
        required_fields = ["feed_id", "title", "url"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(
                    f"Missing required field: {field}",
                    error_code=ErrorCode.VALIDATION_MISSING_FIELD,
                    details={"field": field},
                )

        # Validate title
        title = data["title"]
        if not isinstance(title, str) or not title.strip():
            raise ValidationError(
                "Invalid title: must be a non-empty string",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "title", "value": title},
            )

        if len(title) > 2000:
            raise ValidationError(
                "Invalid title: exceeds maximum length of 2000 characters",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "title", "length": len(title), "max_length": 2000},
            )

        # Validate URL
        url = data["url"]
        if not isinstance(url, str) or not url.strip():
            raise ValidationError(
                "Invalid url: must be a non-empty string",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "url", "value": url},
            )

        # Validate tinkering_index if provided
        if "tinkering_index" in data and data["tinkering_index"] is not None:
            tinkering_index = data["tinkering_index"]
            if not isinstance(tinkering_index, int) or not (1 <= tinkering_index <= 5):
                raise ValidationError(
                    "Invalid tinkering_index: must be an integer between 1 and 5",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "tinkering_index", "value": tinkering_index},
                )

        # Validate ai_summary length if provided
        if "ai_summary" in data and data["ai_summary"] is not None:
            ai_summary = data["ai_summary"]
            if len(ai_summary) > 5000:
                raise ValidationError(
                    "Invalid ai_summary: exceeds maximum length of 5000 characters",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "ai_summary", "length": len(ai_summary), "max_length": 5000},
                )

        # Build validated data
        validated_data = {
            "feed_id": str(data["feed_id"]),
            "title": title.strip(),
            "url": url.strip(),
        }

        # Add optional fields
        optional_fields = [
            "published_at",
            "tinkering_index",
            "ai_summary",
            "deep_summary",
            "deep_summary_generated_at",
            "embedding",
        ]
        for field in optional_fields:
            if field in data:
                validated_data[field] = data[field]

        return validated_data

    def _validate_update_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before updating an article.

        Args:
            data: Dictionary containing fields to update

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        validated_data = {}

        # Validate title if provided
        if "title" in data:
            title = data["title"]
            if not isinstance(title, str) or not title.strip():
                raise ValidationError(
                    "Invalid title: must be a non-empty string",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "title", "value": title},
                )
            if len(title) > 2000:
                raise ValidationError(
                    "Invalid title: exceeds maximum length of 2000 characters",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "title", "length": len(title), "max_length": 2000},
                )
            validated_data["title"] = title.strip()

        # Validate tinkering_index if provided
        if "tinkering_index" in data and data["tinkering_index"] is not None:
            tinkering_index = data["tinkering_index"]
            if not isinstance(tinkering_index, int) or not (1 <= tinkering_index <= 5):
                raise ValidationError(
                    "Invalid tinkering_index: must be an integer between 1 and 5",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "tinkering_index", "value": tinkering_index},
                )
            validated_data["tinkering_index"] = tinkering_index

        # Validate ai_summary if provided
        if "ai_summary" in data and data["ai_summary"] is not None:
            ai_summary = data["ai_summary"]
            if len(ai_summary) > 5000:
                raise ValidationError(
                    "Invalid ai_summary: exceeds maximum length of 5000 characters",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "ai_summary", "length": len(ai_summary), "max_length": 5000},
                )
            validated_data["ai_summary"] = ai_summary

        # Add other optional fields without validation
        optional_fields = ["deep_summary", "deep_summary_generated_at", "embedding", "published_at"]
        for field in optional_fields:
            if field in data:
                validated_data[field] = data[field]

        return validated_data

    async def get_by_url(self, url: str) -> Optional[Article]:
        """
        Retrieve an article by its URL.

        Args:
            url: URL of the article

        Returns:
            Article if found, None otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        return await self.get_by_field("url", url)

    async def list_with_pagination(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[dict[str, Any]] = None,
        order_by: Optional[str] = None,
        ascending: bool = False,
    ) -> tuple[list[Article], PaginationMetadata]:
        """
        List articles with pagination metadata.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            filters: Dictionary of field-value pairs to filter by
            order_by: Field name to sort by
            ascending: Sort direction (True for ascending, False for descending)

        Returns:
            Tuple of (list of articles, pagination metadata)

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

        # Calculate offset
        offset = (page - 1) * page_size

        # Get total count
        total_count = await self.count(filters)

        # Get articles for current page
        articles = await self.list(
            filters=filters,
            limit=page_size,
            offset=offset,
            order_by=order_by or "created_at",
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

        return articles, metadata

    async def list_by_feed(
        self,
        feed_id: UUID,
        page: int = 1,
        page_size: int = 20,
        order_by: Optional[str] = None,
        ascending: bool = False,
    ) -> tuple[list[Article], PaginationMetadata]:
        """
        List articles for a specific feed with pagination.

        Args:
            feed_id: UUID of the feed
            page: Page number (1-indexed)
            page_size: Number of items per page
            order_by: Field name to sort by
            ascending: Sort direction

        Returns:
            Tuple of (list of articles, pagination metadata)

        Raises:
            DatabaseError: If database operation fails
        """
        filters = {"feed_id": str(feed_id)}
        return await self.list_with_pagination(
            page=page, page_size=page_size, filters=filters, order_by=order_by, ascending=ascending
        )
