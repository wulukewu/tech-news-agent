"""ReadingList entity business rule validator."""

from typing import Any
from uuid import UUID

from app.core.errors import ErrorCode, ValidationError
from app.core.logger import get_logger

from .base import BusinessRuleValidator

logger = get_logger(__name__)


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
