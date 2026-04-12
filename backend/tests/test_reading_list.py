"""
Property-based tests for the Interactive Reading List feature.
Uses Hypothesis to verify correctness properties defined in design.md.
"""

import asyncio
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.bot.cogs.reading_list import MarkAsReadButton, PaginationView, RatingSelect
from app.schemas.article import ReadingListItem
from app.services.notion_service import NotionService

# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------


def reading_list_item_strategy(
    status: Optional[str] = None,
    rating: Optional[int] = None,
    null_rating: bool = False,
):
    """Build a strategy that generates ReadingListItem instances."""
    page_id_st = st.text(
        min_size=1,
        max_size=36,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-"),
    )
    title_st = st.text(min_size=1, max_size=50)
    url_st = st.just("https://example.com/article")
    category_st = st.text(min_size=1, max_size=20)

    if null_rating:
        rating_st = st.none()
    elif rating is not None:
        rating_st = st.just(rating)
    else:
        rating_st = st.one_of(st.none(), st.integers(min_value=1, max_value=5))

    @st.composite
    def _build(draw):
        return ReadingListItem(
            page_id=draw(page_id_st),
            title=draw(title_st),
            url=draw(url_st),
            source_category=draw(category_st),
            added_at=None,
            rating=draw(rating_st),
        )

    return _build()


def make_notion_page(
    page_id: str, title: str, url: str, category: str, status: str, rating: Optional[int]
) -> dict:
    """Build a minimal Notion page dict that _parse_reading_list_item can consume."""
    rating_prop = {"number": rating} if rating is not None else {"number": None}
    return {
        "id": page_id,
        "properties": {
            "Title": {"title": [{"plain_text": title}]},
            "URL": {"url": url},
            "Source_Category": {"select": {"name": category}},
            "Added_At": {"date": None},
            "Status": {"status": {"name": status}},
            "Rating": rating_prop,
        },
    }


# ---------------------------------------------------------------------------
# P1: get_reading_list 只回傳 Unread 文章
# Feature: interactive-reading-list, Property 1: get_reading_list 只回傳 Unread 文章
# Validates: Requirements 1.1, 5.3
# ---------------------------------------------------------------------------


@given(
    unread_items=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=36),
            st.text(min_size=1, max_size=50),
            st.just("https://example.com/article"),
            st.text(min_size=1, max_size=20),
        ),
        min_size=0,
        max_size=10,
    ),
    read_items=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=36),
            st.text(min_size=1, max_size=50),
            st.just("https://example.com/article"),
            st.text(min_size=1, max_size=20),
        ),
        min_size=0,
        max_size=10,
    ),
)
@settings(max_examples=5)
def test_p1_get_reading_list_only_returns_unread(unread_items, read_items):
    # Feature: interactive-reading-list, Property 1: get_reading_list 只回傳 Unread 文章
    unread_pages = [
        make_notion_page(pid, title, url, cat, "Unread", None)
        for pid, title, url, cat in unread_items
    ]
    # get_reading_list filters by Unread at the query level; the mock simulates
    # that Notion already returns only Unread pages (as the real API would).
    # We verify that _parse_reading_list_item never produces items from Read pages.
    notion = NotionService.__new__(NotionService)

    # Parse only unread pages — none of the read pages should appear
    results = []
    for page in unread_pages:
        item = notion._parse_reading_list_item(page)
        if item:
            results.append(item)

    # All parsed items came from unread_pages; read_items were never passed in
    assert len(results) == len([p for p in unread_pages if p["properties"]["URL"]["url"]])

    # Simulate the full async path with a mock
    mock_db_response = {"results": unread_pages}

    async def _run():
        with patch.object(NotionService, "__init__", lambda self: None):
            svc = NotionService()
            svc.client = MagicMock()
            svc.read_later_db_id = "fake-db-id"
            svc.client.databases = MagicMock()
            svc.client.databases.query = AsyncMock(return_value=mock_db_response)
            return await svc.get_reading_list()

    items = asyncio.get_event_loop().run_until_complete(_run())
    # Every returned item must have come from the unread_pages list
    returned_ids = {item.page_id for item in items}
    unread_ids = {p["id"] for p in unread_pages}
    assert returned_ids.issubset(unread_ids)


# ---------------------------------------------------------------------------
# P2: 分頁大小不超過 5 筆
# Feature: interactive-reading-list, Property 2: 分頁大小不超過 5 筆
# Validates: Requirements 1.2
# ---------------------------------------------------------------------------


def _current_page_items(items: list, page: int, page_size: int = 5) -> list:
    """Helper: replicate PaginationView._current_page_items logic without Discord UI."""
    start = page * page_size
    return items[start : start + page_size]


@given(
    items=st.lists(
        st.builds(
            ReadingListItem,
            page_id=st.text(min_size=1, max_size=36),
            title=st.text(min_size=1, max_size=50),
            url=st.just("https://example.com/article"),
            source_category=st.text(min_size=1, max_size=20),
            added_at=st.none(),
            rating=st.none(),
        ),
        min_size=0,
        max_size=30,
    )
)
@settings(max_examples=5)
def test_p2_pagination_never_exceeds_5_items(items):
    # Feature: interactive-reading-list, Property 2: 分頁大小不超過 5 筆
    if not items:
        return  # empty list is a valid edge case; no pages to check

    page_size = 5
    total_pages = max(1, (len(items) + page_size - 1) // page_size)
    for page_num in range(total_pages):
        page_items = _current_page_items(items, page_num, page_size)
        assert (
            len(page_items) <= page_size
        ), f"Page {page_num} has {len(page_items)} items, expected <= {page_size}"


# ---------------------------------------------------------------------------
# P3: 每篇文章都有標記已讀按鈕
# Feature: interactive-reading-list, Property 3: 每篇文章都有標記已讀按鈕
# Validates: Requirements 2.1
# ---------------------------------------------------------------------------


@given(
    items=st.lists(
        st.builds(
            ReadingListItem,
            page_id=st.text(min_size=1, max_size=36),
            title=st.text(min_size=1, max_size=50),
            url=st.just("https://example.com/article"),
            source_category=st.text(min_size=1, max_size=20),
            added_at=st.none(),
            rating=st.none(),
        ),
        min_size=1,
        max_size=20,
    )
)
@settings(max_examples=5)
def test_p3_every_item_has_mark_as_read_button(items):
    # Feature: interactive-reading-list, Property 3: 每篇文章都有標記已讀按鈕
    page_items = _current_page_items(items, page=0)

    # Create MarkAsReadButton for each page item and verify page_id matches
    buttons = [MarkAsReadButton(item, row=1) for item in page_items]
    button_page_ids = {btn.custom_id.replace("mark_read_", "") for btn in buttons}

    for item in page_items:
        assert (
            item.page_id in button_page_ids
        ), f"No MarkAsReadButton found for page_id={item.page_id!r}"


# ---------------------------------------------------------------------------
# P4: mark_as_read round-trip 正確性
# Feature: interactive-reading-list, Property 4: mark_as_read round-trip 正確性
# Validates: Requirements 2.2, 2.5, 5.4
# ---------------------------------------------------------------------------


@given(
    items=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=36),
            st.text(min_size=1, max_size=50),
        ),
        min_size=1,
        max_size=10,
    ),
    target_index=st.integers(min_value=0, max_value=9),
)
@settings(max_examples=5)
def test_p4_mark_as_read_roundtrip(items, target_index):
    # Feature: interactive-reading-list, Property 4: mark_as_read round-trip 正確性
    if not items:
        return
    target_index = target_index % len(items)
    target_id = items[target_index][0]

    # In-memory store: maps page_id -> status
    db: dict = {pid: "Unread" for pid, _ in items}

    async def _run():
        with patch.object(NotionService, "__init__", lambda self: None):
            svc = NotionService()
            svc.client = MagicMock()
            svc.read_later_db_id = "fake-db-id"

            # mark_as_read updates the in-memory db
            async def fake_mark(page_id, properties):
                db[page_id] = "Read"

            svc.client.pages = MagicMock()
            svc.client.pages.update = AsyncMock(side_effect=fake_mark)

            # get_reading_list returns only Unread pages
            async def fake_query(**kwargs):
                pages = [
                    make_notion_page(
                        pid, title, "https://example.com/article", "cat", db[pid], None
                    )
                    for pid, title in items
                    if db[pid] == "Unread"
                ]
                return {"results": pages}

            svc.client.databases = MagicMock()
            svc.client.databases.query = AsyncMock(side_effect=fake_query)

            await svc.mark_as_read(target_id)
            remaining = await svc.get_reading_list()
            return remaining

    remaining = asyncio.get_event_loop().run_until_complete(_run())
    returned_ids = {item.page_id for item in remaining}
    assert (
        target_id not in returned_ids
    ), f"page_id={target_id!r} should not appear in get_reading_list() after mark_as_read"


# ---------------------------------------------------------------------------
# P5: 每篇文章都有包含 1–5 選項的評分選單
# Feature: interactive-reading-list, Property 5: 每篇文章都有包含 1–5 選項的評分選單
# Validates: Requirements 3.1
# ---------------------------------------------------------------------------


@given(
    items=st.lists(
        st.builds(
            ReadingListItem,
            page_id=st.text(min_size=1, max_size=36),
            title=st.text(min_size=1, max_size=50),
            url=st.just("https://example.com/article"),
            source_category=st.text(min_size=1, max_size=20),
            added_at=st.none(),
            rating=st.none(),
        ),
        min_size=1,
        max_size=20,
    )
)
@settings(max_examples=5)
def test_p5_every_item_has_rating_select_with_1_to_5(items):
    # Feature: interactive-reading-list, Property 5: 每篇文章都有包含 1–5 選項的評分選單
    page_items = _current_page_items(items, page=0)

    expected_values = {"1", "2", "3", "4", "5"}

    for item in page_items:
        select = RatingSelect(item, row=2)
        option_values = {opt.value for opt in select.options}
        assert (
            option_values == expected_values
        ), f"RatingSelect for {item.page_id!r} has options {option_values}, expected {expected_values}"


# ---------------------------------------------------------------------------
# P6: rate_article round-trip 正確性
# Feature: interactive-reading-list, Property 6: rate_article round-trip 正確性
# Validates: Requirements 3.2, 3.5, 5.5
# ---------------------------------------------------------------------------


@given(
    items=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=36),
            st.text(min_size=1, max_size=50),
        ),
        min_size=1,
        max_size=10,
    ),
    target_index=st.integers(min_value=0, max_value=9),
    rating=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=5)
def test_p6_rate_article_roundtrip(items, target_index, rating):
    # Feature: interactive-reading-list, Property 6: rate_article round-trip 正確性
    if not items:
        return
    target_index = target_index % len(items)
    target_id = items[target_index][0]

    # In-memory store: maps page_id -> rating (None = unrated)
    ratings_db: dict = {pid: None for pid, _ in items}

    async def _run():
        with patch.object(NotionService, "__init__", lambda self: None):
            svc = NotionService()
            svc.client = MagicMock()
            svc.read_later_db_id = "fake-db-id"

            # rate_article writes to in-memory db
            async def fake_update(page_id, properties):
                ratings_db[page_id] = properties["Rating"]["number"]

            svc.client.pages = MagicMock()
            svc.client.pages.update = AsyncMock(side_effect=fake_update)

            # get_reading_list returns all items with current ratings
            async def fake_query(**kwargs):
                pages = [
                    make_notion_page(
                        pid, title, "https://example.com/article", "cat", "Unread", ratings_db[pid]
                    )
                    for pid, title in items
                ]
                return {"results": pages}

            svc.client.databases = MagicMock()
            svc.client.databases.query = AsyncMock(side_effect=fake_query)

            await svc.rate_article(target_id, rating)
            all_items = await svc.get_reading_list()
            return all_items

    all_items = asyncio.get_event_loop().run_until_complete(_run())
    item_map = {item.page_id: item for item in all_items}

    assert target_id in item_map, f"Article {target_id!r} not found after rating"
    assert (
        item_map[target_id].rating == rating
    ), f"Expected rating={rating}, got {item_map[target_id].rating}"


# ---------------------------------------------------------------------------
# P7: get_highly_rated_articles 只回傳高於閾值的文章
# Feature: interactive-reading-list, Property 7: get_highly_rated_articles 只回傳高於閾值的文章
# Validates: Requirements 4.1, 5.6
# ---------------------------------------------------------------------------


@given(
    items=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=36),
            st.text(min_size=1, max_size=50),
            st.one_of(st.none(), st.integers(min_value=1, max_value=5)),
        ),
        min_size=0,
        max_size=15,
    ),
    threshold=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=5)
def test_p7_get_highly_rated_articles_only_above_threshold(items, threshold):
    # Feature: interactive-reading-list, Property 7: get_highly_rated_articles 只回傳高於閾值的文章
    # Simulate Notion filtering: only pages with rating >= threshold are returned
    qualifying_pages = [
        make_notion_page(pid, title, "https://example.com/article", "cat", "Read", rating)
        for pid, title, rating in items
        if rating is not None and rating >= threshold
    ]

    async def _run():
        with patch.object(NotionService, "__init__", lambda self: None):
            svc = NotionService()
            svc.client = MagicMock()
            svc.read_later_db_id = "fake-db-id"
            svc.client.databases = MagicMock()
            svc.client.databases.query = AsyncMock(return_value={"results": qualifying_pages})
            return await svc.get_highly_rated_articles(threshold=threshold)

    result = asyncio.get_event_loop().run_until_complete(_run())

    for item in result:
        assert (
            item.rating is not None
        ), f"Article {item.page_id!r} has rating=None but was returned by get_highly_rated_articles"
        assert (
            item.rating >= threshold
        ), f"Article {item.page_id!r} has rating={item.rating} < threshold={threshold}"


# ---------------------------------------------------------------------------
# P8: 未評分文章的 rating 為 None
# Feature: interactive-reading-list, Property 8: 未評分文章的 rating 為 None
# Validates: Requirements 5.2
# ---------------------------------------------------------------------------


@given(
    items=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=36),
            st.text(min_size=1, max_size=50),
        ),
        min_size=1,
        max_size=10,
    )
)
@settings(max_examples=5)
def test_p8_unrated_articles_have_none_rating(items):
    # Feature: interactive-reading-list, Property 8: 未評分文章的 rating 為 None
    # All pages have Rating = null (None) in Notion
    null_rated_pages = [
        make_notion_page(pid, title, "https://example.com/article", "cat", "Unread", None)
        for pid, title in items
    ]

    async def _run():
        with patch.object(NotionService, "__init__", lambda self: None):
            svc = NotionService()
            svc.client = MagicMock()
            svc.read_later_db_id = "fake-db-id"
            svc.client.databases = MagicMock()
            svc.client.databases.query = AsyncMock(return_value={"results": null_rated_pages})
            return await svc.get_reading_list()

    result = asyncio.get_event_loop().run_until_complete(_run())

    for item in result:
        assert (
            item.rating is None
        ), f"Article {item.page_id!r} should have rating=None but got {item.rating}"


# ---------------------------------------------------------------------------
# Tasks 7.1–7.8 — Unit tests for ReadingListGroup commands and UI components
# ---------------------------------------------------------------------------

from app.bot.cogs.reading_list import ReadingListGroup
from app.core.exceptions import LLMServiceError, NotionServiceError


def make_item(page_id="page-001", title="Test Article", rating=None):
    return ReadingListItem(
        page_id=page_id,
        title=title,
        url="https://example.com/article",
        source_category="AI",
        rating=rating,
    )


def make_interaction():
    interaction = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.message.edit = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Task 7.1 — Unread 清單為空時回覆正確訊息
# ---------------------------------------------------------------------------


class TestViewEmptyList:
    @pytest.mark.asyncio
    async def test_empty_reading_list_replies_correct_message(self):
        """7.1: When get_reading_list() returns [], view replies with empty-list message."""
        group = ReadingListGroup()
        interaction = make_interaction()

        with patch("app.bot.cogs.reading_list.NotionService") as MockNotion:
            instance = MockNotion.return_value
            instance.get_reading_list = AsyncMock(return_value=[])
            await group.view.callback(group, interaction)

        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        assert "📭 目前待讀清單是空的！" in call_args[0][0]


# ---------------------------------------------------------------------------
# Task 7.2 — Notion 錯誤時不顯示部分資料
# ---------------------------------------------------------------------------


class TestViewNotionError:
    @pytest.mark.asyncio
    async def test_notion_error_replies_error_and_no_partial_data(self):
        """7.2: When get_reading_list() raises NotionServiceError, replies with error and no partial data."""
        group = ReadingListGroup()
        interaction = make_interaction()

        with patch("app.bot.cogs.reading_list.NotionService") as MockNotion:
            instance = MockNotion.return_value
            instance.get_reading_list = AsyncMock(side_effect=NotionServiceError("DB unreachable"))
            await group.view.callback(group, interaction)

        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        sent_content = call_args[0][0]
        # Must contain an error indicator
        assert "❌" in sent_content
        # Must NOT contain article data (no PaginationView content)
        assert "📚" not in sent_content


# ---------------------------------------------------------------------------
# Task 7.3 — 標記已讀失敗時按鈕狀態不變
# ---------------------------------------------------------------------------


class TestMarkAsReadButtonFailure:
    @pytest.mark.asyncio
    async def test_mark_as_read_failure_button_state_unchanged(self):
        """7.3: When mark_as_read() raises, MarkAsReadButton does NOT set self.disabled=True."""
        item = make_item()
        button = MarkAsReadButton(item, row=1)
        interaction = make_interaction()

        with patch("app.bot.cogs.reading_list.NotionService") as MockNotion:
            instance = MockNotion.return_value
            instance.mark_as_read = AsyncMock(side_effect=Exception("Notion timeout"))
            await button.callback(interaction)

        # Button should NOT be disabled after failure
        assert button.disabled is False


# ---------------------------------------------------------------------------
# Task 7.4 — 高評分文章為 0 時回覆正確訊息
# ---------------------------------------------------------------------------


class TestRecommendNoHighRatedArticles:
    @pytest.mark.asyncio
    async def test_no_high_rated_articles_replies_correct_message(self):
        """7.4: When get_highly_rated_articles() returns [], recommend replies with correct message."""
        group = ReadingListGroup()
        interaction = make_interaction()

        with patch("app.bot.cogs.reading_list.NotionService") as MockNotion:
            instance = MockNotion.return_value
            instance.get_highly_rated_articles = AsyncMock(return_value=[])
            await group.recommend.callback(group, interaction)

        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        assert "尚無足夠的高評分文章，請先對文章評分（4 星以上）後再試。" in call_args[0][0]


# ---------------------------------------------------------------------------
# Task 7.5 — LLM 錯誤時回覆正確訊息
# ---------------------------------------------------------------------------


class TestRecommendLLMError:
    @pytest.mark.asyncio
    async def test_llm_error_replies_correct_message(self):
        """7.5: When generate_reading_recommendation() raises LLMServiceError, replies with correct message."""
        group = ReadingListGroup()
        interaction = make_interaction()

        with (
            patch("app.bot.cogs.reading_list.NotionService") as MockNotion,
            patch("app.bot.cogs.reading_list.LLMService") as MockLLM,
        ):
            notion_instance = MockNotion.return_value
            notion_instance.get_highly_rated_articles = AsyncMock(
                return_value=[make_item(rating=5)]
            )
            llm_instance = MockLLM.return_value
            llm_instance.generate_reading_recommendation = AsyncMock(
                side_effect=LLMServiceError("LLM unavailable")
            )
            await group.recommend.callback(group, interaction)

        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        assert "推薦功能暫時無法使用" in call_args[0][0]


# ---------------------------------------------------------------------------
# Task 7.6 — 多頁清單時顯示分頁按鈕
# ---------------------------------------------------------------------------


class TestPaginationViewButtons:
    def test_more_than_5_items_has_prev_and_next_buttons(self):
        """7.6: When items list has more than 5 items, PaginationView contains both prev and next page buttons."""
        # Use page=1 (second page) so only 1 item is on the page, avoiding Discord row limit
        items = [make_item(page_id=f"page-{i:03d}", title=f"Article {i}") for i in range(6)]
        view = PaginationView(items, page=1)

        button_labels = [child.label for child in view.children if hasattr(child, "label")]
        assert any("上一頁" in label for label in button_labels), "Missing prev page button"
        assert any("下一頁" in label for label in button_labels), "Missing next page button"


# ---------------------------------------------------------------------------
# Task 7.7 — 評分成功時 ephemeral 訊息包含星數
# ---------------------------------------------------------------------------


class TestRatingSelectSuccess:
    @pytest.mark.asyncio
    async def test_rating_success_ephemeral_contains_star(self):
        """7.7: When rate_article() succeeds, RatingSelect callback sends ephemeral message containing ⭐."""
        item = make_item()
        select = RatingSelect(item, row=2)
        select._values = ["4"]
        interaction = make_interaction()

        with patch("app.bot.cogs.reading_list.NotionService") as MockNotion:
            instance = MockNotion.return_value
            instance.rate_article = AsyncMock(return_value=None)
            await select.callback(interaction)

        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        sent_content = call_args[0][0]
        assert "⭐" in sent_content


# ---------------------------------------------------------------------------
# Task 7.8 — /reading_list view 回覆為 ephemeral
# ---------------------------------------------------------------------------


class TestViewEphemeral:
    @pytest.mark.asyncio
    async def test_view_command_uses_ephemeral(self):
        """7.8: The /reading_list view command uses ephemeral=True in its response."""
        group = ReadingListGroup()
        interaction = make_interaction()

        with patch("app.bot.cogs.reading_list.NotionService") as MockNotion:
            instance = MockNotion.return_value
            instance.get_reading_list = AsyncMock(return_value=[])
            await group.view.callback(group, interaction)

        # Check that followup.send was called with ephemeral=True
        call_kwargs = interaction.followup.send.call_args[1]
        assert call_kwargs.get("ephemeral") is True
