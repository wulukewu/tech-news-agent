"""
User Repository

Concrete repository implementation for User entities.
Handles all database operations related to users.

Validates: Requirements 3.2, 3.4, 14.2, 14.3
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from supabase import Client

from app.core.errors import ErrorCode, ValidationError
from app.core.validators import UserValidator
from app.repositories.base import BaseRepository


class User:
    """User entity model."""

    def __init__(
        self,
        id: UUID,
        discord_id: str,
        dm_notifications_enabled: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        modified_by: str | None = None,
        deleted_at: datetime | None = None,
    ):
        self.id = id
        self.discord_id = discord_id
        self.dm_notifications_enabled = dm_notifications_enabled
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at
        self.modified_by = modified_by
        self.deleted_at = deleted_at

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return self.id == other.id

    def __repr__(self):
        return f"User(id={self.id}, discord_id={self.discord_id})"


class UserRepository(BaseRepository[User]):
    """
    Repository for User entities.

    Provides data access methods for user-related operations including
    CRUD operations and user-specific queries.

    Validates: Requirements 3.2, 3.4
    """

    def __init__(self, client: Client):
        """
        Initialize the user repository.

        Args:
            client: Supabase client instance
        """
        super().__init__(client, "users", enable_audit_trail=True)

    def _validate_business_rules_create(self, data: dict[str, Any]) -> None:
        """
        Validate business rules before creating a user.

        Args:
            data: Dictionary containing user data

        Raises:
            ValidationError: If business rule validation fails
        """
        UserValidator.validate_user_create(data)

    def _validate_business_rules_update(self, data: dict[str, Any]) -> None:
        """
        Validate business rules before updating a user.

        Args:
            data: Dictionary containing fields to update

        Raises:
            ValidationError: If business rule validation fails
        """
        UserValidator.validate_user_update(data)

    def _map_to_entity(self, row: dict[str, Any]) -> User:
        """
        Map a database row to a User entity.

        Args:
            row: Dictionary containing database row data

        Returns:
            User entity object
        """
        return User(
            id=UUID(row["id"]) if isinstance(row["id"], str) else row["id"],
            discord_id=row["discord_id"],
            dm_notifications_enabled=row.get("dm_notifications_enabled", True),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            modified_by=row.get("modified_by"),
            deleted_at=row.get("deleted_at"),
        )

    def _validate_create_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before creating a user.

        Args:
            data: Dictionary containing user data

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields
        if "discord_id" not in data:
            raise ValidationError(
                "Missing required field: discord_id",
                error_code=ErrorCode.VALIDATION_MISSING_FIELD,
                details={"field": "discord_id"},
            )

        # Validate discord_id format
        discord_id = data["discord_id"]
        if not isinstance(discord_id, str) or not discord_id.strip():
            raise ValidationError(
                "Invalid discord_id: must be a non-empty string",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "discord_id", "value": discord_id},
            )

        # Discord IDs must be numeric (snowflake IDs are 64-bit integers)
        if not discord_id.strip().isdigit():
            raise ValidationError(
                "Invalid discord_id: must be a numeric string (Discord snowflake ID)",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "discord_id", "value": discord_id},
            )

        # Validate Discord snowflake range (must fit in 64-bit signed integer)
        try:
            discord_id_int = int(discord_id.strip())
            if discord_id_int > 9223372036854775807:  # Max 64-bit signed int
                raise ValidationError(
                    "Invalid discord_id: value exceeds maximum Discord snowflake ID",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={
                        "field": "discord_id",
                        "value": discord_id,
                        "max": 9223372036854775807,
                    },
                )
        except ValueError:
            raise ValidationError(
                "Invalid discord_id: must be a valid integer",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "discord_id", "value": discord_id},
            )

        # Set default values
        validated_data = {
            "discord_id": discord_id.strip(),
            "dm_notifications_enabled": data.get("dm_notifications_enabled", True),
        }

        return validated_data

    def _validate_update_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before updating a user.

        Args:
            data: Dictionary containing fields to update

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        validated_data = {}

        # Validate discord_id if provided
        if "discord_id" in data:
            discord_id = data["discord_id"]
            if not isinstance(discord_id, str) or not discord_id.strip():
                raise ValidationError(
                    "Invalid discord_id: must be a non-empty string",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "discord_id", "value": discord_id},
                )

            # Discord IDs must be numeric (snowflake IDs are 64-bit integers)
            if not discord_id.strip().isdigit():
                raise ValidationError(
                    "Invalid discord_id: must be a numeric string (Discord snowflake ID)",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "discord_id", "value": discord_id},
                )

            # Validate Discord snowflake range (must fit in 64-bit signed integer)
            try:
                discord_id_int = int(discord_id.strip())
                if discord_id_int > 9223372036854775807:  # Max 64-bit signed int
                    raise ValidationError(
                        "Invalid discord_id: value exceeds maximum Discord snowflake ID",
                        error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                        details={
                            "field": "discord_id",
                            "value": discord_id,
                            "max": 9223372036854775807,
                        },
                    )
            except ValueError:
                raise ValidationError(
                    "Invalid discord_id: must be a valid integer",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "discord_id", "value": discord_id},
                )

            validated_data["discord_id"] = discord_id.strip()

        # Validate dm_notifications_enabled if provided
        if "dm_notifications_enabled" in data:
            dm_notifications = data["dm_notifications_enabled"]
            if not isinstance(dm_notifications, bool):
                raise ValidationError(
                    "Invalid dm_notifications_enabled: must be a boolean",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "dm_notifications_enabled", "value": dm_notifications},
                )
            validated_data["dm_notifications_enabled"] = dm_notifications

        return validated_data

    async def get_by_discord_id(self, discord_id: str) -> User | None:
        """
        Retrieve a user by their Discord ID.

        Args:
            discord_id: Discord ID of the user

        Returns:
            User if found, None otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        return await self.get_by_field("discord_id", discord_id)

    async def exists_by_discord_id(self, discord_id: str) -> bool:
        """
        Check if a user exists by their Discord ID.

        Args:
            discord_id: Discord ID of the user

        Returns:
            True if user exists, False otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        user = await self.get_by_discord_id(discord_id)
        return user is not None
