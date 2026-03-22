import logging
from typing import List

import discord
from discord import app_commands
from discord.ext import commands

from app.schemas.article import ReadingListItem
from app.services.notion_service import NotionService
from app.services.llm_service import LLMService
from app.core.exceptions import NotionServiceError, LLMServiceError

logger = logging.getLogger(__name__)

PAGE_SIZE = 5


class MarkAsReadButton(discord.ui.Button):
    def __init__(self, item: ReadingListItem, row: int):
        label = f"✅ 標記已讀"
        super().__init__(
            style=discord.ButtonStyle.success,
            label=label,
            custom_id=f"mark_read_{item.page_id}",
            row=row,
        )
        self.item = item

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            notion = NotionService()
            await notion.mark_as_read(self.item.page_id)
            self.disabled = True
            try:
                await interaction.message.edit(view=self.view)
            except discord.NotFound:
                pass  # message expired or was deleted, safe to ignore
            await interaction.followup.send(
                f"✅ 已將《{self.item.title}》標記為已讀！", ephemeral=True
            )
        except Exception as e:
            logger.error(f"MarkAsReadButton error for page {self.item.page_id}: {e}")
            await interaction.followup.send(
                "❌ 標記已讀時發生錯誤，請稍後再試。", ephemeral=True
            )


class RatingSelect(discord.ui.Select):
    def __init__(self, item: ReadingListItem, row: int):
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
            custom_id=f"rate_{item.page_id}",
            row=row,
        )
        self.item = item

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        rating = int(self.values[0])
        stars = "⭐" * rating
        try:
            notion = NotionService()
            await notion.rate_article(self.item.page_id, rating)
            await interaction.followup.send(
                f"✅ 已將《{self.item.title}》評為 {stars}（{rating} 星）！", ephemeral=True
            )
        except Exception as e:
            logger.error(f"RatingSelect error for page {self.item.page_id}: {e}")
            await interaction.followup.send(
                "❌ 評分時發生錯誤，請稍後再試。", ephemeral=True
            )


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
    def __init__(self, items: List[ReadingListItem], page: int = 0):
        super().__init__(timeout=300)
        self.items = items
        self.page = page
        self.page_size = PAGE_SIZE
        self._build_components()

    def _build_components(self):
        self.clear_items()

        # Row 0: pagination buttons
        self.add_item(PrevPageButton(self))
        self.add_item(NextPageButton(self))

        # Row 1: MarkAsReadButtons (up to 5 buttons, each width=1, total ≤ 5)
        # Rows 2–5 (one per article): RatingSelect (width=5, must be alone on its row)
        # Discord row width limit is 5 units; Select = 5, Button = 1.
        page_items = self._current_page_items()
        for item in page_items:
            self.add_item(MarkAsReadButton(item, row=1))
        for i, item in enumerate(page_items):
            self.add_item(RatingSelect(item, row=i + 2))  # rows 2–6 (max 5 items → rows 2–6)

    def _current_page_items(self) -> List[ReadingListItem]:
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
            lines.append(f"📂 {item.source_category}　⭐ {rating_str}")
            lines.append("")
        return "\n".join(lines).strip()

    async def update_message(self, interaction: discord.Interaction):
        self._build_components()
        content = self.build_page_content()
        await interaction.response.edit_message(content=content, view=self)


class ReadingListGroup(app_commands.Group):
    """斜線指令群組：/reading_list"""

    def __init__(self):
        super().__init__(name="reading_list", description="查看並管理 Notion 待讀清單")

    @app_commands.command(name="view", description="查看並管理 Notion 待讀清單")
    async def view(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            notion = NotionService()
            items = await notion.get_reading_list()
        except NotionServiceError as e:
            logger.error(f"reading_list view command error: {e}")
            await interaction.followup.send(f"❌ 無法取得待讀清單：{e}", ephemeral=True)
            return

        if not items:
            await interaction.followup.send("📭 目前待讀清單是空的！", ephemeral=True)
            return

        view = PaginationView(items)
        content = view.build_page_content()
        await interaction.followup.send(content, view=view, ephemeral=True)

    @app_commands.command(name="recommend", description="根據高評分文章生成推薦摘要")
    async def recommend(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            notion = NotionService()
            high_rated = await notion.get_highly_rated_articles(threshold=4)
        except NotionServiceError as e:
            logger.error(f"recommend command notion error: {e}")
            await interaction.followup.send(f"❌ 無法取得高評分文章：{e}", ephemeral=True)
            return

        if not high_rated:
            await interaction.followup.send(
                "尚無足夠的高評分文章，請先對文章評分（4 星以上）後再試。", ephemeral=True
            )
            return

        titles = [item.title for item in high_rated]
        categories = [item.source_category for item in high_rated]

        try:
            llm = LLMService()
            summary = await llm.generate_reading_recommendation(titles, categories)
        except LLMServiceError as e:
            logger.error(f"recommend command llm error: {e}")
            await interaction.followup.send("推薦功能暫時無法使用", ephemeral=True)
            return

        if len(summary) > 2000:
            summary = summary[:1997] + "..."
        await interaction.followup.send(summary, ephemeral=True)


class ReadingListCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reading_list_group = ReadingListGroup()
        bot.tree.add_command(self.reading_list_group)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.reading_list_group.name)


async def setup(bot: commands.Bot):
    await bot.add_cog(ReadingListCog(bot))
