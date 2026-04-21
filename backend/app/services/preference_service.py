"""
Preference Service

This module provides the PreferenceService class for managing user notification
preferences including CRUD operations, validation, and default preference creation.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 2.1, 2.2, 2.3, 2.4
"""

from uuid import UUID

from app.core.errors import ErrorCode, ValidationError
from app.core.logger import get_logger
from app.core.timezone_converter import TimezoneConverter
from app.repositories.user_notification_preferences import (
    UserNotificationPreferences,
    UserNotificationPreferencesRepository,
)
from app.schemas.user_notification_preferences import (
    CreateUserNotificationPreferencesRequest,
    UpdateUserNotificationPreferencesRequest,
    ValidationResult,
)
from app.services.base import BaseService
from app.services.preference_event_system import (
    PreferenceChangeEvent,
    get_preference_event_system,
)

logger = get_logger(__name__)


class PreferenceService(BaseService):
    """
    Service for managing user notification preferences.

    This service handles:
    - Retrieving user notification preferences
    - Creating default preferences for new users
    - Updating notification preferences with validation
    - Validating preference settings (frequency, time, timezone)
    - Database CRUD operations with proper error handling

    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 2.1, 2.2, 2.3, 2.4
    """

    def __init__(self, preferences_repo: UserNotificationPreferencesRepository):
        """
        Initialize the PreferenceService.

        Args:
            preferences_repo: Repository for user notification preferences data access
        """
        super().__init__()
        self.preferences_repo = preferences_repo
        self.logger = get_logger(f"{__name__}.PreferenceService")
        self.event_system = get_preference_event_system()

    async def get_user_preferences(self, user_id: UUID) -> UserNotificationPreferences:
        """
        Get user's notification preferences.

        If the user doesn't have preferences, creates default preferences.

        Args:
            user_id: UUID of the user

        Returns:
            UserNotificationPreferences: User's notification preferences

        Raises:
            ServiceError: If database operation fails

        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
        """
        try:
            self.logger.info("Getting user notification preferences", user_id=str(user_id))

            # Try to get existing preferences
            preferences = await self.preferences_repo.get_by_user_id(user_id)

            # If no preferences exist, create default ones
            if not preferences:
                self.logger.info("No preferences found, creating defaults", user_id=str(user_id))
                preferences = await self.create_default_preferences(user_id)

            self.logger.info(
                "Retrieved user notification preferences",
                user_id=str(user_id),
                frequency=preferences.frequency,
                dm_enabled=preferences.dm_enabled,
            )

            return preferences

        except Exception as e:
            self._handle_error(
                e,
                "Failed to get user notification preferences",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={"user_id": str(user_id)},
            )

    async def update_preferences(
        self,
        user_id: UUID,
        updates: UpdateUserNotificationPreferencesRequest,
        source: str = "unknown",
    ) -> UserNotificationPreferences:
        """
        Update user's notification preferences.

        Args:
            user_id: UUID of the user
            updates: Preference updates to apply
            source: Source of the update (web, discord, system)

        Returns:
            UserNotificationPreferences: Updated notification preferences

        Raises:
            ServiceError: If database operation fails
            ValidationError: If validation fails

        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 8.1, 8.2, 8.3, 8.4
        """
        try:
            self.logger.info(
                "Updating user notification preferences", user_id=str(user_id), source=source
            )

            # Validate the updates first
            validation_result = self.validate_preferences(updates)
            if not validation_result.is_valid:
                raise ValidationError(
                    "Invalid preference updates",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"errors": validation_result.errors},
                )

            # Ensure user has preferences (create if not exists)
            old_preferences = await self.preferences_repo.get_by_user_id(user_id)
            if not old_preferences:
                self.logger.info("Creating default preferences before update", user_id=str(user_id))
                old_preferences = await self.create_default_preferences(user_id)

            # Convert request to update data
            update_data = {}
            changed_fields = []

            if updates.frequency is not None:
                update_data["frequency"] = updates.frequency
                changed_fields.append("frequency")
            if updates.notification_time is not None:
                update_data["notification_time"] = updates.notification_time
                changed_fields.append("notification_time")
            if updates.notification_day_of_week is not None:
                update_data["notification_day_of_week"] = updates.notification_day_of_week
                changed_fields.append("notification_day_of_week")
            if updates.notification_day_of_month is not None:
                update_data["notification_day_of_month"] = updates.notification_day_of_month
                changed_fields.append("notification_day_of_month")
            if updates.timezone is not None:
                update_data["timezone"] = updates.timezone
                changed_fields.append("timezone")
            if updates.dm_enabled is not None:
                update_data["dm_enabled"] = updates.dm_enabled
                changed_fields.append("dm_enabled")
            if updates.email_enabled is not None:
                update_data["email_enabled"] = updates.email_enabled
                changed_fields.append("email_enabled")

            # If no fields to update, return existing preferences
            if not update_data:
                self.logger.info(
                    "No fields to update, returning existing preferences", user_id=str(user_id)
                )
                return old_preferences

            # Update preferences
            updated_preferences = await self.preferences_repo.update_by_user_id(
                user_id, update_data
            )

            # Emit preference change event for synchronization
            if changed_fields:
                event = PreferenceChangeEvent(
                    user_id=user_id,
                    old_preferences=old_preferences,
                    new_preferences=updated_preferences,
                    changed_fields=changed_fields,
                    source=source,
                )
                await self.event_system.publish("preference_changed", event)

            self.logger.info(
                "Successfully updated user notification preferences",
                user_id=str(user_id),
                updated_fields=changed_fields,
                source=source,
            )

            return updated_preferences

        except ValidationError:
            raise
        except Exception as e:
            self._handle_error(
                e,
                "Failed to update user notification preferences",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={
                    "user_id": str(user_id),
                    "updates": updates.model_dump(),
                    "source": source,
                },
            )

    async def create_default_preferences(
        self, user_id: UUID, source: str = "system"
    ) -> UserNotificationPreferences:
        """
        Create default notification preferences for a user.

        Default values:
        - frequency: weekly (every Friday)
        - notification_time: 18:00 (6 PM)
        - timezone: Asia/Taipei
        - dm_enabled: true
        - email_enabled: false

        Args:
            user_id: UUID of the user
            source: Source of the creation (system, web, discord)

        Returns:
            UserNotificationPreferences: Created default preferences

        Raises:
            ServiceError: If database operation fails

        Requirements: 2.1, 2.2, 2.3, 2.4, 8.1, 8.2, 8.3, 8.4
        """
        try:
            self.logger.info(
                "Creating default notification preferences", user_id=str(user_id), source=source
            )

            # Check if preferences already exist
            existing_preferences = await self.preferences_repo.get_by_user_id(user_id)
            if existing_preferences:
                self.logger.info(
                    "Preferences already exist, returning existing", user_id=str(user_id)
                )
                return existing_preferences

            # Create default preferences
            preferences = await self.preferences_repo.create_default_for_user(user_id)

            # Emit preference change event for new preferences
            event = PreferenceChangeEvent(
                user_id=user_id,
                old_preferences=None,  # No previous preferences
                new_preferences=preferences,
                changed_fields=[
                    "frequency",
                    "notification_time",
                    "timezone",
                    "dm_enabled",
                    "email_enabled",
                ],
                source=source,
            )
            await self.event_system.publish("preference_changed", event)

            self.logger.info(
                "Successfully created default notification preferences",
                user_id=str(user_id),
                frequency=preferences.frequency,
                notification_time=str(preferences.notification_time),
                timezone=preferences.timezone,
                source=source,
            )

            return preferences

        except Exception as e:
            self._handle_error(
                e,
                "Failed to create default notification preferences",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={"user_id": str(user_id), "source": source},
            )

    def validate_preferences(
        self,
        preferences: UpdateUserNotificationPreferencesRequest
        | CreateUserNotificationPreferencesRequest,
    ) -> ValidationResult:
        """
        Validate notification preference settings.

        Validates:
        - Frequency: must be daily, weekly, monthly, or disabled
        - Time format: must be HH:MM with valid hours (0-23) and minutes (0-59)
        - Timezone: must be valid IANA timezone identifier

        Args:
            preferences: Preferences to validate

        Returns:
            ValidationResult: Validation result with errors if any

        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
        """
        errors = []

        try:
            # Validate frequency
            if hasattr(preferences, "frequency") and preferences.frequency is not None:
                valid_frequencies = ["daily", "weekly", "monthly", "disabled"]
                if preferences.frequency not in valid_frequencies:
                    errors.append(
                        f"Invalid frequency '{preferences.frequency}'. Must be one of: {', '.join(valid_frequencies)}"
                    )

            # Validate notification_time
            if (
                hasattr(preferences, "notification_time")
                and preferences.notification_time is not None
            ):
                time_str = preferences.notification_time
                if not isinstance(time_str, str) or ":" not in time_str:
                    errors.append("notification_time must be in HH:MM format")
                else:
                    try:
                        hour, minute = time_str.split(":")
                        hour_int = int(hour)
                        minute_int = int(minute)

                        if not (0 <= hour_int <= 23):
                            errors.append(f"Invalid hour '{hour_int}'. Must be between 0 and 23")
                        if not (0 <= minute_int <= 59):
                            errors.append(
                                f"Invalid minute '{minute_int}'. Must be between 0 and 59"
                            )
                    except ValueError:
                        errors.append(
                            "notification_time must contain valid integers in HH:MM format"
                        )

            # Validate timezone
            if hasattr(preferences, "timezone") and preferences.timezone is not None:
                timezone = preferences.timezone
                if not TimezoneConverter.is_valid_timezone(timezone):
                    errors.append(
                        f"Invalid timezone identifier '{timezone}'. Must be a valid IANA timezone"
                    )

            # Validate boolean fields
            if hasattr(preferences, "dm_enabled") and preferences.dm_enabled is not None:
                if not isinstance(preferences.dm_enabled, bool):
                    errors.append("dm_enabled must be a boolean value")

            if hasattr(preferences, "email_enabled") and preferences.email_enabled is not None:
                if not isinstance(preferences.email_enabled, bool):
                    errors.append("email_enabled must be a boolean value")

        except Exception as e:
            self.logger.error("Error during preference validation", error=str(e))
            errors.append(f"Validation error: {str(e)}")

        is_valid = len(errors) == 0

        self.logger.info(
            "Preference validation completed",
            is_valid=is_valid,
            error_count=len(errors),
        )

        return ValidationResult(is_valid=is_valid, errors=errors)

    async def delete_user_preferences(self, user_id: UUID) -> None:
        """
        Delete user's notification preferences.

        Args:
            user_id: UUID of the user

        Raises:
            ServiceError: If database operation fails
        """
        try:
            self.logger.info("Deleting user notification preferences", user_id=str(user_id))

            # Get preferences to ensure they exist
            preferences = await self.preferences_repo.get_by_user_id(user_id)
            if not preferences:
                self.logger.info("No preferences found to delete", user_id=str(user_id))
                return

            # Delete preferences
            await self.preferences_repo.delete(preferences.id)

            self.logger.info(
                "Successfully deleted user notification preferences", user_id=str(user_id)
            )

        except Exception as e:
            self._handle_error(
                e,
                "Failed to delete user notification preferences",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={"user_id": str(user_id)},
            )

    async def get_users_with_frequency(self, frequency: str) -> list[UserNotificationPreferences]:
        """
        Get all users with a specific notification frequency.

        Args:
            frequency: Notification frequency to filter by

        Returns:
            List of UserNotificationPreferences with the specified frequency

        Raises:
            ServiceError: If database operation fails
        """
        try:
            self.logger.info("Getting users with frequency", frequency=frequency)

            # Validate frequency
            valid_frequencies = ["daily", "weekly", "monthly", "disabled"]
            if frequency not in valid_frequencies:
                raise ValidationError(
                    f"Invalid frequency '{frequency}'. Must be one of: {', '.join(valid_frequencies)}",
                    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
                    details={"frequency": frequency, "valid_frequencies": valid_frequencies},
                )

            # Get users with the specified frequency
            users = await self.preferences_repo.list_by_field("frequency", frequency)

            self.logger.info(
                "Retrieved users with frequency",
                frequency=frequency,
                user_count=len(users),
            )

            return users

        except ValidationError:
            raise
        except Exception as e:
            self._handle_error(
                e,
                "Failed to get users with frequency",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={"frequency": frequency},
            )
