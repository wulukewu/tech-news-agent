"""
Quiet Hours Service

This service manages user-defined quiet hours when notifications should not be sent.
It handles timezone conversion, weekday checking, and integration with the notification system.
"""

import logging
import zoneinfo
from datetime import datetime, time, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.core.exceptions import SupabaseServiceError
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class QuietHoursSettings:
    """Data class for quiet hours settings."""

    def __init__(
        self,
        user_id: UUID,
        start_time: time,
        end_time: time,
        timezone: str = "UTC",
        weekdays: List[int] = None,
        enabled: bool = True,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.start_time = start_time
        self.end_time = end_time
        self.timezone = timezone
        self.weekdays = weekdays or [1, 2, 3, 4, 5, 6, 7]  # Default: all days
        self.enabled = enabled
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id) if self.id else None,
            "user_id": str(self.user_id),
            "start_time": self.start_time.strftime("%H:%M:%S"),
            "end_time": self.end_time.strftime("%H:%M:%S"),
            "timezone": self.timezone,
            "weekdays": self.weekdays,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "QuietHoursSettings":
        """Create from dictionary."""
        return cls(
            id=UUID(data["id"]) if data.get("id") else None,
            user_id=UUID(data["user_id"]),
            start_time=datetime.strptime(data["start_time"], "%H:%M:%S").time(),
            end_time=datetime.strptime(data["end_time"], "%H:%M:%S").time(),
            timezone=data.get("timezone", "UTC"),
            weekdays=data.get("weekdays", [1, 2, 3, 4, 5, 6, 7]),
            enabled=data.get("enabled", True),
            created_at=(
                datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
            ),
        )


class QuietHoursService:
    """Service for managing user quiet hours settings."""

    def __init__(self, supabase_service: Optional[SupabaseService] = None):
        self.supabase_service = supabase_service or SupabaseService()

    async def get_quiet_hours(self, user_id: UUID) -> Optional[QuietHoursSettings]:
        """
        Get quiet hours settings for a user.

        Args:
            user_id: The user's UUID

        Returns:
            QuietHoursSettings object or None if not found
        """
        try:
            logger.info(f"Fetching quiet hours for user {user_id}")

            result = (
                self.supabase_service.client.table("user_quiet_hours")
                .select("*")
                .eq("user_id", str(user_id))
                .execute()
            )

            if not result.data:
                logger.info(f"No quiet hours found for user {user_id}")
                return None

            data = result.data[0]
            quiet_hours = QuietHoursSettings.from_dict(data)

            logger.info(
                f"Retrieved quiet hours for user {user_id}: {quiet_hours.start_time}-{quiet_hours.end_time} ({quiet_hours.timezone})"
            )
            return quiet_hours

        except Exception as e:
            logger.error(f"Failed to get quiet hours for user {user_id}: {e}")
            raise SupabaseServiceError(f"Failed to get quiet hours: {e}")

    async def update_quiet_hours(
        self,
        user_id: UUID,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        timezone: Optional[str] = None,
        weekdays: Optional[List[int]] = None,
        enabled: Optional[bool] = None,
    ) -> QuietHoursSettings:
        """
        Update quiet hours settings for a user.

        Args:
            user_id: The user's UUID
            start_time: Start time for quiet hours
            end_time: End time for quiet hours
            timezone: Timezone for the quiet hours
            weekdays: List of weekdays (1=Monday, 7=Sunday)
            enabled: Whether quiet hours are enabled

        Returns:
            Updated QuietHoursSettings object
        """
        try:
            logger.info(f"Updating quiet hours for user {user_id}")

            # Validate inputs
            if weekdays is not None:
                self._validate_weekdays(weekdays)

            if timezone is not None:
                self._validate_timezone(timezone)

            if start_time is not None and end_time is not None:
                self._validate_time_range(start_time, end_time)

            # Check if quiet hours exist
            existing = await self.get_quiet_hours(user_id)

            if existing:
                # Update existing record
                update_data = {}
                if start_time is not None:
                    update_data["start_time"] = start_time.strftime("%H:%M:%S")
                if end_time is not None:
                    update_data["end_time"] = end_time.strftime("%H:%M:%S")
                if timezone is not None:
                    update_data["timezone"] = timezone
                if weekdays is not None:
                    update_data["weekdays"] = weekdays
                if enabled is not None:
                    update_data["enabled"] = enabled

                result = (
                    self.supabase_service.client.table("user_quiet_hours")
                    .update(update_data)
                    .eq("user_id", str(user_id))
                    .execute()
                )

                if not result.data:
                    raise SupabaseServiceError("Failed to update quiet hours")

                updated_data = result.data[0]

            else:
                # Create new record
                new_data = {
                    "user_id": str(user_id),
                    "start_time": (start_time or time(22, 0)).strftime("%H:%M:%S"),
                    "end_time": (end_time or time(8, 0)).strftime("%H:%M:%S"),
                    "timezone": timezone or "UTC",
                    "weekdays": weekdays or [1, 2, 3, 4, 5, 6, 7],
                    "enabled": enabled if enabled is not None else True,
                }

                result = (
                    self.supabase_service.client.table("user_quiet_hours")
                    .insert(new_data)
                    .execute()
                )

                if not result.data:
                    raise SupabaseServiceError("Failed to create quiet hours")

                updated_data = result.data[0]

            quiet_hours = QuietHoursSettings.from_dict(updated_data)
            logger.info(f"Updated quiet hours for user {user_id}")

            return quiet_hours

        except Exception as e:
            logger.error(f"Failed to update quiet hours for user {user_id}: {e}")
            raise SupabaseServiceError(f"Failed to update quiet hours: {e}")

    async def is_in_quiet_hours(
        self, user_id: UUID, check_time: Optional[datetime] = None
    ) -> Tuple[bool, Optional[QuietHoursSettings]]:
        """
        Check if the current time (or specified time) is within user's quiet hours.

        Args:
            user_id: The user's UUID
            check_time: Time to check (defaults to current time)

        Returns:
            Tuple of (is_in_quiet_hours, quiet_hours_settings)
        """
        try:
            quiet_hours = await self.get_quiet_hours(user_id)

            if not quiet_hours or not quiet_hours.enabled:
                return False, quiet_hours

            check_time = check_time or datetime.utcnow()

            # Convert check time to user's timezone
            try:
                user_tz = zoneinfo.ZoneInfo(quiet_hours.timezone)
            except zoneinfo.ZoneInfoNotFoundError:
                logger.warning(
                    f"Invalid timezone {quiet_hours.timezone} for user {user_id}, using UTC"
                )
                user_tz = timezone.utc

            if check_time.tzinfo is None:
                check_time = check_time.replace(tzinfo=timezone.utc)

            local_time = check_time.astimezone(user_tz)

            # Check if current weekday is in the quiet hours weekdays
            # Python weekday: Monday=0, Sunday=6
            # Our format: Monday=1, Sunday=7
            current_weekday = local_time.weekday() + 1

            if current_weekday not in quiet_hours.weekdays:
                logger.debug(
                    f"User {user_id}: Current weekday {current_weekday} not in quiet hours weekdays {quiet_hours.weekdays}"
                )
                return False, quiet_hours

            # Check if current time is within quiet hours
            current_time = local_time.time()
            start_time = quiet_hours.start_time
            end_time = quiet_hours.end_time

            is_in_quiet_hours = self._is_time_in_range(current_time, start_time, end_time)

            logger.debug(
                f"User {user_id}: Time check {current_time} vs {start_time}-{end_time} = {is_in_quiet_hours}"
            )

            return is_in_quiet_hours, quiet_hours

        except Exception as e:
            logger.error(f"Failed to check quiet hours for user {user_id}: {e}")
            # Return False on error to avoid blocking notifications
            return False, None

    async def get_next_notification_time(
        self, user_id: UUID, base_time: Optional[datetime] = None
    ) -> Optional[datetime]:
        """
        Get the next time when notifications can be sent (after quiet hours end).

        Args:
            user_id: The user's UUID
            base_time: Base time to calculate from (defaults to current time)

        Returns:
            Next available notification time or None if no quiet hours
        """
        try:
            is_quiet, quiet_hours = await self.is_in_quiet_hours(user_id, base_time)

            if not is_quiet or not quiet_hours:
                return base_time or datetime.utcnow()

            base_time = base_time or datetime.utcnow()

            # Convert to user's timezone
            try:
                user_tz = zoneinfo.ZoneInfo(quiet_hours.timezone)
            except zoneinfo.ZoneInfoNotFoundError:
                logger.warning(
                    f"Invalid timezone {quiet_hours.timezone} for user {user_id}, using UTC"
                )
                user_tz = timezone.utc

            if base_time.tzinfo is None:
                base_time = base_time.replace(tzinfo=timezone.utc)

            local_time = base_time.astimezone(user_tz)

            # Find next time when quiet hours end
            next_time = self._find_next_available_time(local_time, quiet_hours)

            # Convert back to UTC
            next_utc = next_time.astimezone(timezone.utc)

            logger.info(f"User {user_id}: Next notification time after quiet hours: {next_utc}")

            return next_utc.replace(tzinfo=None)

        except Exception as e:
            logger.error(f"Failed to get next notification time for user {user_id}: {e}")
            return base_time or datetime.utcnow()

    def _validate_weekdays(self, weekdays: List[int]) -> None:
        """Validate weekdays list."""
        if not weekdays or not isinstance(weekdays, list):
            raise ValueError("Weekdays must be a non-empty list")

        for day in weekdays:
            if not isinstance(day, int) or day < 1 or day > 7:
                raise ValueError("Weekdays must be integers between 1 (Monday) and 7 (Sunday)")

    def _validate_timezone(self, timezone: str) -> None:
        """Validate timezone string."""
        try:
            zoneinfo.ZoneInfo(timezone)
        except zoneinfo.ZoneInfoNotFoundError:
            raise ValueError(f"Invalid timezone: {timezone}")

    def _validate_time_range(self, start_time: time, end_time: time) -> None:
        """Validate time range (allows overnight ranges)."""
        # Both times are valid - overnight ranges are allowed
        # e.g., 22:00 to 08:00 is valid
        pass

    def _is_time_in_range(self, current_time: time, start_time: time, end_time: time) -> bool:
        """
        Check if current time is within the quiet hours range.
        Handles overnight ranges (e.g., 22:00 to 08:00).
        """
        if start_time <= end_time:
            # Same day range (e.g., 09:00 to 17:00)
            return start_time <= current_time <= end_time
        else:
            # Overnight range (e.g., 22:00 to 08:00)
            return current_time >= start_time or current_time <= end_time

    def _find_next_available_time(
        self, current_time: datetime, quiet_hours: QuietHoursSettings
    ) -> datetime:
        """
        Find the next time when notifications can be sent.
        """
        # Start from current time
        next_time = current_time
        max_days_ahead = 7  # Prevent infinite loops

        for _ in range(max_days_ahead):
            # Check if this day has quiet hours
            weekday = next_time.weekday() + 1  # Convert to our format

            if weekday not in quiet_hours.weekdays:
                # This day doesn't have quiet hours, so any time is fine
                return next_time

            # This day has quiet hours, check if we're past the end time
            current_time_only = next_time.time()

            if not self._is_time_in_range(
                current_time_only, quiet_hours.start_time, quiet_hours.end_time
            ):
                # We're not in quiet hours on this day
                return next_time

            # We're in quiet hours, move to the end time
            if quiet_hours.start_time <= quiet_hours.end_time:
                # Same day range - move to end time
                next_time = next_time.replace(
                    hour=quiet_hours.end_time.hour,
                    minute=quiet_hours.end_time.minute,
                    second=quiet_hours.end_time.second,
                    microsecond=0,
                )
                return next_time
            else:
                # Overnight range - move to end time next day
                if current_time_only >= quiet_hours.start_time:
                    # We're in the first part (after start_time), move to next day's end_time
                    next_time = (next_time + timedelta(days=1)).replace(
                        hour=quiet_hours.end_time.hour,
                        minute=quiet_hours.end_time.minute,
                        second=quiet_hours.end_time.second,
                        microsecond=0,
                    )
                    return next_time
                else:
                    # We're in the second part (before end_time), move to end_time today
                    next_time = next_time.replace(
                        hour=quiet_hours.end_time.hour,
                        minute=quiet_hours.end_time.minute,
                        second=quiet_hours.end_time.second,
                        microsecond=0,
                    )
                    return next_time

        # Fallback: return current time + 1 hour
        return current_time + timedelta(hours=1)

    async def create_default_quiet_hours(
        self, user_id: UUID, timezone: str = "UTC"
    ) -> QuietHoursSettings:
        """
        Create default quiet hours for a user (disabled by default).

        Args:
            user_id: The user's UUID
            timezone: User's timezone

        Returns:
            Created QuietHoursSettings object
        """
        try:
            logger.info(f"Creating default quiet hours for user {user_id}")

            return await self.update_quiet_hours(
                user_id=user_id,
                start_time=time(22, 0),  # 10 PM
                end_time=time(8, 0),  # 8 AM
                timezone=timezone,
                weekdays=[1, 2, 3, 4, 5, 6, 7],  # All days
                enabled=False,  # Disabled by default for backward compatibility
            )

        except Exception as e:
            logger.error(f"Failed to create default quiet hours for user {user_id}: {e}")
            raise SupabaseServiceError(f"Failed to create default quiet hours: {e}")

    async def delete_quiet_hours(self, user_id: UUID) -> bool:
        """
        Delete quiet hours settings for a user.

        Args:
            user_id: The user's UUID

        Returns:
            True if deleted successfully
        """
        try:
            logger.info(f"Deleting quiet hours for user {user_id}")

            result = (
                self.supabase_service.client.table("user_quiet_hours")
                .delete()
                .eq("user_id", str(user_id))
                .execute()
            )

            logger.info(f"Deleted quiet hours for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete quiet hours for user {user_id}: {e}")
            raise SupabaseServiceError(f"Failed to delete quiet hours: {e}")
