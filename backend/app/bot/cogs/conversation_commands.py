"""
Discord Bot Conversation Management Commands

Provides slash commands for managing conversations via Discord:
- /conversations  - List user's conversations with pagination
- /continue <id>  - Continue a specific conversation by loading context
- /search <query> - Search historical conversations
- /link <code>    - Link Discord account to system account

Validates: Requirements 4.1, 4.3, 4.4, 4.5
"""

from __future__ import annotations

from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from app.bot.utils.decorators import ensure_user_registered
from app.core.exceptions import SupabaseServiceError
from app.core.logger import get_logger
from app.repositories.conversation import ConversationFilters, ConversationRepository
from app.repositories.message import MessageRepository
from app.services.conversation_search import ConversationSearchService, SearchFilters
from app.services.supabase_service import SupabaseService
from app.services.user_identity import UserIdentityManager
from app.utils.message_formatter import MessageFormatter

logger = get_logger(__name__)

_PER_PAGE = 5
_CONTEXT_MESSAGES = 5
_MAX_SEARCH_RESULTS = 5
_DISCORD_CHAR_LIMIT = 2000
_RESERVED_CHARS = 100


# ---------------------------------------------------------------------------
# Pagination View
# ---------------------------------------------------------------------------


class ConversationListView(discord.ui.View):
    """Paginated view for the /conversations command.

    Renders up to ``per_page`` conversations per page and provides
    Previous / Next navigation buttons.
    """

    def __init__(self, conversations: list, page: int = 0, per_page: int = _PER_PAGE):
        super().__init__(timeout=60)
        self.conversations = conversations
        self.page = page
        self.per_page = per_page
        self._update_buttons()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _update_buttons(self) -> None:
        """Enable or disable navigation buttons based on the current page."""
        total_pages = max(1, (len(self.conversations) + self.per_page - 1) // self.per_page)
        self.previous_page.disabled = self.page <= 0
        self.next_page.disabled = self.page >= total_pages - 1

    def _build_embed(self) -> str:
        """Build the message content for the current page."""
        start = self.page * self.per_page
        end = start + self.per_page
        page_items = self.conversations[start:end]
        total_pages = max(1, (len(self.conversations) + self.per_page - 1) // self.per_page)

        lines = [
            f"📚 **你的對話列表** (第 {self.page + 1}/{total_pages} 頁，共 {len(self.conversations)} 個對話)\n"
        ]

        for i, conv in enumerate(page_items, start=start + 1):
            platform_emoji = "🌐" if getattr(conv, "platform", "web") == "web" else "💬"
            last_msg = getattr(conv, "last_message_at", None)
            last_msg_str = last_msg.strftime("%Y-%m-%d %H:%M") if last_msg else "N/A"
            msg_count = getattr(conv, "message_count", 0)
            title = getattr(conv, "title", "無標題")
            conv_id = str(getattr(conv, "id", ""))

            entry = (
                f"**{i}.** {platform_emoji} {title}\n"
                f"   🆔 `{conv_id[:8]}...`  💬 {msg_count} 則訊息  🕐 {last_msg_str}\n"
            )

            # Respect Discord character limit
            test = "\n".join(lines) + entry
            if len(test) > _DISCORD_CHAR_LIMIT - _RESERVED_CHARS:
                lines.append("_...更多對話請翻頁查看_")
                break
            lines.append(entry)

        lines.append("\n💡 使用 `/continue <id>` 繼續對話")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Button callbacks
    # ------------------------------------------------------------------

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary)
    async def previous_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.page = max(0, self.page - 1)
        self._update_buttons()
        await interaction.response.edit_message(content=self._build_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        total_pages = max(1, (len(self.conversations) + self.per_page - 1) // self.per_page)
        self.page = min(total_pages - 1, self.page + 1)
        self._update_buttons()
        await interaction.response.edit_message(content=self._build_embed(), view=self)


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class ConversationCommands(commands.Cog):
    """Discord cog providing conversation management slash commands.

    All service dependencies are injected via ``__init__`` for testability.
    """

    def __init__(
        self,
        bot: commands.Bot,
        conversation_repo: Optional[ConversationRepository] = None,
        message_repo: Optional[MessageRepository] = None,
        search_service: Optional[ConversationSearchService] = None,
        identity_manager: Optional[UserIdentityManager] = None,
        supabase_service: Optional[SupabaseService] = None,
    ):
        """Initialise the cog with optional injected service dependencies.

        Args:
            bot: Discord bot instance.
            conversation_repo: Repository for conversation data access.
            message_repo: Repository for message data access.
            search_service: Service for searching conversations.
            identity_manager: Service for user identity linking.
            supabase_service: Supabase service for user registration.
        """
        self.bot = bot
        self._supabase_service = supabase_service or SupabaseService()

        client = self._supabase_service.client
        self.conversation_repo = conversation_repo or ConversationRepository(client)
        self.message_repo = message_repo or MessageRepository(client)
        self.search_service = search_service or ConversationSearchService(
            self.conversation_repo, self.message_repo
        )
        self.identity_manager = identity_manager or UserIdentityManager(client)

    # ------------------------------------------------------------------
    # /conversations
    # ------------------------------------------------------------------

    @app_commands.command(name="conversations", description="列出你的對話歷史（支援分頁）")
    async def conversations(self, interaction: discord.Interaction) -> None:
        """List the user's conversations with pagination support."""
        logger.info(
            "Command /conversations triggered",
            user_id=str(interaction.user.id),
            command="conversations",
        )
        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            user_uuid = await self._get_user_uuid(interaction)
            if user_uuid is None:
                return

            filters = ConversationFilters(limit=100, offset=0)
            conversations = await self.conversation_repo.list_conversations(
                user_id=user_uuid, filters=filters
            )

            if not conversations:
                await interaction.followup.send(
                    "📭 你還沒有任何對話記錄。\n" "💡 開始一個新對話，它將自動被記錄下來！",
                    ephemeral=True,
                )
                return

            view = ConversationListView(conversations)
            await interaction.followup.send(
                content=view._build_embed(),
                view=view,
                ephemeral=True,
            )
            logger.info(
                "Successfully sent /conversations response",
                user_id=str(interaction.user.id),
                conversation_count=len(conversations),
            )

        except SupabaseServiceError as e:
            logger.error(
                "Database error in /conversations",
                user_id=str(interaction.user.id),
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 無法取得對話列表，請稍後再試。",
                ephemeral=True,
            )
        except Exception as e:
            logger.critical(
                "Unexpected error in /conversations",
                user_id=str(interaction.user.id),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。",
                ephemeral=True,
            )

    # ------------------------------------------------------------------
    # /continue
    # ------------------------------------------------------------------

    @app_commands.command(name="continue", description="繼續特定對話並載入上下文")
    @app_commands.describe(conversation_id="對話 ID（可從 /conversations 取得）")
    async def continue_conversation(
        self, interaction: discord.Interaction, conversation_id: str
    ) -> None:
        """Load context for a conversation and confirm the user can continue."""
        logger.info(
            "Command /continue triggered",
            user_id=str(interaction.user.id),
            conversation_id=conversation_id,
            command="continue",
        )
        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            user_uuid = await self._get_user_uuid(interaction)
            if user_uuid is None:
                return

            # Fetch the conversation (ownership check included)
            conversation = await self.conversation_repo.get_conversation(
                conversation_id=conversation_id,
                user_id=user_uuid,
            )

            if conversation is None:
                await interaction.followup.send(
                    f"❌ 找不到對話 `{conversation_id}`。\n" "💡 請使用 `/conversations` 查看你的對話列表。",
                    ephemeral=True,
                )
                return

            # Fetch the last N messages for context
            messages = await self.message_repo.get_messages(
                conversation_id=conversation_id,
                limit=_CONTEXT_MESSAGES,
                ascending=False,
            )
            # Reverse to chronological order
            messages = list(reversed(messages))

            lines = [
                f"✅ **繼續對話：{conversation.title}**\n",
                f"🆔 ID: `{conversation_id}`",
                f"📅 最後訊息：{conversation.last_message_at.strftime('%Y-%m-%d %H:%M')}",
                f"💬 共 {conversation.message_count} 則訊息\n",
            ]

            if messages:
                lines.append(f"📜 **最近 {len(messages)} 則訊息：**\n")
                for msg in messages:
                    role_emoji = "👤" if msg.role == "user" else "🤖"
                    # Truncate long messages for display
                    content = msg.content
                    if len(content) > 200:
                        content = content[:197] + "..."
                    # Convert to Discord format
                    content = MessageFormatter.web_to_discord(content)
                    timestamp = msg.created_at.strftime("%H:%M")
                    entry = f"{role_emoji} [{timestamp}] {content}\n"

                    test = "\n".join(lines) + entry
                    if len(test) > _DISCORD_CHAR_LIMIT - _RESERVED_CHARS:
                        lines.append("_...更多訊息已省略_")
                        break
                    lines.append(entry)
            else:
                lines.append("_（此對話尚無訊息）_")

            lines.append("\n💬 你現在可以繼續這個對話了！")

            await interaction.followup.send(
                content="\n".join(lines),
                ephemeral=True,
            )
            logger.info(
                "Successfully sent /continue response",
                user_id=str(interaction.user.id),
                conversation_id=conversation_id,
                message_count=len(messages),
            )

        except SupabaseServiceError as e:
            logger.error(
                "Database error in /continue",
                user_id=str(interaction.user.id),
                conversation_id=conversation_id,
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 無法載入對話，請稍後再試。",
                ephemeral=True,
            )
        except Exception as e:
            logger.critical(
                "Unexpected error in /continue",
                user_id=str(interaction.user.id),
                conversation_id=conversation_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。",
                ephemeral=True,
            )

    # ------------------------------------------------------------------
    # /search
    # ------------------------------------------------------------------

    @app_commands.command(name="search", description="搜尋歷史對話")
    @app_commands.describe(query="搜尋關鍵字")
    async def search(self, interaction: discord.Interaction, query: str) -> None:
        """Search conversations and messages for the given query."""
        logger.info(
            "Command /search triggered",
            user_id=str(interaction.user.id),
            query=query,
            command="search",
        )
        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            user_uuid = await self._get_user_uuid(interaction)
            if user_uuid is None:
                return

            results = await self.search_service.search_conversations(
                user_id=user_uuid,
                query=query,
                filters=SearchFilters(),
                limit=_MAX_SEARCH_RESULTS,
            )

            if not results:
                await interaction.followup.send(
                    f"🔍 找不到包含「{query}」的對話。\n" "💡 試試不同的關鍵字，或使用 `/conversations` 瀏覽所有對話。",
                    ephemeral=True,
                )
                return

            lines = [
                f"🔍 **搜尋結果：「{query}」**",
                f"找到 {len(results)} 個相關對話\n",
            ]

            for i, result in enumerate(results, 1):
                platform_emoji = "🌐" if result.platform == "web" else "💬"
                score_pct = int(result.relevance_score * 100)
                last_msg = result.last_message_at.strftime("%Y-%m-%d")
                title = result.title
                conv_id = result.conversation_id

                # Build snippet from highlight_snippets or matched_content
                snippet = ""
                if result.highlight_snippets:
                    raw_snippet = result.highlight_snippets[0]
                    # Strip <mark> tags for Discord display
                    import re

                    raw_snippet = re.sub(r"</?mark>", "**", raw_snippet)
                    snippet = raw_snippet[:150] + ("..." if len(raw_snippet) > 150 else "")
                elif result.matched_content:
                    snippet = result.matched_content[0][:150] + (
                        "..." if len(result.matched_content[0]) > 150 else ""
                    )

                entry_lines = [
                    f"**{i}.** {platform_emoji} {title}",
                    f"   🆔 `{conv_id[:8]}...`  📊 相關度 {score_pct}%  📅 {last_msg}",
                ]
                if snippet:
                    entry_lines.append(f"   💬 _{snippet}_")
                entry_lines.append("")

                entry = "\n".join(entry_lines)
                test = "\n".join(lines) + entry
                if len(test) > _DISCORD_CHAR_LIMIT - _RESERVED_CHARS:
                    lines.append("_...更多結果已省略_")
                    break
                lines.append(entry)

            lines.append("💡 使用 `/continue <id>` 繼續對話")

            await interaction.followup.send(
                content="\n".join(lines),
                ephemeral=True,
            )
            logger.info(
                "Successfully sent /search response",
                user_id=str(interaction.user.id),
                query=query,
                result_count=len(results),
            )

        except SupabaseServiceError as e:
            logger.error(
                "Database error in /search",
                user_id=str(interaction.user.id),
                query=query,
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 搜尋失敗，請稍後再試。",
                ephemeral=True,
            )
        except Exception as e:
            logger.critical(
                "Unexpected error in /search",
                user_id=str(interaction.user.id),
                query=query,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。",
                ephemeral=True,
            )

    # ------------------------------------------------------------------
    # /link
    # ------------------------------------------------------------------

    @app_commands.command(name="link", description="綁定 Discord 帳號到系統帳號")
    @app_commands.describe(code="6 位數驗證碼（從 Web 界面取得）")
    async def link(self, interaction: discord.Interaction, code: str) -> None:
        """Link the Discord account to a system account using a verification code."""
        logger.info(
            "Command /link triggered",
            user_id=str(interaction.user.id),
            command="link",
        )
        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            # Validate code format: must be exactly 6 digits
            if not code.isdigit() or len(code) != 6:
                await interaction.followup.send(
                    "❌ 驗證碼格式錯誤。\n" "💡 驗證碼應為 6 位數字，請從 Web 界面取得。",
                    ephemeral=True,
                )
                return

            # Ensure the Discord user is registered in the system
            user_uuid = await self._get_user_uuid(interaction)
            if user_uuid is None:
                return

            discord_user_id = str(interaction.user.id)

            # Attempt to link the platform account
            result = await self.identity_manager.link_platform_account(
                user_id=str(user_uuid),
                platform="discord",
                platform_user_id=discord_user_id,
                verification_token=code,
            )

            if result.success:
                await interaction.followup.send(
                    "✅ **帳號綁定成功！**\n\n"
                    f"你的 Discord 帳號（`{interaction.user}`）已成功綁定到系統帳號。\n"
                    "現在你可以在 Web 和 Discord 之間無縫切換對話了！",
                    ephemeral=True,
                )
                logger.info(
                    "Account linked successfully",
                    user_id=discord_user_id,
                    user_uuid=str(user_uuid),
                )
            else:
                error_msg = result.error or "未知錯誤"
                await interaction.followup.send(
                    f"❌ **帳號綁定失敗**\n\n"
                    f"原因：{error_msg}\n\n"
                    "💡 請確認：\n"
                    "• 驗證碼是否正確且未過期（10 分鐘內有效）\n"
                    "• 請從 Web 界面重新取得驗證碼",
                    ephemeral=True,
                )
                logger.warning(
                    "Account linking failed",
                    user_id=discord_user_id,
                    error=error_msg,
                )

        except SupabaseServiceError as e:
            logger.error(
                "Database error in /link",
                user_id=str(interaction.user.id),
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 綁定失敗，請稍後再試。",
                ephemeral=True,
            )
        except Exception as e:
            logger.critical(
                "Unexpected error in /link",
                user_id=str(interaction.user.id),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。",
                ephemeral=True,
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_user_uuid(self, interaction: discord.Interaction):
        """Register the Discord user and return their system UUID.

        Sends an ephemeral error message and returns ``None`` if registration
        fails, so callers can simply check for ``None`` and return early.

        Args:
            interaction: The Discord interaction (must already be deferred).

        Returns:
            The user's UUID string, or ``None`` on failure.
        """
        try:
            return await ensure_user_registered(interaction)
        except SupabaseServiceError as e:
            logger.error(
                "User registration failed",
                user_id=str(interaction.user.id),
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 無法驗證使用者身份，請稍後再試。",
                ephemeral=True,
            )
            return None


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


async def setup(bot: commands.Bot) -> None:
    """Load the ConversationCommands cog with injected service dependencies."""
    supabase_service = SupabaseService()
    client = supabase_service.client

    conversation_repo = ConversationRepository(client)
    message_repo = MessageRepository(client)
    search_service = ConversationSearchService(conversation_repo, message_repo)
    identity_manager = UserIdentityManager(client)

    await bot.add_cog(
        ConversationCommands(
            bot,
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            search_service=search_service,
            identity_manager=identity_manager,
            supabase_service=supabase_service,
        )
    )
