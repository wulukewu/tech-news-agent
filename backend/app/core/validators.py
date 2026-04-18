"""
Business Rule Validators

This module provides centralized business rule validation for the application.
Validators enforce domain-specific rules before data persistence, ensuring
data integrity and consistency across the system.

Validates: Requirements 14.2, 14.3
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from app.core.errors import ErrorCode, ValidationError
from app.core.logger import get_logger

logger = get_logger(__name__)


class BusinessRuleValidator:
    """
    Base class for business rule validation.

    Provides common validation patterns and error handling for business rules.
    """

    @staticmethod
    def validate_required_field(data: dict[str, Any], field: str, field_type: type = str) -> None:
        """
        Validate that a required field exists and has the correct type.

        Args:
            data: Dictionary containing data to validate
            field: Field name to check
            field_type: Expected type of the field

        Raises:
            ValidationError: If field is missing or has wrong type
        """
        if field not in data:
            raise ValidationError(
                f"Missing required field: {field}",
                error_code=ErrorCode.VALIDATION_MISSING_FIELD,
                details={"field": field},
            )

        if not isinstance(data[field], field_type):
            raise ValidationError(
                f"Invalid type for field '{field}': expected {field_type.__name__}",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={
                    "field": field,
                    "expected_type": field_type.__name__,
                    "actual_type": type(data[field]).__name__,
                },
            )

    @staticmethod
    def validate_string_length(
        value: str, field: str, min_length: int = 1, max_length: int | None = None
    ) -> None:
        """
        Validate string length constraints.

        Args:
            value: String value to validate
            field: Field name for error messages
            min_length: Minimum allowed length
            max_length: Maximum allowed length (None for no limit)

        Raises:
            ValidationError: If length constraints are violated
        """
        if len(value) < min_length:
            raise ValidationError(
                f"Invalid {field}: must be at least {min_length} characters",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": field, "min_length": min_length, "actual_length": len(value)},
            )

        if max_length is not None and len(value) > max_length:
            raise ValidationError(
                f"Invalid {field}: exceeds maximum length of {max_length} characters",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": field, "max_length": max_length, "actual_length": len(value)},
            )

    @staticmethod
    def validate_integer_range(
        value: int, field: str, min_value: int | None = None, max_value: int | None = None
    ) -> None:
        """
        Validate integer range constraints.

        Args:
            value: Integer value to validate
            field: Field name for error messages
            min_value: Minimum allowed value (None for no limit)
            max_value: Maximum allowed value (None for no limit)

        Raises:
            ValidationError: If range constraints are violated
        """
        if min_value is not None and value < min_value:
            raise ValidationError(
                f"Invalid {field}: must be at least {min_value}",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": field, "min_value": min_value, "actual_value": value},
            )

        if max_value is not None and value > max_value:
            raise ValidationError(
                f"Invalid {field}: must be at most {max_value}",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": field, "max_value": max_value, "actual_value": value},
            )

    @staticmethod
    def validate_enum_value(value: Any, field: str, allowed_values: set) -> None:
        """
        Validate that a value is in the allowed set.

        Args:
            value: Value to validate
            field: Field name for error messages
            allowed_values: Set of allowed values

        Raises:
            ValidationError: If value is not in allowed set
        """
        if value not in allowed_values:
            raise ValidationError(
                f"Invalid {field}: must be one of {', '.join(sorted(str(v) for v in allowed_values))}",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": field, "value": value, "allowed_values": list(allowed_values)},
            )


class UserValidator(BusinessRuleValidator):
    """
    Business rule validator for User entities.

    Validates: Requirements 14.2, 14.3
    """

    @staticmethod
    def validate_discord_id(discord_id: str) -> None:
        """
        Validate Discord ID format.

        Discord IDs are numeric strings (snowflakes) typically 17-19 digits.

        Args:
            discord_id: Discord ID to validate

        Raises:
            ValidationError: If Discord ID format is invalid
        """
        if not discord_id or not discord_id.strip():
            raise ValidationError(
                "Invalid discord_id: cannot be empty",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "discord_id"},
            )

        # Discord IDs should be numeric
        if not discord_id.isdigit():
            raise ValidationError(
                "Invalid discord_id: must be numeric",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "discord_id", "value": discord_id},
            )

        # Discord IDs are typically 17-19 digits (snowflakes)
        if len(discord_id) < 17 or len(discord_id) > 20:
            raise ValidationError(
                "Invalid discord_id: must be 17-20 digits",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "discord_id", "length": len(discord_id)},
            )

    @staticmethod
    def validate_user_create(data: dict[str, Any]) -> None:
        """
        Validate business rules for user creation.

        Args:
            data: User data to validate

        Raises:
            ValidationError: If validation fails
        """
        logger.debug("Validating user creation data", operation="validate_user_create")

        # Validate required fields
        BusinessRuleValidator.validate_required_field(data, "discord_id", str)

        # Validate Discord ID format
        UserValidator.validate_discord_id(data["discord_id"])

        # Validate dm_notifications_enabled if provided
        if "dm_notifications_enabled" in data:
            if not isinstance(data["dm_notifications_enabled"], bool):
                raise ValidationError(
                    "Invalid dm_notifications_enabled: must be a boolean",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={
                        "field": "dm_notifications_enabled",
                        "value": data["dm_notifications_enabled"],
                    },
                )

        logger.debug("User creation data validated successfully", operation="validate_user_create")

    @staticmethod
    def validate_user_update(data: dict[str, Any]) -> None:
        """
        Validate business rules for user updates.

        Args:
            data: User update data to validate

        Raises:
            ValidationError: If validation fails
        """
        logger.debug("Validating user update data", operation="validate_user_update")

        # Validate Discord ID if provided
        if "discord_id" in data:
            UserValidator.validate_discord_id(data["discord_id"])

        # Validate dm_notifications_enabled if provided
        if "dm_notifications_enabled" in data:
            if not isinstance(data["dm_notifications_enabled"], bool):
                raise ValidationError(
                    "Invalid dm_notifications_enabled: must be a boolean",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={
                        "field": "dm_notifications_enabled",
                        "value": data["dm_notifications_enabled"],
                    },
                )

        logger.debug("User update data validated successfully", operation="validate_user_update")


class FeedValidator(BusinessRuleValidator):
    """
    Business rule validator for Feed entities.

    Validates: Requirements 14.2, 14.3
    """

    @staticmethod
    def validate_url_format(url: str) -> None:
        """
        Validate URL format.

        Args:
            url: URL to validate

        Raises:
            ValidationError: If URL format is invalid
        """
        if not url or not url.strip():
            raise ValidationError(
                "Invalid url: cannot be empty",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "url"},
            )

        # Must start with http:// or https://
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValidationError(
                "Invalid url: must start with http:// or https://",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "url", "value": url},
            )

        # Basic length check
        if len(url) > 2048:
            raise ValidationError(
                "Invalid url: exceeds maximum length of 2048 characters",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "url", "length": len(url)},
            )

    @staticmethod
    def validate_feed_create(data: dict[str, Any]) -> None:
        """
        Validate business rules for feed creation.

        Args:
            data: Feed data to validate

        Raises:
            ValidationError: If validation fails
        """
        logger.debug("Validating feed creation data", operation="validate_feed_create")

        # Validate required fields
        BusinessRuleValidator.validate_required_field(data, "name", str)
        BusinessRuleValidator.validate_required_field(data, "url", str)
        BusinessRuleValidator.validate_required_field(data, "category", str)

        # Validate name
        name = data["name"].strip()
        BusinessRuleValidator.validate_string_length(name, "name", min_length=1, max_length=255)

        # Validate URL
        FeedValidator.validate_url_format(data["url"])

        # Validate category
        category = data["category"].strip()
        BusinessRuleValidator.validate_string_length(
            category, "category", min_length=1, max_length=100
        )

        # Validate is_active if provided
        if "is_active" in data:
            if not isinstance(data["is_active"], bool):
                raise ValidationError(
                    "Invalid is_active: must be a boolean",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "is_active", "value": data["is_active"]},
                )

        logger.debug("Feed creation data validated successfully", operation="validate_feed_create")

    @staticmethod
    def validate_feed_update(data: dict[str, Any]) -> None:
        """
        Validate business rules for feed updates.

        Args:
            data: Feed update data to validate

        Raises:
            ValidationError: If validation fails
        """
        logger.debug("Validating feed update data", operation="validate_feed_update")

        # Validate name if provided
        if "name" in data:
            name = data["name"].strip()
            BusinessRuleValidator.validate_string_length(name, "name", min_length=1, max_length=255)

        # Validate URL if provided
        if "url" in data:
            FeedValidator.validate_url_format(data["url"])

        # Validate category if provided
        if "category" in data:
            category = data["category"].strip()
            BusinessRuleValidator.validate_string_length(
                category, "category", min_length=1, max_length=100
            )

        # Validate is_active if provided
        if "is_active" in data:
            if not isinstance(data["is_active"], bool):
                raise ValidationError(
                    "Invalid is_active: must be a boolean",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "is_active", "value": data["is_active"]},
                )

        logger.debug("Feed update data validated successfully", operation="validate_feed_update")


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


class ReadingListValidator(BusinessRuleValidator):
    """
    Business rule validator for ReadingList entities.

    Validates: Requirements 14.2, 14.3
    """

    # Valid status values
    VALID_STATUSES = {"Unread", "Read", "Archived"}

    # Valid rating range
    RATING_MIN = 1
    RATING_MAX = 5

    @staticmethod
    def validate_reading_list_create(data: dict[str, Any]) -> None:
        """
        Validate business rules for reading list item creation.

        Args:
            data: Reading list item data to validate

        Raises:
            ValidationError: If validation fails
        """
        logger.debug(
            "Validating reading list creation data", operation="validate_reading_list_create"
        )

        # Validate required fields
        BusinessRuleValidator.validate_required_field(data, "user_id", (str, UUID))
        BusinessRuleValidator.validate_required_field(data, "article_id", (str, UUID))
        BusinessRuleValidator.validate_required_field(data, "status", str)

        # Validate status
        BusinessRuleValidator.validate_enum_value(
            data["status"], "status", ReadingListValidator.VALID_STATUSES
        )

        # Validate rating if provided
        if "rating" in data and data["rating"] is not None:
            if not isinstance(data["rating"], int):
                raise ValidationError(
                    "Invalid rating: must be an integer",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "rating", "value": data["rating"]},
                )
            BusinessRuleValidator.validate_integer_range(
                data["rating"],
                "rating",
                min_value=ReadingListValidator.RATING_MIN,
                max_value=ReadingListValidator.RATING_MAX,
            )

        logger.debug(
            "Reading list creation data validated successfully",
            operation="validate_reading_list_create",
        )

    @staticmethod
    def validate_reading_list_update(data: dict[str, Any]) -> None:
        """
        Validate business rules for reading list item updates.

        Args:
            data: Reading list item update data to validate

        Raises:
            ValidationError: If validation fails
        """
        logger.debug(
            "Validating reading list update data", operation="validate_reading_list_update"
        )

        # Validate status if provided
        if "status" in data:
            BusinessRuleValidator.validate_enum_value(
                data["status"], "status", ReadingListValidator.VALID_STATUSES
            )

        # Validate rating if provided (allow None to clear rating)
        if "rating" in data and data["rating"] is not None:
            if not isinstance(data["rating"], int):
                raise ValidationError(
                    "Invalid rating: must be an integer or null",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "rating", "value": data["rating"]},
                )
            BusinessRuleValidator.validate_integer_range(
                data["rating"],
                "rating",
                min_value=ReadingListValidator.RATING_MIN,
                max_value=ReadingListValidator.RATING_MAX,
            )

        logger.debug(
            "Reading list update data validated successfully",
            operation="validate_reading_list_update",
        )

    @staticmethod
    def validate_status_transition(current_status: str, new_status: str) -> None:
        """
        Validate reading list status transitions.

        Business rule: Status transitions should follow logical flow:
        - Unread -> Read (normal reading flow)
        - Read -> Archived (archiving after reading)
        - Unread -> Archived (skip reading, archive directly)
        - Any status can transition to any other status (flexible for user corrections)

        Args:
            current_status: Current status value
            new_status: New status value

        Raises:
            ValidationError: If transition is invalid
        """
        # Validate both statuses are valid
        BusinessRuleValidator.validate_enum_value(
            current_status, "current_status", ReadingListValidator.VALID_STATUSES
        )
        BusinessRuleValidator.validate_enum_value(
            new_status, "new_status", ReadingListValidator.VALID_STATUSES
        )

        # All transitions are allowed for flexibility
        # This is a placeholder for future business rules if needed
        logger.debug(
            f"Status transition validated: {current_status} -> {new_status}",
            operation="validate_status_transition",
            current_status=current_status,
            new_status=new_status,
        )
