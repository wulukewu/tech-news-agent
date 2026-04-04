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
                
            # 2. Scrape Articles
            rss = RSSService(days_to_fetch=7)
            all_articles = await rss.fetch_all_feeds(feeds)
            
            if not all_articles:
                await interaction.followup.send("📭 最近 7 天內沒有任何新文章。")
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

            # TODO: Implement article insertion into database
            # This requires mapping feed names to feed_ids
            logger.warning("Article insertion to database not yet implemented")

            # 4. Build notification message
            lines = [
                "📰 **本週科技新聞精選**",
                "",
                f"📊 本週統計：",
                f"  • 總共抓取：{stats.get('total_fetched', 0)} 篇文章",
                f"  • 精選推薦：{stats.get('hardcore_count', 0)} 篇",
                "",
                "🔥 **推薦文章：**",
                ""
            ]
            
            # Group articles by category
            from collections import defaultdict
            by_category = defaultdict(list)
            for article in hardcore_articles:
                by_category[article.source_category].append(article)
            
            # Format articles by category
            for category, articles in sorted(by_category.items()):
                lines.append(f"**{category}**")
                for article in articles[:10]:  # Limit to 10 per category
                    tinkering = "🔥" * (article.ai_analysis.tinkering_index if article.ai_analysis else 0)
                    lines.append(f"  {tinkering} {article.title}")
                    lines.append(f"    🔗 {article.url}")
                lines.append("")
            
            notification = "\n".join(lines)

            # 5. Send results back to Discord with interactive buttons
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
