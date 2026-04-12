"""
Onboarding Service

This module provides the OnboardingService class for managing user onboarding
progress, including tracking steps, completion status, and skip functionality.

This service follows the repository pattern and depends on repository interfaces
for data access instead of directly accessing the database client.

Requirements: 1.4, 1.5, 1.6, 10.3, 10.6
Validates: Requirements 3.1, 3.2, 3.3
"""

from datetime import UTC, datetime
from uuid import UUID

from app.core.errors import ErrorCode
from app.core.logger import get_logger
from app.repositories.user_preferences import UserPreferencesRepository
from app.schemas.onboarding import OnboardingStatus
from app.services.base import BaseService

logger = get_logger(__name__)


class OnboardingService(BaseService):
    """
    Service for managing user onboarding progress and state.

    This service handles:
    - Retrieving onboarding status
    - Updating onboarding progress
    - Marking onboarding as completed or skipped
    - Resetting onboarding state

    This service uses the repository pattern for data access, depending on
    UserPreferencesRepository instead of directly accessing the database.

    Requirements: 1.4, 1.5, 1.6, 10.3, 10.6
    Validates: Requirements 3.1, 3.2, 3.3
    """

    def __init__(self, user_preferences_repo: UserPreferencesRepository):
        """
        Initialize the OnboardingService.

        Args:
            user_preferences_repo: Repository for user preferences data access
        """
        super().__init__()
        self.user_preferences_repo = user_preferences_repo
        self.logger = get_logger(f"{__name__}.OnboardingService")

    async def get_onboarding_status(self, user_id: UUID) -> OnboardingStatus:
        """
        Get the current onboarding status for a user.

        If the user doesn't have a preferences record, creates one with default values.

        Args:
            user_id: UUID of the user

        Returns:
            OnboardingStatus with current progress and state

        Raises:
            OnboardingServiceError: If database operation fails

        Requirements: 1.4, 10.3, 10.4
        """
        try:
            self.logger.info("Getting onboarding status", user_id=str(user_id))

            # Query user_preferences using repository
            prefs = await self.user_preferences_repo.get_by_user_id(user_id)

            # If no preferences exist, create default record
            if not prefs:
                self.logger.info(
                    "No preferences found, creating default record", user_id=str(user_id)
                )
                await self._create_default_preferences(user_id)

                # Return default status
                return OnboardingStatus(
                    onboarding_completed=False,
                    onboarding_step=None,
                    onboarding_skipped=False,
                    tooltip_tour_completed=False,
                    should_show_onboarding=True,  # New users should see onboarding
                )

            # Compute should_show_onboarding based on completion and skip states
            # Requirements 10.4, 10.5: Show onboarding only if NOT completed AND NOT skipped
            should_show = not prefs.onboarding_completed and not prefs.onboarding_skipped

            return OnboardingStatus(
                onboarding_completed=prefs.onboarding_completed,
                onboarding_step=prefs.onboarding_step,
                onboarding_skipped=prefs.onboarding_skipped,
                tooltip_tour_completed=prefs.tooltip_tour_completed,
                should_show_onboarding=should_show,
            )

        except Exception as e:
            self._handle_error(
                e,
                "Failed to get onboarding status",
                error_code=ErrorCode.DB_QUERY_FAILED,
                context={"user_id": str(user_id)},
            )

    async def update_onboarding_progress(self, user_id: UUID, step: str, completed: bool) -> None:
        """
        Update the user's onboarding progress.

        Sets the current onboarding step and optionally marks it as completed.
        If this is the first step, sets onboarding_started_at timestamp.

        Args:
            user_id: UUID of the user
            step: Current onboarding step (e.g., 'welcome', 'recommendations', 'complete')
            completed: Whether the step is completed

        Raises:
            OnboardingServiceError: If database operation fails

        Requirements: 1.4, 10.3
        """
        try:
            self.logger.info(
                "Updating onboarding progress", user_id=str(user_id), step=step, completed=completed
            )

            # Ensure preferences record exists
            await self._ensure_preferences_exist(user_id)

            # Prepare update data
            update_data = {
                "onboarding_step": step,
                "updated_at": datetime.now(UTC).isoformat(),
            }

            # If this is the first step, set started_at timestamp
            current_prefs = await self.user_preferences_repo.get_by_user_id(user_id)
            if current_prefs and not current_prefs.onboarding_started_at:
                update_data["onboarding_started_at"] = datetime.now(UTC).isoformat()

            # Update using repository
            await self.user_preferences_repo.update_by_user_id(user_id, update_data)

            self.logger.info(
                "Successfully updated onboarding progress", user_id=str(user_id), step=step
            )

        except Exception as e:
            self._handle_error(
                e,
                "Failed to update onboarding progress",
                error_code=ErrorCode.DB_QUERY_FAILED,
                context={"user_id": str(user_id), "step": step, "completed": completed},
            )

    async def mark_onboarding_completed(self, user_id: UUID) -> None:
        """
        Mark the user's onboarding as completed.

        Sets onboarding_completed to True and records the completion timestamp.

        Args:
            user_id: UUID of the user

        Raises:
            OnboardingServiceError: If database operation fails

        Requirements: 1.5, 10.3
        """
        try:
            self.logger.info("Marking onboarding as completed", user_id=str(user_id))

            # Ensure preferences record exists
            await self._ensure_preferences_exist(user_id)

            # Update the record
            update_data = {
                "onboarding_completed": True,
                "onboarding_completed_at": datetime.now(UTC).isoformat(),
                "onboarding_step": "complete",
                "updated_at": datetime.now(UTC).isoformat(),
            }

            await self.user_preferences_repo.update_by_user_id(user_id, update_data)

            self.logger.info("Successfully marked onboarding as completed", user_id=str(user_id))

        except Exception as e:
            self._handle_error(
                e,
                "Failed to mark onboarding as completed",
                error_code=ErrorCode.DB_QUERY_FAILED,
                context={"user_id": str(user_id)},
            )

    async def mark_onboarding_skipped(self, user_id: UUID) -> None:
        """
        Mark the user's onboarding as skipped.

        Sets onboarding_skipped to True so the onboarding modal won't be shown again.

        Args:
            user_id: UUID of the user

        Raises:
            OnboardingServiceError: If database operation fails

        Requirements: 1.6, 1.7, 10.3
        """
        try:
            self.logger.info("Marking onboarding as skipped", user_id=str(user_id))

            # Ensure preferences record exists
            await self._ensure_preferences_exist(user_id)

            # Update the record
            update_data = {
                "onboarding_skipped": True,
                "updated_at": datetime.now(UTC).isoformat(),
            }

            await self.user_preferences_repo.update_by_user_id(user_id, update_data)

            self.logger.info("Successfully marked onboarding as skipped", user_id=str(user_id))

        except Exception as e:
            self._handle_error(
                e,
                "Failed to mark onboarding as skipped",
                error_code=ErrorCode.DB_QUERY_FAILED,
                context={"user_id": str(user_id)},
            )

    async def reset_onboarding(self, user_id: UUID) -> None:
        """
        Reset the user's onboarding state.

        Clears all onboarding flags and timestamps, allowing the user to go through
        the onboarding flow again.

        Args:
            user_id: UUID of the user

        Raises:
            OnboardingServiceError: If database operation fails

        Requirements: 10.6, 10.7
        """
        try:
            self.logger.info("Resetting onboarding", user_id=str(user_id))

            # Ensure preferences record exists
            await self._ensure_preferences_exist(user_id)

            # Reset all onboarding-related fields
            update_data = {
                "onboarding_completed": False,
                "onboarding_step": None,
                "onboarding_skipped": False,
                "onboarding_started_at": None,
                "onboarding_completed_at": None,
                "updated_at": datetime.now(UTC).isoformat(),
            }

            await self.user_preferences_repo.update_by_user_id(user_id, update_data)

            self.logger.info("Successfully reset onboarding", user_id=str(user_id))

        except Exception as e:
            self._handle_error(
                e,
                "Failed to reset onboarding",
                error_code=ErrorCode.DB_QUERY_FAILED,
                context={"user_id": str(user_id)},
            )

    # Private helper methods

    async def _create_default_preferences(self, user_id: UUID) -> None:
        """
        Create a default preferences record for a user.

        Args:
            user_id: UUID of the user

        Raises:
            OnboardingServiceError: If creation fails
        """
        try:
            insert_data = {
                "user_id": str(user_id),
                "onboarding_completed": False,
                "onboarding_skipped": False,
                "tooltip_tour_completed": False,
                "tooltip_tour_skipped": False,
                "preferred_language": "zh-TW",
            }

            await self.user_preferences_repo.create(insert_data)

            self.logger.info("Created default preferences", user_id=str(user_id))

        except Exception as e:
            self._handle_error(
                e,
                "Failed to create default preferences",
                error_code=ErrorCode.DB_QUERY_FAILED,
                context={"user_id": str(user_id)},
            )

    async def _ensure_preferences_exist(self, user_id: UUID) -> None:
        """
        Ensure a preferences record exists for the user, creating one if needed.

        Args:
            user_id: UUID of the user
        """
        prefs = await self.user_preferences_repo.get_by_user_id(user_id)
        if not prefs:
            await self._create_default_preferences(user_id)
