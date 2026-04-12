"""
Integration tests for Discord bot cogs.

Tests bot commands with mocked Discord client, service layer integration,
and error handling/logging.

Validates: Requirements 7.2, 7.4
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import discord
import pytest
from discord.ext import commands

from app.bot.cogs.news_commands import NewsCommands
from app.bot.cogs.reading_list import (
    MarkAsReadButton,
    RatingSelect,
    ReadingListCog,
)
from app.bot.cogs.subscription_commands import SubscriptionCommands
from app.core.exceptions import LLMServiceError, SupabaseServiceError
from app.schemas.article import ArticleSchema, ReadingListItem, Subscription
from app.services.llm_service import LLMService
from app.services.supabase_service import SupabaseService

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_bot():
    """Create a mock Discord bot."""
    bot = MagicMock(spec=commands.Bot)
    bot.tree = MagicMock()
    bot.tree.add_command = MagicMock()
    bot.tree.remove_command = MagicMock()
    return bot


@pytest.fixture
def mock_interaction():
    """Create a mock Discord interaction."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock()
    interaction.user.id = 123456789
    interaction.response = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    interaction.message = MagicMock()
    interaction.message.edit = AsyncMock()
    return interaction


@pytest.fixture
def mock_supabase_service():
    """Create a mock SupabaseService."""
    service = MagicMock(spec=SupabaseService)
    service.get_or_create_user = AsyncMock()
    service.get_user_subscriptions = AsyncMock()
    service.get_user_articles = AsyncMock()
    service.subscribe_to_feed = AsyncMock()
    service.unsubscribe_from_feed = AsyncMock()
    service.get_reading_list = AsyncMock()
    service.update_article_status = AsyncMock()
    service.update_article_rating = AsyncMock()
    service.get_highly_rated_articles = AsyncMock()
    service.client = MagicMock()
    return service


@pytest.fixture
def mock_llm_service():
    """Create a mock LLMService."""
    service = MagicMock(spec=LLMService)
    service.generate_reading_recommendation = AsyncMock()
    return service


# ============================================================================
# NewsCommands Integration Tests
# ============================================================================


class TestNewsCommandsIntegration:
    """Integration tests for NewsCommands cog."""

    @pytest.mark.asyncio
    async def test_news_now_with_service_layer(
        self, mock_bot, mock_interaction, mock_supabase_service
    ):
        """Test /news_now command integrates with service layer correctly."""
        # Arrange
        user_uuid = uuid4()
        feed_id = uuid4()

        mock_supabase_service.get_or_create_user.return_value = user_uuid
        mock_supabase_service.get_user_subscriptions.return_value = [
            Subscription(
                feed_id=feed_id,
                name="Test Feed",
                url="https://example.com/feed",
                category="AI",
                subscribed_at=datetime.now(UTC),
            )
        ]
        mock_supabase_service.get_user_articles.return_value = [
            ArticleSchema(
                id=uuid4(),
                feed_id=feed_id,
                feed_name="Test Feed",
                title="Test Article",
                url="https://example.com/article",
                category="AI",
                tinkering_index=5,
                ai_summary="Test summary",
                published_at=datetime.now(UTC),
            )
        ]

        cog = NewsCommands(mock_bot, mock_supabase_service)

        # Act
        with patch("app.bot.cogs.news_commands.ensure_user_registered", return_value=user_uuid):
            await cog.news_now.callback(cog, mock_interaction)

        # Assert - Verify service layer methods were called
        mock_supabase_service.get_user_subscriptions.assert_called_once_with("123456789")
        mock_supabase_service.get_user_articles.assert_called_once()

        # Verify response was sent
        mock_interaction.response.defer.assert_called_once_with(thinking=True)
        mock_interaction.followup.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_news_now_error_handling(self, mock_bot, mock_interaction, mock_supabase_service):
        """Test /news_now handles service layer errors gracefully."""
        # Arrange - Mock the ensure_user_registered function to raise an error
        with patch("app.bot.cogs.news_commands.ensure_user_registered") as mock_ensure_user:
            mock_ensure_user.side_effect = SupabaseServiceError("Database error")

            cog = NewsCommands(mock_bot, mock_supabase_service)

            # Act
            await cog.news_now.callback(cog, mock_interaction)

            # Assert - Verify error message was sent
            mock_interaction.followup.send.assert_called_once()
            call_args = mock_interaction.followup.send.call_args
            assert "❌" in call_args[0][0]
            assert call_args[1]["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_news_now_logging(self, mock_bot, mock_interaction, mock_supabase_service):
        """Test /news_now logs operations correctly."""
        # Arrange
        user_uuid = uuid4()
        mock_supabase_service.get_or_create_user.return_value = user_uuid
        mock_supabase_service.get_user_subscriptions.return_value = []

        cog = NewsCommands(mock_bot, mock_supabase_service)

        # Act
        with (
            patch("app.bot.cogs.news_commands.logger") as mock_logger,
            patch("app.bot.cogs.news_commands.ensure_user_registered", return_value=user_uuid),
        ):
            await cog.news_now.callback(cog, mock_interaction)

            # Assert - Verify logging calls
            assert mock_logger.info.call_count >= 2  # At least command trigger and result

            # Verify log contains user_id
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("user_id" in str(call) for call in log_calls)


# ============================================================================
# SubscriptionCommands Integration Tests
# ============================================================================


class TestSubscriptionCommandsIntegration:
    """Integration tests for SubscriptionCommands cog."""

    @pytest.mark.asyncio
    async def test_add_feed_with_service_layer(
        self, mock_bot, mock_interaction, mock_supabase_service
    ):
        """Test /add_feed command integrates with service layer correctly."""
        # Arrange
        user_uuid = uuid4()
        feed_id = uuid4()

        mock_supabase_service.get_or_create_user.return_value = user_uuid

        # Mock feed doesn't exist
        mock_response = MagicMock()
        mock_response.data = []
        mock_supabase_service.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Mock feed creation
        mock_create_response = MagicMock()
        mock_create_response.data = [{"id": str(feed_id)}]
        mock_supabase_service.client.table.return_value.insert.return_value.execute.return_value = (
            mock_create_response
        )

        cog = SubscriptionCommands(mock_bot, mock_supabase_service)

        # Act
        with patch(
            "app.bot.cogs.subscription_commands.ensure_user_registered", return_value=user_uuid
        ):
            await cog.add_feed.callback(
                cog, mock_interaction, "Test Feed", "https://example.com/feed", "AI"
            )

        # Assert - Verify service layer methods were called
        mock_supabase_service.subscribe_to_feed.assert_called_once_with("123456789", feed_id)

        # Verify success message
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "✅" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_feeds_with_service_layer(
        self, mock_bot, mock_interaction, mock_supabase_service
    ):
        """Test /list_feeds command integrates with service layer correctly."""
        # Arrange
        user_uuid = uuid4()
        feed_id = uuid4()

        mock_supabase_service.get_or_create_user.return_value = user_uuid
        mock_supabase_service.get_user_subscriptions.return_value = [
            Subscription(
                feed_id=feed_id,
                name="Test Feed",
                url="https://example.com/feed",
                category="AI",
                subscribed_at=datetime.now(UTC),
            )
        ]

        cog = SubscriptionCommands(mock_bot, mock_supabase_service)

        # Act
        with patch(
            "app.bot.cogs.subscription_commands.ensure_user_registered", return_value=user_uuid
        ):
            await cog.list_feeds.callback(cog, mock_interaction)

        # Assert - Verify service layer was called
        mock_supabase_service.get_user_subscriptions.assert_called_once_with("123456789")

        # Verify response contains feed info
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "Test Feed" in call_args[0][0]
        assert "AI" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_unsubscribe_feed_with_service_layer(
        self, mock_bot, mock_interaction, mock_supabase_service
    ):
        """Test /unsubscribe_feed command integrates with service layer correctly."""
        # Arrange
        user_uuid = uuid4()
        feed_id = uuid4()

        mock_supabase_service.get_or_create_user.return_value = user_uuid
        mock_supabase_service.get_user_subscriptions.return_value = [
            Subscription(
                feed_id=feed_id,
                name="Test Feed",
                url="https://example.com/feed",
                category="AI",
                subscribed_at=datetime.now(UTC),
            )
        ]

        cog = SubscriptionCommands(mock_bot, mock_supabase_service)

        # Act
        with patch(
            "app.bot.cogs.subscription_commands.ensure_user_registered", return_value=user_uuid
        ):
            await cog.unsubscribe_feed.callback(cog, mock_interaction, "Test Feed")

        # Assert - Verify service layer was called
        mock_supabase_service.unsubscribe_from_feed.assert_called_once_with("123456789", feed_id)

        # Verify success message
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "✅" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_subscription_error_handling(
        self, mock_bot, mock_interaction, mock_supabase_service
    ):
        """Test subscription commands handle errors gracefully."""
        # Arrange
        mock_supabase_service.get_or_create_user.side_effect = SupabaseServiceError(
            "Database error"
        )

        cog = SubscriptionCommands(mock_bot, mock_supabase_service)

        # Act
        with patch(
            "app.bot.cogs.subscription_commands.ensure_user_registered",
            side_effect=SupabaseServiceError("Database error"),
        ):
            await cog.add_feed.callback(
                cog, mock_interaction, "Test Feed", "https://example.com/feed", "AI"
            )

        # Assert - Verify error message
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "❌" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_subscription_logging(self, mock_bot, mock_interaction, mock_supabase_service):
        """Test subscription commands log operations correctly."""
        # Arrange
        user_uuid = uuid4()
        mock_supabase_service.get_or_create_user.return_value = user_uuid
        mock_supabase_service.get_user_subscriptions.return_value = []

        cog = SubscriptionCommands(mock_bot, mock_supabase_service)

        # Act
        with (
            patch("app.bot.cogs.subscription_commands.logger") as mock_logger,
            patch(
                "app.bot.cogs.subscription_commands.ensure_user_registered", return_value=user_uuid
            ),
        ):
            await cog.list_feeds.callback(cog, mock_interaction)

            # Assert - Verify logging
            assert mock_logger.info.call_count >= 2


# ============================================================================
# ReadingListCog Integration Tests
# ============================================================================


class TestReadingListCogIntegration:
    """Integration tests for ReadingListCog."""

    @pytest.mark.asyncio
    async def test_reading_list_view_with_service_layer(
        self, mock_bot, mock_interaction, mock_supabase_service, mock_llm_service
    ):
        """Test /reading_list view command integrates with service layer correctly."""
        # Arrange
        article_id = uuid4()
        now = datetime.now(UTC)
        mock_supabase_service.get_reading_list.return_value = [
            ReadingListItem(
                article_id=article_id,
                title="Test Article",
                url="https://example.com/article",
                category="AI",
                status="Unread",
                rating=None,
                added_at=now,
                updated_at=now,
            )
        ]

        cog = ReadingListCog(mock_bot, mock_supabase_service, mock_llm_service)

        # Act
        await cog.reading_list_group.view.callback(cog.reading_list_group, mock_interaction)

        # Assert - Verify service layer was called
        mock_supabase_service.get_reading_list.assert_called_once_with("123456789", status="Unread")

        # Verify response
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "Test Article" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_reading_list_recommend_with_service_layer(
        self, mock_bot, mock_interaction, mock_supabase_service, mock_llm_service
    ):
        """Test /reading_list recommend command integrates with both service layers."""
        # Arrange
        article_id = uuid4()
        now = datetime.now(UTC)
        mock_supabase_service.get_highly_rated_articles.return_value = [
            ReadingListItem(
                article_id=article_id,
                title="Great Article",
                url="https://example.com/article",
                category="AI",
                status="Read",
                rating=5,
                added_at=now,
                updated_at=now,
            )
        ]
        mock_llm_service.generate_reading_recommendation.return_value = (
            "Based on your reading, you might like..."
        )

        cog = ReadingListCog(mock_bot, mock_supabase_service, mock_llm_service)

        # Act
        await cog.reading_list_group.recommend.callback(cog.reading_list_group, mock_interaction)

        # Assert - Verify both service layers were called
        mock_supabase_service.get_highly_rated_articles.assert_called_once_with(
            "123456789", threshold=4
        )
        mock_llm_service.generate_reading_recommendation.assert_called_once()

        # Verify response
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "Based on your reading" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_reading_list_error_handling(
        self, mock_bot, mock_interaction, mock_supabase_service, mock_llm_service
    ):
        """Test reading list commands handle errors gracefully."""
        # Arrange
        mock_supabase_service.get_reading_list.side_effect = SupabaseServiceError("Database error")

        cog = ReadingListCog(mock_bot, mock_supabase_service, mock_llm_service)

        # Act
        await cog.reading_list_group.view.callback(cog.reading_list_group, mock_interaction)

        # Assert - Verify error message
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "❌" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_reading_list_llm_error_handling(
        self, mock_bot, mock_interaction, mock_supabase_service, mock_llm_service
    ):
        """Test reading list handles LLM service errors gracefully."""
        # Arrange
        article_id = uuid4()
        now = datetime.now(UTC)
        mock_supabase_service.get_highly_rated_articles.return_value = [
            ReadingListItem(
                article_id=article_id,
                title="Great Article",
                url="https://example.com/article",
                category="AI",
                status="Read",
                rating=5,
                added_at=now,
                updated_at=now,
            )
        ]
        mock_llm_service.generate_reading_recommendation.side_effect = LLMServiceError(
            "LLM API error"
        )

        cog = ReadingListCog(mock_bot, mock_supabase_service, mock_llm_service)

        # Act
        await cog.reading_list_group.recommend.callback(cog.reading_list_group, mock_interaction)

        # Assert - Verify error message
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "❌" in call_args[0][0]
        assert "AI 服務" in call_args[0][0] or "推薦功能" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_reading_list_logging(
        self, mock_bot, mock_interaction, mock_supabase_service, mock_llm_service
    ):
        """Test reading list commands log operations correctly."""
        # Arrange
        mock_supabase_service.get_reading_list.return_value = []

        cog = ReadingListCog(mock_bot, mock_supabase_service, mock_llm_service)

        # Act
        with patch("app.bot.cogs.reading_list.logger") as mock_logger:
            await cog.reading_list_group.view.callback(cog.reading_list_group, mock_interaction)

            # Assert - Verify logging
            assert mock_logger.info.call_count >= 2


# ============================================================================
# Interactive Components Integration Tests
# ============================================================================


class TestInteractiveComponentsIntegration:
    """Integration tests for interactive components (buttons, selects)."""

    @pytest.mark.asyncio
    async def test_mark_as_read_button_with_service_layer(
        self, mock_interaction, mock_supabase_service
    ):
        """Test MarkAsReadButton integrates with service layer correctly."""
        # Arrange
        article_id = uuid4()
        now = datetime.now(UTC)
        item = ReadingListItem(
            article_id=article_id,
            title="Test Article",
            url="https://example.com/article",
            category="AI",
            status="Unread",
            rating=None,
            added_at=now,
            updated_at=now,
        )

        button = MarkAsReadButton(item, row=1, supabase_service=mock_supabase_service)
        # Mock the view property using object.__setattr__ to bypass read-only property
        object.__setattr__(button, "_view", MagicMock())

        # Act
        await button.callback(mock_interaction)

        # Assert - Verify service layer was called
        mock_supabase_service.update_article_status.assert_called_once_with(
            "123456789", article_id, "Read"
        )

        # Verify success message
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "✅" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_rating_select_with_service_layer(self, mock_interaction, mock_supabase_service):
        """Test RatingSelect integrates with service layer correctly."""
        # Arrange
        article_id = uuid4()
        now = datetime.now(UTC)
        item = ReadingListItem(
            article_id=article_id,
            title="Test Article",
            url="https://example.com/article",
            category="AI",
            status="Unread",
            rating=None,
            added_at=now,
            updated_at=now,
        )

        select = RatingSelect(item, row=2, supabase_service=mock_supabase_service)
        # Mock the values property using object.__setattr__ to bypass read-only property
        object.__setattr__(select, "_values", ["5"])

        # Act
        await select.callback(mock_interaction)

        # Assert - Verify service layer was called
        mock_supabase_service.update_article_rating.assert_called_once_with(
            "123456789", article_id, 5
        )

        # Verify success message
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "✅" in call_args[0][0]
        assert "⭐" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_interactive_component_error_handling(
        self, mock_interaction, mock_supabase_service
    ):
        """Test interactive components handle errors gracefully."""
        # Arrange
        article_id = uuid4()
        now = datetime.now(UTC)
        item = ReadingListItem(
            article_id=article_id,
            title="Test Article",
            url="https://example.com/article",
            category="AI",
            status="Unread",
            rating=None,
            added_at=now,
            updated_at=now,
        )

        mock_supabase_service.update_article_status.side_effect = SupabaseServiceError(
            "Database error"
        )

        button = MarkAsReadButton(item, row=1, supabase_service=mock_supabase_service)
        # Mock the view property using object.__setattr__ to bypass read-only property
        object.__setattr__(button, "_view", MagicMock())

        # Act
        await button.callback(mock_interaction)

        # Assert - Verify error message
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "❌" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_interactive_component_logging(self, mock_interaction, mock_supabase_service):
        """Test interactive components log operations correctly."""
        # Arrange
        article_id = uuid4()
        now = datetime.now(UTC)
        item = ReadingListItem(
            article_id=article_id,
            title="Test Article",
            url="https://example.com/article",
            category="AI",
            status="Unread",
            rating=None,
            added_at=now,
            updated_at=now,
        )

        button = MarkAsReadButton(item, row=1, supabase_service=mock_supabase_service)
        # Mock the view property using object.__setattr__ to bypass read-only property
        object.__setattr__(button, "_view", MagicMock())

        # Act
        with patch("app.bot.cogs.reading_list.logger") as mock_logger:
            await button.callback(mock_interaction)

            # Assert - Verify logging
            assert mock_logger.info.call_count >= 2  # Button click and success
