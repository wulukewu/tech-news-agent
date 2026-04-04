import logging
from typing import List

import discord
from discord import app_commands
from discord.ext import commands

from app.schemas.article import ReadingListItem
from app.services.supabase_service import SupabaseService
from app.services.llm_service import LLMService
from app.core.exceptions import SupabaseServiceError, LLMServiceError
from app.bot.utils.validators import validate_rating

logger = logging.getLogger(__name__)

PAGE_SIZE = 5


class MarkAsReadButton(discord.ui.Button):
    def __init__(self, item: ReadingListItem, row: int):
        label = f"✅ 標記已讀"
        super().__init__(
            style=discord.ButtonStyle.success,
            label=label,
            custom_id=f"mark_read_{item.article_id}",
            row=row,
        )
        self.item = item

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        logger.info(f"User {interaction.user.id} clicked MarkAsReadButton for article {self.item.article_id}")
        
        try:
            supabase = SupabaseService()
            discord_id = str(interaction.user.id)
            await supabase.update_article_status(discord_id, self.item.article_id, 'Read')
            
            self.disabled = True
            try:
                await interaction.message.edit(view=self.view)
            except discord.NotFound:
                logger.warning(f"Message not found when editing view for user {interaction.user.id}")
                pass  # message expired or was deleted, safe to ignore
            except discord.HTTPException as e:
                logger.warning(f"HTTP error when editing message for user {interaction.user.id}: {e}")
                pass  # Handle Discord API errors gracefully
                
            await interaction.followup.send(
                f"✅ 已將《{self.item.title}》標記為已讀！", ephemeral=True
            )
            logger.info(f"Successfully marked article {self.item.article_id} as read for user {interaction.user.id}")
            
        except SupabaseServiceError as e:
            logger.error(
                f"Database error in MarkAsReadButton for user {interaction.user.id}, article {self.item.article_id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "article_id": str(self.item.article_id),
                    "button": "MarkAsReadButton",
                    "error_type": "SupabaseServiceError"
                }
            )
            await interaction.followup.send(
                "❌ 標記已讀時發生錯誤，請稍後再試。", ephemeral=True
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in MarkAsReadButton for user {interaction.user.id}, article {self.item.article_id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "article_id": str(self.item.article_id),
                    "button": "MarkAsReadButton",
                    "error_type": type(e).__name__
                }
            )
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。", ephemeral=True
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
            custom_id=f"rate_{item.article_id}",
            row=row,
        )
        self.item = item

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        rating = int(self.values[0])
        
        # Validate rating
        is_valid, error_msg = validate_rating(rating)
        if not is_valid:
            logger.warning(f"Invalid rating {rating} from user {interaction.user.id}: {error_msg}")
            await interaction.followup.send(
                f"❌ {error_msg}", ephemeral=True
            )
            return
        
        stars = "⭐" * rating
        
        logger.info(f"User {interaction.user.id} rating article {self.item.article_id} with {rating} stars")
        
        try:
            supabase = SupabaseService()
            discord_id = str(interaction.user.id)
            await supabase.update_article_rating(discord_id, self.item.article_id, rating)
            
            await interaction.followup.send(
                f"✅ 已將《{self.item.title}》評為 {stars}（{rating} 星）！", ephemeral=True
            )
            logger.info(f"Successfully rated article {self.item.article_id} with {rating} stars for user {interaction.user.id}")
            
        except SupabaseServiceError as e:
            logger.error(
                f"Database error in RatingSelect for user {interaction.user.id}, article {self.item.article_id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "article_id": str(self.item.article_id),
                    "rating": rating,
                    "select": "RatingSelect",
                    "error_type": "SupabaseServiceError"
                }
            )
            await interaction.followup.send(
                "❌ 評分時發生錯誤，請稍後再試。", ephemeral=True
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in RatingSelect for user {interaction.user.id}, article {self.item.article_id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "article_id": str(self.item.article_id),
                    "rating": rating,
                    "select": "RatingSelect",
                    "error_type": type(e).__name__
                }
            )
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。", ephemeral=True
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
        super().__init__(timeout=None)
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
            lines.append(f"📂 {item.category}　⭐ {rating_str}")
            lines.append("")
        return "\n".join(lines).strip()

    async def update_message(self, interaction: discord.Interaction):
        self._build_components()
        content = self.build_page_content()
        await interaction.response.edit_message(content=content, view=self)


class ReadingListGroup(app_commands.Group):
    """斜線指令群組：/reading_list"""

    def __init__(self):
        super().__init__(name="reading_list", description="查看並管理待讀清單")

    @app_commands.command(name="view", description="查看並管理待讀清單")
    async def view(self, interaction: discord.Interaction):
        logger.info(f"Command /reading_list view triggered by user {interaction.user.id}")
        await interaction.response.defer(ephemeral=True)
        
        try:
            supabase = SupabaseService()
            discord_id = str(interaction.user.id)
            items = await supabase.get_reading_list(discord_id, status='Unread')
            
            if not items:
                await interaction.followup.send("📭 目前待讀清單是空的！", ephemeral=True)
                logger.info(f"User {interaction.user.id} has empty reading list")
                return

            view = PaginationView(items)
            content = view.build_page_content()
            await interaction.followup.send(content, view=view, ephemeral=True)
            logger.info(f"Successfully sent reading list to user {interaction.user.id} with {len(items)} items")
            
        except SupabaseServiceError as e:
            logger.error(
                f"Database error in /reading_list view for user {interaction.user.id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "command": "reading_list_view",
                    "error_type": "SupabaseServiceError"
                }
            )
            await interaction.followup.send(
                "❌ 無法取得待讀清單，請稍後再試。", ephemeral=True
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in /reading_list view for user {interaction.user.id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "command": "reading_list_view",
                    "error_type": type(e).__name__
                }
            )
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。", ephemeral=True
            )

    @app_commands.command(name="recommend", description="根據高評分文章生成推薦摘要")
    async def recommend(self, interaction: discord.Interaction):
        logger.info(f"Command /reading_list recommend triggered by user {interaction.user.id}")
        await interaction.response.defer(ephemeral=True)
        
        try:
            supabase = SupabaseService()
            discord_id = str(interaction.user.id)
            high_rated = await supabase.get_highly_rated_articles(discord_id, threshold=4)
            
            if not high_rated:
                await interaction.followup.send(
                    "尚無足夠的高評分文章，請先對文章評分（4 星以上）後再試。", ephemeral=True
                )
                logger.info(f"User {interaction.user.id} has no highly rated articles")
                return

            titles = [item.title for item in high_rated]
            categories = [item.category for item in high_rated]
            
            logger.info(f"Generating recommendation for user {interaction.user.id} based on {len(high_rated)} highly rated articles")

            try:
                llm = LLMService()
                summary = await llm.generate_reading_recommendation(titles, categories)
                
                if len(summary) > 2000:
                    summary = summary[:1997] + "..."
                    
                await interaction.followup.send(summary, ephemeral=True)
                logger.info(f"Successfully sent recommendation to user {interaction.user.id}")
                
            except LLMServiceError as e:
                logger.error(
                    f"LLM error in /reading_list recommend for user {interaction.user.id}: {e}",
                    exc_info=True,
                    extra={
                        "user_id": interaction.user.id,
                        "command": "reading_list_recommend",
                        "error_type": "LLMServiceError"
                    }
                )
                await interaction.followup.send(
                    "❌ 推薦功能暫時無法使用，請稍後再試。", ephemeral=True
                )
                
        except SupabaseServiceError as e:
            logger.error(
                f"Database error in /reading_list recommend for user {interaction.user.id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "command": "reading_list_recommend",
                    "error_type": "SupabaseServiceError"
                }
            )
            await interaction.followup.send(
                "❌ 無法取得高評分文章，請稍後再試。", ephemeral=True
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in /reading_list recommend for user {interaction.user.id}: {e}",
                exc_info=True,
                extra={
                    "user_id": interaction.user.id,
                    "command": "reading_list_recommend",
                    "error_type": type(e).__name__
                }
            )
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。", ephemeral=True
            )


class ReadingListCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reading_list_group = ReadingListGroup()
        bot.tree.add_command(self.reading_list_group)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.reading_list_group.name)


async def setup(bot: commands.Bot):
    await bot.add_cog(ReadingListCog(bot))
