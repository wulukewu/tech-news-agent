import logging
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class UserMixin:
    """Mixin extracted from SupabaseService — do not instantiate directly."""

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

    async def get_user_by_discord_id(self, discord_id: str) -> Optional[dict]:
        """取得使用者資料（根據 Discord ID）

        Args:
            discord_id: Discord 使用者 ID

        Returns:
            使用者資料字典，包含 id, discord_id 等欄位，如果找不到則返回 None

        Raises:
            SupabaseServiceError: 當資料庫操作失敗時
        """
        logger.info(
            "Database operation: get_user_by_discord_id",
            extra={"operation_type": "SELECT", "table": "users", "discord_id": discord_id},
        )

        try:
            response = (
                self.client.table("users")
                .select("id, discord_id, created_at")
                .eq("discord_id", discord_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                user_data = response.data[0]
                logger.info(
                    "Database operation completed: get_user_by_discord_id (user found)",
                    extra={
                        "operation_type": "SELECT",
                        "table": "users",
                        "affected_records": 1,
                        "user_uuid": user_data["id"],
                    },
                )
                return user_data
            else:
                logger.info(
                    "Database operation completed: get_user_by_discord_id (user not found)",
                    extra={
                        "operation_type": "SELECT",
                        "table": "users",
                        "affected_records": 0,
                        "discord_id": discord_id,
                    },
                )
                return None

        except Exception as e:
            logger.error(
                f"Failed to get user by discord_id: {e}",
                exc_info=True,
                extra={
                    "operation_type": "SELECT",
                    "table": "users",
                    "discord_id": discord_id,
                    "error_type": type(e).__name__,
                },
            )
            self._handle_database_error(
                e, {"discord_id": discord_id, "operation": "get_user_by_discord_id"}
            )

    async def get_user_by_id(self, user_id: UUID) -> Optional[dict]:
        """取得使用者資料（根據 User ID）

        Args:
            user_id: 使用者 UUID

        Returns:
            使用者資料字典，包含 id, discord_id 等欄位，如果找不到則返回 None

        Raises:
            SupabaseServiceError: 當資料庫操作失敗時
        """
        logger.info(
            "Database operation: get_user_by_id",
            extra={"operation_type": "SELECT", "table": "users", "user_id": str(user_id)},
        )

        try:
            response = (
                self.client.table("users")
                .select("id, discord_id, created_at")
                .eq("id", str(user_id))
                .execute()
            )

            if response.data and len(response.data) > 0:
                user_data = response.data[0]
                logger.info(
                    "Database operation completed: get_user_by_id (user found)",
                    extra={
                        "operation_type": "SELECT",
                        "table": "users",
                        "affected_records": 1,
                        "user_id": str(user_id),
                    },
                )
                return user_data
            else:
                logger.info(
                    "Database operation completed: get_user_by_id (user not found)",
                    extra={
                        "operation_type": "SELECT",
                        "table": "users",
                        "affected_records": 0,
                        "user_id": str(user_id),
                    },
                )
                return None

        except Exception as e:
            logger.error(
                f"Failed to get user by id: {e}",
                exc_info=True,
                extra={
                    "operation_type": "SELECT",
                    "table": "users",
                    "user_id": str(user_id),
                    "error_type": type(e).__name__,
                },
            )
            self._handle_database_error(e, {"user_id": str(user_id), "operation": "get_user_by_id"})
