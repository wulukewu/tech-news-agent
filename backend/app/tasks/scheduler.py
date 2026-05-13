"""Scheduler setup, health tracking, and public API.

Job implementations live in app.tasks._jobs to keep this file focused on
scheduler lifecycle and configuration.
"""

import logging
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.services.llm_service import LLMService as LLMService  # noqa: F401 - re-export for tests
from app.services.notion_service import (
    NotionService as NotionService,
)

# noqa: F401 - re-export for tests
from app.services.rss_service import RSSService as RSSService  # noqa: F401 - re-export for tests
from app.services.supabase_service import SupabaseService
from app.tasks._jobs import (
    daily_digest_job,
    intelligent_reminder_job,
    preference_summary_job,
    proactive_learning_job,
    send_reminder_notifications_job,
    version_tracking_job,
    weekly_insights_job,
)

logger = logging.getLogger(__name__)

# Global scheduler instances (initialized lazily in setup_scheduler)
_scheduler: AsyncIOScheduler | None = None
_dynamic_scheduler = None

# Public alias kept for backward compatibility with tests
scheduler: AsyncIOScheduler = AsyncIOScheduler()

# Global health tracking
_scheduler_health = {
    "last_execution_time": None,
    "last_articles_processed": 0,
    "last_failed_operations": 0,
    "last_total_operations": 0,
}

# Track feed changes between executions (Requirement 16.5)
_last_feed_urls = set()

from app.tasks._fetch_job import background_fetch_job  # noqa: E402
from app.tasks._notify_jobs import cleanup_token_blacklist  # noqa: E402


def get_scheduler() -> AsyncIOScheduler | None:
    """Return the global scheduler instance."""
    return _scheduler


def get_dynamic_scheduler():
    """Return the global dynamic scheduler instance."""
    return _dynamic_scheduler


def __getattr__(name: str):
    """Dynamic attribute access for backward compatibility."""
    if name == "scheduler":
        return _scheduler
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def setup_scheduler():
    """
    Register all jobs to the APScheduler with configurable CRON expression.

    Reads configuration from environment variables:
    - SCHEDULER_CRON: CRON expression (default: "0 */6 * * *")
    - SCHEDULER_TIMEZONE: Timezone for schedule (default: from settings.timezone)

    Raises:
        ValueError: If CRON expression is invalid
        RuntimeError: If settings is not loaded
    """
    global _scheduler, _dynamic_scheduler

    logger.info("Setting up scheduler...")

    if settings is None:
        raise RuntimeError(
            "Settings not loaded. Ensure environment variables are properly configured."
        )

    logger.info(f"Settings loaded successfully. Timezone: {settings.timezone}")

    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone=settings.timezone)

    if _dynamic_scheduler is None:
        from app.services.dynamic_scheduler import DynamicScheduler

        _dynamic_scheduler = DynamicScheduler(_scheduler)

    cron_expression = settings.scheduler_cron
    scheduler_tz = settings.scheduler_timezone or settings.timezone

    try:
        trigger = CronTrigger.from_crontab(cron_expression, timezone=scheduler_tz)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid CRON expression '{cron_expression}': {e}") from e

    jobs = [
        (
            background_fetch_job,
            trigger,
            "background_fetch",
            "Background Article Fetch and Analysis",
        ),
        (
            cleanup_token_blacklist,
            CronTrigger(hour="*", timezone=scheduler_tz),
            "token_blacklist_cleanup",
            "Token Blacklist Cleanup",
        ),
        (
            _dynamic_scheduler.cleanup_expired_jobs,
            CronTrigger(hour="*/6", timezone=scheduler_tz),
            "dynamic_scheduler_cleanup",
            "Dynamic Scheduler Cleanup",
        ),
        (
            version_tracking_job,
            CronTrigger(hour="*/6", timezone=scheduler_tz),
            "version_tracking",
            "Technology Version Tracking",
        ),
        (
            daily_digest_job,
            CronTrigger(hour=9, minute=0, timezone=scheduler_tz),
            "daily_digest",
            "Daily Article Digest DM",
        ),
        (
            weekly_insights_job,
            CronTrigger(day_of_week="mon", hour=9, minute=0, timezone=scheduler_tz),
            "weekly_insights",
            "Weekly Insights Report Generation",
        ),
        (
            preference_summary_job,
            CronTrigger(hour=11, minute=0, timezone=scheduler_tz),
            "preference_summary",
            "Preference Summary Update",
        ),
        (
            proactive_learning_job,
            CronTrigger(hour=10, minute=0, timezone=scheduler_tz),
            "proactive_learning",
            "Proactive Learning Behavior Analysis",
        ),
        (
            intelligent_reminder_job,
            CronTrigger(hour=8, minute=0, timezone=scheduler_tz),
            "intelligent_reminders",
            "Intelligent Reminder Generation",
        ),
        (
            send_reminder_notifications_job,
            CronTrigger(hour="*", timezone=scheduler_tz),
            "reminder_notifications",
            "Reminder Notification Delivery",
        ),
    ]

    for func, job_trigger, job_id, name in jobs:
        _scheduler.add_job(func, trigger=job_trigger, id=job_id, name=name, replace_existing=True)

    from app.tasks.learning_stagnation import learning_stagnation_check_job

    _scheduler.add_job(
        learning_stagnation_check_job,
        trigger=CronTrigger(hour=10, minute=5, timezone=scheduler_tz),
        id="learning_stagnation_check",
        name="Learning Stagnation Check",
        replace_existing=True,
    )

    logger.info(
        f"Scheduler configured: CRON='{cron_expression}', Timezone='{scheduler_tz}', "
        f"{len(jobs) + 1} jobs registered"
    )
    return _scheduler


async def get_scheduler_health() -> dict:
    """
    Health check for the scheduler.

    Returns status including last execution time, article counts, failure rates,
    and next scheduled run. Returns 503 if stale (>12h) or high failure rate (>50%).
    """
    is_enabled = getattr(settings, "enable_scheduler", True)

    last_execution = _scheduler_health["last_execution_time"]
    articles_processed = _scheduler_health["last_articles_processed"]
    failed_operations = _scheduler_health["last_failed_operations"]
    total_operations = _scheduler_health["last_total_operations"]

    if last_execution is None:
        try:
            supabase = SupabaseService()
            result = (
                supabase.client.table("articles")
                .select("created_at")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if result.data:
                last_execution = datetime.fromisoformat(
                    result.data[0]["created_at"].replace("Z", "+00:00")
                )
        except Exception as e:
            logger.warning(f"Failed to check database for last execution: {e}")

    is_running = _scheduler is not None and _scheduler.running
    next_execution_time = None
    if _scheduler and is_running:
        job = _scheduler.get_job("background_fetch")
        if job and job.next_run_time:
            next_execution_time = job.next_run_time.isoformat()

    is_healthy = True
    issues = []
    status_code = 200

    if not is_enabled:
        issues.append(
            {"type": "disabled", "message": "Scheduler is disabled (ENABLE_SCHEDULER=false)"}
        )
    else:
        if last_execution is None:
            if is_running and next_execution_time:
                issues.append(
                    {
                        "type": "waiting",
                        "message": "Scheduler is active and waiting for first execution",
                    }
                )
            else:
                is_healthy = False
                status_code = 503
                issues.append({"type": "never_executed", "message": "Scheduler has never executed"})
        else:
            time_since_last_run = datetime.now(UTC) - last_execution
            if time_since_last_run > timedelta(hours=12):
                is_healthy = False
                status_code = 503
                hours_since = int(time_since_last_run.total_seconds() / 3600)
                issues.append(
                    {
                        "type": "stale",
                        "hours": hours_since,
                        "threshold": 12,
                        "message": f"Scheduler has not run in {hours_since} hours (threshold: 12 hours)",
                    }
                )

        if total_operations > 0:
            failure_rate = failed_operations / total_operations
            if failure_rate > 0.5:
                is_healthy = False
                status_code = 503
                issues.append(
                    {
                        "type": "high_failure_rate",
                        "rate": int(failure_rate * 100),
                        "threshold": 50,
                        "message": f"Last execution had {int(failure_rate * 100)}% failure rate (threshold: 50%)",
                    }
                )

    return {
        "last_execution_time": last_execution.isoformat() if last_execution else None,
        "articles_processed": articles_processed,
        "failed_operations": failed_operations,
        "total_operations": total_operations,
        "status_code": status_code,
        "is_healthy": is_healthy,
        "is_enabled": is_enabled,
        "is_running": is_running,
        "next_execution_time": next_execution_time,
        "issues": issues,
    }
