"""
User Preferences Repository

Concrete repository implementation for UserPreferences entities.
Handles all database operations related to user preferences and onboarding state.

Validates: Requirements 3.2, 3.4, 14.2, 14.3
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from supabase import Client

from app.core.errors import ErrorCode, ValidationError
from app.repositories.base import BaseRepository


class UserPreferences:
    """UserPreferences entity model."""

    def __init__(
        self,
        user_id: UUID,
        onboarding_completed: bool = False,
        onboarding_step: str | None = None,
        onboarding_skipped: bool = False,
        onboarding_started_at: datetime | None = None,
        onboarding_completed_at: datetime | None = None,
        tooltip_tour_completed: bool = False,
        tooltip_tour_skipped: bool = False,
        preferred_language: str = "zh-TW",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        modified_by: str | None = None,
        deleted_at: datetime | None = None,
    ):
        self.user_id = user_id
        self.onboarding_completed = onboarding_completed
        self.onboarding_step = onboarding_step
        self.onboarding_skipped = onboarding_skipped
        self.onboarding_started_at = onboarding_started_at
        self.onboarding_completed_at = onboarding_completed_at
        self.tooltip_tour_completed = tooltip_tour_completed
        self.tooltip_tour_skipped = tooltip_tour_skipped
        self.preferred_language = preferred_language
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at
        self.modified_by = modified_by
        self.deleted_at = deleted_at

    def __eq__(self, other):
        if not isinstance(other, UserPreferences):
            return False
        return self.user_id == other.user_id

    def __repr__(self):
        return f"UserPreferences(user_id={self.user_id}, onboarding_completed={self.onboarding_completed})"


class UserPreferencesRepository(BaseRepository[UserPreferences]):
    """
    Repository for UserPreferences entities.

    Provides data access methods for user preferences operations including
    CRUD operations and preference-specific queries.

    Validates: Requirements 3.2, 3.4
    """

    def __init__(self, client: Client):
        """
        Initialize the user preferences repository.

        Args:
            client: Supabase client instance
        """
        super().__init__(
            client, "user_preferences", enable_audit_trail=True, enable_soft_delete=False
        )

    def _map_to_entity(self, row: dict[str, Any]) -> UserPreferences:
        """
        Map a database row to a UserPreferences entity.

        Args:
            row: Dictionary containing database row data

        Returns:
            UserPreferences entity object
        """
        return UserPreferences(
            user_id=UUID(row["user_id"]) if isinstance(row["user_id"], str) else row["user_id"],
            onboarding_completed=row.get("onboarding_completed", False),
            onboarding_step=row.get("onboarding_step"),
            onboarding_skipped=row.get("onboarding_skipped", False),
            onboarding_started_at=row.get("onboarding_started_at"),
            onboarding_completed_at=row.get("onboarding_completed_at"),
            tooltip_tour_completed=row.get("tooltip_tour_completed", False),
            tooltip_tour_skipped=row.get("tooltip_tour_skipped", False),
            preferred_language=row.get("preferred_language", "zh-TW"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            modified_by=row.get("modified_by"),
            deleted_at=row.get("deleted_at"),
        )

    def _validate_create_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before creating user preferences.

        Args:
            data: Dictionary containing user preferences data

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        # Check required fields
        if "user_id" not in data:
            raise ValidationError(
                "Missing required field: user_id",
                error_code=ErrorCode.VALIDATION_MISSING_FIELD,
                details={"field": "user_id"},
            )

        # Build validated data with defaults
        validated_data = {
            "user_id": str(data["user_id"]),
            "onboarding_completed": data.get("onboarding_completed", False),
            "onboarding_step": data.get("onboarding_step"),
            "onboarding_skipped": data.get("onboarding_skipped", False),
            "tooltip_tour_completed": data.get("tooltip_tour_completed", False),
            "tooltip_tour_skipped": data.get("tooltip_tour_skipped", False),
            "preferred_language": data.get("preferred_language", "zh-TW"),
        }

        # Add optional timestamp fields if provided
        if "onboarding_started_at" in data:
            validated_data["onboarding_started_at"] = data["onboarding_started_at"]
        if "onboarding_completed_at" in data:
            validated_data["onboarding_completed_at"] = data["onboarding_completed_at"]

        return validated_data

    def _validate_update_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before updating user preferences.

        Args:
            data: Dictionary containing fields to update

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        validated_data = {}

        # Validate boolean fields if provided
        bool_fields = [
            "onboarding_completed",
            "onboarding_skipped",
            "tooltip_tour_completed",
            "tooltip_tour_skipped",
        ]
        for field in bool_fields:
            if field in data:
                value = data[field]
                if not isinstance(value, bool):
                    raise ValidationError(
                        f"Invalid {field}: must be a boolean",
                        error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                        details={"field": field, "value": value},
                    )
                validated_data[field] = value

        # Validate string fields if provided
        if "onboarding_step" in data:
            validated_data["onboarding_step"] = data["onboarding_step"]

        if "preferred_language" in data:
            lang = data["preferred_language"]
            if not isinstance(lang, str) or not lang.strip():
                raise ValidationError(
                    "Invalid preferred_language: must be a non-empty string",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "preferred_language", "value": lang},
                )
            validated_data["preferred_language"] = lang.strip()

        # Add timestamp fields if provided
        if "onboarding_started_at" in data:
            validated_data["onboarding_started_at"] = data["onboarding_started_at"]
        if "onboarding_completed_at" in data:
            validated_data["onboarding_completed_at"] = data["onboarding_completed_at"]

        return validated_data

    async def get_by_user_id(self, user_id: UUID) -> UserPreferences | None:
        """
        Retrieve user preferences by user ID.

        Args:
            user_id: UUID of the user

        Returns:
            UserPreferences if found, None otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        return await self.get_by_field("user_id", str(user_id))

    async def update_by_user_id(self, user_id: UUID, data: dict[str, Any]) -> UserPreferences:
        """
        Update user preferences by user ID.

        Args:
            user_id: UUID of the user
            data: Dictionary containing fields to update

        Returns:
            Updated UserPreferences entity

        Raises:
            NotFoundError: If preferences not found
            ValidationError: If data validation fails
            DatabaseError: If database operation fails
        """
        # First get the preferences to find the ID
        prefs = await self.get_by_user_id(user_id)
        if not prefs:
            from app.core.errors import NotFoundError

            raise NotFoundError(
                f"User preferences not found for user {user_id}",
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                details={"user_id": str(user_id)},
            )

        # Update using the user_id as the identifier
        # Note: For user_preferences table, user_id is the primary key
        self.logger.info(
            "Updating user preferences by user_id",
            operation="update_by_user_id",
            table=self.table_name,
            user_id=str(user_id),
        )

        try:
            # Validate data before update
            validated_data = self._validate_update_data(data)

            # Add audit trail fields
            validated_data = self._add_audit_fields(validated_data, is_create=False)

            # Update in database using user_id
            response = (
                self.client.table(self.table_name)
                .update(validated_data)
                .eq("user_id", str(user_id))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                from app.core.errors import NotFoundError

                raise NotFoundError(
                    f"User preferences not found for user {user_id}",
                    error_code=ErrorCode.RESOURCE_NOT_FOUND,
                    details={"user_id": str(user_id)},
                )

            entity = self._map_to_entity(response.data[0])

            self.logger.info(
                "Successfully updated user preferences",
                operation="update_by_user_id",
                table=self.table_name,
                user_id=str(user_id),
            )

            return entity

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to update user preferences",
                exc_info=True,
                operation="update_by_user_id",
                table=self.table_name,
                user_id=str(user_id),
                error=str(e),
            )
            self._handle_database_error(
                e, {"operation": "update_by_user_id", "user_id": str(user_id), "data": data}
            )
