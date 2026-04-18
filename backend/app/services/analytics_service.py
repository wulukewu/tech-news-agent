"""
Analytics Service

This module provides the AnalyticsService class for tracking and analyzing
user onboarding events, including logging events, calculating completion rates,
drop-off rates, and average time per step.

This service follows the repository pattern and depends on repository interfaces
for data access instead of directly accessing the database client.

Requirements: 14.1, 14.3, 14.4, 14.5, 14.6
Validates: Requirements 3.1, 3.2, 3.3
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.errors import ErrorCode
from app.core.logger import get_logger
from app.repositories.analytics_event import AnalyticsEventRepository
from app.schemas.analytics import (
    AverageTimePerStepResponse,
    DropOffRatesResponse,
    OnboardingCompletionRateResponse,
)
from app.services.base import BaseService

logger = get_logger(__name__)


class AnalyticsService(BaseService):
    """
    Service for tracking and analyzing user onboarding events.

    This service handles:
    - Logging analytics events to the database
    - Calculating onboarding completion rates
    - Analyzing drop-off rates at each step
    - Computing average time spent per step

    This service uses the repository pattern for data access, depending on
    AnalyticsEventRepository instead of directly accessing the database.

    Requirements: 14.1, 14.3, 14.4, 14.5, 14.6
    Validates: Requirements 3.1, 3.2, 3.3
    """

    # Supported event types
    SUPPORTED_EVENT_TYPES = {
        "onboarding_started",
        "step_completed",
        "onboarding_skipped",
        "onboarding_finished",
        "tooltip_shown",
        "tooltip_skipped",
        "feed_subscribed_from_onboarding",
    }

    def __init__(self, analytics_event_repo: AnalyticsEventRepository):
        """
        Initialize the AnalyticsService.

        Args:
            analytics_event_repo: Repository for analytics event data access
        """
        super().__init__()
        self.analytics_event_repo = analytics_event_repo
        self.logger = get_logger(f"{__name__}.AnalyticsService")

    async def log_event(
        self, user_id: UUID, event_type: str, event_data: dict[str, Any] | None = None
    ) -> None:
        """
        Log an analytics event to the analytics_events table.

        Records user actions during onboarding for later analysis.
        Supports all onboarding event types defined in the design document.

        Args:
            user_id: UUID of the user
            event_type: Type of event (must be one of SUPPORTED_EVENT_TYPES)
            event_data: Optional dictionary containing event metadata

        Raises:
            AnalyticsServiceError: If event logging fails or event_type is invalid

        Requirements: 14.1, 14.3, 14.4
        """
        try:
            self.logger.info("Logging analytics event", user_id=str(user_id), event_type=event_type)

            # Validate event type
            if event_type not in self.SUPPORTED_EVENT_TYPES:
                self.logger.warning(
                    "Unsupported event type",
                    event_type=event_type,
                    supported_types=list(self.SUPPORTED_EVENT_TYPES),
                )
                # Don't raise error, just log warning and continue
                # This allows for forward compatibility with new event types

            # Create event using repository
            await self.analytics_event_repo.create(
                {
                    "user_id": str(user_id),
                    "event_type": event_type,
                    "event_data": event_data or {},
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )

            self.logger.info(
                "Successfully logged analytics event", user_id=str(user_id), event_type=event_type
            )

        except Exception as e:
            self._handle_error(
                e,
                "Failed to log analytics event",
                error_code=ErrorCode.DB_QUERY_FAILED,
                context={"user_id": str(user_id), "event_type": event_type},
            )

    async def get_onboarding_completion_rate(
        self, start_date: datetime, end_date: datetime
    ) -> OnboardingCompletionRateResponse:
        """
        Calculate the onboarding completion rate for a given time period.

        Analyzes how many users who started onboarding actually completed it,
        providing insights into the effectiveness of the onboarding flow.

        Args:
            start_date: Start of the analysis period
            end_date: End of the analysis period

        Returns:
            OnboardingCompletionRateResponse with completion statistics

        Raises:
            AnalyticsServiceError: If database query fails

        Requirements: 14.6
        """
        try:
            self.logger.info(
                "Calculating onboarding completion rate",
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

            # Query users who started onboarding in the period using repository
            started_events = await self.analytics_event_repo.list_by_event_type(
                "onboarding_started", start_date=start_date, end_date=end_date
            )

            # Get unique users who started
            started_users = {event.user_id for event in started_events}
            total_users = len(started_users)

            if total_users == 0:
                # No users started onboarding in this period
                return OnboardingCompletionRateResponse(
                    completion_rate=0.0,
                    total_users=0,
                    completed_users=0,
                    skipped_users=0,
                    start_date=start_date,
                    end_date=end_date,
                )

            # Query users who completed onboarding
            completed_events = await self.analytics_event_repo.list_by_event_type(
                "onboarding_finished", start_date=start_date, end_date=end_date
            )
            completed_users = {event.user_id for event in completed_events}

            # Query users who skipped onboarding
            skipped_events = await self.analytics_event_repo.list_by_event_type(
                "onboarding_skipped", start_date=start_date, end_date=end_date
            )
            skipped_users = {event.user_id for event in skipped_events}

            # Calculate completion rate
            completed_count = len(completed_users)
            skipped_count = len(skipped_users)
            completion_rate = (completed_count / total_users) * 100 if total_users > 0 else 0.0

            self.logger.info(
                "Completion rate calculated",
                completion_rate=round(completion_rate, 2),
                completed_count=completed_count,
                total_users=total_users,
            )

            return OnboardingCompletionRateResponse(
                completion_rate=round(completion_rate, 2),
                total_users=total_users,
                completed_users=completed_count,
                skipped_users=skipped_count,
                start_date=start_date,
                end_date=end_date,
            )

        except Exception as e:
            self._handle_error(
                e,
                "Failed to calculate completion rate",
                error_code=ErrorCode.DB_QUERY_FAILED,
                context={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
            )

    async def get_drop_off_rates(self) -> DropOffRatesResponse:
        """
        Calculate drop-off rates at each onboarding step.

        Identifies where users are abandoning the onboarding flow,
        helping to pinpoint areas for improvement.

        Returns:
            DropOffRatesResponse with drop-off rates per step

        Raises:
            AnalyticsServiceError: If database query fails

        Requirements: 14.6
        """
        try:
            self.logger.info("Calculating drop-off rates by step")

            # Query all step_completed events using repository
            step_events = await self.analytics_event_repo.list_by_event_type("step_completed")

            if not step_events:
                self.logger.info("No step completion events found")
                return DropOffRatesResponse(drop_off_by_step={}, total_started=0)

            # Count users who started onboarding
            started_events = await self.analytics_event_repo.list_by_event_type(
                "onboarding_started"
            )
            total_started = len({event.user_id for event in started_events})

            if total_started == 0:
                return DropOffRatesResponse(drop_off_by_step={}, total_started=0)

            # Count completions per step
            step_completions: dict[str, set] = {}
            for event in step_events:
                step = event.event_data.get("step")
                if step:
                    if step not in step_completions:
                        step_completions[step] = set()
                    step_completions[step].add(event.user_id)

            # Calculate drop-off rates
            # Drop-off rate = (users who started - users who completed step) / users who started * 100
            drop_off_by_step = {}
            for step, users in step_completions.items():
                completed_count = len(users)
                drop_off_count = total_started - completed_count
                drop_off_rate = (drop_off_count / total_started) * 100 if total_started > 0 else 0.0
                drop_off_by_step[step] = round(drop_off_rate, 2)

            self.logger.info(
                "Drop-off rates calculated",
                step_count=len(drop_off_by_step),
                total_started=total_started,
            )

            return DropOffRatesResponse(
                drop_off_by_step=drop_off_by_step, total_started=total_started
            )

        except Exception as e:
            self._handle_error(
                e, "Failed to calculate drop-off rates", error_code=ErrorCode.DB_QUERY_FAILED
            )

    async def get_average_time_per_step(self) -> AverageTimePerStepResponse:
        """
        Calculate average time spent on each onboarding step.

        Provides insights into which steps take the most time,
        helping to optimize the onboarding flow.

        Returns:
            AverageTimePerStepResponse with average time per step in seconds

        Raises:
            AnalyticsServiceError: If database query fails

        Requirements: 14.5
        """
        try:
            self.logger.info("Calculating average time per step")

            # Query all step_completed events with time_spent_seconds using repository
            step_events = await self.analytics_event_repo.list_by_event_type("step_completed")

            if not step_events:
                self.logger.info("No step completion events found")
                return AverageTimePerStepResponse(average_time_by_step={}, total_completions=0)

            # Aggregate time spent per step
            step_times: dict[str, list] = {}
            for event in step_events:
                step = event.event_data.get("step")
                time_spent = event.event_data.get("time_spent_seconds")

                if step and time_spent is not None:
                    if step not in step_times:
                        step_times[step] = []
                    step_times[step].append(float(time_spent))

            # Calculate averages
            average_time_by_step = {}
            total_completions = 0

            for step, times in step_times.items():
                if times:
                    average_time = sum(times) / len(times)
                    average_time_by_step[step] = round(average_time, 2)
                    total_completions += len(times)

            self.logger.info(
                "Average time per step calculated",
                step_count=len(average_time_by_step),
                total_completions=total_completions,
            )

            return AverageTimePerStepResponse(
                average_time_by_step=average_time_by_step, total_completions=total_completions
            )

        except Exception as e:
            self._handle_error(
                e, "Failed to calculate average time per step", error_code=ErrorCode.DB_QUERY_FAILED
            )
