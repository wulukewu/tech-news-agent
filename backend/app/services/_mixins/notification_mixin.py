import logging

logger = logging.getLogger(__name__)


class NotificationMixin:
    """Mixin extracted from SupabaseService — do not instantiate directly."""

    async def update_notification_settings(self, discord_id: str, enabled: bool) -> None:
        """更新使用者的 DM 通知設定

        Args:
            discord_id: Discord 使用者 ID
            enabled: 是否啟用 DM 通知

        Raises:
            SupabaseServiceError: 當資料庫操作失敗時
        """
        logger.info(
            "Database operation: update_notification_settings",
            extra={
                "operation_type": "UPDATE",
                "table": "users",
                "discord_id": discord_id,
                "enabled": enabled,
            },
        )

        try:
            # 取得或建立使用者
            user_uuid = await self.get_or_create_user(discord_id)

            # 更新通知設定
            response = (
                self.client.table("users")
                .update({"dm_notifications_enabled": enabled})
                .eq("id", str(user_uuid))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                raise SupabaseServiceError(
                    f"Failed to update notification settings for user {discord_id}",
                    context={
                        "discord_id": discord_id,
                        "enabled": enabled,
                        "operation": "update_notification_settings",
                    },
                )

            logger.info(
                "Database operation completed: update_notification_settings",
                extra={
                    "operation_type": "UPDATE",
                    "table": "users",
                    "affected_records": 1,
                    "enabled": enabled,
                },
            )

        except SupabaseServiceError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to update notification settings: {e}",
                exc_info=True,
                extra={
                    "operation_type": "UPDATE",
                    "table": "users",
                    "discord_id": discord_id,
                    "enabled": enabled,
                    "error_type": type(e).__name__,
                },
            )
            self._handle_database_error(
                e,
                {
                    "discord_id": discord_id,
                    "enabled": enabled,
                    "operation": "update_notification_settings",
                },
            )

    async def get_notification_settings(self, discord_id: str) -> bool:
        """查詢使用者的 DM 通知設定

        Args:
            discord_id: Discord 使用者 ID

        Returns:
            是否啟用 DM 通知（預設 True）

        Raises:
            SupabaseServiceError: 當資料庫查詢失敗時
        """
        logger.info(
            "Database operation: get_notification_settings",
            extra={"operation_type": "SELECT", "table": "users", "discord_id": discord_id},
        )

        try:
            # 取得或建立使用者
            user_uuid = await self.get_or_create_user(discord_id)

            # 查詢通知設定
            response = (
                self.client.table("users")
                .select("dm_notifications_enabled")
                .eq("id", str(user_uuid))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                # 使用者不存在，返回預設值
                logger.warning(
                    f"User {discord_id} not found, returning default notification setting"
                )
                return True

            enabled = response.data[0].get("dm_notifications_enabled", True)

            logger.info(
                "Database operation completed: get_notification_settings",
                extra={
                    "operation_type": "SELECT",
                    "table": "users",
                    "affected_records": 1,
                    "enabled": enabled,
                },
            )

            return enabled

        except SupabaseServiceError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to get notification settings: {e}",
                exc_info=True,
                extra={
                    "operation_type": "SELECT",
                    "table": "users",
                    "discord_id": discord_id,
                    "error_type": type(e).__name__,
                },
            )
            self._handle_database_error(
                e, {"discord_id": discord_id, "operation": "get_notification_settings"}
            )

    async def get_users_with_dm_enabled(self) -> list[str]:
        """查詢所有啟用 DM 通知的使用者

        Returns:
            Discord ID 列表

        Raises:
            SupabaseServiceError: 當資料庫查詢失敗時
        """
        logger.info("Fetching users with DM notifications enabled")

        try:
            response = (
                self.client.table("users")
                .select("discord_id")
                .eq("dm_notifications_enabled", True)
                .execute()
            )

            if not response.data:
                logger.info("No users with DM notifications enabled")
                return []

            discord_ids = [user["discord_id"] for user in response.data]
            logger.info(f"Retrieved {len(discord_ids)} users with DM notifications enabled")
            return discord_ids

        except SupabaseServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch users with DM enabled: {e}", exc_info=True)
            self._handle_database_error(e, {"operation": "get_users_with_dm_enabled"})

    async def record_sent_articles(
        self, discord_id: str, article_ids: list[str], notification_type: str = "weekly"
    ) -> None:
        """記錄已發送給使用者的文章

        將文章記錄到 dm_sent_articles 表格，用於追蹤哪些文章已經透過 DM 通知發送給使用者。
        使用 UPSERT 邏輯避免重複記錄。

        Args:
            discord_id: Discord 使用者 ID
            article_ids: 已發送的文章 ID 列表
            notification_type: 通知類型 ('daily', 'weekly', 'monthly')

        Raises:
            SupabaseServiceError: 當資料庫操作失敗時

        Validates: Requirements 2.2
        """

        if not article_ids:
            logger.debug(f"No articles to record for user {discord_id}")
            return

        logger.info(
            f"Recording {len(article_ids)} sent articles for user {discord_id}",
            extra={
                "operation_type": "INSERT",
                "table": "dm_sent_articles",
                "discord_id": discord_id,
                "article_count": len(article_ids),
                "notification_type": notification_type,
            },
        )

        try:
            # 取得使用者 UUID
            user_uuid = await self.get_or_create_user(discord_id)

            # 準備記錄資料
            records = [
                {
                    "user_id": str(user_uuid),
                    "article_id": str(article_id),
                    "notification_type": notification_type,
                }
                for article_id in article_ids
            ]

            # 使用 UPSERT 避免重複記錄（如果同一文章被多次發送）
            # Note: This will fail gracefully if dm_sent_articles table doesn't exist
            try:
                self.client.table("dm_sent_articles").upsert(
                    records, on_conflict="user_id,article_id"
                ).execute()

                logger.info(
                    f"Successfully recorded {len(article_ids)} sent articles for user {discord_id}",
                    extra={
                        "operation_type": "INSERT",
                        "table": "dm_sent_articles",
                        "affected_records": len(article_ids),
                    },
                )
            except Exception as table_error:
                # If dm_sent_articles table doesn't exist, log warning but don't crash
                logger.warning(
                    f"Could not record sent articles (table may not exist): {table_error}",
                    extra={
                        "operation_type": "INSERT",
                        "table": "dm_sent_articles",
                        "discord_id": discord_id,
                        "article_count": len(article_ids),
                    },
                )
                # Don't raise error - allow the notification to continue

        except SupabaseServiceError:
            # 重新拋出已經包裝的錯誤
            raise
        except Exception as e:
            logger.error(
                f"Failed to record sent articles for user {discord_id}: {e}",
                exc_info=True,
                extra={
                    "operation_type": "INSERT",
                    "table": "dm_sent_articles",
                    "discord_id": discord_id,
                    "article_count": len(article_ids),
                    "error_type": type(e).__name__,
                },
            )
            # Don't crash the notification system if recording fails
            # This is a non-critical operation
            logger.warning(f"Continuing without recording sent articles for user {discord_id}")
