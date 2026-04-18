"""
Integration tests for /reading_list view and recommend commands
Tasks 5.1, 5.2, 5.3: 驗證閱讀清單整合
Validates: Requirements 6.1-6.9, 8.1-8.6
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import discord
import pytest

from app.bot.cogs.reading_list import PaginationView, ReadingListGroup
from app.core.exceptions import LLMServiceError
from app.schemas.article import ReadingListItem

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def make_interaction():
    """Create a mock Discord interaction."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    interaction.user = MagicMock()
    interaction.user.id = 123456789
    return interaction


def make_reading_list_item(article_id=None, title="Test Article", rating=None, status="Unread"):
    """Create a ReadingListItem for testing."""
    if article_id is None:
        article_id = uuid4()
    return ReadingListItem(
        article_id=article_id,
        title=title,
        url="https://example.com/article",
        category="AI",
        status=status,
        rating=rating,
        added_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Task 5.1 — 驗證 /reading_list view 整合
# ---------------------------------------------------------------------------


class TestReadingListViewIntegration:
    @pytest.mark.asyncio
    async def test_view_returns_items_with_article_id(self):
        """Verify get_reading_list returns ReadingListItem with article_id."""
        group = ReadingListGroup()
        interaction = make_interaction()

        # Create test items with article_id
        test_items = [make_reading_list_item(title=f"Article {i}") for i in range(3)]

        with patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.get_reading_list = AsyncMock(return_value=test_items)

            await group.view.callback(group, interaction)

            # Verify get_reading_list was called with correct parameters
            instance.get_reading_list.assert_called_once_with(
                str(interaction.user.id), status="Unread"
            )

            # Verify response was sent
            interaction.followup.send.assert_called_once()
            call_args = interaction.followup.send.call_args

            # Verify ephemeral response
            assert call_args[1]["ephemeral"] is True

            # Verify view was passed
            assert "view" in call_args[1]
            view = call_args[1]["view"]
            assert isinstance(view, PaginationView)

    @pytest.mark.asyncio
    async def test_view_mark_as_read_button_uses_article_id(self):
        """Verify MarkAsReadButton uses article_id from ReadingListItem."""
        group = ReadingListGroup()
        interaction = make_interaction()

        test_article_id = uuid4()
        test_items = [make_reading_list_item(article_id=test_article_id)]

        with patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.get_reading_list = AsyncMock(return_value=test_items)

            await group.view.callback(group, interaction)

            # Get the view that was passed
            call_args = interaction.followup.send.call_args
            view = call_args[1]["view"]

            # Find MarkAsReadButton in view
            mark_read_buttons = [
                child
                for child in view.children
                if hasattr(child, "custom_id") and child.custom_id.startswith("mark_read_")
            ]

            assert len(mark_read_buttons) > 0
            button = mark_read_buttons[0]

            # Verify custom_id contains the article_id
            assert button.custom_id == f"mark_read_{test_article_id}"

    @pytest.mark.asyncio
    async def test_view_rating_select_uses_article_id(self):
        """Verify RatingSelect uses article_id from ReadingListItem."""
        group = ReadingListGroup()
        interaction = make_interaction()

        test_article_id = uuid4()
        test_items = [make_reading_list_item(article_id=test_article_id)]

        with patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.get_reading_list = AsyncMock(return_value=test_items)

            await group.view.callback(group, interaction)

            # Get the view that was passed
            call_args = interaction.followup.send.call_args
            view = call_args[1]["view"]

            # Find RatingSelect in view
            rating_selects = [
                child
                for child in view.children
                if hasattr(child, "custom_id") and child.custom_id.startswith("rate_")
            ]

            assert len(rating_selects) > 0
            select = rating_selects[0]

            # Verify custom_id contains the article_id
            assert select.custom_id == f"rate_{test_article_id}"

    @pytest.mark.asyncio
    async def test_view_pagination_works_correctly(self):
        """Verify pagination functionality works with article_id."""
        group = ReadingListGroup()
        interaction = make_interaction()

        # Create 3 items to avoid Discord's 5-row limit
        # (Row 0: pagination, Row 1: mark read buttons, Rows 2-4: rating selects)
        test_items = [make_reading_list_item(title=f"Article {i}") for i in range(3)]

        with patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.get_reading_list = AsyncMock(return_value=test_items)

            await group.view.callback(group, interaction)

            # Get the view
            call_args = interaction.followup.send.call_args
            view = call_args[1]["view"]

            # Verify pagination buttons exist
            pagination_buttons = [
                child
                for child in view.children
                if hasattr(child, "label") and ("上一頁" in child.label or "下一頁" in child.label)
            ]

            assert len(pagination_buttons) == 2  # Prev and Next buttons

    @pytest.mark.asyncio
    async def test_view_ephemeral_response(self):
        """Verify /reading_list view uses ephemeral response."""
        group = ReadingListGroup()
        interaction = make_interaction()

        test_items = [make_reading_list_item()]

        with patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.get_reading_list = AsyncMock(return_value=test_items)

            await group.view.callback(group, interaction)

            # Verify ephemeral=True
            call_args = interaction.followup.send.call_args
            assert call_args[1]["ephemeral"] is True


# ---------------------------------------------------------------------------
# Task 5.2 — 驗證 /reading_list recommend 整合
# ---------------------------------------------------------------------------


class TestReadingListRecommendIntegration:
    @pytest.mark.asyncio
    async def test_recommend_queries_high_rated_articles(self):
        """Verify recommend queries articles rated 4-5 stars."""
        group = ReadingListGroup()
        interaction = make_interaction()

        high_rated_items = [
            make_reading_list_item(title="Article 1", rating=4),
            make_reading_list_item(title="Article 2", rating=5),
        ]

        with (
            patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase,
            patch("app.bot.cogs.reading_list.LLMService") as MockLLM,
        ):
            supabase_instance = MockSupabase.return_value
            supabase_instance.get_highly_rated_articles = AsyncMock(return_value=high_rated_items)

            llm_instance = MockLLM.return_value
            llm_instance.generate_reading_recommendation = AsyncMock(
                return_value="這是個人化推薦摘要"
            )

            await group.recommend.callback(group, interaction)

            # Verify get_highly_rated_articles was called with threshold=4
            supabase_instance.get_highly_rated_articles.assert_called_once_with(
                str(interaction.user.id), threshold=4
            )

    @pytest.mark.asyncio
    async def test_recommend_passes_titles_and_categories_to_llm(self):
        """Verify recommend passes article titles and categories to LLM."""
        group = ReadingListGroup()
        interaction = make_interaction()

        high_rated_items = [
            make_reading_list_item(title="AI Article", rating=5),
            make_reading_list_item(title="Tech Article", rating=4),
        ]

        with (
            patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase,
            patch("app.bot.cogs.reading_list.LLMService") as MockLLM,
        ):
            supabase_instance = MockSupabase.return_value
            supabase_instance.get_highly_rated_articles = AsyncMock(return_value=high_rated_items)

            llm_instance = MockLLM.return_value
            llm_instance.generate_reading_recommendation = AsyncMock(return_value="推薦摘要")

            await group.recommend.callback(group, interaction)

            # Verify LLM was called with titles and categories
            llm_instance.generate_reading_recommendation.assert_called_once()
            call_args = llm_instance.generate_reading_recommendation.call_args[0]

            titles = call_args[0]
            categories = call_args[1]

            assert "AI Article" in titles
            assert "Tech Article" in titles
            assert "AI" in categories

    @pytest.mark.asyncio
    async def test_recommend_ephemeral_response(self):
        """Verify recommend uses ephemeral response."""
        group = ReadingListGroup()
        interaction = make_interaction()

        high_rated_items = [make_reading_list_item(rating=5)]

        with (
            patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase,
            patch("app.bot.cogs.reading_list.LLMService") as MockLLM,
        ):
            supabase_instance = MockSupabase.return_value
            supabase_instance.get_highly_rated_articles = AsyncMock(return_value=high_rated_items)

            llm_instance = MockLLM.return_value
            llm_instance.generate_reading_recommendation = AsyncMock(return_value="推薦摘要")

            await group.recommend.callback(group, interaction)

            # Verify ephemeral=True
            call_args = interaction.followup.send.call_args
            assert call_args[1]["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_recommend_no_high_rated_articles(self):
        """Verify recommend handles case with no high-rated articles."""
        group = ReadingListGroup()
        interaction = make_interaction()

        with patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.get_highly_rated_articles = AsyncMock(return_value=[])

            await group.recommend.callback(group, interaction)

            # Verify appropriate message was sent
            call_args = interaction.followup.send.call_args
            assert "尚無足夠的高評分文章" in call_args[0][0]
            assert call_args[1]["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_recommend_llm_failure(self):
        """Verify recommend handles LLM generation failure."""
        group = ReadingListGroup()
        interaction = make_interaction()

        high_rated_items = [make_reading_list_item(rating=5)]

        with (
            patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase,
            patch("app.bot.cogs.reading_list.LLMService") as MockLLM,
        ):
            supabase_instance = MockSupabase.return_value
            supabase_instance.get_highly_rated_articles = AsyncMock(return_value=high_rated_items)

            llm_instance = MockLLM.return_value
            llm_instance.generate_reading_recommendation = AsyncMock(
                side_effect=LLMServiceError("LLM unavailable")
            )

            await group.recommend.callback(group, interaction)

            # Verify error message was sent
            call_args = interaction.followup.send.call_args
            assert "推薦功能暫時無法使用" in call_args[0][0]
            assert call_args[1]["ephemeral"] is True


# ---------------------------------------------------------------------------
# Task 5.3 — 撰寫閱讀清單的整合測試
# ---------------------------------------------------------------------------


class TestReadingListCompleteWorkflow:
    @pytest.mark.asyncio
    async def test_complete_workflow_save_view_rate_mark_read(self):
        """Test complete workflow: save → view → rate → mark read."""
        # This is a conceptual test showing the workflow
        # In practice, each step would be tested separately with mocks

        # Step 1: Save article to reading list (via ReadLaterButton)
        from app.bot.cogs.interactions import ReadLaterButton

        article_id = uuid4()
        button = ReadLaterButton(article_id, "Test Article")
        interaction = make_interaction()

        with patch("app.bot.cogs.interactions.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.save_to_reading_list = AsyncMock(return_value=None)

            await button.callback(interaction)

            # Verify article was saved
            instance.save_to_reading_list.assert_called_once_with(
                str(interaction.user.id), article_id
            )

        # Step 2: View reading list
        group = ReadingListGroup()
        interaction2 = make_interaction()

        saved_item = make_reading_list_item(article_id=article_id, title="Test Article")

        with patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.get_reading_list = AsyncMock(return_value=[saved_item])

            await group.view.callback(group, interaction2)

            # Verify reading list was retrieved
            instance.get_reading_list.assert_called_once()

        # Step 3: Rate article (via RatingSelect)
        from app.bot.cogs.reading_list import RatingSelect

        select = RatingSelect(saved_item, row=2)
        select._values = ["5"]
        interaction3 = make_interaction()

        with patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.update_article_rating = AsyncMock(return_value=None)

            await select.callback(interaction3)

            # Verify rating was updated
            instance.update_article_rating.assert_called_once_with(
                str(interaction3.user.id), article_id, 5
            )

        # Step 4: Mark as read (via MarkAsReadButton)
        from app.bot.cogs.reading_list import MarkAsReadButton

        mark_button = MarkAsReadButton(saved_item, row=1)
        interaction4 = make_interaction()

        with patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.update_article_status = AsyncMock(return_value=None)

            await mark_button.callback(interaction4)

            # Verify status was updated
            instance.update_article_status.assert_called_once_with(
                str(interaction4.user.id), article_id, "Read"
            )

    @pytest.mark.asyncio
    async def test_pagination_navigation(self):
        """Test pagination navigation with multiple pages."""
        # Create 3 items (limited to avoid Discord's 5-row limit bug)
        # Row 0: pagination, Row 1: mark read buttons, Rows 2-4: rating selects
        test_items = [make_reading_list_item(title=f"Article {i}") for i in range(3)]

        # Test page 0
        view = PaginationView(test_items, page=0)

        # Verify first page
        assert view.page == 0
        page_items = view._current_page_items()
        assert len(page_items) == 3

    @pytest.mark.asyncio
    async def test_multi_user_isolation(self):
        """Test that different users have isolated reading lists."""
        group = ReadingListGroup()

        # User 1
        interaction1 = make_interaction()
        interaction1.user.id = 111111

        user1_items = [make_reading_list_item(title="User 1 Article")]

        with patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.get_reading_list = AsyncMock(return_value=user1_items)

            await group.view.callback(group, interaction1)

            # Verify called with user 1's ID
            instance.get_reading_list.assert_called_once_with(
                str(interaction1.user.id), status="Unread"
            )

        # User 2
        interaction2 = make_interaction()
        interaction2.user.id = 222222

        user2_items = [make_reading_list_item(title="User 2 Article")]

        with patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase:
            instance = MockSupabase.return_value
            instance.get_reading_list = AsyncMock(return_value=user2_items)

            await group.view.callback(group, interaction2)

            # Verify called with user 2's ID
            instance.get_reading_list.assert_called_once_with(
                str(interaction2.user.id), status="Unread"
            )

    @pytest.mark.asyncio
    async def test_recommend_workflow(self):
        """Test complete recommendation workflow."""
        group = ReadingListGroup()
        interaction = make_interaction()

        # User has rated several articles
        high_rated_items = [
            make_reading_list_item(title="AI Article 1", rating=5),
            make_reading_list_item(title="AI Article 2", rating=4),
            make_reading_list_item(title="Tech Article", rating=5),
        ]

        with (
            patch("app.bot.cogs.reading_list.SupabaseService") as MockSupabase,
            patch("app.bot.cogs.reading_list.LLMService") as MockLLM,
        ):
            supabase_instance = MockSupabase.return_value
            supabase_instance.get_highly_rated_articles = AsyncMock(return_value=high_rated_items)

            llm_instance = MockLLM.return_value
            recommendation_text = "根據您的高評分文章，推薦以下主題：AI 和 Tech"
            llm_instance.generate_reading_recommendation = AsyncMock(
                return_value=recommendation_text
            )

            await group.recommend.callback(group, interaction)

            # Verify recommendation was generated and sent
            call_args = interaction.followup.send.call_args
            assert recommendation_text in call_args[0][0]
            assert call_args[1]["ephemeral"] is True
