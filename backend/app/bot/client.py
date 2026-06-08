import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class TechNewsBot(commands.Bot):
    def __init__(self):
        # Intents are required for reading messages (if we want to expand) and syncing trees
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents, help_command=None, max_messages=50)

    async def setup_hook(self):
        """Called automatically inside bot.start() before login."""
        # Load cogs dynamically
        logger.info("Loading Discord Cogs...")
        await self.load_extension("app.bot.cogs.news_commands")
        await self.load_extension("app.bot.cogs.interactions")
        await self.load_extension("app.bot.cogs.reading_list")
        await self.load_extension("app.bot.cogs.subscription_commands")
        await self.load_extension("app.bot.cogs.notification_settings")
        await self.load_extension("app.bot.cogs.quiet_hours_settings")
        await self.load_extension("app.bot.cogs.admin_commands")
        await self.load_extension("app.bot.cogs.conversation_commands")
        await self.load_extension("app.bot.cogs.conversation_auto_manager")
        await self.load_extension("app.bot.cogs.qa_commands")
        await self.load_extension("app.bot.cogs.thread_qa_listener")
        await self.load_extension("app.bot.cogs.proactive_dm")
        await self.load_extension("app.bot.cogs.dm_conversation_listener")

        # Register persistent views that survive bot restarts
        logger.info("Registering persistent views...")
        try:
            from app.bot.cogs.persistent_views import (
                PersistentDeepDiveButton,
                PersistentDigestRatingSelect,
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

            digest_rating_view = discord.ui.View(timeout=None)
            digest_rating_view.add_item(PersistentDigestRatingSelect())
            self.add_view(digest_rating_view)

            logger.info("Successfully registered 5 persistent view types")
        except Exception as e:
            logger.error(f"Failed to register persistent views: {e}", exc_info=True)

    async def on_interaction(self, interaction: discord.Interaction):
        """Intercept component interactions to route them to persistent/stateless handlers."""
        # Dev guild isolation check: if running locally in dev mode (enable_dm_listener is False),
        # ignore interactions from other servers to avoid competing with production bot.
        try:
            from app.core.config import get_settings

            settings = get_settings()
            if not settings.enable_dm_listener and interaction.guild_id:
                if not settings.dev_guild_id or interaction.guild_id != int(settings.dev_guild_id):
                    logger.debug(
                        f"Ignoring guild interaction from {interaction.guild_id} in local dev mode due to dev_guild_id isolation."
                    )
                    return
        except Exception as e:
            logger.warning(f"Error during dev guild isolation check: {e}")

        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get("custom_id", "")
            if custom_id:
                # 1. Stateless Pagination & Filter Route (ALWAYS handled statelessly to bypass in-memory dynamic bugs)
                if custom_id.startswith("news_prev:") or custom_id.startswith("news_next:"):
                    try:
                        from app.bot.cogs.news_commands import handle_stateless_news_pagination

                        await handle_stateless_news_pagination(interaction, custom_id)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in stateless news pagination button callback: {e}",
                            exc_info=True,
                        )

                elif custom_id == "news_filter":
                    try:
                        from app.bot.cogs.news_commands import handle_stateless_news_pagination

                        await handle_stateless_news_pagination(interaction, custom_id)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in stateless news pagination select callback: {e}",
                            exc_info=True,
                        )

                elif custom_id == "news_read_later_select":
                    try:
                        from app.bot.cogs.interactions import ReadLaterSelect

                        select = ReadLaterSelect([])
                        select._values = interaction.data.get("values", [])
                        await select.callback(interaction)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in stateless news_read_later_select callback: {e}",
                            exc_info=True,
                        )

                elif custom_id == "news_mark_read_select":
                    try:
                        from app.bot.cogs.interactions import MarkReadSelect

                        select = MarkReadSelect([])
                        select._values = interaction.data.get("values", [])
                        await select.callback(interaction)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in stateless news_mark_read_select callback: {e}",
                            exc_info=True,
                        )

                elif custom_id == "news_deep_dive_select":
                    try:
                        from app.bot.cogs.interactions import DeepDiveSelect

                        select = DeepDiveSelect([])
                        select._values = interaction.data.get("values", [])
                        await select.callback(interaction)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in stateless news_deep_dive_select callback: {e}",
                            exc_info=True,
                        )

                elif custom_id == "reading_list_mark_read_select":
                    try:
                        from app.bot.cogs.reading_list import ReadingListMarkReadSelect

                        select = ReadingListMarkReadSelect([])
                        select._values = interaction.data.get("values", [])
                        await select.callback(interaction)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in stateless reading_list_mark_read_select callback: {e}",
                            exc_info=True,
                        )

                elif custom_id == "reading_list_remove_select":
                    try:
                        from app.bot.cogs.reading_list import ReadingListRemoveSelect

                        select = ReadingListRemoveSelect([])
                        select._values = interaction.data.get("values", [])
                        await select.callback(interaction)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in stateless reading_list_remove_select callback: {e}",
                            exc_info=True,
                        )

                elif custom_id == "settings_toggle_notifications":
                    try:
                        from app.bot.cogs.notification_settings import (
                            NotificationSettingsControlView,
                        )

                        view = NotificationSettingsControlView(True)
                        await view._toggle_callback(interaction)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in stateless settings_toggle_notifications callback: {e}",
                            exc_info=True,
                        )

                elif custom_id == "settings_configure_quiet_hours":
                    try:
                        from app.bot.cogs.notification_settings import (
                            NotificationSettingsControlView,
                        )

                        view = NotificationSettingsControlView(True)
                        await view._quiet_hours_callback(interaction)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in stateless settings_configure_quiet_hours callback: {e}",
                            exc_info=True,
                        )

                elif custom_id == "settings_frequency_select":
                    try:
                        from app.bot.cogs.notification_settings import NotificationFrequencySelect

                        select = NotificationFrequencySelect(1)
                        select._values = interaction.data.get("values", [])
                        await select.callback(interaction)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in stateless settings_frequency_select callback: {e}",
                            exc_info=True,
                        )

                elif custom_id == "settings_timezone_select":
                    try:
                        from app.bot.cogs.notification_settings import NotificationTimezoneSelect

                        select = NotificationTimezoneSelect(2)
                        select._values = interaction.data.get("values", [])
                        await select.callback(interaction)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in stateless settings_timezone_select callback: {e}",
                            exc_info=True,
                        )

                elif custom_id == "subscription_unsubscribe_select":
                    try:
                        from app.bot.cogs.subscription_commands import UnsubscribeFeedSelect

                        select = UnsubscribeFeedSelect([])
                        select._values = interaction.data.get("values", [])
                        await select.callback(interaction)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in stateless subscription_unsubscribe_select callback: {e}",
                            exc_info=True,
                        )

                elif custom_id.startswith("rate_article:"):
                    try:
                        from app.services.supabase_service import SupabaseService

                        supabase_service = SupabaseService()

                        parts = custom_id.split(":")
                        article_id = parts[1]
                        rating = int(parts[2])
                        discord_id = str(interaction.user.id)

                        # Self-healing update
                        try:
                            await supabase_service.update_article_rating(
                                discord_id, article_id, rating
                            )
                        except Exception:
                            await supabase_service.save_to_reading_list(
                                discord_id, article_id, "discord"
                            )
                            await supabase_service.update_article_status(
                                discord_id, article_id, "Read"
                            )
                            await supabase_service.update_article_rating(
                                discord_id, article_id, rating
                            )

                        # Respond immediately to edit the message and remove buttons
                        await interaction.response.edit_message(
                            content=f"✅ 已評為 {rating} 星！{'⭐' * rating} 該文章已成功存入您的永久優質收藏。", view=None
                        )
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in stateless rate_article callback: {e}", exc_info=True
                        )
                        try:
                            await interaction.response.send_message("❌ 評分失敗，請稍後再試。", ephemeral=True)
                        except Exception:
                            await interaction.followup.send("❌ 評分失敗，請稍後再試。", ephemeral=True)
                        return

                elif custom_id.startswith("rate_article_skip:"):
                    try:
                        parts = custom_id.split(":")
                        article_id = parts[1]

                        # Respond immediately to edit the message and remove buttons
                        await interaction.response.edit_message(content="已標記為已讀（不評分）。", view=None)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in stateless rate_article_skip callback: {e}", exc_info=True
                        )
                        try:
                            await interaction.response.send_message("❌ 操作失敗，請稍後再試。", ephemeral=True)
                        except Exception:
                            await interaction.followup.send("❌ 操作失敗，請稍後再試。", ephemeral=True)
                        return

                # 2. In-memory views check (Only check active view in memory for other components)
                view_store = self._connection._view_store
                message_id = interaction.message.id if interaction.message else None

                # If the message has an active view in memory, let discord.py handle it
                if message_id and message_id in view_store._views:
                    await super().on_interaction(interaction)
                    return

                # If the exact custom_id is registered as a persistent view, let discord.py handle it
                if custom_id in view_store._synced_views:
                    await super().on_interaction(interaction)
                    return

                # Route matching prefixes to persistent callbacks
                if custom_id.startswith("read_later_") and not custom_id.endswith("persistent"):
                    try:
                        from app.bot.cogs.persistent_views import PersistentReadLaterButton

                        btn = PersistentReadLaterButton()
                        await btn.callback(interaction)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in intercepted PersistentReadLaterButton: {e}", exc_info=True
                        )

                elif custom_id.startswith("mark_read_") and not custom_id.endswith("persistent"):
                    try:
                        from app.bot.cogs.persistent_views import PersistentMarkReadButton

                        btn = PersistentMarkReadButton()
                        await btn.callback(interaction)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in intercepted PersistentMarkReadButton: {e}", exc_info=True
                        )

                elif (
                    custom_id.startswith("rate_")
                    and not custom_id.startswith("rate_persistent")
                    and not custom_id.startswith("digest_rate_")
                ):
                    try:
                        from app.bot.cogs.persistent_views import PersistentRatingSelect

                        select = PersistentRatingSelect()
                        select._values = interaction.data.get("values", [])
                        await select.callback(interaction)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in intercepted PersistentRatingSelect: {e}", exc_info=True
                        )

                elif custom_id.startswith("deep_dive_") and not custom_id.endswith("persistent"):
                    try:
                        from app.bot.cogs.persistent_views import PersistentDeepDiveButton

                        btn = PersistentDeepDiveButton()
                        await btn.callback(interaction)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in intercepted PersistentDeepDiveButton: {e}", exc_info=True
                        )

                elif custom_id.startswith("digest_rate_") and not custom_id.endswith("persistent"):
                    try:
                        from app.bot.cogs.persistent_views import PersistentDigestRatingSelect

                        select = PersistentDigestRatingSelect()
                        select._values = interaction.data.get("values", [])
                        await select.callback(interaction)
                        return
                    except Exception as e:
                        logger.error(
                            f"Error in intercepted PersistentDigestRatingSelect: {e}", exc_info=True
                        )

                elif custom_id.startswith("proactive_fb_"):
                    try:
                        parts = custom_id.split("_")
                        if len(parts) >= 5:
                            direction = parts[2]
                            user_id = parts[3]
                            category = "_".join(parts[4:])

                            await interaction.response.defer(ephemeral=True)

                            from app.bot.cogs.proactive_dm import FEEDBACK_DELTA
                            from app.qa_agent.proactive_learning.preference_model import (
                                PreferenceModel,
                            )

                            positive = direction == "up"
                            delta = FEEDBACK_DELTA if positive else -FEEDBACK_DELTA

                            pref = PreferenceModel()
                            await pref.apply_adjustments(user_id, {category: delta})

                            # Remove buttons after successful feedback
                            try:
                                await interaction.message.edit(view=None)
                            except Exception:
                                pass

                            dir_text = "增加" if positive else "減少"
                            await interaction.followup.send(
                                f"✅ 已記錄，會{dir_text} **{category}** 的推薦頻率。",
                                ephemeral=True,
                            )
                            return
                        else:
                            logger.error(f"Invalid proactive_fb_ custom_id format: {custom_id}")
                    except Exception as e:
                        logger.error(
                            f"Error in stateless proactive_fb_ callback: {e}", exc_info=True
                        )
                        try:
                            await interaction.followup.send("❌ 處理偏好時發生錯誤，請稍後再試。", ephemeral=True)
                        except Exception:
                            pass
                        return

        await super().on_interaction(interaction)

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        # Sync the command tree to Discord (makes slash commands visible)
        try:
            from app.core.config import get_settings

            settings = get_settings()
            if settings.dev_guild_id:
                guild = discord.Object(id=int(settings.dev_guild_id))
                self.tree.copy_global_to(guild=guild)
                coro = self.tree.sync(guild=guild)
                if coro is not None:
                    synced = await coro
                    logger.info(
                        f"Synced {len(synced)} command(s) to dev guild {settings.dev_guild_id}."
                    )
                else:
                    logger.warning("tree.sync(guild=...) returned None — skipping guild sync.")
            else:
                coro = self.tree.sync()
                if coro is not None:
                    synced = await coro
                    logger.info(f"Successfully synced {len(synced)} slash command(s).")
                else:
                    logger.warning("tree.sync() returned None — skipping global sync.")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")
        logger.info("Discord Bot is fully ready and listening.")


# Singleton instance
bot = TechNewsBot()
