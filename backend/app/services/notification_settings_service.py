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

            # Get user's Discord ID first
            user_data = await self._get_user_data(user_id)
            discord_id = user_data.get("discord_id")

            if not discord_id:
                # Return default settings if user not found
                return self._get_default_settings()

            # Get DM notification setting from existing service
            dm_enabled = await self.supabase_service.get_notification_settings(discord_id)

            # For now, return basic settings based on existing DM setting
            # In the future, this could be expanded to read from a dedicated user_notification_settings table
            settings = NotificationSettings(
                enabled=dm_enabled,
                dm_enabled=dm_enabled,
                email_enabled=False,  # Not implemented yet
                frequency="immediate",
                quiet_hours=QuietHours(enabled=False, start="22:00", end="08:00"),
                min_tinkering_index=3,
                feed_settings=[],
                channels=["dm", "in-app"] if dm_enabled else ["in-app"],
            )

            self.logger.info("Retrieved notification settings", user_id=str(user_id))
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

            # For now, we only support DM notifications
            # In the future, this could be expanded to support more settings

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
            # This would typically query the users table
            # For now, we'll use a placeholder implementation
            # In a real implementation, this would be:
            # user = await self.user_repository.get_by_id(user_id)

            # Placeholder: assume user exists with a Discord ID
            # This should be replaced with actual database query
            return {
                "id": str(user_id),
                "discord_id": f"discord_{user_id}",  # Placeholder
            }
        except Exception as e:
            self.logger.warning("Failed to get user data", user_id=str(user_id), error=str(e))
            return {}

    def _get_default_settings(self) -> NotificationSettings:
        """Get default notification settings."""
        return NotificationSettings(
            enabled=True,
            dm_enabled=True,
            email_enabled=False,
            frequency="immediate",
            quiet_hours=QuietHours(enabled=False, start="22:00", end="08:00"),
            min_tinkering_index=3,
            feed_settings=[],
            channels=["dm", "in-app"],
        )
