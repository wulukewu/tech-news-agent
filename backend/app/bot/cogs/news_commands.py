import logging
import asyncio
from datetime import datetime, timezone, timedelta
from uuid import UUID
from collections import defaultdict

import discord
from discord import app_commands
from discord.ext import commands

from app.services.supabase_service import SupabaseService
from app.services.rss_service import RSSService
from app.services.llm_service import LLMService
from app.core.exceptions import SupabaseServiceError
from app.core.config import settings
from app.schemas.article import ArticlePageResult, ArticleSchema

logger = logging.getLogger(__name__)


async def ensure_user_registered(interaction: discord.Interaction) -> UUID:
    """
    Ensure user exists in database and return user UUID.
    
    Args:
        interaction: Discord interaction object
        
    Returns:
        User UUID from database
        
    Raises:
        SupabaseServiceError: If user registration fails
    """
    discord_id = str(interaction.user.id)
    
    try:
        supabase = SupabaseService()
        user_uuid = await supabase.get_or_create_user(discord_id)
        logger.info(f"User {discord_id} registered/retrieved with UUID: {user_uuid}")
        return user_uuid
    except SupabaseServiceError as e:
        logger.error(
            f"Failed to register user {discord_id}: {e}",
            exc_info=True,
            extra={
                "discord_id": discord_id,
                "function": "ensure_user_registered",
                "error_type": "SupabaseServiceError"
            }
        )
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error registering user {discord_id}: {e}",
            exc_info=True,
            extra={
                "discord_id": discord_id,
                "function": "ensure_user_registered",
                "error_type": type(e).__name__
            }
        )
        raise SupabaseServiceError(
            "使用者註冊失敗",
            original_error=e,
            context={"discord_id": discord_id}
        )


class NewsCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(name="news_now", description="查看你訂閱的最新技術文章")
    async def news_now(self, interaction: discord.Interaction):
        logger.info(f"Command /news_now triggered by user {interaction.user.id}")
        await interaction.response.defer(thinking=True)
        
        try:
            # 1. Register user
            try:
                user_uuid = await ensure_user_registered(interaction)
                logger.info(f"User {interaction.user.id} registered with UUID: {user_uuid}")
            except SupabaseServiceError as e:
                logger.error(f"User registration failed for {interaction.user.id}: {e}")
                await interaction.followup.send(
                    "❌ 無法註冊使用者，請稍後再試。",
                    ephemeral=True
                )
                return
            
            # 2. Get user's subscriptions
            supabase = SupabaseService()
            subscriptions = await supabase.get_user_subscriptions(str(interaction.user.id))
            
            if not subscriptions:
                await interaction.followup.send(
                    "📭 你還沒有訂閱任何 RSS 來源！\n"
                    "使用 `/add_feed` 來訂閱感興趣的來源。"
                )
                return
            
            # 3. Query articles from subscribed feeds
            feed_ids = [str(sub.feed_id) for sub in subscriptions]
            seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            
            response = supabase.client.table('articles')\
                .select('id, title, url, tinkering_index, ai_summary, published_at, feed_id, feeds(category)')\
                .in_('feed_id', feed_ids)\
                .gte('published_at', seven_days_ago)\
                .not_.is_('tinkering_index', 'null')\
                .order('tinkering_index', desc=True)\
                .limit(20)\
                .execute()
            
            if not response.data:
                await interaction.followup.send(
                    "📭 最近 7 天沒有新文章。\n"
                    "背景排程器會定期抓取文章，請稍後再試。"
                )
                return
            
            # 4. Convert to ArticleSchema objects
            articles = []
            for row in response.data:
                # Find the feed name from subscriptions
                feed_name = next((sub.name for sub in subscriptions if str(sub.feed_id) == row['feed_id']), 'Unknown')
                
                # Extract category from nested feeds object
                category = row.get('feeds', {}).get('category', 'Unknown') if isinstance(row.get('feeds'), dict) else 'Unknown'
                
                article = ArticleSchema(
                    id=UUID(row['id']),
                    title=row['title'],
                    url=row['url'],
                    category=category,
                    tinkering_index=row['tinkering_index'],
                    ai_summary=row['ai_summary'],
                    published_at=datetime.fromisoformat(row['published_at']) if row['published_at'] else None,
                    feed_id=UUID(row['feed_id']),
                    feed_name=feed_name,
                    created_at=datetime.now(timezone.utc)
                )
                articles.append(article)
            
            logger.info(f"User {interaction.user.id} retrieved {len(articles)} articles from {len(feed_ids)} subscribed feeds")
            
            # 5. Build notification message (with 2000 char limit)
            lines = [
                "📰 **你的個人化技術新聞**",
                f"📊 找到 {len(articles)} 篇精選文章\n",
                "🔥 **推薦文章：**\n"
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
                    article_lines = [
                        f"  {tinkering} {article.title}",
                        f"    🔗 {article.url}"
                    ]
                    
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
            from app.bot.cogs.interactions import ReadLaterView, FilterView, DeepDiveView
            
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
            logger.info(f"Successfully sent news_now response to user {interaction.user.id}")
            
        except SupabaseServiceError as e:
            # Database-specific errors
            logger.error(
                f"Database error in /news_now for user {interaction.user.id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "command": "news_now",
                    "error_type": "SupabaseServiceError"
                }
            )
            await interaction.followup.send(
                "❌ 無法取得文章資料，請稍後再試。",
                ephemeral=True
            )
        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(
                f"Unexpected error in /news_now for user {interaction.user.id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "command": "news_now",
                    "error_type": type(e).__name__
                }
            )
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(NewsCommands(bot))
