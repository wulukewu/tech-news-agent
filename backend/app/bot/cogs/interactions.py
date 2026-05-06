import hashlib
import logging
from collections import Counter
from uuid import UUID

import discord
from discord.ext import commands

from app.core.exceptions import SupabaseServiceError
from app.schemas.article import ArticleSchema
from app.services.llm_service import LLMService
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class ReadLaterButton(discord.ui.Button):
    def __init__(
        self,
        article_id: "UUID | None" = None,
        article_title: str = "",
        supabase_service: "SupabaseService | None" = None,
        article: "Any | None" = None,
        index: int = 0,
    ):
        # Support old API: ReadLaterButton(article=article, index=0)
        if article is not None and article_id is None:
            article_id = getattr(article, "id", None) or getattr(article, "article_id", None)
            article_title = article_title or getattr(article, "title", "")
        label_text = (
            f"⭐ {article_title[:15]}..." if len(article_title) > 15 else f"⭐ {article_title}"
        )
        custom_id = f"read_later_{article_id}_{index}"
        super().__init__(style=discord.ButtonStyle.primary, label=label_text, custom_id=custom_id)
        self.article_id = article_id
        self.supabase_service = supabase_service

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        logger.info(
            f"User {interaction.user.id} clicked ReadLaterButton for article {self.article_id}"
        )

        try:
            discord_id = str(interaction.user.id)
            await self.supabase_service.save_to_reading_list(
                discord_id, self.article_id, source="discord"
            )

            self.disabled = True
            try:
                await interaction.message.edit(view=self.view)
            except discord.NotFound:
                logger.warning(
                    f"Message not found when editing view for user {interaction.user.id}"
                )
                pass  # message expired or was deleted, safe to ignore
            except discord.HTTPException as e:
                logger.warning(
                    f"HTTP error when editing message for user {interaction.user.id}: {e}"
                )
                pass  # Handle Discord API errors gracefully

            await interaction.followup.send("✅ 已加入閱讀清單！", ephemeral=True)
            logger.info(
                f"Successfully added article {self.article_id} to reading list for user {interaction.user.id}"
            )

        except SupabaseServiceError as e:
            logger.error(
                f"Database error in ReadLaterButton for user {interaction.user.id}, article {self.article_id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "article_id": str(self.article_id),
                    "button": "ReadLaterButton",
                    "error_type": "SupabaseServiceError",
                },
            )
            await interaction.followup.send("❌ 儲存失敗，請稍後再試。", ephemeral=True)
        except Exception as e:
            logger.error(
                f"Unexpected error in ReadLaterButton for user {interaction.user.id}, article {self.article_id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "article_id": str(self.article_id),
                    "button": "ReadLaterButton",
                    "error_type": type(e).__name__,
                },
            )
            await interaction.followup.send("❌ 發生未預期的錯誤，請稍後再試。", ephemeral=True)


class ReadLaterView(discord.ui.View):
    def __init__(self, articles: list[ArticleSchema], supabase_service: SupabaseService = None):
        # timeout=None makes the view persistent across bot restarts
        # (requires the view to be registered via bot.add_view() in setup_hook)
        super().__init__(timeout=None)
        self.supabase_service = supabase_service or SupabaseService()

        # In this UI design, we attach buttons dynamically based on the articles curated
        # Note: articles must have id field populated
        for article in articles:
            if article.id:
                self.add_item(ReadLaterButton(article.id, article.title, self.supabase_service))


class FilterSelect(discord.ui.Select):
    def __init__(self, articles: list[ArticleSchema], supabase_service: SupabaseService = None):
        self.articles = articles
        self.supabase_service = supabase_service

        category_counts = Counter(a.category for a in articles)
        top_categories = [cat for cat, _ in category_counts.most_common(24)]

        options = [discord.SelectOption(label="📋 顯示全部", value="__all__")]
        options += [discord.SelectOption(label=cat, value=cat) for cat in top_categories]

        super().__init__(placeholder="請選擇分類篩選文章…", options=options)

    async def callback(self, interaction: discord.Interaction):
        logger.info(
            f"User {interaction.user.id} clicked FilterSelect with value: {self.values[0] if self.values else 'none'}"
        )

        try:
            selected = self.values[0]

            if selected == "__all__":
                filtered = self.articles
            else:
                filtered = [a for a in self.articles if a.category == selected]

            if not filtered:
                await interaction.response.send_message("⚠️ 此分類目前沒有文章。", ephemeral=True)
                logger.info(
                    f"No articles found for category '{selected}' for user {interaction.user.id}"
                )
                return

            lines = []
            for article in filtered:
                lines.append(f"**{article.title}**")
                lines.append(f"🔗 {article.url}")
                lines.append(f"📂 {article.category}")
                lines.append("")
            content = "\n".join(lines).strip()

            if len(content) > 2000:
                content = content[:1997] + "..."

            # Add Read Later buttons for filtered articles (up to 5)
            view = None
            if self.supabase_service:
                view = discord.ui.View(timeout=None)
                for article in filtered[:5]:
                    if article.id:
                        btn = ReadLaterButton(article.id, article.title, self.supabase_service)
                        view.add_item(btn)

            await interaction.response.send_message(content, view=view, ephemeral=True)
            logger.info(
                f"Successfully sent filtered articles (category: {selected}) to user {interaction.user.id}"
            )

        except Exception as e:
            logger.error(
                f"Unexpected error in FilterSelect for user {interaction.user.id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "selected_value": self.values[0] if self.values else None,
                    "select": "FilterSelect",
                    "error_type": type(e).__name__,
                },
            )
            await interaction.response.send_message("❌ 篩選時發生錯誤，請稍後再試。", ephemeral=True)


class FilterView(discord.ui.View):
    def __init__(self, articles: list[ArticleSchema], supabase_service: SupabaseService = None):
        super().__init__(timeout=None)
        self.add_item(FilterSelect(articles, supabase_service=supabase_service))


class DeepDiveButton(discord.ui.Button):
    def __init__(self, article: ArticleSchema, llm_service: LLMService):
        label_text = (
            f"📖 {article.title[:20]}..." if len(article.title) > 20 else f"📖 {article.title}"
        )
        # Use article.id if available, otherwise fall back to URL hash
        if article.id:
            custom_id = f"deep_dive_{article.id}"
        else:
            custom_id = f"deep_dive_{hashlib.md5(str(article.url).encode()).hexdigest()[:8]}"
        super().__init__(style=discord.ButtonStyle.secondary, label=label_text, custom_id=custom_id)
        self.article = article
        self.llm_service = llm_service

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        logger.info(
            f"User {interaction.user.id} clicked DeepDiveButton for article {self.article.id if self.article.id else 'unknown'}"
        )

        try:
            result = await self.llm_service.generate_deep_dive(self.article)

            if len(result) > 2000:
                result = result[:1997] + "..."

            await interaction.followup.send(result, ephemeral=True)
            logger.info(f"Successfully sent deep dive analysis to user {interaction.user.id}")

        except LLMServiceError as e:
            logger.error(
                f"LLM error in DeepDiveButton for user {interaction.user.id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "article_id": str(self.article.id) if self.article.id else None,
                    "article_title": self.article.title,
                    "button": "DeepDiveButton",
                    "error_type": "LLMServiceError",
                },
            )
            await interaction.followup.send("❌ 生成深度摘要時發生錯誤，請稍後再試。", ephemeral=True)
        except Exception as e:
            logger.error(
                f"Unexpected error in DeepDiveButton for user {interaction.user.id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "article_id": str(self.article.id) if self.article.id else None,
                    "article_title": self.article.title,
                    "button": "DeepDiveButton",
                    "error_type": type(e).__name__,
                },
            )
            await interaction.followup.send("❌ 發生未預期的錯誤，請稍後再試。", ephemeral=True)


class DeepDiveView(discord.ui.View):
    def __init__(self, articles: list[ArticleSchema], llm_service: LLMService = None):
        super().__init__(timeout=None)
        self.llm_service = llm_service or LLMService()
        for article in articles[:5]:
            self.add_item(DeepDiveButton(article, self.llm_service))


class MarkReadButton(discord.ui.Button):
    def __init__(
        self,
        article_id_or_page: "UUID | Any",
        article_title: str = "",
        supabase_service: "SupabaseService | None" = None,
    ):
        from app.schemas.article import ArticlePageResult

        if isinstance(article_id_or_page, ArticlePageResult):
            page = article_id_or_page
            article_id = getattr(page, "article_id", None) or getattr(
                page, "page_id", str(id(page))
            )
            article_title = article_title or getattr(page, "title", "")
        else:
            article_id = article_id_or_page
        label_text = (
            f"✅ {article_title[:15]}..." if len(article_title) > 15 else f"✅ {article_title}"
        )
        custom_id = f"mark_read_{article_id}"
        super().__init__(style=discord.ButtonStyle.success, label=label_text, custom_id=custom_id)
        self.article_id = article_id
        self.supabase_service = supabase_service

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        logger.info(
            f"User {interaction.user.id} clicked MarkReadButton for article {self.article_id}"
        )

        try:
            discord_id = str(interaction.user.id)
            await self.supabase_service.update_article_status(discord_id, self.article_id, "Read")

            self.disabled = True
            try:
                await interaction.message.edit(view=self.view)
            except discord.NotFound:
                logger.warning(
                    f"Message not found when editing view for user {interaction.user.id}"
                )
                pass  # message expired or was deleted, safe to ignore
            except discord.HTTPException as e:
                logger.warning(
                    f"HTTP error when editing message for user {interaction.user.id}: {e}"
                )
                pass  # Handle Discord API errors gracefully

            await interaction.followup.send("✅ 已標記為已讀", ephemeral=True)
            logger.info(
                f"Successfully marked article {self.article_id} as read for user {interaction.user.id}"
            )

        except SupabaseServiceError as e:
            logger.error(
                f"Database error in MarkReadButton for user {interaction.user.id}, article {self.article_id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "article_id": str(self.article_id),
                    "button": "MarkReadButton",
                    "error_type": "SupabaseServiceError",
                },
            )
            await interaction.followup.send("❌ 標記失敗，請稍後再試", ephemeral=True)
        except Exception as e:
            logger.error(
                f"Unexpected error in MarkReadButton for user {interaction.user.id}, article {self.article_id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "article_id": str(self.article_id),
                    "button": "MarkReadButton",
                    "error_type": type(e).__name__,
                },
            )
            await interaction.followup.send("❌ 發生未預期的錯誤，請稍後再試。", ephemeral=True)


class MarkReadView(discord.ui.View):
    def __init__(self, articles: list[ArticleSchema], supabase_service: SupabaseService = None):
        super().__init__(timeout=None)
        self.supabase_service = supabase_service or SupabaseService()

        # Discord limit: max 25 components per view
        # articles must have id field populated
        for article in articles[:25]:
            if article.id:
                self.add_item(MarkReadButton(article.id, article.title, self.supabase_service))


class InteractionsCog(commands.Cog):
    """Interactions cog with service layer dependency injection."""

    def __init__(
        self,
        bot: commands.Bot,
        supabase_service: SupabaseService = None,
        llm_service: LLMService = None,
    ):
        self.bot = bot
        self.supabase_service = supabase_service or SupabaseService()
        self.llm_service = llm_service or LLMService()


async def setup(bot: commands.Bot):
    """Setup function with service layer dependency injection."""
    supabase_service = SupabaseService()
    llm_service = LLMService()
    await bot.add_cog(InteractionsCog(bot, supabase_service, llm_service))
