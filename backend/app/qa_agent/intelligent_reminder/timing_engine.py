"""
Timing Engine for the Intelligent Reminder Agent.
Determines optimal timing for sending reminders based on user behavior patterns.
"""
import logging
from datetime import datetime, time, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from ...services.supabase_service import SupabaseService
from .behavior_analyzer import BehaviorAnalyzer
from .models import ReminderSettings, TimingDecision, UserProfile

logger = logging.getLogger(__name__)


class TimingEngine:
    """Determines optimal timing for sending reminders"""

    def __init__(
        self,
        supabase_service: Optional[SupabaseService] = None,
        behavior_analyzer: Optional[BehaviorAnalyzer] = None,
    ):
        self.supabase_service = supabase_service or SupabaseService()
        self.behavior_analyzer = behavior_analyzer or BehaviorAnalyzer(supabase_service)
        self.max_daily_reminders = 5
        self.min_hours_between_reminders = 2

    async def should_send_reminder(
        self, user_id: UUID, reminder_type: str, priority_score: float = 0.5
    ) -> TimingDecision:
        """
        Determine if and when to send a reminder to the user.
        Ensures max 5 reminders per day and respects user patterns.
        """
        try:
            # Get user settings and profile
            settings = await self._get_user_settings(user_id)
            if not settings or not settings.enabled:
                return TimingDecision(
                    should_send=False, confidence=1.0, reason="User has disabled reminders"
                )

            # Check daily reminder limit
            daily_count = await self._get_daily_reminder_count(user_id)
            if daily_count >= settings.max_daily_reminders:
                return TimingDecision(
                    should_send=False,
                    confidence=1.0,
                    reason=f"Daily limit reached ({daily_count}/{settings.max_daily_reminders})",
                )

            # Check minimum time between reminders
            last_reminder_time = await self._get_last_reminder_time(user_id)
            if last_reminder_time:
                time_since_last = datetime.now() - last_reminder_time
                if time_since_last.total_seconds() < self.min_hours_between_reminders * 3600:
                    next_allowed = last_reminder_time + timedelta(
                        hours=self.min_hours_between_reminders
                    )
                    return TimingDecision(
                        should_send=False,
                        confidence=1.0,
                        reason="Too soon since last reminder",
                        delay_until=next_allowed,
                    )

            # Get user behavior profile
            profile = await self.behavior_analyzer.analyze_user_behavior(user_id)

            # Check if user is in quiet hours
            if await self._is_quiet_hours(settings):
                next_active_time = await self._get_next_active_time(settings, profile)
                return TimingDecision(
                    should_send=False,
                    confidence=0.8,
                    reason="User is in quiet hours",
                    delay_until=next_active_time,
                )

            # Check if current time is optimal
            current_hour = datetime.now().hour
            optimal_time = await self._calculate_optimal_time(profile, priority_score)

            if optimal_time and optimal_time > datetime.now():
                return TimingDecision(
                    should_send=False,
                    confidence=0.7,
                    reason="Waiting for optimal time",
                    optimal_time=optimal_time,
                    delay_until=optimal_time,
                )

            # Check if user has been ignoring reminders
            if await self._should_adjust_for_ignored_reminders(user_id):
                return TimingDecision(
                    should_send=False,
                    confidence=0.6,
                    reason="User has been ignoring reminders, adjusting strategy",
                )

            # All checks passed - send reminder
            confidence = self._calculate_timing_confidence(profile, current_hour, priority_score)

            return TimingDecision(
                should_send=True,
                optimal_time=datetime.now(),
                confidence=confidence,
                reason="Optimal timing conditions met",
            )

        except Exception as e:
            logger.error(f"Error determining reminder timing for {user_id}: {e}")
            return TimingDecision(
                should_send=False, confidence=0.0, reason=f"Error in timing analysis: {str(e)}"
            )

    async def get_next_optimal_time(
        self, user_id: UUID, priority_score: float = 0.5
    ) -> Optional[datetime]:
        """Get the next optimal time to send a reminder to the user"""
        try:
            profile = await self.behavior_analyzer.analyze_user_behavior(user_id)
            settings = await self._get_user_settings(user_id)

            if not settings or not settings.enabled:
                return None

            return await self._calculate_optimal_time(profile, priority_score)

        except Exception as e:
            logger.error(f"Error calculating next optimal time for {user_id}: {e}")
            return None

    async def adjust_strategy_for_user(self, user_id: UUID) -> None:
        """Adjust reminder strategy based on user's recent response patterns"""
        try:
            should_adjust = await self.behavior_analyzer.should_adjust_strategy(user_id)

            if should_adjust:
                # Reduce reminder frequency temporarily
                settings = await self._get_user_settings(user_id)
                if settings:
                    new_max = max(1, settings.max_daily_reminders - 1)
                    await self._update_user_settings(user_id, {"max_daily_reminders": new_max})

                    logger.info(
                        f"Adjusted reminder strategy for user {user_id}: reduced to {new_max} daily reminders"
                    )

        except Exception as e:
            logger.error(f"Error adjusting strategy for user {user_id}: {e}")

    async def _get_user_settings(self, user_id: UUID) -> Optional[ReminderSettings]:
        """Get user's reminder settings"""
        try:
            result = (
                await self.supabase_service.client.table("reminder_settings")
                .select("*")
                .eq("user_id", str(user_id))
                .execute()
            )

            if result.data:
                data = result.data[0]
                return ReminderSettings(
                    id=UUID(data["id"]),
                    user_id=UUID(data["user_id"]),
                    enabled=data["enabled"],
                    max_daily_reminders=data["max_daily_reminders"],
                    preferred_channels=data["preferred_channels"],
                    quiet_hours_start=time.fromisoformat(data["quiet_hours_start"])
                    if data["quiet_hours_start"]
                    else None,
                    quiet_hours_end=time.fromisoformat(data["quiet_hours_end"])
                    if data["quiet_hours_end"]
                    else None,
                    timezone=data["timezone"],
                    reminder_frequency=data["reminder_frequency"],
                    created_at=datetime.fromisoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"]),
                )

            # Create default settings if none exist
            return await self._create_default_settings(user_id)

        except Exception as e:
            logger.error(f"Error getting user settings for {user_id}: {e}")
            return None

    async def _create_default_settings(self, user_id: UUID) -> ReminderSettings:
        """Create default reminder settings for user"""
        try:
            default_data = {
                "user_id": str(user_id),
                "enabled": True,
                "max_daily_reminders": 5,
                "preferred_channels": ["discord"],
                "timezone": "UTC",
                "reminder_frequency": "smart",
            }

            result = (
                await self.supabase_service.client.table("reminder_settings")
                .insert(default_data)
                .execute()
            )

            if result.data:
                data = result.data[0]
                return ReminderSettings(
                    id=UUID(data["id"]),
                    user_id=user_id,
                    enabled=True,
                    max_daily_reminders=5,
                    preferred_channels=["discord"],
                    timezone="UTC",
                    reminder_frequency="smart",
                    created_at=datetime.fromisoformat(data["created_at"]),
                    updated_at=datetime.fromisoformat(data["updated_at"]),
                )

        except Exception as e:
            logger.error(f"Error creating default settings for {user_id}: {e}")

        # Fallback to in-memory default
        return ReminderSettings(
            id=UUID("00000000-0000-0000-0000-000000000000"),
            user_id=user_id,
            enabled=True,
            max_daily_reminders=5,
            preferred_channels=["discord"],
            timezone="UTC",
            reminder_frequency="smart",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    async def _get_daily_reminder_count(self, user_id: UUID) -> int:
        """Get number of reminders sent to user today"""
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            result = (
                await self.supabase_service.client.table("reminder_log")
                .select("id", count="exact")
                .eq("user_id", str(user_id))
                .gte("sent_at", today_start.isoformat())
                .execute()
            )

            return result.count or 0

        except Exception as e:
            logger.error(f"Error getting daily reminder count for {user_id}: {e}")
            return 0

    async def _get_last_reminder_time(self, user_id: UUID) -> Optional[datetime]:
        """Get timestamp of last reminder sent to user"""
        try:
            result = (
                await self.supabase_service.client.table("reminder_log")
                .select("sent_at")
                .eq("user_id", str(user_id))
                .order("sent_at", desc=True)
                .limit(1)
                .execute()
            )

            if result.data:
                return datetime.fromisoformat(result.data[0]["sent_at"])

            return None

        except Exception as e:
            logger.error(f"Error getting last reminder time for {user_id}: {e}")
            return None

    async def _is_quiet_hours(self, settings: ReminderSettings) -> bool:
        """Check if current time is within user's quiet hours"""
        if not settings.quiet_hours_start or not settings.quiet_hours_end:
            return False

        current_time = datetime.now().time()

        # Handle quiet hours that span midnight
        if settings.quiet_hours_start > settings.quiet_hours_end:
            return (
                current_time >= settings.quiet_hours_start
                or current_time <= settings.quiet_hours_end
            )
        else:
            return settings.quiet_hours_start <= current_time <= settings.quiet_hours_end

    async def _get_next_active_time(
        self, settings: ReminderSettings, profile: UserProfile
    ) -> datetime:
        """Get next time when user is likely to be active"""
        now = datetime.now()

        # If in quiet hours, wait until quiet hours end
        if settings.quiet_hours_end:
            next_active = now.replace(
                hour=settings.quiet_hours_end.hour,
                minute=settings.quiet_hours_end.minute,
                second=0,
                microsecond=0,
            )

            # If quiet hours end is tomorrow
            if next_active <= now:
                next_active += timedelta(days=1)

            return next_active

        # Otherwise, use next peak hour
        current_hour = now.hour
        for hour in sorted(profile.active_hours):
            if hour > current_hour:
                return now.replace(hour=hour, minute=0, second=0, microsecond=0)

        # If no more peak hours today, use first peak hour tomorrow
        if profile.active_hours:
            tomorrow = now + timedelta(days=1)
            return tomorrow.replace(hour=profile.active_hours[0], minute=0, second=0, microsecond=0)

        # Fallback to next hour
        return now + timedelta(hours=1)

    async def _calculate_optimal_time(
        self, profile: UserProfile, priority_score: float
    ) -> Optional[datetime]:
        """Calculate optimal time to send reminder based on user profile"""
        now = datetime.now()
        current_hour = now.hour

        # For high priority reminders, send immediately if user is active
        if priority_score > 0.8 and current_hour in profile.active_hours:
            return now

        # Find next optimal hour
        for hour in sorted(profile.active_hours):
            if hour > current_hour:
                optimal_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)

                # Add some randomization to avoid exact hour timing
                import random

                optimal_time += timedelta(minutes=random.randint(0, 30))

                return optimal_time

        # If no more optimal hours today, use first optimal hour tomorrow
        if profile.active_hours:
            tomorrow = now + timedelta(days=1)
            optimal_time = tomorrow.replace(
                hour=profile.active_hours[0], minute=0, second=0, microsecond=0
            )

            import random

            optimal_time += timedelta(minutes=random.randint(0, 30))

            return optimal_time

        return None

    async def _should_adjust_for_ignored_reminders(self, user_id: UUID) -> bool:
        """Check if user has been ignoring reminders and strategy should be adjusted"""
        try:
            # Check last 3 reminders
            result = (
                await self.supabase_service.client.table("reminder_log")
                .select("status")
                .eq("user_id", str(user_id))
                .order("sent_at", desc=True)
                .limit(3)
                .execute()
            )

            if result.data and len(result.data) >= 3:
                ignored_count = sum(1 for r in result.data if r["status"] == "dismissed")
                return ignored_count >= 3

            return False

        except Exception as e:
            logger.error(f"Error checking ignored reminders for {user_id}: {e}")
            return False

    def _calculate_timing_confidence(
        self, profile: UserProfile, current_hour: int, priority_score: float
    ) -> float:
        """Calculate confidence score for current timing"""
        confidence = 0.5  # Base confidence

        # Boost confidence if current hour is in user's active hours
        if current_hour in profile.active_hours:
            confidence += 0.3

        # Boost confidence for high priority reminders
        confidence += priority_score * 0.2

        # Reduce confidence if user has low response rates
        avg_response_rate = sum(profile.response_rate_by_type.values()) / max(
            1, len(profile.response_rate_by_type)
        )
        confidence *= 0.5 + avg_response_rate * 0.5

        return min(1.0, confidence)

    async def _update_user_settings(self, user_id: UUID, updates: Dict[str, Any]) -> None:
        """Update user's reminder settings"""
        try:
            await self.supabase_service.client.table("reminder_settings").update(updates).eq(
                "user_id", str(user_id)
            ).execute()
        except Exception as e:
            logger.error(f"Error updating user settings for {user_id}: {e}")
