from collections import defaultdict

import discord
from discord import app_commands
from discord.ext import commands

from app.bot.utils.decorators import ensure_user_registered
from app.core.exceptions import SupabaseServiceError
from app.core.logger import get_logger
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)


class NewsCommands(commands.Cog):
    """News commands cog with service layer dependency injection."""

    def __init__(self, bot: commands.Bot, supabase_service: SupabaseService = None):
        """
        Initialize NewsCommands cog with service dependencies.

        Args:
            bot: Discord bot instance
            supabase_service: Optional SupabaseService instance for dependency injection
        """
        self.bot = bot
        self.supabase_service = supabase_service or SupabaseService()

    @app_commands.command(name="news_now", description="查看你訂閱的最新技術文章")
    async def news_now(self, interaction: discord.Interaction):
        logger.info(
            "Command /news_now triggered", user_id=str(interaction.user.id), command="news_now"
        )
        await interaction.response.defer(thinking=True)

        try:
            # 1. Register user using decorator
            try:
                user_uuid = await ensure_user_registered(interaction)
                logger.info(
                    "User registered successfully",
                    user_id=str(interaction.user.id),
                    user_uuid=str(user_uuid),
                )
            except SupabaseServiceError as e:
                logger.error(
                    "User registration failed",
                    user_id=str(interaction.user.id),
                    error=str(e),
                    exc_info=True,
                )
                await interaction.followup.send(
                    "❌ 無法註冊使用者，請稍後再試。\n" "💡 建議：請確認你的網路連線正常，或稍後再試。",
                    ephemeral=True,
                )
                return

            # 2. Get user's subscriptions via service layer
            subscriptions = await self.supabase_service.get_user_subscriptions(
                str(interaction.user.id)
            )

            if not subscriptions:
                logger.info("User has no subscriptions", user_id=str(interaction.user.id))
                await interaction.followup.send("📭 你還沒有訂閱任何 RSS 來源！\n" "使用 `/add_feed` 來訂閱感興趣的來源。")
                return

            # 3. Query articles from subscribed feeds via service layer
            # Use the service layer method instead of direct database access
            articles = await self.supabase_service.get_user_articles(
                discord_id=str(interaction.user.id), days=7, limit=20
            )

            if not articles:
                logger.info(
                    "No recent articles found",
                    user_id=str(interaction.user.id),
                    subscription_count=len(subscriptions),
                )
                await interaction.followup.send("📭 最近 7 天沒有新文章。\n" "背景排程器會定期抓取文章，請稍後再試。")
                return

            # 4. Enrich articles with feed names from subscriptions
            for article in articles:
                feed_name = next(
                    (sub.name for sub in subscriptions if str(sub.feed_id) == str(article.feed_id)),
                    "Unknown",
                )
                article.feed_name = feed_name

            logger.info(
                "Retrieved articles for user",
                user_id=str(interaction.user.id),
                article_count=len(articles),
                subscription_count=len(subscriptions),
            )

            # 5. Build notification message (with 2000 char limit)
            lines = [
                "📰 **你的個人化技術新聞**",
                f"📊 找到 {len(articles)} 篇精選文章\n",
                "🔥 **推薦文章：**\n",
            ]

            # Group articles by category
            by_category = defaultdict(list)
            for article in articles:
                by_category[article.category].append(article)

            # Format articles by category with character limit check
            DISCORD_CHAR_LIMIT = 2000
            RESERVED_CHARS = 100  # Reserve space for truncation message

            for category, cat_articles in sorted(by_category.items()):
                category_line = f"**{category}**"
                # Check if adding this would exceed limit
                test_content = "\n".join(lines + [category_line])
                if len(test_content) > DISCORD_CHAR_LIMIT - RESERVED_CHARS:
                    lines.append("\n_...更多文章請使用下方按鈕查看_")
                    break

                lines.append(category_line)

                for article in cat_articles[:5]:  # Limit to 5 per category
                    tinkering = "🔥" * article.tinkering_index
                    article_lines = [f"  {tinkering} {article.title}", f"    🔗 {article.url}"]

                    # Check if adding this article would exceed limit
                    test_content = "\n".join(lines + article_lines)
                    if len(test_content) > DISCORD_CHAR_LIMIT - RESERVED_CHARS:
                        lines.append("\n_...更多文章請使用下方按鈕查看_")
                        break

                    lines.extend(article_lines)
                else:
                    # Only add empty line if we didn't break
                    lines.append("")
                    continue
                # If we broke from inner loop, break from outer loop too
                break

            notification = "\n".join(lines)

            # 6. Create interactive view with article IDs
            from app.bot.cogs.interactions import FilterView

            combined_view = FilterView(articles=articles)

            # Add Deep Dive buttons (top 5 articles)
            for article in articles[:5]:
                from app.bot.cogs.interactions import DeepDiveButton

                combined_view.add_item(DeepDiveButton(article))

            # Add Read Later buttons (top 10 articles)
            for article in articles[:10]:
                from app.bot.cogs.interactions import ReadLaterButton

                combined_view.add_item(ReadLaterButton(article.id, article.title))

            await interaction.followup.send(content=notification, view=combined_view)
            logger.info(
                "Successfully sent news_now response",
                user_id=str(interaction.user.id),
                article_count=len(articles),
            )

        except SupabaseServiceError as e:
            # Database-specific errors
            logger.error(
                "Database error in /news_now command",
                user_id=str(interaction.user.id),
                command="news_now",
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 無法取得文章資料，請稍後再試。\n" "💡 建議：資料庫連線可能暫時中斷，請稍後再試或聯繫管理員。",
                ephemeral=True,
            )
        except Exception as e:
            # Catch-all for unexpected errors
            logger.critical(
                "Unexpected error in /news_now command",
                user_id=str(interaction.user.id),
                command="news_now",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。\n" "💡 建議：如果問題持續發生，請聯繫管理員並提供你的使用者 ID。",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    """Setup function with service layer dependency injection."""
    supabase_service = SupabaseService()
    await bot.add_cog(NewsCommands(bot, supabase_service))
