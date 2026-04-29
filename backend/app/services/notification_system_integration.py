"""
Notification System Integration Service

This module provides the NotificationSystemIntegration class that wires all components
together to create a cohesive personalized notification system. It handles proper
dependency injection, error propagation, and service coordination.

Requirements: All requirements integration (Task 9.1)
"""

from typing import Dict, List, Optional
from uuid import UUID

from app.core.errors import ErrorCode
from app.core.logger import get_logger
from app.repositories.user_notification_preferences import (
    UserNotificationPreferences,
    UserNotificationPreferencesRepository,
)
from app.services.base import BaseService
from app.services.dynamic_scheduler import DynamicScheduler
from app.services.lock_manager import LockManager
from app.services.notification_service import (
    NotificationChannel,
    NotificationResult,
    NotificationService,
)
from app.services.preference_event_system import (
    get_preference_event_system,
)
from app.services.preference_service import PreferenceService
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)


from app.services._nsi_health_mixin import NsiHealthMixin


class NotificationSystemIntegration(BaseService, NsiHealthMixin):
    """
    Integration service that wires all notification system components together.

    This service provides:
    - Centralized service initialization and dependency injection
    - Coordinated notification delivery across all channels
    - Error propagation and handling across service boundaries
    - System health monitoring and diagnostics
    - Unified interface for notification operations

    Components integrated:
    - PreferenceService: User preference management
    - DynamicScheduler: Individual user notification scheduling
    - NotificationService: Multi-channel notification delivery
    - LockManager: Atomic notification locking for multi-instance coordination

    Requirements: All requirements integration
    """

    def __init__(
        self,
        supabase_service: Optional[SupabaseService] = None,
        dynamic_scheduler: Optional[DynamicScheduler] = None,
        bot_client=None,
    ):
        """
        Initialize the notification system integration.

        Args:
            supabase_service: Supabase service for database operations
            dynamic_scheduler: Dynamic scheduler for notification jobs
            bot_client: Discord bot client for DM notifications
        """
        super().__init__()
        self.logger = get_logger(f"{__name__}.NotificationSystemIntegration")

        # Initialize core services
        self.supabase_service = supabase_service or SupabaseService()
        self.dynamic_scheduler = dynamic_scheduler
        self.bot_client = bot_client

        # Initialize repositories
        self.preferences_repo = UserNotificationPreferencesRepository(self.supabase_service.client)

        # Initialize services with proper dependency injection
        self.preference_service = PreferenceService(self.preferences_repo)
        self.lock_manager = LockManager(self.supabase_service.client)
        self.notification_service = NotificationService(
            bot=self.bot_client,
            supabase_service=self.supabase_service,
            lock_manager=self.lock_manager,
        )

        # Initialize event system
        self.event_system = get_preference_event_system()

        # Subscribe to preference change events for scheduler coordination
        self.event_system.subscribe("preference_changed", self._handle_preference_change)

        self.logger.info("Notification system integration initialized successfully")

    async def send_user_notification(
        self,
        user_id: UUID,
        notification_type: str = "weekly_digest",
        subject: str = "Tech News Digest",
        articles: Optional[List] = None,
    ) -> List[NotificationResult]:
        """
        Send notification to a user across all enabled channels.

        This method coordinates the entire notification delivery process:
        1. Gets user preferences to determine enabled channels
        2. Uses LockManager to prevent duplicate notifications
        3. Sends notifications via NotificationService
        4. Handles errors and provides comprehensive results

        Args:
            user_id: User ID to send notification to
            notification_type: Type of notification for locking
            subject: Notification subject/title
            articles: Articles to include in notification

        Returns:
            List[NotificationResult]: Results for each channel attempt
        """
        try:
            self.logger.info(
                "Starting coordinated user notification",
                user_id=str(user_id),
                notification_type=notification_type,
                subject=subject,
            )

            # Get user preferences to determine enabled channels
            preferences = await self.preference_service.get_user_preferences(user_id)

            # Skip if notifications are disabled
            if preferences.frequency == "disabled":
                self.logger.info(
                    "Notifications disabled for user",
                    user_id=str(user_id),
                    frequency=preferences.frequency,
                )
                return [NotificationResult(False, "all", "Notifications disabled")]

            # Determine enabled channels based on preferences
            channels = []
            if preferences.dm_enabled:
                channels.append(NotificationChannel("discord_dm", True))
            if preferences.email_enabled:
                channels.append(NotificationChannel("email", True))

            if not channels:
                self.logger.info(
                    "No notification channels enabled for user",
                    user_id=str(user_id),
                    dm_enabled=preferences.dm_enabled,
                    email_enabled=preferences.email_enabled,
                )
                return [NotificationResult(False, "all", "No channels enabled")]

            # Send notification via NotificationService (includes locking)
            results = await self.notification_service.send_notification(
                user_id=user_id,
                channels=channels,
                subject=subject,
                articles=articles,
                notification_type=notification_type,
            )

            self.logger.info(
                "Coordinated user notification completed",
                user_id=str(user_id),
                successful_channels=[r.channel for r in results if r.success],
                failed_channels=[r.channel for r in results if not r.success],
            )

            return results

        except Exception as e:
            self._handle_error(
                e,
                "Failed to send coordinated user notification",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={
                    "user_id": str(user_id),
                    "notification_type": notification_type,
                    "subject": subject,
                },
            )

    async def schedule_user_notifications(self, user_id: UUID) -> bool:
        """
        Schedule notifications for a user based on their preferences.

        Args:
            user_id: User ID to schedule notifications for

        Returns:
            bool: True if scheduling was successful, False otherwise
        """
        try:
            if not self.dynamic_scheduler:
                self.logger.warning(
                    "Dynamic scheduler not available for scheduling", user_id=str(user_id)
                )
                return False

            self.logger.info("Scheduling user notifications", user_id=str(user_id))

            # Get user preferences
            preferences = await self.preference_service.get_user_preferences(user_id)

            # Schedule notifications via DynamicScheduler
            await self.dynamic_scheduler.schedule_user_notification(user_id, preferences)

            self.logger.info(
                "Successfully scheduled user notifications",
                user_id=str(user_id),
                frequency=preferences.frequency,
                notification_time=str(preferences.notification_time),
                timezone=preferences.timezone,
            )

            return True

        except Exception as e:
            self.logger.error(
                "Failed to schedule user notifications", user_id=str(user_id), error=str(e)
            )
            return False

    async def cancel_user_notifications(self, user_id: UUID) -> bool:
        """
        Cancel all scheduled notifications for a user.

        Args:
            user_id: User ID to cancel notifications for

        Returns:
            bool: True if cancellation was successful, False otherwise
        """
        try:
            if not self.dynamic_scheduler:
                self.logger.warning(
                    "Dynamic scheduler not available for cancellation", user_id=str(user_id)
                )
                return False

            self.logger.info("Cancelling user notifications", user_id=str(user_id))

            # Cancel notifications via DynamicScheduler
            await self.dynamic_scheduler.cancel_user_notification(user_id)

            self.logger.info("Successfully cancelled user notifications", user_id=str(user_id))
            return True

        except Exception as e:
            self.logger.error(
                "Failed to cancel user notifications", user_id=str(user_id), error=str(e)
            )
            return False

    async def update_user_preferences(
        self, user_id: UUID, updates: Dict, source: str = "system"
    ) -> Optional[UserNotificationPreferences]:
        """
        Update user preferences with automatic scheduler coordination.

        Args:
            user_id: User ID to update preferences for
            updates: Preference updates to apply
            source: Source of the update (web, discord, system)

        Returns:
            UserNotificationPreferences: Updated preferences, or None if failed
        """
        try:
            self.logger.info(
                "Updating user preferences with scheduler coordination",
                user_id=str(user_id),
                updates=updates,
                source=source,
            )

            # Convert dict to update request object
            from app.schemas.user_notification_preferences import (
                UpdateUserNotificationPreferencesRequest,
            )

            update_request = UpdateUserNotificationPreferencesRequest(**updates)

            # Update preferences via PreferenceService (triggers events automatically)
            updated_preferences = await self.preference_service.update_preferences(
                user_id, update_request, source
            )

            self.logger.info(
                "Successfully updated user preferences with scheduler coordination",
                user_id=str(user_id),
                source=source,
            )

            return updated_preferences

        except Exception as e:
            self.logger.error(
                "Failed to update user preferences",
                user_id=str(user_id),
                updates=updates,
                source=source,
                error=str(e),
            )
            return None

    async def initialize_user_notifications(self, user_id: UUID) -> bool:
        """
        Initialize notifications for a new user with default preferences.

        Args:
            user_id: User ID to initialize notifications for

        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            self.logger.info("Initializing user notifications", user_id=str(user_id))

            # Create default preferences (triggers events automatically)
            preferences = await self.preference_service.create_default_preferences(
                user_id, source="system"
            )

            self.logger.info(
                "Successfully initialized user notifications",
                user_id=str(user_id),
                frequency=preferences.frequency,
                notification_time=str(preferences.notification_time),
                timezone=preferences.timezone,
            )

            return True

        except Exception as e:
            self.logger.error(
                "Failed to initialize user notifications", user_id=str(user_id), error=str(e)
            )
            return False

    async def get_user_notification_status(self, user_id: UUID) -> Dict:
        """
        Get comprehensive notification status for a user.

        Args:
            user_id: User ID to get status for

        Returns:
            Dict: Comprehensive notification status information
        """
        try:
            self.logger.debug("Getting user notification status", user_id=str(user_id))

            # Get user preferences
            preferences = await self.preference_service.get_user_preferences(user_id)

            # Get scheduler job info if available
            job_info = None
            if self.dynamic_scheduler:
                job_info = await self.dynamic_scheduler.get_user_job_info(user_id)

            # Get lock statistics
            lock_stats = await self.lock_manager.get_lock_statistics()

            status = {
                "user_id": str(user_id),
                "preferences": {
                    "frequency": preferences.frequency,
                    "notification_time": str(preferences.notification_time),
                    "timezone": preferences.timezone,
                    "dm_enabled": preferences.dm_enabled,
                    "email_enabled": preferences.email_enabled,
                },
                "scheduling": {
                    "is_scheduled": job_info is not None,
                    "next_run_time": job_info.get("next_run_time") if job_info else None,
                    "job_id": job_info.get("job_id") if job_info else None,
                },
                "system": {
                    "dynamic_scheduler_available": self.dynamic_scheduler is not None,
                    "lock_manager_stats": lock_stats,
                },
            }

            return status

        except Exception as e:
            self.logger.error(
                "Failed to get user notification status", user_id=str(user_id), error=str(e)
            )
            return {
                "user_id": str(user_id),
                "error": str(e),
                "preferences": None,
                "scheduling": {"is_scheduled": False},
                "system": {"dynamic_scheduler_available": False},
            }


_integration_service: Optional[NotificationSystemIntegration] = None


def get_notification_system_integration() -> Optional[NotificationSystemIntegration]:
    """
    Get the global notification system integration instance.

    Returns:
        NotificationSystemIntegration: Global integration service instance, or None if not initialized
    """
    return _integration_service


def initialize_notification_system_integration(
    supabase_service: Optional[SupabaseService] = None,
    dynamic_scheduler: Optional[DynamicScheduler] = None,
    bot_client=None,
) -> NotificationSystemIntegration:
    """
    Initialize the global notification system integration.

    Args:
        supabase_service: Supabase service for database operations
        dynamic_scheduler: Dynamic scheduler for notification jobs
        bot_client: Discord bot client for DM notifications

    Returns:
        NotificationSystemIntegration: Initialized integration service
    """
    global _integration_service
    _integration_service = NotificationSystemIntegration(
        supabase_service=supabase_service,
        dynamic_scheduler=dynamic_scheduler,
        bot_client=bot_client,
    )
    return _integration_service
