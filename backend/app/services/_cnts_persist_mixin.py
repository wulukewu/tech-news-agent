"""Mixin from app/services/chat_notification_timing_service.py."""
from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

logger = logging.getLogger(__name__)


class CntsPersistMixin:
    async def _persist_activity(self, user_id: UUID, platform: str, occurred_at: datetime) -> None:
        """Persist an activity event to the database (best-effort).

        Args:
            user_id: System user UUID.
            platform: Platform of the activity.
            occurred_at: UTC timestamp.
        """
        try:
            self._supabase.table("user_activity_events").insert(
                {
                    "user_id": str(user_id),
                    "platform": platform,
                    "occurred_at": occurred_at.isoformat(),
                    "hour_utc": occurred_at.hour,
                }
            ).execute()
        except Exception as exc:
            self.logger.debug(
                "Failed to persist activity event",
                user_id=str(user_id),
                error=str(exc),
            )

    async def _persist_quiet_hours(self, user_id: UUID, cfg: QuietHoursConfig) -> None:
        """Persist quiet hours configuration to the database (best-effort).

        Args:
            user_id: System user UUID.
            cfg: Quiet hours configuration to persist.
        """
        try:
            self._supabase.table("user_notification_preferences").upsert(
                {
                    "user_id": str(user_id),
                    "chat_quiet_hours_enabled": cfg.enabled,
                    "chat_quiet_start": cfg.start.isoformat(),
                    "chat_quiet_end": cfg.end.isoformat(),
                    "chat_timezone_offset": cfg.timezone_offset_hours,
                }
            ).execute()
        except Exception as exc:
            self.logger.debug(
                "Failed to persist quiet hours",
                user_id=str(user_id),
                error=str(exc),
            )
