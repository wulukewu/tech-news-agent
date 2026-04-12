"""
Unit tests for MarkReadView
Task 7.1: Write unit tests for MarkReadView
Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
"""

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from app.bot.cogs.interactions import MarkReadButton, MarkReadView
from app.schemas.article import ArticlePageResult
from app.services.notion_service import NotionServiceError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_article_page(
    page_id="page-001",
    page_url="https://notion.so/page-001",
    title="Test Article",
    category="AI",
    tinkering_index=3,
):
    return ArticlePageResult(
        page_id=page_id,
        page_url=page_url,
        title=title,
        category=category,
        tinkering_index=tinkering_index,
    )


def make_interaction():
    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    interaction.message = MagicMock()
    interaction.message.edit = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Task 7.1 — Unit tests for MarkReadView
# ---------------------------------------------------------------------------


class TestMarkReadButtonLabel:
    def test_label_truncated_when_title_exceeds_15_chars(self):
        """Title > 15 chars → label is '✅ {title[:15]}...'"""
        article_page = make_article_page(title="A" * 16)
        btn = MarkReadButton(article_page)
        assert btn.label == f"✅ {'A' * 15}..."

    def test_label_not_truncated_when_title_is_exactly_15_chars(self):
        """Title == 15 chars → label is '✅ {title}' (no ellipsis)"""
        article_page = make_article_page(title="B" * 15)
        btn = MarkReadButton(article_page)
        assert btn.label == f"✅ {'B' * 15}"

    def test_label_not_truncated_when_title_is_short(self):
        """Title < 15 chars → label is '✅ {title}' (no ellipsis)"""
        article_page = make_article_page(title="Short")
        btn = MarkReadButton(article_page)
        assert btn.label == "✅ Short"


class TestMarkReadButtonCustomId:
    def test_custom_id_format(self):
        """custom_id must be 'mark_read_{page_id}'"""
        article_page = make_article_page(page_id="test-page-123")
        btn = MarkReadButton(article_page)
        assert btn.custom_id == "mark_read_test-page-123"


class TestMarkReadButtonCallback:
    @pytest.mark.asyncio
    async def test_calls_mark_article_as_read_with_correct_page_id(self):
        """Button click calls notion.mark_article_as_read with the correct page_id."""
        article_page = make_article_page(page_id="article-page-001", title="Test Article")
        btn = MarkReadButton(article_page)

        # Mock view via the internal _view attribute (discord.py stores it there)
        mock_view = MagicMock()
        btn._view = mock_view

        interaction = make_interaction()

        with patch("app.bot.cogs.interactions.NotionService") as MockNotionService:
            mock_notion = MockNotionService.return_value
            mock_notion.mark_article_as_read = AsyncMock()

            await btn.callback(interaction)

            mock_notion.mark_article_as_read.assert_called_once_with("article-page-001")

    @pytest.mark.asyncio
    async def test_success_response_message(self):
        """On success, sends '✅ 已標記「{title}」為已讀' (ephemeral)."""
        article_page = make_article_page(title="Amazing Article")
        btn = MarkReadButton(article_page)

        mock_view = MagicMock()
        btn._view = mock_view

        interaction = make_interaction()

        with patch("app.bot.cogs.interactions.NotionService") as MockNotionService:
            mock_notion = MockNotionService.return_value
            mock_notion.mark_article_as_read = AsyncMock()

            await btn.callback(interaction)

            interaction.followup.send.assert_called_once_with(
                "✅ 已標記「Amazing Article」為已讀", ephemeral=True
            )

    @pytest.mark.asyncio
    async def test_failure_response_message(self):
        """On failure, sends '❌ 標記失敗，請稍後再試' (ephemeral)."""
        article_page = make_article_page()
        btn = MarkReadButton(article_page)

        mock_view = MagicMock()
        btn._view = mock_view

        interaction = make_interaction()

        with patch("app.bot.cogs.interactions.NotionService") as MockNotionService:
            mock_notion = MockNotionService.return_value
            mock_notion.mark_article_as_read = AsyncMock(
                side_effect=NotionServiceError("API Error")
            )

            await btn.callback(interaction)

            interaction.followup.send.assert_called_once_with("❌ 標記失敗，請稍後再試", ephemeral=True)

    @pytest.mark.asyncio
    async def test_button_disabled_after_success(self):
        """Button is disabled after successful mark."""
        article_page = make_article_page()
        btn = MarkReadButton(article_page)

        mock_view = MagicMock()
        btn._view = mock_view

        interaction = make_interaction()

        with patch("app.bot.cogs.interactions.NotionService") as MockNotionService:
            mock_notion = MockNotionService.return_value
            mock_notion.mark_article_as_read = AsyncMock()

            assert btn.disabled is False
            await btn.callback(interaction)
            assert btn.disabled is True


class TestMarkReadViewButtonCount:
    def test_view_has_correct_number_of_buttons_for_small_list(self):
        """With 3 article pages, view should have 3 buttons."""
        article_pages = [make_article_page(page_id=f"page-{i}") for i in range(3)]
        view = MarkReadView(article_pages)
        assert len(view.children) == 3

    def test_view_capped_at_25_buttons(self):
        """With 30 article pages, view should have at most 25 buttons (Discord limit)."""
        article_pages = [make_article_page(page_id=f"page-{i}") for i in range(30)]
        view = MarkReadView(article_pages)
        assert len(view.children) == 25

    def test_view_with_empty_list(self):
        """With 0 article pages, view should have 0 buttons."""
        view = MarkReadView([])
        assert len(view.children) == 0

    def test_view_with_exactly_25_articles(self):
        """With exactly 25 article pages, view should have 25 buttons."""
        article_pages = [make_article_page(page_id=f"page-{i}") for i in range(25)]
        view = MarkReadView(article_pages)
        assert len(view.children) == 25


class TestMarkReadViewTimeout:
    def test_view_timeout_is_none(self):
        """MarkReadView.timeout is None for persistence."""
        article_pages = [make_article_page()]
        view = MarkReadView(article_pages)
        assert view.timeout is None
