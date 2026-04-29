import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

# Global scheduler instance (initialized lazily)
_scheduler: AsyncIOScheduler | None = None

# Global dynamic scheduler instance (initialized lazily)
_dynamic_scheduler = None


def get_scheduler() -> AsyncIOScheduler | None:
    """Get the global scheduler instance."""
    return _scheduler


def get_dynamic_scheduler():
    """Get the global dynamic scheduler instance."""
    return _dynamic_scheduler


def __getattr__(name: str):
    """
    Dynamic attribute access for backward compatibility.
    Allows 'from app.tasks.scheduler import scheduler' to work correctly.
    """
    if name == "scheduler":
        return _scheduler
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Global health tracking
_scheduler_health = {
    "last_execution_time": None,
    "last_articles_processed": 0,
    "last_failed_operations": 0,
    "last_total_operations": 0,
}

# Track feed changes between executions (Requirement 16.5)
_last_feed_urls = set()


async def cleanup_token_blacklist():
    """
    定期清理過期的 Token 黑名單項目

    此任務每小時執行一次，移除已過期的 Token 以避免記憶體無限增長。

    Validates: Requirements 13.6, 14.3
    """
    try:
        from app.api.auth import get_token_blacklist

        logger.info("Starting token blacklist cleanup...")
        blacklist = get_token_blacklist()

        # 執行清理
        await blacklist.cleanup_expired()

        logger.info("Token blacklist cleanup completed successfully")

    except Exception as e:
        logger.error(f"Token blacklist cleanup failed: {e}", exc_info=True)


async def send_dm_notifications():
    """
    發送 DM 通知給所有啟用通知的使用者

    ⚠️ DEPRECATED: This function is deprecated in favor of personalized notification scheduling.
    Use the DynamicScheduler service for individual user notification scheduling instead.

    此任務會：
    1. 查詢所有啟用 DM 通知的使用者
    2. 為每個使用者查詢其訂閱的最新文章
    3. 發送個人化的文章摘要 DM

    Validates: Requirements 18.1, 18.2, 18.3, 18.4
    """
    logger.warning(
        "send_dm_notifications is deprecated. "
        "Use DynamicScheduler for personalized notification scheduling instead."
    )
    logger.info("Starting DM notification job")

    try:
        # 取得 Discord bot 實例
        from app.bot.client import bot

        # 確保 bot 已連線
        if not bot.is_ready():
            logger.warning("Bot is not ready, skipping DM notifications")
            return

        # 建立 DM 通知服務
        from app.services.dm_notification_service import DMNotificationService

        dm_service = DMNotificationService(bot)

        # 發送每週摘要給所有使用者
        stats = await dm_service.send_weekly_digest_to_all_users()

        logger.info(
            f"DM notification job completed: "
            f"Total users: {stats['total_users']}, "
            f"Successful: {stats['successful']}, "
            f"Failed: {stats['failed']}"
        )

    except Exception as e:
        logger.critical(f"Unexpected error during DM notification job: {e}", exc_info=True)
