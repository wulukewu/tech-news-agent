"""
Intelligent Reminder Agent - Main orchestrator class.
Coordinates all components to deliver context-aware, personalized reminders.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from ...services.llm_service import LLMService
from ...services.notification_service import NotificationService
from ...services.supabase_service import SupabaseService
from .behavior_analyzer import BehaviorAnalyzer
from .content_analyzer import ContentAnalyzer
from .context_generator import ContextGenerator
from .models import (
    ReminderContext,
    ReminderEffectivenessReport,
    ReminderStatus,
    ReminderType,
)
from .timing_engine import TimingEngine
from .version_tracker import VersionTracker

logger = logging.getLogger(__name__)


class IntelligentReminderAgent:
    """Main intelligent reminder agent that coordinates all components"""

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        supabase_service: Optional[SupabaseService] = None,
        notification_service: Optional[NotificationService] = None,
    ):
        self.llm_service = llm_service or LLMService()
        self.supabase_service = supabase_service or SupabaseService()
        self.notification_service = notification_service or NotificationService()

        # Initialize components
        self.content_analyzer = ContentAnalyzer(self.llm_service, self.supabase_service)
        self.version_tracker = VersionTracker(self.supabase_service)
        self.behavior_analyzer = BehaviorAnalyzer(self.supabase_service)
        self.timing_engine = TimingEngine(self.supabase_service, self.behavior_analyzer)
        self.context_generator = ContextGenerator(
            self.llm_service, self.supabase_service, self.content_analyzer, self.version_tracker
        )

    async def process_new_article(self, article_id: UUID) -> None:
        """Process a new article and generate related reminders"""
        try:
            logger.info(f"Processing new article {article_id} for intelligent reminders")

            # Analyze article relationships
            relationships = await self.content_analyzer.analyze_article_relationships(article_id)

            if relationships:
                # Find users who might be interested in related content
                for relationship in relationships:
                    await self._create_article_relation_reminders(relationship)

        except Exception as e:
            logger.error(f"Error processing new article {article_id}: {e}")

    async def check_version_updates(self) -> None:
        """Check for technology version updates and create reminders"""
        try:
            logger.info("Checking for technology version updates")

            # Get version updates
            updates = await self.version_tracker.check_version_updates()

            for update in updates:
                # Find interested users
                interested_users = await self.version_tracker.get_users_interested_in_technology(
                    update.technology_name
                )

                # Create reminders for interested users
                for user_id in interested_users:
                    await self._create_version_update_reminder(user_id, update)

            logger.info(f"Created version update reminders for {len(updates)} technologies")

        except Exception as e:
            logger.error(f"Error checking version updates: {e}")

    async def send_pending_reminders(self) -> None:
        """Send all pending reminders that are ready to be delivered"""
        try:
            logger.info("Processing pending reminders")

            # Get pending reminders
            pending_reminders = await self._get_pending_reminders()

            sent_count = 0
            for reminder in pending_reminders:
                try:
                    # Check if it's the right time to send
                    timing_decision = await self.timing_engine.should_send_reminder(
                        reminder["user_id"],
                        reminder["reminder_type"],
                        reminder.get("priority_score", 0.5),
                    )

                    if timing_decision.should_send:
                        await self._send_reminder(reminder)
                        sent_count += 1
                    elif timing_decision.delay_until:
                        # Update reminder to be sent later
                        await self._reschedule_reminder(reminder["id"], timing_decision.delay_until)

                except Exception as e:
                    logger.error(f"Error processing reminder {reminder.get('id')}: {e}")

            logger.info(f"Sent {sent_count} reminders")

        except Exception as e:
            logger.error(f"Error sending pending reminders: {e}")

    async def generate_effectiveness_report(self, user_id: UUID) -> ReminderEffectivenessReport:
        """Generate weekly effectiveness report for a user"""
        try:
            week_start = datetime.now() - timedelta(days=7)

            # Get reminder statistics
            query = """
            SELECT
                COUNT(*) as total_sent,
                COUNT(CASE WHEN status = 'clicked' THEN 1 END) as total_clicked,
                COUNT(CASE WHEN status = 'read' THEN 1 END) as total_read,
                COUNT(CASE WHEN status = 'dismissed' THEN 1 END) as total_dismissed,
                AVG(EXTRACT(EPOCH FROM response_time)) as avg_response_time,
                channel,
                EXTRACT(HOUR FROM sent_at) as hour
            FROM reminder_log
            WHERE user_id = $1 AND sent_at >= $2
            GROUP BY channel, EXTRACT(HOUR FROM sent_at)
            """

            result = await self.supabase_service.client.rpc(
                "execute_sql", {"query": query, "params": [str(user_id), week_start.isoformat()]}
            ).execute()

            # Process statistics
            total_sent = 0
            total_clicked = 0
            total_read = 0
            total_dismissed = 0
            response_times = []
            channel_performance = {}
            hour_performance = {}

            if result.data:
                for row in result.data:
                    total_sent += row["total_sent"]
                    total_clicked += row["total_clicked"]
                    total_read += row["total_read"]
                    total_dismissed += row["total_dismissed"]

                    if row["avg_response_time"]:
                        response_times.append(row["avg_response_time"])

                    # Track channel performance
                    channel = row["channel"]
                    if channel not in channel_performance:
                        channel_performance[channel] = {"sent": 0, "clicked": 0}
                    channel_performance[channel]["sent"] += row["total_sent"]
                    channel_performance[channel]["clicked"] += row["total_clicked"]

                    # Track hour performance
                    hour = int(row["hour"])
                    if hour not in hour_performance:
                        hour_performance[hour] = {"sent": 0, "clicked": 0}
                    hour_performance[hour]["sent"] += row["total_sent"]
                    hour_performance[hour]["clicked"] += row["total_clicked"]

            # Calculate rates
            click_rate = total_clicked / max(1, total_sent)
            read_rate = total_read / max(1, total_sent)
            avg_response_time = (
                sum(response_times) / max(1, len(response_times)) if response_times else None
            )

            # Find most effective channel and time
            most_effective_channel = None
            best_channel_rate = 0
            for channel, stats in channel_performance.items():
                rate = stats["clicked"] / max(1, stats["sent"])
                if rate > best_channel_rate:
                    best_channel_rate = rate
                    most_effective_channel = channel

            most_effective_time = None
            best_hour_rate = 0
            for hour, stats in hour_performance.items():
                rate = stats["clicked"] / max(1, stats["sent"])
                if rate > best_hour_rate:
                    best_hour_rate = rate
                    most_effective_time = hour

            # Generate recommendations
            recommendations = self._generate_recommendations(
                click_rate, read_rate, most_effective_channel, most_effective_time
            )

            return ReminderEffectivenessReport(
                user_id=user_id,
                week_start=week_start,
                total_sent=total_sent,
                total_clicked=total_clicked,
                total_read=total_read,
                total_dismissed=total_dismissed,
                click_rate=click_rate,
                read_rate=read_rate,
                average_response_time=avg_response_time,
                most_effective_channel=most_effective_channel,
                most_effective_time=most_effective_time,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Error generating effectiveness report for {user_id}: {e}")
            return ReminderEffectivenessReport(
                user_id=user_id,
                week_start=week_start,
                total_sent=0,
                total_clicked=0,
                total_read=0,
                total_dismissed=0,
                click_rate=0.0,
                read_rate=0.0,
                recommendations=["Unable to generate report due to error"],
            )

    async def track_reminder_interaction(self, reminder_id: UUID, interaction_type: str) -> None:
        """Track user interaction with a reminder"""
        try:
            # Update reminder status
            update_data = {"status": interaction_type, "updated_at": datetime.now().isoformat()}

            # Calculate response time if this is the first interaction
            if interaction_type in ["clicked", "read", "dismissed"]:
                reminder = await self._get_reminder_by_id(reminder_id)
                if reminder and reminder.get("status") == "sent":
                    sent_at = datetime.fromisoformat(reminder["sent_at"])
                    response_time = datetime.now() - sent_at
                    update_data["response_time"] = f"{response_time.total_seconds()} seconds"

            await self.supabase_service.client.table("reminder_log").update(update_data).eq(
                "id", str(reminder_id)
            ).execute()

            # Update user behavior patterns
            if interaction_type in ["clicked", "read"]:
                reminder = await self._get_reminder_by_id(reminder_id)
                if reminder:
                    await self.behavior_analyzer.track_reminder_response(
                        UUID(reminder["user_id"]),
                        reminder_id,
                        interaction_type,
                        int(response_time.total_seconds()) if "response_time" in locals() else None,
                    )

        except Exception as e:
            logger.error(f"Error tracking reminder interaction {reminder_id}: {e}")

    async def _create_article_relation_reminders(self, relationship) -> None:
        """Create reminders for article relationships"""
        try:
            # Find users who have read the source article
            users_who_read = await self._get_users_who_read_article(relationship.source_article_id)

            for user_id in users_who_read:
                # Generate reminder context
                context = await self.context_generator.generate_article_relation_reminder(
                    user_id, relationship.target_article_id, relationship.relationship_type.value
                )

                # Create reminder log entry
                await self._create_reminder_log(
                    user_id=user_id,
                    reminder_type=ReminderType.ARTICLE_RELATION,
                    content_id=relationship.target_article_id,
                    context=context,
                )

        except Exception as e:
            logger.error(f"Error creating article relation reminders: {e}")

    async def _create_version_update_reminder(self, user_id: UUID, tech_version) -> None:
        """Create reminder for version update"""
        try:
            # Generate reminder context
            context = await self.context_generator.generate_version_update_reminder(
                user_id, tech_version
            )

            # Create reminder log entry
            await self._create_reminder_log(
                user_id=user_id,
                reminder_type=ReminderType.VERSION_UPDATE,
                content_id=tech_version.id,
                context=context,
            )

        except Exception as e:
            logger.error(f"Error creating version update reminder: {e}")

    async def _create_reminder_log(
        self,
        user_id: UUID,
        reminder_type: ReminderType,
        content_id: Optional[UUID],
        context: ReminderContext,
    ) -> UUID:
        """Create a reminder log entry"""
        try:
            reminder_data = {
                "user_id": str(user_id),
                "reminder_type": reminder_type.value,
                "content_id": str(content_id) if content_id else None,
                "reminder_context": context.dict(),
                "sent_at": datetime.now().isoformat(),
                "channel": "discord",  # Default channel
                "status": "pending",
            }

            result = (
                await self.supabase_service.client.table("reminder_log")
                .insert(reminder_data)
                .execute()
            )

            if result.data:
                return UUID(result.data[0]["id"])

            raise Exception("Failed to create reminder log")

        except Exception as e:
            logger.error(f"Error creating reminder log: {e}")
            raise

    async def _get_pending_reminders(self) -> List[Dict[str, Any]]:
        """Get all pending reminders ready to be sent"""
        try:
            result = (
                await self.supabase_service.client.table("reminder_log")
                .select("*")
                .eq("status", "pending")
                .order("sent_at")
                .execute()
            )

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting pending reminders: {e}")
            return []

    async def _send_reminder(self, reminder: Dict[str, Any]) -> None:
        """Send a reminder to the user"""
        try:
            user_id = UUID(reminder["user_id"])
            context = ReminderContext(**reminder["reminder_context"])

            # Format reminder content
            from .context_generator import ContentFormatter

            text_content = ContentFormatter.format_to_text(context)
            html_content = ContentFormatter.format_to_html(context)

            # Send via notification service
            success = await self.notification_service.send_discord_dm(
                user_id=user_id, message=text_content
            )

            # Update reminder status
            status = ReminderStatus.DELIVERED if success else ReminderStatus.FAILED
            await self.supabase_service.client.table("reminder_log").update(
                {"status": status.value, "sent_at": datetime.now().isoformat()}
            ).eq("id", reminder["id"]).execute()

        except Exception as e:
            logger.error(f"Error sending reminder {reminder.get('id')}: {e}")
            # Mark as failed
            await self.supabase_service.client.table("reminder_log").update(
                {"status": ReminderStatus.FAILED.value}
            ).eq("id", reminder["id"]).execute()

    async def _reschedule_reminder(self, reminder_id: str, new_time: datetime) -> None:
        """Reschedule a reminder for later delivery"""
        try:
            await self.supabase_service.client.table("reminder_log").update(
                {"sent_at": new_time.isoformat()}
            ).eq("id", reminder_id).execute()
        except Exception as e:
            logger.error(f"Error rescheduling reminder {reminder_id}: {e}")

    async def _get_users_who_read_article(self, article_id: UUID) -> List[UUID]:
        """Get users who have read a specific article"""
        try:
            result = (
                await self.supabase_service.client.table("reading_list")
                .select("user_id")
                .eq("article_id", str(article_id))
                .eq("status", "read")
                .execute()
            )

            return [UUID(row["user_id"]) for row in (result.data or [])]

        except Exception as e:
            logger.error(f"Error getting users who read article {article_id}: {e}")
            return []

    async def _get_reminder_by_id(self, reminder_id: UUID) -> Optional[Dict[str, Any]]:
        """Get reminder by ID"""
        try:
            result = (
                await self.supabase_service.client.table("reminder_log")
                .select("*")
                .eq("id", str(reminder_id))
                .execute()
            )

            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error getting reminder {reminder_id}: {e}")
            return None

    def _generate_recommendations(
        self,
        click_rate: float,
        read_rate: float,
        best_channel: Optional[str],
        best_time: Optional[int],
    ) -> List[str]:
        """Generate recommendations based on effectiveness metrics"""
        recommendations = []

        if click_rate < 0.2:
            recommendations.append(
                "Consider reducing reminder frequency or improving content relevance"
            )

        if read_rate < 0.1:
            recommendations.append("Focus on shorter, more digestible content")

        if best_channel:
            recommendations.append(
                f"Continue using {best_channel} as your primary reminder channel"
            )

        if best_time is not None:
            recommendations.append(f"Optimal reminder time appears to be around {best_time}:00")

        if not recommendations:
            recommendations.append(
                "Your reminder engagement is good! Keep up the current strategy."
            )

        return recommendations
