"""Feed entity business rule validator."""
from typing import Any

from app.core.errors import ErrorCode, ValidationError
from app.core.logger import get_logger

from .base import BusinessRuleValidator

logger = get_logger(__name__)


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
