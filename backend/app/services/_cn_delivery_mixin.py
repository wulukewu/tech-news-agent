"""Mixin extracted from chat_notification_service.py."""
from __future__ import annotations

import asyncio
from typing import Any, Optional
from uuid import UUID

import discord

from app.core.logger import get_logger

logger = get_logger(__name__)

_RETRY_BASE_DELAY = 0.5
_RETRY_MULTIPLIER = 2.0
_RETRY_MAX_DELAY = 8.0
_RETRY_MAX_ATTEMPTS = 3


class DeliveryMixin:
    async def _deliver_web_push(
        self, payload: ChatNotificationPayload
    ) -> NotificationDeliveryResult:
        """Deliver a Web push notification.

        Currently stores the notification in the ``chat_notifications`` table
        so the frontend can poll or use Supabase Realtime to receive it.
        A future iteration can integrate a proper Web Push (VAPID) service.

        Args:
            payload: Notification payload.

        Returns:
            :class:`NotificationDeliveryResult` for the web_push channel.
        """

        async def _attempt() -> None:
            if self._supabase is None:
                # No Supabase client — treat as no-op success so tests pass
                return

            record = {
                "user_id": str(payload.user_id),
                "notification_type": payload.notification_type,
                "conversation_id": str(payload.conversation_id),
                "conversation_title": payload.conversation_title,
                "message_preview": payload.message_preview[:200],
                "source_platform": payload.source_platform,
                "channel": CHANNEL_WEB_PUSH,
                "priority": payload.priority.value,
                "is_read": False,
                "metadata": payload.metadata,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._supabase.table("chat_notifications").insert(record).execute()

        try:
            await self._retry_with_backoff(_attempt)
            return NotificationDeliveryResult(
                success=True,
                channel=CHANNEL_WEB_PUSH,
                notification_type=payload.notification_type,
                user_id=payload.user_id,
                delivered_at=datetime.now(timezone.utc),
            )
        except Exception as exc:
            self.logger.error(
                "Web push delivery failed",
                user_id=str(payload.user_id),
                error=str(exc),
            )
            return NotificationDeliveryResult(
                success=False,
                channel=CHANNEL_WEB_PUSH,
                notification_type=payload.notification_type,
                user_id=payload.user_id,
                error=str(exc),
            )

    async def _deliver_discord_dm(
        self,
        payload: ChatNotificationPayload,
        discord_user_id: str,
    ) -> NotificationDeliveryResult:
        """Deliver a Discord DM notification.

        Builds a rich embed and sends it via the Discord bot.

        Args:
            payload: Notification payload.
            discord_user_id: Discord snowflake ID of the target user.

        Returns:
            :class:`NotificationDeliveryResult` for the discord_dm channel.
        """
        if self._bot is None:
            self.logger.debug(
                "Discord DM skipped — no bot client",
                user_id=str(payload.user_id),
            )
            return NotificationDeliveryResult(
                success=False,
                channel=CHANNEL_DISCORD_DM,
                notification_type=payload.notification_type,
                user_id=payload.user_id,
                error="Discord bot not available",
            )

        embed = self._build_discord_embed(payload)

        async def _attempt() -> None:
            if not discord_user_id.isdigit():
                raise ValueError(f"Invalid Discord user ID: {discord_user_id!r}")
            user = await self._bot.fetch_user(int(discord_user_id))  # type: ignore[union-attr]
            await user.send(embed=embed)

        try:
            await self._retry_with_backoff(_attempt)
            self.logger.info(
                "Discord DM delivered",
                user_id=str(payload.user_id),
                discord_user_id=discord_user_id,
            )
            return NotificationDeliveryResult(
                success=True,
                channel=CHANNEL_DISCORD_DM,
                notification_type=payload.notification_type,
                user_id=payload.user_id,
                delivered_at=datetime.now(timezone.utc),
            )
        except discord.Forbidden:
            msg = "User has DMs disabled or has blocked the bot"
            self.logger.warning(
                "Discord DM forbidden",
                user_id=str(payload.user_id),
                discord_user_id=discord_user_id,
            )
            return NotificationDeliveryResult(
                success=False,
                channel=CHANNEL_DISCORD_DM,
                notification_type=payload.notification_type,
                user_id=payload.user_id,
                error=msg,
            )
        except Exception as exc:
            self.logger.error(
                "Discord DM delivery failed",
                user_id=str(payload.user_id),
                discord_user_id=discord_user_id,
                error=str(exc),
            )
            return NotificationDeliveryResult(
                success=False,
                channel=CHANNEL_DISCORD_DM,
                notification_type=payload.notification_type,
                user_id=payload.user_id,
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Preference helpers
    # ------------------------------------------------------------------

    async def _get_user_preferences(self, user_id: UUID) -> UserNotificationPreferences:
        """Fetch notification preferences from the database.

        Falls back to all-enabled defaults when the Supabase client is not
        available or the user has no stored preferences.

        Args:
            user_id: System user UUID.

        Returns:
            :class:`UserNotificationPreferences` for the user.
        """
        if self._supabase is None:
            return UserNotificationPreferences(user_id=user_id)

        try:
            # Fetch chat-specific notification preferences
            pref_resp = (
                self._supabase.table("user_notification_preferences")
                .select("chat_web_push_enabled, chat_discord_dm_enabled, chat_notification_types")
                .eq("user_id", str(user_id))
                .maybe_single()
                .execute()
            )

            # Fetch Discord ID from platform links
            link_resp = (
                self._supabase.table("user_platform_links")
                .select("platform_user_id")
                .eq("user_id", str(user_id))
                .eq("platform", "discord")
                .eq("is_active", True)
                .maybe_single()
                .execute()
            )

            discord_user_id: Optional[str] = None
            if link_resp.data:
                discord_user_id = link_resp.data.get("platform_user_id")

            if pref_resp.data:
                raw = pref_resp.data
                enabled_types_raw = raw.get("chat_notification_types") or []
                return UserNotificationPreferences(
                    user_id=user_id,
                    web_push_enabled=raw.get("chat_web_push_enabled", True),
                    discord_dm_enabled=raw.get("chat_discord_dm_enabled", True),
                    discord_user_id=discord_user_id,
                    enabled_types=set(enabled_types_raw),
                )

            # No preferences row — return defaults with Discord ID if available
            return UserNotificationPreferences(
                user_id=user_id,
                discord_user_id=discord_user_id,
            )

        except Exception as exc:
            self.logger.warning(
                "Failed to fetch user notification preferences, using defaults",
                user_id=str(user_id),
                error=str(exc),
            )
            return UserNotificationPreferences(user_id=user_id)

    # ------------------------------------------------------------------
    # History recording
    # ------------------------------------------------------------------

    async def _record_delivery(
        self,
        payload: ChatNotificationPayload,
        result: NotificationDeliveryResult,
    ) -> None:
        """Persist a delivery attempt to the notification history table.

        Silently swallows errors so that a history write failure never
        prevents the caller from continuing.

        Args:
            payload: The original notification payload.
            result: The delivery result to record.
        """
        if self._supabase is None:
            return

        try:
            record = {
                "user_id": str(payload.user_id),
                "conversation_id": str(payload.conversation_id),
                "notification_type": payload.notification_type,
                "channel": result.channel,
                "success": result.success,
                "error": result.error,
                "delivered_at": (result.delivered_at.isoformat() if result.delivered_at else None),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._supabase.table("chat_notification_history").insert(record).execute()
        except Exception as exc:
            self.logger.debug(
                "Failed to record notification history",
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Discord embed builder
    # ------------------------------------------------------------------

    def _build_discord_embed(self, payload: ChatNotificationPayload) -> discord.Embed:
        """Build a Discord embed for a chat notification.

        Args:
            payload: Notification payload.

        Returns:
            A :class:`discord.Embed` ready to send.
        """
        type_labels = {
            NOTIF_NEW_RESPONSE: ("💬 New Response", "Your conversation has a new reply."),
            NOTIF_CROSS_PLATFORM: (
                "🔄 Cross-Platform Update",
                "New activity from another platform.",
            ),
            NOTIF_REMINDER: ("⏰ Conversation Reminder", "You have an unfinished conversation."),
        }
        title, description = type_labels.get(
            payload.notification_type,
            ("🔔 Notification", "You have a new notification."),
        )

        embed = discord.Embed(
            title=title,
            description=description,
            colour=_DISCORD_EMBED_COLOUR,
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(
            name="Conversation",
            value=payload.conversation_title[:256],
            inline=False,
        )

        preview = payload.message_preview[:200]
        if preview:
            embed.add_field(name="Preview", value=f"> {preview}", inline=False)

        embed.add_field(
            name="Platform",
            value=payload.source_platform.capitalize(),
            inline=True,
        )
        embed.set_footer(text="Use /conversations to manage your chats")
        return embed

    # ------------------------------------------------------------------
    # Retry mechanism (mirrors cross_platform_sync.py)
    # ------------------------------------------------------------------

    async def _retry_with_backoff(
        self,
        operation: Any,
        max_retries: int = _RETRY_MAX_ATTEMPTS,
    ) -> None:
        """Execute an async callable with exponential-backoff retry.

        Args:
            operation: Zero-argument async callable.
            max_retries: Maximum number of attempts.

        Raises:
            Exception: The last exception after all retries are exhausted.
        """
        last_exc: Optional[Exception] = None
        delay = _RETRY_BASE_DELAY

        for attempt in range(1, max_retries + 1):
            try:
                await operation()
                return
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries:
                    self.logger.warning(
                        "Notification delivery attempt failed, retrying",
                        attempt=attempt,
                        max_retries=max_retries,
                        delay=delay,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * _RETRY_MULTIPLIER, _RETRY_MAX_DELAY)
                else:
                    self.logger.error(
                        "Notification delivery failed after all retries",
                        attempt=attempt,
                        error=str(exc),
                    )

        if last_exc is not None:
            raise last_exc
