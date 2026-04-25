"""
Discord Bot Q&A Commands

Provides slash command for querying the intelligent Q&A agent:
- /ask <question> - Ask a question about your subscribed articles
"""

from __future__ import annotations

from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from app.bot.utils.decorators import ensure_user_registered
from app.core.exceptions import SupabaseServiceError
from app.core.logger import get_logger
from app.qa_agent import QAAgentController

logger = get_logger(__name__)

_DISCORD_CHAR_LIMIT = 2000


def _format_response(response) -> str:
    """Format a StructuredResponse into a Discord message."""
    lines = []

    if response.articles:
        lines.append("📚 **相關文章**")
        for i, article in enumerate(response.articles[:5], 1):
            title = article.title[:60] + "..." if len(article.title) > 60 else article.title
            lines.append(f"{i}. **{title}**")
            lines.append(f"   🔗 {article.url}")
            if article.summary:
                snippet = (
                    article.summary[:120] + "..." if len(article.summary) > 120 else article.summary
                )
                lines.append(f"   _{snippet}_")
        lines.append("")

    if response.insights:
        lines.append("💡 **洞察**")
        for insight in response.insights[:3]:
            lines.append(f"• {insight}")
        lines.append("")

    if response.recommendations:
        lines.append("📖 **延伸閱讀建議**")
        for rec in response.recommendations[:3]:
            lines.append(f"• {rec}")

    if not lines:
        lines.append("🔍 找不到相關文章，請嘗試換個問法或訂閱更多 RSS 來源。")

    content = "\n".join(lines)
    if len(content) > _DISCORD_CHAR_LIMIT:
        content = content[: _DISCORD_CHAR_LIMIT - 3] + "..."
    return content


class QACommands(commands.Cog):
    """Intelligent Q&A commands cog."""

    def __init__(self, bot: commands.Bot, qa_controller: Optional[QAAgentController] = None):
        self.bot = bot
        self._qa_controller = qa_controller

    def _get_controller(self) -> QAAgentController:
        if self._qa_controller is None:
            self._qa_controller = QAAgentController()
        return self._qa_controller

    @app_commands.command(name="ask", description="用自然語言詢問你訂閱文章庫中的問題")
    @app_commands.describe(question="你想問的問題（支援中文和英文）")
    async def ask(self, interaction: discord.Interaction, question: str):
        logger.info("Command /ask triggered", user_id=str(interaction.user.id), query=question[:50])
        await interaction.response.defer(thinking=True)

        try:
            user_uuid = await ensure_user_registered(interaction)
        except SupabaseServiceError as e:
            logger.error("User registration failed", user_id=str(interaction.user.id), error=str(e))
            await interaction.followup.send("❌ 無法驗證使用者，請稍後再試。", ephemeral=True)
            return

        try:
            controller = self._get_controller()
            response = await controller.process_query(
                user_id=str(user_uuid),
                query=question,
            )
            content = _format_response(response)
            await interaction.followup.send(content=content)

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
