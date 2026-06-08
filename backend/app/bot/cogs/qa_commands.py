"""
Discord Bot Q&A Commands

Provides slash command for querying the intelligent Q&A agent:
- /ask <question> - Ask a question about your subscribed articles
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from app.bot.utils.decorators import ensure_user_registered
from app.bot.utils.thread_utils import ensure_discussion_thread
from app.core.exceptions import SupabaseServiceError
from app.core.logger import get_logger
from app.services.thread_memory_service import ThreadMemoryService

logger = get_logger(__name__)

_DISCORD_CHAR_LIMIT = 2000


def _chunk_content(content: str, max_len: int = _DISCORD_CHAR_LIMIT) -> list[str]:
    if len(content) <= max_len:
        return [content]
    chunks: list[str] = []
    remaining = content
    while remaining:
        chunks.append(remaining[:max_len])
        remaining = remaining[max_len:]
    return chunks


class QACommands(commands.Cog):
    """Intelligent Q&A commands cog."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ask", description="用自然語言詢問你訂閱文章庫中的問題")
    @app_commands.describe(question="你想問的問題（支援中文和英文）")
    async def ask(self, interaction: discord.Interaction, question: str):
        logger.info("Command /ask triggered", user_id=str(interaction.user.id), query=question[:50])
        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            user_uuid = await ensure_user_registered(interaction)
        except SupabaseServiceError as e:
            logger.error("User registration failed", user_id=str(interaction.user.id), error=str(e))
            await interaction.followup.send("❌ 無法驗證使用者，請稍後再試。", ephemeral=True)
            return

        try:
            thread, created = await ensure_discussion_thread(
                interaction=interaction,
                thread_name=f"ask-{question[:40]}",
            )

            if created:
                await interaction.followup.send(
                    f"✅ 已建立問答討論串：{thread.mention}\n我會在討論串內回覆你。",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send("✅ 已在此討論串處理你的問題。", ephemeral=True)

            await thread.send(f"❓ **問題**：{question}")
            memory_service = ThreadMemoryService()
            result = await memory_service.process_thread_query(
                user_id=str(user_uuid),
                thread_id=str(thread.id),
                query=question,
                title=getattr(thread, "name", None) or f"Ask {question[:30]}",
            )

            for chunk in _chunk_content(result["answer"]):
                await thread.send(chunk)

        except Exception as e:
            logger.error(
                "Error in /ask command",
                user_id=str(interaction.user.id),
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 無法處理你的問題，請稍後再試。\n" "💡 提示：嘗試更具體的問題，例如「最近有什麼關於 AI 的文章？」",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(QACommands(bot))
