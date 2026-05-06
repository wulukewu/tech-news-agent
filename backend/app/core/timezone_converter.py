"""
Timezone Converter Utility

This module provides the TimezoneConverter utility class for handling accurate timezone
conversion between user local time and UTC, and calculating next notification times
based on user preferences.

Requirements: 5.3
"""

import zoneinfo
from datetime import datetime, time, timedelta
from typing import Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


class TimezoneConverter:
    """
    Utility class for timezone conversion and notification scheduling.

    This class provides static methods for:
    - Converting between user local time and UTC
    - Calculating next notification time based on frequency
    - Handling timezone boundaries and daylight saving time transitions
    - Supporting all IANA timezone identifiers

    Requirements: 5.3
    """

    @staticmethod
    def convert_to_user_time(utc_time: datetime, user_timezone: str) -> datetime:
        """
        Convert UTC datetime to user's local timezone.

        Args:
            utc_time: UTC datetime to convert
            user_timezone: IANA timezone identifier (e.g., 'Asia/Taipei', 'America/New_York')

        Returns:
            datetime: Datetime in user's local timezone

        Raises:
            ValueError: If timezone identifier is invalid

        Requirements: 5.3
        """
        try:
            # Ensure UTC time is timezone-aware
            if utc_time.tzinfo is None:
                utc_time = utc_time.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
            elif utc_time.tzinfo != zoneinfo.ZoneInfo("UTC"):
                # Convert to UTC first if it's in a different timezone
                utc_time = utc_time.astimezone(zoneinfo.ZoneInfo("UTC"))

            # Convert to user timezone
            user_tz = zoneinfo.ZoneInfo(user_timezone)
            local_time = utc_time.astimezone(user_tz)

            logger.debug(
                "Converted UTC to user time",
                utc_time=utc_time.isoformat(),
                user_timezone=user_timezone,
                local_time=local_time.isoformat(),
            )

            return local_time

        except Exception as e:
            logger.error(
                "Failed to convert UTC to user time",
                error=str(e),
                utc_time=utc_time.isoformat() if utc_time else None,
                user_timezone=user_timezone,
            )
            raise ValueError(f"Invalid timezone identifier '{user_timezone}': {str(e)}")

    @staticmethod
    def convert_to_utc(local_time: datetime, user_timezone: str) -> datetime:
        """
        Convert user's local datetime to UTC.

        Args:
            local_time: Local datetime to convert
            user_timezone: IANA timezone identifier (e.g., 'Asia/Taipei', 'America/New_York')

        Returns:
            datetime: Datetime in UTC timezone

        Raises:
            ValueError: If timezone identifier is invalid

        Requirements: 5.3
        """
        try:
            # Create timezone-aware datetime if it's naive
            if local_time.tzinfo is None:
                user_tz = zoneinfo.ZoneInfo(user_timezone)
                local_time = local_time.replace(tzinfo=user_tz)

            # Convert to UTC
            utc_time = local_time.astimezone(zoneinfo.ZoneInfo("UTC"))

            logger.debug(
                "Converted local time to UTC",
                local_time=local_time.isoformat(),
                user_timezone=user_timezone,
                utc_time=utc_time.isoformat(),
            )

            return utc_time

        except Exception as e:
            logger.error(
                "Failed to convert local time to UTC",
                error=str(e),
                local_time=local_time.isoformat() if local_time else None,
                user_timezone=user_timezone,
            )
            raise ValueError(f"Invalid timezone identifier '{user_timezone}': {str(e)}")

    @staticmethod
    def get_next_notification_time(
        frequency: str,
        notification_time: str,
        timezone: str,
        from_date: Optional[datetime] = None,
        notification_day_of_week: Optional[int] = None,
        notification_day_of_month: Optional[int] = None,
    ) -> Optional[datetime]:
        """
        Calculate the next notification time based on user preferences.

        Args:
            frequency: Notification frequency ('daily', 'weekly', 'monthly', 'disabled')
            notification_time: Time in HH:MM format (e.g., '18:00')
            timezone: IANA timezone identifier
            from_date: Reference date to calculate from (defaults to current UTC time)
            notification_day_of_week: Day of week for weekly notifications (0=Sunday, 6=Saturday)
            notification_day_of_month: Day of month for monthly notifications (1-31)

        Returns:
            datetime: Next notification time in UTC, or None if disabled

        Raises:
            ValueError: If parameters are invalid

        Requirements: 5.3
        """
        try:
            # Return None for disabled notifications
            if frequency == "disabled":
                logger.debug("Notifications disabled, returning None")
                return None

            # Validate frequency
            valid_frequencies = ["daily", "weekly", "monthly"]
            if frequency not in valid_frequencies:
                raise ValueError(
                    f"Invalid frequency '{frequency}'. Must be one of: {', '.join(valid_frequencies)}"
                )

            # Parse notification time (supports both HH:MM and HH:MM:SS formats)
            try:
                time_parts = notification_time.split(":")
                if len(time_parts) < 2 or len(time_parts) > 3:
                    raise ValueError("Time must have 2 or 3 parts (HH:MM or HH:MM:SS)")

                hour_int = int(time_parts[0])
                minute_int = int(time_parts[1])

                if not (0 <= hour_int <= 23):
                    raise ValueError(f"Invalid hour '{hour_int}'. Must be between 0 and 23")
                if not (0 <= minute_int <= 59):
                    raise ValueError(f"Invalid minute '{minute_int}'. Must be between 0 and 59")

                notification_time_obj = time(hour_int, minute_int)
            except (ValueError, IndexError) as e:
                raise ValueError(
                    f"Invalid notification_time format '{notification_time}'. Must be HH:MM or HH:MM:SS format"
                )

            # Use current UTC time if from_date not provided
            if from_date is None:
                from_date = datetime.utcnow().replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
            elif from_date.tzinfo is None:
                from_date = from_date.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))

            # Convert reference time to user timezone
            user_now = TimezoneConverter.convert_to_user_time(from_date, timezone)

            # Create next notification datetime in user timezone
            next_notification = user_now.replace(
                hour=notification_time_obj.hour,
                minute=notification_time_obj.minute,
                second=0,
                microsecond=0,
            )

            # If the time has already passed today, move to the next occurrence
            if next_notification <= user_now:
                if frequency == "daily":
                    next_notification += timedelta(days=1)
                elif frequency == "weekly":
                    # Use notification_day_of_week if provided, otherwise default to Friday (4)
                    target_weekday = (
                        notification_day_of_week if notification_day_of_week is not None else 5
                    )
                    # Convert from our format (0=Sunday) to Python's format (0=Monday)
                    # Our: 0=Sun, 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri, 6=Sat
                    # Python: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
                    python_weekday = (target_weekday - 1) % 7

                    current_weekday = next_notification.weekday()
                    days_ahead = (python_weekday - current_weekday) % 7
                    if days_ahead == 0:  # It's the target day but time has passed
                        days_ahead = 7
                    next_notification += timedelta(days=days_ahead)
                elif frequency == "monthly":
                    # Use notification_day_of_month if provided, otherwise default to 1
                    target_day = (
                        notification_day_of_month if notification_day_of_month is not None else 1
                    )

                    # Move to next month
                    if next_notification.month == 12:
                        next_year = next_notification.year + 1
                        next_month = 1
                    else:
                        next_year = next_notification.year
                        next_month = next_notification.month + 1

                    # Handle months with fewer days (e.g., Feb 31 -> Feb 28/29)
                    import calendar

                    max_day = calendar.monthrange(next_year, next_month)[1]
                    actual_day = min(target_day, max_day)

                    next_notification = next_notification.replace(
                        year=next_year, month=next_month, day=actual_day
                    )
            else:
                # For weekly notifications, schedule for the target day
                if frequency == "weekly":
                    target_weekday = (
                        notification_day_of_week if notification_day_of_week is not None else 5
                    )
                    python_weekday = (target_weekday - 1) % 7

                    current_weekday = next_notification.weekday()
                    if current_weekday != python_weekday:
                        days_ahead = (python_weekday - current_weekday) % 7
                        if days_ahead == 0:
                            days_ahead = 7
                        next_notification += timedelta(days=days_ahead)
                # For monthly notifications, schedule for the target day
                elif frequency == "monthly":
                    target_day = (
                        notification_day_of_month if notification_day_of_month is not None else 1
                    )

                    # If current day is past target day, move to next month
                    if next_notification.day > target_day:
                        if next_notification.month == 12:
                            next_year = next_notification.year + 1
                            next_month = 1
                        else:
                            next_year = next_notification.year
                            next_month = next_notification.month + 1
                    else:
                        next_year = next_notification.year
                        next_month = next_notification.month

                    # Handle months with fewer days
                    import calendar

                    max_day = calendar.monthrange(next_year, next_month)[1]
                    actual_day = min(target_day, max_day)

                    next_notification = next_notification.replace(
                        year=next_year, month=next_month, day=actual_day
                    )

            # Convert back to UTC
            next_notification_utc = TimezoneConverter.convert_to_utc(next_notification, timezone)

            logger.debug(
                "Calculated next notification time",
                frequency=frequency,
                notification_time=notification_time,
                timezone=timezone,
                from_date=from_date.isoformat(),
                next_notification_utc=next_notification_utc.isoformat(),
            )

            return next_notification_utc

        except Exception as e:
            logger.error(
                "Failed to calculate next notification time",
                error=str(e),
                frequency=frequency,
                notification_time=notification_time,
                timezone=timezone,
                from_date=from_date.isoformat() if from_date else None,
            )
            raise ValueError(f"Failed to calculate next notification time: {str(e)}")

    @staticmethod
    def is_valid_timezone(timezone: str) -> bool:
        """
        Check if a timezone identifier is valid.

        Args:
            timezone: IANA timezone identifier to validate

        Returns:
            bool: True if timezone is valid, False otherwise

        Requirements: 5.3
        """
        try:
            zoneinfo.ZoneInfo(timezone)
            return True
        except Exception:
            return False

    @staticmethod
    def get_timezone_offset(timezone: str, at_time: Optional[datetime] = None) -> str:
        """
        Get the timezone offset string for a given timezone at a specific time.

        Args:
            timezone: IANA timezone identifier
            at_time: Datetime to get offset for (defaults to current UTC time)

        Returns:
            str: Timezone offset in format like '+08:00' or '-05:00'

        Raises:
            ValueError: If timezone identifier is invalid

        Requirements: 5.3
        """
        try:
            if at_time is None:
                at_time = datetime.utcnow().replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
            elif at_time.tzinfo is None:
                at_time = at_time.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))

            # Convert to the target timezone
            local_time = TimezoneConverter.convert_to_user_time(at_time, timezone)

            # Get the offset
            offset = local_time.utcoffset()
            if offset is None:
                raise ValueError(f"Could not determine offset for timezone '{timezone}'")

            # Format as +HH:MM or -HH:MM
            total_seconds = int(offset.total_seconds())
            hours, remainder = divmod(abs(total_seconds), 3600)
            minutes = remainder // 60
            sign = "+" if total_seconds >= 0 else "-"

            offset_str = f"{sign}{hours:02d}:{minutes:02d}"

            logger.debug(
                "Got timezone offset",
                timezone=timezone,
                at_time=at_time.isoformat(),
                offset=offset_str,
            )

            return offset_str

        except Exception as e:
            logger.error(
                "Failed to get timezone offset",
                error=str(e),
                timezone=timezone,
                at_time=at_time.isoformat() if at_time else None,
            )
            raise ValueError(f"Invalid timezone identifier '{timezone}': {str(e)}")
