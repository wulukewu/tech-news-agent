"""
Unit tests for CrossPlatformSyncService

Tests cover:
- sync_message: successful sync, source-platform exclusion, failure handling
- sync_conversation_state: state update enqueuing, status tracking
- handle_platform_message: normalisation, validation, unsupported platforms
- resolve_sync_conflict: latest-wins strategy, tie-break logic
- get_sync_status: status retrieval, unknown-platform defaults
- _retry_with_backoff: retry count, exponential delay, success on retry
- _parse_timestamp: various input types

Validates: Requirements 2.1, 2.2, 2.4, 2.5
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.cross_platform_sync import (
    PLATFORM_DISCORD,
    PLATFORM_WEB,
    STATUS_FAILED,
    STATUS_SYNCED,
    STATUS_UNKNOWN,
    SUPPORTED_PLATFORMS,
    ConflictResolution,
    ConversationMessage,
    CrossPlatformSyncService,
    SyncConflict,
    SyncResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(timezone.utc)


def _make_message(
    *,
    conversation_id: str = "conv-1",
    platform: str = PLATFORM_WEB,
    content: str = "Hello",
    timestamp: datetime | None = None,
) -> ConversationMessage:
    return ConversationMessage(
        id="msg-1",
        conversation_id=conversation_id,
        role="user",
        content=content,
        platform=platform,
        timestamp=timestamp or _NOW,
    )


def _make_service() -> CrossPlatformSyncService:
    return CrossPlatformSyncService()


# ---------------------------------------------------------------------------
# Data model tests
# ---------------------------------------------------------------------------


class TestDataModels:
    def test_sync_result_fields(self):
        result = SyncResult(
            success=True,
            synced_platforms=["web"],
            failed_platforms=[],
            errors=[],
            sync_timestamp=_NOW,
        )
        assert result.success is True
        assert result.synced_platforms == ["web"]
        assert result.failed_platforms == []
        assert result.errors == []

    def test_conversation_message_defaults(self):
        msg = ConversationMessage(
            id="m1",
            conversation_id="c1",
            role="user",
            content="hi",
            platform=PLATFORM_WEB,
            timestamp=_NOW,
        )
        assert msg.metadata == {}

    def test_sync_conflict_fields(self):
        conflict = SyncConflict(
            conversation_id="c1",
            platform_a=PLATFORM_WEB,
            platform_b=PLATFORM_DISCORD,
            timestamp_a=_NOW,
            timestamp_b=_NOW,
            content_a="web content",
            content_b="discord content",
        )
        assert conflict.conversation_id == "c1"

    def test_conflict_resolution_fields(self):
        resolution = ConflictResolution(
            resolved=True,
            winning_platform=PLATFORM_WEB,
            resolution_strategy="latest_wins",
            resolved_content="web content",
        )
        assert resolution.resolved is True
        assert resolution.resolution_strategy == "latest_wins"


# ---------------------------------------------------------------------------
# sync_message
# ---------------------------------------------------------------------------


class TestSyncMessage:
    @pytest.mark.asyncio
    async def test_sync_to_single_platform_succeeds(self):
        svc = _make_service()
        msg = _make_message(platform=PLATFORM_WEB)
        result = await svc.sync_message(msg, [PLATFORM_DISCORD])

        assert result.success is True
        assert PLATFORM_DISCORD in result.synced_platforms
        assert result.failed_platforms == []
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_source_platform_excluded_from_targets(self):
        """The source platform should not appear in synced_platforms."""
        svc = _make_service()
        msg = _make_message(platform=PLATFORM_WEB)
        # Pass both platforms; web (source) should be excluded
        result = await svc.sync_message(msg, [PLATFORM_WEB, PLATFORM_DISCORD])

        assert PLATFORM_WEB not in result.synced_platforms
        assert PLATFORM_DISCORD in result.synced_platforms

    @pytest.mark.asyncio
    async def test_sync_to_no_effective_targets_returns_success(self):
        """If all targets equal the source platform, result is success with empty lists."""
        svc = _make_service()
        msg = _make_message(platform=PLATFORM_WEB)
        result = await svc.sync_message(msg, [PLATFORM_WEB])

        assert result.success is True
        assert result.synced_platforms == []
        assert result.failed_platforms == []

    @pytest.mark.asyncio
    async def test_sync_failure_recorded_in_result(self):
        """When the queue raises, the platform should appear in failed_platforms."""
        svc = _make_service()
        msg = _make_message(platform=PLATFORM_WEB)

        # Make the queue raise on every put
        svc._queue = MagicMock()
        svc._queue.put = AsyncMock(side_effect=RuntimeError("queue full"))

        result = await svc.sync_message(msg, [PLATFORM_DISCORD])

        assert result.success is False
        assert PLATFORM_DISCORD in result.failed_platforms
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_sync_result_has_timestamp(self):
        svc = _make_service()
        msg = _make_message()
        result = await svc.sync_message(msg, [PLATFORM_DISCORD])
        assert isinstance(result.sync_timestamp, datetime)
        assert result.sync_timestamp.tzinfo is not None

    @pytest.mark.asyncio
    async def test_message_enqueued_with_correct_payload(self):
        svc = _make_service()
        msg = _make_message(platform=PLATFORM_WEB, content="Test content")

        result = await svc.sync_message(msg, [PLATFORM_DISCORD])

        assert result.success is True
        # Verify the item was placed on the queue
        assert not svc._queue.empty()
        item = await svc._queue.get()
        assert item["type"] == "message"
        assert item["content"] == "Test content"
        assert item["target_platform"] == PLATFORM_DISCORD
        assert item["source_platform"] == PLATFORM_WEB

    @pytest.mark.asyncio
    async def test_status_set_to_synced_on_success(self):
        svc = _make_service()
        msg = _make_message(conversation_id="conv-abc", platform=PLATFORM_WEB)
        await svc.sync_message(msg, [PLATFORM_DISCORD])

        status = await svc.get_sync_status("conv-abc")
        assert status[PLATFORM_DISCORD] == STATUS_SYNCED

    @pytest.mark.asyncio
    async def test_status_set_to_failed_on_error(self):
        svc = _make_service()
        msg = _make_message(conversation_id="conv-fail", platform=PLATFORM_WEB)
        svc._queue = MagicMock()
        svc._queue.put = AsyncMock(side_effect=RuntimeError("error"))

        await svc.sync_message(msg, [PLATFORM_DISCORD])

        status = await svc.get_sync_status("conv-fail")
        assert status[PLATFORM_DISCORD] == STATUS_FAILED


# ---------------------------------------------------------------------------
# sync_conversation_state
# ---------------------------------------------------------------------------


class TestSyncConversationState:
    @pytest.mark.asyncio
    async def test_syncs_to_all_supported_platforms_when_no_tracked(self):
        svc = _make_service()
        result = await svc.sync_conversation_state("conv-1", {"title": "New Title"})

        assert result.success is True
        assert set(result.synced_platforms) == SUPPORTED_PLATFORMS

    @pytest.mark.asyncio
    async def test_syncs_only_to_tracked_platforms(self):
        svc = _make_service()
        # Pre-track only discord
        svc._set_status("conv-2", PLATFORM_DISCORD, STATUS_SYNCED)

        result = await svc.sync_conversation_state("conv-2", {"is_archived": True})

        assert result.success is True
        assert result.synced_platforms == [PLATFORM_DISCORD]

    @pytest.mark.asyncio
    async def test_state_update_enqueued_with_correct_payload(self):
        svc = _make_service()
        await svc.sync_conversation_state("conv-3", {"tags": ["ai"]})

        # Drain the queue and check payloads
        items = []
        while not svc._queue.empty():
            items.append(await svc._queue.get())

        assert len(items) == len(SUPPORTED_PLATFORMS)
        for item in items:
            assert item["type"] == "state_update"
            assert item["conversation_id"] == "conv-3"
            assert item["state_update"] == {"tags": ["ai"]}

    @pytest.mark.asyncio
    async def test_failure_recorded_when_queue_raises(self):
        svc = _make_service()
        svc._queue = MagicMock()
        svc._queue.put = AsyncMock(side_effect=RuntimeError("queue error"))

        result = await svc.sync_conversation_state("conv-4", {"title": "X"})

        assert result.success is False
        assert len(result.failed_platforms) > 0

    @pytest.mark.asyncio
    async def test_result_has_sync_timestamp(self):
        svc = _make_service()
        result = await svc.sync_conversation_state("conv-5", {})
        assert isinstance(result.sync_timestamp, datetime)


# ---------------------------------------------------------------------------
# handle_platform_message
# ---------------------------------------------------------------------------


class TestHandlePlatformMessage:
    @pytest.mark.asyncio
    async def test_valid_web_message_processed(self):
        svc = _make_service()
        raw = {
            "conversation_id": "conv-1",
            "content": "Hello",
            "platform": PLATFORM_WEB,
            "role": "user",
        }
        result = await svc.handle_platform_message(raw)

        assert result["processed"] is True
        assert result["conversation_id"] == "conv-1"
        assert result["content"] == "Hello"
        assert result["platform"] == PLATFORM_WEB
        assert result["role"] == "user"

    @pytest.mark.asyncio
    async def test_valid_discord_message_processed(self):
        svc = _make_service()
        raw = {
            "conversation_id": "conv-2",
            "content": "Discord message",
            "platform": PLATFORM_DISCORD,
        }
        result = await svc.handle_platform_message(raw)

        assert result["processed"] is True
        assert result["platform"] == PLATFORM_DISCORD

    @pytest.mark.asyncio
    async def test_missing_conversation_id_returns_error(self):
        svc = _make_service()
        raw = {"content": "Hello", "platform": PLATFORM_WEB}
        result = await svc.handle_platform_message(raw)

        assert result["processed"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_missing_content_returns_error(self):
        svc = _make_service()
        raw = {"conversation_id": "conv-1", "platform": PLATFORM_WEB}
        result = await svc.handle_platform_message(raw)

        assert result["processed"] is False

    @pytest.mark.asyncio
    async def test_missing_platform_returns_error(self):
        svc = _make_service()
        raw = {"conversation_id": "conv-1", "content": "Hello"}
        result = await svc.handle_platform_message(raw)

        assert result["processed"] is False

    @pytest.mark.asyncio
    async def test_unsupported_platform_returns_error(self):
        svc = _make_service()
        raw = {
            "conversation_id": "conv-1",
            "content": "Hello",
            "platform": "telegram",
        }
        result = await svc.handle_platform_message(raw)

        assert result["processed"] is False
        assert "Unsupported platform" in result["error"]

    @pytest.mark.asyncio
    async def test_timestamp_parsed_from_iso_string(self):
        svc = _make_service()
        raw = {
            "conversation_id": "conv-1",
            "content": "Hello",
            "platform": PLATFORM_WEB,
            "timestamp": "2024-01-15T10:30:00Z",
        }
        result = await svc.handle_platform_message(raw)

        assert result["processed"] is True
        ts = result["timestamp"]
        assert isinstance(ts, datetime)
        assert ts.tzinfo is not None
        assert ts.year == 2024

    @pytest.mark.asyncio
    async def test_timestamp_defaults_to_now_when_missing(self):
        svc = _make_service()
        raw = {
            "conversation_id": "conv-1",
            "content": "Hello",
            "platform": PLATFORM_WEB,
        }
        result = await svc.handle_platform_message(raw)

        assert result["processed"] is True
        assert isinstance(result["timestamp"], datetime)

    @pytest.mark.asyncio
    async def test_role_defaults_to_user(self):
        svc = _make_service()
        raw = {
            "conversation_id": "conv-1",
            "content": "Hello",
            "platform": PLATFORM_WEB,
        }
        result = await svc.handle_platform_message(raw)

        assert result["role"] == "user"

    @pytest.mark.asyncio
    async def test_metadata_preserved(self):
        svc = _make_service()
        raw = {
            "conversation_id": "conv-1",
            "content": "Hello",
            "platform": PLATFORM_WEB,
            "metadata": {"discord_message_id": "12345"},
        }
        result = await svc.handle_platform_message(raw)

        assert result["metadata"] == {"discord_message_id": "12345"}


# ---------------------------------------------------------------------------
# resolve_sync_conflict
# ---------------------------------------------------------------------------


class TestResolveSyncConflict:
    @pytest.mark.asyncio
    async def test_later_timestamp_wins(self):
        svc = _make_service()
        from datetime import timedelta

        earlier = _NOW
        later = _NOW + timedelta(seconds=5)

        conflict = {
            "conversation_id": "conv-1",
            "platform_a": PLATFORM_WEB,
            "platform_b": PLATFORM_DISCORD,
            "timestamp_a": earlier,
            "timestamp_b": later,
            "content_a": "web content",
            "content_b": "discord content",
        }
        result = await svc.resolve_sync_conflict(conflict)

        assert result["resolved"] is True
        assert result["winning_platform"] == PLATFORM_DISCORD
        assert result["resolved_content"] == "discord content"
        assert result["resolution_strategy"] == "latest_wins"

    @pytest.mark.asyncio
    async def test_platform_a_wins_when_timestamp_a_later(self):
        svc = _make_service()
        from datetime import timedelta

        earlier = _NOW
        later = _NOW + timedelta(seconds=10)

        conflict = {
            "conversation_id": "conv-1",
            "platform_a": PLATFORM_DISCORD,
            "platform_b": PLATFORM_WEB,
            "timestamp_a": later,
            "timestamp_b": earlier,
            "content_a": "discord content",
            "content_b": "web content",
        }
        result = await svc.resolve_sync_conflict(conflict)

        assert result["winning_platform"] == PLATFORM_DISCORD
        assert result["resolved_content"] == "discord content"

    @pytest.mark.asyncio
    async def test_web_preferred_on_timestamp_tie(self):
        """When timestamps are equal, 'web' platform should win."""
        svc = _make_service()
        conflict = {
            "conversation_id": "conv-1",
            "platform_a": PLATFORM_DISCORD,
            "platform_b": PLATFORM_WEB,
            "timestamp_a": _NOW,
            "timestamp_b": _NOW,
            "content_a": "discord content",
            "content_b": "web content",
        }
        result = await svc.resolve_sync_conflict(conflict)

        assert result["winning_platform"] == PLATFORM_WEB
        assert result["resolved_content"] == "web content"

    @pytest.mark.asyncio
    async def test_web_preferred_on_tie_when_platform_a_is_web(self):
        svc = _make_service()
        conflict = {
            "conversation_id": "conv-1",
            "platform_a": PLATFORM_WEB,
            "platform_b": PLATFORM_DISCORD,
            "timestamp_a": _NOW,
            "timestamp_b": _NOW,
            "content_a": "web content",
            "content_b": "discord content",
        }
        result = await svc.resolve_sync_conflict(conflict)

        assert result["winning_platform"] == PLATFORM_WEB
        assert result["resolved_content"] == "web content"

    @pytest.mark.asyncio
    async def test_resolution_strategy_is_latest_wins(self):
        svc = _make_service()
        conflict = {
            "conversation_id": "conv-1",
            "platform_a": PLATFORM_WEB,
            "platform_b": PLATFORM_DISCORD,
            "timestamp_a": _NOW,
            "timestamp_b": _NOW,
            "content_a": "a",
            "content_b": "b",
        }
        result = await svc.resolve_sync_conflict(conflict)
        assert result["resolution_strategy"] == "latest_wins"

    @pytest.mark.asyncio
    async def test_resolved_is_true(self):
        svc = _make_service()
        conflict = {
            "conversation_id": "conv-1",
            "platform_a": PLATFORM_WEB,
            "platform_b": PLATFORM_DISCORD,
            "timestamp_a": _NOW,
            "timestamp_b": _NOW,
            "content_a": "a",
            "content_b": "b",
        }
        result = await svc.resolve_sync_conflict(conflict)
        assert result["resolved"] is True

    @pytest.mark.asyncio
    async def test_iso_string_timestamps_parsed(self):
        svc = _make_service()
        from datetime import timedelta

        earlier_str = (_NOW - timedelta(seconds=10)).isoformat()
        later_str = _NOW.isoformat()

        conflict = {
            "conversation_id": "conv-1",
            "platform_a": PLATFORM_WEB,
            "platform_b": PLATFORM_DISCORD,
            "timestamp_a": earlier_str,
            "timestamp_b": later_str,
            "content_a": "web content",
            "content_b": "discord content",
        }
        result = await svc.resolve_sync_conflict(conflict)
        assert result["winning_platform"] == PLATFORM_DISCORD


# ---------------------------------------------------------------------------
# get_sync_status
# ---------------------------------------------------------------------------


class TestGetSyncStatus:
    @pytest.mark.asyncio
    async def test_unknown_status_for_untracked_conversation(self):
        svc = _make_service()
        status = await svc.get_sync_status("unknown-conv")

        for platform in SUPPORTED_PLATFORMS:
            assert status[platform] == STATUS_UNKNOWN

    @pytest.mark.asyncio
    async def test_returns_tracked_status(self):
        svc = _make_service()
        svc._set_status("conv-1", PLATFORM_WEB, STATUS_SYNCED)
        svc._set_status("conv-1", PLATFORM_DISCORD, STATUS_FAILED)

        status = await svc.get_sync_status("conv-1")

        assert status[PLATFORM_WEB] == STATUS_SYNCED
        assert status[PLATFORM_DISCORD] == STATUS_FAILED

    @pytest.mark.asyncio
    async def test_returns_copy_not_reference(self):
        """Mutating the returned dict should not affect internal state."""
        svc = _make_service()
        svc._set_status("conv-1", PLATFORM_WEB, STATUS_SYNCED)

        status = await svc.get_sync_status("conv-1")
        status[PLATFORM_WEB] = "mutated"

        internal = svc._sync_status.get("conv-1", {})
        assert internal.get(PLATFORM_WEB) == STATUS_SYNCED

    @pytest.mark.asyncio
    async def test_status_updated_after_sync(self):
        svc = _make_service()
        msg = _make_message(conversation_id="conv-track", platform=PLATFORM_WEB)
        await svc.sync_message(msg, [PLATFORM_DISCORD])

        status = await svc.get_sync_status("conv-track")
        assert status[PLATFORM_DISCORD] == STATUS_SYNCED


# ---------------------------------------------------------------------------
# _retry_with_backoff
# ---------------------------------------------------------------------------


class TestRetryWithBackoff:
    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self):
        svc = _make_service()
        call_count = [0]

        async def op():
            call_count[0] += 1

        await svc._retry_with_backoff(op)
        assert call_count[0] == 1

    @pytest.mark.asyncio
    async def test_retries_on_failure_and_succeeds(self):
        svc = _make_service()
        call_count = [0]

        async def op():
            call_count[0] += 1
            if call_count[0] < 2:
                raise RuntimeError("transient error")

        # Patch sleep to avoid actual delays in tests
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await svc._retry_with_backoff(op)

        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        svc = _make_service()
        call_count = [0]

        async def op():
            call_count[0] += 1
            raise RuntimeError("persistent error")

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RuntimeError, match="persistent error"):
                await svc._retry_with_backoff(op, max_retries=3)

        assert call_count[0] == 3

    @pytest.mark.asyncio
    async def test_max_retries_respected(self):
        svc = _make_service()
        call_count = [0]

        async def op():
            call_count[0] += 1
            raise RuntimeError("always fails")

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RuntimeError):
                await svc._retry_with_backoff(op, max_retries=2)

        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_sleep_called_between_retries(self):
        svc = _make_service()

        async def op():
            raise RuntimeError("fail")

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(RuntimeError):
                await svc._retry_with_backoff(op, max_retries=3)

        # sleep should be called max_retries - 1 times (not after the last attempt)
        assert mock_sleep.call_count == 2


# ---------------------------------------------------------------------------
# _parse_timestamp
# ---------------------------------------------------------------------------


class TestParseTimestamp:
    def test_none_returns_epoch(self):
        result = CrossPlatformSyncService._parse_timestamp(None)
        assert result == datetime.fromtimestamp(0, tz=timezone.utc)

    def test_aware_datetime_returned_as_is(self):
        dt = datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)
        result = CrossPlatformSyncService._parse_timestamp(dt)
        assert result == dt

    def test_naive_datetime_gets_utc(self):
        naive = datetime(2024, 1, 15, 10, 30)
        result = CrossPlatformSyncService._parse_timestamp(naive)
        assert result.tzinfo == timezone.utc

    def test_iso_string_with_z(self):
        result = CrossPlatformSyncService._parse_timestamp("2024-01-15T10:30:00Z")
        assert result.year == 2024
        assert result.tzinfo is not None

    def test_iso_string_with_offset(self):
        result = CrossPlatformSyncService._parse_timestamp("2024-01-15T10:30:00+00:00")
        assert result.tzinfo is not None

    def test_invalid_string_returns_epoch(self):
        result = CrossPlatformSyncService._parse_timestamp("not-a-date")
        assert result == datetime.fromtimestamp(0, tz=timezone.utc)

    def test_invalid_type_returns_epoch(self):
        result = CrossPlatformSyncService._parse_timestamp(12345)
        assert result == datetime.fromtimestamp(0, tz=timezone.utc)


# ---------------------------------------------------------------------------
# Integration-style: full sync flow
# ---------------------------------------------------------------------------


class TestFullSyncFlow:
    @pytest.mark.asyncio
    async def test_web_message_synced_to_discord(self):
        """End-to-end: a web message is synced to discord and status updated."""
        svc = _make_service()
        msg = ConversationMessage(
            id="msg-e2e",
            conversation_id="conv-e2e",
            role="user",
            content="Cross-platform message",
            platform=PLATFORM_WEB,
            timestamp=_NOW,
        )

        result = await svc.sync_message(msg, [PLATFORM_DISCORD])

        assert result.success is True
        assert PLATFORM_DISCORD in result.synced_platforms

        status = await svc.get_sync_status("conv-e2e")
        assert status[PLATFORM_DISCORD] == STATUS_SYNCED

    @pytest.mark.asyncio
    async def test_conflict_resolution_then_state_sync(self):
        """Resolve a conflict and then sync the resolved state."""
        svc = _make_service()
        from datetime import timedelta

        conflict = {
            "conversation_id": "conv-conflict",
            "platform_a": PLATFORM_WEB,
            "platform_b": PLATFORM_DISCORD,
            "timestamp_a": _NOW + timedelta(seconds=1),
            "timestamp_b": _NOW,
            "content_a": "newer web content",
            "content_b": "older discord content",
        }

        resolution = await svc.resolve_sync_conflict(conflict)
        assert resolution["winning_platform"] == PLATFORM_WEB
        assert resolution["resolved_content"] == "newer web content"

        # Sync the resolved content as a state update
        state_result = await svc.sync_conversation_state(
            "conv-conflict",
            {"content": resolution["resolved_content"]},
        )
        assert state_result.success is True

    @pytest.mark.asyncio
    async def test_handle_then_sync_message(self):
        """Process an incoming platform message and then sync it."""
        svc = _make_service()
        raw = {
            "message_id": "raw-msg-1",
            "conversation_id": "conv-handle",
            "content": "Incoming message",
            "platform": PLATFORM_DISCORD,
            "role": "user",
        }

        processed = await svc.handle_platform_message(raw)
        assert processed["processed"] is True

        msg = ConversationMessage(
            id=processed["message_id"] or "generated-id",
            conversation_id=processed["conversation_id"],
            role=processed["role"],
            content=processed["content"],
            platform=processed["platform"],
            timestamp=processed["timestamp"],
        )

        result = await svc.sync_message(msg, [PLATFORM_WEB])
        assert result.success is True
        assert PLATFORM_WEB in result.synced_platforms
