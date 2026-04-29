"""
Behavior Analyzer for the Intelligent Reminder Agent.
Analyzes user behavior patterns to optimize reminder timing.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from ...services.supabase_service import SupabaseService
from .models import PatternType, UserBehaviorPattern, UserProfile

logger = logging.getLogger(__name__)


class BehaviorAnalyzer:
    """Analyzes user behavior patterns for optimal reminder timing"""

    def __init__(self, supabase_service: Optional[SupabaseService] = None):
        self.supabase_service = supabase_service or SupabaseService()
        self.min_data_days = 7  # Minimum days of data before generating profile

    async def analyze_user_behavior(self, user_id: UUID) -> UserProfile:
        """Analyze user behavior and generate/update user profile"""
        try:
            # Check if we have enough data (7+ days)
            if not await self._has_sufficient_data(user_id):
                return await self._get_default_profile(user_id)

            # Analyze different behavior patterns
            reading_times = await self._analyze_reading_times(user_id)
            active_hours = await self._analyze_active_hours(user_id)
            response_rates = await self._analyze_response_rates(user_id)

            # Store patterns in database
            await self._store_behavior_patterns(
                user_id,
                {
                    PatternType.READING_TIME: reading_times,
                    PatternType.ACTIVE_HOURS: active_hours,
                    PatternType.RESPONSE_RATE: response_rates,
                },
            )

            # Generate user profile
            profile = UserProfile(
                user_id=user_id,
                active_hours=active_hours.get("peak_hours", []),
                preferred_reading_time=reading_times.get("average_duration", 15),
                response_rate_by_type=response_rates.get("by_type", {}),
                ignored_reminder_count=response_rates.get("ignored_count", 0),
                last_reminder_sent=await self._get_last_reminder_time(user_id),
                learning_velocity=self._calculate_learning_velocity(reading_times),
                technical_interests=await self._extract_technical_interests(user_id),
            )

            return profile

        except Exception as e:
            logger.error(f"Error analyzing user behavior for {user_id}: {e}")
            return await self._get_default_profile(user_id)

    async def update_daily_patterns(self, user_id: UUID) -> None:
        """Update user behavior patterns daily"""
        try:
            profile = await self.analyze_user_behavior(user_id)
            logger.info(f"Updated behavior patterns for user {user_id}")
        except Exception as e:
            logger.error(f"Error updating daily patterns for {user_id}: {e}")

    async def track_reading_activity(
        self, user_id: UUID, article_id: UUID, duration_seconds: int
    ) -> None:
        """Track a reading activity for behavior analysis"""
        try:
            activity_data = {
                "user_id": str(user_id),
                "article_id": str(article_id),
                "duration_seconds": duration_seconds,
                "timestamp": datetime.now().isoformat(),
                "hour_of_day": datetime.now().hour,
                "day_of_week": datetime.now().weekday(),
            }

            # Store in a tracking table (you may need to create this)
            await self.supabase_service.client.table("user_reading_activity").insert(
                activity_data
            ).execute()

        except Exception as e:
            logger.error(f"Error tracking reading activity: {e}")

    async def track_reminder_response(
        self,
        user_id: UUID,
        reminder_id: UUID,
        response_type: str,
        response_time_seconds: Optional[int] = None,
    ) -> None:
        """Track user response to a reminder"""
        try:
            # Update reminder log with response
            update_data = {"status": response_type, "updated_at": datetime.now().isoformat()}

            if response_time_seconds:
                update_data["response_time"] = f"{response_time_seconds} seconds"

            await self.supabase_service.client.table("reminder_log").update(update_data).eq(
                "id", str(reminder_id)
            ).execute()

        except Exception as e:
            logger.error(f"Error tracking reminder response: {e}")

    async def get_optimal_reminder_hours(self, user_id: UUID) -> List[int]:
        """Get optimal hours for sending reminders to user"""
        try:
            patterns = await self._get_behavior_patterns(user_id, PatternType.ACTIVE_HOURS)
            if patterns and patterns.pattern_data:
                return patterns.pattern_data.get(
                    "peak_hours", [9, 14, 19]
                )  # Default to 9am, 2pm, 7pm

            return [9, 14, 19]  # Default hours

        except Exception as e:
            logger.error(f"Error getting optimal hours for {user_id}: {e}")
            return [9, 14, 19]

    async def should_adjust_strategy(self, user_id: UUID) -> bool:
        """Check if reminder strategy should be adjusted based on recent performance"""
        try:
            # Get recent reminder performance (last 7 days)
            seven_days_ago = datetime.now() - timedelta(days=7)

            query = """
            SELECT COUNT(*) as total_sent,
                   COUNT(CASE WHEN status IN ('clicked', 'read') THEN 1 END) as successful,
                   COUNT(CASE WHEN status = 'dismissed' THEN 1 END) as dismissed
            FROM reminder_log
            WHERE user_id = $1 AND sent_at >= $2
            """

            result = await self.supabase_service.client.rpc(
                "execute_sql",
                {"query": query, "params": [str(user_id), seven_days_ago.isoformat()]},
            ).execute()

            if result.data and result.data[0]:
                stats = result.data[0]
                total_sent = stats.get("total_sent", 0)
                successful = stats.get("successful", 0)
                dismissed = stats.get("dismissed", 0)

                if total_sent > 0:
                    success_rate = successful / total_sent
                    dismiss_rate = dismissed / total_sent

                    # Adjust if success rate < 20% or dismiss rate > 60%
                    return success_rate < 0.2 or dismiss_rate > 0.6

            return False

        except Exception as e:
            logger.error(f"Error checking strategy adjustment for {user_id}: {e}")
            return False

    async def _has_sufficient_data(self, user_id: UUID) -> bool:
        """Check if user has sufficient data for analysis (7+ days)"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.min_data_days)

            # Check reading list activity
            result = (
                await self.supabase_service.client.table("reading_list")
                .select("id")
                .eq("user_id", str(user_id))
                .gte("created_at", cutoff_date.isoformat())
                .limit(1)
                .execute()
            )

            return bool(result.data)

        except Exception as e:
            logger.error(f"Error checking data sufficiency for {user_id}: {e}")
            return False

    async def _analyze_reading_times(self, user_id: UUID) -> Dict[str, Any]:
        """Analyze user's reading time patterns"""
        try:
            # Get reading activity from reading list updates
            query = """
            SELECT
                EXTRACT(HOUR FROM updated_at) as hour,
                COUNT(*) as activity_count,
                AVG(CASE WHEN status = 'read' THEN 1 ELSE 0 END) as completion_rate
            FROM reading_list
            WHERE user_id = $1
              AND updated_at >= $2
            GROUP BY EXTRACT(HOUR FROM updated_at)
            ORDER BY activity_count DESC
            """

            thirty_days_ago = datetime.now() - timedelta(days=30)
            result = await self.supabase_service.client.rpc(
                "execute_sql",
                {"query": query, "params": [str(user_id), thirty_days_ago.isoformat()]},
            ).execute()

            if result.data:
                total_activities = sum(row["activity_count"] for row in result.data)
                avg_completion_rate = sum(row["completion_rate"] for row in result.data) / len(
                    result.data
                )

                return {
                    "total_activities": total_activities,
                    "average_completion_rate": avg_completion_rate,
                    "average_duration": 15,  # Default estimate
                    "confidence": min(
                        1.0, total_activities / 50.0
                    ),  # Higher confidence with more data
                }

            return {"confidence": 0.0}

        except Exception as e:
            logger.error(f"Error analyzing reading times for {user_id}: {e}")
            return {"confidence": 0.0}

    async def _analyze_active_hours(self, user_id: UUID) -> Dict[str, Any]:
        """Analyze user's active hours"""
        try:
            query = """
            SELECT
                EXTRACT(HOUR FROM updated_at) as hour,
                COUNT(*) as activity_count
            FROM reading_list
            WHERE user_id = $1
              AND updated_at >= $2
            GROUP BY EXTRACT(HOUR FROM updated_at)
            ORDER BY activity_count DESC
            """

            thirty_days_ago = datetime.now() - timedelta(days=30)
            result = await self.supabase_service.client.rpc(
                "execute_sql",
                {"query": query, "params": [str(user_id), thirty_days_ago.isoformat()]},
            ).execute()

            if result.data:
                # Get top 3 most active hours
                peak_hours = [int(row["hour"]) for row in result.data[:3]]
                total_activities = sum(row["activity_count"] for row in result.data)

                # Calculate activity distribution
                hourly_distribution = {
                    int(row["hour"]): row["activity_count"] for row in result.data
                }

                return {
                    "peak_hours": peak_hours,
                    "hourly_distribution": hourly_distribution,
                    "total_activities": total_activities,
                    "confidence": min(1.0, total_activities / 30.0),
                }

            return {"peak_hours": [9, 14, 19], "confidence": 0.0}  # Default hours

        except Exception as e:
            logger.error(f"Error analyzing active hours for {user_id}: {e}")
            return {"peak_hours": [9, 14, 19], "confidence": 0.0}

    async def _analyze_response_rates(self, user_id: UUID) -> Dict[str, Any]:
        """Analyze user's response rates to different reminder types"""
        try:
            query = """
            SELECT
                reminder_type,
                COUNT(*) as total_sent,
                COUNT(CASE WHEN status IN ('clicked', 'read') THEN 1 END) as successful_responses,
                COUNT(CASE WHEN status = 'dismissed' THEN 1 END) as dismissed,
                AVG(EXTRACT(EPOCH FROM response_time)) as avg_response_time
            FROM reminder_log
            WHERE user_id = $1
              AND sent_at >= $2
            GROUP BY reminder_type
            """

            thirty_days_ago = datetime.now() - timedelta(days=30)
            result = await self.supabase_service.client.rpc(
                "execute_sql",
                {"query": query, "params": [str(user_id), thirty_days_ago.isoformat()]},
            ).execute()

            response_rates = {}
            total_ignored = 0

            if result.data:
                for row in result.data:
                    reminder_type = row["reminder_type"]
                    total_sent = row["total_sent"]
                    successful = row["successful_responses"]
                    dismissed = row["dismissed"]

                    if total_sent > 0:
                        response_rates[reminder_type] = successful / total_sent
                        total_ignored += dismissed

            return {
                "by_type": response_rates,
                "ignored_count": total_ignored,
                "confidence": min(1.0, sum(response_rates.values()) / max(1, len(response_rates))),
            }

        except Exception as e:
            logger.error(f"Error analyzing response rates for {user_id}: {e}")
            return {"by_type": {}, "ignored_count": 0, "confidence": 0.0}

    async def _store_behavior_patterns(
        self, user_id: UUID, patterns: Dict[PatternType, Dict[str, Any]]
    ) -> None:
        """Store behavior patterns in database"""
        try:
            for pattern_type, pattern_data in patterns.items():
                data = {
                    "user_id": str(user_id),
                    "pattern_type": pattern_type.value,
                    "pattern_data": pattern_data,
                    "confidence_level": pattern_data.get("confidence", 0.5),
                    "last_updated": datetime.now().isoformat(),
                }

                await self.supabase_service.client.table("user_behavior_patterns").upsert(
                    data
                ).execute()

        except Exception as e:
            logger.error(f"Error storing behavior patterns: {e}")

    async def _get_behavior_patterns(
        self, user_id: UUID, pattern_type: PatternType
    ) -> Optional[UserBehaviorPattern]:
        """Get specific behavior pattern for user"""
        try:
            result = (
                await self.supabase_service.client.table("user_behavior_patterns")
                .select("*")
                .eq("user_id", str(user_id))
                .eq("pattern_type", pattern_type.value)
                .execute()
            )

            if result.data:
                return UserBehaviorPattern(**result.data[0])

            return None

        except Exception as e:
            logger.error(f"Error getting behavior patterns: {e}")
            return None

    async def _get_last_reminder_time(self, user_id: UUID) -> Optional[datetime]:
        """Get timestamp of last reminder sent to user"""
        try:
            result = (
                await self.supabase_service.client.table("reminder_log")
                .select("sent_at")
                .eq("user_id", str(user_id))
                .order("sent_at", desc=True)
                .limit(1)
                .execute()
            )

            if result.data:
                return datetime.fromisoformat(result.data[0]["sent_at"])

            return None

        except Exception as e:
            logger.error(f"Error getting last reminder time: {e}")
            return None

    def _calculate_learning_velocity(self, reading_times: Dict[str, Any]) -> float:
        """Calculate user's learning velocity (0-1 scale)"""
        completion_rate = reading_times.get("average_completion_rate", 0.5)
        activity_level = min(1.0, reading_times.get("total_activities", 0) / 100.0)

        return (completion_rate + activity_level) / 2.0

    async def _extract_technical_interests(self, user_id: UUID) -> List[str]:
        """Extract user's technical interests from reading history"""
        try:
            query = """
            SELECT a.title, a.ai_summary
            FROM reading_list rl
            JOIN articles a ON a.id = rl.article_id
            WHERE rl.user_id = $1
              AND rl.rating >= 4
            ORDER BY rl.updated_at DESC
            LIMIT 20
            """

            result = await self.supabase_service.client.rpc(
                "execute_sql", {"query": query, "params": [str(user_id)]}
            ).execute()

            interests = []
            if result.data:
                # Simple keyword extraction from highly-rated articles
                common_tech_terms = [
                    "python",
                    "javascript",
                    "react",
                    "node",
                    "docker",
                    "kubernetes",
                    "aws",
                    "azure",
                    "gcp",
                    "machine learning",
                    "ai",
                    "blockchain",
                    "typescript",
                    "vue",
                    "angular",
                    "django",
                    "flask",
                    "fastapi",
                ]

                text_content = " ".join(
                    [
                        (row.get("title", "") + " " + row.get("ai_summary", "")).lower()
                        for row in result.data
                    ]
                )

                for term in common_tech_terms:
                    if term in text_content:
                        interests.append(term)

            return interests[:10]  # Limit to top 10 interests

        except Exception as e:
            logger.error(f"Error extracting technical interests: {e}")
            return []

    async def _get_default_profile(self, user_id: UUID) -> UserProfile:
        """Get default user profile for users with insufficient data"""
        return UserProfile(
            user_id=user_id,
            active_hours=[9, 14, 19],  # Default active hours
            preferred_reading_time=15,  # Default 15 minutes
            response_rate_by_type={},
            ignored_reminder_count=0,
            last_reminder_sent=None,
            learning_velocity=0.5,  # Default medium velocity
            technical_interests=[],
        )
