"""Article entity business rule validator."""
from datetime import datetime
from typing import Any
from uuid import UUID

from app.core.errors import ErrorCode, ValidationError
from app.core.logger import get_logger

from .base import BusinessRuleValidator

logger = get_logger(__name__)


class ArticleValidator(BusinessRuleValidator):
    """
    Business rule validator for Article entities.

    Validates: Requirements 14.2, 14.3
    """

    # Valid tinkering index range
    TINKERING_INDEX_MIN = 1
    TINKERING_INDEX_MAX = 5

    @staticmethod
    def validate_article_create(data: dict[str, Any]) -> None:
        """
        Validate business rules for article creation.

        Args:
            data: Article data to validate

        Raises:
            ValidationError: If validation fails
        """
        logger.debug("Validating article creation data", operation="validate_article_create")

        # Validate required fields
        BusinessRuleValidator.validate_required_field(data, "feed_id", (str, UUID))
        BusinessRuleValidator.validate_required_field(data, "title", str)
        BusinessRuleValidator.validate_required_field(data, "url", str)

        # Validate title
        title = data["title"].strip()
        BusinessRuleValidator.validate_string_length(title, "title", min_length=1, max_length=2000)

        # Validate URL
        url = data["url"].strip()
        BusinessRuleValidator.validate_string_length(url, "url", min_length=1, max_length=2048)

        # Validate tinkering_index if provided
        if "tinkering_index" in data and data["tinkering_index"] is not None:
            if not isinstance(data["tinkering_index"], int):
                raise ValidationError(
                    "Invalid tinkering_index: must be an integer",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "tinkering_index", "value": data["tinkering_index"]},
                )
            BusinessRuleValidator.validate_integer_range(
                data["tinkering_index"],
                "tinkering_index",
                min_value=ArticleValidator.TINKERING_INDEX_MIN,
                max_value=ArticleValidator.TINKERING_INDEX_MAX,
            )

        # Validate ai_summary length if provided
        if "ai_summary" in data and data["ai_summary"] is not None:
            BusinessRuleValidator.validate_string_length(
                data["ai_summary"], "ai_summary", min_length=0, max_length=5000
            )

        # Validate deep_summary length if provided
        if "deep_summary" in data and data["deep_summary"] is not None:
            BusinessRuleValidator.validate_string_length(
                data["deep_summary"], "deep_summary", min_length=0, max_length=10000
            )

        # Validate published_at if provided
        if "published_at" in data and data["published_at"] is not None:
            if not isinstance(data["published_at"], (datetime, str)):
                raise ValidationError(
                    "Invalid published_at: must be a datetime or ISO string",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "published_at", "value": data["published_at"]},
                )

        logger.debug(
            "Article creation data validated successfully", operation="validate_article_create"
        )

    @staticmethod
    def validate_article_update(data: dict[str, Any]) -> None:
        """
        Validate business rules for article updates.

        Args:
            data: Article update data to validate

        Raises:
            ValidationError: If validation fails
        """
        logger.debug("Validating article update data", operation="validate_article_update")

        # Validate title if provided
        if "title" in data:
            title = data["title"].strip()
            BusinessRuleValidator.validate_string_length(
                title, "title", min_length=1, max_length=2000
            )

        # Validate tinkering_index if provided
        if "tinkering_index" in data and data["tinkering_index"] is not None:
            if not isinstance(data["tinkering_index"], int):
                raise ValidationError(
                    "Invalid tinkering_index: must be an integer",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "tinkering_index", "value": data["tinkering_index"]},
                )
            BusinessRuleValidator.validate_integer_range(
                data["tinkering_index"],
                "tinkering_index",
                min_value=ArticleValidator.TINKERING_INDEX_MIN,
                max_value=ArticleValidator.TINKERING_INDEX_MAX,
            )

        # Validate ai_summary if provided
        if "ai_summary" in data and data["ai_summary"] is not None:
            BusinessRuleValidator.validate_string_length(
                data["ai_summary"], "ai_summary", min_length=0, max_length=5000
            )

        # Validate deep_summary if provided
        if "deep_summary" in data and data["deep_summary"] is not None:
            BusinessRuleValidator.validate_string_length(
                data["deep_summary"], "deep_summary", min_length=0, max_length=10000
            )

        logger.debug(
            "Article update data validated successfully", operation="validate_article_update"
        )
