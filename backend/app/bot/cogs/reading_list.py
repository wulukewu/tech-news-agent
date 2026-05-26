import discord
from discord import app_commands
from discord.ext import commands

from app.core.exceptions import LLMServiceError, SupabaseServiceError
from app.core.logger import get_logger
from app.schemas.article import ReadingListItem
from app.services.llm_service import LLMService
from app.services.notion_service import NotionService as NotionService  # noqa: F401
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)

# Discord UI has a maximum of 5 rows (0-4)
# Row 0: Pagination buttons
# Row 1: ReadingListMarkReadSelect
# Row 2: ReadingListRemoveSelect
PAGE_SIZE = 5


class MarkAsReadButton(discord.ui.Button):
    def __init__(self, item: ReadingListItem, row: int, supabase_service: SupabaseService = None):
        label = "✅ 標記已讀"
        super().__init__(
            style=discord.ButtonStyle.success,
            label=label,
            custom_id=f"mark_read_{item.article_id}",
            row=row,
        )
        self.item = item
        self.supabase_service = supabase_service

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        discord_id = str(interaction.user.id)
        logger.info(
            f"MarkAsReadButton clicked by user {discord_id} for article {self.item.article_id}"
        )
        try:
            await self.supabase_service.update_article_status(
                discord_id, self.item.article_id, "Read"
            )
            self.disabled = True
            try:
                await interaction.message.edit(view=self.view)
            except Exception:
                pass
            await interaction.followup.send(f"✅ 已將《{self.item.title}》標記為已讀！", ephemeral=True)
            logger.info(f"Successfully marked article as read via button for user {discord_id}")
        except Exception as e:
            logger.error(f"Error in MarkAsReadButton callback: {e}", exc_info=True)
            await interaction.followup.send("❌ 標記已讀時發生錯誤，請稍後再試。", ephemeral=True)


class RatingSelect(discord.ui.Select):
    def __init__(self, item: ReadingListItem, row: int, supabase_service: SupabaseService = None):
        options = [
            discord.SelectOption(label="⭐", value="1"),
            discord.SelectOption(label="⭐⭐", value="2"),
            discord.SelectOption(label="⭐⭐⭐", value="3"),
            discord.SelectOption(label="⭐⭐⭐⭐", value="4"),
            discord.SelectOption(label="⭐⭐⭐⭐⭐", value="5"),
        ]
        title_short = item.title[:20] + "…" if len(item.title) > 20 else item.title
        super().__init__(
            placeholder=f"評分：{title_short}",
            options=options,
            custom_id=f"rate_{item.article_id}",
            row=row,
        )
        self.item = item
        self.supabase_service = supabase_service

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            rating = int(self.values[0])
            discord_id = str(interaction.user.id)
            await self.supabase_service.update_article_rating(
                discord_id, self.item.article_id, rating
            )
            await interaction.followup.send(f"✅ 已評為 {rating} 星！{'⭐' * rating}", ephemeral=True)
        except Exception:
            await interaction.followup.send("❌ 評分時發生錯誤，請稍後再試。", ephemeral=True)


class ReadingListMarkReadSelect(discord.ui.Select):
    def __init__(self, items: list[ReadingListItem], supabase_service: SupabaseService = None):
        self.supabase_service = supabase_service or SupabaseService()
        options = []
        for i, item in enumerate(items):
            label = f"{i+1}. {item.title}"
            if len(label) > 100:
                label = label[:97] + "..."

            desc = f"分類: {item.category}"
            if item.rating:
                desc += f" | 評分: {'⭐' * item.rating}"
            if len(desc) > 100:
                desc = desc[:97] + "..."

            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(item.article_id),
                    description=desc,
                    emoji="✅",
                )
            )

        super().__init__(
            placeholder="✅ 將文章標記為已讀…",
            options=options,
            custom_id="reading_list_mark_read_select",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            from uuid import UUID

            article_id = self.values[0]
            discord_id = str(interaction.user.id)
            await self.supabase_service.update_article_status(discord_id, UUID(article_id), "Read")
            await interaction.followup.send("✅ 已標記為已讀！", ephemeral=True)

            # Update the view dynamically to reflect the removed item
            if self.view:
                self.view.items = [x for x in self.view.items if str(x.article_id) != article_id]
                await self.view.update_message(interaction)
            else:
                # Reconstruct statelessly
                items = await self.supabase_service.get_reading_list(discord_id, status="Unread")
                if not items:
                    await interaction.message.edit(content="📭 目前待讀清單是空的！", view=None)
                else:
                    view = PaginationView(items, supabase_service=self.supabase_service)
                    content = view.build_page_content()
                    await interaction.message.edit(content=content, view=view)
        except Exception as e:
            logger.error(f"Error in ReadingListMarkReadSelect callback: {e}", exc_info=True)
            await interaction.followup.send("❌ 標記失敗，請稍後再試。", ephemeral=True)


class ReadingListRemoveSelect(discord.ui.Select):
    def __init__(self, items: list[ReadingListItem], supabase_service: SupabaseService = None):
        self.supabase_service = supabase_service or SupabaseService()
        options = []
        for i, item in enumerate(items):
            label = f"{i+1}. {item.title}"
            if len(label) > 100:
                label = label[:97] + "..."

            desc = f"分類: {item.category}"
            if item.rating:
                desc += f" | 評分: {'⭐' * item.rating}"
            if len(desc) > 100:
                desc = desc[:97] + "..."

            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(item.article_id),
                    description=desc,
                    emoji="❌",
                )
            )

        super().__init__(
            placeholder="❌ 從待讀清單中移除文章…",
            options=options,
            custom_id="reading_list_remove_select",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            from uuid import UUID

            article_id = self.values[0]
            discord_id = str(interaction.user.id)
            await self.supabase_service.remove_from_reading_list(discord_id, UUID(article_id))
            await interaction.followup.send("✅ 已從待讀清單移除該文章！", ephemeral=True)

            # Update the view dynamically to reflect the removed item
            if self.view:
                self.view.items = [x for x in self.view.items if str(x.article_id) != article_id]
                await self.view.update_message(interaction)
            else:
                # Reconstruct statelessly
                items = await self.supabase_service.get_reading_list(discord_id, status="Unread")
                if not items:
                    await interaction.message.edit(content="📭 目前待讀清單是空的！", view=None)
                else:
                    view = PaginationView(items, supabase_service=self.supabase_service)
                    content = view.build_page_content()
                    await interaction.message.edit(content=content, view=view)
        except Exception as e:
            logger.error(f"Error in ReadingListRemoveSelect callback: {e}", exc_info=True)
            await interaction.followup.send("❌ 移除失敗，請稍後再試。", ephemeral=True)


class PrevPageButton(discord.ui.Button):
    def __init__(self, view: "PaginationView"):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="◀ 上一頁",
            custom_id="prev_page",
            row=0,
            disabled=view.page == 0,
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.page -= 1
        await self.view.update_message(interaction)


class NextPageButton(discord.ui.Button):
    def __init__(self, view: "PaginationView"):
        total_pages = (len(view.items) + PAGE_SIZE - 1) // PAGE_SIZE
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="下一頁 ▶",
            custom_id="next_page",
            row=0,
            disabled=view.page >= total_pages - 1,
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.page += 1
        await self.view.update_message(interaction)


class PaginationView(discord.ui.View):
    def __init__(
        self, items: list[ReadingListItem], page: int = 0, supabase_service: SupabaseService = None
    ):
        super().__init__(timeout=None)
        self.items = items
        self.page = page
        self.page_size = PAGE_SIZE
        self.supabase_service = supabase_service or SupabaseService()
        self._build_components()

    def _build_components(self):
        self.clear_items()

        # Row 0: pagination buttons
        self.add_item(PrevPageButton(self))
        self.add_item(NextPageButton(self))

        page_items = self._current_page_items()

        if page_items:
            # Row 1: MarkRead dropdown
            mark_read_select = ReadingListMarkReadSelect(page_items, self.supabase_service)
            mark_read_select.row = 1
            self.add_item(mark_read_select)

            # Row 2: Remove dropdown
            remove_select = ReadingListRemoveSelect(page_items, self.supabase_service)
            remove_select.row = 2
            self.add_item(remove_select)

    def _current_page_items(self) -> list[ReadingListItem]:
        start = self.page * self.page_size
        return self.items[start : start + self.page_size]

    def build_page_content(self) -> str:
        page_items = self._current_page_items()
        total_pages = (len(self.items) + self.page_size - 1) // self.page_size
        lines = [f"📚 **待讀清單**（第 {self.page + 1} / {total_pages} 頁，共 {len(self.items)} 篇）\n"]
        for i, item in enumerate(page_items, start=1):
            rating_str = "⭐" * item.rating if item.rating else "未評分"
            lines.append(f"**{i}. {item.title}**")
            lines.append(f"🔗 {item.url}")
            lines.append(f"📂 {item.category}　⭐ {rating_str}")
            lines.append(f"🆔 `{item.article_id}`")
            lines.append("")
        return "\n".join(lines).strip()

    async def update_message(self, interaction: discord.Interaction):
        if not self.items:
            try:
                await interaction.response.edit_message(content="📭 目前待讀清單是空的！", view=None)
            except discord.InteractionResponded:
                await interaction.message.edit(content="📭 目前待讀清單是空的！", view=None)
            return

        total_pages = (len(self.items) + self.page_size - 1) // self.page_size
        if self.page >= total_pages:
            self.page = max(0, total_pages - 1)

        self._build_components()
        content = self.build_page_content()
        try:
            await interaction.response.edit_message(content=content, view=self)
        except discord.InteractionResponded:
            await interaction.message.edit(content=content, view=self)


class ReadingListGroup(app_commands.Group):
    """斜線指令群組：/reading_list with service layer dependency injection"""

    def __init__(self, supabase_service: SupabaseService = None, llm_service: LLMService = None):
        super().__init__(name="reading_list", description="查看並管理待讀清單")
        self.supabase_service = supabase_service or SupabaseService()
        self.llm_service = llm_service or LLMService()

    @app_commands.command(name="view", description="查看並管理待讀清單")
    async def view(self, interaction: discord.Interaction):
        logger.info(
            "Command /reading_list view triggered",
            user_id=str(interaction.user.id),
            command="reading_list_view",
        )
        await interaction.response.defer(ephemeral=True)

        try:
            discord_id = str(interaction.user.id)
            items = await self.supabase_service.get_reading_list(discord_id, status="Unread")

            if not items:
                logger.info("User has empty reading list", user_id=str(interaction.user.id))
                await interaction.followup.send("📭 目前待讀清單是空的！", ephemeral=True)
                return

            view = PaginationView(items, supabase_service=self.supabase_service)
            content = view.build_page_content()
            await interaction.followup.send(content, view=view, ephemeral=True)
            logger.info(
                "Successfully sent reading list to user",
                user_id=str(interaction.user.id),
                item_count=len(items),
            )

        except SupabaseServiceError as e:
            logger.error(
                "Database error in /reading_list view",
                user_id=str(interaction.user.id),
                command="reading_list_view",
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 無法取得待讀清單，請稍後再試。\n" "💡 建議：資料庫連線可能暫時中斷，請稍後再試或聯繫管理員。",
                ephemeral=True,
            )
        except Exception as e:
            logger.critical(
                "Unexpected error in /reading_list view",
                user_id=str(interaction.user.id),
                command="reading_list_view",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。\n" "💡 建議：如果問題持續發生，請聯繫管理員並提供你的使用者 ID。",
                ephemeral=True,
            )

    async def _article_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete: prefix-search reading list articles by title."""
        try:
            discord_id = str(interaction.user.id)
            user_uuid = await self.supabase_service.get_or_create_user(discord_id)
            resp = (
                self.supabase_service.client.table("reading_list")
                .select("article_id, articles(id, title)")
                .eq("user_id", str(user_uuid))
                .ilike("articles.title", f"{current}%")
                .limit(25)
                .execute()
            )
            results = []
            for row in resp.data or []:
                art = row.get("articles")
                if art:
                    title = art["title"][:100]  # Choice name max 100 chars
                    results.append(app_commands.Choice(name=title, value=str(art["id"])))
            return results
        except Exception:
            return []

    @app_commands.command(name="remove", description="從待讀清單移除文章")
    @app_commands.describe(article_id="文章標題（輸入可自動補全）")
    @app_commands.autocomplete(article_id=_article_autocomplete)
    async def remove(self, interaction: discord.Interaction, article_id: str):
        logger.info(
            "Command /reading_list remove triggered",
            user_id=str(interaction.user.id),
            article_id=article_id,
        )
        await interaction.response.defer(ephemeral=True)

        try:
            from uuid import UUID

            try:
                parsed_id = UUID(article_id)
            except ValueError:
                await interaction.followup.send("❌ 無效的文章 ID 格式。", ephemeral=True)
                return

            discord_id = str(interaction.user.id)
            removed = await self.supabase_service.remove_from_reading_list(discord_id, parsed_id)

            if removed:
                await interaction.followup.send("✅ 已從待讀清單移除該文章。", ephemeral=True)
            else:
                await interaction.followup.send("ℹ️ 找不到該文章，可能已被移除。", ephemeral=True)

        except SupabaseServiceError as e:
            logger.error(
                "Database error in /reading_list remove",
                user_id=str(interaction.user.id),
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send("❌ 移除失敗，請稍後再試。", ephemeral=True)
        except Exception as e:
            logger.critical(
                "Unexpected error in /reading_list remove",
                user_id=str(interaction.user.id),
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send("❌ 發生未預期的錯誤，請稍後再試。", ephemeral=True)

    @app_commands.command(name="recommend", description="根據高評分文章生成推薦摘要")
    async def recommend(self, interaction: discord.Interaction):
        logger.info(
            "Command /reading_list recommend triggered",
            user_id=str(interaction.user.id),
            command="reading_list_recommend",
        )
        await interaction.response.defer(ephemeral=True)

        try:
            discord_id = str(interaction.user.id)
            high_rated = await self.supabase_service.get_highly_rated_articles(
                discord_id, threshold=4
            )

            if not high_rated:
                logger.info("User has no highly rated articles", user_id=str(interaction.user.id))
                await interaction.followup.send("尚無足夠的高評分文章，請先對文章評分（4 星以上）後再試。", ephemeral=True)
                return

            titles = [item.title for item in high_rated]
            categories = [item.category for item in high_rated]

            logger.info(
                "Generating recommendation for user",
                user_id=str(interaction.user.id),
                high_rated_count=len(high_rated),
            )

            try:
                summary = await self.llm_service.generate_reading_recommendation(titles, categories)

                if len(summary) > 2000:
                    summary = summary[:1997] + "..."

                await interaction.followup.send(summary, ephemeral=True)
                logger.info(
                    "Successfully sent recommendation to user", user_id=str(interaction.user.id)
                )

            except LLMServiceError as e:
                logger.error(
                    "LLM error in /reading_list recommend",
                    user_id=str(interaction.user.id),
                    command="reading_list_recommend",
                    error=str(e),
                    exc_info=True,
                )
                await interaction.followup.send(
                    "❌ 推薦功能暫時無法使用，請稍後再試。\n" "💡 建議：AI 服務可能暫時無法連線，請稍後再試。",
                    ephemeral=True,
                )

        except SupabaseServiceError as e:
            logger.error(
                "Database error in /reading_list recommend",
                user_id=str(interaction.user.id),
                command="reading_list_recommend",
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 無法取得高評分文章，請稍後再試。\n" "💡 建議：資料庫連線可能暫時中斷，請稍後再試或聯繫管理員。",
                ephemeral=True,
            )
        except Exception as e:
            logger.critical(
                "Unexpected error in /reading_list recommend",
                user_id=str(interaction.user.id),
                command="reading_list_recommend",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。\n" "💡 建議：如果問題持續發生，請聯繫管理員並提供你的使用者 ID。",
                ephemeral=True,
            )


class ReadingListCog(commands.Cog):
    """Reading list cog with service layer dependency injection."""

    def __init__(
        self,
        bot: commands.Bot,
        supabase_service: SupabaseService = None,
        llm_service: LLMService = None,
    ):
        self.bot = bot
        self.supabase_service = supabase_service or SupabaseService()
        self.llm_service = llm_service or LLMService()
        self.reading_list_group = ReadingListGroup(
            supabase_service=self.supabase_service, llm_service=self.llm_service
        )
        bot.tree.add_command(self.reading_list_group)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.reading_list_group.name)


async def setup(bot: commands.Bot):
    """Setup function with service layer dependency injection."""
    supabase_service = SupabaseService()
    llm_service = LLMService()
    await bot.add_cog(ReadingListCog(bot, supabase_service, llm_service))
