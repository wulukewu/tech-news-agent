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
import uuid

import discord
from discord.ext import commands

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

# Keywords that indicate a question / article query
_QUESTION_PATTERNS = re.compile(
    r"[?？]|什麼|怎麼|如何|有沒有|推薦|介紹|解釋|告訴我|幫我找|最近.*文章|有什麼.*關於",
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

        # --- Intent detection ---
        if _QUESTION_PATTERNS.search(content):
            await self._handle_question(message, user_id, discord_id, content, supabase, show_hint)
        elif _PREFERENCE_PATTERNS.search(content):
            await self._handle_preference(
                message, user_id, discord_id, content, supabase, show_hint
            )
        else:
            # Ambiguous — store as preference signal and give a light reply
            await self._store_dm(supabase, user_id, content)
            reply = "已記錄 👍"
            if show_hint:
                reply += _USAGE_HINT
            await message.reply(reply, mention_author=False)

    async def _handle_question(
        self,
        message: discord.Message,
        user_id: str,
        discord_id: str,
        content: str,
        supabase: SupabaseService,
        show_hint: bool,
    ) -> None:
        """Route to QA agent and reply with results."""
        async with message.channel.typing():
            try:
                from app.qa_agent.simple_qa import SimpleQAAgent

                agent = SimpleQAAgent()
                response = await agent.process_query(
                    user_id=uuid.UUID(user_id),
                    query=content,
                )

                lines = []
                if response.articles:
                    lines.append("📚 **相關文章**")
                    for i, a in enumerate(response.articles[:3], 1):
                        title = a.get("title", "")[:60]
                        url = a.get("url", "")
                        summary = (a.get("summary") or a.get("ai_summary") or "")[:100]
                        lines.append(f"**{i}. {title}**")
                        if url:
                            lines.append(f"🔗 {url}")
                        if summary:
                            lines.append(f"_{summary}..._")
                    lines.append("")

                if response.insights:
                    lines.append("💡 " + response.insights[0])

                if not lines:
                    lines.append("找不到相關文章，試試換個關鍵字，或先訂閱更多 RSS 來源。")

                reply = "\n".join(lines)
                if len(reply) > 1900:
                    reply = reply[:1900] + "..."
                if show_hint:
                    reply += _USAGE_HINT

                await message.reply(reply, mention_author=False)

            except Exception as exc:
                logger.error("QA agent failed for %s: %s", discord_id, exc)
                await message.reply(
                    "抱歉，查詢時發生錯誤，請稍後再試。",
                    mention_author=False,
                )

        # Store as preference signal regardless
        await self._store_dm(supabase, user_id, content)

    async def _handle_preference(
        self,
        message: discord.Message,
        user_id: str,
        discord_id: str,
        content: str,
        supabase: SupabaseService,
        show_hint: bool,
    ) -> None:
        """Store preference and prompt user to update profile."""
        await self._store_dm(supabase, user_id, content)
        reply = "✅ 已記錄你的偏好！使用 `/update_profile` 更新摘要，下次推薦會更精準 🎯"
        if show_hint:
            reply += _USAGE_HINT
        await message.reply(reply, mention_author=False)

    async def _store_dm(self, supabase: SupabaseService, user_id: str, content: str) -> None:
        try:
            supabase.client.table("dm_conversations").insert(
                {"user_id": user_id, "content": content}
            ).execute()
        except Exception as exc:
            logger.error("Failed to store DM conversation: %s", exc)


async def setup(bot: commands.Bot) -> None:
    from app.core.config import settings

    if getattr(settings, "enable_dm_listener", True):
        await bot.add_cog(DMConversationListener(bot))
    else:
        logger.info("DM conversation listener disabled via ENABLE_DM_LISTENER=false")
