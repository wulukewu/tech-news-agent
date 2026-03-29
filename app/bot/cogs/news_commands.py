import logging
import asyncio
from datetime import datetime, timezone, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from app.services.notion_service import NotionService, build_week_string
from app.services.rss_service import RSSService
from app.services.llm_service import LLMService
from app.core.exceptions import NotionServiceError
from app.core.config import settings
from app.schemas.article import ArticlePageResult

logger = logging.getLogger(__name__)

class NewsCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(name="news_now", description="強制立即抓取並生成本週的技術新聞報表")
    async def news_now(self, interaction: discord.Interaction):
        logger.info(f"Command /news_now triggered by {interaction.user}")
        await interaction.response.defer(thinking=True)
        
        try:
            # 1. Fetch Feeds
            notion = NotionService()
            feeds = await notion.get_active_feeds()
            
            if not feeds:
                await interaction.followup.send("⚠️ 目前 Notion 中沒有任何啟用的 RSS 訂閱源！")
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

            # 4. Calculate current week
            tz_taipei = timezone(timedelta(hours=8))
            dt = datetime.now(tz=tz_taipei)
            published_week = build_week_string(dt)
            logger.info(f"Current week: {published_week}")

            # 5. Batch create article Pages (limit concurrency to 5)
            article_pages = []
            semaphore = asyncio.Semaphore(5)

            async def create_with_semaphore(article):
                async with semaphore:
                    try:
                        page_id, page_url = await notion.create_article_page(article, published_week)
                        return ArticlePageResult(
                            page_id=page_id,
                            page_url=page_url,
                            title=article.title,
                            category=article.source_category,
                            tinkering_index=article.ai_analysis.tinkering_index if article.ai_analysis else 0,
                        )
                    except NotionServiceError as e:
                        logger.error(f"Failed to create page for '{article.title}': {e}")
                        return None

            results = await asyncio.gather(*(create_with_semaphore(a) for a in hardcore_articles))
            article_pages = [r for r in results if r is not None]
            logger.info(f"Created {len(article_pages)} article pages out of {len(hardcore_articles)} articles.")

            # 6. Check if all articles failed
            if hardcore_articles and not article_pages:
                logger.error("All article pages failed to create, skipping Discord notification")
                await interaction.followup.send("❌ 所有文章頁面建立失敗，請檢查 Notion 設定或稍後再試。")
                return

            # 7. Build Discord notification
            notification = notion.build_article_list_notification(article_pages, stats)

            # 8. Send results back to Discord with interactive buttons
            from app.bot.cogs.interactions import ReadLaterView, FilterView, DeepDiveView, MarkReadView  # Local import to prevent circular deps

            combined_view = FilterView(articles=hardcore_articles)
            for item in DeepDiveView(articles=hardcore_articles[:5]).children:
                combined_view.add_item(item)
            # Add ReadLaterButtons, capped at 10 to keep total components ≤ 25.
            # Discord allows 5 rows × 5 items = 25 slots, but a Select occupies a full row:
            # Row 0: 1 FilterSelect (width=5), Row 1: up to 5 DeepDiveButtons,
            # Rows 2-4: up to 10 ReadLaterButtons, Rows 4-5: up to 5 MarkReadButtons
            # → total max = 1 + 5 + 10 + 5 = 21 ≤ 25
            MAX_READ_LATER = 10
            read_later_view = ReadLaterView(articles=hardcore_articles[:MAX_READ_LATER])
            for item in read_later_view.children:
                combined_view.add_item(item)
            
            # Add MarkReadView buttons (limit 5 to stay within 25 component limit)
            MAX_MARK_READ = 5
            mark_read_view = MarkReadView(article_pages[:MAX_MARK_READ])
            for item in mark_read_view.children:
                combined_view.add_item(item)

            await interaction.followup.send(content=notification, view=combined_view)
            
        except Exception as e:
            logger.error(f"Error during /news_now execution: {e}", exc_info=True)
            await interaction.followup.send(f"❌ 發生錯誤：{e}")

    @app_commands.command(name="add_feed", description="將一個新的 RSS 訂閱源加入 Notion 資料庫")
    @app_commands.describe(
        name="訂閱源名稱 (例如: YCombinator)",
        url="RSS/Atom 網址",
        category="分類 (例如: AI, Frontend, Backend)"
    )
    async def add_feed(self, interaction: discord.Interaction, name: str, url: str, category: str):
        await interaction.response.defer(thinking=True)
        try:
            notion = NotionService()
            await notion.add_feed(name, url, category)
            await interaction.followup.send(
                f"✅ 已成功新增 `{name}` ({category}) 至 Notion！\n🔗 {url}"
            )
        except Exception as e:
            logger.error(f"Error during /add_feed execution: {e}", exc_info=True)
            await interaction.followup.send(f"❌ 新增失敗：{e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(NewsCommands(bot))
