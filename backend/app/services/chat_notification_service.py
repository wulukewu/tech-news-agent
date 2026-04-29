"""
Chat Notification Service

Cross-platform notification service for the chat persistence system.
Handles sending notifications when conversations receive new responses
across Web (push) and Discord (DM) channels.

Key capabilities:
- Unified notification interface for Web push and Discord DM
- Platform-specific message formatting
- Notification queue with batch sending support
- User notification preference management
- Notification history tracking

Validates: Requirements 10.1, 10.4

See also: chat_notification_timing_service.py for smart timing logic (Req 10.2, 10.3, 10.5)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

import discord

from app.core.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Supported notification channels
CHANNEL_WEB_PUSH = "web_push"
CHANNEL_DISCORD_DM = "discord_dm"
SUPPORTED_CHANNELS = {CHANNEL_WEB_PUSH, CHANNEL_DISCORD_DM}

# Notification types
NOTIF_NEW_RESPONSE = "new_response"  # AI replied to a conversation
NOTIF_CROSS_PLATFORM = "cross_platform"  # New message from another platform
NOTIF_REMINDER = "reminder"  # Gentle reminder for stale conversation

# Retry configuration (mirrors cross_platform_sync.py pattern)
_RETRY_BASE_DELAY = 0.5  # seconds
_RETRY_MULTIPLIER = 2.0
_RETRY_MAX_DELAY = 8.0  # seconds
_RETRY_MAX_ATTEMPTS = 3

# Discord embed colour for chat notifications
_DISCORD_EMBED_COLOUR = 0x5865F2  # Discord blurple


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

from app.services._cn_delivery_mixin import DeliveryMixin


class NotificationPriority(str, Enum):
    """Priority level for a notification."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


@dataclass
class ChatNotificationPayload:
    """Describes a single chat notification to be delivered.

    Attributes:
        user_id: System user UUID.
        notification_type: One of the NOTIF_* constants.
        conversation_id: UUID of the relevant conversation.
        conversation_title: Human-readable conversation title.
        message_preview: Short preview of the triggering message (≤ 200 chars).
        source_platform: Platform where the triggering event occurred.
        priority: Delivery priority.
        metadata: Optional extra data (e.g. message_id, sender_name).
    """

    user_id: UUID
    notification_type: str
    conversation_id: UUID
    conversation_title: str
    message_preview: str
    source_platform: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationDeliveryResult:
    """Result of a single notification delivery attempt.

    Attributes:
        success: Whether delivery succeeded.
        channel: Channel used (CHANNEL_WEB_PUSH or CHANNEL_DISCORD_DM).
        notification_type: Type of notification sent.
        user_id: Target user UUID.
        error: Human-readable error message on failure.
        delivered_at: UTC timestamp of delivery (set on success).
    """

    success: bool
    channel: str
    notification_type: str
    user_id: UUID
    error: Optional[str] = None
    delivered_at: Optional[datetime] = None


@dataclass
class UserNotificationPreferences:
    """Notification preferences for a single user.

    Attributes:
        user_id: System user UUID.
        web_push_enabled: Whether Web push notifications are enabled.
        discord_dm_enabled: Whether Discord DM notifications are enabled.
        discord_user_id: Discord snowflake ID (required for DM delivery).
        enabled_types: Set of notification types the user wants to receive.
            Empty set means all types are enabled.
    """

    user_id: UUID
    web_push_enabled: bool = True
    discord_dm_enabled: bool = True
    discord_user_id: Optional[str] = None
    enabled_types: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ChatNotificationService(DeliveryMixin):
    """Cross-platform notification service for the chat persistence system.

    Delivers notifications to users when their conversations receive new
    responses or cross-platform activity occurs.  Supports Web push and
    Discord DM channels.

    The service is intentionally decoupled from the smart-timing logic
    (see :class:`~app.services.chat_notification_timing_service.ChatNotificationTimingService`).
    Callers should consult the timing service before invoking
    :meth:`send_notification` to respect user quiet hours and frequency
    limits.

    Validates: Requirements 10.1, 10.4
    """

    def __init__(
        self,
        bot: Optional[discord.Client] = None,
        supabase_client: Any = None,
    ) -> None:
        """Initialise the service.

        Args:
            bot: Discord bot client used for DM delivery.  When ``None``,
                Discord DM notifications are silently skipped.
            supabase_client: Supabase client for preference and history
                lookups.  When ``None``, preferences default to all-enabled
                and history is not persisted.
        """
        self._bot = bot
        self._supabase = supabase_client
        self._queue: asyncio.Queue[ChatNotificationPayload] = asyncio.Queue()
        self.logger = get_logger(f"{__name__}.ChatNotificationService")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def send_notification(
        self,
        payload: ChatNotificationPayload,
    ) -> list[NotificationDeliveryResult]:
        """Deliver a chat notification to all enabled channels for the user.

        Fetches the user's notification preferences, then attempts delivery
        on each enabled channel.  Each channel attempt uses exponential-
        backoff retry (up to 3 attempts).

        Args:
            payload: Notification payload describing what to send and to whom.

        Returns:
            A list of :class:`NotificationDeliveryResult` — one entry per
            channel that was attempted.

        Validates: Requirements 10.1, 10.4
        """
        self.logger.info(
            "Delivering chat notification",
            user_id=str(payload.user_id),
            notification_type=payload.notification_type,
            conversation_id=str(payload.conversation_id),
            source_platform=payload.source_platform,
        )

        prefs = await self._get_user_preferences(payload.user_id)
        results: list[NotificationDeliveryResult] = []

        # Determine which notification types the user wants
        if prefs.enabled_types and payload.notification_type not in prefs.enabled_types:
            self.logger.debug(
                "Notification type filtered by user preferences",
                user_id=str(payload.user_id),
                notification_type=payload.notification_type,
            )
            return results

        # --- Web push ---
        if prefs.web_push_enabled:
            result = await self._deliver_web_push(payload)
            results.append(result)
            await self._record_delivery(payload, result)

        # --- Discord DM ---
        if prefs.discord_dm_enabled and prefs.discord_user_id:
            result = await self._deliver_discord_dm(payload, prefs.discord_user_id)
            results.append(result)
            await self._record_delivery(payload, result)

        successful = sum(1 for r in results if r.success)
        self.logger.info(
            "Chat notification delivery complete",
            user_id=str(payload.user_id),
            total_channels=len(results),
            successful=successful,
        )
        return results

    async def send_batch_notifications(
        self,
        payloads: list[ChatNotificationPayload],
    ) -> dict[str, list[NotificationDeliveryResult]]:
        """Deliver multiple notifications concurrently.

        Notifications are dispatched concurrently using ``asyncio.gather``.
        Each payload is processed independently; a failure in one does not
        affect the others.

        Args:
            payloads: List of notification payloads to deliver.

        Returns:
            A dict mapping ``str(payload.user_id)`` to the list of delivery
            results for that payload.

        Validates: Requirements 10.1, 10.4
        """
        self.logger.info(
            "Starting batch notification delivery",
            count=len(payloads),
        )

        tasks = [self.send_notification(p) for p in payloads]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        output: dict[str, list[NotificationDeliveryResult]] = {}
        for payload, result in zip(payloads, all_results):
            key = str(payload.user_id)
            if isinstance(result, Exception):
                self.logger.error(
                    "Batch notification failed for user",
                    user_id=key,
                    error=str(result),
                )
                output[key] = [
                    NotificationDeliveryResult(
                        success=False,
                        channel="all",
                        notification_type=payload.notification_type,
                        user_id=payload.user_id,
                        error=str(result),
                    )
                ]
            else:
                output[key] = result  # type: ignore[assignment]

        return output

    async def enqueue_notification(self, payload: ChatNotificationPayload) -> None:
        """Add a notification to the internal queue for deferred delivery.

        Use this when you want fire-and-forget semantics.  Call
        :meth:`process_queue` in a background task to drain the queue.

        Args:
            payload: Notification payload to enqueue.
        """
        await self._queue.put(payload)
        self.logger.debug(
            "Notification enqueued",
            user_id=str(payload.user_id),
            notification_type=payload.notification_type,
            queue_size=self._queue.qsize(),
        )

    async def process_queue(self, max_items: int = 50) -> int:
        """Drain up to *max_items* notifications from the internal queue.

        Intended to be called periodically from a background task or
        scheduler.

        Args:
            max_items: Maximum number of notifications to process in one
                call.

        Returns:
            Number of notifications processed.
        """
        processed = 0
        while processed < max_items and not self._queue.empty():
            try:
                payload = self._queue.get_nowait()
                await self.send_notification(payload)
                self._queue.task_done()
                processed += 1
            except asyncio.QueueEmpty:
                break
            except Exception as exc:
                self.logger.error(
                    "Error processing queued notification",
                    error=str(exc),
                )
                processed += 1  # count as processed to avoid infinite loop

        if processed:
            self.logger.info("Processed queued notifications", count=processed)
        return processed

    async def get_user_preferences(self, user_id: UUID) -> UserNotificationPreferences:
        """Return the notification preferences for a user (public wrapper).

        Args:
            user_id: System user UUID.

        Returns:
            :class:`UserNotificationPreferences` for the user.
        """
        return await self._get_user_preferences(user_id)

    async def update_user_preferences(
        self,
        user_id: UUID,
        web_push_enabled: Optional[bool] = None,
        discord_dm_enabled: Optional[bool] = None,
        enabled_types: Optional[set[str]] = None,
    ) -> bool:
        """Persist updated notification preferences for a user.

        Only the fields that are not ``None`` are updated.

        Args:
            user_id: System user UUID.
            web_push_enabled: New value for web push toggle, or ``None`` to
                leave unchanged.
            discord_dm_enabled: New value for Discord DM toggle, or ``None``
                to leave unchanged.
            enabled_types: New set of enabled notification types, or ``None``
                to leave unchanged.

        Returns:
            ``True`` if the update succeeded, ``False`` otherwise.

        Validates: Requirements 10.4
        """
        if self._supabase is None:
            self.logger.warning(
                "Cannot update preferences — no Supabase client",
                user_id=str(user_id),
            )
            return False

        try:
            updates: dict[str, Any] = {}
            if web_push_enabled is not None:
                updates["chat_web_push_enabled"] = web_push_enabled
            if discord_dm_enabled is not None:
                updates["chat_discord_dm_enabled"] = discord_dm_enabled
            if enabled_types is not None:
                updates["chat_notification_types"] = list(enabled_types)

            if not updates:
                return True  # nothing to do

            self._supabase.table("user_notification_preferences").upsert(
                {"user_id": str(user_id), **updates}
            ).execute()

            self.logger.info(
                "User notification preferences updated",
                user_id=str(user_id),
                fields=list(updates.keys()),
            )
            return True

        except Exception as exc:
            self.logger.error(
                "Failed to update user notification preferences",
                user_id=str(user_id),
                error=str(exc),
            )
            return False

    # ------------------------------------------------------------------
    # Delivery helpers
    # ------------------------------------------------------------------
