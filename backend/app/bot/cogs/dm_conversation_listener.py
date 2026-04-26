"""
DM Conversation Listener

Listens for user messages in Discord DMs, stores them as preference signals.
Requirements: dm-conversation-memory §1
"""

import logging

import discord
from discord.ext import commands

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class DMConversationListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # Only handle DMs, ignore bot messages and commands
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
            # Resolve internal user_id
            user = await supabase.get_user_by_discord_id(discord_id)
            if not user:
                return
            user_id = user["id"]

            supabase.client.table("dm_conversations").insert(
                {"user_id": user_id, "content": content}
            ).execute()
            logger.info("Stored DM conversation for user %s", discord_id)
        except Exception as exc:
            logger.error("Failed to store DM conversation for %s: %s", discord_id, exc)
            return

        await message.reply("已記錄，這會幫助我更了解你的偏好 👍", mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DMConversationListener(bot))
