import logging

logger = logging.getLogger(__name__)


class ArticleMixin:
    """Mixin extracted from SupabaseService — do not instantiate directly."""

    async def insert_articles(self, articles: list[dict]) -> "BatchResult":
        """批次插入或更新文章（使用 UPSERT 邏輯）

        使用 INSERT ... ON CONFLICT (url) DO UPDATE 實作 UPSERT，
        確保相同 URL 的文章不會重複插入。個別文章失敗時繼續處理其他文章。

        Args:
            articles: 文章資料字典列表

        Returns:
            BatchResult 包含插入、更新、失敗的統計資訊

        Raises:
            SupabaseServiceError: 當資料庫操作失敗時

        Validates: Requirements 4.2, 4.3, 4.4, 4.6, 4.8, 5.1, 5.2, 5.3, 5.4, 5.5,
                   5.6, 5.7, 5.8, 5.9, 15.1, 15.2, 15.3, 15.4, 16.1, 16.2, 16.3,
                   16.4, 13.1, 13.2
        """
        from app.schemas.article import BatchResult

        if not articles:
            logger.info("Empty articles list, returning zero counts")
            return BatchResult(inserted_count=0, updated_count=0, failed_count=0)

        logger.info(f"Starting batch insert of {len(articles)} articles with UPSERT logic")

        result = BatchResult(inserted_count=0, updated_count=0, failed_count=0)

        # 分批處理（每批 100 筆）- Requirement 4.2
        batch_size = 100
        for i in range(0, len(articles), batch_size):
            batch = articles[i : i + batch_size]
            logger.info(
                f"Processing batch {i // batch_size + 1}, articles {i + 1} to {min(i + batch_size, len(articles))}"
            )

            # 個別處理每篇文章以支援部分失敗 - Requirement 4.8
            for article in batch:
                try:
                    # 驗證資料 - Requirement 4.6
                    self._validate_article_data(article)

                    # 準備插入資料
                    article_data = {
                        "title": self._truncate_text(article.get("title", ""), 2000),
                        "url": article["url"],
                        "feed_id": str(article["feed_id"]),
                        "published_at": article.get("published_at"),
                        "tinkering_index": article.get("tinkering_index"),
                        "ai_summary": (
                            self._truncate_text(article.get("ai_summary", ""), 5000)
                            if article.get("ai_summary")
                            else None
                        ),
                        "embedding": article.get("embedding"),
                    }

                    # 移除 None 值以避免覆蓋預設值
                    article_data = {k: v for k, v in article_data.items() if v is not None}

                    # 先檢查文章是否存在以追蹤 inserted vs updated
                    # 這是為了統計目的，實際的 UPSERT 邏輯在下面
                    existing = (
                        self.client.table("articles")
                        .select("id")
                        .eq("url", article["url"])
                        .execute()
                    )
                    is_update = bool(existing.data and len(existing.data) > 0)

                    # 使用 UPSERT 邏輯：INSERT ... ON CONFLICT (url) DO UPDATE
                    # Supabase Python client 使用 upsert() 方法實作 - Requirement 4.3, 4.4
                    # on_conflict 參數指定衝突時的行為
                    self.client.table("articles").upsert(
                        article_data,
                        on_conflict="url",  # 當 URL 衝突時更新
                        returning="minimal",  # 減少返回資料以提升效能
                    ).execute()

                    # 追蹤插入或更新 - Requirement 4.6
                    if is_update:
                        result.updated_count += 1
                        logger.debug(f"Updated article via UPSERT: {article['url']}")
                    else:
                        result.inserted_count += 1
                        logger.debug(f"Inserted article via UPSERT: {article['url']}")

                except Exception as e:
                    # 個別文章失敗時繼續處理其他文章 - Requirement 4.8
                    result.failed_count += 1
                    error_info = {
                        "article": {
                            "url": article.get("url", "unknown"),
                            "title": article.get("title", "unknown")[:100],  # 截斷標題以避免日誌過長
                        },
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                    result.failed_articles.append(error_info)
                    logger.error(
                        f"Failed to insert/update article: {article.get('url', 'unknown')} - Error: {e!s}",
                        extra=error_info,
                        exc_info=True,
                    )
                    # 繼續處理下一篇文章，不中斷批次處理

        logger.info(
            f"Batch insert completed: {result.inserted_count} inserted, "
            f"{result.updated_count} updated, {result.failed_count} failed"
        )

        return result

    def _validate_article_data(self, article: dict) -> None:
        """驗證文章資料

        Args:
            article: 文章資料字典

        Raises:
            ValueError: 當資料驗證失敗時

        Validates: Requirements 16.1, 16.2
        """
        # 驗證必要欄位
        if "url" not in article or not article["url"]:
            raise ValueError("Article must have a 'url' field")

        if "feed_id" not in article or not article["feed_id"]:
            raise ValueError("Article must have a 'feed_id' field")

        # 驗證 URL 格式
        self._validate_url(article["url"])

        # 驗證 tinkering_index 範圍（如果提供）
        if "tinkering_index" in article and article["tinkering_index"] is not None:
            tinkering_index = article["tinkering_index"]
            if not isinstance(tinkering_index, int) or tinkering_index < 1 or tinkering_index > 5:
                # Log the invalid value but don't raise - set to None instead
                logger.warning(
                    f"Invalid tinkering_index: {tinkering_index} for article {article.get('url')}. "
                    f"Must be an integer between 1 and 5. Setting to None."
                )
                article["tinkering_index"] = None

    async def check_article_exists(self, url: str) -> bool:
        """檢查文章 URL 是否已存在於資料庫

        Args:
            url: 文章 URL

        Returns:
            True 如果文章存在，False 如果不存在

        Raises:
            SupabaseServiceError: 當資料庫查詢失敗時
            ValueError: 當 URL 格式無效時

        Validates: Requirements 2.2, 2.3
        """
        logger.debug(f"Checking if article exists: {url}")

        try:
            # 驗證 URL 格式
            validated_url = self._validate_url(url)

            # 查詢 articles 表檢查 URL 是否存在
            # 使用 SELECT id 進行高效查詢（只需要知道是否存在）
            response = self.client.table("articles").select("id").eq("url", validated_url).execute()

            # 檢查是否有返回資料
            exists = bool(response.data and len(response.data) > 0)

            logger.debug(f"Article {'exists' if exists else 'does not exist'}: {url}")
            return exists

        except (ValueError, SupabaseServiceError):
            # 重新拋出驗證錯誤和已包裝的錯誤
            raise
        except Exception as e:
            logger.error(f"Failed to check article existence: {e}", exc_info=True)
            self._handle_database_error(e, {"url": url, "operation": "check_article_exists"})

    async def get_unanalyzed_articles(self, limit: int = 100) -> list[dict]:
        """查詢尚未分析的文章（ai_summary 或 tinkering_index 為 NULL）

        此方法用於識別需要重新處理的文章，因為 LLM 分析失敗。
        查詢 ai_summary IS NULL 或 tinkering_index IS NULL 的文章。

        Args:
            limit: 返回的最大文章數量（預設 100）

        Returns:
            文章字典列表，包含 id, url, title, feed_id

        Raises:
            SupabaseServiceError: 當資料庫查詢失敗時

        Validates: Requirements 13.1, 13.2, 13.7
        """
        logger.info(f"Fetching unanalyzed articles with limit {limit}")

        try:
            # 查詢 ai_summary IS NULL 或 tinkering_index IS NULL 的文章
            # 使用 .or_() 來組合條件
            response = (
                self.client.table("articles")
                .select("id, url, title, feed_id")
                .or_("ai_summary.is.null,tinkering_index.is.null")
                .limit(limit)
                .execute()
            )

            if not response.data:
                logger.info("No unanalyzed articles found")
                return []

            # 返回文章列表
            articles = response.data
            logger.info(f"Retrieved {len(articles)} unanalyzed articles")
            return articles

        except SupabaseServiceError:
            # 重新拋出已包裝的錯誤
            raise
        except Exception as e:
            logger.error(f"Failed to fetch unanalyzed articles: {e}", exc_info=True)
            self._handle_database_error(e, {"limit": limit, "operation": "get_unanalyzed_articles"})

    async def get_user_articles(
        self,
        discord_id: str,
        days: int = 7,
        limit: int = 20,
        frequency: str | None = None,
    ) -> list["ArticleSchema"]:
        """查詢使用者訂閱的文章

        Args:
            discord_id: Discord 使用者 ID
            days: 查詢最近幾天的文章（如果提供 frequency 則忽略此參數）
            limit: 返回的最大文章數量
            frequency: 通知頻率 ('daily', 'weekly', 'monthly')，用於自動調整時間範圍

        Returns:
            文章列表，按 tinkering_index 降序排列

        Raises:
            SupabaseServiceError: 當資料庫查詢失敗時
        """
        from datetime import datetime, timedelta

        from app.schemas.article import ArticleSchema

        # 根據頻率自動調整時間範圍
        if frequency:
            if frequency == "daily":
                days = 1
            elif frequency == "weekly":
                days = 7
            elif frequency == "monthly":
                days = 30
            else:
                # 預設使用傳入的 days 參數
                pass

        logger.info(
            "Database operation: get_user_articles",
            extra={
                "operation_type": "SELECT",
                "table": "articles",
                "discord_id": discord_id,
                "days": days,
                "limit": limit,
                "frequency": frequency,
            },
        )

        try:
            # 取得使用者 UUID
            user_uuid = await self.get_or_create_user(discord_id)

            # 計算時間範圍
            cutoff_date = datetime.now(UTC) - timedelta(days=days)

            # 查詢使用者訂閱的 feeds（只取啟用通知的）
            subscriptions_response = (
                self.client.table("user_subscriptions")
                .select("feed_id")
                .eq("user_id", str(user_uuid))
                .eq("notification_enabled", True)
                .execute()
            )

            if not subscriptions_response.data:
                logger.info(f"User {discord_id} has no subscriptions")
                return []

            # 提取 feed IDs
            feed_ids = [sub["feed_id"] for sub in subscriptions_response.data]

            # 查詢已發送給使用者的文章 IDs（用於排除重複）
            # Note: dm_sent_articles table may not exist yet, handle gracefully
            sent_article_ids = []
            try:
                sent_articles_response = (
                    self.client.table("dm_sent_articles")
                    .select("article_id")
                    .eq("user_id", str(user_uuid))
                    .execute()
                )
                # 提取已發送的文章 IDs
                sent_article_ids = (
                    [record["article_id"] for record in sent_articles_response.data]
                    if sent_articles_response.data
                    else []
                )
            except Exception as e:
                # If dm_sent_articles table doesn't exist, log warning and continue
                logger.warning(
                    f"Could not query dm_sent_articles table (may not exist yet): {e}",
                    extra={
                        "operation_type": "SELECT",
                        "table": "dm_sent_articles",
                        "user_uuid": str(user_uuid),
                    },
                )

            # 查詢文章，排除已發送的文章
            query = (
                self.client.table("articles")
                .select(
                    "id, title, url, published_at, tinkering_index, ai_summary, feed_id, feeds(category)"
                )
                .in_("feed_id", feed_ids)
                .gte("published_at", cutoff_date.isoformat())
                .not_.is_("tinkering_index", "null")
                .order("tinkering_index", desc=True)
                .limit(limit)
            )

            # 如果有已發送的文章，排除它們
            if sent_article_ids:
                query = query.not_.in_("id", sent_article_ids)

            response = query.execute()

            if not response.data:
                logger.info(f"No articles found for user {discord_id}")
                return []

            # 轉換為 ArticleSchema 物件
            articles = []
            for article_data in response.data:
                try:
                    # 從 JOIN 結果中提取 feed 資訊
                    feed_data = article_data.get("feeds")
                    if not feed_data:
                        logger.warning(f"Feed data missing for article: {article_data}")
                        continue

                    article = ArticleSchema(
                        id=article_data["id"],  # Include article ID
                        title=article_data["title"],
                        url=article_data["url"],
                        feed_id=article_data["feed_id"],
                        feed_name="",  # 不需要
                        category=feed_data.get("category", "其他"),
                        published_at=(
                            datetime.fromisoformat(
                                article_data["published_at"].replace("Z", "+00:00")
                            )
                            if article_data.get("published_at")
                            else None
                        ),
                        tinkering_index=article_data.get("tinkering_index"),
                        ai_summary=article_data.get("ai_summary"),
                    )
                    articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to parse article: {article_data}, error: {e}")
                    continue

            logger.info(
                "Database operation completed: get_user_articles",
                extra={
                    "operation_type": "SELECT",
                    "table": "articles",
                    "affected_records": len(articles),
                },
            )

            return articles

        except SupabaseServiceError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to fetch user articles: {e}",
                exc_info=True,
                extra={
                    "operation_type": "SELECT",
                    "table": "articles",
                    "discord_id": discord_id,
                    "days": days,
                    "limit": limit,
                    "error_type": type(e).__name__,
                },
            )
            self._handle_database_error(
                e,
                {
                    "discord_id": discord_id,
                    "days": days,
                    "limit": limit,
                    "operation": "get_user_articles",
                },
            )
