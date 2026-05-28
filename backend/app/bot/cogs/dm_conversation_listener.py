"""
DM Conversation Listener

Handles Discord DM messages with intent detection:
- Questions → QA agent answers + stores preference signals
- Preference statements → stores to dm_conversations, no LLM call
- Other → brief reply with usage hint

Token-efficient: only questions trigger LLM calls.
Requirements: dm-conversation-memory §1, §4
"""

import logging
import re

import discord
from discord.ext import commands

from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

# Keywords that indicate a question / article query
_QUESTION_PATTERNS = re.compile(
    r"[?？]|什麼|怎麼|如何|有沒有|推薦|介紹|解釋|告訴我|幫我找"
    r"|最近.*文章|有什麼.*關於|關於.*文章|哪些.*文章|找.*文章"
    r"|最新|新聞|資訊|教學|文章|新的|有哪些|哪裡|為什麼|誰|何時",
    re.IGNORECASE,
)

# Keywords that indicate preference statements (store only, no LLM)
_PREFERENCE_PATTERNS = re.compile(
    r"我喜歡|我不喜歡|我想看|我偏好|我對.*感興趣|不想看|希望多|希望少",
    re.IGNORECASE,
)

_HINT_INTERVAL = 5  # Show usage hint every N messages
_user_message_counts: dict[str, int] = {}

_USAGE_HINT = (
    "\n\n💡 **你可以：**\n"
    "• 直接問我問題，例如「最近有什麼 Rust 文章？」\n"
    "• 告訴我偏好，例如「我喜歡系統設計，不喜歡入門教學」\n"
    "• `/update_profile` 更新偏好摘要\n"
    "• `/recommend_now` 立即獲取個人化推薦\n"
    "• `/my_profile` 查看你的偏好檔案"
)


def _should_show_hint(discord_id: str) -> bool:
    count = _user_message_counts.get(discord_id, 0) + 1
    _user_message_counts[discord_id] = count
    return count % _HINT_INTERVAL == 1  # Show on 1st, 6th, 11th... message


class DMConversationListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        supabase = SupabaseService()
        self._conv_repo = ConversationRepository(supabase.client)
        self._msg_repo = MessageRepository(supabase.client)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if not isinstance(message.channel, discord.DMChannel):
            return
        if message.content.startswith("/"):
            return

        discord_id = str(message.author.id)
        content = message.content.strip()
        if not content:
            return

        supabase = SupabaseService()
        try:
            user = await supabase.get_user_by_discord_id(discord_id)
            if not user:
                return
            user_id = user["id"]
        except Exception as exc:
            logger.error("Failed to resolve user %s: %s", discord_id, exc)
            return

        show_hint = _should_show_hint(discord_id)

        # Get active conversation ID or create a new one
        from uuid import uuid4

        conv_id = await self._get_active_conversation_id(user_id)
        if not conv_id:
            from app.api._qa_helpers import _create_conversation_in_db

            try:
                conv_id = await _create_conversation_in_db(user_id, title="Discord DM 對話")
            except Exception as e:
                logger.warning(f"Failed to create new conversation for Discord DM: {e}")
                conv_id = str(uuid4())

        from app.api._qa_helpers import _process_query_with_intent, _save_messages_to_db

        reply = ""
        async with message.channel.typing():
            try:
                # Store raw user message in dm_conversations table
                await self._store_dm(supabase, user_id, content)

                # Process query using context-aware agent dispatcher
                qa_response = await _process_query_with_intent(user_id, content, conv_id)

                # Formulate reply format
                if qa_response.articles:
                    lines = [f"📚 **{qa_response.insights[0] if qa_response.insights else '相關文章'}**"]
                    for i, a in enumerate(qa_response.articles, 1):
                        title = (a.title or "")[:60]
                        url = str(a.url) if a.url else ""
                        summary = (getattr(a, "summary", getattr(a, "ai_summary", "")) or "")[:120]
                        lines.append(f"\n**{i}. {title}**")
                        if url:
                            lines.append(f"🔗 {url}")
                        if summary:
                            lines.append(f"_{summary.strip()}..._")
                    reply = "\n".join(lines)
                else:
                    reply = qa_response.insights[0] if qa_response.insights else "已處理您的查詢。"

                if len(reply) > 1900:
                    reply = reply[:1900] + "..."
                if show_hint:
                    reply += _USAGE_HINT

                await message.reply(reply, mention_author=False)

                # Save history turns
                try:
                    await _save_messages_to_db(conv_id, content, qa_response)
                except Exception as e:
                    logger.warning(f"Failed to save DM messages to DB: {e}")

            except Exception as exc:
                logger.error("Failed to process DM conversation: %s", exc)
                reply = "抱歉，查詢時發生錯誤，請稍後再試。"
                await message.reply(reply, mention_author=False)

    async def _store_dm(self, supabase: SupabaseService, user_id: str, content: str) -> None:
        try:
            supabase.client.table("dm_conversations").insert(
                {"user_id": user_id, "content": content}
            ).execute()
        except Exception as exc:
            logger.error("Failed to store DM conversation: %s", exc)

    async def _get_active_conversation_id(self, user_id: str) -> str | None:
        """Find the most recent discord conversation for this user."""
        try:
            from app.repositories.conversation import ConversationFilters

            convs = await self._conv_repo.list_conversations(
                user_id=user_id,
                filters=ConversationFilters(limit=1, offset=0),
            )
            if convs:
                return str(convs[0].id)
        except Exception as exc:
            logger.warning("Could not fetch active conversation: %s", exc)
        return None

    async def _save_assistant_message(self, user_id: str, content: str) -> None:
        """Save bot reply as assistant message so it appears in web chat."""
        conv_id = await self._get_active_conversation_id(user_id)
        if not conv_id:
            return
        try:
            await self._msg_repo.add_message(
                conversation_id=conv_id,
                role="assistant",
                content=content,
                platform="discord",
            )
        except Exception as exc:
            logger.warning("Failed to save assistant message: %s", exc)


async def setup(bot: commands.Bot) -> None:
    from app.core.config import settings

    if getattr(settings, "enable_dm_listener", True):
        await bot.add_cog(DMConversationListener(bot))
    else:
        logger.info("DM conversation listener disabled via ENABLE_DM_LISTENER=false")
