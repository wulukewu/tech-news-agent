"""
Tests for NotionService.create_weekly_digest_page and build_digest_title.
"""
import re
import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from hypothesis import given, settings as h_settings
from hypothesis import strategies as st

from app.services.notion_service import NotionService, build_digest_title
from app.core.exceptions import NotionServiceError
from app.schemas.article import ArticleSchema, AIAnalysis


# ===========================================================================
# Sub-task 5.1 — Property 1: 週報標題格式符合 ISO 週次規範
# ===========================================================================

# Feature: notion-weekly-digest, Property 1: 週報標題格式符合 ISO 週次規範
@given(dt=st.datetimes())
@h_settings(max_examples=100)
def test_digest_title_format(dt):
    """Validates: Requirements 2.2

    For any valid datetime, build_digest_title(dt) must match ^週報 \\d{4}-\\d{2}$
    and the week number must be in range 1-53.
    """
    title = build_digest_title(dt)
    assert re.match(r"^週報 \d{4}-\d{2}$", title), (
        f"Title '{title}' does not match expected format '週報 YYYY-WW'"
    )
    # Extract week number and verify range
    week_str = title.split("-")[1]
    week_num = int(week_str)
    assert 1 <= week_num <= 53, f"Week number {week_num} is out of range 1-53"


# ===========================================================================
# Sub-task 5.2 — Property 2: Article_Count 與 Hardcore 文章列表長度一致
# ===========================================================================

ai_analysis_strategy = st.builds(
    AIAnalysis,
    is_hardcore=st.booleans(),
    reason=st.text(min_size=1, max_size=100),
    actionable_takeaway=st.text(max_size=100),
    tinkering_index=st.integers(min_value=1, max_value=5),
)

article_strategy = st.builds(
    ArticleSchema,
    title=st.text(min_size=1, max_size=100),
    url=st.just("https://example.com/article"),
    content_preview=st.text(max_size=200),
    source_category=st.sampled_from(["AI", "DevOps", "Security", "Web"]),
    source_name=st.text(min_size=1, max_size=50),
    ai_analysis=ai_analysis_strategy,
)


# Feature: notion-weekly-digest, Property 2: Article_Count 與 Hardcore 文章列表長度一致
@given(hardcore_articles=st.lists(article_strategy))
@h_settings(max_examples=100)
def test_article_count_matches_list(hardcore_articles):
    """Validates: Requirements 2.4

    For any list of ArticleSchema (including empty), the article_count passed to
    create_weekly_digest_page equals len(hardcore_articles).
    """
    captured = {}

    async def mock_pages_create(**kwargs):
        captured["article_count"] = kwargs["properties"]["Article_Count"]["number"]
        return {"id": "page-123", "url": "https://notion.so/page-123"}

    import asyncio

    async def run():
        service = NotionService.__new__(NotionService)
        service.client = MagicMock()
        service.client.pages = MagicMock()
        service.client.pages.create = AsyncMock(side_effect=mock_pages_create)

        with patch("app.services.notion_service.settings") as mock_settings:
            mock_settings.notion_token = "fake-token"
            mock_settings.notion_weekly_digests_db_id = "fake-db-id"
            await service.create_weekly_digest_page(
                title="週報 2025-28",
                published_date=date(2025, 7, 11),
                article_count=len(hardcore_articles),
            )

    asyncio.get_event_loop().run_until_complete(run())
    assert captured["article_count"] == len(hardcore_articles), (
        f"article_count={captured['article_count']} != len(hardcore_articles)={len(hardcore_articles)}"
    )


# ===========================================================================
# Sub-task 5.3 — Unit Tests for create_weekly_digest_page
# ===========================================================================

def make_notion_service_with_mock():
    """Create a NotionService instance with a mocked Notion client."""
    service = NotionService.__new__(NotionService)
    service.client = MagicMock()
    service.client.pages = MagicMock()
    return service


class TestCreateWeeklyDigestPage:
    """Unit tests for NotionService.create_weekly_digest_page — Requirements 1.3, 2.6"""

    @pytest.mark.asyncio
    async def test_api_failure_raises_notion_service_error(self):
        """Notion API failure must raise NotionServiceError. Validates: Requirements 2.6"""
        service = make_notion_service_with_mock()
        service.client.pages.create = AsyncMock(side_effect=Exception("API error"))

        with patch("app.services.notion_service.settings") as mock_settings:
            mock_settings.notion_weekly_digests_db_id = "fake-db-id"
            with pytest.raises(NotionServiceError):
                await service.create_weekly_digest_page(
                    title="週報 2025-28",
                    published_date=date(2025, 7, 11),
                    article_count=5,
                )

    @pytest.mark.asyncio
    async def test_empty_db_id_raises_notion_service_error(self):
        """Empty notion_weekly_digests_db_id must raise NotionServiceError. Validates: Requirements 1.3"""
        service = make_notion_service_with_mock()
        service.client.pages.create = AsyncMock()

        with patch("app.services.notion_service.settings") as mock_settings:
            mock_settings.notion_weekly_digests_db_id = ""
            with pytest.raises(NotionServiceError, match="notion_weekly_digests_db_id"):
                await service.create_weekly_digest_page(
                    title="週報 2025-28",
                    published_date=date(2025, 7, 11),
                    article_count=3,
                )

    @pytest.mark.asyncio
    async def test_successful_creation_returns_page_id_and_url(self):
        """Successful API call returns (page_id, page_url) tuple."""
        service = make_notion_service_with_mock()
        service.client.pages.create = AsyncMock(return_value={
            "id": "abc-123",
            "url": "https://notion.so/abc-123",
        })

        with patch("app.services.notion_service.settings") as mock_settings:
            mock_settings.notion_weekly_digests_db_id = "fake-db-id"
            page_id, page_url = await service.create_weekly_digest_page(
                title="週報 2025-28",
                published_date=date(2025, 7, 11),
                article_count=7,
            )

        assert page_id == "abc-123"
        assert page_url == "https://notion.so/abc-123"

    @pytest.mark.asyncio
    async def test_correct_properties_sent_to_api(self):
        """API is called with correct Title, Published_Date, and Article_Count properties."""
        service = make_notion_service_with_mock()
        service.client.pages.create = AsyncMock(return_value={
            "id": "page-xyz",
            "url": "https://notion.so/page-xyz",
        })

        published = date(2025, 7, 11)
        with patch("app.services.notion_service.settings") as mock_settings:
            mock_settings.notion_weekly_digests_db_id = "db-id-123"
            await service.create_weekly_digest_page(
                title="週報 2025-28",
                published_date=published,
                article_count=10,
            )

        call_kwargs = service.client.pages.create.call_args.kwargs
        props = call_kwargs["properties"]
        assert props["Title"]["title"][0]["text"]["content"] == "週報 2025-28"
        assert props["Published_Date"]["date"]["start"] == "2025-07-11"
        assert props["Article_Count"]["number"] == 10


# ===========================================================================
# Sub-task 6.1 — Property 8: append_digest_blocks 自動分批，每批不超過 100 個
# ===========================================================================

# Feature: notion-weekly-digest, Property 8: append_digest_blocks 自動分批，每批不超過 100 個
@given(blocks=st.lists(st.dictionaries(st.text(), st.text()), min_size=1))
@h_settings(max_examples=100)
def test_append_blocks_batching(blocks):
    """Validates: Requirements 3.7, 6.3

    For any list of N blocks, append_digest_blocks calls blocks.children.append
    exactly ceil(N / 100) times, and each call receives at most 100 blocks.
    """
    import asyncio
    import math

    call_args_list = []

    async def mock_append(**kwargs):
        call_args_list.append(kwargs["children"])

    async def run():
        service = NotionService.__new__(NotionService)
        service.client = MagicMock()
        service.client.blocks = MagicMock()
        service.client.blocks.children = MagicMock()
        service.client.blocks.children.append = AsyncMock(side_effect=mock_append)
        await service.append_digest_blocks(page_id="page-test", blocks=blocks)

    asyncio.get_event_loop().run_until_complete(run())

    n = len(blocks)
    expected_calls = math.ceil(n / 100)
    assert len(call_args_list) == expected_calls, (
        f"Expected {expected_calls} API call(s) for {n} blocks, got {len(call_args_list)}"
    )
    for batch in call_args_list:
        assert len(batch) <= 100, (
            f"Batch size {len(batch)} exceeds 100-block limit"
        )
    # Verify all blocks are present and in order
    all_sent = [block for batch in call_args_list for block in batch]
    assert all_sent == blocks, "Blocks sent to API do not match input blocks"
