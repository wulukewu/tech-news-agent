from collections import defaultdict

import discord
from discord import app_commands
from discord.ext import commands

from app.bot.utils.decorators import ensure_user_registered
from app.core.config import settings as settings  # noqa: F401
from app.core.exceptions import SupabaseServiceError
from app.core.logger import get_logger
from app.services.llm_service import LLMService
from app.services.notion_service import NotionService as NotionService  # noqa: F401
from app.services.rss_service import RSSService as RSSService  # noqa: F401
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)

_NEWS_PAGE_SIZE = 5  # articles per page in /news_now


def _build_news_page(articles, page: int) -> str:
    """Build message content for a single page of news articles."""
    total_pages = (len(articles) + _NEWS_PAGE_SIZE - 1) // _NEWS_PAGE_SIZE
    start = page * _NEWS_PAGE_SIZE
    page_articles = articles[start : start + _NEWS_PAGE_SIZE]

    lines = [
        f"📰 **你的個人化技術新聞**（第 {page + 1}/{total_pages} 頁，共 {len(articles)} 篇）\n",
        "🔥 **推薦文章：**\n",
    ]

    by_category = defaultdict(list)
    for article in page_articles:
        by_category[article.category].append(article)

    for category, cat_articles in sorted(by_category.items()):
        lines.append(f"**{category}**")
        for article in cat_articles:
            tinkering = "🔥" * article.tinkering_index
            lines.append(f"  {tinkering} {article.title}")
            lines.append(f"    🔗 {article.url}")

            ai_sum = getattr(article, "ai_summary", None)
            if ai_sum:
                ai_sum = ai_sum.strip()
                # Defensive length check per summary to avoid exceeding 2000 discord limit
                if len(ai_sum) > 160:
                    ai_sum = ai_sum[:157] + "..."
                lines.append(f"    📝 *{ai_sum}*")

            takeaway = getattr(article, "actionable_takeaway", None)
            if takeaway:
                takeaway = takeaway.strip()
                # Defensive length check per takeaway
                if len(takeaway) > 80:
                    takeaway = takeaway[:77] + "..."
                lines.append(f"    💡 *核心精華：{takeaway}*")
        lines.append("")

    content = "\n".join(lines)
    # Absolute safety threshold block to ensure discord API acceptance (max 2000 chars)
    if len(content) > 1990:
        content = content[:1950] + "\n... *(由於 Discord 訊息長度限制，其餘內容已省略)*"
    return content


class NewsPaginationView(discord.ui.View):
    """Pagination view for /news_now with filter and deep-dive buttons."""

    def __init__(
        self,
        articles,
        page: int,
        llm_service: LLMService,
        supabase_service: SupabaseService,
        category: str = "__all__",
    ):
        super().__init__(timeout=None)
        self.articles = articles
        self.page = page
        self.category = category
        self.llm_service = llm_service
        self.supabase_service = supabase_service
        self._build_components()

    def _build_components(self):
        self.clear_items()

        # Filter articles by category
        if self.category == "__all__":
            filtered = self.articles
        else:
            filtered = [a for a in self.articles if a.category == self.category]

        total_pages = (len(filtered) + _NEWS_PAGE_SIZE - 1) // _NEWS_PAGE_SIZE
        start = self.page * _NEWS_PAGE_SIZE
        page_articles = filtered[start : start + _NEWS_PAGE_SIZE]

        # Row 0: filter select
        from app.bot.cogs.interactions import FilterSelect

        filter_select = FilterSelect(self.articles, supabase_service=self.supabase_service)
        filter_select.custom_id = "news_filter"
        filter_select.row = 0
        self.add_item(filter_select)

        # Row 1: prev/next buttons
        prev_page = self.page - 1
        next_page = self.page + 1

        prev_btn = discord.ui.Button(
            label="◀ 上一頁",
            style=discord.ButtonStyle.secondary,
            disabled=self.page == 0,
            custom_id=f"news_prev:{prev_page}:{self.category}",
            row=1,
        )
        next_btn = discord.ui.Button(
            label="下一頁 ▶",
            style=discord.ButtonStyle.secondary,
            disabled=self.page >= total_pages - 1,
            custom_id=f"news_next:{next_page}:{self.category}",
            row=1,
        )
        prev_btn.callback = self._prev_callback
        next_btn.callback = self._next_callback
        self.add_item(prev_btn)
        self.add_item(next_btn)

        # Rows 2-4: Clean dropdown menus for page articles
        if page_articles:
            from app.bot.cogs.interactions import DeepDiveSelect, MarkReadSelect, ReadLaterSelect

            # Row 2: Read Later dropdown
            read_later_select = ReadLaterSelect(page_articles, self.supabase_service)
            read_later_select.row = 2
            self.add_item(read_later_select)

            # Row 3: Mark as Read dropdown
            mark_read_select = MarkReadSelect(page_articles, self.supabase_service)
            mark_read_select.row = 3
            self.add_item(mark_read_select)

            # Row 4: Deep Dive dropdown
            deep_dive_select = DeepDiveSelect(
                page_articles, self.llm_service, self.supabase_service
            )
            deep_dive_select.row = 4
            self.add_item(deep_dive_select)

    async def _prev_callback(self, interaction: discord.Interaction):
        self.page -= 1
        self._build_components()
        filtered = [
            a for a in self.articles if self.category == "__all__" or a.category == self.category
        ]
        await interaction.response.edit_message(
            content=_build_news_page(filtered, self.page), view=self
        )

    async def _next_callback(self, interaction: discord.Interaction):
        self.page += 1
        self._build_components()
        filtered = [
            a for a in self.articles if self.category == "__all__" or a.category == self.category
        ]
        await interaction.response.edit_message(
            content=_build_news_page(filtered, self.page), view=self
        )


class NewsCommands(commands.Cog):
    """News commands cog with service layer dependency injection."""

    def __init__(
        self,
        bot: commands.Bot,
        supabase_service: SupabaseService = None,
        llm_service: LLMService = None,
    ):
        """
        Initialize NewsCommands cog with service dependencies.

        Args:
            bot: Discord bot instance
            supabase_service: Optional SupabaseService instance for dependency injection
            llm_service: Optional LLMService instance for dependency injection
        """
        self.bot = bot
        self.supabase_service = supabase_service or SupabaseService()
        self.llm_service = llm_service or LLMService()

    @app_commands.command(name="update_profile", description="立刻根據你的 DM 對話更新偏好摘要")
    async def update_profile(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        discord_id = str(interaction.user.id)
        try:
            user = await self.supabase_service.get_user_by_discord_id(discord_id)
            if not user:
                await interaction.followup.send("❌ 找不到你的帳號。", ephemeral=True)
                return
            user_id = user["id"]
        except Exception:
            await interaction.followup.send("❌ 無法取得用戶資料。", ephemeral=True)
            return

        from app.services.preference_summary_service import update_preference_summary

        summary = await update_preference_summary(user_id, self.supabase_service)
        if summary:
            await interaction.followup.send(f"✅ 偏好摘要已更新！\n\n> {summary[:500]}", ephemeral=True)
        else:
            await interaction.followup.send("⚠️ 沒有足夠的 DM 對話來生成摘要。先在 DM 裡多說幾句你的偏好吧！", ephemeral=True)

    @app_commands.command(name="my_profile", description="查看你的偏好摘要與分類權重")
    async def my_profile(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        discord_id = str(interaction.user.id)
        try:
            user = await self.supabase_service.get_user_by_discord_id(discord_id)
            if not user:
                await interaction.followup.send("❌ 找不到你的帳號，請先使用其他指令註冊。", ephemeral=True)
                return
            user_id = user["id"]

            resp = (
                self.supabase_service.client.table("preference_model")
                .select("preference_summary, category_weights, summary_updated_at")
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            data = resp.data or {}
        except Exception as exc:
            logger.error("my_profile: failed to fetch preference model: %s", exc)
            await interaction.followup.send("❌ 無法取得偏好資料，請稍後再試。", ephemeral=True)
            return

        import json

        summary = data.get("preference_summary")
        weights_raw = data.get("category_weights") or {}
        if isinstance(weights_raw, str):
            weights_raw = json.loads(weights_raw)

        embed = discord.Embed(title="📊 我的偏好檔案", color=discord.Color.blurple())

        if summary:
            embed.add_field(name="💬 偏好摘要", value=summary[:1000], inline=False)
            updated = data.get("summary_updated_at", "")
            if updated:
                embed.set_footer(text=f"摘要更新於 {updated[:10]}")
        else:
            embed.add_field(
                name="💬 偏好摘要",
                value="還沒有足夠資料。在 DM 裡直接告訴我你喜歡什麼技術主題，我會記住！",
                inline=False,
            )

        if weights_raw:
            top5 = sorted(weights_raw.items(), key=lambda x: x[1], reverse=True)[:5]
            bars = "\n".join(
                f"`{cat:<20}` {'█' * int(w * 10)}{' ' * (10 - int(w * 10))} {w:.2f}"
                for cat, w in top5
            )
            embed.add_field(name="⚖️ 分類權重 (Top 5)", value=bars, inline=False)
        else:
            embed.add_field(
                name="⚖️ 分類權重",
                value="尚無資料，對文章評分或點擊 👍/👎 後會開始累積。",
                inline=False,
            )

        embed.add_field(
            name="💡 如何改善推薦？",
            value="直接在這個 DM 裡說出你的偏好，例如：\n「我喜歡 Rust 和系統設計，不喜歡入門教學」",
            inline=False,
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="recommend_now", description="立即觸發個人化文章推薦（發送 DM）")
    async def recommend_now(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        discord_id = str(interaction.user.id)
        try:
            user_uuid = await ensure_user_registered(interaction)
        except Exception:
            await interaction.followup.send("❌ 無法取得用戶資料，請稍後再試。", ephemeral=True)
            return

        # Fetch recent articles from user's subscribed feeds
        try:
            article_objects = await self.supabase_service.get_user_articles(
                discord_id=discord_id, days=7, limit=50
            )
            # Convert ArticleSchema objects to dicts for scoring
            articles = [
                {
                    "id": str(a.id) if hasattr(a, "id") and a.id else None,
                    "title": a.title,
                    "url": str(a.url),
                    "category": getattr(a, "category", "") or "",
                    "tinkering_index": a.tinkering_index,
                    "ai_summary": a.ai_summary,
                }
                for a in (article_objects or [])
            ]
        except Exception as exc:
            logger.error("recommend_now: failed to fetch articles: %s", exc)
            await interaction.followup.send("❌ 無法取得文章，請稍後再試。", ephemeral=True)
            return

        if not articles:
            await interaction.followup.send("目前沒有文章可以推薦。", ephemeral=True)
            return

        from app.bot.cogs.proactive_dm import send_proactive_dm
        from app.tasks.proactive_recommendation import _build_recommendations

        try:
            items = await _build_recommendations(
                self.supabase_service, None, str(user_uuid), discord_id, articles
            )
        except Exception as exc:
            logger.error("recommend_now: build recommendations failed: %s", exc)
            await interaction.followup.send("❌ 推薦生成失敗，請稍後再試。", ephemeral=True)
            return

        if not items:
            await interaction.followup.send("目前沒有足夠資料生成個人化推薦。", ephemeral=True)
            return

        success = await send_proactive_dm(self.bot, discord_id, items)
        if success:
            await interaction.followup.send("✅ 已發送個人化推薦到你的 DM！", ephemeral=True)
        else:
            await interaction.followup.send("❌ 無法發送 DM，請確認你的 DM 設定是否開啟。", ephemeral=True)

    @app_commands.command(name="news_now", description="查看你訂閱的最新技術文章")
    async def news_now(self, interaction: discord.Interaction):
        logger.info(
            "Command /news_now triggered", user_id=str(interaction.user.id), command="news_now"
        )
        await interaction.response.defer(thinking=True)

        try:
            # 1. Register user using decorator
            try:
                user_uuid = await ensure_user_registered(interaction)
                logger.info(
                    "User registered successfully",
                    user_id=str(interaction.user.id),
                    user_uuid=str(user_uuid),
                )
            except SupabaseServiceError as e:
                logger.error(
                    "User registration failed",
                    user_id=str(interaction.user.id),
                    error=str(e),
                    exc_info=True,
                )
                await interaction.followup.send(
                    "❌ 無法註冊使用者，請稍後再試。\n" "💡 建議：請確認你的網路連線正常，或稍後再試。",
                    ephemeral=True,
                )
                return

            # 2. Get user's subscriptions via service layer
            subscriptions = await self.supabase_service.get_user_subscriptions(
                str(interaction.user.id)
            )

            if not subscriptions:
                logger.info("User has no subscriptions", user_id=str(interaction.user.id))
                await interaction.followup.send("📭 你還沒有訂閱任何 RSS 來源！\n使用 `/add_feed` 來訂閱感興趣的來源。")
                return

            # 3. Query articles from subscribed feeds via service layer
            articles = await self.supabase_service.get_user_articles(
                discord_id=str(interaction.user.id), days=7, limit=50
            )

            if not articles:
                logger.info(
                    "No recent articles found",
                    user_id=str(interaction.user.id),
                    subscription_count=len(subscriptions),
                )
                await interaction.followup.send("📭 最近 7 天沒有新文章。\n背景排程器會定期抓取文章，請稍後再試。")
                return

            # 4. Enrich articles with feed names from subscriptions
            for article in articles:
                feed_name = next(
                    (sub.name for sub in subscriptions if str(sub.feed_id) == str(article.feed_id)),
                    "Unknown",
                )
                article.feed_name = feed_name

            logger.info(
                "Retrieved articles for user",
                user_id=str(interaction.user.id),
                article_count=len(articles),
                subscription_count=len(subscriptions),
            )

            # 5. Build paginated view
            view = NewsPaginationView(
                articles=articles,
                page=0,
                llm_service=self.llm_service,
                supabase_service=self.supabase_service,
            )
            content = _build_news_page(articles, 0)

            await interaction.followup.send(content=content, view=view)
            logger.info(
                "Successfully sent news_now response",
                user_id=str(interaction.user.id),
                article_count=len(articles),
            )

        except SupabaseServiceError as e:
            # Database-specific errors
            logger.error(
                "Database error in /news_now command",
                user_id=str(interaction.user.id),
                command="news_now",
                error=str(e),
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 無法取得文章資料，請稍後再試。\n" "💡 建議：資料庫連線可能暫時中斷，請稍後再試或聯繫管理員。",
                ephemeral=True,
            )
        except Exception as e:
            # Catch-all for unexpected errors
            logger.critical(
                "Unexpected error in /news_now command",
                user_id=str(interaction.user.id),
                command="news_now",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            await interaction.followup.send(
                "❌ 發生未預期的錯誤，請稍後再試。\n" "💡 建議：如果問題持續發生，請聯繫管理員並提供你的使用者 ID。",
                ephemeral=True,
            )

    @app_commands.command(name="stats", description="查看你的閱讀統計")
    async def stats(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        discord_id = str(interaction.user.id)

        try:
            user_uuid = await self.supabase_service.get_or_create_user(discord_id)
            resp = (
                self.supabase_service.client.table("reading_list")
                .select("status, rating, source, articles(category)")
                .eq("user_id", str(user_uuid))
                .execute()
            )
            rows = resp.data or []
        except Exception as exc:
            logger.error("stats: failed to fetch data: %s", exc)
            await interaction.followup.send("❌ 無法取得統計資料，請稍後再試。", ephemeral=True)
            return

        if not rows:
            await interaction.followup.send("📭 你還沒有任何閱讀記錄。", ephemeral=True)
            return

        total = len(rows)
        read = sum(1 for r in rows if r["status"] == "Read")
        unread = sum(1 for r in rows if r["status"] == "Unread")
        rated = [r["rating"] for r in rows if r.get("rating")]
        avg_rating = sum(rated) / len(rated) if rated else 0

        from collections import Counter

        category_counts = Counter(
            r["articles"]["category"]
            for r in rows
            if r.get("articles") and r["articles"].get("category")
        )
        top_cats = category_counts.most_common(5)

        embed = discord.Embed(title="📊 我的閱讀統計", color=discord.Color.blurple())
        embed.add_field(name="📚 總收藏", value=str(total), inline=True)
        embed.add_field(name="✅ 已讀", value=str(read), inline=True)
        embed.add_field(name="📖 未讀", value=str(unread), inline=True)
        embed.add_field(
            name="⭐ 平均評分",
            value=f"{avg_rating:.1f} / 5.0（共 {len(rated)} 篇已評分）",
            inline=False,
        )
        if top_cats:
            bars = "\n".join(f"`{cat:<20}` {count} 篇" for cat, count in top_cats)
            embed.add_field(name="🏷️ 最常收藏分類 (Top 5)", value=bars, inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="export", description="匯出你的待讀清單（CSV 格式）")
    async def export(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        discord_id = str(interaction.user.id)

        try:
            items = await self.supabase_service.get_reading_list(discord_id)
        except Exception as exc:
            logger.error("export: failed to fetch reading list: %s", exc)
            await interaction.followup.send("❌ 無法取得閱讀清單，請稍後再試。", ephemeral=True)
            return

        if not items:
            await interaction.followup.send("📭 你的閱讀清單是空的。", ephemeral=True)
            return

        import csv
        import io

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["title", "url", "category", "status", "rating", "added_at"])
        for item in items:
            writer.writerow(
                [
                    item.title,
                    str(item.url),
                    item.category,
                    item.status,
                    item.rating or "",
                    item.added_at.strftime("%Y-%m-%d %H:%M"),
                ]
            )

        buf.seek(0)
        file = discord.File(
            fp=io.BytesIO(buf.getvalue().encode("utf-8-sig")), filename="reading_list.csv"
        )
        await interaction.followup.send(f"📥 匯出完成，共 {len(items)} 篇文章。", file=file, ephemeral=True)


async def handle_stateless_news_pagination(interaction: discord.Interaction, custom_id: str):
    """
    Stateless handler for news pagination and filter components.
    Reconstructs the view state dynamically from the custom_id or selected option values,
    and queries Supabase to rebuild the message and view without relying on in-memory state.
    """
    # Defer interaction to give us time to fetch from database
    await interaction.response.defer()

    # Initialize services
    supabase_service = SupabaseService()
    llm_service = LLMService()

    # Parse target_page and category from custom_id
    if custom_id.startswith("news_prev:"):
        parts = custom_id.split(":")
        target_page = int(parts[1])
        category = parts[2]
    elif custom_id.startswith("news_next:"):
        parts = custom_id.split(":")
        target_page = int(parts[1])
        category = parts[2]
    elif custom_id == "news_filter":
        target_page = 0
        values = interaction.data.get("values", [])
        category = values[0] if values else "__all__"
    else:
        logger.error(f"Unknown stateless news interaction custom_id: {custom_id}")
        return

    # Fetch fresh articles and subscriptions for the user
    discord_id = str(interaction.user.id)
    try:
        subscriptions = await supabase_service.get_user_subscriptions(discord_id)
        articles = await supabase_service.get_user_articles(discord_id=discord_id, days=7, limit=50)
    except Exception as e:
        logger.error(f"Stateless news database query failed: {e}")
        await interaction.followup.send("❌ 無法取得文章資料，請稍後再試。", ephemeral=True)
        return

    if not articles:
        await interaction.followup.send("📭 最近已無可用文章。", ephemeral=True)
        return

    # Enrich feed names
    for article in articles:
        feed_name = next(
            (sub.name for sub in subscriptions if str(sub.feed_id) == str(article.feed_id)),
            "Unknown",
        )
        article.feed_name = feed_name

    # Build new pagination view and content
    view = NewsPaginationView(
        articles=articles,
        page=target_page,
        llm_service=llm_service,
        supabase_service=supabase_service,
        category=category,
    )

    # Filter articles for build_page content rendering
    if category == "__all__":
        filtered = articles
    else:
        filtered = [a for a in articles if a.category == category]

    content = _build_news_page(filtered, target_page)

    try:
        await interaction.message.edit(content=content, view=view)
        logger.info(
            f"Stateless news pagination handled: user={discord_id}, page={target_page}, category={category}"
        )
    except Exception as e:
        logger.error(f"Failed to edit interaction message in stateless handler: {e}")


async def setup(bot: commands.Bot):
    """Setup function with service layer dependency injection."""
    supabase_service = SupabaseService()
    llm_service = LLMService()
    await bot.add_cog(NewsCommands(bot, supabase_service, llm_service))
