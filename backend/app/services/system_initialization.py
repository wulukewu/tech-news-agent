"""
System Initialization Service

This module provides system initialization functionality for the personalized
notification system, including migrating existing users to default preferences
and starting background cleanup processes.

Requirements: 2.4, 10.5 (Task 9.2)
"""

import asyncio
from typing import Dict
from uuid import UUID

from app.core.logger import get_logger
from app.repositories.user_notification_preferences import (
    UserNotificationPreferencesRepository,
)
from app.services.base import BaseService
from app.services.notification_system_integration import (
    get_notification_system_integration,
)
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)


class SystemInitializationService(BaseService):
    """
    Service for initializing the personalized notification system.

    This service handles:
    - Migrating existing users to default notification preferences
    - Initializing dynamic scheduling for existing users
    - Starting background cleanup processes
    - System health validation

    Requirements: 2.4, 10.5
    """

    def __init__(self, supabase_service: SupabaseService):
        """
        Initialize the system initialization service.

        Args:
            supabase_service: Supabase service for database operations
        """
        super().__init__()
        self.supabase_service = supabase_service
        self.preferences_repo = UserNotificationPreferencesRepository(supabase_service.client)
        self.logger = get_logger(f"{__name__}.SystemInitializationService")

    async def initialize_system(self) -> Dict:
        """
        Initialize the entire personalized notification system.

        This method:
        1. Migrates existing users to default preferences
        2. Initializes dynamic scheduling for all users
        3. Starts background cleanup processes
        4. Validates system health

        Returns:
            Dict: Initialization results and statistics
        """
        try:
            self.logger.info("Starting system initialization for personalized notifications")

            results = {
                "success": True,
                "migration": {},
                "scheduling": {},
                "cleanup": {},
                "validation": {},
            }

            # Step 1: Migrate existing users to default preferences
            migration_results = await self._migrate_existing_users()
            results["migration"] = migration_results

            # Step 2: Initialize dynamic scheduling for users with preferences
            scheduling_results = await self._initialize_user_scheduling()
            results["scheduling"] = scheduling_results

            # Step 3: Start background cleanup processes
            cleanup_results = await self._start_background_cleanup()
            results["cleanup"] = cleanup_results

            # Step 4: Validate system health
            validation_results = await self._validate_system_health()
            results["validation"] = validation_results

            # Determine overall success
            results["success"] = all(
                [
                    migration_results.get("success", False),
                    scheduling_results.get("success", False),
                    cleanup_results.get("success", False),
                    validation_results.get("success", False),
                ]
            )

            self.logger.info(
                "System initialization completed",
                success=results["success"],
                migrated_users=migration_results.get("migrated_count", 0),
                scheduled_users=scheduling_results.get("scheduled_count", 0),
            )

            return results

        except Exception as e:
            self.logger.error("Failed to initialize system", error=str(e), exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "migration": {},
                "scheduling": {},
                "cleanup": {},
                "validation": {},
            }

    async def _migrate_existing_users(self) -> Dict:
        """
        Migrate existing users to default notification preferences.

        Returns:
            Dict: Migration results and statistics
        """
        try:
            self.logger.info("Starting migration of existing users to default preferences")

            # Get all users from the database
            users_response = self.supabase_service.client.table("users").select("id").execute()

            if not users_response.data:
                self.logger.info("No users found in database")
                return {
                    "success": True,
                    "total_users": 0,
                    "migrated_count": 0,
                    "already_migrated": 0,
                    "failed_count": 0,
                }

            total_users = len(users_response.data)
            migrated_count = 0
            already_migrated = 0
            failed_count = 0

            self.logger.info(f"Found {total_users} users to check for migration")

            # Get integration service
            integration_service = get_notification_system_integration()
            if not integration_service:
                raise RuntimeError("Notification system integration not available")

            # Process users in batches to avoid overwhelming the system
            batch_size = 50
            for i in range(0, total_users, batch_size):
                batch_users = users_response.data[i : i + batch_size]

                self.logger.info(
                    f"Processing user batch {i // batch_size + 1}: "
                    f"users {i + 1}-{min(i + batch_size, total_users)} of {total_users}"
                )

                # Process batch concurrently
                batch_tasks = []
                for user_data in batch_users:
                    user_id = UUID(user_data["id"])
                    batch_tasks.append(self._migrate_single_user(user_id, integration_service))

                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                # Count results
                for result in batch_results:
                    if isinstance(result, Exception):
                        failed_count += 1
                        self.logger.error(f"Failed to migrate user: {result}")
                    elif result == "migrated":
                        migrated_count += 1
                    elif result == "already_migrated":
                        already_migrated += 1
                    else:
                        failed_count += 1

                # Small delay between batches to avoid overwhelming the system
                if i + batch_size < total_users:
                    await asyncio.sleep(0.1)

            self.logger.info(
                f"User migration completed: "
                f"Total: {total_users}, "
                f"Migrated: {migrated_count}, "
                f"Already migrated: {already_migrated}, "
                f"Failed: {failed_count}"
            )

            return {
                "success": True,
                "total_users": total_users,
                "migrated_count": migrated_count,
                "already_migrated": already_migrated,
                "failed_count": failed_count,
            }

        except Exception as e:
            self.logger.error("Failed to migrate existing users", error=str(e), exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "total_users": 0,
                "migrated_count": 0,
                "already_migrated": 0,
                "failed_count": 0,
            }

    async def _migrate_single_user(self, user_id: UUID, integration_service) -> str:
        """
        Migrate a single user to default preferences.

        Args:
            user_id: User ID to migrate
            integration_service: Integration service instance

        Returns:
            str: Migration result ("migrated", "already_migrated", or "failed")
        """
        try:
            # Check if user already has preferences
            existing_preferences = await self.preferences_repo.get_by_user_id(user_id)

            if existing_preferences:
                return "already_migrated"

            # Initialize notifications for the user
            success = await integration_service.initialize_user_notifications(user_id)

            if success:
                return "migrated"
            else:
                return "failed"

        except Exception as e:
            self.logger.error(f"Failed to migrate user {user_id}: {e}")
            return "failed"

    async def _initialize_user_scheduling(self) -> Dict:
        """
        Initialize dynamic scheduling for all users with preferences.

        Returns:
            Dict: Scheduling initialization results
        """
        try:
            self.logger.info("Starting dynamic scheduling initialization for users")

            # Get integration service
            integration_service = get_notification_system_integration()
            if not integration_service:
                raise RuntimeError("Notification system integration not available")

            # Get all users with notification preferences
            users_with_preferences = await self.preferences_repo.get_all_active_preferences()

            if not users_with_preferences:
                self.logger.info("No users with preferences found")
                return {
                    "success": True,
                    "total_users": 0,
                    "scheduled_count": 0,
                    "skipped_count": 0,
                    "failed_count": 0,
                }

            total_users = len(users_with_preferences)
            scheduled_count = 0
            skipped_count = 0
            failed_count = 0

            self.logger.info(f"Found {total_users} users with preferences to schedule")

            # Process users in batches
            batch_size = 25  # Smaller batch size for scheduling operations
            for i in range(0, total_users, batch_size):
                batch_users = users_with_preferences[i : i + batch_size]

                self.logger.info(
                    f"Processing scheduling batch {i // batch_size + 1}: "
                    f"users {i + 1}-{min(i + batch_size, total_users)} of {total_users}"
                )

                # Process batch concurrently
                batch_tasks = []
                for preferences in batch_users:
                    batch_tasks.append(
                        self._schedule_single_user(preferences.user_id, integration_service)
                    )

                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                # Count results
                for result in batch_results:
                    if isinstance(result, Exception):
                        failed_count += 1
                        self.logger.error(f"Failed to schedule user: {result}")
                    elif result == "scheduled":
                        scheduled_count += 1
                    elif result == "skipped":
                        skipped_count += 1
                    else:
                        failed_count += 1

                # Small delay between batches
                if i + batch_size < total_users:
                    await asyncio.sleep(0.2)

            self.logger.info(
                f"User scheduling initialization completed: "
                f"Total: {total_users}, "
                f"Scheduled: {scheduled_count}, "
                f"Skipped: {skipped_count}, "
                f"Failed: {failed_count}"
            )

            return {
                "success": True,
                "total_users": total_users,
                "scheduled_count": scheduled_count,
                "skipped_count": skipped_count,
                "failed_count": failed_count,
            }

        except Exception as e:
            self.logger.error("Failed to initialize user scheduling", error=str(e), exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "total_users": 0,
                "scheduled_count": 0,
                "skipped_count": 0,
                "failed_count": 0,
            }

    async def _schedule_single_user(self, user_id: UUID, integration_service) -> str:
        """
        Schedule notifications for a single user.

        Args:
            user_id: User ID to schedule
            integration_service: Integration service instance

        Returns:
            str: Scheduling result ("scheduled", "skipped", or "failed")
        """
        try:
            # Get user preferences to check if scheduling is needed
            preferences = await integration_service.preference_service.get_user_preferences(user_id)

            # Skip if notifications are disabled
            if preferences.frequency == "disabled":
                return "skipped"

            # Schedule notifications
            success = await integration_service.schedule_user_notifications(user_id)

            if success:
                return "scheduled"
            else:
                return "failed"

        except Exception as e:
            self.logger.error(f"Failed to schedule user {user_id}: {e}")
            return "failed"

    async def _start_background_cleanup(self) -> Dict:
        """
        Start background cleanup processes.

        Returns:
            Dict: Cleanup initialization results
        """
        try:
            self.logger.info("Starting background cleanup processes")

            # Get integration service
            integration_service = get_notification_system_integration()
            if not integration_service:
                raise RuntimeError("Notification system integration not available")

            # Run initial cleanup
            cleanup_results = await integration_service.cleanup_system_resources()

            self.logger.info(
                "Background cleanup processes started",
                overall_success=cleanup_results.get("overall_success", False),
            )

            return {
                "success": cleanup_results.get("overall_success", False),
                "results": cleanup_results,
            }

        except Exception as e:
            self.logger.error("Failed to start background cleanup", error=str(e), exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }

    async def _validate_system_health(self) -> Dict:
        """
        Validate system health after initialization.

        Returns:
            Dict: System health validation results
        """
        try:
            self.logger.info("Validating system health after initialization")

            # Get integration service
            integration_service = get_notification_system_integration()
            if not integration_service:
                raise RuntimeError("Notification system integration not available")

            # Get system health
            health = await integration_service.get_system_health()

            is_healthy = health.get("overall_status") == "healthy"

            self.logger.info(
                "System health validation completed",
                is_healthy=is_healthy,
                overall_status=health.get("overall_status"),
            )

            return {
                "success": is_healthy,
                "health": health,
            }

        except Exception as e:
            self.logger.error("Failed to validate system health", error=str(e), exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }


async def initialize_personalized_notification_system(supabase_service: SupabaseService) -> Dict:
    """
    Initialize the personalized notification system.

    This function should be called during application startup to:
    - Migrate existing users to default preferences
    - Initialize dynamic scheduling
    - Start background cleanup processes
    - Validate system health

    Args:
        supabase_service: Supabase service for database operations

    Returns:
        Dict: Initialization results and statistics
    """
    initialization_service = SystemInitializationService(supabase_service)
    return await initialization_service.initialize_system()
