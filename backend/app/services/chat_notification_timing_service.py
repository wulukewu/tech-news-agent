"""
Chat Notification Timing Service

Implements intelligent notification timing for the chat persistence system.
Learns user activity patterns to choose the best delivery window, enforces
frequency limits, and provides a "do-not-disturb" mechanism.

Key capabilities:
- User activity pattern learning (hourly activity histogram)
- Optimal delivery window selection based on learned patterns
- Notification frequency control (per-type cooldown periods)
- Urgency-based priority override (high-priority bypasses quiet windows)
- Quiet hours enforcement

Validates: Requirements 10.2, 10.3, 10.5
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from app.core.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Number of hourly buckets in the activity histogram
_HISTOGRAM_BUCKETS = 24

# Minimum activity score to consider an hour "active"
_ACTIVE_HOUR_THRESHOLD = 0.1

# Default cooldown periods per notification type (seconds)
_DEFAULT_COOLDOWNS: dict[str, int] = {
    "new_response": 300,  # 5 minutes
    "cross_platform": 60,  # 1 minute
    "reminder": 3600,  # 1 hour
}

# Default quiet hours (22:00 – 08:00 local time)
_DEFAULT_QUIET_START = time(22, 0)
_DEFAULT_QUIET_END = time(8, 0)

# Maximum number of activity events stored per user (rolling window)
_MAX_ACTIVITY_EVENTS = 500


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ActivityEvent:
    """A single user activity event used for pattern learning.

    Attributes:
        user_id: System user UUID.
        platform: Platform where the activity occurred.
        occurred_at: UTC timestamp of the activity.
    """

    user_id: UUID
    platform: str
    occurred_at: datetime


@dataclass
class QuietHoursConfig:
    """Quiet hours configuration for a user.

    Attributes:
        enabled: Whether quiet hours are active.
        start: Local time when quiet hours begin.
        end: Local time when quiet hours end.
        timezone_offset_hours: User's UTC offset in hours (e.g. +8 for CST).
    """

    enabled: bool = True
    start: time = _DEFAULT_QUIET_START
    end: time = _DEFAULT_QUIET_END
    timezone_offset_hours: float = 0.0


@dataclass
class TimingDecision:
    """Result of a timing evaluation.

    Attributes:
        should_send_now: Whether the notification should be delivered
            immediately.
        reason: Human-readable explanation of the decision.
        suggested_delay_seconds: Suggested delay before retrying when
            ``should_send_now`` is ``False``.  ``0`` means "do not retry".
        best_hour_utc: The UTC hour (0-23) that the timing service
            recommends for delivery, based on learned activity patterns.
    """

    should_send_now: bool
    reason: str
    suggested_delay_seconds: int = 0
    best_hour_utc: Optional[int] = None


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


from app.services._cnts_persist_mixin import CntsPersistMixin


class ChatNotificationTimingService(CntsPersistMixin):
    """Intelligent notification timing for the chat persistence system.

    Maintains per-user activity histograms and last-notification timestamps
    in memory.  When a Supabase client is provided, activity data and
    preferences are also persisted to the database for cross-process
    consistency.

    Usage::

        timing = ChatNotificationTimingService(supabase_client=client)

        # Record that the user was active
        await timing.record_activity(user_id, platform="web")

        # Check whether to send a notification right now
        decision = await timing.should_notify(
            user_id=user_id,
            notification_type="new_response",
            priority=NotificationPriority.NORMAL,
        )
        if decision.should_send_now:
            await notification_service.send_notification(payload)

    Validates: Requirements 10.2, 10.3, 10.5
    """

    def __init__(self, supabase_client: Any = None) -> None:
        """Initialise the timing service.

        Args:
            supabase_client: Optional Supabase client for persisting activity
                data and loading user preferences.
        """
        self._supabase = supabase_client

        # user_id (str) -> list[ActivityEvent]
        self._activity_log: dict[str, list[ActivityEvent]] = {}

        # user_id (str) -> {notification_type: last_sent_at (datetime)}
        self._last_sent: dict[str, dict[str, datetime]] = {}

        # user_id (str) -> QuietHoursConfig
        self._quiet_hours: dict[str, QuietHoursConfig] = {}

        self.logger = get_logger(f"{__name__}.ChatNotificationTimingService")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def record_activity(
        self,
        user_id: UUID,
        platform: str,
        occurred_at: Optional[datetime] = None,
    ) -> None:
        """Record a user activity event for pattern learning.

        Appends the event to the in-memory activity log and persists it to
        the database when a Supabase client is available.  The log is capped
        at ``_MAX_ACTIVITY_EVENTS`` entries per user (oldest are dropped).

        Args:
            user_id: System user UUID.
            platform: Platform where the activity occurred.
            occurred_at: UTC timestamp of the event.  Defaults to now.

        Validates: Requirements 10.2
        """
        ts = occurred_at or datetime.now(timezone.utc)
        event = ActivityEvent(user_id=user_id, platform=platform, occurred_at=ts)

        key = str(user_id)
        if key not in self._activity_log:
            self._activity_log[key] = []

        self._activity_log[key].append(event)

        # Rolling window — keep only the most recent events
        if len(self._activity_log[key]) > _MAX_ACTIVITY_EVENTS:
            self._activity_log[key] = self._activity_log[key][-_MAX_ACTIVITY_EVENTS:]

        self.logger.debug(
            "Activity recorded",
            user_id=key,
            platform=platform,
            hour_utc=ts.hour,
        )

        # Persist to database asynchronously (best-effort)
        if self._supabase is not None:
            await self._persist_activity(user_id, platform, ts)

    async def should_notify(
        self,
        user_id: UUID,
        notification_type: str,
        priority: str = "normal",
        now: Optional[datetime] = None,
    ) -> TimingDecision:
        """Decide whether to deliver a notification right now.

        Evaluation order:
        1. High-priority notifications bypass quiet hours and cooldowns.
        2. Quiet hours check — defer if the user is in their quiet window.
        3. Frequency / cooldown check — defer if the type was recently sent.
        4. Activity pattern check — prefer delivery during active hours.

        Args:
            user_id: System user UUID.
            notification_type: Type of notification (e.g. ``"new_response"``).
            priority: Notification priority (``"low"``, ``"normal"``,
                ``"high"``).
            now: Override for the current UTC time (useful in tests).

        Returns:
            A :class:`TimingDecision` describing whether to send now and why.

        Validates: Requirements 10.2, 10.3, 10.5
        """
        now = now or datetime.now(timezone.utc)
        key = str(user_id)

        # 1. High-priority always sends immediately
        if priority == "high":
            self.logger.debug(
                "High-priority notification — sending immediately",
                user_id=key,
                notification_type=notification_type,
            )
            return TimingDecision(
                should_send_now=True,
                reason="High-priority notification bypasses timing rules",
            )

        # 2. Quiet hours check
        quiet_cfg = await self._get_quiet_hours(user_id)
        if quiet_cfg.enabled and self._is_quiet_hour(now, quiet_cfg):
            seconds_until_end = self._seconds_until_quiet_end(now, quiet_cfg)
            self.logger.debug(
                "User is in quiet hours — deferring",
                user_id=key,
                seconds_until_end=seconds_until_end,
            )
            return TimingDecision(
                should_send_now=False,
                reason="User is in quiet hours",
                suggested_delay_seconds=seconds_until_end,
            )

        # 3. Cooldown / frequency check
        cooldown = _DEFAULT_COOLDOWNS.get(notification_type, 300)
        last_sent = self._last_sent.get(key, {}).get(notification_type)
        if last_sent is not None:
            elapsed = (now - last_sent).total_seconds()
            if elapsed < cooldown:
                remaining = int(cooldown - elapsed)
                self.logger.debug(
                    "Notification type in cooldown — deferring",
                    user_id=key,
                    notification_type=notification_type,
                    remaining_seconds=remaining,
                )
                return TimingDecision(
                    should_send_now=False,
                    reason=f"Cooldown active for {notification_type} ({remaining}s remaining)",
                    suggested_delay_seconds=remaining,
                )

        # 4. Activity pattern check (low-priority only defers to active hours)
        if priority == "low":
            histogram = self._build_histogram(user_id)
            best_hour = self._best_delivery_hour(histogram)
            if best_hour is not None and now.hour != best_hour:
                # Suggest delivery at the best hour
                delay = self._seconds_until_hour(now, best_hour)
                self.logger.debug(
                    "Low-priority notification deferred to optimal hour",
                    user_id=key,
                    current_hour=now.hour,
                    best_hour=best_hour,
                    delay_seconds=delay,
                )
                return TimingDecision(
                    should_send_now=False,
                    reason=f"Deferring to optimal delivery hour {best_hour:02d}:00 UTC",
                    suggested_delay_seconds=delay,
                    best_hour_utc=best_hour,
                )

        # All checks passed — send now
        best_hour = self._best_delivery_hour(self._build_histogram(user_id))
        return TimingDecision(
            should_send_now=True,
            reason="All timing checks passed",
            best_hour_utc=best_hour,
        )

    def record_sent(
        self,
        user_id: UUID,
        notification_type: str,
        sent_at: Optional[datetime] = None,
    ) -> None:
        """Record that a notification was successfully delivered.

        Updates the last-sent timestamp used for cooldown enforcement.

        Args:
            user_id: System user UUID.
            notification_type: Type of notification that was sent.
            sent_at: UTC timestamp of delivery.  Defaults to now.
        """
        key = str(user_id)
        ts = sent_at or datetime.now(timezone.utc)
        if key not in self._last_sent:
            self._last_sent[key] = {}
        self._last_sent[key][notification_type] = ts
        self.logger.debug(
            "Recorded sent notification",
            user_id=key,
            notification_type=notification_type,
        )

    async def get_activity_histogram(self, user_id: UUID) -> list[float]:
        """Return the normalised hourly activity histogram for a user.

        The histogram has 24 buckets (one per UTC hour).  Each value is in
        the range [0.0, 1.0], where 1.0 represents the most active hour.

        Args:
            user_id: System user UUID.

        Returns:
            A list of 24 floats representing relative activity per hour.
        """
        return self._build_histogram(user_id)

    async def set_quiet_hours(
        self,
        user_id: UUID,
        enabled: bool,
        start: time,
        end: time,
        timezone_offset_hours: float = 0.0,
    ) -> None:
        """Configure quiet hours for a user.

        Args:
            user_id: System user UUID.
            enabled: Whether quiet hours should be enforced.
            start: Local time when quiet hours begin.
            end: Local time when quiet hours end.
            timezone_offset_hours: User's UTC offset in hours.

        Validates: Requirements 10.3, 10.5
        """
        cfg = QuietHoursConfig(
            enabled=enabled,
            start=start,
            end=end,
            timezone_offset_hours=timezone_offset_hours,
        )
        self._quiet_hours[str(user_id)] = cfg
        self.logger.info(
            "Quiet hours configured",
            user_id=str(user_id),
            enabled=enabled,
            start=start.isoformat(),
            end=end.isoformat(),
        )

        if self._supabase is not None:
            await self._persist_quiet_hours(user_id, cfg)

    async def get_optimal_send_time(
        self,
        user_id: UUID,
        within_hours: int = 24,
        now: Optional[datetime] = None,
    ) -> datetime:
        """Return the next optimal UTC datetime to send a notification.

        Finds the best delivery hour within the next *within_hours* hours
        based on the user's activity histogram, skipping quiet hours.

        Args:
            user_id: System user UUID.
            within_hours: Search window in hours.
            now: Override for the current UTC time.

        Returns:
            A UTC :class:`datetime` representing the recommended send time.
            Falls back to ``now + 1 hour`` if no suitable window is found.

        Validates: Requirements 10.2
        """
        now = now or datetime.now(timezone.utc)
        histogram = self._build_histogram(user_id)
        quiet_cfg = await self._get_quiet_hours(user_id)

        # Build candidate hours sorted by activity score (descending)
        scored: list[tuple[float, int]] = [(histogram[h], h) for h in range(_HISTOGRAM_BUCKETS)]
        scored.sort(reverse=True)

        for score, hour in scored:
            if score < _ACTIVE_HOUR_THRESHOLD and any(
                s > _ACTIVE_HOUR_THRESHOLD for _, s in scored
            ):
                continue  # skip inactive hours when active ones exist

            # Find the next occurrence of this hour within the window
            candidate = now.replace(minute=0, second=0, microsecond=0)
            if candidate.hour > hour:
                candidate = candidate + timedelta(days=1)
            candidate = candidate.replace(hour=hour)

            if candidate <= now:
                candidate += timedelta(days=1)

            if (candidate - now).total_seconds() > within_hours * 3600:
                continue

            # Skip if candidate falls in quiet hours
            if quiet_cfg.enabled and self._is_quiet_hour(candidate, quiet_cfg):
                continue

            self.logger.debug(
                "Optimal send time found",
                user_id=str(user_id),
                optimal_hour=hour,
                candidate=candidate.isoformat(),
            )
            return candidate

        # Fallback: 1 hour from now
        return now + timedelta(hours=1)

    # ------------------------------------------------------------------
    # Private helpers — activity histogram
    # ------------------------------------------------------------------

    def _build_histogram(self, user_id: UUID) -> list[float]:
        """Build a normalised 24-bucket activity histogram for a user.

        Args:
            user_id: System user UUID.

        Returns:
            List of 24 floats in [0.0, 1.0].
        """
        key = str(user_id)
        events = self._activity_log.get(key, [])

        counts = [0] * _HISTOGRAM_BUCKETS
        for event in events:
            counts[event.occurred_at.hour] += 1

        max_count = max(counts) if counts else 0
        if max_count == 0:
            return [0.0] * _HISTOGRAM_BUCKETS

        return [c / max_count for c in counts]

    @staticmethod
    def _best_delivery_hour(histogram: list[float]) -> Optional[int]:
        """Return the UTC hour with the highest activity score.

        Args:
            histogram: Normalised 24-bucket histogram.

        Returns:
            The hour (0-23) with the highest score, or ``None`` if all
            scores are zero (no activity data).
        """
        if not any(histogram):
            return None
        return histogram.index(max(histogram))

    # ------------------------------------------------------------------
    # Private helpers — quiet hours
    # ------------------------------------------------------------------

    async def _get_quiet_hours(self, user_id: UUID) -> QuietHoursConfig:
        """Return the quiet hours config for a user.

        Checks the in-memory cache first, then falls back to the database.
        Returns the default config if neither source has data.

        Args:
            user_id: System user UUID.

        Returns:
            :class:`QuietHoursConfig` for the user.
        """
        key = str(user_id)
        if key in self._quiet_hours:
            return self._quiet_hours[key]

        if self._supabase is not None:
            try:
                resp = (
                    self._supabase.table("user_notification_preferences")
                    .select(
                        "chat_quiet_hours_enabled, chat_quiet_start, "
                        "chat_quiet_end, chat_timezone_offset"
                    )
                    .eq("user_id", key)
                    .maybe_single()
                    .execute()
                )
                if resp.data:
                    raw = resp.data
                    start_str = raw.get("chat_quiet_start", "22:00")
                    end_str = raw.get("chat_quiet_end", "08:00")
                    cfg = QuietHoursConfig(
                        enabled=raw.get("chat_quiet_hours_enabled", True),
                        start=time.fromisoformat(start_str),
                        end=time.fromisoformat(end_str),
                        timezone_offset_hours=float(raw.get("chat_timezone_offset", 0.0)),
                    )
                    self._quiet_hours[key] = cfg
                    return cfg
            except Exception as exc:
                self.logger.debug(
                    "Failed to load quiet hours from DB, using defaults",
                    user_id=key,
                    error=str(exc),
                )

        default = QuietHoursConfig()
        self._quiet_hours[key] = default
        return default

    @staticmethod
    def _is_quiet_hour(dt: datetime, cfg: QuietHoursConfig) -> bool:
        """Return ``True`` if *dt* falls within the user's quiet hours.

        Handles overnight ranges (e.g. 22:00 – 08:00).

        Args:
            dt: UTC datetime to check.
            cfg: Quiet hours configuration.

        Returns:
            ``True`` if *dt* is within the quiet window.
        """
        # Convert UTC to user's local time
        local_hour = (dt.hour + cfg.timezone_offset_hours) % 24
        local_minute = dt.minute
        local_time = time(int(local_hour), local_minute)

        start = cfg.start
        end = cfg.end

        if start <= end:
            # Same-day range (e.g. 09:00 – 17:00)
            return start <= local_time < end
        else:
            # Overnight range (e.g. 22:00 – 08:00)
            return local_time >= start or local_time < end

    @staticmethod
    def _seconds_until_quiet_end(dt: datetime, cfg: QuietHoursConfig) -> int:
        """Return the number of seconds until quiet hours end.

        Args:
            dt: Current UTC datetime.
            cfg: Quiet hours configuration.

        Returns:
            Seconds until the quiet window ends.
        """
        local_hour = int((dt.hour + cfg.timezone_offset_hours) % 24)
        local_minute = dt.minute
        local_time = time(local_hour, local_minute)

        end = cfg.end

        # Calculate minutes until end time
        end_minutes = end.hour * 60 + end.minute
        current_minutes = local_time.hour * 60 + local_time.minute

        if end_minutes > current_minutes:
            delta_minutes = end_minutes - current_minutes
        else:
            # End is on the next day
            delta_minutes = (24 * 60 - current_minutes) + end_minutes

        return delta_minutes * 60

    @staticmethod
    def _seconds_until_hour(now: datetime, target_hour: int) -> int:
        """Return seconds until the next occurrence of *target_hour* UTC.

        Args:
            now: Current UTC datetime.
            target_hour: Target UTC hour (0-23).

        Returns:
            Seconds until the target hour.
        """
        candidate = now.replace(minute=0, second=0, microsecond=0)
        if candidate.hour >= target_hour:
            candidate = candidate + timedelta(days=1)
        candidate = candidate.replace(hour=target_hour)
        return int((candidate - now).total_seconds())

    # ------------------------------------------------------------------
    # Database persistence helpers
    # ------------------------------------------------------------------
