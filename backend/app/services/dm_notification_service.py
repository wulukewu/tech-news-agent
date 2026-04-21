"""
DM 通知服務

負責發送 DM 通知給啟用通知的使用者。
"""

import logging
from datetime import UTC, datetime

import discord

from app.core.exceptions import SupabaseServiceError
from app.schemas.article import ArticleSchema
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


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
                                    content=getattr(article, "content", "") or "",
                                    title=article.title or "",
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

            # 建立 DM 訊息
            embed = self._create_digest_embed(articles)

            # 發送 DM
            try:
                await user.send(embed=embed)

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

    def _create_digest_embed(self, articles: list[ArticleSchema]) -> discord.Embed:
        """建立文章摘要 Embed

        Args:
            articles: 文章列表

        Returns:
            Discord Embed 物件
        """
        embed = discord.Embed(
            title="📰 本週技術文章精選",
            description=f"為你精選了 {len(articles)} 篇新技術文章",
            color=discord.Color.blue(),
            timestamp=datetime.now(UTC),
        )

        # 按類別分組
        categories = {}
        for article in articles:
            category = article.category or "其他"
            if category not in categories:
                categories[category] = []
            categories[category].append(article)

        # 每個類別最多顯示 3 篇，避免超過 Discord 1024 字元限制
        for category, cat_articles in list(categories.items())[:5]:
            articles_text = ""
            for article in cat_articles[:3]:  # 限制每個分類最多 3 篇
                # 完整標題（但限制長度避免過長）
                title = article.title[:100] if len(article.title) > 100 else article.title

                # 星星評分
                tinkering = "⭐" * (article.tinkering_index or 3)

                # 文章摘要（前 80 字）
                summary = ""
                if article.ai_summary:
                    summary = (
                        article.ai_summary[:80] + "..."
                        if len(article.ai_summary) > 80
                        else article.ai_summary
                    )

                # 發布時間（相對時間）
                time_ago = ""
                if article.published_at:
                    now = datetime.now(UTC)
                    delta = now - article.published_at
                    if delta.days > 0:
                        time_ago = f"🗓️ {delta.days} 天前"
                    elif delta.seconds >= 3600:
                        hours = delta.seconds // 3600
                        time_ago = f"🗓️ {hours} 小時前"
                    else:
                        minutes = delta.seconds // 60
                        time_ago = f"🗓️ {minutes} 分鐘前"

                # 組合文章資訊（精簡版，確保不超過 1024 字元）
                articles_text += f"{tinkering} **{title}**\n"
                articles_text += f"🔗 {article.url}\n"
                if summary:
                    articles_text += f"📝 {summary}\n"
                if time_ago:
                    articles_text += f"{time_ago}\n"
                articles_text += "\n"

                # 檢查長度，如果接近 1024 就停止添加
                if len(articles_text) > 900:  # 留一些緩衝空間
                    break

            # 添加分類欄位，顯示文章數量
            field_name = f"📂 {category} ({len(cat_articles)} 篇)"
            # 確保 field value 不超過 1024 字元
            if len(articles_text) > 1024:
                articles_text = articles_text[:1020] + "..."
            embed.add_field(name=field_name, value=articles_text or "無文章", inline=False)

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
