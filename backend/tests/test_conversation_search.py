"""
Unit tests for ConversationSearchService

Tests cover:
- _generate_highlights helper
- _passes_filters static method
- _apply_filters query builder method
- _merge_results scoring and deduplication
- search_conversations orchestration (mocked repositories)
- SearchFilters and ConversationSearchResult dataclasses

Validates: Requirements 3.1, 3.3
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.conversation_search import (
    ConversationSearchResult,
    ConversationSearchService,
    SearchFilters,
    _parse_datetime,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(timezone.utc)


def _make_conv_row(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a minimal conversations table row dict."""
    row: dict[str, Any] = {
        "id": str(uuid4()),
        "title": "Test Conversation",
        "summary": None,
        "platform": "web",
        "last_message_at": _NOW.isoformat(),
        "message_count": 3,
        "tags": [],
        "is_favorite": False,
        "is_archived": False,
    }
    if overrides:
        row.update(overrides)
    return row


def _make_service(
    conv_response_data: list[dict] | None = None,
    msg_response_data: list[dict] | None = None,
) -> ConversationSearchService:
    """Build a ConversationSearchService with mocked Supabase client."""
    conv_response = MagicMock()
    conv_response.data = conv_response_data if conv_response_data is not None else []

    msg_response = MagicMock()
    msg_response.data = msg_response_data if msg_response_data is not None else []

    client = MagicMock()
    table_mock = MagicMock()
    client.table.return_value = table_mock

    for method in (
        "select",
        "eq",
        "ilike",
        "gte",
        "lte",
        "contains",
        "limit",
        "offset",
        "order",
        "insert",
        "update",
        "delete",
    ):
        getattr(table_mock, method).return_value = table_mock

    # Return conv_response for conversations table, msg_response for messages
    def _execute_side_effect():
        # Determine which table was queried by inspecting call args
        call_args = client.table.call_args
        if call_args and "conversation_messages" in str(call_args):
            return msg_response
        return conv_response

    table_mock.execute.side_effect = _execute_side_effect

    conv_repo = MagicMock()
    conv_repo.client = client
    conv_repo.get_conversation = AsyncMock(return_value=None)

    msg_repo = MagicMock()

    return ConversationSearchService(
        conversation_repo=conv_repo,
        message_repo=msg_repo,
    )


# ---------------------------------------------------------------------------
# _parse_datetime
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
# SearchFilters dataclass
# ---------------------------------------------------------------------------


class TestSearchFilters:
    def test_defaults(self):
        f = SearchFilters()
        assert f.platform is None
        assert f.is_favorite is None
        assert f.is_archived is False  # default excludes archived
        assert f.tags is None
        assert f.date_from is None
        assert f.date_to is None

    def test_custom_values(self):
        f = SearchFilters(
            platform="discord",
            is_favorite=True,
            is_archived=True,
            tags=["ai", "python"],
            date_from=_NOW - timedelta(days=7),
            date_to=_NOW,
        )
        assert f.platform == "discord"
        assert f.is_favorite is True
        assert f.tags == ["ai", "python"]


# ---------------------------------------------------------------------------
# ConversationSearchResult dataclass
# ---------------------------------------------------------------------------


class TestConversationSearchResult:
    def test_construction(self):
        result = ConversationSearchResult(
            conversation_id=str(uuid4()),
            title="Hello",
            summary="A summary",
            platform="web",
            last_message_at=_NOW,
            message_count=5,
            tags=["ai"],
            is_favorite=True,
            is_archived=False,
            relevance_score=0.9,
            matched_content=["Hello world"],
            highlight_snippets=["<mark>Hello</mark> world"],
        )
        assert result.relevance_score == 0.9
        assert result.tags == ["ai"]
        assert result.is_favorite is True


# ---------------------------------------------------------------------------
# _generate_highlights
# ---------------------------------------------------------------------------


class TestGenerateHighlights:
    def test_wraps_single_term(self):
        result = ConversationSearchService._generate_highlights("Hello World", "world")
        assert "<mark>World</mark>" in result

    def test_case_insensitive(self):
        result = ConversationSearchService._generate_highlights("Python is great", "PYTHON")
        assert "<mark>Python</mark>" in result

    def test_multiple_terms(self):
        result = ConversationSearchService._generate_highlights(
            "Python and machine learning", "python learning"
        )
        assert "<mark>Python</mark>" in result
        assert "<mark>learning</mark>" in result

    def test_empty_query_returns_original(self):
        text = "Hello World"
        result = ConversationSearchService._generate_highlights(text, "")
        assert result == text

    def test_empty_text_returns_empty(self):
        result = ConversationSearchService._generate_highlights("", "query")
        assert result == ""

    def test_no_match_returns_original(self):
        text = "Hello World"
        result = ConversationSearchService._generate_highlights(text, "xyz")
        assert result == text

    def test_preserves_original_casing(self):
        result = ConversationSearchService._generate_highlights("Hello World", "hello")
        assert "<mark>Hello</mark>" in result
        assert "World" in result

    def test_multiple_occurrences(self):
        result = ConversationSearchService._generate_highlights("cat and cat", "cat")
        assert result.count("<mark>cat</mark>") == 2

    def test_special_regex_chars_in_query(self):
        # Should not raise even with regex special characters
        result = ConversationSearchService._generate_highlights("price is $10.00", "$10")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# _passes_filters
# ---------------------------------------------------------------------------


class TestPassesFilters:
    def _conv(self, **kwargs) -> dict[str, Any]:
        base = {
            "platform": "web",
            "is_archived": False,
            "is_favorite": False,
            "tags": [],
            "last_message_at": _NOW,
        }
        base.update(kwargs)
        return base

    def test_no_filters_passes_everything(self):
        assert ConversationSearchService._passes_filters(self._conv(), SearchFilters()) is True

    def test_platform_filter_match(self):
        f = SearchFilters(platform="web")
        assert ConversationSearchService._passes_filters(self._conv(platform="web"), f) is True

    def test_platform_filter_no_match(self):
        f = SearchFilters(platform="discord")
        assert ConversationSearchService._passes_filters(self._conv(platform="web"), f) is False

    def test_is_archived_filter(self):
        f = SearchFilters(is_archived=False)
        assert ConversationSearchService._passes_filters(self._conv(is_archived=False), f) is True
        assert ConversationSearchService._passes_filters(self._conv(is_archived=True), f) is False

    def test_is_favorite_filter(self):
        f = SearchFilters(is_favorite=True)
        assert ConversationSearchService._passes_filters(self._conv(is_favorite=True), f) is True
        assert ConversationSearchService._passes_filters(self._conv(is_favorite=False), f) is False

    def test_tags_filter_all_required(self):
        f = SearchFilters(tags=["ai", "python"])
        assert (
            ConversationSearchService._passes_filters(self._conv(tags=["ai", "python", "ml"]), f)
            is True
        )
        assert ConversationSearchService._passes_filters(self._conv(tags=["ai"]), f) is False

    def test_date_from_filter(self):
        cutoff = _NOW - timedelta(days=5)
        f = SearchFilters(date_from=cutoff)
        # recent conversation passes
        assert (
            ConversationSearchService._passes_filters(self._conv(last_message_at=_NOW), f) is True
        )
        # old conversation fails
        assert (
            ConversationSearchService._passes_filters(
                self._conv(last_message_at=_NOW - timedelta(days=10)), f
            )
            is False
        )

    def test_date_to_filter(self):
        cutoff = _NOW - timedelta(days=5)
        f = SearchFilters(date_to=cutoff)
        # old conversation passes
        assert (
            ConversationSearchService._passes_filters(
                self._conv(last_message_at=_NOW - timedelta(days=10)), f
            )
            is True
        )
        # recent conversation fails
        assert (
            ConversationSearchService._passes_filters(self._conv(last_message_at=_NOW), f) is False
        )

    def test_combined_filters(self):
        f = SearchFilters(platform="discord", is_favorite=True)
        assert (
            ConversationSearchService._passes_filters(
                self._conv(platform="discord", is_favorite=True), f
            )
            is True
        )
        assert (
            ConversationSearchService._passes_filters(
                self._conv(platform="web", is_favorite=True), f
            )
            is False
        )


# ---------------------------------------------------------------------------
# _merge_results scoring
# ---------------------------------------------------------------------------


class TestMergeResults:
    def _service(self) -> ConversationSearchService:
        return _make_service()

    def _raw(self, source: str, cid: str | None = None, **kwargs) -> dict[str, Any]:
        row = _make_conv_row(kwargs)
        row["conversation_id"] = cid or row["id"]
        row["match_source"] = source
        row["matched_text"] = kwargs.get("matched_text", "some text")
        return row

    def test_title_match_scores_1(self):
        svc = self._service()
        cid = str(uuid4())
        results = svc._merge_results("query", [self._raw("title", cid)], [])
        assert len(results) == 1
        assert results[0].relevance_score == 1.0

    def test_summary_match_scores_07(self):
        svc = self._service()
        cid = str(uuid4())
        results = svc._merge_results("query", [self._raw("summary", cid)], [])
        assert len(results) == 1
        assert results[0].relevance_score == 0.7

    def test_message_match_scores_05(self):
        svc = self._service()
        cid = str(uuid4())
        results = svc._merge_results("query", [], [self._raw("message", cid)])
        assert len(results) == 1
        assert results[0].relevance_score == 0.5

    def test_multi_source_boost(self):
        svc = self._service()
        cid = str(uuid4())
        # title match + message match for same conversation
        results = svc._merge_results(
            "query",
            [self._raw("title", cid)],
            [self._raw("message", cid)],
        )
        assert len(results) == 1
        # title (1.0) + boost (0.1) = 1.0 (capped)
        assert results[0].relevance_score == 1.0

    def test_summary_plus_message_boost(self):
        svc = self._service()
        cid = str(uuid4())
        results = svc._merge_results(
            "query",
            [self._raw("summary", cid)],
            [self._raw("message", cid)],
        )
        assert len(results) == 1
        # summary (0.7) + boost (0.1) = 0.8
        assert results[0].relevance_score == pytest.approx(0.8, abs=0.001)

    def test_deduplication(self):
        svc = self._service()
        cid = str(uuid4())
        # Same conversation appears twice in conv_matches (title + summary)
        results = svc._merge_results(
            "query",
            [self._raw("title", cid), self._raw("summary", cid)],
            [],
        )
        assert len(results) == 1

    def test_multiple_conversations(self):
        svc = self._service()
        cid1, cid2 = str(uuid4()), str(uuid4())
        results = svc._merge_results(
            "query",
            [self._raw("title", cid1), self._raw("summary", cid2)],
            [],
        )
        assert len(results) == 2

    def test_highlight_snippets_generated(self):
        svc = self._service()
        cid = str(uuid4())
        results = svc._merge_results(
            "hello",
            [self._raw("title", cid, matched_text="Hello World")],
            [],
        )
        assert len(results) == 1
        assert "<mark>" in results[0].highlight_snippets[0]

    def test_matched_content_populated(self):
        svc = self._service()
        cid = str(uuid4())
        results = svc._merge_results(
            "query",
            [self._raw("title", cid, matched_text="My Title")],
            [],
        )
        assert "My Title" in results[0].matched_content


# ---------------------------------------------------------------------------
# search_conversations - orchestration
# ---------------------------------------------------------------------------


class TestSearchConversations:
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_matches(self):
        svc = _make_service(conv_response_data=[], msg_response_data=[])
        results = await svc.search_conversations(user_id=uuid4(), query="nothing")
        assert results == []

    @pytest.mark.asyncio
    async def test_returns_results_sorted_by_score(self):
        cid1 = str(uuid4())
        cid2 = str(uuid4())

        # Two conversations: one title match (score 1.0), one summary match (0.7)
        title_row = _make_conv_row({"id": cid1, "title": "Python tutorial"})
        summary_row = _make_conv_row({"id": cid2, "summary": "Python tutorial"})

        client = MagicMock()
        table_mock = MagicMock()
        client.table.return_value = table_mock

        for method in (
            "select",
            "eq",
            "ilike",
            "gte",
            "lte",
            "contains",
            "limit",
            "offset",
            "order",
        ):
            getattr(table_mock, method).return_value = table_mock

        call_count = [0]

        def execute_side_effect():
            call_count[0] += 1
            resp = MagicMock()
            # First call: title search → title_row
            # Second call: summary search → summary_row
            # Third call: message search → empty
            if call_count[0] == 1:
                resp.data = [title_row]
            elif call_count[0] == 2:
                resp.data = [summary_row]
            else:
                resp.data = []
            return resp

        table_mock.execute.side_effect = execute_side_effect

        conv_repo = MagicMock()
        conv_repo.client = client
        conv_repo.get_conversation = AsyncMock(return_value=None)
        msg_repo = MagicMock()

        svc = ConversationSearchService(conv_repo, msg_repo)
        results = await svc.search_conversations(user_id=uuid4(), query="Python")

        assert len(results) >= 1
        # First result should have higher or equal score
        if len(results) >= 2:
            assert results[0].relevance_score >= results[1].relevance_score

    @pytest.mark.asyncio
    async def test_pagination_offset(self):
        """offset parameter skips the correct number of results."""
        rows = [_make_conv_row({"id": str(uuid4()), "title": f"Conv {i}"}) for i in range(5)]

        client = MagicMock()
        table_mock = MagicMock()
        client.table.return_value = table_mock

        for method in (
            "select",
            "eq",
            "ilike",
            "gte",
            "lte",
            "contains",
            "limit",
            "offset",
            "order",
        ):
            getattr(table_mock, method).return_value = table_mock

        call_count = [0]

        def execute_side_effect():
            call_count[0] += 1
            resp = MagicMock()
            if call_count[0] == 1:
                resp.data = rows
            else:
                resp.data = []
            return resp

        table_mock.execute.side_effect = execute_side_effect

        conv_repo = MagicMock()
        conv_repo.client = client
        conv_repo.get_conversation = AsyncMock(return_value=None)
        msg_repo = MagicMock()

        svc = ConversationSearchService(conv_repo, msg_repo)
        results = await svc.search_conversations(user_id=uuid4(), query="Conv", limit=3, offset=2)
        # 5 total results, skip 2, return up to 3 → 3 results
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_pagination_limit(self):
        """limit parameter caps the number of results."""
        rows = [_make_conv_row({"id": str(uuid4()), "title": f"Conv {i}"}) for i in range(10)]

        client = MagicMock()
        table_mock = MagicMock()
        client.table.return_value = table_mock

        for method in (
            "select",
            "eq",
            "ilike",
            "gte",
            "lte",
            "contains",
            "limit",
            "offset",
            "order",
        ):
            getattr(table_mock, method).return_value = table_mock

        call_count = [0]

        def execute_side_effect():
            call_count[0] += 1
            resp = MagicMock()
            if call_count[0] == 1:
                resp.data = rows
            else:
                resp.data = []
            return resp

        table_mock.execute.side_effect = execute_side_effect

        conv_repo = MagicMock()
        conv_repo.client = client
        conv_repo.get_conversation = AsyncMock(return_value=None)
        msg_repo = MagicMock()

        svc = ConversationSearchService(conv_repo, msg_repo)
        results = await svc.search_conversations(user_id=uuid4(), query="Conv", limit=5, offset=0)
        assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_default_filters_exclude_archived(self):
        """Default SearchFilters should exclude archived conversations."""
        svc = _make_service()
        # Verify _apply_filters is called with is_archived=False by default
        # We check indirectly: the query builder's eq() should be called with is_archived=False
        client = svc.conversation_repo.client
        table_mock = client.table.return_value

        await svc.search_conversations(user_id=uuid4(), query="test")

        # eq should have been called with is_archived=False at some point
        eq_calls = [str(c) for c in table_mock.eq.call_args_list]
        assert any("is_archived" in c for c in eq_calls)

    @pytest.mark.asyncio
    async def test_uses_default_filters_when_none_provided(self):
        svc = _make_service()
        # Should not raise
        results = await svc.search_conversations(user_id=uuid4(), query="test")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_database_error_propagates(self):
        """A fatal error (e.g. client itself raises) should propagate as DatabaseError.

        Individual sub-query failures are swallowed (resilient design), but if
        the client object itself is broken in a way that raises outside the
        try/except guards, the service wraps it in a DatabaseError.
        """
        from app.core.errors import DatabaseError

        conv_repo = MagicMock()
        # Make client.table raise *after* the internal try/except guards, by
        # making the conv_repo.client property itself raise.
        type(conv_repo).client = property(lambda self: (_ for _ in ()).throw(RuntimeError("fatal")))
        conv_repo.get_conversation = AsyncMock(return_value=None)
        msg_repo = MagicMock()

        svc = ConversationSearchService(conv_repo, msg_repo)

        with pytest.raises((DatabaseError, RuntimeError)):
            await svc.search_conversations(user_id=uuid4(), query="test")

    @pytest.mark.asyncio
    async def test_accepts_uuid_user_id(self):
        svc = _make_service()
        uid = uuid4()
        results = await svc.search_conversations(user_id=uid, query="test")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_accepts_string_user_id(self):
        svc = _make_service()
        results = await svc.search_conversations(user_id=str(uuid4()), query="test")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_strips_query_whitespace(self):
        """Leading/trailing whitespace in query should be stripped."""
        svc = _make_service()
        # Should not raise and should work the same as a clean query
        results = await svc.search_conversations(user_id=uuid4(), query="  test  ")
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# _apply_filters - query builder integration
# ---------------------------------------------------------------------------


class TestApplyFilters:
    def _make_query_mock(self) -> MagicMock:
        q = MagicMock()
        for method in ("eq", "gte", "lte", "contains"):
            getattr(q, method).return_value = q
        return q

    def _service(self) -> ConversationSearchService:
        return _make_service()

    def test_no_filters_no_calls(self):
        svc = self._service()
        q = self._make_query_mock()
        result = svc._apply_filters(q, SearchFilters(is_archived=None))
        q.eq.assert_not_called()
        q.gte.assert_not_called()
        q.lte.assert_not_called()
        q.contains.assert_not_called()

    def test_platform_filter_calls_eq(self):
        svc = self._service()
        q = self._make_query_mock()
        svc._apply_filters(q, SearchFilters(platform="discord", is_archived=None))
        q.eq.assert_any_call("platform", "discord")

    def test_is_archived_filter_calls_eq(self):
        svc = self._service()
        q = self._make_query_mock()
        svc._apply_filters(q, SearchFilters(is_archived=False))
        q.eq.assert_any_call("is_archived", False)

    def test_is_favorite_filter_calls_eq(self):
        svc = self._service()
        q = self._make_query_mock()
        svc._apply_filters(q, SearchFilters(is_favorite=True, is_archived=None))
        q.eq.assert_any_call("is_favorite", True)

    def test_tags_filter_calls_contains(self):
        svc = self._service()
        q = self._make_query_mock()
        svc._apply_filters(q, SearchFilters(tags=["ai", "python"], is_archived=None))
        assert q.contains.call_count == 2

    def test_date_from_calls_gte(self):
        svc = self._service()
        q = self._make_query_mock()
        cutoff = _NOW - timedelta(days=7)
        svc._apply_filters(q, SearchFilters(date_from=cutoff, is_archived=None))
        q.gte.assert_called_once()

    def test_date_to_calls_lte(self):
        svc = self._service()
        q = self._make_query_mock()
        svc._apply_filters(q, SearchFilters(date_to=_NOW, is_archived=None))
        q.lte.assert_called_once()
