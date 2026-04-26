import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class TechNewsBot(commands.Bot):
    def __init__(self):
        # Intents are required for reading messages (if we want to expand) and syncing trees
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        """Called automatically inside bot.start() before login."""
        # Load cogs dynamically
        logger.info("Loading Discord Cogs...")
        await self.load_extension("app.bot.cogs.news_commands")
        await self.load_extension("app.bot.cogs.interactions")
        await self.load_extension("app.bot.cogs.reading_list")
        await self.load_extension("app.bot.cogs.subscription_commands")
        await self.load_extension("app.bot.cogs.notification_settings")
        await self.load_extension("app.bot.cogs.admin_commands")
        await self.load_extension("app.bot.cogs.conversation_commands")
        await self.load_extension("app.bot.cogs.conversation_auto_manager")
        await self.load_extension("app.bot.cogs.qa_commands")
        await self.load_extension("app.bot.cogs.proactive_dm")

        # Register persistent views that survive bot restarts
        logger.info("Registering persistent views...")
        try:
            from app.bot.cogs.persistent_views import (
                PersistentDeepDiveButton,
                PersistentMarkReadButton,
                PersistentRatingSelect,
                PersistentReadLaterButton,
            )

            # Create a persistent view for each button/select type
            # These will handle interactions even after bot restart
            read_later_view = discord.ui.View(timeout=None)
            read_later_view.add_item(PersistentReadLaterButton())
            self.add_view(read_later_view)

            mark_read_view = discord.ui.View(timeout=None)
            mark_read_view.add_item(PersistentMarkReadButton())
            self.add_view(mark_read_view)

            rating_view = discord.ui.View(timeout=None)
            rating_view.add_item(PersistentRatingSelect())
            self.add_view(rating_view)

            deep_dive_view = discord.ui.View(timeout=None)
            deep_dive_view.add_item(PersistentDeepDiveButton())
            self.add_view(deep_dive_view)

            logger.info("Successfully registered 4 persistent view types")
        except Exception as e:
            logger.error(f"Failed to register persistent views: {e}", exc_info=True)

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        # Sync the command tree to Discord (makes slash commands visible)
        try:
            synced = await self.tree.sync()
            logger.info(f"Successfully synced {len(synced)} slash command(s).")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")
        logger.info("Discord Bot is fully ready and listening.")


# Singleton instance
bot = TechNewsBot()
