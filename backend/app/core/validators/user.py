"""User entity business rule validator."""
from typing import Any

from app.core.errors import ErrorCode, ValidationError
from app.core.logger import get_logger

from .base import BusinessRuleValidator

logger = get_logger(__name__)


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
