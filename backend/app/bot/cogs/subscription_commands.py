"""Discord bot commands for subscription management."""

import logging
from uuid import UUID
from discord import app_commands
from discord.ext import commands
import discord

from app.bot.utils.decorators import ensure_user_registered
from app.bot.utils.validators import validate_and_sanitize_feed_data, validate_uuid
from app.services.supabase_service import SupabaseService
from app.core.exceptions import SupabaseServiceError

logger = logging.getLogger(__name__)


class SubscriptionCommands(commands.Cog):
    """Cog for managing user feed subscriptions."""

    def __init__(self, bot: commands.Bot):
        """
        Initialize the SubscriptionCommands cog.

        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
        logger.info("SubscriptionCommands cog initialized")

    @app_commands.command(name="add_feed", description="訂閱一個 RSS 來源")
    @app_commands.describe(
        name="訂閱源名稱",
        url="RSS/Atom 網址",
        category="分類（例如：AI、Web、Security）"
    )
    async def add_feed(
        self,
        interaction: discord.Interaction,
        name: str,
        url: str,
        category: str
    ):
        """
        訂閱一個 RSS 來源
        
        Args:
            interaction: Discord interaction object
            name: Feed name
            url: RSS/Atom feed URL
            category: Feed category
            
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8
        """
        await interaction.response.defer(ephemeral=True)
        
        logger.info(f"User {interaction.user.id} executing /add_feed: name={name}, url={url}, category={category}")
        
        try:
            # 1. Validate and sanitize feed data
            is_valid, sanitized_data, error_msg = validate_and_sanitize_feed_data(name, url, category)
            if not is_valid:
                logger.warning(f"Feed data validation failed: {error_msg}")
                await interaction.followup.send(
                    f"❌ {error_msg}",
                    ephemeral=True
                )
                return
            
            # 2. Register user and get UUID
            user_uuid = await ensure_user_registered(interaction)
            logger.info(f"User registered with UUID: {user_uuid}")
            
            # 3. Use sanitized data
            supabase = SupabaseService()
            validated_url = sanitized_data["url"]
            sanitized_name = sanitized_data["name"]
            sanitized_category = sanitized_data["category"]
            logger.info(f"Feed data validated: {sanitized_name}, {validated_url}, {sanitized_category}")
            
            # 3. Check if feed exists in feeds table
            response = supabase.client.table('feeds')\
                .select('id')\
                .eq('url', validated_url)\
                .execute()
            
            if response.data and len(response.data) > 0:
                # Feed exists, use existing feed_id
                feed_id = UUID(response.data[0]['id'])
                logger.info(f"Feed already exists with ID: {feed_id}")
            else:
                # 4. Create new feed if it doesn't exist
                logger.info(f"Creating new feed: {sanitized_name}")
                insert_response = supabase.client.table('feeds')\
                    .insert({
                        'name': sanitized_name,
                        'url': validated_url,
                        'category': sanitized_category,
                        'is_active': True
                    })\
                    .execute()
                
                if not insert_response.data or len(insert_response.data) == 0:
                    raise SupabaseServiceError(
                        "Failed to create feed: No data returned",
                        context={"name": sanitized_name, "url": validated_url, "category": sanitized_category}
                    )
                
                feed_id = UUID(insert_response.data[0]['id'])
                logger.info(f"Feed created successfully with ID: {feed_id}")
            
            # 5. Subscribe user to feed
            await supabase.subscribe_to_feed(str(interaction.user.id), feed_id)
            logger.info(f"User {interaction.user.id} subscribed to feed {feed_id}")
            
            # 6. Send confirmation message
            await interaction.followup.send(
                f"✅ 已成功訂閱 **{sanitized_name}** ({sanitized_category})\n"
                f"🔗 {validated_url}",
                ephemeral=True
            )
            
        except ValueError as e:
            # URL validation error
            logger.warning(f"URL validation failed: {e}")
            await interaction.followup.send(
                f"❌ URL 格式無效：{e}\n"
                f"請確保 URL 以 http:// 或 https:// 開頭。",
                ephemeral=True
            )
            
        except SupabaseServiceError as e:
            # Database operation error
            logger.error(f"Database operation failed: {e}", exc_info=True)
            
            # Check if it's a duplicate subscription (user already subscribed)
            error_str = str(e).lower()
            if "duplicate" in error_str or "already exists" in error_str:
                await interaction.followup.send(
                    f"ℹ️ 你已經訂閱過 **{name}** 了！",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ 訂閱失敗，請稍後再試。",
                    ephemeral=True
                )
                
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error in add_feed: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ 發生未預期的錯誤，請稍後再試。",
                ephemeral=True
            )

    @app_commands.command(name="list_feeds", description="查看已訂閱的 RSS 來源")
    async def list_feeds(self, interaction: discord.Interaction):
        """
        查看已訂閱的 RSS 來源
        
        Args:
            interaction: Discord interaction object
            
        Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
        """
        await interaction.response.defer(ephemeral=True)
        
        logger.info(f"User {interaction.user.id} executing /list_feeds")
        
        try:
            # 1. Register user and get UUID
            user_uuid = await ensure_user_registered(interaction)
            logger.info(f"User registered with UUID: {user_uuid}")
            
            # 2. Get user subscriptions
            supabase = SupabaseService()
            subscriptions = await supabase.get_user_subscriptions(str(interaction.user.id))
            
            # 3. Handle empty subscriptions
            if not subscriptions:
                logger.info(f"User {interaction.user.id} has no subscriptions")
                await interaction.followup.send(
                    "📭 你還沒有訂閱任何 RSS 來源！\n"
                    "使用 `/add_feed` 來訂閱感興趣的來源。",
                    ephemeral=True
                )
                return
            
            # 4. Build subscription list message
            lines = ["📚 **你的訂閱清單**\n"]
            
            # Group by category for better organization
            from collections import defaultdict
            by_category = defaultdict(list)
            for sub in subscriptions:
                by_category[sub.category].append(sub)
            
            # Display subscriptions grouped by category
            for category in sorted(by_category.keys()):
                lines.append(f"**{category}**")
                for sub in by_category[category]:
                    lines.append(f"• **{sub.name}**")
                    lines.append(f"  🔗 {sub.url}")
                lines.append("")
            
            # Add footer with total count
            lines.append(f"_共 {len(subscriptions)} 個訂閱源_")
            
            content = "\n".join(lines)
            
            # 5. Send ephemeral response
            await interaction.followup.send(content, ephemeral=True)
            logger.info(f"Sent {len(subscriptions)} subscriptions to user {interaction.user.id}")
            
        except SupabaseServiceError as e:
            # Database operation error
            logger.error(f"Database operation failed: {e}", exc_info=True)
            await interaction.followup.send(
                "❌ 無法取得訂閱清單，請稍後再試。",
                ephemeral=True
            )
            
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error in list_feeds: {e}", exc_info=True)
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。",
                ephemeral=True
            )

    @app_commands.command(name="unsubscribe_feed", description="取消訂閱 RSS 來源")
    @app_commands.describe(
        feed_identifier="訂閱源名稱或 ID"
    )
    async def unsubscribe_feed(
        self,
        interaction: discord.Interaction,
        feed_identifier: str
    ):
        """
        取消訂閱 RSS 來源
        
        Args:
            interaction: Discord interaction object
            feed_identifier: Feed name or feed ID (UUID)
            
        Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5, 11.6
        """
        await interaction.response.defer(ephemeral=True)
        
        logger.info(f"User {interaction.user.id} executing /unsubscribe_feed: feed_identifier={feed_identifier}")
        
        try:
            # 1. Register user and get UUID
            user_uuid = await ensure_user_registered(interaction)
            logger.info(f"User registered with UUID: {user_uuid}")
            
            # 2. Get user subscriptions to find the feed
            supabase = SupabaseService()
            subscriptions = await supabase.get_user_subscriptions(str(interaction.user.id))
            
            # 3. Handle empty subscriptions
            if not subscriptions:
                logger.info(f"User {interaction.user.id} has no subscriptions")
                await interaction.followup.send(
                    "📭 你還沒有訂閱任何 RSS 來源！",
                    ephemeral=True
                )
                return
            
            # 4. Find the feed by name or ID
            feed_to_unsubscribe = None
            feed_identifier_lower = feed_identifier.lower().strip()
            
            # Try to match by UUID first
            try:
                from uuid import UUID
                feed_uuid = UUID(feed_identifier)
                for sub in subscriptions:
                    if sub.feed_id == feed_uuid:
                        feed_to_unsubscribe = sub
                        break
            except ValueError:
                # Not a valid UUID, try matching by name
                for sub in subscriptions:
                    if sub.name.lower() == feed_identifier_lower:
                        feed_to_unsubscribe = sub
                        break
            
            # 5. Handle feed not found
            if not feed_to_unsubscribe:
                logger.info(f"Feed not found in user subscriptions: {feed_identifier}")
                await interaction.followup.send(
                    f"❌ 找不到訂閱源：**{feed_identifier}**\n"
                    f"請使用 `/list_feeds` 查看你的訂閱清單。",
                    ephemeral=True
                )
                return
            
            # 6. Unsubscribe from feed
            await supabase.unsubscribe_from_feed(
                str(interaction.user.id),
                feed_to_unsubscribe.feed_id
            )
            logger.info(f"User {interaction.user.id} unsubscribed from feed {feed_to_unsubscribe.feed_id}")
            
            # 7. Send confirmation message
            await interaction.followup.send(
                f"✅ 已取消訂閱 **{feed_to_unsubscribe.name}** ({feed_to_unsubscribe.category})",
                ephemeral=True
            )
            
        except SupabaseServiceError as e:
            # Database operation error
            logger.error(f"Database operation failed: {e}", exc_info=True)
            await interaction.followup.send(
                "❌ 取消訂閱失敗，請稍後再試。",
                ephemeral=True
            )
            
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error in unsubscribe_feed: {e}", exc_info=True)
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """
    Setup function to register the cog with the bot.

    Args:
        bot: The Discord bot instance
    """
    await bot.add_cog(SubscriptionCommands(bot))
    logger.info("SubscriptionCommands cog registered")
