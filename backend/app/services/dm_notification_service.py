"""
DM 通知服務

負責發送 DM 通知給啟用通知的使用者。
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

import discord

from app.core.exceptions import SupabaseServiceError
from app.schemas.article import ArticleSchema
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class DigestRatingSelect(discord.ui.Select):
    """Per-article rating select attached to digest DMs."""

    def __init__(self, article_id: UUID, article_title: str, index: int):
        short_title = article_title[:20] + "…" if len(article_title) > 20 else article_title
        options = [
            discord.SelectOption(label=f"{'⭐' * i} {i} 星", value=str(i)) for i in range(1, 6)
        ]
        super().__init__(
            placeholder=f"評分：{short_title}",
            options=options,
            custom_id=f"digest_rate_{article_id}_{index}",
        )
        self.article_id = article_id

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            from app.services.supabase_service import SupabaseService

            supabase = SupabaseService()
            discord_id = str(interaction.user.id)
            rating = int(self.values[0])
            # Ensure article is in reading list before rating
            await supabase.save_to_reading_list(discord_id, self.article_id, source="discord")
            await supabase.update_article_rating(discord_id, self.article_id, rating)
            await interaction.followup.send(f"✅ 已評為 {'⭐' * rating}（{rating} 星）", ephemeral=True)
        except Exception as e:
            logger.error(f"DigestRatingSelect callback error: {e}")
            await interaction.followup.send("❌ 評分失敗，請稍後再試", ephemeral=True)


class DigestActionsView(discord.ui.View):
    """View with dropdown selects for daily/weekly technical article digests."""

    def __init__(
        self,
        articles: list[ArticleSchema],
        supabase_service: SupabaseService = None,
        llm_service=None,
    ):
        super().__init__(timeout=None)

        # Row 0: Read Later select
        from app.bot.cogs.interactions import ReadLaterSelect

        read_later_select = ReadLaterSelect(articles, supabase_service)
        read_later_select.row = 0
        self.add_item(read_later_select)

        # Row 1: Mark Read select
        from app.bot.cogs.interactions import MarkReadSelect

        mark_read_select = MarkReadSelect(articles, supabase_service)
        mark_read_select.row = 1
        self.add_item(mark_read_select)

        # Row 2: Deep Dive select
        from app.bot.cogs.interactions import DeepDiveSelect

        deep_dive_select = DeepDiveSelect(articles, llm_service, supabase_service)
        deep_dive_select.row = 2
        self.add_item(deep_dive_select)


class DMNotificationService:
    """DM 通知服務"""

    def __init__(self, bot: discord.Client):
        """初始化 DM 通知服務

        Args:
            bot: Discord bot 實例
        """
        self.bot = bot

    async def send_weekly_digest_to_all_users(self) -> dict:
        """發送每週文章摘要給所有啟用 DM 通知的使用者

        Returns:
            統計資訊字典：
            - total_users: 總使用者數
            - successful: 成功發送數
            - failed: 失敗數
            - disabled: 未啟用通知數
        """
        logger.info("Starting weekly digest DM notification to all users")

        stats = {"total_users": 0, "successful": 0, "failed": 0, "disabled": 0}

        try:
            # 查詢所有啟用 DM 通知的使用者
            supabase = SupabaseService()
            discord_ids = await supabase.get_users_with_dm_enabled()

            stats["total_users"] = len(discord_ids)

            if not discord_ids:
                logger.info("No users with DM notifications enabled")
                return stats

            logger.info(f"Found {len(discord_ids)} users with DM notifications enabled")

            # 對每個使用者發送個人化的文章摘要
            for discord_id in discord_ids:
                try:
                    success = await self.send_personalized_digest(discord_id)
                    if success:
                        stats["successful"] += 1
                    else:
                        stats["failed"] += 1
                except Exception as e:
                    logger.error(f"Failed to send digest to user {discord_id}: {e}", exc_info=True)
                    stats["failed"] += 1

            logger.info(
                f"Weekly digest DM notification completed: "
                f"{stats['successful']} successful, {stats['failed']} failed"
            )

            return stats

        except SupabaseServiceError as e:
            logger.error(f"Failed to fetch users with DM enabled: {e}", exc_info=True)
            return stats
        except Exception as e:
            logger.error(f"Unexpected error in send_weekly_digest_to_all_users: {e}", exc_info=True)
            return stats

    async def _get_user_category_weights(
        self, supabase: SupabaseService, user_id: str
    ) -> dict[str, float]:
        """Get category weights from user's reading list ratings (4+ stars)."""
        try:
            response = (
                supabase.client.table("reading_list")
                .select("rating, articles(feeds(category))")
                .eq("user_id", user_id)
                .gte("rating", 4)
                .execute()
            )
            weights: dict[str, float] = {}
            for row in response.data or []:
                cat = ((row.get("articles") or {}).get("feeds") or {}).get("category", "")
                if cat:
                    weights[cat] = weights.get(cat, 0) + (row.get("rating") or 0)
            # Normalize to 0-1
            if weights:
                max_w = max(weights.values())
                weights = {k: v / max_w for k, v in weights.items()}
            return weights
        except Exception as e:
            logger.warning(f"Could not load category weights for user {user_id}: {e}")
            return {}

    async def _get_recent_engagement(self, supabase: SupabaseService, user_id: str) -> int:
        """Count user interactions (ratings/saves) in the last 7 days."""
        try:
            from datetime import timedelta

            cutoff = (datetime.now(UTC) - timedelta(days=7)).isoformat()
            response = (
                supabase.client.table("reading_list")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .gte("created_at", cutoff)
                .execute()
            )
            return response.count or 0
        except Exception as e:
            logger.warning(f"Could not get engagement for user {user_id}: {e}")
            return 0

    def _rank_articles(
        self,
        articles: list[ArticleSchema],
        category_weights: dict[str, float],
    ) -> list[tuple[ArticleSchema, str]]:
        """
        Re-rank articles with a blended score and attach a reason string.
        Score = 40% tinkering_index + 40% category_affinity + 20% recency
        Returns list of (article, reason) sorted by score desc.
        """
        now = datetime.now(UTC)
        scored: list[tuple[float, ArticleSchema, str]] = []

        for article in articles:
            # Tinkering score (1-5 → 0-1)
            tinkering = (article.tinkering_index or 3) / 5.0

            # Category affinity (0-1)
            affinity = category_weights.get(article.category or "", 0.0)

            # Recency score (0-1, decays over 7 days)
            recency = 0.5
            if article.published_at:
                age_hours = (now - article.published_at).total_seconds() / 3600
                recency = max(0.0, 1.0 - age_hours / (7 * 24))

            score = 0.4 * tinkering + 0.4 * affinity + 0.2 * recency

            # Build reason string
            if affinity >= 0.7:
                reason = f"💡 符合你偏好的 {article.category} 類別"
            elif tinkering >= 0.8:
                reason = "🔬 高技術深度文章"
            elif recency >= 0.8:
                reason = "🆕 最新發布"
            else:
                reason = f"📂 來自你訂閱的 {article.category} 頻道"

            scored.append((score, article, reason))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [(a, r) for _, a, r in scored]

    async def send_personalized_digest(self, discord_id: str) -> bool:
        """發送個人化的文章摘要給單一使用者

        Args:
            discord_id: Discord 使用者 ID

        Returns:
            是否成功發送
        """
        try:
            # 驗證 discord_id 是否為有效的數字
            if not discord_id.isdigit():
                logger.warning(f"Invalid discord_id format: {discord_id}, skipping")
                return False

            # 取得使用者物件
            user = await self.bot.fetch_user(int(discord_id))
            if not user:
                logger.warning(f"User {discord_id} not found")
                return False

            # 查詢使用者訂閱的文章
            supabase = SupabaseService()

            # 取得使用者的通知頻率設定
            user_data = await supabase.get_user_by_discord_id(discord_id)
            frequency = "weekly"  # 預設值
            if user_data and user_data.get("id"):
                try:
                    from uuid import UUID

                    user_uuid = UUID(user_data["id"])
                    prefs_response = (
                        supabase.client.table("user_notification_preferences")
                        .select("frequency")
                        .eq("user_id", str(user_uuid))
                        .execute()
                    )
                    if prefs_response.data and len(prefs_response.data) > 0:
                        frequency = prefs_response.data[0].get("frequency", "weekly")
                except Exception as freq_error:
                    logger.warning(
                        f"Failed to get notification frequency for user {discord_id}: {freq_error}"
                    )

            # 根據頻率查詢文章
            articles = await supabase.get_user_articles(
                discord_id=discord_id, limit=20, frequency=frequency
            )

            if not articles:
                logger.info(f"No articles found for user {discord_id}, skipping DM")
                return True  # 沒有文章不算失敗

            # Apply technical depth filtering
            try:
                from uuid import UUID

                from app.services.technical_depth_service import TechnicalDepthService

                # Get user UUID from discord_id
                user_data = await supabase.get_user_by_discord_id(discord_id)
                if user_data and user_data.get("id"):
                    user_uuid = UUID(user_data["id"])

                    tech_depth_service = TechnicalDepthService()
                    tech_settings = await tech_depth_service.get_tech_depth_settings(user_uuid)

                    if tech_settings.enabled:
                        # Filter articles based on technical depth
                        filtered_articles = []
                        for article in articles:
                            # Estimate article depth if not already set
                            article_depth = getattr(article, "technical_depth", None)
                            if not article_depth:
                                article_depth = tech_depth_service.estimate_article_depth(
                                    content=getattr(article, "ai_summary", "") or "",
                                    title=article.title or "",
                                    tinkering_index=article.tinkering_index,
                                )

                            # Check if article meets user's threshold
                            should_send, reason = await tech_depth_service.should_send_notification(
                                user_uuid, article_depth
                            )

                            if should_send:
                                filtered_articles.append(article)
                            else:
                                logger.debug(
                                    f"Filtered out article for user {discord_id}: {reason}"
                                )

                        articles = filtered_articles
                        logger.info(
                            f"Technical depth filtering for user {discord_id}: {len(filtered_articles)} articles after filtering"
                        )
                    else:
                        logger.debug(f"Technical depth filtering disabled for user {discord_id}")
                else:
                    logger.warning(
                        f"Could not find user UUID for discord_id {discord_id}, skipping technical depth filtering"
                    )

            except Exception as filter_error:
                logger.error(
                    f"Error applying technical depth filtering for user {discord_id}: {filter_error}"
                )
                # Continue with unfiltered articles if filtering fails

            # Check if we still have articles after filtering
            if not articles:
                logger.info(
                    f"No articles remaining after technical depth filtering for user {discord_id}, skipping DM"
                )
                return True  # No articles after filtering is not a failure

            # P1 + P2 + P3: Smart ranking, dynamic count, and recommendation reasons
            ranked_articles_with_reasons: list[tuple[ArticleSchema, str]] = []
            send_limit = 5  # default
            try:
                if user_data and user_data.get("id"):
                    user_id_str = user_data["id"]
                    # P1: Get category weights from user's rating history
                    category_weights = await self._get_user_category_weights(supabase, user_id_str)
                    # P2: Dynamic count based on recent engagement
                    engagement = await self._get_recent_engagement(supabase, user_id_str)
                    if engagement == 0:
                        send_limit = 2
                    elif engagement >= 5:
                        send_limit = 7
                    else:
                        send_limit = 5
                    logger.info(
                        f"Smart digest for {discord_id}: engagement={engagement}, limit={send_limit}, "
                        f"category_weights={list(category_weights.keys())}"
                    )
                    # P1+P3: Re-rank and attach reasons
                    ranked_articles_with_reasons = self._rank_articles(articles, category_weights)
                else:
                    ranked_articles_with_reasons = [
                        (a, f"📂 來自你訂閱的 {a.category or '技術'} 頻道") for a in articles
                    ]
            except Exception as rank_error:
                logger.warning(f"Smart ranking failed for {discord_id}, falling back: {rank_error}")
                ranked_articles_with_reasons = [(a, "") for a in articles]

            # Apply dynamic limit
            ranked_articles_with_reasons = ranked_articles_with_reasons[:send_limit]
            articles = [a for a, _ in ranked_articles_with_reasons]

            # 建立 DM 訊息
            embed = self._create_digest_embed(ranked_articles_with_reasons, frequency)
            actions_view = DigestActionsView(articles, supabase_service=supabase)

            # 發送 DM
            try:
                await user.send(embed=embed, view=actions_view)

                # Record notification history
                try:
                    from app.services.notification_history_service import (
                        NotificationChannel,
                        NotificationHistoryService,
                        NotificationStatus,
                    )

                    if user_data and user_data.get("id"):
                        history_service = NotificationHistoryService()
                        await history_service.record_notification(
                            user_id=UUID(user_data["id"]),
                            channel=NotificationChannel.DISCORD.value,
                            status=NotificationStatus.SENT.value,
                            content=f"Weekly digest with {len(articles)} articles",
                            feed_source="weekly_digest",
                        )
                        logger.debug(f"Recorded notification history for user {discord_id}")
                except Exception as history_error:
                    logger.error(
                        f"Failed to record notification history for user {discord_id}: {history_error}"
                    )

                # 記錄已發送的文章（防止重複發送）
                try:
                    article_ids = [str(article.id) for article in articles if article.id]
                    if article_ids:
                        await supabase.record_sent_articles(discord_id, article_ids, frequency)
                        logger.info(
                            f"Recorded {len(article_ids)} sent articles for user {discord_id}"
                        )
                except Exception as record_error:
                    # 記錄失敗不應該影響 DM 發送成功的狀態
                    logger.error(
                        f"Failed to record sent articles for user {discord_id}: {record_error}",
                        exc_info=True,
                    )

                logger.info(f"Successfully sent digest DM to user {discord_id}")
                return True
            except discord.Forbidden:
                logger.warning(
                    f"Cannot send DM to user {discord_id}: "
                    f"User has DMs disabled or bot is blocked"
                )

                # Record failed notification
                try:
                    from app.services.notification_history_service import (
                        NotificationChannel,
                        NotificationHistoryService,
                        NotificationStatus,
                    )

                    if user_data and user_data.get("id"):
                        history_service = NotificationHistoryService()
                        await history_service.record_notification(
                            user_id=UUID(user_data["id"]),
                            channel=NotificationChannel.DISCORD.value,
                            status=NotificationStatus.FAILED.value,
                            content=f"Weekly digest with {len(articles)} articles",
                            feed_source="weekly_digest",
                            error_message="User has DMs disabled or bot is blocked",
                        )
                except Exception as history_error:
                    logger.error(
                        f"Failed to record failed notification history for user {discord_id}: {history_error}"
                    )

                return False
            except discord.HTTPException as e:
                logger.error(f"HTTP error sending DM to user {discord_id}: {e}")

                # Record failed notification
                try:
                    from app.services.notification_history_service import (
                        NotificationChannel,
                        NotificationHistoryService,
                        NotificationStatus,
                    )

                    if user_data and user_data.get("id"):
                        history_service = NotificationHistoryService()
                        await history_service.record_notification(
                            user_id=UUID(user_data["id"]),
                            channel=NotificationChannel.DISCORD.value,
                            status=NotificationStatus.FAILED.value,
                            content=f"Weekly digest with {len(articles)} articles",
                            feed_source="weekly_digest",
                            error_message=f"HTTP error: {str(e)}",
                        )
                except Exception as history_error:
                    logger.error(
                        f"Failed to record failed notification history for user {discord_id}: {history_error}"
                    )

                return False

        except Exception as e:
            logger.error(
                f"Failed to send personalized digest to user {discord_id}: {e}", exc_info=True
            )
            return False

    def _create_digest_embed(
        self,
        articles_with_reasons: list[tuple[ArticleSchema, str]],
        frequency: str = "daily",
    ) -> discord.Embed:
        """建立文章摘要 Embed"""
        count = len(articles_with_reasons)
        title_map = {
            "daily": "📰 今日技術文章精選",
            "weekly": "📰 本週技術文章精選",
            "monthly": "📰 本月技術文章精選",
        }
        embed = discord.Embed(
            title=title_map.get(frequency, "📰 技術文章精選"),
            description=f"根據你的閱讀偏好，為你精選了 **{count}** 篇文章",
            color=discord.Color.blue(),
            timestamp=datetime.now(UTC),
        )

        now = datetime.now(UTC)
        for article, reason in articles_with_reasons:
            title = article.title[:90] if len(article.title) > 90 else article.title
            tinkering = "⭐" * (article.tinkering_index or 3)

            lines = [f"{tinkering} **{title}**"]
            lines.append(f"🔗 {article.url}")

            if getattr(article, "actionable_takeaway", None):
                lines.append(f"💡 *{article.actionable_takeaway}*")

            if article.ai_summary:
                summary = (
                    article.ai_summary[:80] + "..."
                    if len(article.ai_summary) > 80
                    else article.ai_summary
                )
                lines.append(f"📝 {summary}")

            if article.published_at:
                delta = now - article.published_at
                if delta.days > 0:
                    lines.append(f"🗓️ {delta.days} 天前")
                elif delta.seconds >= 3600:
                    lines.append(f"🗓️ {delta.seconds // 3600} 小時前")

            if reason:
                lines.append(reason)

            field_value = "\n".join(lines)
            if len(field_value) > 1024:
                field_value = field_value[:1020] + "..."

            embed.add_field(
                name=f"📄 {article.category or '技術'}",
                value=field_value,
                inline=False,
            )

        embed.set_footer(text="💡 使用 /news_now 查看完整列表 | 使用 /notifications 管理通知設定")
        return embed

    async def send_test_dm(self, discord_id: str) -> bool:
        """發送測試 DM（用於測試 DM 功能）

        Args:
            discord_id: Discord 使用者 ID

        Returns:
            是否成功發送
        """
        try:
            # 驗證 discord_id 是否為有效的數字
            if not discord_id.isdigit():
                logger.warning(f"Invalid discord_id format: {discord_id}, skipping")
                return False

            user = await self.bot.fetch_user(int(discord_id))
            if not user:
                logger.warning(f"User {discord_id} not found")
                return False

            embed = discord.Embed(
                title="✅ DM 通知測試",
                description="如果你看到這則訊息，代表 DM 通知功能正常運作！",
                color=discord.Color.green(),
            )
            embed.add_field(
                name="📬 你將會收到",
                value="• 每週新文章推薦\n• 訂閱來源的最新內容\n• 個人化的閱讀建議",
                inline=False,
            )
            embed.set_footer(text="使用 /notifications 來管理通知設定")

            await user.send(embed=embed)
            logger.info(f"Successfully sent test DM to user {discord_id}")
            return True

        except discord.Forbidden:
            logger.warning(f"Cannot send DM to user {discord_id}: DMs disabled or bot blocked")
            return False
        except Exception as e:
            logger.error(f"Failed to send test DM to user {discord_id}: {e}", exc_info=True)
            return False
