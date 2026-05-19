"""Base business rule validator with common validation patterns."""

from typing import Any

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
