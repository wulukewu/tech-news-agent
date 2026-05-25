import hashlib
import logging
from collections import Counter
from uuid import UUID

import discord
from discord.ext import commands

from app.bot.utils.thread_utils import ensure_discussion_thread
from app.core.exceptions import SupabaseServiceError
from app.schemas.article import ArticleSchema
from app.services.llm_service import LLMService
from app.services.notion_service import NotionService as NotionService  # noqa: F401
from app.services.supabase_service import SupabaseService
from app.services.thread_memory_service import ThreadMemoryService

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


class ReadLaterSelect(discord.ui.Select):
    def __init__(self, articles: list[ArticleSchema], supabase_service: SupabaseService = None):
        self.supabase_service = supabase_service or SupabaseService()
        options = []
        for i, article in enumerate(articles):
            if article.id:
                label = f"{i+1}. {article.title}"
                if len(label) > 100:
                    label = label[:97] + "..."

                desc = f"分類: {article.category}"
                if article.feed_name:
                    desc += f" | 來源: {article.feed_name}"
                if len(desc) > 100:
                    desc = desc[:97] + "..."

                options.append(
                    discord.SelectOption(
                        label=label,
                        value=str(article.id),
                        description=desc,
                        emoji="⭐",
                    )
                )

        super().__init__(
            placeholder="⭐ 收藏文章至待讀清單…",
            options=options,
            custom_id="news_read_later_select",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            article_id = self.values[0]
            discord_id = str(interaction.user.id)
            await self.supabase_service.save_to_reading_list(
                discord_id, article_id, source="discord"
            )
            await interaction.followup.send("✅ 已加入閱讀清單！", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in ReadLaterSelect callback: {e}", exc_info=True)
            await interaction.followup.send("❌ 收藏失敗，請稍後再試。", ephemeral=True)


class MarkReadSelect(discord.ui.Select):
    def __init__(self, articles: list[ArticleSchema], supabase_service: SupabaseService = None):
        self.supabase_service = supabase_service or SupabaseService()
        options = []
        for i, article in enumerate(articles):
            if article.id:
                label = f"{i+1}. {article.title}"
                if len(label) > 100:
                    label = label[:97] + "..."

                desc = f"分類: {article.category}"
                if article.feed_name:
                    desc += f" | 來源: {article.feed_name}"
                if len(desc) > 100:
                    desc = desc[:97] + "..."

                options.append(
                    discord.SelectOption(
                        label=label,
                        value=str(article.id),
                        description=desc,
                        emoji="✅",
                    )
                )

        super().__init__(
            placeholder="✅ 將文章標記為已讀…",
            options=options,
            custom_id="news_mark_read_select",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            article_id = self.values[0]
            discord_id = str(interaction.user.id)
            await self.supabase_service.update_article_status(discord_id, article_id, "Read")
            await interaction.followup.send("✅ 已將文章標記為已讀！", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in MarkReadSelect callback: {e}", exc_info=True)
            await interaction.followup.send("❌ 標記失敗，請稍後再試。", ephemeral=True)


class DeepDiveSelect(discord.ui.Select):
    def __init__(
        self,
        articles: list[ArticleSchema],
        llm_service: LLMService = None,
        supabase_service: SupabaseService = None,
    ):
        self.llm_service = llm_service or LLMService()
        self.supabase_service = supabase_service or SupabaseService()
        options = []
        for i, article in enumerate(articles):
            if article.id:
                label = f"{i+1}. {article.title}"
                if len(label) > 100:
                    label = label[:97] + "..."

                desc = f"分類: {article.category}"
                if article.feed_name:
                    desc += f" | 來源: {article.feed_name}"
                if len(desc) > 100:
                    desc = desc[:97] + "..."

                options.append(
                    discord.SelectOption(
                        label=label,
                        value=str(article.id),
                        description=desc,
                        emoji="📖",
                    )
                )

        super().__init__(
            placeholder="📖 產生 AI 深度分析…",
            options=options,
            custom_id="news_deep_dive_select",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            article_id = self.values[0]
            discord_id = str(interaction.user.id)

            # Fetch article details
            response = (
                self.supabase_service.client.table("articles")
                .select("*")
                .eq("id", str(article_id))
                .execute()
            )

            if not response.data:
                await interaction.followup.send("❌ 找不到該文章", ephemeral=True)
                return

            article_data = response.data[0]

            from datetime import datetime

            from app.schemas.article import ArticleSchema

            article = ArticleSchema(
                id=UUID(article_data["id"]) if article_data.get("id") else None,
                title=article_data["title"],
                url=article_data["url"],
                category=article_data.get("category") or "Unknown",
                tinkering_index=article_data.get("tinkering_index"),
                ai_summary=article_data.get("ai_summary"),
                published_at=(
                    datetime.fromisoformat(article_data["published_at"].replace("Z", "+00:00"))
                    if article_data.get("published_at")
                    else None
                ),
                feed_id=UUID(article_data["feed_id"]) if article_data.get("feed_id") else None,
                feed_name=article_data.get("feed_name") or "",
            )

            thread, created = await ensure_discussion_thread(
                interaction=interaction,
                thread_name=f"deep-dive-{article.title[:40]}",
            )
            if created:
                await interaction.followup.send(
                    f"✅ 已建立深度分析討論串：{thread.mention}",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send("✅ 已在此討論串提供深度分析。", ephemeral=True)

            await thread.send(f"📖 **深度分析標的**：{article.title}")
            result = await self.llm_service.generate_deep_dive(article)
            await thread.send(result[:2000])

            user = await self.supabase_service.get_user_by_discord_id(discord_id)
            if user:
                memory_service = ThreadMemoryService(supabase_service=self.supabase_service)
                conversation = await memory_service.get_or_create_thread_conversation(
                    user_id=str(user["id"]),
                    thread_id=str(thread.id),
                    title=f"Deep Dive: {article.title}",
                    article_id=str(article.id) if article.id else None,
                )
                await memory_service.save_assistant_message(conversation.id, str(thread.id), result)

        except Exception as e:
            logger.error(f"Error in DeepDiveSelect callback: {e}", exc_info=True)
            await interaction.followup.send("❌ 發生未預期的錯誤，請稍後再試。", ephemeral=True)


class DeepDiveButton(discord.ui.Button):
    def __init__(
        self,
        article: ArticleSchema,
        llm_service: "LLMService | None" = None,
        supabase_service: "SupabaseService | None" = None,
    ):
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
        self.supabase_service = supabase_service or SupabaseService()

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        logger.info(
            f"User {interaction.user.id} clicked DeepDiveButton for article {self.article.id if self.article.id else 'unknown'}"
        )

        try:
            thread, created = await ensure_discussion_thread(
                interaction=interaction,
                thread_name=f"deep-dive-{self.article.title[:40]}",
            )
            if created:
                await interaction.followup.send(
                    f"✅ 已建立深度分析討論串：{thread.mention}",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send("✅ 已在此討論串提供深度分析。", ephemeral=True)

            await thread.send(f"📖 **深度分析標的**：{self.article.title}")
            result = await self.llm_service.generate_deep_dive(self.article)
            await thread.send(result[:2000])

            user = await self.supabase_service.get_user_by_discord_id(str(interaction.user.id))
            if user:
                memory_service = ThreadMemoryService(supabase_service=self.supabase_service)
                conversation = await memory_service.get_or_create_thread_conversation(
                    user_id=str(user["id"]),
                    thread_id=str(thread.id),
                    title=f"Deep Dive: {self.article.title}",
                    article_id=str(self.article.id) if self.article.id else None,
                )
                await memory_service.save_assistant_message(conversation.id, str(thread.id), result)
            logger.info(
                f"Successfully sent deep dive analysis in thread for user {interaction.user.id}"
            )
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
    def __init__(
        self,
        articles: list[ArticleSchema],
        llm_service: LLMService = None,
        supabase_service: SupabaseService = None,
    ):
        super().__init__(timeout=None)
        self.llm_service = llm_service or LLMService()
        self.supabase_service = supabase_service or SupabaseService()
        for article in articles[:5]:
            self.add_item(DeepDiveButton(article, self.llm_service, self.supabase_service))


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
            article_id = (
                getattr(article, "id", None)
                or getattr(article, "article_id", None)
                or getattr(article, "page_id", None)
            )
            if article_id:
                self.add_item(MarkReadButton(article_id, article.title, self.supabase_service))


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
