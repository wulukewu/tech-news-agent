import logging
import re
from datetime import datetime, timezone, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from app.services.notion_service import NotionService, build_digest_title
from app.services.rss_service import RSSService
from app.services.llm_service import LLMService
from app.core.exceptions import NotionServiceError
from app.core.config import settings
from app.schemas.article import WeeklyDigestResult
from app.tasks.scheduler import build_discord_notification

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

            # Compute top articles (top 7 by tinkering_index descending)
            top_articles = sorted(
                hardcore_articles,
                key=lambda a: a.ai_analysis.tinkering_index if a.ai_analysis else 0,
                reverse=True,
            )[:7]

            # Build stats dict
            tz_taipei = timezone(timedelta(hours=8))
            dt = datetime.now(tz=tz_taipei)
            date_str = dt.strftime("%Y-%m-%d")
            stats = {
                "total_fetched": len(all_articles),
                "hardcore_count": len(hardcore_articles),
                "run_date": date_str,
            }

            # 4. Generate digest intro via LLM
            intro_text = await llm.generate_digest_intro(hardcore_articles)
            logger.info("Generated digest intro text.")

            # 5. Create Notion weekly digest page (graceful degradation)
            digest_result: WeeklyDigestResult | None = None
            title = build_digest_title(dt)
            published_date = dt.date()

            if not settings.notion_weekly_digests_db_id:
                logger.error("notion_weekly_digests_db_id is not configured; skipping Notion page creation.")
            else:
                try:
                    page_id, page_url = await notion.create_weekly_digest_page(
                        title=title,
                        published_date=published_date,
                        article_count=len(hardcore_articles),
                    )
                    digest_result = WeeklyDigestResult(
                        page_id=page_id,
                        page_url=page_url,
                        article_count=len(hardcore_articles),
                        top_articles=top_articles,
                    )
                    logger.info(f"Created Notion weekly digest page: {page_url}")

                    # 6. Build and append blocks to the Notion page
                    blocks = notion.build_digest_blocks(top_articles, intro_text, stats)
                    await notion.append_digest_blocks(page_id, blocks)
                    logger.info("Appended digest blocks to Notion page.")

                except NotionServiceError as e:
                    logger.error(f"Notion page creation failed, continuing with degraded notification: {e}")
                    digest_result = None

            # 7. Build lightweight Discord notification
            notification = build_discord_notification(digest_result, top_articles, stats)

            # 8. Send results back to Discord with interactive buttons
            from app.bot.cogs.interactions import ReadLaterView, FilterView, DeepDiveView  # Local import to prevent circular deps

            combined_view = FilterView(articles=hardcore_articles)
            for item in DeepDiveView(articles=hardcore_articles[:5]).children:
                combined_view.add_item(item)
            # Add ReadLaterButtons, capped at 15 to keep total components ≤ 25.
            # Discord allows 5 rows × 5 items = 25 slots, but a Select occupies a full row:
            # Row 0: 1 FilterSelect (width=5), Row 1: up to 5 DeepDiveButtons,
            # Rows 2-4: up to 15 ReadLaterButtons → total max = 1 + 5 + 15 = 21 ≤ 25
            MAX_READ_LATER = 15
            read_later_view = ReadLaterView(articles=hardcore_articles[:MAX_READ_LATER])
            for item in read_later_view.children:
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
