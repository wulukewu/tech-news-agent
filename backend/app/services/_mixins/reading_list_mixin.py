import logging
from datetime import datetime
from uuid import UUID

from app.core.exceptions import SupabaseServiceError

logger = logging.getLogger(__name__)


class ReadingListMixin:
    """Mixin extracted from SupabaseService — do not instantiate directly."""

    async def save_to_reading_list(self, discord_id: str, article_id: "UUID") -> None:
        """將文章加入使用者的閱讀清單

        使用 UPSERT 邏輯處理並發操作，確保在多個請求同時嘗試加入相同文章時不會產生錯誤。
        當記錄已存在時，只更新 updated_at 時間戳。

        Args:
            discord_id: Discord 使用者 ID
            article_id: 文章 UUID

        Raises:
            SupabaseServiceError: 當資料庫操作失敗時
            ValueError: 當 article_id 格式無效時

        Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 13.1, 13.2, 13.3, 17.3
        """
        from uuid import UUID

        logger.info(
            "Database operation: save_to_reading_list",
            extra={
                "operation_type": "UPSERT",
                "table": "reading_list",
                "discord_id": discord_id,
                "article_id": str(article_id),
            },
        )

        try:
            # 驗證 article_id 格式
            if isinstance(article_id, str):
                article_id = self._validate_uuid(article_id)
            elif not isinstance(article_id, UUID):
                raise ValueError(
                    f"article_id must be a UUID or valid UUID string, got {type(article_id)}"
                )

            # 取得或建立使用者（Requirement 13.1 - 冪等性使用者註冊）
            user_uuid = await self.get_or_create_user(discord_id)

            # 使用 UPSERT 邏輯處理並發操作（Requirement 13.3）
            # Supabase Python client 的 upsert() 方法會：
            # 1. 如果記錄不存在，插入新記錄
            # 2. 如果記錄已存在（基於 UNIQUE 約束），更新現有記錄
            # 這確保了並發安全性，不需要先查詢再插入
            reading_list_data = {
                "user_id": str(user_uuid),
                "article_id": str(article_id),
                "status": "Unread",
                "updated_at": datetime.utcnow().isoformat(),
            }

            # 使用 upsert 處理並發情況
            # on_conflict 指定當 (user_id, article_id) 衝突時的行為
            # ignoreDuplicates=False 表示衝突時更新記錄
            response = (
                self.client.table("reading_list")
                .upsert(
                    reading_list_data,
                    on_conflict="user_id,article_id",  # 基於 UNIQUE(user_id, article_id) 約束
                    returning="minimal",  # 減少返回資料以提升效能
                )
                .execute()
            )

            logger.info(
                "Database operation completed: save_to_reading_list (UPSERT)",
                extra={
                    "operation_type": "UPSERT",
                    "table": "reading_list",
                    "affected_records": 1,
                    "article_id": str(article_id),
                    "status": "Unread",
                },
            )

        except (ValueError, SupabaseServiceError):
            # 重新拋出驗證錯誤和已包裝的錯誤
            raise
        except Exception as e:
            logger.error(
                f"Failed to save to reading list: {e}",
                exc_info=True,
                extra={
                    "operation_type": "UPSERT",
                    "table": "reading_list",
                    "discord_id": discord_id,
                    "article_id": str(article_id),
                    "error_type": type(e).__name__,
                },
            )
            self._handle_database_error(
                e,
                {
                    "discord_id": discord_id,
                    "article_id": str(article_id),
                    "operation": "save_to_reading_list",
                },
            )

    async def update_article_status(self, discord_id: str, article_id: "UUID", status: str) -> None:
        """更新文章閱讀狀態

        Args:
            discord_id: Discord 使用者 ID
            article_id: 文章 UUID
            status: 新狀態（'Unread', 'Read', 'Archived'）

        Raises:
            SupabaseServiceError: 當資料庫操作失敗時
            ValueError: 當 status 無效時

        Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 13.1, 13.2, 17.3
        """
        from uuid import UUID

        logger.info(
            "Database operation: update_article_status",
            extra={
                "operation_type": "UPDATE",
                "table": "reading_list",
                "discord_id": discord_id,
                "article_id": str(article_id),
                "new_status": status,
            },
        )

        try:
            # 驗證狀態
            normalized_status = self._validate_status(status)

            # 驗證 article_id 格式
            if isinstance(article_id, str):
                article_id = self._validate_uuid(article_id)
            elif not isinstance(article_id, UUID):
                raise ValueError(
                    f"article_id must be a UUID or valid UUID string, got {type(article_id)}"
                )

            # 取得使用者 UUID
            user_uuid = await self.get_or_create_user(discord_id)

            # 更新狀態
            response = (
                self.client.table("reading_list")
                .update({"status": normalized_status, "updated_at": datetime.utcnow().isoformat()})
                .eq("user_id", str(user_uuid))
                .eq("article_id", str(article_id))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                raise SupabaseServiceError(
                    f"Reading list entry not found for user {discord_id} and article {article_id}",
                    context={
                        "discord_id": discord_id,
                        "article_id": str(article_id),
                        "operation": "update_article_status",
                    },
                )

            logger.info(
                "Database operation completed: update_article_status",
                extra={
                    "operation_type": "UPDATE",
                    "table": "reading_list",
                    "affected_records": len(response.data),
                    "new_status": normalized_status,
                },
            )

        except (ValueError, SupabaseServiceError):
            # 重新拋出驗證錯誤和已包裝的錯誤
            raise
        except Exception as e:
            logger.error(
                f"Failed to update article status: {e}",
                exc_info=True,
                extra={
                    "operation_type": "UPDATE",
                    "table": "reading_list",
                    "discord_id": discord_id,
                    "article_id": str(article_id),
                    "status": status,
                    "error_type": type(e).__name__,
                },
            )
            self._handle_database_error(
                e,
                {
                    "discord_id": discord_id,
                    "article_id": str(article_id),
                    "status": status,
                    "operation": "update_article_status",
                },
            )

    async def update_article_rating(self, discord_id: str, article_id: "UUID", rating: int) -> None:
        """更新文章評分

        Args:
            discord_id: Discord 使用者 ID
            article_id: 文章 UUID
            rating: 評分（1-5）

        Raises:
            SupabaseServiceError: 當資料庫操作失敗時
            ValueError: 當 rating 超出範圍時

        Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 13.1, 13.2, 17.3
        """
        from uuid import UUID

        logger.info(
            "Database operation: update_article_rating",
            extra={
                "operation_type": "UPDATE",
                "table": "reading_list",
                "discord_id": discord_id,
                "article_id": str(article_id),
                "rating": rating,
            },
        )

        try:
            # 驗證評分
            self._validate_rating(rating)

            # 驗證 article_id 格式
            if isinstance(article_id, str):
                article_id = self._validate_uuid(article_id)
            elif not isinstance(article_id, UUID):
                raise ValueError(
                    f"article_id must be a UUID or valid UUID string, got {type(article_id)}"
                )

            # 取得使用者 UUID
            user_uuid = await self.get_or_create_user(discord_id)

            # 更新評分
            response = (
                self.client.table("reading_list")
                .update({"rating": rating, "updated_at": datetime.utcnow().isoformat()})
                .eq("user_id", str(user_uuid))
                .eq("article_id", str(article_id))
                .execute()
            )

            if not response.data or len(response.data) == 0:
                raise SupabaseServiceError(
                    f"Reading list entry not found for user {discord_id} and article {article_id}",
                    context={
                        "discord_id": discord_id,
                        "article_id": str(article_id),
                        "operation": "update_article_rating",
                    },
                )

            logger.info(
                "Database operation completed: update_article_rating",
                extra={
                    "operation_type": "UPDATE",
                    "table": "reading_list",
                    "affected_records": len(response.data),
                    "rating": rating,
                },
            )

            # Auto-sync learning progress when rating >= 3
            if rating >= 3:
                try:
                    await self._sync_learning_progress(str(user_uuid), str(article_id))
                except Exception as sync_err:
                    # Non-critical: log but don't fail the rating update
                    logger.warning("Failed to sync learning progress: %s", sync_err)

        except (ValueError, SupabaseServiceError):
            # 重新拋出驗證錯誤和已包裝的錯誤
            raise
        except Exception as e:
            logger.error(
                f"Failed to update article rating: {e}",
                exc_info=True,
                extra={
                    "operation_type": "UPDATE",
                    "table": "reading_list",
                    "discord_id": discord_id,
                    "article_id": str(article_id),
                    "rating": rating,
                    "error_type": type(e).__name__,
                },
            )
            self._handle_database_error(
                e,
                {
                    "discord_id": discord_id,
                    "article_id": str(article_id),
                    "rating": rating,
                    "operation": "update_article_rating",
                },
            )

    async def _sync_learning_progress(self, user_id: str, article_id: str) -> None:
        """Auto-sync learning progress when user rates an article >= 3.

        Checks if the article matches any active learning goal stage and marks it complete.
        """
        # Get article category
        article_resp = (
            self.client.table("articles").select("category").eq("id", article_id).single().execute()
        )
        if not article_resp.data:
            return
        article_category = (article_resp.data.get("category") or "").lower()
        if not article_category:
            return

        # Get user's active learning goals with their stages
        goals_resp = (
            self.client.table("learning_goals")
            .select("id, learning_paths(id, learning_stages(id, stage_name, prerequisites))")
            .eq("user_id", user_id)
            .eq("status", "active")
            .execute()
        )
        if not goals_resp.data:
            return

        # Check if already recorded in learning_progress
        existing_resp = (
            self.client.table("learning_progress")
            .select("id")
            .eq("user_id", user_id)
            .eq("article_id", article_id)
            .eq("status", "completed")
            .execute()
        )
        if existing_resp.data:
            return  # Already marked, skip

        for goal in goals_resp.data:
            goal_id = goal["id"]
            paths = goal.get("learning_paths") or []
            if not paths:
                continue
            path = paths[0]
            stages = path.get("learning_stages") or []

            for stage in stages:
                # Match article category against stage skills (prerequisites field)
                skills = [s.lower() for s in (stage.get("prerequisites") or [])]
                stage_name = (stage.get("stage_name") or "").lower()
                all_keywords = skills + [stage_name]

                if any(
                    kw in article_category or article_category in kw for kw in all_keywords if kw
                ):
                    # Mark as completed
                    self.client.table("learning_progress").upsert(
                        {
                            "user_id": user_id,
                            "goal_id": goal_id,
                            "stage_id": stage["id"],
                            "article_id": article_id,
                            "status": "completed",
                            "completion_percentage": 100,
                            "completed_at": datetime.utcnow().isoformat(),
                        }
                    ).execute()
                    logger.info(
                        "Auto-synced learning progress: article %s → goal %s stage %s",
                        article_id,
                        goal_id,
                        stage["id"],
                    )
                    break  # One match per goal is enough

    async def get_reading_list(
        self, discord_id: str, status: str | None = None
    ) -> list["ReadingListItem"]:
        """查詢使用者的閱讀清單

        Args:
            discord_id: Discord 使用者 ID
            status: 可選的狀態篩選

        Returns:
            閱讀清單項目列表，按 added_at 降序排列

        Raises:
            SupabaseServiceError: 當資料庫查詢失敗時

        Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 13.1, 13.2, 17.3
        """

        from app.schemas.article import ReadingListItem

        logger.info(
            "Database operation: get_reading_list",
            extra={
                "operation_type": "SELECT",
                "table": "reading_list",
                "discord_id": discord_id,
                "status_filter": status,
            },
        )

        try:
            # 驗證狀態（如果提供）
            if status:
                status = self._validate_status(status)

            # 取得使用者 UUID
            user_uuid = await self.get_or_create_user(discord_id)

            # 建立查詢 - join with feeds table to get category
            query = (
                self.client.table("reading_list")
                .select(
                    "article_id, status, rating, added_at, updated_at, articles(id, title, url, feeds(category))"
                )
                .eq("user_id", str(user_uuid))
            )

            # 加入狀態篩選（如果提供）
            if status:
                query = query.eq("status", status)

            # 執行查詢並排序
            response = query.order("added_at", desc=True).execute()

            if not response.data:
                logger.info(
                    "Database operation completed: get_reading_list (no items found)",
                    extra={
                        "operation_type": "SELECT",
                        "table": "reading_list",
                        "affected_records": 0,
                    },
                )
                return []

            # 轉換為 ReadingListItem 物件
            items = []
            for item_data in response.data:
                try:
                    # 從 JOIN 結果中提取文章資訊
                    article_data = item_data.get("articles")
                    if not article_data:
                        logger.warning(f"Article data missing for reading list item: {item_data}")
                        continue

                    # 從 nested JOIN 結果中提取 feed 資訊
                    feed_data = article_data.get("feeds")
                    if not feed_data:
                        logger.warning(f"Feed data missing for article: {article_data}")
                        continue

                    reading_list_item = ReadingListItem(
                        article_id=item_data["article_id"],
                        title=article_data["title"],
                        url=article_data["url"],
                        category=feed_data["category"],
                        status=item_data["status"],
                        rating=item_data.get("rating"),
                        added_at=datetime.fromisoformat(
                            item_data["added_at"].replace("Z", "+00:00")
                        ),
                        updated_at=datetime.fromisoformat(
                            item_data["updated_at"].replace("Z", "+00:00")
                        ),
                    )
                    items.append(reading_list_item)
                except Exception as e:
                    logger.warning(f"Failed to parse reading list item: {item_data}, error: {e}")
                    continue

            logger.info(
                "Database operation completed: get_reading_list",
                extra={
                    "operation_type": "SELECT",
                    "table": "reading_list",
                    "affected_records": len(items),
                },
            )
            return items

        except (ValueError, SupabaseServiceError):
            # 重新拋出驗證錯誤和已包裝的錯誤
            raise
        except Exception as e:
            logger.error(
                f"Failed to fetch reading list: {e}",
                exc_info=True,
                extra={
                    "operation_type": "SELECT",
                    "table": "reading_list",
                    "discord_id": discord_id,
                    "status": status,
                    "error_type": type(e).__name__,
                },
            )
            self._handle_database_error(
                e, {"discord_id": discord_id, "status": status, "operation": "get_reading_list"}
            )

    async def get_highly_rated_articles(
        self, discord_id: str, threshold: int = 4
    ) -> list["ReadingListItem"]:
        """查詢使用者的高評分文章

        Args:
            discord_id: Discord 使用者 ID
            threshold: 評分門檻（預設 4）

        Returns:
            高評分文章列表，按 rating 降序、added_at 降序排列

        Raises:
            SupabaseServiceError: 當資料庫查詢失敗時

        Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 13.1, 13.2
        """

        from app.schemas.article import ReadingListItem

        logger.info(f"Fetching highly rated articles (>= {threshold}) for user {discord_id}")

        try:
            # 取得使用者 UUID
            user_uuid = await self.get_or_create_user(discord_id)

            # 查詢高評分文章
            response = (
                self.client.table("reading_list")
                .select(
                    "article_id, status, rating, added_at, updated_at, articles(id, title, url, feeds(category))"
                )
                .eq("user_id", str(user_uuid))
                .gte("rating", threshold)
                .order("rating", desc=True)
                .order("added_at", desc=True)
                .execute()
            )

            if not response.data:
                logger.info("No highly rated articles found")
                return []

            # 轉換為 ReadingListItem 物件
            items = []
            for item_data in response.data:
                try:
                    # 從 JOIN 結果中提取文章資訊
                    article_data = item_data.get("articles")
                    if not article_data:
                        logger.warning(f"Article data missing for reading list item: {item_data}")
                        continue

                    # 從 nested JOIN 結果中提取 feed 資訊
                    feed_data = article_data.get("feeds")
                    if not feed_data:
                        logger.warning(f"Feed data missing for article: {article_data}")
                        continue

                    reading_list_item = ReadingListItem(
                        article_id=item_data["article_id"],
                        title=article_data["title"],
                        url=article_data["url"],
                        category=feed_data["category"],
                        status=item_data["status"],
                        rating=item_data.get("rating"),
                        added_at=datetime.fromisoformat(
                            item_data["added_at"].replace("Z", "+00:00")
                        ),
                        updated_at=datetime.fromisoformat(
                            item_data["updated_at"].replace("Z", "+00:00")
                        ),
                    )
                    items.append(reading_list_item)
                except Exception as e:
                    logger.warning(f"Failed to parse reading list item: {item_data}, error: {e}")
                    continue

            logger.info(f"Retrieved {len(items)} highly rated articles")
            return items

        except SupabaseServiceError:
            # 重新拋出已包裝的錯誤
            raise
        except Exception as e:
            logger.error(f"Failed to fetch highly rated articles: {e}", exc_info=True)
            self._handle_database_error(
                e,
                {
                    "discord_id": discord_id,
                    "threshold": threshold,
                    "operation": "get_highly_rated_articles",
                },
            )
