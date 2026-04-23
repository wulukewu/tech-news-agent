"""
Cross-Platform Sync Service

Handles real-time conversation state synchronisation between Web and Discord
platforms.  Uses an in-memory asyncio.Queue as the primary message queue
(Redis can be substituted later without changing the public interface).

Key capabilities:
- Sync individual messages to one or more target platforms
- Sync full conversation state updates across platforms
- Conflict detection and resolution (latest-wins strategy)
- Exponential-backoff retry for failed sync operations (max 3 retries)
- In-memory sync-status tracking per conversation / platform

Validates: Requirements 2.1, 2.2, 2.4, 2.5
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine

from app.core.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Supported platform identifiers
PLATFORM_WEB = "web"
PLATFORM_DISCORD = "discord"
SUPPORTED_PLATFORMS = {PLATFORM_WEB, PLATFORM_DISCORD}

# Retry configuration
_RETRY_BASE_DELAY = 0.1  # seconds
_RETRY_MULTIPLIER = 2.0
_RETRY_MAX_DELAY = 2.0  # seconds
_RETRY_MAX_ATTEMPTS = 3

# Sync status values
STATUS_SYNCED = "synced"
STATUS_PENDING = "pending"
STATUS_FAILED = "failed"
STATUS_UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ConversationMessage:
    """Represents a single conversation message to be synced.

    Attributes:
        id: Unique message identifier.
        conversation_id: Parent conversation identifier.
        role: Author role — ``"user"`` or ``"assistant"``.
        content: Text content of the message.
        platform: Originating platform (``"web"`` or ``"discord"``).
        timestamp: UTC timestamp of the message.
        metadata: Optional arbitrary metadata dict.
    """

    id: str
    conversation_id: str
    role: str
    content: str
    platform: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncResult:
    """Result of a sync operation.

    Attributes:
        success: Whether the overall sync succeeded.
        synced_platforms: Platforms that were successfully synced.
        failed_platforms: Platforms that failed to sync.
        errors: Human-readable error messages for each failure.
        sync_timestamp: UTC timestamp when the sync was performed.
    """

    success: bool
    synced_platforms: list[str]
    failed_platforms: list[str]
    errors: list[str]
    sync_timestamp: datetime


@dataclass
class SyncConflict:
    """Represents a detected sync conflict between two platforms.

    Attributes:
        conversation_id: Conversation where the conflict occurred.
        platform_a: First platform involved.
        platform_b: Second platform involved.
        timestamp_a: Timestamp of the message on platform_a.
        timestamp_b: Timestamp of the message on platform_b.
        content_a: Message content from platform_a.
        content_b: Message content from platform_b.
    """

    conversation_id: str
    platform_a: str
    platform_b: str
    timestamp_a: datetime
    timestamp_b: datetime
    content_a: str
    content_b: str


@dataclass
class ConflictResolution:
    """Result of resolving a sync conflict.

    Attributes:
        resolved: Whether the conflict was successfully resolved.
        winning_platform: The platform whose content was chosen.
        resolution_strategy: Strategy used — ``"latest_wins"`` or ``"merge"``.
        resolved_content: The final resolved content.
    """

    resolved: bool
    winning_platform: str
    resolution_strategy: str  # 'latest_wins' | 'merge'
    resolved_content: str


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class CrossPlatformSyncService:
    """Service for synchronising conversation state across platforms.

    Uses an in-memory ``asyncio.Queue`` as the message queue.  A Redis-backed
    queue can be substituted by replacing ``_queue`` with a Redis stream
    consumer without changing the public interface.

    Sync status is tracked in ``_sync_status``:
        ``{conversation_id: {platform: status}}``

    Status values: ``"synced"``, ``"pending"``, ``"failed"``, ``"unknown"``

    Validates: Requirements 2.1, 2.2, 2.4, 2.5
    """

    def __init__(self) -> None:
        """Initialise the sync service with an in-memory queue."""
        # NOTE: Replace with a Redis-backed queue for production multi-process
        # deployments.  The interface remains identical.
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        # conversation_id -> {platform -> status}
        self._sync_status: dict[str, dict[str, str]] = {}

        self.logger = get_logger(f"{__name__}.CrossPlatformSyncService")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def sync_message(
        self,
        message: ConversationMessage,
        target_platforms: list[str],
    ) -> SyncResult:
        """Sync a single message to one or more target platforms.

        The source platform of the message is excluded from the target list
        automatically to avoid echo-back.

        Args:
            message: The message to sync.
            target_platforms: Platforms to sync the message to.

        Returns:
            A :class:`SyncResult` describing which platforms succeeded or
            failed.

        Validates: Requirements 2.1, 2.2
        """
        self.logger.info(
            "Syncing message",
            message_id=message.id,
            conversation_id=message.conversation_id,
            source_platform=message.platform,
            target_platforms=target_platforms,
        )

        # Exclude the source platform from targets
        effective_targets = [p for p in target_platforms if p != message.platform]

        synced: list[str] = []
        failed: list[str] = []
        errors: list[str] = []

        for platform in effective_targets:
            self._set_status(message.conversation_id, platform, STATUS_PENDING)

            async def _do_sync(p: str = platform) -> None:
                payload: dict[str, Any] = {
                    "type": "message",
                    "message_id": message.id,
                    "conversation_id": message.conversation_id,
                    "role": message.role,
                    "content": message.content,
                    "source_platform": message.platform,
                    "target_platform": p,
                    "timestamp": message.timestamp.isoformat(),
                    "metadata": message.metadata,
                }
                await self._queue.put(payload)

            try:
                await self._retry_with_backoff(_do_sync)
                synced.append(platform)
                self._set_status(message.conversation_id, platform, STATUS_SYNCED)
                self.logger.info(
                    "Message synced to platform",
                    message_id=message.id,
                    platform=platform,
                )
            except Exception as exc:
                failed.append(platform)
                error_msg = f"Failed to sync to {platform}: {exc}"
                errors.append(error_msg)
                self._set_status(message.conversation_id, platform, STATUS_FAILED)
                self.logger.error(
                    "Message sync failed",
                    message_id=message.id,
                    platform=platform,
                    error=str(exc),
                )

        success = len(failed) == 0
        return SyncResult(
            success=success,
            synced_platforms=synced,
            failed_platforms=failed,
            errors=errors,
            sync_timestamp=datetime.now(timezone.utc),
        )

    async def sync_conversation_state(
        self,
        conversation_id: str,
        state_update: dict[str, Any],
    ) -> SyncResult:
        """Sync a conversation state update to all known platforms.

        Enqueues a state-update event for every platform that has a tracked
        sync status for the given conversation.  If no platforms are tracked
        yet, the update is enqueued for all supported platforms.

        Args:
            conversation_id: Identifier of the conversation to update.
            state_update: Dictionary of state fields to update (e.g. title,
                tags, is_archived).

        Returns:
            A :class:`SyncResult` describing which platforms succeeded or
            failed.

        Validates: Requirements 2.1, 2.4
        """
        self.logger.info(
            "Syncing conversation state",
            conversation_id=conversation_id,
            fields=list(state_update.keys()),
        )

        # Determine target platforms from tracked status or fall back to all
        tracked = self._sync_status.get(conversation_id, {})
        target_platforms = list(tracked.keys()) if tracked else list(SUPPORTED_PLATFORMS)

        synced: list[str] = []
        failed: list[str] = []
        errors: list[str] = []

        for platform in target_platforms:
            self._set_status(conversation_id, platform, STATUS_PENDING)

            async def _do_state_sync(p: str = platform) -> None:
                payload: dict[str, Any] = {
                    "type": "state_update",
                    "conversation_id": conversation_id,
                    "target_platform": p,
                    "state_update": state_update,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await self._queue.put(payload)

            try:
                await self._retry_with_backoff(_do_state_sync)
                synced.append(platform)
                self._set_status(conversation_id, platform, STATUS_SYNCED)
                self.logger.info(
                    "Conversation state synced",
                    conversation_id=conversation_id,
                    platform=platform,
                )
            except Exception as exc:
                failed.append(platform)
                error_msg = f"Failed to sync state to {platform}: {exc}"
                errors.append(error_msg)
                self._set_status(conversation_id, platform, STATUS_FAILED)
                self.logger.error(
                    "Conversation state sync failed",
                    conversation_id=conversation_id,
                    platform=platform,
                    error=str(exc),
                )

        success = len(failed) == 0
        return SyncResult(
            success=success,
            synced_platforms=synced,
            failed_platforms=failed,
            errors=errors,
            sync_timestamp=datetime.now(timezone.utc),
        )

    async def handle_platform_message(
        self,
        platform_message: dict[str, Any],
    ) -> dict[str, Any]:
        """Process an incoming platform-specific message and normalise it.

        Validates the message structure, extracts required fields, and
        returns a normalised ``ProcessedMessage`` dict suitable for further
        processing by the conversation manager.

        Args:
            platform_message: Raw message dict from a platform adapter.
                Expected keys: ``conversation_id``, ``content``,
                ``platform``.  Optional: ``role``, ``timestamp``,
                ``metadata``, ``message_id``.

        Returns:
            A normalised ``ProcessedMessage`` dict with keys:
            ``conversation_id``, ``content``, ``platform``, ``role``,
            ``timestamp``, ``metadata``, ``message_id``, ``processed``.

        Validates: Requirements 2.2, 2.5
        """
        self.logger.debug(
            "Handling platform message",
            platform=platform_message.get("platform"),
            conversation_id=platform_message.get("conversation_id"),
        )

        # Validate required fields
        required_fields = ["conversation_id", "content", "platform"]
        missing = [f for f in required_fields if not platform_message.get(f)]
        if missing:
            self.logger.warning(
                "Platform message missing required fields",
                missing_fields=missing,
            )
            return {
                "processed": False,
                "error": f"Missing required fields: {missing}",
                "original": platform_message,
            }

        platform = platform_message["platform"]
        if platform not in SUPPORTED_PLATFORMS:
            self.logger.warning(
                "Unsupported platform in message",
                platform=platform,
            )
            return {
                "processed": False,
                "error": f"Unsupported platform: {platform}",
                "original": platform_message,
            }

        # Parse timestamp
        raw_ts = platform_message.get("timestamp")
        if raw_ts is None:
            timestamp = datetime.now(timezone.utc)
        elif isinstance(raw_ts, datetime):
            timestamp = raw_ts if raw_ts.tzinfo else raw_ts.replace(tzinfo=timezone.utc)
        else:
            try:
                timestamp = datetime.fromisoformat(str(raw_ts).replace("Z", "+00:00"))
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                timestamp = datetime.now(timezone.utc)

        processed: dict[str, Any] = {
            "message_id": platform_message.get("message_id", ""),
            "conversation_id": platform_message["conversation_id"],
            "content": platform_message["content"],
            "platform": platform,
            "role": platform_message.get("role", "user"),
            "timestamp": timestamp,
            "metadata": platform_message.get("metadata", {}),
            "processed": True,
        }

        self.logger.debug(
            "Platform message processed",
            conversation_id=processed["conversation_id"],
            platform=processed["platform"],
        )
        return processed

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
