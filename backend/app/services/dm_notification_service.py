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
            articles = await supabase.get_user_articles(discord_id=discord_id, days=7, limit=20)

            if not articles:
                logger.info(f"No articles found for user {discord_id}, skipping DM")
                return True  # 沒有文章不算失敗

            # 建立 DM 訊息
            embed = self._create_digest_embed(articles)

            # 發送 DM
            try:
                await user.send(embed=embed)

                # 記錄已發送的文章（防止重複發送）
                try:
                    article_ids = [str(article.id) for article in articles if article.id]
                    if article_ids:
                        await supabase.record_sent_articles(discord_id, article_ids)
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
                return False
            except discord.HTTPException as e:
                logger.error(f"HTTP error sending DM to user {discord_id}: {e}")
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
            description=f"為你精選了 {len(articles)} 篇技術文章",
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

        # 每個類別最多顯示 5 篇
        for category, cat_articles in list(categories.items())[:5]:
            articles_text = ""
            for article in cat_articles[:5]:
                # 截斷標題
                title = article.title[:80] + "..." if len(article.title) > 80 else article.title
                tinkering = "⭐" * (article.tinkering_index or 3)
                articles_text += f"{tinkering} [{title}]({article.url})\n"

            embed.add_field(name=f"📂 {category}", value=articles_text or "無文章", inline=False)

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
