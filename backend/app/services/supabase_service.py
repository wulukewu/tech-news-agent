import asyncio
import logging
from uuid import UUID

from supabase import Client, create_client

from app.core.config import settings
from app.core.exceptions import SupabaseServiceError
from app.services._mixins.article_mixin import ArticleMixin
from app.services._mixins.feed_mixin import FeedMixin
from app.services._mixins.notification_mixin import NotificationMixin
from app.services._mixins.reading_list_mixin import ReadingListMixin
from app.services._mixins.user_mixin import UserMixin

logger = logging.getLogger(__name__)


class SupabaseService(UserMixin, FeedMixin, ArticleMixin, ReadingListMixin, NotificationMixin):
    """Supabase 資料存取層服務

    Methods are organized into domain-specific mixins:
    - UserMixin: user CRUD (get_or_create_user, get_user_by_*)
    - FeedMixin: feed & subscription management
    - ArticleMixin: article insert/query
    - ReadingListMixin: reading list operations
    - NotificationMixin: DM notification settings
    """

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
