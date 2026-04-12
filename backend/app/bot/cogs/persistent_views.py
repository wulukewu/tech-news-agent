"""
Persistent views that survive bot restarts.

These views are registered in the bot's setup_hook with timeout=None.
They reconstruct their state from custom_id when interactions occur after a restart.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

import discord

from app.core.exceptions import SupabaseServiceError
from app.services.llm_service import LLMService
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


def parse_article_id_from_custom_id(custom_id: str, prefix: str) -> UUID:
    """
    Parse article_id from custom_id.

    Args:
        custom_id: The custom_id string (e.g., "read_later_123e4567-...")
        prefix: The expected prefix (e.g., "read_later_")

    Returns:
        UUID: The parsed article_id

    Raises:
        ValueError: If custom_id format is invalid or UUID is malformed
    """
    if not custom_id.startswith(prefix):
        raise ValueError(f"Invalid custom_id format: expected prefix '{prefix}', got '{custom_id}'")

    article_id_str = custom_id[len(prefix) :]
    return UUID(article_id_str)


def log_persistent_interaction(
    user_id: str,
    action: str,
    article_id: UUID,
    custom_id: str,
    success: bool = True,
    error: str = None,
):
    """
    Log persistent view interactions with comprehensive context.

    This helps track interactions that occur after bot restarts,
    including custom_id parsing, database operations, and error handling.

    Args:
        user_id: Discord user ID
        action: Action type (e.g., "read_later", "mark_read", "rate", "deep_dive")
        article_id: Article UUID
        custom_id: The full custom_id from the interaction
        success: Whether the operation succeeded
        error: Error message if operation failed
    """
    log_data = {
        "timestamp": datetime.now(UTC).isoformat(),
        "user_id": user_id,
        "action": action,
        "article_id": str(article_id),
        "custom_id": custom_id,
        "success": success,
        "interaction_type": "persistent_view",
    }

    if error:
        log_data["error"] = error
        logger.error(
            f"Persistent interaction failed: {action} | "
            f"User: {user_id} | Article: {article_id} | "
            f"Error: {error}",
            extra=log_data,
        )
    else:
        logger.info(
            f"Persistent interaction: {action} | "
            f"User: {user_id} | Article: {article_id} | "
            f"CustomID: {custom_id}",
            extra=log_data,
        )


class PersistentReadLaterButton(discord.ui.Button):
    """
    Persistent Read Later button that can be reconstructed after bot restart.
    The custom_id contains the article_id, allowing state reconstruction.
    """

    def __init__(self, supabase_service: SupabaseService = None):
        # Initialize with a placeholder - the actual custom_id will be set when added to a view
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="⭐ 稍後閱讀",
            custom_id="read_later_persistent",
        )
        self.supabase_service = supabase_service or SupabaseService()

    async def callback(self, interaction: discord.Interaction):
        """
        Handle button click after bot restart.

        This method:
        1. Parses article_id from custom_id
        2. Reloads necessary data from database
        3. Handles message context loss gracefully
        4. Logs the post-restart interaction
        """
        await interaction.response.defer(ephemeral=True)

        custom_id = interaction.data.get("custom_id", "")
        discord_id = str(interaction.user.id)

        try:
            # Parse article_id from custom_id (format: read_later_{uuid})
            article_id = parse_article_id_from_custom_id(custom_id, "read_later_")

            # Save to reading list (database operation) via service layer
            await self.supabase_service.save_to_reading_list(discord_id, article_id)

            # Disable the button (handle message context loss)
            self.disabled = True
            try:
                await interaction.message.edit(view=self.view)
            except discord.NotFound:
                # Original message was deleted - this is expected after bot restart
                logger.info(
                    f"Message not found when disabling button (likely deleted) | "
                    f"User: {discord_id} | Article: {article_id}"
                )
            except discord.HTTPException as e:
                # Other Discord API errors (rate limit, permissions, etc.)
                logger.warning(
                    f"Failed to edit message: {e} | " f"User: {discord_id} | Article: {article_id}"
                )

            # Send confirmation
            await interaction.followup.send("✅ 已加入閱讀清單！", ephemeral=True)

            # Log successful post-restart interaction
            log_persistent_interaction(
                user_id=discord_id,
                action="read_later",
                article_id=article_id,
                custom_id=custom_id,
                success=True,
            )

        except ValueError as e:
            # Invalid custom_id format or UUID
            error_msg = f"Invalid custom_id or UUID: {e}"
            log_persistent_interaction(
                user_id=discord_id,
                action="read_later",
                article_id=None,
                custom_id=custom_id,
                success=False,
                error=error_msg,
            )
            await interaction.followup.send("❌ 無效的按鈕 ID", ephemeral=True)
        except SupabaseServiceError as e:
            # Database operation failed
            error_msg = f"Database error: {e}"
            log_persistent_interaction(
                user_id=discord_id,
                action="read_later",
                article_id=None,
                custom_id=custom_id,
                success=False,
                error=error_msg,
            )
            await interaction.followup.send("❌ 儲存失敗，請稍後再試。", ephemeral=True)
        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error: {e}"
            logger.error(f"PersistentReadLaterButton error: {e}", exc_info=True)
            log_persistent_interaction(
                user_id=discord_id,
                action="read_later",
                article_id=None,
                custom_id=custom_id,
                success=False,
                error=error_msg,
            )
            await interaction.followup.send("❌ 儲存失敗，請稍後再試。", ephemeral=True)


class PersistentMarkReadButton(discord.ui.Button):
    """
    Persistent Mark Read button that can be reconstructed after bot restart.
    """

    def __init__(self, supabase_service: SupabaseService = None):
        super().__init__(
            style=discord.ButtonStyle.success, label="✅ 標記已讀", custom_id="mark_read_persistent"
        )
        self.supabase_service = supabase_service or SupabaseService()

    async def callback(self, interaction: discord.Interaction):
        """
        Handle button click after bot restart.

        This method:
        1. Parses article_id from custom_id
        2. Updates article status in database
        3. Handles message context loss gracefully
        4. Logs the post-restart interaction
        """
        await interaction.response.defer(ephemeral=True)

        custom_id = interaction.data.get("custom_id", "")
        discord_id = str(interaction.user.id)

        try:
            # Parse article_id from custom_id (format: mark_read_{uuid})
            article_id = parse_article_id_from_custom_id(custom_id, "mark_read_")

            # Update article status (database operation) via service layer
            await self.supabase_service.update_article_status(discord_id, article_id, "Read")

            # Disable the button (handle message context loss)
            self.disabled = True
            try:
                await interaction.message.edit(view=self.view)
            except discord.NotFound:
                logger.info(
                    f"Message not found when disabling button (likely deleted) | "
                    f"User: {discord_id} | Article: {article_id}"
                )
            except discord.HTTPException as e:
                logger.warning(
                    f"Failed to edit message: {e} | " f"User: {discord_id} | Article: {article_id}"
                )

            # Send confirmation
            await interaction.followup.send("✅ 已標記為已讀", ephemeral=True)

            # Log successful post-restart interaction
            log_persistent_interaction(
                user_id=discord_id,
                action="mark_read",
                article_id=article_id,
                custom_id=custom_id,
                success=True,
            )

        except ValueError as e:
            error_msg = f"Invalid custom_id or UUID: {e}"
            log_persistent_interaction(
                user_id=discord_id,
                action="mark_read",
                article_id=None,
                custom_id=custom_id,
                success=False,
                error=error_msg,
            )
            await interaction.followup.send("❌ 無效的按鈕 ID", ephemeral=True)
        except SupabaseServiceError as e:
            error_msg = f"Database error: {e}"
            log_persistent_interaction(
                user_id=discord_id,
                action="mark_read",
                article_id=None,
                custom_id=custom_id,
                success=False,
                error=error_msg,
            )
            await interaction.followup.send("❌ 標記失敗，請稍後再試", ephemeral=True)
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(f"PersistentMarkReadButton error: {e}", exc_info=True)
            log_persistent_interaction(
                user_id=discord_id,
                action="mark_read",
                article_id=None,
                custom_id=custom_id,
                success=False,
                error=error_msg,
            )
            await interaction.followup.send("❌ 標記失敗，請稍後再試", ephemeral=True)


class PersistentRatingSelect(discord.ui.Select):
    """
    Persistent Rating select that can be reconstructed after bot restart.
    """

    def __init__(self, supabase_service: SupabaseService = None):
        options = [
            discord.SelectOption(label="⭐", value="1"),
            discord.SelectOption(label="⭐⭐", value="2"),
            discord.SelectOption(label="⭐⭐⭐", value="3"),
            discord.SelectOption(label="⭐⭐⭐⭐", value="4"),
            discord.SelectOption(label="⭐⭐⭐⭐⭐", value="5"),
        ]
        super().__init__(placeholder="評分文章", options=options, custom_id="rate_persistent")
        self.supabase_service = supabase_service or SupabaseService()

    async def callback(self, interaction: discord.Interaction):
        """
        Handle rating selection after bot restart.

        This method:
        1. Parses article_id from custom_id
        2. Updates article rating in database
        3. Logs the post-restart interaction
        """
        await interaction.response.defer(ephemeral=True)

        custom_id = interaction.data.get("custom_id", "")
        discord_id = str(interaction.user.id)

        try:
            # Parse article_id from custom_id (format: rate_{uuid})
            article_id = parse_article_id_from_custom_id(custom_id, "rate_")

            # Get rating from selection
            rating = int(self.values[0])
            stars = "⭐" * rating

            # Update article rating (database operation) via service layer
            await self.supabase_service.update_article_rating(discord_id, article_id, rating)

            # Send confirmation
            await interaction.followup.send(f"✅ 已評為 {stars}（{rating} 星）！", ephemeral=True)

            # Log successful post-restart interaction
            log_persistent_interaction(
                user_id=discord_id,
                action=f"rate_{rating}",
                article_id=article_id,
                custom_id=custom_id,
                success=True,
            )

        except ValueError as e:
            error_msg = f"Invalid custom_id, UUID, or rating: {e}"
            log_persistent_interaction(
                user_id=discord_id,
                action="rate",
                article_id=None,
                custom_id=custom_id,
                success=False,
                error=error_msg,
            )
            await interaction.followup.send("❌ 無效的文章 ID 或評分", ephemeral=True)
        except SupabaseServiceError as e:
            error_msg = f"Database error: {e}"
            log_persistent_interaction(
                user_id=discord_id,
                action="rate",
                article_id=None,
                custom_id=custom_id,
                success=False,
                error=error_msg,
            )
            await interaction.followup.send("❌ 評分時發生錯誤，請稍後再試。", ephemeral=True)
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(f"PersistentRatingSelect error: {e}", exc_info=True)
            log_persistent_interaction(
                user_id=discord_id,
                action="rate",
                article_id=None,
                custom_id=custom_id,
                success=False,
                error=error_msg,
            )
            await interaction.followup.send("❌ 評分時發生錯誤，請稍後再試。", ephemeral=True)


class PersistentDeepDiveButton(discord.ui.Button):
    """
    Persistent Deep Dive button that can be reconstructed after bot restart.
    Note: This requires fetching the article from the database to generate the deep dive.
    """

    def __init__(self, supabase_service: SupabaseService = None, llm_service: LLMService = None):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="📖 深度分析",
            custom_id="deep_dive_persistent",
        )
        self.supabase_service = supabase_service or SupabaseService()
        self.llm_service = llm_service or LLMService()

    async def callback(self, interaction: discord.Interaction):
        """
        Handle button click after bot restart.

        This method:
        1. Parses article_id from custom_id
        2. Reloads article data from database (critical for post-restart)
        3. Generates deep dive analysis
        4. Logs the post-restart interaction
        """
        await interaction.response.defer(ephemeral=True)

        custom_id = interaction.data.get("custom_id", "")
        discord_id = str(interaction.user.id)

        try:
            # Parse article_id from custom_id (format: deep_dive_{uuid})
            article_id = parse_article_id_from_custom_id(custom_id, "deep_dive_")

            # Fetch article from database (necessary after bot restart) via service layer
            response = (
                self.supabase_service.client.table("articles")
                .select("*")
                .eq("id", str(article_id))
                .execute()
            )

            if not response.data:
                error_msg = "Article not found in database"
                log_persistent_interaction(
                    user_id=discord_id,
                    action="deep_dive",
                    article_id=article_id,
                    custom_id=custom_id,
                    success=False,
                    error=error_msg,
                )
                await interaction.followup.send("❌ 找不到該文章", ephemeral=True)
                return

            article_data = response.data[0]

            # Create ArticleSchema object for LLM service
            from datetime import datetime

            from app.schemas.article import ArticleSchema

            article = ArticleSchema(
                id=UUID(article_data["id"]),
                title=article_data["title"],
                url=article_data["url"],
                category=article_data.get("category", "Unknown"),
                tinkering_index=article_data.get("tinkering_index"),
                ai_summary=article_data.get("ai_summary"),
                published_at=datetime.fromisoformat(article_data["published_at"]),
                feed_id=UUID(article_data["feed_id"]),
                feed_name=article_data.get("feed_name", ""),
            )

            # Generate deep dive via service layer
            result = await self.llm_service.generate_deep_dive(article)
            if len(result) > 2000:
                result = result[:1997] + "..."

            await interaction.followup.send(result, ephemeral=True)

            # Log successful post-restart interaction
            log_persistent_interaction(
                user_id=discord_id,
                action="deep_dive",
                article_id=article_id,
                custom_id=custom_id,
                success=True,
            )

        except ValueError as e:
            error_msg = f"Invalid custom_id or UUID: {e}"
            log_persistent_interaction(
                user_id=discord_id,
                action="deep_dive",
                article_id=None,
                custom_id=custom_id,
                success=False,
                error=error_msg,
            )
            await interaction.followup.send("❌ 無效的按鈕 ID", ephemeral=True)
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(f"PersistentDeepDiveButton callback error: {e}", exc_info=True)
            log_persistent_interaction(
                user_id=discord_id,
                action="deep_dive",
                article_id=None,
                custom_id=custom_id,
                success=False,
                error=error_msg,
            )
            await interaction.followup.send("❌ 生成深度摘要時發生錯誤，請稍後再試。", ephemeral=True)


class PersistentInteractionView(discord.ui.View):
    """
    A persistent view that registers all persistent interactive components.
    This view is registered once in setup_hook and handles all interactions.
    """

    def __init__(self, supabase_service: SupabaseService = None, llm_service: LLMService = None):
        super().__init__(timeout=None)
        self.supabase_service = supabase_service or SupabaseService()
        self.llm_service = llm_service or LLMService()
        # Add all persistent components
        # Note: We only add one instance of each type
        # The actual custom_id will be parsed from the interaction
        self.add_item(PersistentReadLaterButton(self.supabase_service))
        self.add_item(PersistentMarkReadButton(self.supabase_service))
        self.add_item(PersistentRatingSelect(self.supabase_service))
        self.add_item(PersistentDeepDiveButton(self.supabase_service, self.llm_service))
