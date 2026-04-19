"""
Notification Settings Service

This module provides the NotificationSettingsService class for managing
user notification preferences and settings.

Requirements: Notification management, user preferences
"""

from uuid import UUID

from app.core.errors import ErrorCode, ValidationError
from app.core.logger import get_logger
from app.schemas.notification import (
    NotificationSettings,
    QuietHours,
    UpdateNotificationSettingsRequest,
)
from app.services.base import BaseService
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)


class NotificationSettingsService(BaseService):
    """
    Service for managing user notification settings.

    This service handles:
    - Retrieving user notification preferences
    - Updating notification settings
    - Managing feed-specific notification settings
    """

    def __init__(self, supabase_service: SupabaseService):
        """
        Initialize the NotificationSettingsService.

        Args:
            supabase_service: Supabase service for database operations
        """
        super().__init__()
        self.supabase_service = supabase_service
        self.logger = get_logger(f"{__name__}.NotificationSettingsService")

    async def get_notification_settings(self, user_id: UUID) -> NotificationSettings:
        """
        Get user's notification settings.

        Args:
            user_id: UUID of the user

        Returns:
            NotificationSettings: User's notification preferences

        Raises:
            ServiceError: If database operation fails
        """
        try:
            self.logger.info("Getting notification settings", user_id=str(user_id))

            # Get user's data from database
            user_data = await self._get_user_data(user_id)
            discord_id = user_data.get("discord_id")

            if not discord_id:
                # Return default settings if user not found
                return self._get_default_settings()

            # Get DM notification setting from database
            dm_enabled = user_data.get("dm_notifications_enabled", True)

            # Get additional settings from database (with defaults)
            frequency = user_data.get("notification_frequency", "immediate")
            min_tinkering_index = user_data.get("min_tinkering_index", 3)
            quiet_hours_enabled = user_data.get("quiet_hours_enabled", False)
            quiet_hours_start = user_data.get("quiet_hours_start", "22:00")
            quiet_hours_end = user_data.get("quiet_hours_end", "08:00")

            # Create settings based on actual database data
            settings = NotificationSettings(
                enabled=True,  # Global toggle - always enabled for now
                dm_enabled=dm_enabled,
                email_enabled=False,  # Not implemented yet
                frequency=frequency,
                quiet_hours=QuietHours(
                    enabled=quiet_hours_enabled, start=quiet_hours_start, end=quiet_hours_end
                ),
                min_tinkering_index=min_tinkering_index,
                feed_settings=[],
                channels=["dm", "in-app"] if dm_enabled else ["in-app"],
            )

            self.logger.info(
                "Retrieved notification settings", user_id=str(user_id), dm_enabled=dm_enabled
            )
            return settings

        except Exception as e:
            self._handle_error(
                e,
                "Failed to get notification settings",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={"user_id": str(user_id)},
            )

    async def update_notification_settings(
        self, user_id: UUID, updates: UpdateNotificationSettingsRequest
    ) -> NotificationSettings:
        """
        Update user's notification settings.

        Args:
            user_id: UUID of the user
            updates: Settings to update

        Returns:
            NotificationSettings: Updated notification settings

        Raises:
            ServiceError: If database operation fails
        """
        try:
            self.logger.info("Updating notification settings", user_id=str(user_id))

            # Get user's Discord ID
            user_data = await self._get_user_data(user_id)
            discord_id = user_data.get("discord_id")

            if not discord_id:
                raise ValidationError(
                    "User not found",
                    error_code=ErrorCode.RESOURCE_NOT_FOUND,
                    details={"user_id": str(user_id)},
                )

            # Update DM notification setting if provided
            if updates.dm_enabled is not None:
                await self.supabase_service.update_notification_settings(
                    discord_id, updates.dm_enabled
                )

            # Update other settings in the database
            update_data = {}

            if updates.frequency is not None:
                update_data["notification_frequency"] = updates.frequency
                self.logger.info(
                    "Updating frequency setting", user_id=str(user_id), frequency=updates.frequency
                )

            if updates.quiet_hours is not None:
                update_data["quiet_hours_enabled"] = updates.quiet_hours.enabled
                update_data["quiet_hours_start"] = updates.quiet_hours.start
                update_data["quiet_hours_end"] = updates.quiet_hours.end
                self.logger.info(
                    "Updating quiet hours setting",
                    user_id=str(user_id),
                    quiet_hours=updates.quiet_hours,
                )

            if updates.min_tinkering_index is not None:
                update_data["min_tinkering_index"] = updates.min_tinkering_index
                self.logger.info(
                    "Updating min tinkering index",
                    user_id=str(user_id),
                    min_tinkering_index=updates.min_tinkering_index,
                )

            # Apply updates to database if there are any
            if update_data:
                response = (
                    self.supabase_service.client.table("users")
                    .update(update_data)
                    .eq("id", str(user_id))
                    .execute()
                )

                if not response.data:
                    self.logger.warning("No rows updated", user_id=str(user_id))
                else:
                    self.logger.info(
                        "Successfully updated user settings",
                        user_id=str(user_id),
                        updated_fields=list(update_data.keys()),
                    )

            # Return updated settings
            updated_settings = await self.get_notification_settings(user_id)

            self.logger.info("Updated notification settings", user_id=str(user_id))
            return updated_settings

        except ValidationError:
            raise
        except Exception as e:
            self._handle_error(
                e,
                "Failed to update notification settings",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={"user_id": str(user_id)},
            )

    async def send_test_notification(self, user_id: UUID) -> None:
        """
        Send a test notification to the user.

        Args:
            user_id: UUID of the user

        Raises:
            ServiceError: If operation fails
        """
        try:
            self.logger.info("Sending test notification", user_id=str(user_id))

            # Get user's Discord ID
            user_data = await self._get_user_data(user_id)
            discord_id = user_data.get("discord_id")

            if not discord_id:
                raise ValidationError(
                    "User not found",
                    error_code=ErrorCode.RESOURCE_NOT_FOUND,
                    details={"user_id": str(user_id)},
                )

            # Check if DM notifications are enabled
            dm_enabled = await self.supabase_service.get_notification_settings(discord_id)

            if not dm_enabled:
                raise ValidationError(
                    "DM notifications are disabled",
                    error_code=ErrorCode.VALIDATION_BUSINESS_RULE,
                    details={"user_id": str(user_id)},
                )

            # For now, just log the test notification
            # In the future, this could actually send a test DM via Discord bot
            self.logger.info(
                "Test notification would be sent", user_id=str(user_id), discord_id=discord_id
            )

        except ValidationError:
            raise
        except Exception as e:
            self._handle_error(
                e,
                "Failed to send test notification",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={"user_id": str(user_id)},
            )

    # Private helper methods

    async def _get_user_data(self, user_id: UUID) -> dict:
        """Get user data from database."""
        try:
            # Query the users table to get actual user data
            response = (
                self.supabase_service.client.table("users")
                .select(
                    "id, discord_id, dm_notifications_enabled, notification_frequency, min_tinkering_index, quiet_hours_enabled, quiet_hours_start, quiet_hours_end"
                )
                .eq("id", str(user_id))
                .execute()
            )

            if not response.data:
                self.logger.warning("User not found in database", user_id=str(user_id))
                return {}

            user_data = response.data[0]
            return {
                "id": user_data["id"],
                "discord_id": user_data["discord_id"],
                "dm_notifications_enabled": user_data.get("dm_notifications_enabled", True),
                "notification_frequency": user_data.get("notification_frequency", "immediate"),
                "min_tinkering_index": user_data.get("min_tinkering_index", 3),
                "quiet_hours_enabled": user_data.get("quiet_hours_enabled", False),
                "quiet_hours_start": user_data.get("quiet_hours_start", "22:00"),
                "quiet_hours_end": user_data.get("quiet_hours_end", "08:00"),
            }
        except Exception as e:
            self.logger.warning("Failed to get user data", user_id=str(user_id), error=str(e))
            return {}

    def _get_default_settings(self) -> NotificationSettings:
        """Get default notification settings."""
        return NotificationSettings(
            enabled=True,  # Global toggle - always enabled for now
            dm_enabled=True,
            email_enabled=False,
            frequency="immediate",
            quiet_hours=QuietHours(enabled=False, start="22:00", end="08:00"),
            min_tinkering_index=3,
            feed_settings=[],
            channels=["dm", "in-app"],
        )
