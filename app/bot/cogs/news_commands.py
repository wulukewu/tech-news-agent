import logging
import asyncio
from datetime import datetime, timezone, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from app.services.supabase_service import SupabaseService
from app.services.rss_service import RSSService
from app.services.llm_service import LLMService
from app.core.exceptions import SupabaseServiceError
from app.core.config import settings
from app.schemas.article import ArticlePageResult

logger = logging.getLogger(__name__)


def build_week_string(dt: datetime) -> str:
    """Build a week string in format YYYY-WW from a datetime object."""
    year = dt.year
    week = dt.isocalendar()[1]
    return f"{year}-{week:02d}"

class NewsCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(name="news_now", description="強制立即抓取並生成本週的技術新聞報表")
    async def news_now(self, interaction: discord.Interaction):
        logger.info(f"Command /news_now triggered by {interaction.user}")
        await interaction.response.defer(thinking=True)
        
        try:
            # 1. Fetch Feeds
            supabase = SupabaseService()
            feeds = await supabase.get_active_feeds()
            
            if not feeds:
                await interaction.followup.send("⚠️ 目前資料庫中沒有任何啟用的 RSS 訂閱源！")
                return
            
            # Build feed_id_map for RSS service
            feed_id_map = {}
            try:
                response = supabase.client.table('feeds')\
                    .select('id, url')\
                    .eq('is_active', True)\
                    .execute()
                
                if response.data:
                    for feed in response.data:
                        feed_id_map[feed['url']] = feed['id']
                    logger.info(f"Built feed_id_map with {len(feed_id_map)} entries")
            except Exception as e:
                logger.error(f"Failed to build feed_id_map: {e}", exc_info=True)
                
            # 2. Scrape Articles (with deduplication)
            rss = RSSService(days_to_fetch=settings.rss_fetch_days)
            
            # Use fetch_new_articles to avoid re-processing existing articles
            all_articles = await rss.fetch_new_articles(feeds, supabase)
            
            if not all_articles:
                await interaction.followup.send("📭 最近 7 天內沒有任何新文章（或所有文章都已處理過）。")
                return
                
            # 3. Evaluate Hardcore level
            llm = LLMService()
            hardcore_articles = await llm.evaluate_batch(all_articles)
            logger.info(f"Evaluated articles: {len(hardcore_articles)} hardcore retained.")

            # Build stats dict
            stats = {
                "total_fetched": len(all_articles),
                "hardcore_count": len(hardcore_articles),
            }

            # 4. Insert articles into database
            try:
                articles_to_insert = []
                for article in hardcore_articles:
                    article_dict = {
                        'title': article.title,
                        'url': str(article.url),
                        'feed_id': str(article.feed_id),
                        'published_at': article.published_at.isoformat() if article.published_at else None,
                        'tinkering_index': article.tinkering_index,
                        'ai_summary': article.ai_summary,
                        'embedding': article.embedding
                    }
                    articles_to_insert.append(article_dict)
                
                if articles_to_insert:
                    batch_result = await supabase.insert_articles(articles_to_insert)
                    logger.info(
                        f"Article insertion complete: {batch_result.inserted_count} inserted, "
                        f"{batch_result.updated_count} updated, {batch_result.failed_count} failed"
                    )
                    stats['inserted'] = batch_result.inserted_count
                    stats['updated'] = batch_result.updated_count
                    stats['failed'] = batch_result.failed_count
                else:
                    logger.warning("No articles to insert")
                    stats['inserted'] = 0
                    stats['updated'] = 0
                    stats['failed'] = 0
                    
            except Exception as e:
                logger.error(f"Failed to insert articles into database: {e}", exc_info=True)
                stats['inserted'] = 0
                stats['updated'] = 0
                stats['failed'] = len(hardcore_articles)

            # 5. Build notification message (with 2000 char limit)
            lines = [
                "📰 **本週科技新聞精選**",
                "",
                f"📊 本週統計：",
                f"  • 總共抓取：{stats.get('total_fetched', 0)} 篇文章",
                f"  • 精選推薦：{stats.get('hardcore_count', 0)} 篇",
                f"  • 新增資料庫：{stats.get('inserted', 0)} 篇",
                f"  • 更新資料庫：{stats.get('updated', 0)} 篇",
                "",
                "🔥 **推薦文章：**",
                ""
            ]
            
            # Group articles by category
            from collections import defaultdict
            by_category = defaultdict(list)
            for article in hardcore_articles:
                by_category[article.category].append(article)
            
            # Format articles by category with character limit check
            DISCORD_CHAR_LIMIT = 2000
            RESERVED_CHARS = 100  # Reserve space for truncation message
            
            for category, articles in sorted(by_category.items()):
                category_line = f"**{category}**"
                # Check if adding this would exceed limit
                test_content = "\n".join(lines + [category_line])
                if len(test_content) > DISCORD_CHAR_LIMIT - RESERVED_CHARS:
                    lines.append("\n_...更多文章請使用下方按鈕查看_")
                    break
                    
                lines.append(category_line)
                
                for article in articles[:10]:  # Limit to 10 per category
                    tinkering = "🔥" * (article.tinkering_index if article.tinkering_index else 0)
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

            # 6. Send results back to Discord with interactive buttons
            from app.bot.cogs.interactions import ReadLaterView, FilterView, DeepDiveView  # Local import to prevent circular deps

            combined_view = FilterView(articles=hardcore_articles)
            for item in DeepDiveView(articles=hardcore_articles[:5]).children:
                combined_view.add_item(item)
            # Add ReadLaterButtons, capped at 10 to keep total components ≤ 25.
            MAX_READ_LATER = 10
            read_later_view = ReadLaterView(articles=hardcore_articles[:MAX_READ_LATER])
            for item in read_later_view.children:
                combined_view.add_item(item)

            await interaction.followup.send(content=notification, view=combined_view)
            
        except Exception as e:
            logger.error(f"Error during /news_now execution: {e}", exc_info=True)
            await interaction.followup.send(f"❌ 發生錯誤：{e}")

    @app_commands.command(name="add_feed", description="將一個新的 RSS 訂閱源加入資料庫")
    @app_commands.describe(
        name="訂閱源名稱 (例如: YCombinator)",
        url="RSS/Atom 網址",
        category="分類 (例如: AI, Frontend, Backend)"
    )
    async def add_feed(self, interaction: discord.Interaction, name: str, url: str, category: str):
        await interaction.response.defer(thinking=True)
        try:
            # TODO: Implement add_feed in SupabaseService
            # This requires direct database access to insert into feeds table
            logger.warning("add_feed command not yet implemented for Supabase")
            await interaction.followup.send(
                f"❌ 此功能暫時無法使用（需要實作 Supabase 的 add_feed 方法）"
            )
        except Exception as e:
            logger.error(f"Error during /add_feed execution: {e}", exc_info=True)
            await interaction.followup.send(f"❌ 新增失敗：{e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(NewsCommands(bot))
