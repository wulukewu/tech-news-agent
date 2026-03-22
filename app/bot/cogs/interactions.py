import hashlib
import logging
import discord
from discord.ext import commands

from app.schemas.article import ArticleSchema
from app.services.notion_service import NotionService

logger = logging.getLogger(__name__)

class ReadLaterButton(discord.ui.Button):
    def __init__(self, article: ArticleSchema, index: int):
        # Labels have limits, so we truncate the title slightly for the button
        label_text = f"⭐ 稍後閱讀: {article.title[:20]}..." if len(article.title) > 20 else f"⭐ 稍後閱讀: {article.title}"
        super().__init__(style=discord.ButtonStyle.primary, label=label_text, custom_id=f"read_later_{hashlib.md5(str(article.url).encode()).hexdigest()[:8]}")
        self.article = article

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True) # Ephemeral means only the user clicking sees the response
        try:
            notion = NotionService()
            await notion.add_to_read_later(self.article)
            
            # Disable the button after successful save
            self.disabled = True
            await interaction.followup.send(f"✅ 已成功將 **{self.article.title}** 加入 Notion 的「稍後閱讀」清單！", ephemeral=True)
            await interaction.message.edit(view=self.view)
        except Exception as e:
            logger.error(f"Interaction error: {e}")
            await interaction.followup.send("❌ 存入 Notion 時發生錯誤，請稍後再試。", ephemeral=True)


class ReadLaterView(discord.ui.View):
    def __init__(self, articles: list[ArticleSchema]):
        # timeout=None makes the view persistent across bot restarts
        # (requires the view to be registered via bot.add_view() in setup_hook)
        super().__init__(timeout=None)
        
        # In this UI design, we attach buttons dynamically based on the articles curated
        for i, article in enumerate(articles):
            self.add_item(ReadLaterButton(article, i))

class InteractionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

async def setup(bot: commands.Bot):
    await bot.add_cog(InteractionsCog(bot))
