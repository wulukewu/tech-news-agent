"""
Unit tests for ConversationCommands Discord cog.

Tests cover:
- /conversations command (list, empty, error)
- /continue command (found, not found, error)
- /search command (results, no results, error)
- /link command (success, invalid code format, link failure, error)
- ConversationListView pagination

All Discord interactions are mocked so no live bot or database is required.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.bot.cogs.conversation_commands import ConversationCommands, ConversationListView
from app.repositories.conversation import ConversationSummary
from app.services.conversation_search import ConversationSearchResult
from app.services.user_identity import LinkResult

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def _make_interaction(discord_id: str = "123456789") -> MagicMock:
    """Build a minimal mock Discord Interaction."""
    interaction = MagicMock()
    interaction.user.id = discord_id
    interaction.user.__str__ = lambda self: f"TestUser#{discord_id[-4:]}"
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    return interaction


def _make_conversation_summary(
    title: str = "Test Conversation",
    platform: str = "web",
    message_count: int = 5,
    conv_id: UUID | None = None,
) -> ConversationSummary:
    """Build a ConversationSummary for testing."""
    return ConversationSummary(
        id=conv_id or uuid4(),
        title=title,
        platform=platform,
        last_message_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
        message_count=message_count,
        tags=[],
        is_favorite=False,
        is_archived=False,
    )


def _make_search_result(
    title: str = "Search Result",
    platform: str = "web",
    relevance_score: float = 0.9,
    conv_id: str | None = None,
) -> ConversationSearchResult:
    """Build a ConversationSearchResult for testing."""
    return ConversationSearchResult(
        conversation_id=conv_id or str(uuid4()),
        title=title,
        summary=None,
        platform=platform,
        last_message_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
        message_count=3,
        tags=[],
        is_favorite=False,
        is_archived=False,
        relevance_score=relevance_score,
        matched_content=["some matched content"],
        highlight_snippets=["some <mark>matched</mark> content"],
    )


def _make_message(role: str = "user", content: str = "Hello") -> MagicMock:
    """Build a minimal mock ConversationMessage."""
    msg = MagicMock()
    msg.role = role
    msg.content = content
    msg.created_at = datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)
    return msg


def _make_conversation(title: str = "Test Conv", message_count: int = 3) -> MagicMock:
    """Build a minimal mock Conversation."""
    conv = MagicMock()
    conv.id = uuid4()
    conv.title = title
    conv.message_count = message_count
    conv.last_message_at = datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)
    conv.platform = "web"
    return conv


def _make_cog(
    conversations: list | None = None,
    messages: list | None = None,
    search_results: list | None = None,
    link_result: LinkResult | None = None,
    user_uuid: UUID | None = None,
    get_conversation_return: Any = None,
) -> ConversationCommands:
    """Build a ConversationCommands cog with all services mocked."""
    bot = MagicMock()

    conversation_repo = AsyncMock()
    conversation_repo.list_conversations = AsyncMock(return_value=conversations or [])
    conversation_repo.get_conversation = AsyncMock(return_value=get_conversation_return)

    message_repo = AsyncMock()
    message_repo.get_messages = AsyncMock(return_value=messages or [])

    search_service = AsyncMock()
    search_service.search_conversations = AsyncMock(return_value=search_results or [])

    identity_manager = AsyncMock()
    identity_manager.link_platform_account = AsyncMock(
        return_value=link_result
        or LinkResult(
            success=True,
            user_id="user-uuid",
            platform="discord",
            platform_user_id="123456789",
        )
    )

    supabase_service = MagicMock()
    supabase_service.client = MagicMock()

    cog = ConversationCommands(
        bot=bot,
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        search_service=search_service,
        identity_manager=identity_manager,
        supabase_service=supabase_service,
    )

    # Patch _get_user_uuid to return a fixed UUID
    _uuid = user_uuid or uuid4()
    cog._get_user_uuid = AsyncMock(return_value=_uuid)

    return cog


# ---------------------------------------------------------------------------
# ConversationListView tests
# ---------------------------------------------------------------------------


class TestConversationListView:
    def test_single_page_disables_both_buttons(self):
        convs = [_make_conversation_summary(f"Conv {i}") for i in range(3)]
        view = ConversationListView(convs, page=0, per_page=5)
        assert view.previous_page.disabled is True
        assert view.next_page.disabled is True

    def test_first_page_disables_previous(self):
        convs = [_make_conversation_summary(f"Conv {i}") for i in range(10)]
        view = ConversationListView(convs, page=0, per_page=5)
        assert view.previous_page.disabled is True
        assert view.next_page.disabled is False

    def test_last_page_disables_next(self):
        convs = [_make_conversation_summary(f"Conv {i}") for i in range(10)]
        view = ConversationListView(convs, page=1, per_page=5)
        assert view.previous_page.disabled is False
        assert view.next_page.disabled is True

    def test_middle_page_enables_both(self):
        convs = [_make_conversation_summary(f"Conv {i}") for i in range(15)]
        view = ConversationListView(convs, page=1, per_page=5)
        assert view.previous_page.disabled is False
        assert view.next_page.disabled is False

    def test_build_embed_contains_title(self):
        convs = [_make_conversation_summary("My Special Conversation")]
        view = ConversationListView(convs)
        content = view._build_embed()
        assert "My Special Conversation" in content

    def test_build_embed_shows_page_info(self):
        convs = [_make_conversation_summary(f"Conv {i}") for i in range(10)]
        view = ConversationListView(convs, page=0, per_page=5)
        content = view._build_embed()
        assert "第 1/2 頁" in content

    def test_build_embed_respects_char_limit(self):
        # Create conversations with very long titles
        convs = [_make_conversation_summary("A" * 300) for _ in range(20)]
        view = ConversationListView(convs)
        content = view._build_embed()
        assert len(content) <= 2000

    @pytest.mark.asyncio
    async def test_previous_page_decrements_page(self):
        convs = [_make_conversation_summary(f"Conv {i}") for i in range(10)]
        view = ConversationListView(convs, page=1, per_page=5)
        interaction = MagicMock()
        interaction.response = AsyncMock()
        # _ItemCallback is already bound to the view; only interaction is passed
        await view.previous_page.callback(interaction)
        assert view.page == 0
        interaction.response.edit_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_next_page_increments_page(self):
        convs = [_make_conversation_summary(f"Conv {i}") for i in range(10)]
        view = ConversationListView(convs, page=0, per_page=5)
        interaction = MagicMock()
        interaction.response = AsyncMock()
        # _ItemCallback is already bound to the view; only interaction is passed
        await view.next_page.callback(interaction)
        assert view.page == 1
        interaction.response.edit_message.assert_called_once()


# ---------------------------------------------------------------------------
# /conversations command tests
# ---------------------------------------------------------------------------


class TestConversationsCommand:
    @pytest.mark.asyncio
    async def test_lists_conversations_when_present(self):
        convs = [_make_conversation_summary(f"Conv {i}") for i in range(3)]
        cog = _make_cog(conversations=convs)
        interaction = _make_interaction()

        await cog.conversations.callback(cog, interaction)

        interaction.response.defer.assert_called_once_with(thinking=True, ephemeral=True)
        interaction.followup.send.assert_called_once()
        call_kwargs = interaction.followup.send.call_args
        assert call_kwargs.kwargs.get("ephemeral") is True
        # Should include a view for pagination
        assert call_kwargs.kwargs.get("view") is not None

    @pytest.mark.asyncio
    async def test_empty_conversations_sends_no_history_message(self):
        cog = _make_cog(conversations=[])
        interaction = _make_interaction()

        await cog.conversations.callback(cog, interaction)

        interaction.followup.send.assert_called_once()
        content = interaction.followup.send.call_args.args[0]
        assert "還沒有" in content or "沒有" in content

    @pytest.mark.asyncio
    async def test_user_not_registered_returns_early(self):
        cog = _make_cog()
        cog._get_user_uuid = AsyncMock(return_value=None)
        interaction = _make_interaction()

        await cog.conversations.callback(cog, interaction)

        # followup.send should NOT be called for conversation list
        interaction.followup.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_database_error_sends_error_message(self):
        from app.core.exceptions import SupabaseServiceError

        cog = _make_cog()
        cog.conversation_repo.list_conversations = AsyncMock(
            side_effect=SupabaseServiceError("DB error")
        )
        interaction = _make_interaction()

        await cog.conversations.callback(cog, interaction)

        interaction.followup.send.assert_called_once()
        content = interaction.followup.send.call_args.args[0]
        assert "❌" in content

    @pytest.mark.asyncio
    async def test_unexpected_error_sends_error_message(self):
        cog = _make_cog()
        cog.conversation_repo.list_conversations = AsyncMock(
            side_effect=RuntimeError("Unexpected!")
        )
        interaction = _make_interaction()

        await cog.conversations.callback(cog, interaction)

        interaction.followup.send.assert_called_once()
        content = interaction.followup.send.call_args.args[0]
        assert "❌" in content


# ---------------------------------------------------------------------------
# /continue command tests
# ---------------------------------------------------------------------------


class TestContinueCommand:
    @pytest.mark.asyncio
    async def test_loads_context_for_existing_conversation(self):
        conv = _make_conversation("My Conversation", message_count=10)
        msgs = [
            _make_message("user", "Hello"),
            _make_message("assistant", "Hi there!"),
        ]
        cog = _make_cog(messages=msgs, get_conversation_return=conv)
        interaction = _make_interaction()

        await cog.continue_conversation.callback(cog, interaction, str(conv.id))

        interaction.followup.send.assert_called_once()
        # followup.send uses keyword arg content=
        content = interaction.followup.send.call_args.kwargs["content"]
        assert "My Conversation" in content
        assert "✅" in content

    @pytest.mark.asyncio
    async def test_not_found_sends_error_message(self):
        cog = _make_cog(get_conversation_return=None)
        interaction = _make_interaction()

        await cog.continue_conversation.callback(cog, interaction, "nonexistent-id")

        interaction.followup.send.assert_called_once()
        content = interaction.followup.send.call_args.args[0]
        assert "❌" in content
        assert "找不到" in content

    @pytest.mark.asyncio
    async def test_shows_last_messages_as_context(self):
        conv = _make_conversation("Conv with messages")
        msgs = [
            _make_message("user", "First message"),
            _make_message("assistant", "Second message"),
            _make_message("user", "Third message"),
        ]
        cog = _make_cog(messages=msgs, get_conversation_return=conv)
        interaction = _make_interaction()

        await cog.continue_conversation.callback(cog, interaction, str(conv.id))

        # followup.send uses keyword arg content=
        content = interaction.followup.send.call_args.kwargs["content"]
        assert "First message" in content or "Third message" in content

    @pytest.mark.asyncio
    async def test_truncates_long_message_content(self):
        conv = _make_conversation("Conv")
        long_content = "A" * 500
        msgs = [_make_message("user", long_content)]
        cog = _make_cog(messages=msgs, get_conversation_return=conv)
        interaction = _make_interaction()

        await cog.continue_conversation.callback(cog, interaction, str(conv.id))

        # followup.send uses keyword arg content=
        content = interaction.followup.send.call_args.kwargs["content"]
        # The full 500-char content should not appear verbatim
        assert long_content not in content
        assert "..." in content

    @pytest.mark.asyncio
    async def test_user_not_registered_returns_early(self):
        cog = _make_cog()
        cog._get_user_uuid = AsyncMock(return_value=None)
        interaction = _make_interaction()

        await cog.continue_conversation.callback(cog, interaction, "some-id")

        interaction.followup.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_database_error_sends_error_message(self):
        from app.core.exceptions import SupabaseServiceError

        cog = _make_cog()
        cog.conversation_repo.get_conversation = AsyncMock(
            side_effect=SupabaseServiceError("DB error")
        )
        interaction = _make_interaction()

        await cog.continue_conversation.callback(cog, interaction, "some-id")

        content = interaction.followup.send.call_args.args[0]
        assert "❌" in content


# ---------------------------------------------------------------------------
# /search command tests
# ---------------------------------------------------------------------------


class TestSearchCommand:
    @pytest.mark.asyncio
    async def test_returns_search_results(self):
        results = [
            _make_search_result("Python Tutorial", relevance_score=0.95),
            _make_search_result("Python Tips", relevance_score=0.80),
        ]
        cog = _make_cog(search_results=results)
        interaction = _make_interaction()

        await cog.search.callback(cog, interaction, "python")

        interaction.followup.send.assert_called_once()
        content = interaction.followup.send.call_args.kwargs["content"]
        assert "python" in content.lower() or "Python" in content
        assert "Python Tutorial" in content

    @pytest.mark.asyncio
    async def test_no_results_sends_not_found_message(self):
        cog = _make_cog(search_results=[])
        interaction = _make_interaction()

        await cog.search.callback(cog, interaction, "nonexistent query")

        content = interaction.followup.send.call_args.args[0]
        assert "找不到" in content

    @pytest.mark.asyncio
    async def test_shows_relevance_score(self):
        results = [_make_search_result("Result", relevance_score=0.75)]
        cog = _make_cog(search_results=results)
        interaction = _make_interaction()

        await cog.search.callback(cog, interaction, "query")

        content = interaction.followup.send.call_args.kwargs["content"]
        assert "75%" in content

    @pytest.mark.asyncio
    async def test_strips_mark_tags_from_snippets(self):
        result = _make_search_result()
        result.highlight_snippets = ["some <mark>highlighted</mark> text"]
        cog = _make_cog(search_results=[result])
        interaction = _make_interaction()

        await cog.search.callback(cog, interaction, "highlighted")

        content = interaction.followup.send.call_args.kwargs["content"]
        assert "<mark>" not in content
        assert "</mark>" not in content

    @pytest.mark.asyncio
    async def test_respects_discord_char_limit(self):
        # Many results with long titles
        results = [_make_search_result("A" * 200, relevance_score=0.9) for _ in range(10)]
        cog = _make_cog(search_results=results)
        interaction = _make_interaction()

        await cog.search.callback(cog, interaction, "query")

        content = interaction.followup.send.call_args.kwargs["content"]
        assert len(content) <= 2000

    @pytest.mark.asyncio
    async def test_user_not_registered_returns_early(self):
        cog = _make_cog()
        cog._get_user_uuid = AsyncMock(return_value=None)
        interaction = _make_interaction()

        await cog.search.callback(cog, interaction, "query")

        interaction.followup.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_database_error_sends_error_message(self):
        from app.core.exceptions import SupabaseServiceError

        cog = _make_cog()
        cog.search_service.search_conversations = AsyncMock(
            side_effect=SupabaseServiceError("DB error")
        )
        interaction = _make_interaction()

        await cog.search.callback(cog, interaction, "query")

        content = interaction.followup.send.call_args.args[0]
        assert "❌" in content


# ---------------------------------------------------------------------------
# /link command tests
# ---------------------------------------------------------------------------


class TestLinkCommand:
    @pytest.mark.asyncio
    async def test_successful_link(self):
        link_result = LinkResult(
            success=True,
            user_id="user-uuid",
            platform="discord",
            platform_user_id="123456789",
        )
        cog = _make_cog(link_result=link_result)
        interaction = _make_interaction()

        await cog.link.callback(cog, interaction, "123456")

        content = interaction.followup.send.call_args.args[0]
        assert "✅" in content
        assert "成功" in content

    @pytest.mark.asyncio
    async def test_invalid_code_format_non_digits(self):
        cog = _make_cog()
        interaction = _make_interaction()

        await cog.link.callback(cog, interaction, "abc123")

        content = interaction.followup.send.call_args.args[0]
        assert "❌" in content
        assert "格式" in content

    @pytest.mark.asyncio
    async def test_invalid_code_format_wrong_length(self):
        cog = _make_cog()
        interaction = _make_interaction()

        await cog.link.callback(cog, interaction, "12345")  # 5 digits, not 6

        content = interaction.followup.send.call_args.args[0]
        assert "❌" in content
        assert "格式" in content

    @pytest.mark.asyncio
    async def test_link_failure_shows_error_reason(self):
        link_result = LinkResult(
            success=False,
            user_id="user-uuid",
            platform="discord",
            platform_user_id="123456789",
            error="Invalid or expired verification code",
        )
        cog = _make_cog(link_result=link_result)
        interaction = _make_interaction()

        await cog.link.callback(cog, interaction, "999999")

        content = interaction.followup.send.call_args.args[0]
        assert "❌" in content
        assert "Invalid or expired verification code" in content

    @pytest.mark.asyncio
    async def test_user_not_registered_returns_early(self):
        cog = _make_cog()
        cog._get_user_uuid = AsyncMock(return_value=None)
        interaction = _make_interaction()

        await cog.link.callback(cog, interaction, "123456")

        # identity_manager.link_platform_account should NOT be called
        cog.identity_manager.link_platform_account.assert_not_called()

    @pytest.mark.asyncio
    async def test_database_error_sends_error_message(self):
        from app.core.exceptions import SupabaseServiceError

        cog = _make_cog()
        cog.identity_manager.link_platform_account = AsyncMock(
            side_effect=SupabaseServiceError("DB error")
        )
        interaction = _make_interaction()

        await cog.link.callback(cog, interaction, "123456")

        content = interaction.followup.send.call_args.args[0]
        assert "❌" in content

    @pytest.mark.asyncio
    async def test_seven_digit_code_rejected(self):
        cog = _make_cog()
        interaction = _make_interaction()

        await cog.link.callback(cog, interaction, "1234567")  # 7 digits

        content = interaction.followup.send.call_args.args[0]
        assert "❌" in content
        assert "格式" in content


# ---------------------------------------------------------------------------
# _get_user_uuid helper tests
# ---------------------------------------------------------------------------


class TestGetUserUuid:
    @pytest.mark.asyncio
    async def test_returns_uuid_on_success(self):
        expected_uuid = uuid4()
        cog = _make_cog(user_uuid=expected_uuid)
        # Restore the real method to test it

        with patch(
            "app.bot.cogs.conversation_commands.ensure_user_registered",
            new_callable=AsyncMock,
            return_value=expected_uuid,
        ):
            # Re-create cog without the patched _get_user_uuid
            bot = MagicMock()
            supabase_service = MagicMock()
            supabase_service.client = MagicMock()
            real_cog = ConversationCommands(
                bot=bot,
                supabase_service=supabase_service,
                conversation_repo=AsyncMock(),
                message_repo=AsyncMock(),
                search_service=AsyncMock(),
                identity_manager=AsyncMock(),
            )
            interaction = _make_interaction()
            result = await real_cog._get_user_uuid(interaction)
            assert result == expected_uuid

    @pytest.mark.asyncio
    async def test_returns_none_and_sends_error_on_failure(self):
        from app.core.exceptions import SupabaseServiceError

        bot = MagicMock()
        supabase_service = MagicMock()
        supabase_service.client = MagicMock()
        cog = ConversationCommands(
            bot=bot,
            supabase_service=supabase_service,
            conversation_repo=AsyncMock(),
            message_repo=AsyncMock(),
            search_service=AsyncMock(),
            identity_manager=AsyncMock(),
        )

        with patch(
            "app.bot.cogs.conversation_commands.ensure_user_registered",
            new_callable=AsyncMock,
            side_effect=SupabaseServiceError("Registration failed"),
        ):
            interaction = _make_interaction()
            result = await cog._get_user_uuid(interaction)

        assert result is None
        interaction.followup.send.assert_called_once()
        content = interaction.followup.send.call_args.args[0]
        assert "❌" in content
