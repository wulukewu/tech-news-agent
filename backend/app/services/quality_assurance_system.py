import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


@dataclass
class ContentFeedback:
    user_id: str
    article_id: str
    educational_value_rating: int
    difficulty_accuracy: bool
    content_type_accuracy: bool
    completion_status: str
    time_spent_minutes: int
    feedback_text: Optional[str]


@dataclass
class QualityMetrics:
    average_rating: float
    completion_rate: float
    user_engagement_score: float
    classification_accuracy: float
    recommendation_relevance: float


class QualityAssuranceSystem:
    """System for monitoring and improving content quality."""

    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service

    async def collect_user_feedback(self, feedback: ContentFeedback) -> bool:
        """Collect and store user feedback on content quality."""
        try:
            feedback_data = {
                "user_id": feedback.user_id,
                "article_id": feedback.article_id,
                "educational_value_rating": feedback.educational_value_rating,
                "difficulty_accuracy": feedback.difficulty_accuracy,
                "content_type_accuracy": feedback.content_type_accuracy,
                "completion_status": feedback.completion_status,
                "time_spent_minutes": feedback.time_spent_minutes,
                "feedback_text": feedback.feedback_text,
            }

            self.supabase.client.table("content_feedback").insert(feedback_data).execute()

            # Update quality metrics asynchronously
            await self._update_article_quality_metrics(feedback.article_id)

            return True

        except Exception as e:
            logger.error(f"Failed to collect feedback: {e}")
            return False

    async def calculate_content_quality_score(self, article_id: str) -> float:
        """Calculate overall quality score for an article."""
        try:
            # Get all feedback for this article
            result = (
                self.supabase.client.table("content_feedback")
                .select("*")
                .eq("article_id", article_id)
                .execute()
            )

            if not result.data:
                return 0.5  # Default score for articles without feedback

            feedback_items = result.data

            # Calculate average rating
            ratings = [
                f["educational_value_rating"]
                for f in feedback_items
                if f["educational_value_rating"]
            ]
            avg_rating = sum(ratings) / len(ratings) if ratings else 3.0

            # Calculate completion rate
            completed = len([f for f in feedback_items if f["completion_status"] == "completed"])
            completion_rate = completed / len(feedback_items) if feedback_items else 0.5

            # Calculate accuracy scores
            difficulty_accurate = len(
                [f for f in feedback_items if f["difficulty_accuracy"] is True]
            )
            type_accurate = len([f for f in feedback_items if f["content_type_accuracy"] is True])

            accuracy_rate = (
                (difficulty_accurate + type_accurate) / (2 * len(feedback_items))
                if feedback_items
                else 0.5
            )

            # Weighted quality score
            quality_score = (
                (avg_rating / 5.0) * 0.4
                + completion_rate * 0.3  # Rating weight: 40%
                + accuracy_rate * 0.3  # Completion weight: 30%  # Accuracy weight: 30%
            )

            return min(1.0, max(0.0, quality_score))

        except Exception as e:
            logger.error(f"Failed to calculate quality score for article {article_id}: {e}")
            return 0.5

    async def get_source_quality_metrics(self, feed_id: str) -> QualityMetrics:
        """Get quality metrics for a specific RSS source."""
        try:
            # Get all articles from this feed
            articles_result = (
                self.supabase.client.table("articles").select("id").eq("feed_id", feed_id).execute()
            )

            if not articles_result.data:
                return QualityMetrics(0.0, 0.0, 0.0, 0.0, 0.0)

            article_ids = [a["id"] for a in articles_result.data]

            # Get feedback for all articles from this feed
            feedback_result = (
                self.supabase.client.table("content_feedback")
                .select("*")
                .in_("article_id", article_ids)
                .execute()
            )

            if not feedback_result.data:
                return QualityMetrics(0.0, 0.0, 0.0, 0.0, 0.0)

            feedback_items = feedback_result.data

            # Calculate metrics
            ratings = [
                f["educational_value_rating"]
                for f in feedback_items
                if f["educational_value_rating"]
            ]
            average_rating = sum(ratings) / len(ratings) if ratings else 0.0

            completed = len([f for f in feedback_items if f["completion_status"] == "completed"])
            completion_rate = completed / len(feedback_items) if feedback_items else 0.0

            total_time = sum(
                [f["time_spent_minutes"] for f in feedback_items if f["time_spent_minutes"]]
            )
            avg_time = total_time / len(feedback_items) if feedback_items else 0.0
            user_engagement_score = min(1.0, avg_time / 30.0)  # Normalize to 30 minutes

            difficulty_accurate = len(
                [f for f in feedback_items if f["difficulty_accuracy"] is True]
            )
            type_accurate = len([f for f in feedback_items if f["content_type_accuracy"] is True])
            classification_accuracy = (
                (difficulty_accurate + type_accurate) / (2 * len(feedback_items))
                if feedback_items
                else 0.0
            )

            # Recommendation relevance (based on high ratings)
            high_ratings = len(
                [
                    f
                    for f in feedback_items
                    if f["educational_value_rating"] and f["educational_value_rating"] >= 4
                ]
            )
            recommendation_relevance = high_ratings / len(feedback_items) if feedback_items else 0.0

            return QualityMetrics(
                average_rating=average_rating,
                completion_rate=completion_rate,
                user_engagement_score=user_engagement_score,
                classification_accuracy=classification_accuracy,
                recommendation_relevance=recommendation_relevance,
            )

        except Exception as e:
            logger.error(f"Failed to get quality metrics for feed {feed_id}: {e}")
            return QualityMetrics(0.0, 0.0, 0.0, 0.0, 0.0)

    async def identify_low_quality_sources(self, threshold: float = 0.6) -> List[Dict]:
        """Identify RSS sources with consistently low quality scores."""
        try:
            # Get all feeds with their quality metrics
            feeds_result = self.supabase.client.table("feeds").select("id, name, url").execute()

            low_quality_sources = []

            for feed in feeds_result.data:
                metrics = await self.get_source_quality_metrics(feed["id"])

                # Calculate overall quality score
                overall_score = (
                    metrics.average_rating / 5.0 * 0.3
                    + metrics.completion_rate * 0.25
                    + metrics.user_engagement_score * 0.2
                    + metrics.classification_accuracy * 0.15
                    + metrics.recommendation_relevance * 0.1
                )

                if overall_score < threshold:
                    low_quality_sources.append(
                        {
                            "feed_id": feed["id"],
                            "feed_name": feed["name"],
                            "feed_url": feed["url"],
                            "quality_score": overall_score,
                            "metrics": metrics,
                        }
                    )

            return sorted(low_quality_sources, key=lambda x: x["quality_score"])

        except Exception as e:
            logger.error(f"Failed to identify low quality sources: {e}")
            return []

    async def _update_article_quality_metrics(self, article_id: str):
        """Update cached quality metrics for an article."""
        try:
            quality_score = await self.calculate_content_quality_score(article_id)

            # Get article's feed_id
            article_result = (
                self.supabase.client.table("articles")
                .select("feed_id")
                .eq("id", article_id)
                .execute()
            )

            if not article_result.data:
                return

            feed_id = article_result.data[0]["feed_id"]

            # Get feedback stats
            feedback_result = (
                self.supabase.client.table("content_feedback")
                .select("*")
                .eq("article_id", article_id)
                .execute()
            )

            feedback_items = feedback_result.data
            completed = len([f for f in feedback_items if f["completion_status"] == "completed"])
            completion_rate = completed / len(feedback_items) if feedback_items else 0.0

            total_time = sum(
                [f["time_spent_minutes"] for f in feedback_items if f["time_spent_minutes"]]
            )
            avg_time = total_time / len(feedback_items) if feedback_items else 0.0
            engagement_score = min(1.0, avg_time / 30.0)

            # Upsert quality metrics
            metrics_data = {
                "article_id": article_id,
                "feed_id": feed_id,
                "average_rating": quality_score * 5.0,  # Convert back to 1-5 scale
                "completion_rate": completion_rate,
                "user_engagement_score": engagement_score,
                "recommendation_success_rate": quality_score,
                "total_feedback_count": len(feedback_items),
                "last_calculated": "NOW()",
            }

            self.supabase.client.table("content_quality_metrics").upsert(metrics_data).execute()

        except Exception as e:
            logger.error(f"Failed to update quality metrics for article {article_id}: {e}")

    async def get_quality_overview(self) -> Dict:
        """Get overall system quality metrics."""
        try:
            # Get total articles with classifications
            classified_result = (
                self.supabase.client.table("article_classifications")
                .select("content_type, learning_value_score")
                .execute()
            )

            if not classified_result.data:
                return {"error": "No classified articles found"}

            classifications = classified_result.data

            # Calculate content type distribution
            type_counts = {}
            total_learning_value = 0

            for item in classifications:
                content_type = item["content_type"]
                type_counts[content_type] = type_counts.get(content_type, 0) + 1
                total_learning_value += item["learning_value_score"]

            total_articles = len(classifications)
            avg_learning_value = total_learning_value / total_articles

            # Calculate educational content ratio
            educational_types = ["tutorial", "guide", "project", "reference"]
            educational_count = sum([type_counts.get(t, 0) for t in educational_types])
            educational_ratio = educational_count / total_articles

            # Get feedback stats
            feedback_result = (
                self.supabase.client.table("content_feedback")
                .select("educational_value_rating, completion_status")
                .execute()
            )

            feedback_items = feedback_result.data

            if feedback_items:
                ratings = [
                    f["educational_value_rating"]
                    for f in feedback_items
                    if f["educational_value_rating"]
                ]
                avg_user_rating = sum(ratings) / len(ratings) if ratings else 0.0

                completed = len(
                    [f for f in feedback_items if f["completion_status"] == "completed"]
                )
                completion_rate = completed / len(feedback_items)
            else:
                avg_user_rating = 0.0
                completion_rate = 0.0

            return {
                "total_articles": total_articles,
                "educational_content_ratio": educational_ratio,
                "average_learning_value": avg_learning_value,
                "average_user_rating": avg_user_rating,
                "completion_rate": completion_rate,
                "content_type_distribution": type_counts,
                "total_feedback_items": len(feedback_items),
            }

        except Exception as e:
            logger.error(f"Failed to get quality overview: {e}")
            return {"error": str(e)}
