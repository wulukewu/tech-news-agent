import logging
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.services.supabase_service import SupabaseService

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


from app.tasks._fetch_job import background_fetch_job
from app.tasks._notify_jobs import cleanup_token_blacklist


async def version_tracking_job():
    """
    Background job to check for technology version updates.
    Runs every 6 hours to monitor technology frameworks and create reminders.
    """
    logger.info("Starting version tracking job...")

    try:
        from app.qa_agent.intelligent_reminder import IntelligentReminderAgent

        # Initialize the intelligent reminder agent
        reminder_agent = IntelligentReminderAgent()

        # Check for version updates
        await reminder_agent.check_version_updates()

        logger.info("Version tracking job completed successfully")

    except Exception as e:
        logger.error(f"Version tracking job failed: {e}", exc_info=True)


async def weekly_insights_job():
    """
    Scheduled job: generate weekly insights report every Monday at 09:00.
    Requirements: 7.2, 7.4
    """
    logger.info("Starting weekly insights report generation job...")
    try:
        from app.qa_agent.weekly_insights.report_generator import InsightReportGenerator

        generator = InsightReportGenerator()
        report = await generator.generate(days=7)
        logger.info(
            "Weekly insights report generated successfully (id=%s, articles=%d)",
            report.get("id"),
            report.get("article_count", 0),
        )
    except Exception as exc:
        logger.error("Weekly insights job failed: %s", exc, exc_info=True)


async def preference_summary_job():
    """
    Daily job: condense DM conversations into preference summaries.
    Requirements: dm-conversation-memory §2
    """
    logger.info("Starting preference summary job...")
    try:
        from app.services.preference_summary_service import update_preference_summary

        supabase = SupabaseService()
        resp = supabase.client.table("dm_conversations").select("user_id").execute()
        user_ids = list({r["user_id"] for r in (resp.data or [])})

        updated = 0
        for user_id in user_ids:
            result = await update_preference_summary(user_id, supabase)
            if result:
                updated += 1

        logger.info("Preference summary job complete: %d summaries updated", updated)
    except Exception as exc:
        logger.error("Preference summary job failed: %s", exc, exc_info=True)


async def proactive_learning_job():
    """
    Scheduled job: run behavior analysis for all active users daily at 10:00.
    Triggers learning conversations where warranted.
    Requirements: 2.1
    """
    logger.info("Starting proactive learning behavior analysis job...")
    try:
        from app.qa_agent.proactive_learning.conversation_manager import ConversationManager
        from app.qa_agent.proactive_learning.learning_trigger import LearningTrigger
        from app.services.supabase_service import SupabaseService

        supabase = SupabaseService()
        # Fetch users who have learning enabled
        resp = (
            supabase.client.table("preference_model")
            .select("user_id")
            .eq("learning_enabled", True)
            .execute()
        )
        user_rows = resp.data or []
        trigger = LearningTrigger(supabase)
        mgr = ConversationManager(supabase)

        triggered = 0
        for row in user_rows:
            uid = row.get("user_id")
            if not uid:
                continue
            should, context = await trigger.should_trigger(uid)
            if should:
                await mgr.create_conversation(uid, context)
                await trigger.increment_conversation_count(uid)
                triggered += 1

        logger.info("Proactive learning job complete: %d conversations created", triggered)
    except Exception as exc:
        logger.error("Proactive learning job failed: %s", exc, exc_info=True)


def setup_scheduler():
    """
    Register jobs to the scheduler with configurable CRON expression.

    Reads configuration from environment variables:
    - SCHEDULER_CRON: CRON expression (default: "0 */6 * * *")
    - SCHEDULER_TIMEZONE: Timezone for schedule (default: from settings.timezone)

    Raises:
        ValueError: If CRON expression is invalid
        RuntimeError: If settings is not loaded

    Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
    """
    global _scheduler, _dynamic_scheduler

    logger.info("Setting up scheduler...")

    # Ensure settings is loaded
    if settings is None:
        error_msg = (
            "Settings not loaded. Ensure environment variables are properly configured. "
            "Check .env file and required variables."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info(f"Settings loaded successfully. Timezone: {settings.timezone}")

    # Initialize scheduler if not already done
    if _scheduler is None:
        logger.info("Initializing AsyncIOScheduler...")
        _scheduler = AsyncIOScheduler(timezone=settings.timezone)
        logger.info(f"Scheduler initialized: {_scheduler}")
    else:
        logger.info(f"Scheduler already initialized: {_scheduler}")

    # Initialize dynamic scheduler if not already done
    if _dynamic_scheduler is None:
        logger.info("Initializing DynamicScheduler...")
        from app.services.dynamic_scheduler import DynamicScheduler

        _dynamic_scheduler = DynamicScheduler(_scheduler)
        logger.info("DynamicScheduler initialized successfully")

    # Get CRON expression from settings
    cron_expression = settings.scheduler_cron

    # Get timezone (use scheduler_timezone if set, otherwise fall back to general timezone)
    scheduler_tz = settings.scheduler_timezone or settings.timezone

    # Validate CRON expression by attempting to create CronTrigger
    try:
        trigger = CronTrigger.from_crontab(cron_expression, timezone=scheduler_tz)
    except (ValueError, TypeError) as e:
        error_msg = f"Invalid CRON expression '{cron_expression}': {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e

    # Register the background job
    _scheduler.add_job(
        background_fetch_job,
        trigger=trigger,
        id="background_fetch",
        name="Background Article Fetch and Analysis",
        replace_existing=True,
    )

    # Register token blacklist cleanup job (runs every hour)
    _scheduler.add_job(
        cleanup_token_blacklist,
        trigger=CronTrigger(hour="*", timezone=scheduler_tz),  # Every hour
        id="token_blacklist_cleanup",
        name="Token Blacklist Cleanup",
        replace_existing=True,
    )

    # Register dynamic scheduler cleanup job (runs every 6 hours)
    _scheduler.add_job(
        _dynamic_scheduler.cleanup_expired_jobs,
        trigger=CronTrigger(hour="*/6", timezone=scheduler_tz),  # Every 6 hours
        id="dynamic_scheduler_cleanup",
        name="Dynamic Scheduler Cleanup",
        replace_existing=True,
    )

    # Register intelligent reminder version tracking job (runs every 6 hours)
    _scheduler.add_job(
        version_tracking_job,
        trigger=CronTrigger(hour="*/6", timezone=scheduler_tz),  # Every 6 hours
        id="version_tracking",
        name="Technology Version Tracking",
        replace_existing=True,
    )

    # Register weekly insights generation job (every Monday at 09:00)
    _scheduler.add_job(
        weekly_insights_job,
        trigger=CronTrigger(day_of_week="mon", hour=9, minute=0, timezone=scheduler_tz),
        id="weekly_insights",
        name="Weekly Insights Report Generation",
        replace_existing=True,
    )
    logger.info(
        f"Weekly insights job registered: Runs every Monday at 09:00 in timezone '{scheduler_tz}'"
    )

    # Register preference summary job (daily at 11:00)
    _scheduler.add_job(
        preference_summary_job,
        trigger=CronTrigger(hour=11, minute=0, timezone=scheduler_tz),
        id="preference_summary",
        name="Preference Summary Update",
        replace_existing=True,
    )
    logger.info("Preference summary job registered: Runs daily at 11:00")

    # Register proactive learning behavior analysis job (daily at 10:00)
    _scheduler.add_job(
        proactive_learning_job,
        trigger=CronTrigger(hour=10, minute=0, timezone=scheduler_tz),
        id="proactive_learning",
        name="Proactive Learning Behavior Analysis",
        replace_existing=True,
    )
    logger.info(
        f"Proactive learning job registered: Runs daily at 10:00 in timezone '{scheduler_tz}'"
    )

    # Register learning stagnation check job (daily at 10:00)
    from app.tasks.learning_stagnation import learning_stagnation_check_job

    _scheduler.add_job(
        learning_stagnation_check_job,
        trigger=CronTrigger(hour=10, minute=5, timezone=scheduler_tz),
        id="learning_stagnation_check",
        name="Learning Stagnation Check",
        replace_existing=True,
    )
    logger.info(
        f"Learning stagnation check job registered: Runs daily at 10:05 in timezone '{scheduler_tz}'"
    )

    # Log the configured schedule
    logger.info(
        f"Scheduler configured successfully: "
        f"CRON='{cron_expression}', "
        f"Timezone='{scheduler_tz}', "
        f"Job='background_fetch_job'"
    )
    logger.info(
        f"Token blacklist cleanup job registered: " f"Runs every hour in timezone '{scheduler_tz}'"
    )
    logger.info(
        f"Dynamic scheduler cleanup job registered: "
        f"Runs every 6 hours in timezone '{scheduler_tz}'"
    )

    # Note: User notification schedule restoration is done in the lifespan function
    # after the scheduler is started, since it requires async context

    # Verify scheduler was initialized
    if _scheduler is None:
        error_msg = "CRITICAL: Scheduler is still None after setup_scheduler()"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info(f"Scheduler setup completed successfully. Scheduler instance: {_scheduler}")
    return _scheduler


async def get_scheduler_health() -> dict:
    """
    Health check endpoint for monitoring scheduler status.

    Returns a dictionary containing:
    - last_execution_time: ISO timestamp of last execution (or None if never run)
    - articles_processed: Count of articles processed in last execution
    - failed_operations: Count of failed operations in last execution
    - total_operations: Total operations attempted in last execution
    - status_code: HTTP status code (200 for healthy, 503 for unhealthy)
    - is_healthy: Boolean indicating overall health
    - is_enabled: Boolean indicating if scheduler is enabled
    - issues: List of health issues detected

    Health criteria:
    - Disabled if ENABLE_SCHEDULER=false
    - Unhealthy (503) if scheduler has not run in the last 12 hours
    - Unhealthy (503) if last execution had more than 50% failures
    - Healthy (200) otherwise

    Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
    """
    from app.core.config import settings

    last_execution = _scheduler_health["last_execution_time"]
    articles_processed = _scheduler_health["last_articles_processed"]
    failed_operations = _scheduler_health["last_failed_operations"]
    total_operations = _scheduler_health["last_total_operations"]

    # Check if scheduler is enabled
    is_enabled = settings.enable_scheduler

    # Determine health status
    is_healthy = True
    issues = []
    status_code = 200

    if not is_enabled:
        # Scheduler is disabled - this is not an error in dev environment
        is_healthy = True  # Not unhealthy, just disabled
        status_code = 200
        issues.append("Scheduler is disabled (ENABLE_SCHEDULER=false)")
    else:
        # Check if scheduler has run recently (within last 12 hours)
        if last_execution is None:
            is_healthy = False
            status_code = 503
            issues.append("Scheduler has never executed")
        else:
            time_since_last_run = datetime.now(UTC) - last_execution
            if time_since_last_run > timedelta(hours=12):
                is_healthy = False
                status_code = 503
                issues.append(
                    f"Scheduler has not run in {time_since_last_run.total_seconds() / 3600:.1f} hours (threshold: 12 hours)"
                )

        # Check failure rate (only if there were operations)
        if total_operations > 0:
            failure_rate = failed_operations / total_operations
            if failure_rate > 0.5:
                is_healthy = False
                status_code = 503
            issues.append(f"Last execution had {failure_rate:.1%} failure rate (threshold: 50%)")

    return {
        "last_execution_time": last_execution.isoformat() if last_execution else None,
        "articles_processed": articles_processed,
        "failed_operations": failed_operations,
        "total_operations": total_operations,
        "status_code": status_code,
        "is_healthy": is_healthy,
        "is_enabled": is_enabled,
        "issues": issues,
    }
