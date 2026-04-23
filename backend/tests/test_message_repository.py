"""
Unit tests for MessageRepository

Tests cover CRUD operations, bulk insertion, paginated queries, search,
platform filtering, statistics, and the supporting MessageStats dataclass.

Validates: Requirements 1.2, 1.3, 7.2
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from app.core.errors import DatabaseError
from app.repositories.message import (
    MessageRepository,
    MessageStats,
    _map_to_message,
    _parse_datetime,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_row(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a minimal valid conversation_messages table row."""
    now = datetime.now(timezone.utc).isoformat()
    row: dict[str, Any] = {
        "id": str(uuid4()),
        "conversation_id": str(uuid4()),
        "role": "user",
        "content": "Hello, world!",
        "platform": "web",
        "metadata": {},
        "created_at": now,
    }
    if overrides:
        row.update(overrides)
    return row


def _make_client(
    response_data: list[dict] | None = None,
    count: int | None = None,
) -> MagicMock:
    """Build a minimal Supabase client mock that returns ``response_data``."""
    client = MagicMock()
    response = MagicMock()
    response.data = response_data if response_data is not None else []
    response.count = count

    table_mock = MagicMock()
    client.table.return_value = table_mock

    for method in (
        "select",
        "eq",
        "ilike",
        "order",
        "limit",
        "offset",
        "insert",
        "update",
        "delete",
        "contains",
    ):
        getattr(table_mock, method).return_value = table_mock

    table_mock.execute.return_value = response
    return client


# ---------------------------------------------------------------------------
# _parse_datetime helper
# ---------------------------------------------------------------------------


class TestParseDatetime:
    def test_parses_iso_string_with_z(self):
        dt = _parse_datetime("2024-01-15T10:30:00Z")
        assert dt.tzinfo is not None
        assert dt.year == 2024

    def test_parses_iso_string_with_offset(self):
        dt = _parse_datetime("2024-01-15T10:30:00+00:00")
        assert dt.tzinfo is not None

    def test_passes_through_aware_datetime(self):
        original = datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)
        result = _parse_datetime(original)
        assert result == original

    def test_adds_utc_to_naive_datetime(self):
        naive = datetime(2024, 1, 15, 10, 30)
        result = _parse_datetime(naive)
        assert result.tzinfo == timezone.utc

    def test_raises_on_invalid_type(self):
        with pytest.raises((ValueError, TypeError)):
            _parse_datetime(99999)


# ---------------------------------------------------------------------------
# _map_to_message helper
# ---------------------------------------------------------------------------


class TestMapToMessage:
    def test_maps_string_ids_to_uuid(self):
        row = _make_row()
        msg = _map_to_message(row)
        assert isinstance(msg.id, UUID)
        assert isinstance(msg.conversation_id, UUID)

    def test_maps_uuid_ids_directly(self):
        row = _make_row()
        row["id"] = UUID(row["id"])
        row["conversation_id"] = UUID(row["conversation_id"])
        msg = _map_to_message(row)
        assert isinstance(msg.id, UUID)

    def test_defaults_empty_metadata(self):
        row = _make_row({"metadata": None})
        msg = _map_to_message(row)
        assert msg.metadata == {}

    def test_defaults_platform_to_web(self):
        row = _make_row()
        del row["platform"]
        msg = _map_to_message(row)
        assert msg.platform == "web"

    def test_preserves_content(self):
        row = _make_row({"content": "Test content here"})
        msg = _map_to_message(row)
        assert msg.content == "Test content here"

    def test_preserves_role(self):
        row = _make_row({"role": "assistant"})
        msg = _map_to_message(row)
        assert msg.role == "assistant"


# ---------------------------------------------------------------------------
# MessageStats dataclass
# ---------------------------------------------------------------------------


class TestMessageStats:
    def test_defaults(self):
        stats = MessageStats(
            total_count=0,
            user_count=0,
            assistant_count=0,
            platforms=[],
        )
        assert stats.first_message_at is None
        assert stats.last_message_at is None

    def test_full_construction(self):
        now = datetime.now(timezone.utc)
        stats = MessageStats(
            total_count=10,
            user_count=6,
            assistant_count=4,
            platforms=["web", "discord"],
            first_message_at=now,
            last_message_at=now,
        )
        assert stats.total_count == 10
        assert stats.user_count == 6
        assert stats.assistant_count == 4
        assert "web" in stats.platforms
        assert "discord" in stats.platforms


# ---------------------------------------------------------------------------
# MessageRepository — add_message
# ---------------------------------------------------------------------------


class TestAddMessage:
    @pytest.mark.asyncio
    async def test_creates_and_returns_message(self):
        row = _make_row()
        client = _make_client([row])
        repo = MessageRepository(client)

        result = await repo.add_message(
            conversation_id=row["conversation_id"],
            role="user",
            content="Hello",
            platform="web",
        )

        assert str(result.id) == row["id"]
        assert result.role == "user"
        assert result.platform == "web"

    @pytest.mark.asyncio
    async def test_passes_metadata(self):
        meta = {"source": "discord", "attachment": "image.png"}
        row = _make_row({"metadata": meta})
        client = _make_client([row])
        repo = MessageRepository(client)

        result = await repo.add_message(
            conversation_id=row["conversation_id"],
            role="user",
            content="With metadata",
            metadata=meta,
        )

        assert result.metadata == meta

    @pytest.mark.asyncio
    async def test_raises_database_error_on_empty_response(self):
        client = _make_client([])
        repo = MessageRepository(client)

        with pytest.raises(DatabaseError):
            await repo.add_message(
                conversation_id=uuid4(),
                role="user",
                content="Fail",
            )

    @pytest.mark.asyncio
    async def test_raises_database_error_on_exception(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError("connection refused")
        repo = MessageRepository(client)

        with pytest.raises(DatabaseError):
            await repo.add_message(
                conversation_id=uuid4(),
                role="user",
                content="Fail",
            )

    @pytest.mark.asyncio
    async def test_defaults_platform_to_web(self):
        row = _make_row({"platform": "web"})
        client = _make_client([row])
        repo = MessageRepository(client)

        result = await repo.add_message(
            conversation_id=row["conversation_id"],
            role="user",
            content="No platform specified",
        )

        assert result.platform == "web"


# ---------------------------------------------------------------------------
# MessageRepository — add_messages_batch
# ---------------------------------------------------------------------------


class TestAddMessagesBatch:
    @pytest.mark.asyncio
    async def test_returns_empty_list_for_empty_input(self):
        client = _make_client([])
        repo = MessageRepository(client)

        result = await repo.add_messages_batch([])

        assert result == []

    @pytest.mark.asyncio
    async def test_bulk_inserts_and_returns_messages(self):
        conv_id = str(uuid4())
        rows = [_make_row({"conversation_id": conv_id}) for _ in range(3)]
        client = _make_client(rows)
        repo = MessageRepository(client)

        messages = [
            {"conversation_id": conv_id, "role": "user", "content": f"Msg {i}"} for i in range(3)
        ]
        result = await repo.add_messages_batch(messages)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_raises_database_error_on_empty_response(self):
        client = _make_client([])
        repo = MessageRepository(client)

        messages = [{"conversation_id": uuid4(), "role": "user", "content": "Fail"}]
        with pytest.raises(DatabaseError):
            await repo.add_messages_batch(messages)

    @pytest.mark.asyncio
    async def test_defaults_platform_when_not_provided(self):
        conv_id = str(uuid4())
        row = _make_row({"conversation_id": conv_id, "platform": "web"})
        client = _make_client([row])
        repo = MessageRepository(client)

        messages = [{"conversation_id": conv_id, "role": "user", "content": "No platform"}]
        result = await repo.add_messages_batch(messages)

        assert result[0].platform == "web"

    @pytest.mark.asyncio
    async def test_raises_database_error_on_exception(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError("db error")
        repo = MessageRepository(client)

        with pytest.raises(DatabaseError):
            await repo.add_messages_batch(
                [{"conversation_id": uuid4(), "role": "user", "content": "Fail"}]
            )


# ---------------------------------------------------------------------------
# MessageRepository — get_message
# ---------------------------------------------------------------------------


class TestGetMessage:
    @pytest.mark.asyncio
    async def test_returns_message_when_found(self):
        row = _make_row()
        client = _make_client([row])
        repo = MessageRepository(client)

        result = await repo.get_message(message_id=row["id"])

        assert result is not None
        assert str(result.id) == row["id"]

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        client = _make_client([])
        repo = MessageRepository(client)

        result = await repo.get_message(message_id=uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_raises_database_error_on_exception(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError("db error")
        repo = MessageRepository(client)

        with pytest.raises(DatabaseError):
            await repo.get_message(message_id=uuid4())


# ---------------------------------------------------------------------------
# MessageRepository — delete_message
# ---------------------------------------------------------------------------


class TestDeleteMessage:
    @pytest.mark.asyncio
    async def test_returns_true_when_deleted(self):
        row = _make_row()
        client = _make_client([row])
        repo = MessageRepository(client)

        result = await repo.delete_message(
            message_id=row["id"],
            conversation_id=row["conversation_id"],
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self):
        client = _make_client([])
        repo = MessageRepository(client)

        result = await repo.delete_message(
            message_id=uuid4(),
            conversation_id=uuid4(),
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_raises_database_error_on_exception(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError("db error")
        repo = MessageRepository(client)

        with pytest.raises(DatabaseError):
            await repo.delete_message(message_id=uuid4(), conversation_id=uuid4())


# ---------------------------------------------------------------------------
# MessageRepository — get_messages
# ---------------------------------------------------------------------------


class TestGetMessages:
    @pytest.mark.asyncio
    async def test_returns_messages(self):
        conv_id = str(uuid4())
        rows = [_make_row({"conversation_id": conv_id}) for _ in range(5)]
        client = _make_client(rows)
        repo = MessageRepository(client)

        result = await repo.get_messages(conversation_id=conv_id)

        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_messages(self):
        client = _make_client([])
        repo = MessageRepository(client)

        result = await repo.get_messages(conversation_id=uuid4())

        assert result == []

    @pytest.mark.asyncio
    async def test_passes_limit_and_offset(self):
        client = _make_client([])
        repo = MessageRepository(client)

        await repo.get_messages(conversation_id=uuid4(), limit=10, offset=20)

        table_mock = client.table.return_value
        table_mock.limit.assert_called_with(10)
        table_mock.offset.assert_called_with(20)

    @pytest.mark.asyncio
    async def test_ascending_order(self):
        client = _make_client([])
        repo = MessageRepository(client)

        await repo.get_messages(conversation_id=uuid4(), ascending=True)

        table_mock = client.table.return_value
        table_mock.order.assert_called_with("created_at", desc=False)

    @pytest.mark.asyncio
    async def test_descending_order_by_default(self):
        client = _make_client([])
        repo = MessageRepository(client)

        await repo.get_messages(conversation_id=uuid4())

        table_mock = client.table.return_value
        table_mock.order.assert_called_with("created_at", desc=True)

    @pytest.mark.asyncio
    async def test_raises_database_error_on_exception(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError("db error")
        repo = MessageRepository(client)

        with pytest.raises(DatabaseError):
            await repo.get_messages(conversation_id=uuid4())


# ---------------------------------------------------------------------------
# MessageRepository — get_message_count
# ---------------------------------------------------------------------------


class TestGetMessageCount:
    @pytest.mark.asyncio
    async def test_returns_count_from_response_count(self):
        client = _make_client([], count=7)
        repo = MessageRepository(client)

        result = await repo.get_message_count(conversation_id=uuid4())

        assert result == 7

    @pytest.mark.asyncio
    async def test_falls_back_to_data_length_when_count_is_none(self):
        rows = [_make_row() for _ in range(3)]
        client = _make_client(rows, count=None)
        # Ensure response.count is None
        client.table.return_value.execute.return_value.count = None
        repo = MessageRepository(client)

        result = await repo.get_message_count(conversation_id=uuid4())

        assert result == 3

    @pytest.mark.asyncio
    async def test_raises_database_error_on_exception(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError("db error")
        repo = MessageRepository(client)

        with pytest.raises(DatabaseError):
            await repo.get_message_count(conversation_id=uuid4())


# ---------------------------------------------------------------------------
# MessageRepository — search_messages
# ---------------------------------------------------------------------------


class TestSearchMessages:
    @pytest.mark.asyncio
    async def test_returns_matching_messages(self):
        conv_id = str(uuid4())
        rows = [_make_row({"conversation_id": conv_id, "content": "Python is great"})]
        client = _make_client(rows)
        repo = MessageRepository(client)

        result = await repo.search_messages(conversation_id=conv_id, query="Python")

        assert len(result) == 1
        assert result[0].content == "Python is great"

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_match(self):
        client = _make_client([])
        repo = MessageRepository(client)

        result = await repo.search_messages(conversation_id=uuid4(), query="nonexistent")

        assert result == []

    @pytest.mark.asyncio
    async def test_uses_ilike_with_wildcards(self):
        client = _make_client([])
        repo = MessageRepository(client)

        await repo.search_messages(conversation_id=uuid4(), query="hello")

        table_mock = client.table.return_value
        table_mock.ilike.assert_called_with("content", "%hello%")

    @pytest.mark.asyncio
    async def test_respects_limit(self):
        client = _make_client([])
        repo = MessageRepository(client)

        await repo.search_messages(conversation_id=uuid4(), query="test", limit=5)

        table_mock = client.table.return_value
        table_mock.limit.assert_called_with(5)

    @pytest.mark.asyncio
    async def test_raises_database_error_on_exception(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError("db error")
        repo = MessageRepository(client)

        with pytest.raises(DatabaseError):
            await repo.search_messages(conversation_id=uuid4(), query="test")


# ---------------------------------------------------------------------------
# MessageRepository — get_messages_by_platform
# ---------------------------------------------------------------------------


class TestGetMessagesByPlatform:
    @pytest.mark.asyncio
    async def test_returns_messages_for_platform(self):
        conv_id = str(uuid4())
        rows = [_make_row({"conversation_id": conv_id, "platform": "discord"})]
        client = _make_client(rows)
        repo = MessageRepository(client)

        result = await repo.get_messages_by_platform(conversation_id=conv_id, platform="discord")

        assert len(result) == 1
        assert result[0].platform == "discord"

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_match(self):
        client = _make_client([])
        repo = MessageRepository(client)

        result = await repo.get_messages_by_platform(conversation_id=uuid4(), platform="discord")

        assert result == []

    @pytest.mark.asyncio
    async def test_filters_by_platform(self):
        client = _make_client([])
        repo = MessageRepository(client)

        await repo.get_messages_by_platform(conversation_id=uuid4(), platform="discord")

        table_mock = client.table.return_value
        # eq should be called with platform filter
        calls = [str(c) for c in table_mock.eq.call_args_list]
        assert any("discord" in c for c in calls)

    @pytest.mark.asyncio
    async def test_respects_limit_and_offset(self):
        client = _make_client([])
        repo = MessageRepository(client)

        await repo.get_messages_by_platform(
            conversation_id=uuid4(), platform="web", limit=10, offset=5
        )

        table_mock = client.table.return_value
        table_mock.limit.assert_called_with(10)
        table_mock.offset.assert_called_with(5)

    @pytest.mark.asyncio
    async def test_raises_database_error_on_exception(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError("db error")
        repo = MessageRepository(client)

        with pytest.raises(DatabaseError):
            await repo.get_messages_by_platform(conversation_id=uuid4(), platform="web")


# ---------------------------------------------------------------------------
# MessageRepository — get_conversation_stats
# ---------------------------------------------------------------------------


class TestGetConversationStats:
    @pytest.mark.asyncio
    async def test_returns_stats_for_empty_conversation(self):
        client = _make_client([])
        repo = MessageRepository(client)

        stats = await repo.get_conversation_stats(conversation_id=uuid4())

        assert stats.total_count == 0
        assert stats.user_count == 0
        assert stats.assistant_count == 0
        assert stats.platforms == []
        assert stats.first_message_at is None
        assert stats.last_message_at is None

    @pytest.mark.asyncio
    async def test_counts_roles_correctly(self):
        conv_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        rows = [
            {"role": "user", "platform": "web", "created_at": now},
            {"role": "user", "platform": "web", "created_at": now},
            {"role": "assistant", "platform": "web", "created_at": now},
        ]
        client = _make_client(rows)
        repo = MessageRepository(client)

        stats = await repo.get_conversation_stats(conversation_id=conv_id)

        assert stats.total_count == 3
        assert stats.user_count == 2
        assert stats.assistant_count == 1

    @pytest.mark.asyncio
    async def test_collects_distinct_platforms(self):
        conv_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        rows = [
            {"role": "user", "platform": "web", "created_at": now},
            {"role": "assistant", "platform": "discord", "created_at": now},
            {"role": "user", "platform": "web", "created_at": now},
        ]
        client = _make_client(rows)
        repo = MessageRepository(client)

        stats = await repo.get_conversation_stats(conversation_id=conv_id)

        assert set(stats.platforms) == {"web", "discord"}

    @pytest.mark.asyncio
    async def test_sets_first_and_last_message_timestamps(self):
        conv_id = str(uuid4())
        early = "2024-01-01T00:00:00Z"
        late = "2024-06-01T00:00:00Z"
        rows = [
            {"role": "user", "platform": "web", "created_at": early},
            {"role": "assistant", "platform": "web", "created_at": late},
        ]
        client = _make_client(rows)
        repo = MessageRepository(client)

        stats = await repo.get_conversation_stats(conversation_id=conv_id)

        assert stats.first_message_at is not None
        assert stats.last_message_at is not None
        assert stats.first_message_at < stats.last_message_at

    @pytest.mark.asyncio
    async def test_raises_database_error_on_exception(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError("db error")
        repo = MessageRepository(client)

        with pytest.raises(DatabaseError):
            await repo.get_conversation_stats(conversation_id=uuid4())

    @pytest.mark.asyncio
    async def test_returns_message_stats_instance(self):
        client = _make_client([])
        repo = MessageRepository(client)

        stats = await repo.get_conversation_stats(conversation_id=uuid4())

        assert isinstance(stats, MessageStats)
