"""Scheduled job functions for the APScheduler.

Each function is a standalone async job that can be registered with the scheduler.
They are separated here to keep scheduler.py focused on setup/health logic.
"""

import logging

from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


async def weekly_news_job() -> None:
    """Stub for backward compatibility with tests."""
    pass


async def version_tracking_job() -> None:
    """Check for technology version updates every 6 hours."""
    logger.info("Starting version tracking job...")
    try:
        from app.qa_agent.intelligent_reminder import IntelligentReminderAgent

        reminder_agent = IntelligentReminderAgent()
        await reminder_agent.check_version_updates()
        logger.info("Version tracking job completed successfully")
    except Exception as e:
        logger.error(f"Version tracking job failed: {e}", exc_info=True)


async def daily_digest_job() -> None:
    """Send daily article digest DM — only to users with frequency='daily' (09:00 every day)."""
    logger.info("Starting daily digest DM job...")
    try:
        from app.bot.client import bot
        from app.services.dm_notification_service import DMNotificationService
        from app.services.supabase_service import SupabaseService

        if not bot.is_ready():
            logger.warning("Bot is not ready, skipping daily digest")
            return

        supabase = SupabaseService()
        prefs = (
            supabase.client.table("user_notification_preferences")
            .select("user_id")
            .eq("frequency", "daily")
            .eq("dm_enabled", True)
            .execute()
        )
        user_ids = [row["user_id"] for row in (prefs.data or [])]
        if not user_ids:
            logger.info("No daily-frequency users to notify")
            return

        discord_ids = []
        for uid in user_ids:
            user = await supabase.get_user_by_id(uid)
            if user and user.get("discord_id"):
                discord_ids.append(user["discord_id"])

        service = DMNotificationService(bot)
        successful = failed = 0
        for discord_id in discord_ids:
            if await service.send_personalized_digest(discord_id):
                successful += 1
            else:
                failed += 1

        logger.info("Daily digest job completed: %d sent, %d failed", successful, failed)
    except Exception as exc:
        logger.error("Daily digest job failed: %s", exc, exc_info=True)


async def weekly_digest_job() -> None:
    """Send weekly article digest DM — only to users with frequency='weekly' (Monday 09:00)."""
    logger.info("Starting weekly digest DM job...")
    try:
        from app.bot.client import bot
        from app.services.dm_notification_service import DMNotificationService
        from app.services.supabase_service import SupabaseService

        if not bot.is_ready():
            logger.warning("Bot is not ready, skipping weekly digest")
            return

        supabase = SupabaseService()
        prefs = (
            supabase.client.table("user_notification_preferences")
            .select("user_id")
            .eq("frequency", "weekly")
            .eq("dm_enabled", True)
            .execute()
        )
        user_ids = [row["user_id"] for row in (prefs.data or [])]
        if not user_ids:
            logger.info("No weekly-frequency users to notify")
            return

        discord_ids = []
        for uid in user_ids:
            user = await supabase.get_user_by_id(uid)
            if user and user.get("discord_id"):
                discord_ids.append(user["discord_id"])

        service = DMNotificationService(bot)
        successful = failed = 0
        for discord_id in discord_ids:
            if await service.send_personalized_digest(discord_id):
                successful += 1
            else:
                failed += 1

        logger.info("Weekly digest job completed: %d sent, %d failed", successful, failed)
    except Exception as exc:
        logger.error("Weekly digest job failed: %s", exc, exc_info=True)


async def weekly_insights_job() -> None:
    """Generate weekly insights report every Monday at 09:00."""
    logger.info("Starting weekly insights report generation job...")
    try:
        from app.qa_agent.weekly_insights.report_generator import InsightReportGenerator

        supabase = SupabaseService()
        generator = InsightReportGenerator(supabase)

        resp = (
            supabase.client.table("reading_list")
            .select("user_id")
            .not_.is_("rating", "null")
            .execute()
        )
        user_ids = list({row["user_id"] for row in (resp.data or [])})

        if user_ids:
            for user_id in user_ids:
                try:
                    await generator.generate(days=7, user_id=user_id)
                    logger.info("Weekly insights generated for user %s", user_id)
                except Exception as exc:
                    logger.error("Weekly insights failed for user %s: %s", user_id, exc)
        else:
            report = await generator.generate(days=7)
            logger.info(
                "Weekly insights global report generated (id=%s, articles=%d)",
                report.get("id"),
                report.get("article_count", 0),
            )
    except Exception as exc:
        logger.error("Weekly insights job failed: %s", exc, exc_info=True)


async def preference_summary_job() -> None:
    """Condense DM conversations into preference summaries (daily at 11:00)."""
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


async def proactive_learning_job() -> None:
    """Run behavior analysis for all active users daily at 10:00."""
    logger.info("Starting proactive learning behavior analysis job...")
    try:
        from app.qa_agent.proactive_learning.conversation_manager import ConversationManager
        from app.qa_agent.proactive_learning.learning_trigger import LearningTrigger

        supabase = SupabaseService()
        resp = (
            supabase.client.table("preference_model")
            .select("user_id")
            .eq("learning_enabled", True)
            .execute()
        )
        trigger = LearningTrigger(supabase)
        mgr = ConversationManager(supabase)

        triggered = 0
        for row in resp.data or []:
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


async def intelligent_reminder_job() -> None:
    """Generate intelligent reminders for all active users (daily at 08:00)."""
    logger.info("Starting intelligent reminder generation job...")
    try:
        from app.services.intelligent_reminder_generator import IntelligentReminderGenerator

        supabase = SupabaseService()
        generator = IntelligentReminderGenerator()

        settings_result = (
            supabase.client.table("reminder_settings")
            .select("user_id, enabled")
            .eq("enabled", True)
            .execute()
        )
        if not settings_result.data:
            users_result = supabase.client.table("users").select("id").execute()
            user_ids = [str(u["id"]) for u in users_result.data]
        else:
            user_ids = [row["user_id"] for row in settings_result.data]

        total_reminders = 0
        successful_users = 0
        failed_users = 0

        for user_id in user_ids:
            try:
                reminders = await generator.generate_reminders_for_user(user_id)
                if reminders:
                    total_reminders += len(reminders)
                    successful_users += 1
            except Exception as e:
                failed_users += 1
                logger.error(f"Failed to generate reminders for user {user_id}: {e}")

        logger.info(
            f"Intelligent reminder job complete: {total_reminders} reminders for "
            f"{successful_users} users ({failed_users} failed)"
        )
    except Exception as exc:
        logger.error(f"Intelligent reminder job failed: {exc}", exc_info=True)


async def send_reminder_notifications_job() -> None:
    """Send pending reminders to users via Discord DM (every hour)."""
    logger.info("Starting reminder notification delivery job...")
    try:
        from app.services.reminder_notification_service import ReminderNotificationService

        supabase = SupabaseService()
        notification_service = ReminderNotificationService()

        pending_result = (
            supabase.client.table("reminder_log")
            .select("user_id")
            .eq("status", "pending")
            .execute()
        )
        if not pending_result.data:
            logger.info("No pending reminders to send")
            return

        user_ids = list({row["user_id"] for row in pending_result.data})
        total_sent = 0
        successful_users = 0
        failed_users = 0

        for user_id in user_ids:
            try:
                sent_count = await notification_service.send_pending_reminders(user_id)
                if sent_count > 0:
                    total_sent += sent_count
                    successful_users += 1
            except Exception as e:
                failed_users += 1
                logger.error(f"Failed to send reminders to user {user_id}: {e}")

        logger.info(
            f"Reminder notification job complete: {total_sent} reminders sent to "
            f"{successful_users} users ({failed_users} failed)"
        )
    except Exception as exc:
        logger.error(f"Reminder notification job failed: {exc}", exc_info=True)


async def monthly_digest_job() -> None:
    """Send monthly article digest DM — only to users with frequency='monthly' (1st of month 09:00)."""
    logger.info("Starting monthly digest DM job...")
    try:
        from app.bot.client import bot
        from app.services.dm_notification_service import DMNotificationService
        from app.services.supabase_service import SupabaseService

        if not bot.is_ready():
            logger.warning("Bot is not ready, skipping monthly digest")
            return

        supabase = SupabaseService()
        prefs = (
            supabase.client.table("user_notification_preferences")
            .select("user_id")
            .eq("frequency", "monthly")
            .eq("dm_enabled", True)
            .execute()
        )
        user_ids = [row["user_id"] for row in (prefs.data or [])]
        if not user_ids:
            logger.info("No monthly-frequency users to notify")
            return

        discord_ids = []
        for uid in user_ids:
            user = await supabase.get_user_by_id(uid)
            if user and user.get("discord_id"):
                discord_ids.append(user["discord_id"])

        service = DMNotificationService(bot)
        successful = failed = 0
        for discord_id in discord_ids:
            if await service.send_personalized_digest(discord_id):
                successful += 1
            else:
                failed += 1

        logger.info("Monthly digest job completed: %d sent, %d failed", successful, failed)
    except Exception as exc:
        logger.error("Monthly digest job failed: %s", exc, exc_info=True)
