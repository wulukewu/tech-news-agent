"""Mixin from app/services/cross_platform_sync.py."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

_RETRY_BASE_DELAY = 0.1
_RETRY_MULTIPLIER = 2.0
_RETRY_MAX_DELAY = 2.0
_RETRY_MAX_ATTEMPTS = 3


class CpsResolveMixin:
    async def resolve_sync_conflict(
        self,
        conflict: dict[str, Any],
    ) -> dict[str, Any]:
        """Resolve a sync conflict using the "latest wins" strategy.

        If both timestamps are equal, the ``web`` platform is preferred over
        ``discord``.

        Args:
            conflict: A dict describing the conflict.  Expected keys:
                ``conversation_id``, ``platform_a``, ``platform_b``,
                ``timestamp_a``, ``timestamp_b``, ``content_a``,
                ``content_b``.

        Returns:
            A ``ConflictResolution`` dict with keys: ``resolved``,
            ``winning_platform``, ``resolution_strategy``,
            ``resolved_content``.

        Validates: Requirements 2.1, 2.4
        """
        self.logger.info(
            "Resolving sync conflict",
            conversation_id=conflict.get("conversation_id"),
            platform_a=conflict.get("platform_a"),
            platform_b=conflict.get("platform_b"),
        )

        # Parse timestamps
        ts_a = self._parse_timestamp(conflict.get("timestamp_a"))
        ts_b = self._parse_timestamp(conflict.get("timestamp_b"))

        platform_a: str = conflict.get("platform_a", "")
        platform_b: str = conflict.get("platform_b", "")
        content_a: str = conflict.get("content_a", "")
        content_b: str = conflict.get("content_b", "")

        # Latest-wins strategy
        if ts_a > ts_b:
            winning_platform = platform_a
            resolved_content = content_a
        elif ts_b > ts_a:
            winning_platform = platform_b
            resolved_content = content_b
        else:
            # Tie-break: prefer 'web' over 'discord'
            if platform_a == PLATFORM_WEB:
                winning_platform = platform_a
                resolved_content = content_a
            elif platform_b == PLATFORM_WEB:
                winning_platform = platform_b
                resolved_content = content_b
            else:
                # Both non-web: prefer platform_a as default
                winning_platform = platform_a
                resolved_content = content_a

        resolution = ConflictResolution(
            resolved=True,
            winning_platform=winning_platform,
            resolution_strategy="latest_wins",
            resolved_content=resolved_content,
        )

        self.logger.info(
            "Conflict resolved",
            conversation_id=conflict.get("conversation_id"),
            winning_platform=winning_platform,
            strategy="latest_wins",
        )

        return {
            "resolved": resolution.resolved,
            "winning_platform": resolution.winning_platform,
            "resolution_strategy": resolution.resolution_strategy,
            "resolved_content": resolution.resolved_content,
        }

    async def get_sync_status(
        self,
        conversation_id: str,
    ) -> dict[str, str]:
        """Return the sync status for each platform for a given conversation.

        Args:
            conversation_id: Identifier of the conversation.

        Returns:
            A dict mapping platform name to status string.  Platforms with
            no recorded status are reported as ``"unknown"``.

        Validates: Requirements 2.1
        """
        status = self._sync_status.get(conversation_id, {})
        # Return a copy to prevent external mutation
        return dict(status) if status else {p: STATUS_UNKNOWN for p in SUPPORTED_PLATFORMS}

    # ------------------------------------------------------------------
    # Retry mechanism
    # ------------------------------------------------------------------

    async def _retry_with_backoff(
        self,
        operation: Callable[[], Coroutine[Any, Any, None]],
        max_retries: int = _RETRY_MAX_ATTEMPTS,
    ) -> None:
        """Execute an async operation with exponential-backoff retry.

        Retries up to ``max_retries`` times on failure.  The delay between
        attempts starts at ``_RETRY_BASE_DELAY`` seconds and doubles each
        time, capped at ``_RETRY_MAX_DELAY`` seconds.

        Args:
            operation: Zero-argument async callable to execute.
            max_retries: Maximum number of attempts (default: 3).

        Raises:
            Exception: The last exception raised by ``operation`` after all
                retries are exhausted.

        Validates: Requirements 2.4
        """
        last_exc: Exception | None = None
        delay = _RETRY_BASE_DELAY

        for attempt in range(1, max_retries + 1):
            try:
                await operation()
                return  # success
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries:
                    self.logger.warning(
                        "Sync operation failed, retrying",
                        attempt=attempt,
                        max_retries=max_retries,
                        delay=delay,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * _RETRY_MULTIPLIER, _RETRY_MAX_DELAY)
                else:
                    self.logger.error(
                        "Sync operation failed after all retries",
                        attempt=attempt,
                        max_retries=max_retries,
                        error=str(exc),
                    )

        if last_exc is not None:
            raise last_exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _set_status(
        self,
        conversation_id: str,
        platform: str,
        status: str,
    ) -> None:
        """Update the sync status for a conversation / platform pair.

        Args:
            conversation_id: Conversation identifier.
            platform: Platform identifier.
            status: New status value.
        """
        if conversation_id not in self._sync_status:
            self._sync_status[conversation_id] = {}
        self._sync_status[conversation_id][platform] = status

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        """Parse a timestamp value into a timezone-aware datetime.

        Args:
            value: Raw timestamp — may be a ``datetime``, ISO-8601 string,
                or ``None``.

        Returns:
            A timezone-aware :class:`datetime`.  Returns the Unix epoch if
            the value cannot be parsed.
        """
        if value is None:
            return datetime.fromtimestamp(0, tz=timezone.utc)
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass
        return datetime.fromtimestamp(0, tz=timezone.utc)
