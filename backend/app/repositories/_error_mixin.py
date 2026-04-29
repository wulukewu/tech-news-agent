"""Error handling mixin for BaseRepository."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class RepositoryErrorMixin:
    """Mixin providing database error handling for repositories."""

    def _handle_database_error(self, error: Exception, context: dict[str, Any]) -> None:
        """
        Handle database errors and wrap them in appropriate exception types.

        Args:
            error: Original database error
            context: Error context information

        Raises:
            DatabaseError: Wrapped database error with context
        """
        error_str = str(error).lower()

        # Check for specific constraint violations
        if "duplicate key" in error_str or "unique constraint" in error_str:
            field = self._extract_field_from_error(error_str)
            raise DatabaseError(
                f"Duplicate entry: {field} already exists",
                error_code=ErrorCode.DB_CONSTRAINT_VIOLATION,
                details={**context, "constraint_type": "unique"},
                original_error=error,
            )

        elif "foreign key" in error_str:
            reference = self._extract_reference_from_error(error_str)
            raise DatabaseError(
                f"Invalid reference: {reference} does not exist",
                error_code=ErrorCode.DB_CONSTRAINT_VIOLATION,
                details={**context, "constraint_type": "foreign_key"},
                original_error=error,
            )

        elif "check constraint" in error_str:
            constraint = self._extract_constraint_from_error(error_str)
            raise DatabaseError(
                f"Validation failed: {constraint}",
                error_code=ErrorCode.DB_CONSTRAINT_VIOLATION,
                details={**context, "constraint_type": "check"},
                original_error=error,
            )

        elif "null value" in error_str and "not null" in error_str:
            field = self._extract_field_from_error(error_str)
            raise DatabaseError(
                f"Missing required field: '{field}' cannot be null",
                error_code=ErrorCode.DB_CONSTRAINT_VIOLATION,
                details={**context, "constraint_type": "not_null"},
                original_error=error,
            )

        else:
            # Generic database error
            raise DatabaseError(
                f"Database operation failed: {error}",
                error_code=ErrorCode.DB_QUERY_FAILED,
                details=context,
                original_error=error,
            )

    def _extract_field_from_error(self, error_str: str) -> str:
        """Extract field name from error message."""
        import re

        # Try to match "column \"field_name\""
        match = re.search(r'column\s+"([^"]+)"', error_str)
        if match:
            return match.group(1)

        # Try to match "key (field_name)"
        match = re.search(r"key\s+\(([^)]+)\)", error_str)
        if match:
            return match.group(1)

        return "field"

    def _extract_reference_from_error(self, error_str: str) -> str:
        """Extract reference information from error message."""
        import re

        # Try to match "table \"table_name\""
        match = re.search(r'table\s+"([^"]+)"', error_str)
        if match:
            return f"reference to table {match.group(1)}"

        return "reference"

    def _extract_constraint_from_error(self, error_str: str) -> str:
        """Extract constraint information from error message."""
        import re

        # Try to match "constraint \"constraint_name\""
        match = re.search(r'constraint\s+"([^"]+)"', error_str)
        if match:
            return match.group(1)

        return "constraint violation"
