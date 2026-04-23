"""
Unit tests for ConversationRepository

Tests cover CRUD operations, metadata management, auto-archive logic,
and the supporting Pydantic models (ConversationSummary, ConversationFilters).

Validates: Requirements 1.1, 1.2, 1.4, 3.4
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from app.core.errors import DatabaseError, NotFoundError
from app.repositories.conversation import (
    ConversationFilters,
    ConversationRepository,
    ConversationSummary,
    _parse_datetime,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_row(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a minimal valid conversations table row."""
    now = datetime.now(timezone.utc).isoformat()
    row: dict[str, Any] = {
        "id": str(uuid4()),
        "user_id": str(uuid4()),
        "title": "Test Conversation",
        "summary": None,
        "platform": "web",
        "tags": [],
        "is_archived": False,
        "is_favorite": False,
        "created_at": now,
        "last_message_at": now,
        "message_count": 0,
        "metadata": {},
    }
    if overrides:
        row.update(overrides)
    return row


def _make_client(response_data: list[dict] | None = None) -> MagicMock:
    """Build a minimal Supabase client mock that returns ``response_data``."""
    client = MagicMock()
    response = MagicMock()
    response.data = response_data if response_data is not None else []

    # Chain: client.table().select().eq()...execute() → response
    table_mock = MagicMock()
    client.table.return_value = table_mock

    # Make every chained call return the same mock so arbitrary chains work
    for method in (
        "select",
        "eq",
        "lt",
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
            _parse_datetime(12345)


# ---------------------------------------------------------------------------
# ConversationSummary model
# ---------------------------------------------------------------------------


class TestConversationSummary:
    def test_defaults(self):
        now = datetime.now(timezone.utc)
        summary = ConversationSummary(
            id=uuid4(),
            title="Hello",
            platform="web",
            last_message_at=now,
        )
        assert summary.tags == []
        assert summary.is_favorite is False
        assert summary.is_archived is False
        assert summary.message_count == 0
        assert summary.summary is None

    def test_full_construction(self):
        uid = uuid4()
        now = datetime.now(timezone.utc)
        summary = ConversationSummary(
            id=uid,
            title="Full",
            summary="A summary",
            platform="discord",
            last_message_at=now,
            message_count=5,
            tags=["python", "ai"],
            is_favorite=True,
            is_archived=False,
        )
        assert summary.id == uid
        assert summary.tags == ["python", "ai"]
        assert summary.is_favorite is True


# ---------------------------------------------------------------------------
# ConversationFilters model
# ---------------------------------------------------------------------------


class TestConversationFilters:
    def test_defaults(self):
        f = ConversationFilters()
        assert f.is_archived is False  # default hides archived
        assert f.is_favorite is None
        assert f.platform is None
        assert f.limit == 20
        assert f.offset == 0
        assert f.order_by == "last_message_at"
        assert f.ascending is False

    def test_custom_values(self):
        f = ConversationFilters(
            platform="discord",
            is_archived=True,
            is_favorite=True,
            tags=["ai"],
            limit=10,
            offset=5,
            order_by="created_at",
            ascending=True,
        )
        assert f.platform == "discord"
        assert f.is_archived is True
        assert f.tags == ["ai"]
        assert f.limit == 10


# ---------------------------------------------------------------------------
# ConversationRepository — create_conversation
# ---------------------------------------------------------------------------


class TestCreateConversation:
    @pytest.mark.asyncio
    async def test_creates_and_returns_conversation(self):
        row = _make_row()
        client = _make_client([row])
        repo = ConversationRepository(client)

        result = await repo.create_conversation(
            user_id=row["user_id"],
            title="Test Conversation",
            platform="web",
        )

        assert str(result.id) == row["id"]
        assert result.title == "Test Conversation"
        assert result.platform == "web"
        assert result.is_archived is False
        assert result.is_favorite is False

    @pytest.mark.asyncio
    async def test_passes_tags_and_metadata(self):
        row = _make_row({"tags": ["ai", "python"], "metadata": {"source": "test"}})
        client = _make_client([row])
        repo = ConversationRepository(client)

        result = await repo.create_conversation(
            user_id=row["user_id"],
            title="Tagged",
            tags=["ai", "python"],
            metadata={"source": "test"},
        )

        assert result.tags == ["ai", "python"]
        assert result.metadata == {"source": "test"}

    @pytest.mark.asyncio
    async def test_raises_database_error_on_empty_response(self):
        client = _make_client([])  # empty response
        repo = ConversationRepository(client)

        with pytest.raises(DatabaseError):
            await repo.create_conversation(user_id=uuid4(), title="Fail")

    @pytest.mark.asyncio
    async def test_raises_database_error_on_exception(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError("connection refused")
        repo = ConversationRepository(client)

        with pytest.raises(DatabaseError):
            await repo.create_conversation(user_id=uuid4(), title="Fail")


# ---------------------------------------------------------------------------
# ConversationRepository — get_conversation
# ---------------------------------------------------------------------------


class TestGetConversation:
    @pytest.mark.asyncio
    async def test_returns_conversation_when_found(self):
        row = _make_row()
        client = _make_client([row])
        repo = ConversationRepository(client)

        result = await repo.get_conversation(
            conversation_id=row["id"],
            user_id=row["user_id"],
        )

        assert result is not None
        assert str(result.id) == row["id"]

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        client = _make_client([])
        repo = ConversationRepository(client)

        result = await repo.get_conversation(
            conversation_id=uuid4(),
            user_id=uuid4(),
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_raises_database_error_on_exception(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError("db error")
        repo = ConversationRepository(client)

        with pytest.raises(DatabaseError):
            await repo.get_conversation(conversation_id=uuid4(), user_id=uuid4())


# ---------------------------------------------------------------------------
# ConversationRepository — list_conversations
# ---------------------------------------------------------------------------


class TestListConversations:
    @pytest.mark.asyncio
    async def test_returns_summaries(self):
        rows = [_make_row({"title": f"Conv {i}"}) for i in range(3)]
        client = _make_client(rows)
        repo = ConversationRepository(client)

        results = await repo.list_conversations(user_id=uuid4())

        assert len(results) == 3
        assert all(isinstance(r, ConversationSummary) for r in results)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_conversations(self):
        client = _make_client([])
        repo = ConversationRepository(client)

        results = await repo.list_conversations(user_id=uuid4())

        assert results == []

    @pytest.mark.asyncio
    async def test_uses_default_filters(self):
        client = _make_client([])
        repo = ConversationRepository(client)

        # Should not raise; default filters applied internally
        await repo.list_conversations(user_id=uuid4())

    @pytest.mark.asyncio
    async def test_accepts_custom_filters(self):
        rows = [_make_row({"platform": "discord", "is_favorite": True})]
        client = _make_client(rows)
        repo = ConversationRepository(client)

        filters = ConversationFilters(platform="discord", is_favorite=True, limit=5)
        results = await repo.list_conversations(user_id=uuid4(), filters=filters)

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_raises_database_error_on_exception(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError("db error")
        repo = ConversationRepository(client)

        with pytest.raises(DatabaseError):
            await repo.list_conversations(user_id=uuid4())


# ---------------------------------------------------------------------------
# ConversationRepository — update_conversation
# ---------------------------------------------------------------------------


class TestUpdateConversation:
    @pytest.mark.asyncio
    async def test_returns_updated_conversation(self):
        row = _make_row({"title": "Updated Title"})
        client = _make_client([row])
        repo = ConversationRepository(client)

        result = await repo.update_conversation(
            conversation_id=row["id"],
            user_id=row["user_id"],
            updates={"title": "Updated Title"},
        )

        assert result.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_raises_not_found_when_no_rows_returned(self):
        client = _make_client([])
        repo = ConversationRepository(client)

        with pytest.raises(NotFoundError):
            await repo.update_conversation(
                conversation_id=uuid4(),
                user_id=uuid4(),
                updates={"title": "X"},
            )

    @pytest.mark.asyncio
    async def test_raises_database_error_on_exception(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError("db error")
        repo = ConversationRepository(client)

        with pytest.raises(DatabaseError):
            await repo.update_conversation(
                conversation_id=uuid4(),
                user_id=uuid4(),
                updates={"title": "X"},
            )


# ---------------------------------------------------------------------------
# ConversationRepository — delete_conversation
# ---------------------------------------------------------------------------


class TestDeleteConversation:
    @pytest.mark.asyncio
    async def test_returns_true_when_deleted(self):
        row = _make_row()
        client = _make_client([row])
        repo = ConversationRepository(client)

        result = await repo.delete_conversation(
            conversation_id=row["id"],
            user_id=row["user_id"],
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self):
        client = _make_client([])
        repo = ConversationRepository(client)

        result = await repo.delete_conversation(
            conversation_id=uuid4(),
            user_id=uuid4(),
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_raises_database_error_on_exception(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError("db error")
        repo = ConversationRepository(client)

        with pytest.raises(DatabaseError):
            await repo.delete_conversation(conversation_id=uuid4(), user_id=uuid4())


# ---------------------------------------------------------------------------
# ConversationRepository — metadata management
# ---------------------------------------------------------------------------


class TestSetFavorite:
    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        row = _make_row({"is_favorite": True})
        client = _make_client([row])
        repo = ConversationRepository(client)

        result = await repo.set_favorite(
            conversation_id=row["id"],
            user_id=row["user_id"],
            is_favorite=True,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self):
        client = _make_client([])
        repo = ConversationRepository(client)

        result = await repo.set_favorite(
            conversation_id=uuid4(),
            user_id=uuid4(),
            is_favorite=True,
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_raises_database_error_on_exception(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError("db error")
        repo = ConversationRepository(client)

        with pytest.raises(DatabaseError):
            await repo.set_favorite(conversation_id=uuid4(), user_id=uuid4(), is_favorite=True)


class TestSetArchived:
    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        row = _make_row({"is_archived": True})
        client = _make_client([row])
        repo = ConversationRepository(client)

        result = await repo.set_archived(
            conversation_id=row["id"],
            user_id=row["user_id"],
            is_archived=True,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self):
        client = _make_client([])
        repo = ConversationRepository(client)

        result = await repo.set_archived(
            conversation_id=uuid4(),
            user_id=uuid4(),
            is_archived=True,
        )

        assert result is False


class TestUpdateTags:
    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        row = _make_row({"tags": ["ai", "python"]})
        client = _make_client([row])
        repo = ConversationRepository(client)

        result = await repo.update_tags(
            conversation_id=row["id"],
            user_id=row["user_id"],
            tags=["ai", "python"],
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self):
        client = _make_client([])
        repo = ConversationRepository(client)

        result = await repo.update_tags(
            conversation_id=uuid4(),
            user_id=uuid4(),
            tags=["ai"],
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_accepts_empty_tag_list(self):
        row = _make_row({"tags": []})
        client = _make_client([row])
        repo = ConversationRepository(client)

        result = await repo.update_tags(
            conversation_id=row["id"],
            user_id=row["user_id"],
            tags=[],
        )

        assert result is True


class TestUpdateTitle:
    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        row = _make_row({"title": "New Title"})
        client = _make_client([row])
        repo = ConversationRepository(client)

        result = await repo.update_title(
            conversation_id=row["id"],
            user_id=row["user_id"],
            title="New Title",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self):
        client = _make_client([])
        repo = ConversationRepository(client)

        result = await repo.update_title(
            conversation_id=uuid4(),
            user_id=uuid4(),
            title="New Title",
        )

        assert result is False


# ---------------------------------------------------------------------------
# ConversationRepository — archive_inactive_conversations
# ---------------------------------------------------------------------------


class TestArchiveInactiveConversations:
    @pytest.mark.asyncio
    async def test_returns_count_of_archived_conversations(self):
        # Simulate 3 conversations being archived
        rows = [_make_row({"is_archived": True}) for _ in range(3)]
        client = _make_client(rows)
        repo = ConversationRepository(client)

        count = await repo.archive_inactive_conversations(user_id=uuid4(), days_threshold=30)

        assert count == 3

    @pytest.mark.asyncio
    async def test_returns_zero_when_nothing_to_archive(self):
        client = _make_client([])
        repo = ConversationRepository(client)

        count = await repo.archive_inactive_conversations(user_id=uuid4(), days_threshold=30)

        assert count == 0

    @pytest.mark.asyncio
    async def test_uses_correct_cutoff_date(self):
        """Verify the lt() filter is called with a date ~30 days in the past."""
        client = _make_client([])
        repo = ConversationRepository(client)

        user_id = uuid4()
        await repo.archive_inactive_conversations(user_id=user_id, days_threshold=30)

        # Verify lt() was called (cutoff date filter)
        table_mock = client.table.return_value
        table_mock.lt.assert_called_once()
        field_arg, cutoff_arg = table_mock.lt.call_args[0]
        assert field_arg == "last_message_at"

        # The cutoff should be approximately 30 days ago
        cutoff_dt = datetime.fromisoformat(cutoff_arg.replace("Z", "+00:00"))
        expected = datetime.now(timezone.utc) - timedelta(days=30)
        diff = abs((cutoff_dt - expected).total_seconds())
        assert diff < 5  # within 5 seconds

    @pytest.mark.asyncio
    async def test_custom_days_threshold(self):
        client = _make_client([])
        repo = ConversationRepository(client)

        await repo.archive_inactive_conversations(user_id=uuid4(), days_threshold=7)

        table_mock = client.table.return_value
        _, cutoff_arg = table_mock.lt.call_args[0]
        cutoff_dt = datetime.fromisoformat(cutoff_arg.replace("Z", "+00:00"))
        expected = datetime.now(timezone.utc) - timedelta(days=7)
        diff = abs((cutoff_dt - expected).total_seconds())
        assert diff < 5

    @pytest.mark.asyncio
    async def test_raises_database_error_on_exception(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError("db error")
        repo = ConversationRepository(client)

        with pytest.raises(DatabaseError):
            await repo.archive_inactive_conversations(user_id=uuid4())


# ---------------------------------------------------------------------------
# ConversationRepository — _map_to_conversation / _map_to_summary
# ---------------------------------------------------------------------------


class TestMappers:
    def test_map_to_conversation_with_string_ids(self):
        row = _make_row()
        result = ConversationRepository._map_to_conversation(row)
        assert isinstance(result.id, UUID)
        assert isinstance(result.user_id, UUID)

    def test_map_to_conversation_with_uuid_ids(self):
        row = _make_row()
        row["id"] = UUID(row["id"])
        row["user_id"] = UUID(row["user_id"])
        result = ConversationRepository._map_to_conversation(row)
        assert isinstance(result.id, UUID)

    def test_map_to_conversation_defaults_empty_tags(self):
        row = _make_row({"tags": None})
        result = ConversationRepository._map_to_conversation(row)
        assert result.tags == []

    def test_map_to_conversation_defaults_empty_metadata(self):
        row = _make_row({"metadata": None})
        result = ConversationRepository._map_to_conversation(row)
        assert result.metadata == {}

    def test_map_to_summary_with_string_id(self):
        row = _make_row()
        result = ConversationRepository._map_to_summary(row)
        assert isinstance(result, ConversationSummary)
        assert isinstance(result.id, UUID)

    def test_map_to_summary_defaults_empty_tags(self):
        row = _make_row({"tags": None})
        result = ConversationRepository._map_to_summary(row)
        assert result.tags == []
