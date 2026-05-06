"""
User Notification Preferences Repository

Concrete repository implementation for UserNotificationPreferences entities.
Handles all database operations related to user notification preferences.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 2.1, 2.2, 2.3, 2.4
"""

from datetime import datetime, time
from typing import Any
from uuid import UUID

from supabase import Client

from app.core.errors import ErrorCode, ValidationError
from app.repositories.base import BaseRepository


class UserNotificationPreferences:
    """UserNotificationPreferences entity model."""

    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        frequency: str = "weekly",
        notification_time: time = time(18, 0),
        notification_day_of_week: int = 5,  # Friday
        notification_day_of_month: int = 1,  # First day of month
        timezone: str = "Asia/Taipei",
        dm_enabled: bool = True,
        email_enabled: bool = False,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = id
        self.user_id = user_id
        self.frequency = frequency
        self.notification_time = notification_time
        self.notification_day_of_week = notification_day_of_week
        self.notification_day_of_month = notification_day_of_month
        self.timezone = timezone
        self.dm_enabled = dm_enabled
        self.email_enabled = email_enabled
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def __eq__(self, other):
        if not isinstance(other, UserNotificationPreferences):
            return False
        return self.id == other.id

    def __repr__(self):
        return f"UserNotificationPreferences(id={self.id}, user_id={self.user_id}, frequency={self.frequency})"


class UserNotificationPreferencesRepository(BaseRepository[UserNotificationPreferences]):
    """
    Repository for UserNotificationPreferences entities.

    Provides data access methods for user notification preferences operations
    including CRUD operations and preference-specific queries.

    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 2.1, 2.2, 2.3, 2.4
    """

    def __init__(self, client: Client):
        """
        Initialize the user notification preferences repository.

        Args:
            client: Supabase client instance
        """
        super().__init__(
            client,
            "user_notification_preferences",
            enable_audit_trail=False,
            enable_soft_delete=False,
        )

    def _map_to_entity(self, row: dict[str, Any]) -> UserNotificationPreferences:
        """
        Map a database row to a UserNotificationPreferences entity.

        Args:
            row: Dictionary containing database row data

        Returns:
            UserNotificationPreferences entity object
        """
        # Parse notification_time from various formats
        notification_time_value = row.get("notification_time")
        if isinstance(notification_time_value, str):
            # Handle HH:MM:SS or HH:MM format
            time_parts = notification_time_value.split(":")
            if len(time_parts) >= 2:
                notification_time = time(int(time_parts[0]), int(time_parts[1]))
            else:
                notification_time = time(18, 0)  # Default fallback
        elif isinstance(notification_time_value, time):
            notification_time = notification_time_value
        else:
            notification_time = time(18, 0)  # Default fallback

        return UserNotificationPreferences(
            id=UUID(row["id"]) if isinstance(row["id"], str) else row["id"],
            user_id=UUID(row["user_id"]) if isinstance(row["user_id"], str) else row["user_id"],
            frequency=row.get("frequency", "weekly"),
            notification_time=notification_time,
            notification_day_of_week=row.get("notification_day_of_week", 5),  # Default: Friday
            notification_day_of_month=row.get("notification_day_of_month", 1),  # Default: 1st
            timezone=row.get("timezone", "Asia/Taipei"),
            dm_enabled=row.get("dm_enabled", True),
            email_enabled=row.get("email_enabled", False),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def _validate_create_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before creating user notification preferences.

        Args:
            data: Dictionary containing user notification preferences data

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

        # Validate frequency
        frequency = data.get("frequency", "weekly")
        valid_frequencies = ["daily", "weekly", "monthly", "disabled"]
        if frequency not in valid_frequencies:
            raise ValidationError(
                f"Invalid frequency: {frequency}. Must be one of {valid_frequencies}",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={
                    "field": "frequency",
                    "value": frequency,
                    "valid_values": valid_frequencies,
                },
            )

        # Validate notification_time
        notification_time = data.get("notification_time", "18:00")
        if isinstance(notification_time, str):
            try:
                if ":" in notification_time:
                    # Support both HH:MM and HH:MM:SS formats
                    time_parts = notification_time.split(":")
                    if len(time_parts) < 2 or len(time_parts) > 3:
                        raise ValidationError(
                            "notification_time must be in HH:MM or HH:MM:SS format",
                            error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                            details={"field": "notification_time", "value": notification_time},
                        )

                    hour_int = int(time_parts[0])
                    minute_int = int(time_parts[1])

                    if not (0 <= hour_int <= 23):
                        raise ValidationError(
                            f"Invalid hour: {hour_int}. Must be between 0 and 23",
                            error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                            details={"field": "notification_time", "hour": hour_int},
                        )
                    if not (0 <= minute_int <= 59):
                        raise ValidationError(
                            f"Invalid minute: {minute_int}. Must be between 0 and 59",
                            error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                            details={"field": "notification_time", "minute": minute_int},
                        )

                    # Convert to time format for database
                    notification_time = f"{hour_int:02d}:{minute_int:02d}:00"
                else:
                    raise ValidationError(
                        "notification_time must be in HH:MM or HH:MM:SS format",
                        error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                        details={"field": "notification_time", "value": notification_time},
                    )
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValidationError(
                        "notification_time must contain valid integers",
                        error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                        details={"field": "notification_time", "value": notification_time},
                    )
                raise

        # Validate timezone
        timezone = data.get("timezone", "Asia/Taipei")
        try:
            # Try to validate timezone
            import zoneinfo

            zoneinfo.ZoneInfo(timezone)
        except Exception:
            # Fallback validation
            try:
                import pytz

                pytz.timezone(timezone)
            except Exception:
                raise ValidationError(
                    f"Invalid timezone identifier: {timezone}",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "timezone", "value": timezone},
                )

        # Build validated data with defaults
        validated_data = {
            "user_id": str(data["user_id"]),
            "frequency": frequency,
            "notification_time": notification_time,
            "notification_day_of_week": data.get("notification_day_of_week", 5),  # Default: Friday
            "notification_day_of_month": data.get("notification_day_of_month", 1),  # Default: 1st
            "timezone": timezone,
            "dm_enabled": data.get("dm_enabled", True),
            "email_enabled": data.get("email_enabled", False),
        }

        # Validate notification_day_of_week if provided
        day_of_week = validated_data["notification_day_of_week"]
        if not isinstance(day_of_week, int) or not (0 <= day_of_week <= 6):
            raise ValidationError(
                f"Invalid notification_day_of_week: {day_of_week}. Must be an integer between 0 (Sunday) and 6 (Saturday)",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "notification_day_of_week", "value": day_of_week},
            )

        # Validate notification_day_of_month if provided
        day_of_month = validated_data["notification_day_of_month"]
        if not isinstance(day_of_month, int) or not (1 <= day_of_month <= 31):
            raise ValidationError(
                f"Invalid notification_day_of_month: {day_of_month}. Must be an integer between 1 and 31",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                details={"field": "notification_day_of_month", "value": day_of_month},
            )

        return validated_data

    def _validate_update_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate data before updating user notification preferences.

        Args:
            data: Dictionary containing fields to update

        Returns:
            Validated and potentially transformed data

        Raises:
            ValidationError: If validation fails
        """
        validated_data = {}

        # Validate frequency if provided
        if "frequency" in data:
            frequency = data["frequency"]
            valid_frequencies = ["daily", "weekly", "monthly", "disabled"]
            if frequency not in valid_frequencies:
                raise ValidationError(
                    f"Invalid frequency: {frequency}. Must be one of {valid_frequencies}",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={
                        "field": "frequency",
                        "value": frequency,
                        "valid_values": valid_frequencies,
                    },
                )
            validated_data["frequency"] = frequency

        # Validate notification_time if provided
        if "notification_time" in data:
            notification_time = data["notification_time"]
            if isinstance(notification_time, str):
                try:
                    if ":" in notification_time:
                        # Support both HH:MM and HH:MM:SS formats
                        time_parts = notification_time.split(":")
                        if len(time_parts) < 2 or len(time_parts) > 3:
                            raise ValidationError(
                                "notification_time must be in HH:MM or HH:MM:SS format",
                                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                                details={"field": "notification_time", "value": notification_time},
                            )

                        hour_int = int(time_parts[0])
                        minute_int = int(time_parts[1])

                        if not (0 <= hour_int <= 23):
                            raise ValidationError(
                                f"Invalid hour: {hour_int}. Must be between 0 and 23",
                                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                                details={"field": "notification_time", "hour": hour_int},
                            )
                        if not (0 <= minute_int <= 59):
                            raise ValidationError(
                                f"Invalid minute: {minute_int}. Must be between 0 and 59",
                                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                                details={"field": "notification_time", "minute": minute_int},
                            )

                        # Convert to time format for database
                        validated_data["notification_time"] = f"{hour_int:02d}:{minute_int:02d}:00"
                    else:
                        raise ValidationError(
                            "notification_time must be in HH:MM format",
                            error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                            details={"field": "notification_time", "value": notification_time},
                        )
                except ValueError as e:
                    if "invalid literal" in str(e):
                        raise ValidationError(
                            "notification_time must contain valid integers",
                            error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                            details={"field": "notification_time", "value": notification_time},
                        )
                    raise

        # Validate timezone if provided
        if "timezone" in data:
            timezone = data["timezone"]
            try:
                # Try to validate timezone
                import zoneinfo

                zoneinfo.ZoneInfo(timezone)
                validated_data["timezone"] = timezone
            except Exception:
                # Fallback validation
                try:
                    import pytz

                    pytz.timezone(timezone)
                    validated_data["timezone"] = timezone
                except Exception:
                    raise ValidationError(
                        f"Invalid timezone identifier: {timezone}",
                        error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                        details={"field": "timezone", "value": timezone},
                    )

        # Validate boolean fields if provided
        if "dm_enabled" in data:
            dm_enabled = data["dm_enabled"]
            if not isinstance(dm_enabled, bool):
                raise ValidationError(
                    "dm_enabled must be a boolean",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "dm_enabled", "value": dm_enabled},
                )
            validated_data["dm_enabled"] = dm_enabled

        if "email_enabled" in data:
            email_enabled = data["email_enabled"]
            if not isinstance(email_enabled, bool):
                raise ValidationError(
                    "email_enabled must be a boolean",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "email_enabled", "value": email_enabled},
                )
            validated_data["email_enabled"] = email_enabled

        # Validate notification_day_of_week if provided
        if "notification_day_of_week" in data:
            day_of_week = data["notification_day_of_week"]
            if not isinstance(day_of_week, int) or not (0 <= day_of_week <= 6):
                raise ValidationError(
                    f"Invalid notification_day_of_week: {day_of_week}. Must be an integer between 0 (Sunday) and 6 (Saturday)",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "notification_day_of_week", "value": day_of_week},
                )
            validated_data["notification_day_of_week"] = day_of_week

        # Validate notification_day_of_month if provided
        if "notification_day_of_month" in data:
            day_of_month = data["notification_day_of_month"]
            if not isinstance(day_of_month, int) or not (1 <= day_of_month <= 31):
                raise ValidationError(
                    f"Invalid notification_day_of_month: {day_of_month}. Must be an integer between 1 and 31",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"field": "notification_day_of_month", "value": day_of_month},
                )
            validated_data["notification_day_of_month"] = day_of_month

        return validated_data

    async def get_by_user_id(self, user_id: UUID) -> UserNotificationPreferences | None:
        """
        Retrieve user notification preferences by user ID.

        Args:
            user_id: UUID of the user

        Returns:
            UserNotificationPreferences if found, None otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        return await self.get_by_field("user_id", str(user_id))

    async def update_by_user_id(
        self, user_id: UUID, data: dict[str, Any]
    ) -> UserNotificationPreferences:
        """
        Update user notification preferences by user ID.

        Args:
            user_id: UUID of the user
            data: Dictionary containing fields to update

        Returns:
            Updated UserNotificationPreferences entity

        Raises:
            NotFoundError: If preferences not found
            ValidationError: If data validation fails
            DatabaseError: If database operation fails
        """
        # First get the preferences to ensure they exist
        prefs = await self.get_by_user_id(user_id)
        if not prefs:
            from app.core.errors import NotFoundError

            raise NotFoundError(
                f"User notification preferences not found for user {user_id}",
                error_code=ErrorCode.RESOURCE_NOT_FOUND,
                details={"user_id": str(user_id)},
            )

        # Update using the user_id as the identifier
        self.logger.info(
            "Updating user notification preferences by user_id",
            operation="update_by_user_id",
            table=self.table_name,
            user_id=str(user_id),
        )

        try:
            # Validate data before update
            validated_data = self._validate_update_data(data)

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
                    f"User notification preferences not found for user {user_id}",
                    error_code=ErrorCode.RESOURCE_NOT_FOUND,
                    details={"user_id": str(user_id)},
                )

            entity = self._map_to_entity(response.data[0])

            self.logger.info(
                "Successfully updated user notification preferences",
                operation="update_by_user_id",
                table=self.table_name,
                user_id=str(user_id),
            )

            return entity

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to update user notification preferences",
                exc_info=True,
                operation="update_by_user_id",
                table=self.table_name,
                user_id=str(user_id),
                error=str(e),
            )
            self._handle_database_error(
                e, {"operation": "update_by_user_id", "user_id": str(user_id), "data": data}
            )

    async def create_default_for_user(self, user_id: UUID) -> UserNotificationPreferences:
        """
        Create default notification preferences for a user.

        Args:
            user_id: UUID of the user

        Returns:
            Created UserNotificationPreferences entity

        Raises:
            ValidationError: If data validation fails
            DatabaseError: If database operation fails
        """
        default_data = {
            "user_id": str(user_id),
            "frequency": "weekly",
            "notification_time": "18:00",
            "notification_day_of_week": 5,  # Friday
            "notification_day_of_month": 1,  # First day of month
            "timezone": "Asia/Taipei",
            "dm_enabled": True,
            "email_enabled": False,
        }

        return await self.create(default_data)

    async def list_by_field(self, field: str, value: Any) -> list[UserNotificationPreferences]:
        """
        List all entities matching a specific field value.

        Args:
            field: Field name to filter by
            value: Value to match

        Returns:
            List of UserNotificationPreferences entities

        Raises:
            DatabaseError: If database operation fails
        """
        self.logger.info(
            "Listing entities by field",
            operation="list_by_field",
            table=self.table_name,
            field=field,
            value=value,
        )

        try:
            query = self.client.table(self.table_name).select("*").eq(field, value)

            response = query.execute()

            entities = [self._map_to_entity(row) for row in response.data]

            self.logger.info(
                "Successfully listed entities by field",
                operation="list_by_field",
                table=self.table_name,
                field=field,
                value=value,
                count=len(entities),
            )

            return entities

        except Exception as e:
            self.logger.error(
                "Failed to list entities by field",
                exc_info=True,
                operation="list_by_field",
                table=self.table_name,
                field=field,
                value=value,
                error=str(e),
            )
            self._handle_database_error(
                e, {"operation": "list_by_field", "field": field, "value": value}
            )

    async def get_all_active_preferences(self) -> list[UserNotificationPreferences]:
        """
        Get all active user notification preferences.

        Returns preferences for users who have:
        - frequency != 'disabled'
        - dm_enabled = True

        This is used to restore notification schedules on application startup.

        Returns:
            List of active UserNotificationPreferences entities

        Raises:
            DatabaseError: If database operation fails
        """
        self.logger.info(
            "Getting all active notification preferences",
            operation="get_all_active_preferences",
            table=self.table_name,
        )

        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .neq("frequency", "disabled")
                .eq("dm_enabled", True)
                .execute()
            )

            entities = [self._map_to_entity(row) for row in response.data]

            self.logger.info(
                "Successfully retrieved active notification preferences",
                operation="get_all_active_preferences",
                table=self.table_name,
                count=len(entities),
            )

            return entities

        except Exception as e:
            self.logger.error(
                "Failed to get all active preferences",
                exc_info=True,
                operation="get_all_active_preferences",
                table=self.table_name,
                error=str(e),
            )
            self._handle_database_error(e, {"operation": "get_all_active_preferences"})
