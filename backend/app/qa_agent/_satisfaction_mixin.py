"""Satisfaction analysis mixin for UserProfileManager."""
import logging
from typing import Any, Dict
from uuid import UUID

logger = logging.getLogger(__name__)


class SatisfactionMixin:
    async def calculate_implicit_satisfaction(
        self,
        read_duration_seconds: int,
        completion_rate: float,
        expected_read_time: int,
    ) -> float:
        """
        Calculate implicit satisfaction score from reading behavior.

        Uses reading duration and completion rate to infer satisfaction.

        Args:
            read_duration_seconds: Actual time spent reading
            completion_rate: Percentage of article read (0.0-1.0)
            expected_read_time: Expected reading time for the article

        Returns:
            Implicit satisfaction score (0.0-1.0)

        Validates: Requirement 8.5 - Track satisfaction feedback
        """
        # Base score from completion rate
        completion_score = completion_rate

        # Adjust based on reading time vs expected time
        if expected_read_time > 0:
            time_ratio = read_duration_seconds / expected_read_time
            # Ideal ratio is 0.8-1.2 (reading at reasonable pace)
            if 0.8 <= time_ratio <= 1.2:
                time_score = 1.0
            elif time_ratio < 0.8:
                # Too fast - might be skimming
                time_score = max(0.5, time_ratio / 0.8)
            else:
                # Too slow - might be struggling or distracted
                time_score = max(0.5, 1.2 / time_ratio)
        else:
            time_score = 0.7  # Neutral score if no expected time

        # Combine scores
        implicit_satisfaction = (completion_score * 0.6) + (time_score * 0.4)

        return min(1.0, max(0.0, implicit_satisfaction))

    async def analyze_satisfaction_trends(
        self, user_id: UUID, days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze satisfaction trends over time for optimization.

        Args:
            user_id: User identifier
            days_back: Number of days to analyze

        Returns:
            Dictionary containing satisfaction trend analysis

        Validates: Requirement 8.5 - Optimize based on satisfaction feedback
        """
        try:
            async with get_db_connection() as conn:
                cutoff_date = datetime.utcnow() - timedelta(days=days_back)

                # Get satisfaction scores over time
                rows = await conn.fetch(
                    """
                    SELECT
                        DATE(read_at) as read_date,
                        AVG(satisfaction_score) as avg_satisfaction,
                        COUNT(*) as article_count
                    FROM reading_history
                    WHERE user_id = $1
                      AND read_at >= $2
                      AND satisfaction_score IS NOT NULL
                    GROUP BY DATE(read_at)
                    ORDER BY read_date DESC
                    """,
                    user_id,
                    cutoff_date,
                )

                if not rows:
                    return {
                        "trend": "insufficient_data",
                        "avg_satisfaction": 0.5,
                        "satisfaction_improving": False,
                        "recommendations": [],
                    }

                # Calculate trend
                satisfaction_scores = [float(row["avg_satisfaction"]) for row in rows]
                avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)

                # Simple trend detection (compare first half vs second half)
                mid_point = len(satisfaction_scores) // 2
                if mid_point > 0:
                    recent_avg = sum(satisfaction_scores[:mid_point]) / mid_point
                    older_avg = sum(satisfaction_scores[mid_point:]) / (
                        len(satisfaction_scores) - mid_point
                    )
                    satisfaction_improving = recent_avg > older_avg
                    trend = "improving" if satisfaction_improving else "declining"
                else:
                    satisfaction_improving = False
                    trend = "stable"

                # Generate recommendations based on trends
                recommendations = []
                if avg_satisfaction < 0.5:
                    recommendations.append(
                        "Consider adjusting content recommendations to better match user interests"
                    )
                    recommendations.append("Focus on more practical, actionable content")
                elif avg_satisfaction > 0.7:
                    recommendations.append(
                        "User is highly satisfied - maintain current recommendation strategy"
                    )
                    recommendations.append("Consider introducing more advanced or diverse content")

                if not satisfaction_improving and len(satisfaction_scores) > 2:
                    recommendations.append(
                        "Satisfaction declining - review recent recommendations for quality"
                    )

                return {
                    "trend": trend,
                    "avg_satisfaction": avg_satisfaction,
                    "satisfaction_improving": satisfaction_improving,
                    "data_points": len(satisfaction_scores),
                    "recommendations": recommendations,
                }

        except Exception as e:
            logger.error(f"Failed to analyze satisfaction trends: {e}", exc_info=True)
            raise UserProfileManagerError(
                f"Failed to analyze satisfaction trends: {e}", original_error=e
            )

    # ------------------------------------------------------------------
    # Profile Management
    # ------------------------------------------------------------------
