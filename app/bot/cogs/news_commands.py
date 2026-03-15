import logging
import discord
from discord import app_commands
from discord.ext import commands

from app.services.notion_service import NotionService
from app.services.rss_service import RSSService
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class NewsCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(name="news_now", description="強制立即抓取並生成本週的技術新聞報表")
    async def news_now(self, interaction: discord.Interaction):
        logger.info(f"Command /news_now triggered by {interaction.user}")
        # Notify the user that processing has started, because LLM inference takes time
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
            
            # 4. Generate Markdown
            from app.bot.cogs.interactions import ReadLaterView # Local import to prevent circular deps
            
            draft = await llm.generate_weekly_newsletter(hardcore_articles)
            
            # 5. Send results back to Discord Channel
            view = ReadLaterView(articles=hardcore_articles[:7]) # Attach read later buttons for top 7
            
            # Note: Discord limit is 4000 for standard embeds or 2000 for messages. 
            # We enforce 3500 max in the LLM prompt.
            await interaction.followup.send(content=draft, view=view)
            
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
        # We can directly use Notion API to add a new row here
        # For full implementation, we'd add `add_feed` to notion_service.py
        # Here's a placeholder response
        await interaction.response.send_message(f"✅ 已收到您的請求：新增 `{name}` ({category})\n🔗 {url}\n\n*(此功能 Notion 寫入邏輯待實作)*")


async def setup(bot: commands.Bot):
    await bot.add_cog(NewsCommands(bot))
