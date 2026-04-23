"""
Unit tests for ConversationAutoManager cog.

Tests cover:
- Title generation logic
- Session activity detection (active / timed-out / missing)
- on_message filtering (bots, non-DM channels, slash commands)
- New conversation creation and notification
- Existing conversation reuse
- Session timeout triggering a new conversation
- Database error handling
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import discord
import pytest

from app.bot.cogs.conversation_auto_manager import (
    _AUTO_TITLE_MAX_CHARS,
    _AUTO_TITLE_MIN_CHARS,
    _DEFAULT_TITLE,
    _SESSION_TIMEOUT_MINUTES,
    ConversationAutoManager,
)
from app.core.exceptions import SupabaseServiceError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_cog(
    conversation_repo=None,
    message_repo=None,
    supabase_service=None,
) -> ConversationAutoManager:
    """Create a ConversationAutoManager with fully mocked dependencies."""
    bot = MagicMock(spec=discord.ext.commands.Bot)

    if supabase_service is None:
        supabase_service = MagicMock()
        supabase_service.client = MagicMock()

    if conversation_repo is None:
        conversation_repo = AsyncMock()

    if message_repo is None:
        message_repo = AsyncMock()

    cog = ConversationAutoManager(
        bot=bot,
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        supabase_service=supabase_service,
    )
    return cog


def _make_dm_message(
    content: str = "Hello",
    author_bot: bool = False,
    user_id: int = 123456789,
) -> MagicMock:
    """Build a mock Discord DM message."""
    message = MagicMock(spec=discord.Message)
    message.content = content
    message.author = MagicMock()
    message.author.bot = author_bot
    message.author.id = user_id
    message.channel = MagicMock(spec=discord.DMChannel)
    message.channel.send = AsyncMock()
    return message


def _make_guild_message(content: str = "Hello") -> MagicMock:
    """Build a mock Discord guild (non-DM) message."""
    message = MagicMock(spec=discord.Message)
    message.content = content
    message.author = MagicMock()
    message.author.bot = False
    message.author.id = 111
    # Not a DMChannel
    message.channel = MagicMock(spec=discord.TextChannel)
    return message


def _make_conversation(conv_id: UUID | None = None) -> MagicMock:
    """Build a mock Conversation object."""
    conv = MagicMock()
    conv.id = conv_id or uuid4()
    return conv


# ---------------------------------------------------------------------------
# _generate_title
# ---------------------------------------------------------------------------


class TestGenerateTitle:
    def test_short_content_returns_default_title(self):
        cog = _make_cog()
        # Content shorter than _AUTO_TITLE_MIN_CHARS
        short = "Hi"
        assert len(short) < _AUTO_TITLE_MIN_CHARS
        assert cog._generate_title(short) == _DEFAULT_TITLE

    def test_empty_content_returns_default_title(self):
        cog = _make_cog()
        assert cog._generate_title("") == _DEFAULT_TITLE

    def test_whitespace_only_returns_default_title(self):
        cog = _make_cog()
        assert cog._generate_title("   ") == _DEFAULT_TITLE

    def test_content_exactly_min_chars_returns_content(self):
        cog = _make_cog()
        content = "a" * _AUTO_TITLE_MIN_CHARS
        assert cog._generate_title(content) == content

    def test_content_within_max_chars_returns_full_content(self):
        cog = _make_cog()
        content = "This is a normal message"
        assert len(content) <= _AUTO_TITLE_MAX_CHARS
        assert cog._generate_title(content) == content

    def test_long_content_is_truncated_to_max_chars(self):
        cog = _make_cog()
        content = "x" * (_AUTO_TITLE_MAX_CHARS + 20)
        result = cog._generate_title(content)
        assert len(result) == _AUTO_TITLE_MAX_CHARS
        assert result == content[:_AUTO_TITLE_MAX_CHARS]

    def test_leading_trailing_whitespace_is_stripped(self):
        cog = _make_cog()
        content = "  Hello world  "
        result = cog._generate_title(content)
        assert result == "Hello world"

    def test_content_exactly_max_chars_returns_full_content(self):
        cog = _make_cog()
        content = "a" * _AUTO_TITLE_MAX_CHARS
        assert cog._generate_title(content) == content


# ---------------------------------------------------------------------------
# _is_session_active
# ---------------------------------------------------------------------------


class TestIsSessionActive:
    def test_no_cached_conversation_returns_false(self):
        cog = _make_cog()
        assert cog._is_session_active("999") is False

    def test_cached_conversation_with_recent_activity_returns_true(self):
        cog = _make_cog()
        user_id = "111"
        cog._active_conversations[user_id] = str(uuid4())
        cog._last_activity[user_id] = datetime.now(timezone.utc) - timedelta(minutes=5)
        assert cog._is_session_active(user_id) is True

    def test_cached_conversation_with_timed_out_activity_returns_false(self):
        cog = _make_cog()
        user_id = "222"
        cog._active_conversations[user_id] = str(uuid4())
        cog._last_activity[user_id] = datetime.now(timezone.utc) - timedelta(
            minutes=_SESSION_TIMEOUT_MINUTES + 1
        )
        assert cog._is_session_active(user_id) is False

    def test_cached_conversation_with_no_last_activity_returns_false(self):
        cog = _make_cog()
        user_id = "333"
        cog._active_conversations[user_id] = str(uuid4())
        # No entry in _last_activity
        assert cog._is_session_active(user_id) is False

    def test_exactly_at_timeout_boundary_returns_false(self):
        cog = _make_cog()
        user_id = "444"
        cog._active_conversations[user_id] = str(uuid4())
        # Exactly at the timeout boundary (not strictly less than)
        cog._last_activity[user_id] = datetime.now(timezone.utc) - timedelta(
            minutes=_SESSION_TIMEOUT_MINUTES
        )
        assert cog._is_session_active(user_id) is False


# ---------------------------------------------------------------------------
# _get_or_create_conversation
# ---------------------------------------------------------------------------


class TestGetOrCreateConversation:
    @pytest.mark.asyncio
    async def test_creates_new_conversation_when_no_active_session(self):
        conv_id = uuid4()
        mock_conv = _make_conversation(conv_id)

        conv_repo = AsyncMock()
        conv_repo.create_conversation = AsyncMock(return_value=mock_conv)

        cog = _make_cog(conversation_repo=conv_repo)

        result_id, is_new = await cog._get_or_create_conversation(
            discord_user_id="user1",
            system_user_id=str(uuid4()),
            first_message="Hello there",
        )

        assert is_new is True
        assert result_id == str(conv_id)
        conv_repo.create_conversation.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reuses_existing_conversation_when_session_active(self):
        existing_conv_id = str(uuid4())
        conv_repo = AsyncMock()

        cog = _make_cog(conversation_repo=conv_repo)
        user_id = "user2"
        cog._active_conversations[user_id] = existing_conv_id
        cog._last_activity[user_id] = datetime.now(timezone.utc) - timedelta(minutes=1)

        result_id, is_new = await cog._get_or_create_conversation(
            discord_user_id=user_id,
            system_user_id=str(uuid4()),
            first_message="Follow-up message",
        )

        assert is_new is False
        assert result_id == existing_conv_id
        conv_repo.create_conversation.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_creates_new_conversation_after_session_timeout(self):
        old_conv_id = str(uuid4())
        new_conv_id = uuid4()
        mock_conv = _make_conversation(new_conv_id)

        conv_repo = AsyncMock()
        conv_repo.create_conversation = AsyncMock(return_value=mock_conv)

        cog = _make_cog(conversation_repo=conv_repo)
        user_id = "user3"
        cog._active_conversations[user_id] = old_conv_id
        cog._last_activity[user_id] = datetime.now(timezone.utc) - timedelta(
            minutes=_SESSION_TIMEOUT_MINUTES + 5
        )

        result_id, is_new = await cog._get_or_create_conversation(
            discord_user_id=user_id,
            system_user_id=str(uuid4()),
            first_message="New session message",
        )

        assert is_new is True
        assert result_id == str(new_conv_id)
        assert cog._active_conversations[user_id] == str(new_conv_id)

    @pytest.mark.asyncio
    async def test_title_generated_from_first_message(self):
        conv_repo = AsyncMock()
        conv_repo.create_conversation = AsyncMock(return_value=_make_conversation())

        cog = _make_cog(conversation_repo=conv_repo)

        first_message = "What is the capital of France?"
        await cog._get_or_create_conversation(
            discord_user_id="user4",
            system_user_id=str(uuid4()),
            first_message=first_message,
        )

        call_kwargs = conv_repo.create_conversation.call_args.kwargs
        assert call_kwargs["title"] == first_message
        assert call_kwargs["platform"] == "discord"

    @pytest.mark.asyncio
    async def test_short_message_uses_default_title(self):
        conv_repo = AsyncMock()
        conv_repo.create_conversation = AsyncMock(return_value=_make_conversation())

        cog = _make_cog(conversation_repo=conv_repo)

        await cog._get_or_create_conversation(
            discord_user_id="user5",
            system_user_id=str(uuid4()),
            first_message="Hi",
        )

        call_kwargs = conv_repo.create_conversation.call_args.kwargs
        assert call_kwargs["title"] == _DEFAULT_TITLE


# ---------------------------------------------------------------------------
# on_message
# ---------------------------------------------------------------------------


class TestOnMessage:
    @pytest.mark.asyncio
    async def test_ignores_bot_messages(self):
        cog = _make_cog()
        message = _make_dm_message(author_bot=True)

        await cog.on_message(message)

        # No DB calls should have been made
        cog.conversation_repo.create_conversation.assert_not_awaited()
        cog.message_repo.add_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_ignores_non_dm_channels(self):
        cog = _make_cog()
        message = _make_guild_message()

        await cog.on_message(message)

        cog.conversation_repo.create_conversation.assert_not_awaited()
        cog.message_repo.add_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_ignores_slash_commands(self):
        cog = _make_cog()
        message = _make_dm_message(content="/conversations")

        await cog.on_message(message)

        cog.conversation_repo.create_conversation.assert_not_awaited()
        cog.message_repo.add_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_creates_conversation_and_saves_message_for_new_user(self):
        system_uuid = uuid4()
        conv_id = uuid4()
        mock_conv = _make_conversation(conv_id)

        supabase_service = MagicMock()
        supabase_service.client = MagicMock()
        supabase_service.get_or_create_user = AsyncMock(return_value=system_uuid)

        conv_repo = AsyncMock()
        conv_repo.create_conversation = AsyncMock(return_value=mock_conv)

        msg_repo = AsyncMock()
        msg_repo.add_message = AsyncMock()

        cog = _make_cog(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
            supabase_service=supabase_service,
        )

        message = _make_dm_message(content="Hello, I need help!", user_id=42)
        await cog.on_message(message)

        # Conversation should have been created
        conv_repo.create_conversation.assert_awaited_once()
        # Message should have been saved
        msg_repo.add_message.assert_awaited_once_with(
            conversation_id=str(conv_id),
            role="user",
            content="Hello, I need help!",
            platform="discord",
        )
        # Notification should have been sent
        message.channel.send.assert_awaited_once()
        notification_text: str = message.channel.send.call_args.args[0]
        assert str(conv_id)[:8] in notification_text

    @pytest.mark.asyncio
    async def test_reuses_conversation_for_active_session(self):
        system_uuid = uuid4()
        existing_conv_id = str(uuid4())

        supabase_service = MagicMock()
        supabase_service.client = MagicMock()
        supabase_service.get_or_create_user = AsyncMock(return_value=system_uuid)

        conv_repo = AsyncMock()
        msg_repo = AsyncMock()
        msg_repo.add_message = AsyncMock()

        cog = _make_cog(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
            supabase_service=supabase_service,
        )

        user_id = "77"
        cog._active_conversations[user_id] = existing_conv_id
        cog._last_activity[user_id] = datetime.now(timezone.utc) - timedelta(minutes=2)

        message = _make_dm_message(content="Follow-up question", user_id=int(user_id))
        await cog.on_message(message)

        # No new conversation should be created
        conv_repo.create_conversation.assert_not_awaited()
        # Message saved to existing conversation
        msg_repo.add_message.assert_awaited_once_with(
            conversation_id=existing_conv_id,
            role="user",
            content="Follow-up question",
            platform="discord",
        )
        # No notification for existing conversation
        message.channel.send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_notification_sent_for_existing_conversation(self):
        system_uuid = uuid4()
        existing_conv_id = str(uuid4())

        supabase_service = MagicMock()
        supabase_service.client = MagicMock()
        supabase_service.get_or_create_user = AsyncMock(return_value=system_uuid)

        conv_repo = AsyncMock()
        msg_repo = AsyncMock()

        cog = _make_cog(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
            supabase_service=supabase_service,
        )

        user_id = "88"
        cog._active_conversations[user_id] = existing_conv_id
        cog._last_activity[user_id] = datetime.now(timezone.utc) - timedelta(minutes=1)

        message = _make_dm_message(content="Another message", user_id=int(user_id))
        await cog.on_message(message)

        message.channel.send.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_database_error_is_handled_gracefully(self):
        supabase_service = MagicMock()
        supabase_service.client = MagicMock()
        supabase_service.get_or_create_user = AsyncMock(
            side_effect=SupabaseServiceError("DB error")
        )

        cog = _make_cog(supabase_service=supabase_service)
        message = _make_dm_message(content="Hello")

        # Should not raise; errors are caught and logged
        await cog.on_message(message)

    @pytest.mark.asyncio
    async def test_unexpected_error_is_handled_gracefully(self):
        supabase_service = MagicMock()
        supabase_service.client = MagicMock()
        supabase_service.get_or_create_user = AsyncMock(side_effect=RuntimeError("Unexpected!"))

        cog = _make_cog(supabase_service=supabase_service)
        message = _make_dm_message(content="Hello")

        # Should not raise
        await cog.on_message(message)

    @pytest.mark.asyncio
    async def test_last_activity_updated_after_message(self):
        system_uuid = uuid4()
        conv_id = uuid4()
        mock_conv = _make_conversation(conv_id)

        supabase_service = MagicMock()
        supabase_service.client = MagicMock()
        supabase_service.get_or_create_user = AsyncMock(return_value=system_uuid)

        conv_repo = AsyncMock()
        conv_repo.create_conversation = AsyncMock(return_value=mock_conv)

        msg_repo = AsyncMock()

        cog = _make_cog(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
            supabase_service=supabase_service,
        )

        user_id = "99"
        message = _make_dm_message(content="Test message", user_id=int(user_id))

        before = datetime.now(timezone.utc)
        await cog.on_message(message)
        after = datetime.now(timezone.utc)

        assert user_id in cog._last_activity
        assert before <= cog._last_activity[user_id] <= after

    @pytest.mark.asyncio
    async def test_notification_contains_continue_command(self):
        system_uuid = uuid4()
        conv_id = uuid4()
        mock_conv = _make_conversation(conv_id)

        supabase_service = MagicMock()
        supabase_service.client = MagicMock()
        supabase_service.get_or_create_user = AsyncMock(return_value=system_uuid)

        conv_repo = AsyncMock()
        conv_repo.create_conversation = AsyncMock(return_value=mock_conv)

        msg_repo = AsyncMock()

        cog = _make_cog(
            conversation_repo=conv_repo,
            message_repo=msg_repo,
            supabase_service=supabase_service,
        )

        message = _make_dm_message(content="Start a new conversation", user_id=55)
        await cog.on_message(message)

        notification: str = message.channel.send.call_args.args[0]
        assert "/continue" in notification
        assert str(conv_id) in notification
