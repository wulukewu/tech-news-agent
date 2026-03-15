import logging
import discord
from discord.ext import commands
from app.core.config import settings

logger = logging.getLogger(__name__)

class TechNewsBot(commands.Bot):
    def __init__(self):
        # Intents are required for reading messages (if we want to expand) and syncing trees
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        """Called automatically inside bot.start() before login."""
        # Load cogs dynamically
        logger.info("Loading Discord Cogs...")
        await self.load_extension("app.bot.cogs.news_commands")
        await self.load_extension("app.bot.cogs.interactions")
        
        # Sync the command tree to Discord (makes slash commands visible)
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash command(s).")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("Discord Bot is fully ready and listening.")

# Singleton instance
bot = TechNewsBot()
