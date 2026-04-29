import logging
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class FeedMixin:
    """Mixin extracted from SupabaseService — do not instantiate directly."""

    async def get_active_feeds(self, user_id: "UUID | None" = None) -> list["RSSSource"]:
        """取得所有啟用的 RSS 訂閱源（系統 feed + 該使用者的自訂 feed）

        Args:
            user_id: 使用者 UUID，用於包含該使用者的自訂 feed

        Returns:
            啟用的訂閱源列表，按 category 和 name 排序

        Raises:
            SupabaseServiceError: 當資料庫查詢失敗時
        """

        from app.schemas.article import RSSSource

        logger.info("Fetching active feeds")

        try:
            # 查詢系統 feed（created_by IS NULL）+ 使用者自訂 feed
            # Fallback: if created_by column doesn't exist yet, select without it
            try:
                query = (
                    self.client.table("feeds")
                    .select("id, name, url, category, created_by, last_fetched_at")
                    .eq("is_active", True)
                )
                if user_id:
                    query = query.or_(f"created_by.is.null,created_by.eq.{user_id}")
                else:
                    query = query.is_("created_by", "null")
                response = query.order("category").order("name").execute()
            except Exception:
                # Migration not yet applied — fall back to all feeds without created_by filter
                response = (
                    self.client.table("feeds")
                    .select("id, name, url, category")
                    .eq("is_active", True)
                    .order("category")
                    .order("name")
                    .execute()
                )

            if not response.data:
                logger.info("No active feeds found")
                return []

            feeds = []
            for feed_data in response.data:
                try:
                    rss_source = RSSSource(
                        id=feed_data["id"],
                        name=feed_data["name"],
                        url=feed_data["url"],
                        category=feed_data["category"],
                        created_by=feed_data.get("created_by"),
                        last_fetched_at=feed_data.get("last_fetched_at"),
                    )
                    feeds.append(rss_source)
                except Exception as e:
                    logger.warning(f"Failed to parse feed data: {feed_data}, error: {e}")
                    continue

            logger.info(f"Retrieved {len(feeds)} active feeds")
            return feeds

        except SupabaseServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch active feeds: {e}", exc_info=True)
            self._handle_database_error(e, {"operation": "get_active_feeds"})

    async def update_feeds_last_fetched(self, feed_ids: list[str]) -> None:
        """Update last_fetched_at for a list of feeds to the current time."""
        if not feed_ids:
            return
        try:
            now = datetime.now(UTC).isoformat()
            for feed_id in feed_ids:
                self.client.table("feeds").update({"last_fetched_at": now}).eq(
                    "id", feed_id
                ).execute()
            logger.info(f"Updated last_fetched_at for {len(feed_ids)} feeds")
        except Exception as e:
            logger.warning(f"Failed to update last_fetched_at: {e}")

    async def find_feed_by_url(self, url: str) -> Optional["UUID"]:
        """根據 URL 查找 feed

        Args:
            url: Feed URL

        Returns:
            Feed UUID if found, None otherwise

        Raises:
            SupabaseServiceError: 當資料庫操作失敗時
        """
        from uuid import UUID

        logger.info(
            "Database operation: find_feed_by_url",
            extra={"operation_type": "SELECT", "table": "feeds", "url": url},
        )

        try:
            response = self.client.table("feeds").select("id").eq("url", url).execute()

            if response.data and len(response.data) > 0:
                feed_id = UUID(response.data[0]["id"])
                logger.info(
                    "Database operation completed: find_feed_by_url (found)",
                    extra={"operation_type": "SELECT", "table": "feeds", "feed_id": str(feed_id)},
                )
                return feed_id

            logger.info(
                "Database operation completed: find_feed_by_url (not found)",
                extra={"operation_type": "SELECT", "table": "feeds", "url": url},
            )
            return None

        except Exception as e:
            logger.error(f"Failed to find feed by URL: {e}", exc_info=True)
            self._handle_database_error(e, {"url": url, "operation": "find_feed_by_url"})

    async def create_feed(
        self, name: str, url: str, category: str, created_by: "UUID | None" = None
    ) -> "UUID":
        """建立新的 feed

        Args:
            name: Feed 名稱
            url: Feed URL
            category: Feed 分類

        Returns:
            新建立的 feed UUID

        Raises:
            SupabaseServiceError: 當資料庫操作失敗時
        """
        from uuid import UUID

        logger.info(
            "Database operation: create_feed",
            extra={
                "operation_type": "INSERT",
                "table": "feeds",
                "name": name,
                "url": url,
                "category": category,
            },
        )

        try:
            insert_data: dict = {"name": name, "url": url, "category": category, "is_active": True}
            if created_by is not None:
                insert_data["created_by"] = str(created_by)
            try:
                insert_response = self.client.table("feeds").insert(insert_data).execute()
            except Exception as e:
                if "created_by" in str(e):
                    # Migration not yet applied — insert without created_by
                    insert_data.pop("created_by", None)
                    insert_response = self.client.table("feeds").insert(insert_data).execute()
                else:
                    raise

            if not insert_response.data or len(insert_response.data) == 0:
                raise SupabaseServiceError(
                    "Failed to create feed: No data returned",
                    context={"name": name, "url": url, "category": category},
                )

            feed_id = UUID(insert_response.data[0]["id"])
            logger.info(
                "Database operation completed: create_feed",
                extra={
                    "operation_type": "INSERT",
                    "table": "feeds",
                    "feed_id": str(feed_id),
                    "affected_records": 1,
                },
            )
            return feed_id

        except SupabaseServiceError:
            # Re-raise already wrapped errors
            raise
        except Exception as e:
            logger.error(f"Failed to create feed: {e}", exc_info=True)
            self._handle_database_error(
                e, {"name": name, "url": url, "category": category, "operation": "create_feed"}
            )

    async def delete_feed(self, feed_id: "UUID") -> None:
        """刪除 feed（同時刪除所有相關訂閱）

        Args:
            feed_id: Feed UUID

        Raises:
            SupabaseServiceError: 當資料庫操作失敗時
        """
        logger.info(
            "Database operation: delete_feed",
            extra={"operation_type": "DELETE", "table": "feeds", "feed_id": str(feed_id)},
        )
        try:
            self.client.table("feeds").delete().eq("id", str(feed_id)).execute()
            logger.info(
                "Database operation completed: delete_feed",
                extra={"operation_type": "DELETE", "table": "feeds", "feed_id": str(feed_id)},
            )
        except Exception as e:
            logger.error(f"Failed to delete feed: {e}", exc_info=True)
            self._handle_database_error(e, {"feed_id": str(feed_id), "operation": "delete_feed"})

    async def subscribe_to_feed(self, discord_id: str, feed_id: "UUID") -> None:
        """訂閱 RSS 來源

        Args:
            discord_id: Discord 使用者 ID
            feed_id: 訂閱源 UUID

        Raises:
            SupabaseServiceError: 當資料庫操作失敗時

        Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.9, 13.1, 13.2, 17.3
        """
        from uuid import UUID

        logger.info(
            "Database operation: subscribe_to_feed",
            extra={
                "operation_type": "INSERT",
                "table": "user_subscriptions",
                "discord_id": discord_id,
                "feed_id": str(feed_id),
            },
        )

        try:
            # 驗證 feed_id 格式
            if isinstance(feed_id, str):
                feed_id = self._validate_uuid(feed_id)
            elif not isinstance(feed_id, UUID):
                raise ValueError(
                    f"feed_id must be a UUID or valid UUID string, got {type(feed_id)}"
                )

            # 取得或建立使用者
            user_uuid = await self.get_or_create_user(discord_id)

            # 檢查是否已訂閱
            existing = (
                self.client.table("user_subscriptions")
                .select("id")
                .eq("user_id", str(user_uuid))
                .eq("feed_id", str(feed_id))
                .execute()
            )

            if existing.data and len(existing.data) > 0:
                logger.info(
                    "Database operation completed: subscribe_to_feed (already subscribed)",
                    extra={
                        "operation_type": "SELECT",
                        "table": "user_subscriptions",
                        "affected_records": 0,
                        "feed_id": str(feed_id),
                    },
                )
                return

            # 插入訂閱記錄
            self.client.table("user_subscriptions").insert(
                {"user_id": str(user_uuid), "feed_id": str(feed_id)}
            ).execute()

            logger.info(
                "Database operation completed: subscribe_to_feed",
                extra={
                    "operation_type": "INSERT",
                    "table": "user_subscriptions",
                    "affected_records": 1,
                    "feed_id": str(feed_id),
                },
            )

        except (ValueError, SupabaseServiceError):
            # 重新拋出驗證錯誤和已包裝的錯誤
            raise
        except Exception as e:
            error_str = str(e).lower()

            # 處理重複訂閱（並發情況）
            if "duplicate key" in error_str or "unique" in error_str or "23505" in error_str:
                logger.info(
                    "Database operation completed: subscribe_to_feed (concurrent duplicate)",
                    extra={
                        "operation_type": "INSERT",
                        "table": "user_subscriptions",
                        "affected_records": 0,
                        "feed_id": str(feed_id),
                        "note": "concurrent_duplicate",
                    },
                )
                return

            logger.error(
                f"Failed to subscribe to feed: {e}",
                exc_info=True,
                extra={
                    "operation_type": "INSERT",
                    "table": "user_subscriptions",
                    "discord_id": discord_id,
                    "feed_id": str(feed_id),
                    "error_type": type(e).__name__,
                },
            )
            self._handle_database_error(
                e,
                {
                    "discord_id": discord_id,
                    "feed_id": str(feed_id),
                    "operation": "subscribe_to_feed",
                },
            )

    async def unsubscribe_from_feed(self, discord_id: str, feed_id: "UUID") -> None:
        """取消訂閱 RSS 來源

        Args:
            discord_id: Discord 使用者 ID
            feed_id: 訂閱源 UUID

        Raises:
            SupabaseServiceError: 當資料庫操作失敗時

        Validates: Requirements 11.5, 11.6, 11.7, 11.8, 11.9, 13.1, 13.2, 17.3
        """
        from uuid import UUID

        logger.info(
            "Database operation: unsubscribe_from_feed",
            extra={
                "operation_type": "DELETE",
                "table": "user_subscriptions",
                "discord_id": discord_id,
                "feed_id": str(feed_id),
            },
        )

        try:
            # 驗證 feed_id 格式
            if isinstance(feed_id, str):
                feed_id = self._validate_uuid(feed_id)
            elif not isinstance(feed_id, UUID):
                raise ValueError(
                    f"feed_id must be a UUID or valid UUID string, got {type(feed_id)}"
                )

            # 取得使用者 UUID
            user_uuid = await self.get_or_create_user(discord_id)

            # 刪除訂閱記錄
            response = (
                self.client.table("user_subscriptions")
                .delete()
                .eq("user_id", str(user_uuid))
                .eq("feed_id", str(feed_id))
                .execute()
            )

            affected_records = len(response.data) if response.data else 0
            logger.info(
                "Database operation completed: unsubscribe_from_feed",
                extra={
                    "operation_type": "DELETE",
                    "table": "user_subscriptions",
                    "affected_records": affected_records,
                    "feed_id": str(feed_id),
                },
            )

        except (ValueError, SupabaseServiceError):
            # 重新拋出驗證錯誤和已包裝的錯誤
            raise
        except Exception as e:
            logger.error(
                f"Failed to unsubscribe from feed: {e}",
                exc_info=True,
                extra={
                    "operation_type": "DELETE",
                    "table": "user_subscriptions",
                    "discord_id": discord_id,
                    "feed_id": str(feed_id),
                    "error_type": type(e).__name__,
                },
            )
            self._handle_database_error(
                e,
                {
                    "discord_id": discord_id,
                    "feed_id": str(feed_id),
                    "operation": "unsubscribe_from_feed",
                },
            )

    async def get_user_subscriptions(self, discord_id: str) -> list["Subscription"]:
        """查詢使用者的所有訂閱

        Args:
            discord_id: Discord 使用者 ID

        Returns:
            訂閱列表，按 subscribed_at 降序排列

        Raises:
            SupabaseServiceError: 當資料庫查詢失敗時

        Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 13.1, 13.2, 17.3
        """

        from app.schemas.article import Subscription

        logger.info(
            "Database operation: get_user_subscriptions",
            extra={
                "operation_type": "SELECT",
                "table": "user_subscriptions",
                "discord_id": discord_id,
            },
        )

        try:
            # 取得使用者 UUID
            user_uuid = await self.get_or_create_user(discord_id)

            # 查詢訂閱
            response = (
                self.client.table("user_subscriptions")
                .select(
                    "feed_id, subscribed_at, notification_enabled, feeds(id, name, url, category)"
                )
                .eq("user_id", str(user_uuid))
                .order("subscribed_at", desc=True)
                .execute()
            )

            if not response.data:
                logger.info(
                    "Database operation completed: get_user_subscriptions (no subscriptions found)",
                    extra={
                        "operation_type": "SELECT",
                        "table": "user_subscriptions",
                        "affected_records": 0,
                    },
                )
                return []

            # 轉換為 Subscription 物件
            subscriptions = []
            for sub_data in response.data:
                try:
                    # 從 JOIN 結果中提取訂閱源資訊
                    feed_data = sub_data.get("feeds")
                    if not feed_data:
                        logger.warning(f"Feed data missing for subscription: {sub_data}")
                        continue

                    subscription = Subscription(
                        feed_id=sub_data["feed_id"],
                        name=feed_data["name"],
                        url=feed_data["url"],
                        category=feed_data["category"],
                        subscribed_at=datetime.fromisoformat(
                            sub_data["subscribed_at"].replace("Z", "+00:00")
                        ),
                        notification_enabled=sub_data.get("notification_enabled", True),
                    )
                    subscriptions.append(subscription)
                except Exception as e:
                    logger.warning(f"Failed to parse subscription: {sub_data}, error: {e}")
                    continue

            logger.info(
                "Database operation completed: get_user_subscriptions",
                extra={
                    "operation_type": "SELECT",
                    "table": "user_subscriptions",
                    "affected_records": len(subscriptions),
                },
            )
            return subscriptions

        except SupabaseServiceError:
            # 重新拋出已包裝的錯誤
            raise
        except Exception as e:
            logger.error(
                f"Failed to fetch user subscriptions: {e}",
                exc_info=True,
                extra={
                    "operation_type": "SELECT",
                    "table": "user_subscriptions",
                    "discord_id": discord_id,
                    "error_type": type(e).__name__,
                },
            )
            self._handle_database_error(
                e, {"discord_id": discord_id, "operation": "get_user_subscriptions"}
            )
