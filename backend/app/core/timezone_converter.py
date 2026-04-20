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
        frequency: str, notification_time: str, timezone: str, from_date: Optional[datetime] = None
    ) -> Optional[datetime]:
        """
        Calculate the next notification time based on user preferences.

        Args:
            frequency: Notification frequency ('daily', 'weekly', 'monthly', 'disabled')
            notification_time: Time in HH:MM format (e.g., '18:00')
            timezone: IANA timezone identifier
            from_date: Reference date to calculate from (defaults to current UTC time)

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

            # Parse notification time
            try:
                hour, minute = notification_time.split(":")
                hour_int = int(hour)
                minute_int = int(minute)

                if not (0 <= hour_int <= 23):
                    raise ValueError(f"Invalid hour '{hour_int}'. Must be between 0 and 23")
                if not (0 <= minute_int <= 59):
                    raise ValueError(f"Invalid minute '{minute_int}'. Must be between 0 and 59")

                notification_time_obj = time(hour_int, minute_int)
            except (ValueError, IndexError) as e:
                raise ValueError(
                    f"Invalid notification_time format '{notification_time}'. Must be HH:MM format"
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
                    # Default to Friday (weekday 4, where Monday is 0)
                    days_until_friday = (4 - next_notification.weekday()) % 7
                    if days_until_friday == 0:  # It's Friday but time has passed
                        days_until_friday = 7
                    next_notification += timedelta(days=days_until_friday)
                elif frequency == "monthly":
                    # Move to the first day of next month
                    if next_notification.month == 12:
                        next_notification = next_notification.replace(
                            year=next_notification.year + 1, month=1, day=1
                        )
                    else:
                        next_notification = next_notification.replace(
                            month=next_notification.month + 1, day=1
                        )
            else:
                # For weekly notifications, always schedule for Friday even if time hasn't passed today
                if frequency == "weekly" and next_notification.weekday() != 4:
                    days_until_friday = (4 - next_notification.weekday()) % 7
                    if days_until_friday == 0:  # It's Friday
                        days_until_friday = 7
                    next_notification += timedelta(days=days_until_friday)
                # For monthly notifications, always schedule for the first day of next month
                elif frequency == "monthly":
                    if next_notification.month == 12:
                        next_notification = next_notification.replace(
                            year=next_notification.year + 1, month=1, day=1
                        )
                    else:
                        next_notification = next_notification.replace(
                            month=next_notification.month + 1, day=1
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
