"""
Property-based test for Multi-Channel Notification Delivery
Task 5.2

This module tests Property 7: Multi-Channel Notification Delivery
For any enabled notification channel (Discord DM or Email), the system SHALL deliver
notifications to the correct recipient address, provide both HTML and text formats
for emails, implement retry logic for failures, and maintain delivery logs.

**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 10.6**
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import discord
from hypothesis import HealthCheck, given
from hypothesis import settings as hypothesis_settings
from hypothesis import strategies as st

from app.schemas.article import ArticleSchema
from app.services.notification_service import (
    NotificationChannel,
    NotificationService,
)

# Test data generators
valid_user_ids = st.builds(uuid4)
valid_discord_ids = st.integers(min_value=100000000000000000, max_value=999999999999999999).map(str)
valid_emails = st.builds(
    lambda name, domain: f"{name}@{domain}.com",
    st.text(min_size=3, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
    st.text(min_size=3, max_size=15, alphabet="abcdefghijklmnopqrstuvwxyz"),
)

# Channel configurations
discord_channel_enabled = st.builds(NotificationChannel, st.just("discord_dm"), st.just(True))
discord_channel_disabled = st.builds(NotificationChannel, st.just("discord_dm"), st.just(False))
email_channel_enabled = st.builds(NotificationChannel, st.just("email"), st.just(True))
email_channel_disabled = st.builds(NotificationChannel, st.just("email"), st.just(False))

single_channel_configs = st.one_of(
    st.lists(discord_channel_enabled, min_size=1, max_size=1),
    st.lists(email_channel_enabled, min_size=1, max_size=1),
)

multi_channel_configs = st.lists(
    st.one_of(discord_channel_enabled, email_channel_enabled), min_size=2, max_size=2
)

mixed_channel_configs = st.lists(
    st.one_of(
        discord_channel_enabled,
        discord_channel_disabled,
        email_channel_enabled,
        email_channel_disabled,
    ),
    min_size=1,
    max_size=4,
)

# Article data for notifications
sample_articles = st.lists(
    st.builds(
        ArticleSchema,
        id=st.builds(uuid4),
        title=st.text(min_size=10, max_size=100),
        url=st.builds(lambda: f"https://example.com/article/{uuid4()}"),
        feed_id=st.builds(uuid4),
        feed_name=st.text(min_size=5, max_size=30),
        category=st.sampled_from(["AI", "Backend", "Frontend", "DevOps", "Mobile"]),
        tinkering_index=st.integers(min_value=1, max_value=5),
        ai_summary=st.text(min_size=50, max_size=200),
    ),
    min_size=1,
    max_size=10,
)

notification_subjects = st.text(min_size=5, max_size=100)
notification_types = st.sampled_from(["weekly_digest", "daily_digest", "immediate"])


def create_mock_notification_service():
    """Create a NotificationService with mocked dependencies."""
    mock_bot = Mock(spec=discord.Client)
    mock_supabase = Mock()
    mock_lock_manager = Mock()

    service = NotificationService(
        bot=mock_bot,
        supabase_service=mock_supabase,
        lock_manager=mock_lock_manager,
        smtp_host="test.smtp.com",
        smtp_port=587,
        smtp_username="test@example.com",
        smtp_password="password",
        from_email="noreply@technews.com",
    )

    return service, mock_bot, mock_supabase, mock_lock_manager


def create_mock_user_data(
    user_id: UUID,
    discord_id: str = None,
    email: str = None,
    dm_enabled: bool = True,
    email_enabled: bool = False,
):
    """Create mock user data for testing."""
    return {
        "id": str(user_id),
        "discord_id": discord_id,
        "email": email,
        "dm_notifications_enabled": dm_enabled,
        "email_notifications_enabled": email_enabled,
    }


# Feature: personalized-notification-frequency, Property 7: Multi-Channel Notification Delivery (Discord DM)
@hypothesis_settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(
    user_id=valid_user_ids,
    discord_id=valid_discord_ids,
    subject=notification_subjects,
    articles=sample_articles,
    notification_type=notification_types,
)
def test_property_7_discord_dm_delivery_to_correct_recipient(
    user_id, discord_id, subject, articles, notification_type
):
    """
    **Validates: Requirements 9.1, 9.2, 9.3**

    Property 7: For any enabled Discord DM channel, the system SHALL deliver
    notifications to the correct Discord user ID.
    """
    service, mock_bot, mock_supabase, mock_lock_manager = create_mock_notification_service()

    # Setup user data
    user_data = create_mock_user_data(user_id, discord_id=discord_id, dm_enabled=True)

    # Mock database response
    mock_supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        user_data
    ]

    # Mock lock manager
    mock_lock = Mock()
    mock_lock.id = "test-lock-id"
    mock_lock_manager.acquire_notification_lock = AsyncMock(return_value=mock_lock)
    mock_lock_manager.release_lock = AsyncMock()

    # Mock Discord bot
    mock_user = Mock()
    mock_user.send = AsyncMock()
    mock_bot.fetch_user = AsyncMock(return_value=mock_user)

    # Test notification delivery
    channels = [NotificationChannel("discord_dm", True)]

    async def run_test():
        results = await service.send_notification(
            user_id=user_id,
            channels=channels,
            subject=subject,
            articles=articles,
            notification_type=notification_type,
        )
        return results

    results = asyncio.run(run_test())

    # Verify Discord user was fetched with correct ID
    mock_bot.fetch_user.assert_called_once_with(int(discord_id))

    # Verify message was sent to the correct user
    mock_user.send.assert_called_once()

    # Verify successful result
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].channel == "discord_dm"

    # Verify lock was acquired and released
    mock_lock_manager.acquire_notification_lock.assert_called_once()
    mock_lock_manager.release_lock.assert_called_once_with("test-lock-id", "completed")


# Feature: personalized-notification-frequency, Property 7: Multi-Channel Notification Delivery (Email)
@hypothesis_settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(
    user_id=valid_user_ids,
    email=valid_emails,
    subject=notification_subjects,
    articles=sample_articles,
    notification_type=notification_types,
)
def test_property_7_email_delivery_to_correct_recipient(
    user_id, email, subject, articles, notification_type
):
    """
    **Validates: Requirements 9.1, 9.3, 9.4**

    Property 7: For any enabled email channel, the system SHALL deliver
    notifications to the correct email address with both HTML and text formats.
    """
    service, mock_bot, mock_supabase, mock_lock_manager = create_mock_notification_service()

    # Setup user data
    user_data = create_mock_user_data(user_id, email=email, email_enabled=True)

    # Mock database response
    mock_supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        user_data
    ]

    # Mock lock manager
    mock_lock = Mock()
    mock_lock.id = "test-lock-id"
    mock_lock_manager.acquire_notification_lock = AsyncMock(return_value=mock_lock)
    mock_lock_manager.release_lock = AsyncMock()

    # Mock SMTP sending
    with patch.object(service, "_send_smtp_email", new_callable=AsyncMock) as mock_smtp:
        channels = [NotificationChannel("email", True)]

        async def run_test():
            results = await service.send_notification(
                user_id=user_id,
                channels=channels,
                subject=subject,
                articles=articles,
                notification_type=notification_type,
            )
            return results

        results = asyncio.run(run_test())

        # Verify SMTP was called
        mock_smtp.assert_called_once()

        # Get the email message that was sent
        sent_message = mock_smtp.call_args[0][0]

        # Verify correct recipient
        assert sent_message["To"] == email
        assert sent_message["From"] == service.from_email
        assert sent_message["Subject"] == subject

        # Verify both HTML and text parts are present
        parts = sent_message.get_payload()
        assert len(parts) == 2

        # Check for text and HTML parts
        text_part = parts[0]
        html_part = parts[1]

        assert text_part.get_content_type() == "text/plain"
        assert html_part.get_content_type() == "text/html"

        # Verify content contains article information
        text_content = text_part.get_payload(decode=True).decode("utf-8")
        html_content = html_part.get_payload(decode=True).decode("utf-8")

        # Should contain article titles
        for article in articles[:3]:  # Check first few articles
            assert article.title in text_content
            assert article.title in html_content

        # Verify successful result
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].channel == "email"


# Feature: personalized-notification-frequency, Property 7: Multi-Channel Notification Delivery (Multi-Channel)
@hypothesis_settings(
    max_examples=30,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(
    user_id=valid_user_ids,
    discord_id=valid_discord_ids,
    email=valid_emails,
    subject=notification_subjects,
    articles=sample_articles,
)
def test_property_7_multi_channel_delivery_to_all_enabled_channels(
    user_id, discord_id, email, subject, articles
):
    """
    **Validates: Requirements 9.1, 9.2, 9.3, 9.4**

    Property 7: For any combination of enabled channels, the system SHALL deliver
    notifications to all enabled channels with correct recipient addresses.
    """
    service, mock_bot, mock_supabase, mock_lock_manager = create_mock_notification_service()

    # Setup user data with both channels enabled
    user_data = create_mock_user_data(
        user_id, discord_id=discord_id, email=email, dm_enabled=True, email_enabled=True
    )

    # Mock database response
    mock_supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        user_data
    ]

    # Mock lock manager
    mock_lock = Mock()
    mock_lock.id = "test-lock-id"
    mock_lock_manager.acquire_notification_lock = AsyncMock(return_value=mock_lock)
    mock_lock_manager.release_lock = AsyncMock()

    # Mock Discord bot
    mock_user = Mock()
    mock_user.send = AsyncMock()
    mock_bot.fetch_user = AsyncMock(return_value=mock_user)

    # Mock SMTP sending
    with patch.object(service, "_send_smtp_email", new_callable=AsyncMock) as mock_smtp:
        channels = [NotificationChannel("discord_dm", True), NotificationChannel("email", True)]

        async def run_test():
            results = await service.send_notification(
                user_id=user_id,
                channels=channels,
                subject=subject,
                articles=articles,
                notification_type="weekly_digest",
            )
            return results

        results = asyncio.run(run_test())

        # Verify both channels were attempted
        assert len(results) == 2

        # Check Discord delivery
        discord_result = next(r for r in results if r.channel == "discord_dm")
        assert discord_result.success is True
        mock_bot.fetch_user.assert_called_once_with(int(discord_id))
        mock_user.send.assert_called_once()

        # Check email delivery
        email_result = next(r for r in results if r.channel == "email")
        assert email_result.success is True
        mock_smtp.assert_called_once()

        sent_message = mock_smtp.call_args[0][0]
        assert sent_message["To"] == email


# Feature: personalized-notification-frequency, Property 7: Multi-Channel Notification Delivery (Retry Logic)
@hypothesis_settings(
    max_examples=30,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(user_id=valid_user_ids, discord_id=valid_discord_ids, subject=notification_subjects)
def test_property_7_retry_logic_for_failed_deliveries(user_id, discord_id, subject):
    """
    **Validates: Requirements 9.5**

    Property 7: For any delivery failure, the system SHALL implement retry logic
    with exponential backoff.
    """
    service, mock_bot, mock_supabase, mock_lock_manager = create_mock_notification_service()

    # Setup user data
    user_data = create_mock_user_data(user_id, discord_id=discord_id, dm_enabled=True)

    # Mock database response
    mock_supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        user_data
    ]

    # Mock lock manager
    mock_lock = Mock()
    mock_lock.id = "test-lock-id"
    mock_lock_manager.acquire_notification_lock = AsyncMock(return_value=mock_lock)
    mock_lock_manager.release_lock = AsyncMock()

    # Mock Discord bot to fail first two attempts, succeed on third
    mock_user = Mock()

    # Use a simple counter to track calls and fail appropriately
    call_count = [0]  # Use list to make it mutable in nested function

    async def mock_send(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] <= 2:
            raise discord.HTTPException(Mock(), "Rate limited")
        return None

    mock_user.send = mock_send
    mock_bot.fetch_user = AsyncMock(return_value=mock_user)

    channels = [NotificationChannel("discord_dm", True)]

    async def run_test():
        results = await service.send_notification(
            user_id=user_id,
            channels=channels,
            subject=subject,
            articles=[],
            notification_type="test",
        )
        return results

    results = asyncio.run(run_test())

    # Verify retry attempts were made (3 total calls due to @retry decorator)
    assert call_count[0] == 3

    # Verify final success
    assert len(results) == 1
    assert results[0].success is True
    assert results[0].channel == "discord_dm"


# Feature: personalized-notification-frequency, Property 7: Multi-Channel Notification Delivery (Disabled Channels)
@hypothesis_settings(
    max_examples=30,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(
    user_id=valid_user_ids,
    discord_id=valid_discord_ids,
    email=valid_emails,
    channels=mixed_channel_configs,
)
def test_property_7_skips_disabled_channels(user_id, discord_id, email, channels):
    """
    **Validates: Requirements 9.2**

    Property 7: For any disabled notification channel, the system SHALL skip
    delivery and not attempt to send notifications through that channel.
    """
    service, mock_bot, mock_supabase, mock_lock_manager = create_mock_notification_service()

    # Setup user data
    user_data = create_mock_user_data(
        user_id, discord_id=discord_id, email=email, dm_enabled=True, email_enabled=True
    )

    # Mock database response
    mock_supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        user_data
    ]

    # Mock lock manager
    mock_lock = Mock()
    mock_lock.id = "test-lock-id"
    mock_lock_manager.acquire_notification_lock = AsyncMock(return_value=mock_lock)
    mock_lock_manager.release_lock = AsyncMock()

    # Mock Discord bot
    mock_user = Mock()
    mock_user.send = AsyncMock()
    mock_bot.fetch_user = AsyncMock(return_value=mock_user)

    # Mock SMTP sending
    with patch.object(service, "_send_smtp_email", new_callable=AsyncMock) as mock_smtp:

        async def run_test():
            results = await service.send_notification(
                user_id=user_id,
                channels=channels,
                subject="Test Subject",
                articles=[],
                notification_type="test",
            )
            return results

        results = asyncio.run(run_test())

        # Count enabled channels (remove duplicates)
        unique_channels = {}
        for c in channels:
            unique_channels[c.type] = c.enabled

        enabled_discord = unique_channels.get("discord_dm", False)
        enabled_email = unique_channels.get("email", False)
        expected_results = sum([enabled_discord, enabled_email])

        # Verify only enabled channels were processed
        assert len(results) == expected_results

        # Verify Discord was only called if enabled
        if enabled_discord:
            mock_bot.fetch_user.assert_called_once()
            mock_user.send.assert_called_once()
        else:
            mock_bot.fetch_user.assert_not_called()
            mock_user.send.assert_not_called()

        # Verify SMTP was only called if enabled
        if enabled_email:
            mock_smtp.assert_called_once()
        else:
            mock_smtp.assert_not_called()


# Feature: personalized-notification-frequency, Property 7: Multi-Channel Notification Delivery (Logging)
@hypothesis_settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(
    user_id=valid_user_ids,
    discord_id=valid_discord_ids,
    subject=notification_subjects,
    notification_type=notification_types,
)
def test_property_7_maintains_delivery_logs(user_id, discord_id, subject, notification_type):
    """
    **Validates: Requirements 10.6**

    Property 7: For any notification delivery attempt, the system SHALL maintain
    delivery logs for tracking and debugging purposes.
    """
    service, mock_bot, mock_supabase, mock_lock_manager = create_mock_notification_service()

    # Setup user data
    user_data = create_mock_user_data(user_id, discord_id=discord_id, dm_enabled=True)

    # Mock database response
    mock_supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        user_data
    ]

    # Mock lock manager
    mock_lock = Mock()
    mock_lock.id = "test-lock-id"
    mock_lock_manager.acquire_notification_lock = AsyncMock(return_value=mock_lock)
    mock_lock_manager.release_lock = AsyncMock()

    # Mock Discord bot
    mock_user = Mock()
    mock_user.send = AsyncMock()
    mock_bot.fetch_user = AsyncMock(return_value=mock_user)

    # Capture log messages
    with (
        patch.object(service.logger, "info") as mock_log_info,
        patch.object(service.logger, "warning") as mock_log_warning,
        patch.object(service.logger, "error") as mock_log_error,
    ):
        channels = [NotificationChannel("discord_dm", True)]

        async def run_test():
            results = await service.send_notification(
                user_id=user_id,
                channels=channels,
                subject=subject,
                articles=[],
                notification_type=notification_type,
            )
            return results

        results = asyncio.run(run_test())

        # Verify logging occurred
        assert mock_log_info.call_count >= 2  # At least start and completion logs

        # Check for specific log messages
        log_calls = [call.args for call in mock_log_info.call_args_list]
        log_messages = [call[0] if call else "" for call in log_calls]

        # Should log notification start
        assert any("Starting notification delivery" in msg for msg in log_messages)

        # Should log notification completion
        assert any("Notification delivery completed" in msg for msg in log_messages)

        # Should log successful Discord DM
        assert any("Successfully sent Discord DM" in msg for msg in log_messages)


# Feature: personalized-notification-frequency, Property 7: Multi-Channel Notification Delivery (Error Handling)
@hypothesis_settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(user_id=valid_user_ids, discord_id=valid_discord_ids, subject=notification_subjects)
def test_property_7_handles_delivery_errors_gracefully(user_id, discord_id, subject):
    """
    **Validates: Requirements 9.5, 10.6**

    Property 7: For any delivery error, the system SHALL handle the error gracefully,
    log the failure, and return appropriate error information.
    """
    service, mock_bot, mock_supabase, mock_lock_manager = create_mock_notification_service()

    # Setup user data
    user_data = create_mock_user_data(user_id, discord_id=discord_id, dm_enabled=True)

    # Mock database response
    mock_supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        user_data
    ]

    # Mock lock manager
    mock_lock = Mock()
    mock_lock.id = "test-lock-id"
    mock_lock_manager.acquire_notification_lock = AsyncMock(return_value=mock_lock)
    mock_lock_manager.release_lock = AsyncMock()

    # Mock Discord bot to always fail
    mock_user = Mock()
    mock_user.send = AsyncMock(side_effect=discord.Forbidden(Mock(), "User has DMs disabled"))
    mock_bot.fetch_user = AsyncMock(return_value=mock_user)

    channels = [NotificationChannel("discord_dm", True)]

    async def run_test():
        results = await service.send_notification(
            user_id=user_id,
            channels=channels,
            subject=subject,
            articles=[],
            notification_type="test",
        )
        return results

    results = asyncio.run(run_test())

    # Verify error was handled gracefully
    assert len(results) == 1
    assert results[0].success is False
    assert results[0].channel == "discord_dm"
    assert results[0].error is not None
    assert "User has DMs disabled" in results[0].error

    # Verify lock was released with failed status
    mock_lock_manager.release_lock.assert_called_once_with("test-lock-id", "failed")


# Feature: personalized-notification-frequency, Property 7: Multi-Channel Notification Delivery (User Preferences)
@hypothesis_settings(
    max_examples=30,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(
    user_id=valid_user_ids,
    discord_id=valid_discord_ids,
    email=valid_emails,
    dm_enabled=st.booleans(),
    email_enabled=st.booleans(),
)
def test_property_7_respects_user_channel_preferences(
    user_id, discord_id, email, dm_enabled, email_enabled
):
    """
    **Validates: Requirements 9.2**

    Property 7: For any user preference setting, the system SHALL respect
    the user's channel enable/disable preferences even when channels are
    configured as enabled in the request.
    """
    service, mock_bot, mock_supabase, mock_lock_manager = create_mock_notification_service()

    # Setup user data with specific preferences
    user_data = create_mock_user_data(
        user_id,
        discord_id=discord_id,
        email=email,
        dm_enabled=dm_enabled,
        email_enabled=email_enabled,
    )

    # Mock database response
    mock_supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        user_data
    ]

    # Mock lock manager
    mock_lock = Mock()
    mock_lock.id = "test-lock-id"
    mock_lock_manager.acquire_notification_lock = AsyncMock(return_value=mock_lock)
    mock_lock_manager.release_lock = AsyncMock()

    # Mock Discord bot
    mock_user = Mock()
    mock_user.send = AsyncMock()
    mock_bot.fetch_user = AsyncMock(return_value=mock_user)

    # Mock SMTP sending
    with patch.object(service, "_send_smtp_email", new_callable=AsyncMock) as mock_smtp:
        # Request both channels enabled
        channels = [NotificationChannel("discord_dm", True), NotificationChannel("email", True)]

        async def run_test():
            results = await service.send_notification(
                user_id=user_id,
                channels=channels,
                subject="Test Subject",
                articles=[],
                notification_type="test",
            )
            return results

        results = asyncio.run(run_test())

        # Filter results by success/failure based on user preferences
        discord_results = [r for r in results if r.channel == "discord_dm"]
        email_results = [r for r in results if r.channel == "email"]

        # Verify Discord DM behavior
        if dm_enabled:
            # Should succeed if user has DM enabled
            assert len(discord_results) == 1
            assert discord_results[0].success is True
            mock_bot.fetch_user.assert_called_once()
        else:
            # Should fail if user has DM disabled
            if discord_results:  # Only check if Discord was attempted
                assert discord_results[0].success is False
                assert "DM notifications disabled" in discord_results[0].error

        # Verify Email behavior
        if email_enabled:
            # Should succeed if user has email enabled
            assert len(email_results) == 1
            assert email_results[0].success is True
            mock_smtp.assert_called_once()
        else:
            # Should fail if user has email disabled
            if email_results:  # Only check if email was attempted
                assert email_results[0].success is False
                assert "Email notifications disabled" in email_results[0].error
