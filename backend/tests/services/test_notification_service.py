"""
Unit tests for NotificationService

Tests the core functionality of the NotificationService including:
- Discord DM sending
- Email sending with HTML and text formats
- Multi-channel notification orchestration
- Retry logic and error handling
- Integration with LockManager for duplicate prevention
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import discord
import pytest

from app.schemas.article import ArticleSchema
from app.services.notification_service import (
    EmailContent,
    NotificationChannel,
    NotificationResult,
    NotificationService,
)


@pytest.fixture
def mock_bot():
    """Create a mock Discord bot."""
    bot = AsyncMock(spec=discord.Client)
    mock_user = AsyncMock()
    mock_user.send = AsyncMock()
    bot.fetch_user.return_value = mock_user
    return bot


@pytest.fixture
def mock_supabase_service():
    """Create a mock Supabase service."""
    service = AsyncMock()
    service.client = Mock()
    return service


@pytest.fixture
def mock_lock_manager():
    """Create a mock LockManager."""
    manager = AsyncMock()
    mock_lock = Mock()
    mock_lock.id = uuid4()
    manager.acquire_notification_lock.return_value = mock_lock
    manager.release_lock = AsyncMock()
    return manager


@pytest.fixture
def notification_service(mock_bot, mock_supabase_service, mock_lock_manager):
    """Create a NotificationService instance with mock dependencies."""
    return NotificationService(
        bot=mock_bot,
        supabase_service=mock_supabase_service,
        lock_manager=mock_lock_manager,
        smtp_host="test.smtp.com",
        smtp_port=587,
        smtp_username="test@example.com",
        smtp_password="password",
        from_email="noreply@test.com",
    )


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": str(uuid4()),
        "discord_id": "123456789",
        "email": "test@example.com",
        "dm_notifications_enabled": True,
        "email_notifications_enabled": True,
    }


@pytest.fixture
def sample_articles():
    """Sample articles for testing."""
    return [
        ArticleSchema(
            id=uuid4(),
            title="Test Article 1",
            url="https://example.com/1",
            feed_id=uuid4(),
            feed_name="Test Feed 1",
            category="Python",
            tinkering_index=4,
        ),
        ArticleSchema(
            id=uuid4(),
            title="Test Article 2",
            url="https://example.com/2",
            feed_id=uuid4(),
            feed_name="Test Feed 2",
            category="JavaScript",
            tinkering_index=3,
        ),
    ]


class TestNotificationService:
    """Test cases for NotificationService"""

    @pytest.mark.asyncio
    async def test_send_discord_dm_success(self, notification_service, mock_bot, sample_user_data):
        """Test successful Discord DM sending."""
        # Mock user data retrieval
        notification_service._get_user_data = AsyncMock(return_value=sample_user_data)

        user_id = uuid4()
        message = "Test message"

        result = await notification_service.send_discord_dm(user_id, message)

        assert result is True
        mock_bot.fetch_user.assert_called_once_with(123456789)
        mock_bot.fetch_user.return_value.send.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_discord_dm_user_not_found(self, notification_service):
        """Test Discord DM sending when user not found."""
        # Mock user not found
        notification_service._get_user_data = AsyncMock(return_value=None)

        user_id = uuid4()
        message = "Test message"

        result = await notification_service.send_discord_dm(user_id, message)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_discord_dm_invalid_discord_id(self, notification_service, sample_user_data):
        """Test Discord DM sending with invalid Discord ID."""
        # Mock user data with invalid Discord ID
        invalid_user_data = sample_user_data.copy()
        invalid_user_data["discord_id"] = "invalid_id"
        notification_service._get_user_data = AsyncMock(return_value=invalid_user_data)

        user_id = uuid4()
        message = "Test message"

        result = await notification_service.send_discord_dm(user_id, message)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_discord_dm_forbidden(
        self, notification_service, mock_bot, sample_user_data
    ):
        """Test Discord DM sending when user has DMs disabled."""
        # Mock user data retrieval
        notification_service._get_user_data = AsyncMock(return_value=sample_user_data)

        # Mock Discord Forbidden exception
        mock_bot.fetch_user.return_value.send.side_effect = discord.Forbidden(
            Mock(), "Cannot send messages to this user"
        )

        user_id = uuid4()
        message = "Test message"

        result = await notification_service.send_discord_dm(user_id, message)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_email_success(self, notification_service, sample_user_data):
        """Test successful email sending."""
        # Mock user data retrieval
        notification_service._get_user_data = AsyncMock(return_value=sample_user_data)

        # Mock SMTP sending
        with patch.object(notification_service, "_send_smtp_email", new_callable=AsyncMock):
            user_id = uuid4()
            subject = "Test Subject"
            content = EmailContent(html="<h1>Test HTML</h1>", text="Test Text")

            result = await notification_service.send_email(user_id, subject, content)

            assert result is True

    @pytest.mark.asyncio
    async def test_send_email_user_not_found(self, notification_service):
        """Test email sending when user not found."""
        # Mock user not found
        notification_service._get_user_data = AsyncMock(return_value=None)

        user_id = uuid4()
        subject = "Test Subject"
        content = EmailContent(html="<h1>Test</h1>", text="Test")

        result = await notification_service.send_email(user_id, subject, content)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_email_no_email_address(self, notification_service):
        """Test email sending when user has no email address."""
        # Mock user data without email
        user_data = {"id": str(uuid4()), "discord_id": "123456789"}
        notification_service._get_user_data = AsyncMock(return_value=user_data)

        user_id = uuid4()
        subject = "Test Subject"
        content = EmailContent(html="<h1>Test</h1>", text="Test")

        result = await notification_service.send_email(user_id, subject, content)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_notification_multi_channel_success(
        self, notification_service, mock_lock_manager, sample_user_data, sample_articles
    ):
        """Test successful multi-channel notification sending."""
        # Mock user data retrieval
        notification_service._get_user_data = AsyncMock(return_value=sample_user_data)

        # Mock Discord DM sending
        notification_service._send_discord_dm = AsyncMock(
            return_value=NotificationResult(True, "discord_dm")
        )

        # Mock email sending
        notification_service._send_email_notification = AsyncMock(
            return_value=NotificationResult(True, "email")
        )

        user_id = uuid4()
        channels = [NotificationChannel("discord_dm", True), NotificationChannel("email", True)]

        results = await notification_service.send_notification(
            user_id=user_id,
            channels=channels,
            subject="Test Notification",
            articles=sample_articles,
        )

        assert len(results) == 2
        assert all(result.success for result in results)

        # Verify lock was acquired and released
        mock_lock_manager.acquire_notification_lock.assert_called_once()
        mock_lock_manager.release_lock.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_lock_already_exists(
        self, notification_service, mock_lock_manager, sample_user_data
    ):
        """Test notification sending when lock already exists."""
        # Mock user data retrieval
        notification_service._get_user_data = AsyncMock(return_value=sample_user_data)

        # Mock lock already exists
        mock_lock_manager.acquire_notification_lock.return_value = None

        user_id = uuid4()
        channels = [NotificationChannel("discord_dm", True)]

        results = await notification_service.send_notification(
            user_id=user_id, channels=channels, subject="Test Notification"
        )

        assert len(results) == 1
        assert not results[0].success
        assert "already processed" in results[0].error

    @pytest.mark.asyncio
    async def test_send_notification_partial_failure(
        self, notification_service, mock_lock_manager, sample_user_data
    ):
        """Test notification sending with partial channel failure."""
        # Mock user data retrieval
        notification_service._get_user_data = AsyncMock(return_value=sample_user_data)

        # Mock Discord DM success
        notification_service._send_discord_dm = AsyncMock(
            return_value=NotificationResult(True, "discord_dm")
        )

        # Mock email failure
        notification_service._send_email_notification = AsyncMock(
            return_value=NotificationResult(False, "email", "SMTP error")
        )

        user_id = uuid4()
        channels = [NotificationChannel("discord_dm", True), NotificationChannel("email", True)]

        results = await notification_service.send_notification(
            user_id=user_id, channels=channels, subject="Test Notification"
        )

        assert len(results) == 2
        assert results[0].success  # Discord DM succeeded
        assert not results[1].success  # Email failed

        # Verify lock was released as completed (since one channel succeeded)
        mock_lock_manager.release_lock.assert_called_once()
        args, kwargs = mock_lock_manager.release_lock.call_args
        assert args[1] == "completed"

    @pytest.mark.asyncio
    async def test_send_notification_all_channels_disabled(
        self, notification_service, mock_lock_manager, sample_user_data
    ):
        """Test notification sending when all channels are disabled."""
        # Mock user data retrieval
        notification_service._get_user_data = AsyncMock(return_value=sample_user_data)

        user_id = uuid4()
        channels = [NotificationChannel("discord_dm", False), NotificationChannel("email", False)]

        results = await notification_service.send_notification(
            user_id=user_id, channels=channels, subject="Test Notification"
        )

        assert len(results) == 0

        # Verify lock was still acquired and released
        mock_lock_manager.acquire_notification_lock.assert_called_once()
        mock_lock_manager.release_lock.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_digest_embed(self, notification_service, sample_articles):
        """Test Discord embed creation for article digest."""
        embed = notification_service._create_digest_embed(sample_articles, "Weekly Digest")

        assert embed.title == "📰 Weekly Digest"
        assert "2 篇技術文章" in embed.description
        assert len(embed.fields) >= 1  # Should have at least one category field

        # Check that articles are grouped by category
        field_names = [field.name for field in embed.fields]
        assert any("Python" in name for name in field_names)
        assert any("JavaScript" in name for name in field_names)

    @pytest.mark.asyncio
    async def test_create_email_content(self, notification_service, sample_articles):
        """Test email content creation with HTML and text formats."""
        content = notification_service._create_email_content(sample_articles, "Weekly Digest")

        # Check HTML content
        assert "Weekly Digest" in content.html
        assert "Test Article 1" in content.html
        assert "Test Article 2" in content.html
        assert "https://example.com/1" in content.html
        assert "https://example.com/2" in content.html

        # Check text content
        assert "Weekly Digest" in content.text
        assert "Test Article 1" in content.text
        assert "Test Article 2" in content.text
        assert "https://example.com/1" in content.text
        assert "https://example.com/2" in content.text

    @pytest.mark.asyncio
    async def test_retry_logic_discord_dm(self, notification_service, mock_bot, sample_user_data):
        """Test retry logic for Discord DM failures."""
        # Mock user data retrieval
        notification_service._get_user_data = AsyncMock(return_value=sample_user_data)

        # Mock Discord HTTP exception that should trigger retry
        mock_bot.fetch_user.return_value.send.side_effect = [
            discord.HTTPException(Mock(), "Rate limited"),
            discord.HTTPException(Mock(), "Server error"),
            None,  # Success on third attempt
        ]

        user_id = uuid4()
        message = "Test message"

        result = await notification_service.send_discord_dm(user_id, message)

        assert result is True
        # Should have been called 3 times due to retries
        assert mock_bot.fetch_user.return_value.send.call_count == 3

    @pytest.mark.asyncio
    async def test_email_content_formats(self, notification_service):
        """Test that email content includes both HTML and text formats."""
        articles = [
            ArticleSchema(
                id=uuid4(),
                title="HTML & Text Test",
                url="https://example.com/test",
                feed_id=uuid4(),
                feed_name="Test Feed",
                category="Testing",
                tinkering_index=5,
            )
        ]

        content = notification_service._create_email_content(articles, "Format Test")

        # HTML should contain HTML tags
        assert "<html>" in content.html
        assert "<h1>" in content.html
        assert "<div" in content.html
        assert "href=" in content.html

        # Text should not contain HTML tags
        assert "<html>" not in content.text
        assert "<h1>" not in content.text
        assert "<div" not in content.text
        assert "href=" not in content.text

        # Both should contain the article title and URL
        assert "HTML & Text Test" in content.html
        assert "HTML & Text Test" in content.text
        assert "https://example.com/test" in content.html
        assert "https://example.com/test" in content.text

    @pytest.mark.asyncio
    async def test_notification_channel_configuration(self, notification_service):
        """Test NotificationChannel configuration."""
        # Test enabled channel
        enabled_channel = NotificationChannel("discord_dm", True)
        assert enabled_channel.type == "discord_dm"
        assert enabled_channel.enabled is True

        # Test disabled channel
        disabled_channel = NotificationChannel("email", False)
        assert disabled_channel.type == "email"
        assert disabled_channel.enabled is False

    @pytest.mark.asyncio
    async def test_notification_result_structure(self, notification_service):
        """Test NotificationResult structure."""
        # Test successful result
        success_result = NotificationResult(True, "discord_dm")
        assert success_result.success is True
        assert success_result.channel == "discord_dm"
        assert success_result.error is None

        # Test failed result with error
        error_result = NotificationResult(False, "email", "SMTP connection failed")
        assert error_result.success is False
        assert error_result.channel == "email"
        assert error_result.error == "SMTP connection failed"
