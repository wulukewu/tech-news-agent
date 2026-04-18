import asyncio
import logging
from datetime import UTC, datetime
from typing import Optional

from supabase import Client, create_client

from app.core.config import settings
from app.core.exceptions import SupabaseServiceError

logger = logging.getLogger(__name__)


class SupabaseService:
    """Supabase 資料存取層服務"""

    def __init__(self, client: Client | None = None, validate_connection: bool = True):
        """初始化 Supabase 服務

        Args:
            client: 可選的 Supabase client（用於測試依賴注入）
            validate_connection: 是否驗證連線（預設為 True，測試時可設為 False）

        Raises:
            SupabaseServiceError: 當配置缺失或連線失敗時
        """
        logger.info("Initializing SupabaseService")

        # 驗證配置存在
        if not settings.supabase_url or not settings.supabase_key:
            raise SupabaseServiceError(
                "Supabase configuration is missing",
                context={
                    "supabase_url_present": bool(settings.supabase_url),
                    "supabase_key_present": bool(settings.supabase_key),
                    "troubleshooting": "Check .env file and ensure SUPABASE_URL and SUPABASE_KEY are set",
                },
            )

        # 使用提供的 client 或建立新的 client
        if client is not None:
            self.client = client
            logger.info("Using provided Supabase client for testing")
        else:
            try:
                self.client = create_client(settings.supabase_url, settings.supabase_key)
                logger.info("Successfully created Supabase client")
            except Exception as e:
                logger.error(f"Failed to create Supabase client: {e}", exc_info=True)
                raise SupabaseServiceError(
                    "Failed to initialize Supabase client",
                    original_error=e,
                    context={
                        "supabase_url": settings.supabase_url,
                        "troubleshooting": [
                            "Check network connection",
                            "Verify Supabase project is active",
                            "Check firewall settings",
                            "Visit https://status.supabase.com for service status",
                        ],
                    },
                )

        # 驗證連線（Requirement 14.4）
        if validate_connection:
            self._validate_connection()

        logger.info("SupabaseService initialized successfully")

    def _validate_connection(self, timeout: int = 10) -> None:
        """驗證 Supabase 連線

        Args:
            timeout: 連線超時時間（秒），預設 10 秒

        Raises:
            SupabaseServiceError: 當連線驗證失敗時（Requirement 14.5, 14.7）
        """
        logger.info("Validating Supabase connection")

        try:
            # 使用簡單的查詢來驗證連線
            # 嘗試查詢一個系統表或執行一個簡單的操作
            # 使用 asyncio.wait_for 來實作超時控制（Requirement 14.7）
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("Connection validation timed out")

            # 設定超時處理器
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)

            try:
                # 執行簡單的查詢來驗證連線
                # 查詢 users 表的計數（不需要返回資料）
                response = self.client.table("users").select("id", count="exact").limit(0).execute()

                # 取消超時
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

                logger.info("Supabase connection validated successfully")

            except TimeoutError as e:
                # 取消超時
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                raise e
            except Exception as e:
                # 取消超時
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                raise e

        except TimeoutError as e:
            # 連線超時錯誤（Requirement 14.7）
            logger.error(f"Connection validation timed out after {timeout} seconds", exc_info=True)
            raise SupabaseServiceError(
                f"Connection validation timed out after {timeout} seconds",
                original_error=e,
                context={
                    "supabase_url": settings.supabase_url,
                    "timeout_seconds": timeout,
                    "troubleshooting": [
                        "Check network connection speed and stability",
                        "Verify Supabase project is responding",
                        "Check if there are any network proxies or firewalls blocking the connection",
                        "Try increasing the timeout value if on a slow network",
                        "Visit https://status.supabase.com to check service status",
                    ],
                },
            )
        except Exception as e:
            # 其他連線錯誤（Requirement 14.5）
            error_str = str(e).lower()
            logger.error(f"Connection validation failed: {e}", exc_info=True)

            # 提供更具體的錯誤訊息和故障排除提示
            troubleshooting_hints = [
                "Check network connection",
                "Verify Supabase project is active and accessible",
                "Ensure SUPABASE_URL and SUPABASE_KEY are correct",
                "Check firewall settings and network security rules",
                "Visit https://status.supabase.com for service status",
            ]

            # 根據錯誤類型提供更具體的提示
            if "authentication" in error_str or "unauthorized" in error_str or "401" in error_str:
                troubleshooting_hints.insert(
                    0, "Verify SUPABASE_KEY is correct and has not expired"
                )
                troubleshooting_hints.insert(1, "Check if the API key has sufficient permissions")
            elif "not found" in error_str or "404" in error_str:
                troubleshooting_hints.insert(0, "Verify SUPABASE_URL is correct")
                troubleshooting_hints.insert(
                    1, "Ensure the Supabase project exists and is not deleted"
                )
            elif "timeout" in error_str or "timed out" in error_str:
                troubleshooting_hints.insert(0, "Check network connection speed")
                troubleshooting_hints.insert(1, "Try again in a few moments")
            elif "connection" in error_str or "network" in error_str:
                troubleshooting_hints.insert(0, "Check internet connectivity")
                troubleshooting_hints.insert(1, "Verify DNS resolution is working")
            elif "ssl" in error_str or "certificate" in error_str:
                troubleshooting_hints.insert(0, "Check SSL/TLS certificate validity")
                troubleshooting_hints.insert(1, "Ensure system time is correct")

            raise SupabaseServiceError(
                "Failed to validate Supabase connection",
                original_error=e,
                context={
                    "supabase_url": settings.supabase_url,
                    "error_type": type(e).__name__,
                    "troubleshooting": troubleshooting_hints,
                },
            )

    async def close(self) -> None:
        """關閉連線並清理資源

        此方法用於清理 Supabase 連線和相關資源。
        雖然 Supabase Python client 不需要顯式關閉連線，
        但提供此方法以支援 context manager 協議和未來的資源管理需求。

        Validates: Requirements 17.2
        """
        logger.info("Closing SupabaseService and cleaning up resources")
        # Supabase Python client 使用 httpx，不需要顯式關閉
        # 但我們記錄清理動作以便追蹤
        logger.info("SupabaseService closed successfully")

    async def __aenter__(self):
        """支援 async context manager

        允許使用 async with 語法來自動管理資源：
        async with SupabaseService() as service:
            # 使用 service
            pass
        # 自動呼叫 close()

        Returns:
            self: SupabaseService 實例

        Validates: Requirements 17.3
        """
        logger.debug("Entering SupabaseService context")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """支援 async context manager，自動清理資源

        當離開 async with 區塊時自動呼叫，確保資源被正確清理。
        無論是否發生例外都會執行清理。

        Args:
            exc_type: 例外類型（如果有）
            exc_val: 例外值（如果有）
            exc_tb: 例外追蹤（如果有）

        Validates: Requirements 17.3
        """
        logger.debug("Exiting SupabaseService context")
        if exc_type is not None:
            logger.warning(
                f"Exiting SupabaseService context with exception: {exc_type.__name__}",
                extra={"exception": str(exc_val)},
            )
        await self.close()

    # Validation Helper Methods

    def _validate_status(self, status: str) -> str:
        """驗證並正規化狀態值

        Args:
            status: 狀態值（不區分大小寫）

        Returns:
            正規化的狀態值（Title Case）

        Raises:
            ValueError: 當狀態值無效時

        Validates: Requirements 7.2, 7.3, 16.6
        """
        normalized = status.strip().title()
        allowed_statuses = {"Unread", "Read", "Archived"}

        if normalized not in allowed_statuses:
            raise ValueError(
                f"Invalid status: '{status}'. Allowed values are: {', '.join(sorted(allowed_statuses))}"
            )

        return normalized

    def _validate_rating(self, rating: int) -> None:
        """驗證評分範圍

        Args:
            rating: 評分值

        Raises:
            ValueError: 當評分超出範圍時

        Validates: Requirements 8.2, 8.3
        """
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            raise ValueError(
                f"Invalid rating: {rating}. Rating must be an integer between 1 and 5 (inclusive)"
            )

    def _validate_uuid(self, uuid_str: str) -> "UUID":
        """驗證 UUID 格式

        Args:
            uuid_str: UUID 字串

        Returns:
            UUID 物件

        Raises:
            ValueError: 當 UUID 格式無效時

        Validates: Requirements 16.5
        """
        from uuid import UUID

        try:
            return UUID(uuid_str)
        except (ValueError, AttributeError, TypeError) as e:
            raise ValueError(
                f"Invalid UUID format: '{uuid_str}'. Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            ) from e

    def _validate_url(self, url: str) -> str:
        """驗證 URL 格式

        Args:
            url: URL 字串

        Returns:
            驗證後的 URL

        Raises:
            ValueError: 當 URL 格式無效時

        Validates: Requirements 16.1
        """
        if not url or not isinstance(url, str):
            raise ValueError("Invalid URL: URL must be a non-empty string")

        url = url.strip()

        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError(f"Invalid URL: '{url}'. URL must start with http:// or https://")

        return url

    def _truncate_text(self, text: str, max_length: int) -> str:
        """截斷文字至指定長度

        Args:
            text: 要截斷的文字
            max_length: 最大長度

        Returns:
            截斷後的文字

        Validates: Requirements 16.3, 16.4
        """
        if not text:
            return text

        if len(text) <= max_length:
            return text

        return text[:max_length]

    def _handle_database_error(self, error: Exception, context: dict) -> None:
        """處理資料庫錯誤，包裝為 SupabaseServiceError

        Args:
            error: 原始資料庫錯誤
            context: 錯誤上下文資訊

        Raises:
            SupabaseServiceError: 包裝後的錯誤

        Validates: Requirements 13.3, 13.4, 13.5, 13.6
        """
        error_str = str(error).lower()

        # Check for specific constraint violations
        # Order matters: check more specific patterns first

        # Check for duplicate key (unique constraint)
        if "duplicate key" in error_str and "unique constraint" in error_str:
            # 解析重複的欄位名稱
            field = self._extract_field_from_error(error_str)
            raise SupabaseServiceError(
                f"Duplicate entry: {field} already exists",
                original_error=error,
                context={**context, "constraint_type": "unique"},
            )

        # Check for foreign key constraint
        elif "foreign key" in error_str and "foreign key constraint" in error_str:
            # 解析外鍵參考
            reference = self._extract_reference_from_error(error_str)
            raise SupabaseServiceError(
                f"Invalid reference: {reference} does not exist",
                original_error=error,
                context={**context, "constraint_type": "foreign_key"},
            )

        # Check for check constraint
        elif "check constraint" in error_str and "violates check constraint" in error_str:
            # 解析檢查約束名稱
            constraint = self._extract_constraint_from_error(error_str)
            raise SupabaseServiceError(
                f"Validation failed: {constraint}",
                original_error=error,
                context={**context, "constraint_type": "check"},
            )

        # Check for not null constraint
        elif "null value in column" in error_str and "not-null constraint" in error_str:
            # 解析缺少的欄位
            field = self._extract_field_from_error(error_str)
            raise SupabaseServiceError(
                f"Missing required field: '{field}' cannot be null",
                original_error=error,
                context={**context, "constraint_type": "not_null"},
            )

        else:
            # 通用資料庫錯誤
            raise SupabaseServiceError(
                f"Database operation failed: {error}", original_error=error, context=context
            )

    def _extract_field_from_error(self, error_str: str) -> str:
        """從錯誤訊息中提取欄位名稱

        Args:
            error_str: 錯誤訊息字串

        Returns:
            欄位名稱或通用描述
        """
        # 嘗試從常見的 PostgreSQL 錯誤格式中提取欄位名稱
        import re

        # 嘗試匹配 "column \"field_name\""
        match = re.search(r'column\s+"([^"]+)"', error_str)
        if match:
            return match.group(1)

        # 嘗試匹配 "key (field_name)" - 更寬鬆的匹配
        match = re.search(r"key\s+\(([^)]+)\)", error_str)
        if match:
            return match.group(1)

        # 嘗試匹配 "null value in column \"field_name\""
        match = re.search(r'null value in column\s+"([^"]+)"', error_str)
        if match:
            return match.group(1)

        return "field"

    def _extract_reference_from_error(self, error_str: str) -> str:
        """從錯誤訊息中提取參考資訊

        Args:
            error_str: 錯誤訊息字串

        Returns:
            參考資訊或通用描述
        """
        import re

        # 嘗試匹配 "table \"table_name\""
        match = re.search(r'table\s+"([^"]+)"', error_str)
        if match:
            return f"reference to table {match.group(1)}"

        # 嘗試匹配 "constraint \"constraint_name\""
        match = re.search(r'constraint\s+"([^"]+)"', error_str)
        if match:
            return match.group(1)

        return "reference"

    def _extract_constraint_from_error(self, error_str: str) -> str:
        """從錯誤訊息中提取約束資訊

        Args:
            error_str: 錯誤訊息字串

        Returns:
            約束資訊或通用描述
        """
        import re

        # 嘗試匹配 "constraint \"constraint_name\""
        match = re.search(r'constraint\s+"([^"]+)"', error_str)
        if match:
            return match.group(1)

        return "constraint violation"

    async def _execute_with_retry(self, operation, max_retries: int = 3, base_delay: float = 1.0):
        """執行操作並在暫時性錯誤時重試

        Args:
            operation: 要執行的操作（callable）
            max_retries: 最大重試次數
            base_delay: 基礎延遲時間（秒）

        Returns:
            操作的返回值

        Raises:
            Exception: 當所有重試都失敗時

        Validates: Requirements 15.6
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return await operation()
            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # 判斷是否為暫時性錯誤
                is_transient = any(
                    keyword in error_str
                    for keyword in ["timeout", "connection", "temporary", "unavailable"]
                )

                if not is_transient or attempt == max_retries - 1:
                    # 非暫時性錯誤或已達最大重試次數
                    raise

                # 計算退避時間
                delay = base_delay * (2**attempt)
                logger.warning(
                    f"Transient error on attempt {attempt + 1}/{max_retries}, "
                    f"retrying in {delay}s: {e}"
                )
                await asyncio.sleep(delay)

        # 不應該到達這裡，但為了型別安全
        raise last_error

    # CRUD Operations

    async def get_or_create_user(self, discord_id: str) -> "UUID":
        """取得或建立使用者

        Args:
            discord_id: Discord 使用者 ID

        Returns:
            使用者的 UUID

        Raises:
            SupabaseServiceError: 當資料庫操作失敗時

        Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 13.1, 13.2, 17.3
        """
        from uuid import UUID

        logger.info(
            "Database operation: get_or_create_user",
            extra={"operation_type": "SELECT", "table": "users", "discord_id": discord_id},
        )

        try:
            # 先嘗試查詢使用者
            response = (
                self.client.table("users").select("id").eq("discord_id", discord_id).execute()
            )

            if response.data and len(response.data) > 0:
                # 使用者已存在，返回 UUID
                user_uuid = UUID(response.data[0]["id"])
                logger.info(
                    "Database operation completed: get_or_create_user (user found)",
                    extra={
                        "operation_type": "SELECT",
                        "table": "users",
                        "affected_records": 1,
                        "user_uuid": str(user_uuid),
                    },
                )
                return user_uuid

            # 使用者不存在，建立新使用者
            logger.info(
                "Database operation: create_user",
                extra={"operation_type": "INSERT", "table": "users", "discord_id": discord_id},
            )

            insert_response = (
                self.client.table("users").insert({"discord_id": discord_id}).execute()
            )

            if insert_response.data and len(insert_response.data) > 0:
                user_uuid = UUID(insert_response.data[0]["id"])
                logger.info(
                    "Database operation completed: create_user",
                    extra={
                        "operation_type": "INSERT",
                        "table": "users",
                        "affected_records": 1,
                        "user_uuid": str(user_uuid),
                    },
                )

                # 為新用戶自動訂閱所有 feeds
                try:
                    feeds_response = (
                        self.client.table("feeds").select("id").eq("is_active", True).execute()
                    )
                    if feeds_response.data:
                        subscriptions = [
                            {"user_id": str(user_uuid), "feed_id": feed["id"]}
                            for feed in feeds_response.data
                        ]
                        if subscriptions:
                            self.client.table("user_subscriptions").insert(subscriptions).execute()
                            logger.info(
                                f"Auto-subscribed new user to {len(subscriptions)} feeds",
                                extra={
                                    "user_uuid": str(user_uuid),
                                    "feed_count": len(subscriptions),
                                },
                            )
                except Exception as sub_error:
                    # 訂閱失敗不應該阻止用戶創建
                    logger.warning(
                        f"Failed to auto-subscribe new user to feeds: {sub_error!s}",
                        extra={"user_uuid": str(user_uuid)},
                    )

                return user_uuid
            else:
                raise SupabaseServiceError(
                    "Failed to create user: No data returned from insert operation",
                    context={"discord_id": discord_id},
                )

        except SupabaseServiceError:
            # 重新拋出已經包裝的錯誤
            raise
        except Exception as e:
            error_str = str(e).lower()

            # 處理 unique constraint 違反（可能是並發建立）
            if "duplicate key" in error_str or "unique" in error_str or "23505" in error_str:
                logger.warning(
                    "Concurrent user creation detected, retrying query",
                    extra={
                        "operation_type": "SELECT",
                        "table": "users",
                        "discord_id": discord_id,
                        "error_type": "concurrent_creation",
                    },
                )
                # 重新查詢以取得 UUID
                try:
                    response = (
                        self.client.table("users")
                        .select("id")
                        .eq("discord_id", discord_id)
                        .execute()
                    )
                    if response.data and len(response.data) > 0:
                        user_uuid = UUID(response.data[0]["id"])
                        logger.info(
                            "Database operation completed: get_or_create_user (retry after concurrent creation)",
                            extra={
                                "operation_type": "SELECT",
                                "table": "users",
                                "affected_records": 1,
                                "user_uuid": str(user_uuid),
                            },
                        )
                        return user_uuid
                except Exception as retry_error:
                    logger.error(
                        f"Failed to query user after concurrent creation: {retry_error}",
                        exc_info=True,
                        extra={
                            "operation_type": "SELECT",
                            "table": "users",
                            "discord_id": discord_id,
                            "error_type": type(retry_error).__name__,
                        },
                    )
                    self._handle_database_error(
                        retry_error,
                        {"discord_id": discord_id, "operation": "get_or_create_user_retry"},
                    )

            # 處理其他資料庫錯誤
            logger.error(
                f"Failed to get or create user: {e}",
                exc_info=True,
                extra={
                    "operation_type": "INSERT/SELECT",
                    "table": "users",
                    "discord_id": discord_id,
                    "error_type": type(e).__name__,
                },
            )
            self._handle_database_error(
                e, {"discord_id": discord_id, "operation": "get_or_create_user"}
            )

    async def get_active_feeds(self) -> list["RSSSource"]:
        """取得所有啟用的 RSS 訂閱源

        Returns:
            啟用的訂閱源列表，按 category 和 name 排序

        Raises:
            SupabaseServiceError: 當資料庫查詢失敗時

        Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 13.1, 13.2
        """

        from app.schemas.article import RSSSource

        logger.info("Fetching active feeds")

        try:
            # 查詢啟用的訂閱源，按 category 和 name 排序
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

            # 轉換為 RSSSource 物件
            feeds = []
            for feed_data in response.data:
                try:
                    rss_source = RSSSource(
                        id=feed_data["id"],
                        name=feed_data["name"],
                        url=feed_data["url"],
                        category=feed_data["category"],
                    )
                    feeds.append(rss_source)
                except Exception as e:
                    logger.warning(f"Failed to parse feed data: {feed_data}, error: {e}")
                    continue

            logger.info(f"Retrieved {len(feeds)} active feeds")
            return feeds

        except SupabaseServiceError:
            # 重新拋出已經包裝的錯誤
            raise
        except Exception as e:
            logger.error(f"Failed to fetch active feeds: {e}", exc_info=True)
            self._handle_database_error(e, {"operation": "get_active_feeds"})

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
                            "title": article.get("title", "unknown")[
                                :100
                            ],  # 截斷標題以避免日誌過長
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

    async def create_feed(self, name: str, url: str, category: str) -> "UUID":
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
            insert_response = (
                self.client.table("feeds")
                .insert({"name": name, "url": url, "category": category, "is_active": True})
                .execute()
            )

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
                .select("feed_id, subscribed_at, feeds(id, name, url, category)")
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

    async def record_sent_articles(self, discord_id: str, article_ids: list[str]) -> None:
        """記錄已發送給使用者的文章

        將文章記錄到 dm_sent_articles 表格，用於追蹤哪些文章已經透過 DM 通知發送給使用者。
        使用 UPSERT 邏輯避免重複記錄。

        Args:
            discord_id: Discord 使用者 ID
            article_ids: 已發送的文章 ID 列表

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
            },
        )

        try:
            # 取得使用者 UUID
            user_uuid = await self.get_or_create_user(discord_id)

            # 準備記錄資料
            records = [
                {"user_id": str(user_uuid), "article_id": str(article_id)}
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

    async def get_user_articles(
        self, discord_id: str, days: int = 7, limit: int = 20
    ) -> list["ArticleSchema"]:
        """查詢使用者訂閱的文章

        Args:
            discord_id: Discord 使用者 ID
            days: 查詢最近幾天的文章
            limit: 返回的最大文章數量

        Returns:
            文章列表，按 tinkering_index 降序排列

        Raises:
            SupabaseServiceError: 當資料庫查詢失敗時
        """
        from datetime import datetime, timedelta

        from app.schemas.article import ArticleSchema

        logger.info(
            "Database operation: get_user_articles",
            extra={
                "operation_type": "SELECT",
                "table": "articles",
                "discord_id": discord_id,
                "days": days,
                "limit": limit,
            },
        )

        try:
            # 取得使用者 UUID
            user_uuid = await self.get_or_create_user(discord_id)

            # 計算時間範圍
            cutoff_date = datetime.now(UTC) - timedelta(days=days)

            # 查詢使用者訂閱的 feeds
            subscriptions_response = (
                self.client.table("user_subscriptions")
                .select("feed_id")
                .eq("user_id", str(user_uuid))
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
