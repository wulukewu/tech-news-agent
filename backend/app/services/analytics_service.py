"""
Analytics Service

This module provides the AnalyticsService class for tracking and analyzing
user onboarding events, including logging events, calculating completion rates,
drop-off rates, and average time per step.

Requirements: 14.1, 14.3, 14.4, 14.5, 14.6
"""

import logging
from uuid import UUID
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from supabase import Client

from app.schemas.analytics import (
    AnalyticsEvent,
    OnboardingCompletionRateResponse,
    DropOffRatesResponse,
    AverageTimePerStepResponse
)


logger = logging.getLogger(__name__)


class AnalyticsServiceError(Exception):
    """Base exception for AnalyticsService errors"""
    pass


class AnalyticsService:
    """
    Service for tracking and analyzing user onboarding events.
    
    This service handles:
    - Logging analytics events to the database
    - Calculating onboarding completion rates
    - Analyzing drop-off rates at each step
    - Computing average time spent per step
    
    Requirements: 14.1, 14.3, 14.4, 14.5, 14.6
    """
    
    # Supported event types
    SUPPORTED_EVENT_TYPES = {
        'onboarding_started',
        'step_completed',
        'onboarding_skipped',
        'onboarding_finished',
        'tooltip_shown',
        'tooltip_skipped',
        'feed_subscribed_from_onboarding'
    }
    
    def __init__(self, supabase_client: Client):
        """
        Initialize the AnalyticsService.
        
        Args:
            supabase_client: Supabase client instance for database operations
        """
        self.client = supabase_client
        self.logger = logging.getLogger(__name__)
    
    async def log_event(
        self,
        user_id: UUID,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None
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
            self.logger.info(f"Logging analytics event: user={user_id}, type={event_type}")
            
            # Validate event type
            if event_type not in self.SUPPORTED_EVENT_TYPES:
                self.logger.warning(
                    f"Unsupported event type: {event_type}. "
                    f"Supported types: {self.SUPPORTED_EVENT_TYPES}"
                )
                # Don't raise error, just log warning and continue
                # This allows for forward compatibility with new event types
            
            # Prepare event data
            insert_data = {
                'user_id': str(user_id),
                'event_type': event_type,
                'event_data': event_data or {},
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Insert event into database
            response = self.client.table('analytics_events') \
                .insert(insert_data) \
                .execute()
            
            if not response.data:
                raise AnalyticsServiceError(f"Failed to log event for user {user_id}")
            
            self.logger.info(f"Successfully logged analytics event for user {user_id}")
            
        except AnalyticsServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to log analytics event for user {user_id}: {e}")
            raise AnalyticsServiceError(f"Failed to log analytics event: {str(e)}")
    
    async def get_onboarding_completion_rate(
        self,
        start_date: datetime,
        end_date: datetime
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
                f"Calculating completion rate from {start_date} to {end_date}"
            )
            
            # Query users who started onboarding in the period
            started_response = self.client.table('analytics_events') \
                .select('user_id', count='exact') \
                .eq('event_type', 'onboarding_started') \
                .gte('created_at', start_date.isoformat()) \
                .lte('created_at', end_date.isoformat()) \
                .execute()
            
            # Get unique users who started
            started_users = set()
            if started_response.data:
                started_users = {event['user_id'] for event in started_response.data}
            
            total_users = len(started_users)
            
            if total_users == 0:
                # No users started onboarding in this period
                return OnboardingCompletionRateResponse(
                    completion_rate=0.0,
                    total_users=0,
                    completed_users=0,
                    skipped_users=0,
                    start_date=start_date,
                    end_date=end_date
                )
            
            # Query users who completed onboarding
            completed_response = self.client.table('analytics_events') \
                .select('user_id') \
                .eq('event_type', 'onboarding_finished') \
                .gte('created_at', start_date.isoformat()) \
                .lte('created_at', end_date.isoformat()) \
                .execute()
            
            completed_users = set()
            if completed_response.data:
                completed_users = {event['user_id'] for event in completed_response.data}
            
            # Query users who skipped onboarding
            skipped_response = self.client.table('analytics_events') \
                .select('user_id') \
                .eq('event_type', 'onboarding_skipped') \
                .gte('created_at', start_date.isoformat()) \
                .lte('created_at', end_date.isoformat()) \
                .execute()
            
            skipped_users = set()
            if skipped_response.data:
                skipped_users = {event['user_id'] for event in skipped_response.data}
            
            # Calculate completion rate
            completed_count = len(completed_users)
            skipped_count = len(skipped_users)
            completion_rate = (completed_count / total_users) * 100 if total_users > 0 else 0.0
            
            self.logger.info(
                f"Completion rate: {completion_rate:.2f}% "
                f"({completed_count}/{total_users} users)"
            )
            
            return OnboardingCompletionRateResponse(
                completion_rate=round(completion_rate, 2),
                total_users=total_users,
                completed_users=completed_count,
                skipped_users=skipped_count,
                start_date=start_date,
                end_date=end_date
            )
            
        except Exception as e:
            self.logger.error(f"Failed to calculate completion rate: {e}")
            raise AnalyticsServiceError(f"Failed to calculate completion rate: {str(e)}")
    
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
            
            # Query all step_completed events
            step_events_response = self.client.table('analytics_events') \
                .select('user_id, event_data') \
                .eq('event_type', 'step_completed') \
                .execute()
            
            if not step_events_response.data:
                self.logger.info("No step completion events found")
                return DropOffRatesResponse(
                    drop_off_by_step={},
                    total_started=0
                )
            
            # Count users who started onboarding
            started_response = self.client.table('analytics_events') \
                .select('user_id') \
                .eq('event_type', 'onboarding_started') \
                .execute()
            
            total_started = len(set(event['user_id'] for event in started_response.data)) if started_response.data else 0
            
            if total_started == 0:
                return DropOffRatesResponse(
                    drop_off_by_step={},
                    total_started=0
                )
            
            # Count completions per step
            step_completions: Dict[str, set] = {}
            for event in step_events_response.data:
                event_data = event.get('event_data', {})
                step = event_data.get('step')
                if step:
                    if step not in step_completions:
                        step_completions[step] = set()
                    step_completions[step].add(event['user_id'])
            
            # Calculate drop-off rates
            # Drop-off rate = (users who started - users who completed step) / users who started * 100
            drop_off_by_step = {}
            for step, users in step_completions.items():
                completed_count = len(users)
                drop_off_count = total_started - completed_count
                drop_off_rate = (drop_off_count / total_started) * 100 if total_started > 0 else 0.0
                drop_off_by_step[step] = round(drop_off_rate, 2)
            
            self.logger.info(f"Calculated drop-off rates for {len(drop_off_by_step)} steps")
            
            return DropOffRatesResponse(
                drop_off_by_step=drop_off_by_step,
                total_started=total_started
            )
            
        except Exception as e:
            self.logger.error(f"Failed to calculate drop-off rates: {e}")
            raise AnalyticsServiceError(f"Failed to calculate drop-off rates: {str(e)}")
    
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
            
            # Query all step_completed events with time_spent_seconds
            step_events_response = self.client.table('analytics_events') \
                .select('event_data') \
                .eq('event_type', 'step_completed') \
                .execute()
            
            if not step_events_response.data:
                self.logger.info("No step completion events found")
                return AverageTimePerStepResponse(
                    average_time_by_step={},
                    total_completions=0
                )
            
            # Aggregate time spent per step
            step_times: Dict[str, list] = {}
            for event in step_events_response.data:
                event_data = event.get('event_data', {})
                step = event_data.get('step')
                time_spent = event_data.get('time_spent_seconds')
                
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
                f"Calculated average time for {len(average_time_by_step)} steps "
                f"({total_completions} total completions)"
            )
            
            return AverageTimePerStepResponse(
                average_time_by_step=average_time_by_step,
                total_completions=total_completions
            )
            
        except Exception as e:
            self.logger.error(f"Failed to calculate average time per step: {e}")
            raise AnalyticsServiceError(f"Failed to calculate average time per step: {str(e)}")
