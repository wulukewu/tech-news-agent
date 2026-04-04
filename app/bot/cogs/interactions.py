import hashlib
import logging
from collections import Counter
from typing import List

import discord
from discord.ext import commands

from app.schemas.article import ArticleSchema, ArticlePageResult
from app.services.supabase_service import SupabaseService
from app.core.exceptions import SupabaseServiceError
from app.services.llm_service import LLMService

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
            supabase = SupabaseService()
            # Note: We need article_id (UUID) but we only have the article object
            # This is a limitation - we'd need to query the database to get the article_id
            # For now, we'll log a warning
            logger.warning(f"Cannot save article to reading list - article_id not available for {self.article.url}")
            await interaction.followup.send("❌ 此功能暫時無法使用（需要文章 ID）", ephemeral=True)
            
            # TODO: Implement proper article lookup by URL to get article_id
            # article_id = await supabase.get_article_id_by_url(str(self.article.url))
            # discord_id = str(interaction.user.id)
            # await supabase.save_to_reading_list(discord_id, article_id)
            
            # Disable the button after attempt
            # self.disabled = True
            # await interaction.followup.send(f"✅ 已成功將 **{self.article.title}** 加入閱讀清單！", ephemeral=True)
            # await interaction.message.edit(view=self.view)
        except Exception as e:
            logger.error(f"Interaction error: {e}")
            await interaction.followup.send("❌ 儲存時發生錯誤，請稍後再試。", ephemeral=True)


class ReadLaterView(discord.ui.View):
    def __init__(self, articles: list[ArticleSchema]):
        # timeout=None makes the view persistent across bot restarts
        # (requires the view to be registered via bot.add_view() in setup_hook)
        super().__init__(timeout=None)
        
        # In this UI design, we attach buttons dynamically based on the articles curated
        for i, article in enumerate(articles):
            self.add_item(ReadLaterButton(article, i))

class FilterSelect(discord.ui.Select):
    def __init__(self, articles: List[ArticleSchema]):
        self.articles = articles

        category_counts = Counter(a.source_category for a in articles)
        top_categories = [cat for cat, _ in category_counts.most_common(24)]

        options = [discord.SelectOption(label="📋 顯示全部", value="__all__")]
        options += [discord.SelectOption(label=cat, value=cat) for cat in top_categories]

        super().__init__(placeholder="請選擇分類篩選文章…", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            selected = self.values[0]

            if selected == "__all__":
                filtered = self.articles
            else:
                filtered = [a for a in self.articles if a.source_category == selected]

            if not filtered:
                await interaction.response.send_message("⚠️ 此分類目前沒有文章。", ephemeral=True)
                return

            lines = []
            for article in filtered:
                lines.append(f"**{article.title}**")
                lines.append(f"🔗 {article.url}")
                lines.append(f"📂 {article.source_category}")
                lines.append("")
            content = "\n".join(lines).strip()

            if len(content) > 2000:
                content = content[:1997] + "..."

            await interaction.response.send_message(content, ephemeral=True)
        except Exception as e:
            logger.error(f"FilterSelect callback error: {e}")
            await interaction.response.send_message("❌ 篩選時發生錯誤，請稍後再試。", ephemeral=True)


class FilterView(discord.ui.View):
    def __init__(self, articles: List[ArticleSchema]):
        super().__init__(timeout=None)
        self.add_item(FilterSelect(articles))


class DeepDiveButton(discord.ui.Button):
    def __init__(self, article: ArticleSchema):
        label_text = f"📖 {article.title[:20]}..." if len(article.title) > 20 else f"📖 {article.title}"
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=label_text,
            custom_id=f"deep_dive_{hashlib.md5(str(article.url).encode()).hexdigest()[:8]}"
        )
        self.article = article

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            result = await LLMService().generate_deep_dive(self.article)
            if len(result) > 2000:
                result = result[:1997] + "..."
            await interaction.followup.send(result, ephemeral=True)
        except Exception as e:
            logger.error(f"DeepDiveButton callback error: {e}")
            await interaction.followup.send("❌ 生成深度摘要時發生錯誤，請稍後再試。", ephemeral=True)


class DeepDiveView(discord.ui.View):
    def __init__(self, articles: List[ArticleSchema]):
        super().__init__(timeout=None)
        for article in articles[:5]:
            self.add_item(DeepDiveButton(article))


class MarkReadButton(discord.ui.Button):
    def __init__(self, article_page: ArticlePageResult):
        label_text = f"✅ {article_page.title[:15]}..." if len(article_page.title) > 15 else f"✅ {article_page.title}"
        super().__init__(
            style=discord.ButtonStyle.success,
            label=label_text,
            custom_id=f"mark_read_{article_page.page_id}"
        )
        self.article_page = article_page

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            supabase = SupabaseService()
            discord_id = str(interaction.user.id)
            # Note: page_id in the old system was a Notion page ID
            # In the new system, we need article_id (UUID)
            # The article_page.page_id might be a URL or other identifier
            # We need to look up the article by some identifier
            logger.warning(f"Cannot mark article as read - need to implement article lookup for page_id: {self.article_page.page_id}")
            await interaction.followup.send("❌ 此功能暫時無法使用（需要實作文章查詢）", ephemeral=True)
            
            # TODO: Implement proper article lookup
            # article_id = await supabase.get_article_id_by_url(self.article_page.page_url)
            # await supabase.update_article_status(discord_id, article_id, 'Read')
            
            # Disable the button after attempt
            # self.disabled = True
            # await interaction.followup.send(f"✅ 已標記「{self.article_page.title}」為已讀", ephemeral=True)
            # await interaction.message.edit(view=self.view)
        except SupabaseServiceError as e:
            logger.error(f"Mark read interaction error: {e}")
            await interaction.followup.send("❌ 標記失敗，請稍後再試", ephemeral=True)


class MarkReadView(discord.ui.View):
    def __init__(self, article_pages: List[ArticlePageResult]):
        super().__init__(timeout=None)
        
        # Discord limit: max 25 components per view
        for article_page in article_pages[:25]:
            self.add_item(MarkReadButton(article_page))


class InteractionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

async def setup(bot: commands.Bot):
    await bot.add_cog(InteractionsCog(bot))
