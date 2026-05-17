"""Discord Thread QA listener.

Handles follow-up messages inside Discord threads created by /ask and deep-dive actions.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from app.core.logger import get_logger
from app.services.supabase_service import SupabaseService
from app.services.thread_memory_service import ThreadMemoryService

logger = get_logger(__name__)


def _chunk_content(content: str, max_len: int = 2000) -> list[str]:
    if len(content) <= max_len:
        return [content]
    return [content[i : i + max_len] for i in range(0, len(content), max_len)]


class ThreadQAListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.supabase_service = SupabaseService()
        self.memory_service = ThreadMemoryService(supabase_service=self.supabase_service)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if not isinstance(message.channel, discord.Thread):
            return
        if message.content.startswith("/"):
            return

        user = await self.supabase_service.get_user_by_discord_id(str(message.author.id))
        if not user:
            return
        user_id = str(user["id"])
        thread_id = str(message.channel.id)

        # Avoid hijacking unrelated threads: require an existing conversation mapping.
        existing = await self.memory_service._conversation_repo.get_conversation_by_thread_id(
            user_id=user_id,
            thread_id=thread_id,
        )
        if not existing:
            return

        async with message.channel.typing():
            try:
                result = await self.memory_service.process_thread_query(
                    user_id=user_id,
                    thread_id=thread_id,
                    query=message.content.strip(),
                    title=message.channel.name or "Thread QA",
                )
                answer = result["answer"]
                first = True
                for chunk in _chunk_content(answer):
                    if first:
                        await message.reply(chunk, mention_author=False)
                        first = False
                    else:
                        await message.channel.send(chunk)
            except Exception as exc:
                logger.error("Thread QA handling failed: %s", exc, exc_info=True)
                await message.reply("❌ 目前無法處理此問題，請稍後再試。", mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ThreadQAListener(bot))
