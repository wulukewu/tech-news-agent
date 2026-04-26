import logging
from dataclasses import dataclass
from typing import Dict, List

from ..schemas.article import ArticleSchema
from ..services.content_classification_service import (
    ContentClassificationService,
    ContentType,
)
from ..services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


@dataclass
class LearningPreferences:
    preferred_content_types: List[ContentType]
    preferred_difficulty_progression: float
    learning_style: str
    time_availability: int
    completion_rate_threshold: float


@dataclass
class RecommendationContext:
    user_id: str
    current_learning_stage: int
    target_skills: List[str]
    completed_articles: List[str]
    learning_preferences: LearningPreferences
    session_context: Dict


@dataclass
class ScoredArticle:
    article: ArticleSchema
    score: float
    reasoning: str


class EnhancedRecommendationEngine:
    """Enhanced recommendation engine prioritizing educational content."""

    def __init__(
        self,
        supabase_service: SupabaseService,
        classification_service: ContentClassificationService,
    ):
        self.supabase = supabase_service
        self.classifier = classification_service

    async def get_learning_recommendations(
        self,
        user_id: str,
        goal_id: str = None,
        stage: int = 1,
        content_types: List[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Get personalized learning recommendations with educational priority."""
        try:
            # Get user preferences
            preferences = await self._get_user_preferences(user_id)

            # Get user's completed articles
            completed_articles = await self._get_completed_articles(user_id)

            # Get candidate articles
            candidates = await self._get_candidate_articles(
                content_types or [ct.value for ct in preferences.preferred_content_types],
                completed_articles,
            )

            # Score and rank articles
            scored_articles = await self._score_articles(candidates, preferences, user_id)

            # Apply diversity and final ranking
            final_recommendations = await self._apply_final_ranking(scored_articles, limit)

            return final_recommendations

        except Exception as e:
            logger.error(f"Failed to get learning recommendations for user {user_id}: {e}")
            return []

    async def _get_user_preferences(self, user_id: str) -> LearningPreferences:
        """Get user learning preferences or create defaults."""
        try:
            result = (
                self.supabase.client.table("user_learning_preferences")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if result.data:
                prefs = result.data[0]
                return LearningPreferences(
                    preferred_content_types=[
                        ContentType(ct) for ct in prefs["preferred_content_types"]
                    ],
                    preferred_difficulty_progression=prefs["preferred_difficulty_progression"],
                    learning_style=prefs["learning_style"],
                    time_availability=prefs["time_availability_minutes"],
                    completion_rate_threshold=prefs["completion_rate_threshold"],
                )
            else:
                # Create default preferences
                default_prefs = {
                    "user_id": user_id,
                    "preferred_content_types": ["tutorial", "guide"],
                    "preferred_difficulty_progression": 0.7,
                    "learning_style": "balanced",
                    "time_availability_minutes": 30,
                    "completion_rate_threshold": 0.8,
                }

                self.supabase.client.table("user_learning_preferences").insert(
                    default_prefs
                ).execute()

                return LearningPreferences(
                    preferred_content_types=[ContentType.TUTORIAL, ContentType.GUIDE],
                    preferred_difficulty_progression=0.7,
                    learning_style="balanced",
                    time_availability=30,
                    completion_rate_threshold=0.8,
                )

        except Exception as e:
            logger.error(f"Failed to get user preferences for {user_id}: {e}")
            return LearningPreferences(
                preferred_content_types=[ContentType.TUTORIAL, ContentType.GUIDE],
                preferred_difficulty_progression=0.7,
                learning_style="balanced",
                time_availability=30,
                completion_rate_threshold=0.8,
            )

    async def _get_completed_articles(self, user_id: str) -> List[str]:
        """Get list of articles user has completed."""
        try:
            result = (
                self.supabase.client.table("reading_list")
                .select("article_id")
                .eq("user_id", user_id)
                .eq("status", "read")
                .execute()
            )

            return [item["article_id"] for item in result.data]

        except Exception as e:
            logger.error(f"Failed to get completed articles for {user_id}: {e}")
            return []

    async def _get_candidate_articles(
        self, content_types: List[str], completed_articles: List[str]
    ) -> List[Dict]:
        """Get candidate articles for recommendation."""
        try:
            query = (
                self.supabase.client.table("article_classifications")
                .select(
                    "*, articles(id, title, url, published_at, feed_id, tinkering_index, ai_summary)"
                )
                .in_("content_type", content_types)
                .gte("learning_value_score", 0.6)
            )

            if completed_articles:
                query = query.not_.in_("article_id", completed_articles)

            result = query.order("learning_value_score", desc=True).limit(100).execute()

            return result.data

        except Exception as e:
            logger.error(f"Failed to get candidate articles: {e}")
            return []

    async def _score_articles(
        self, candidates: List[Dict], preferences: LearningPreferences, user_id: str
    ) -> List[ScoredArticle]:
        """Score articles based on learning value and user preferences."""
        scored_articles = []

        for candidate in candidates:
            try:
                article_data = candidate["articles"]
                classification = candidate

                # Base learning value score
                base_score = classification["learning_value_score"]

                # Content type preference bonus
                content_type_bonus = 0.0
                if (
                    ContentType(classification["content_type"])
                    in preferences.preferred_content_types
                ):
                    content_type_bonus = 0.2

                # Difficulty appropriateness
                difficulty_score = self._calculate_difficulty_score(
                    classification["difficulty_level"], preferences.preferred_difficulty_progression
                )

                # Time availability match
                estimated_time = classification["educational_features"].get(
                    "estimated_reading_time", 15
                )
                time_score = 1.0 if estimated_time <= preferences.time_availability else 0.5

                # Educational features bonus
                features = classification["educational_features"]
                feature_bonus = 0.0
                if features.get("has_code_examples", False):
                    feature_bonus += 0.1
                if features.get("has_step_by_step", False):
                    feature_bonus += 0.1
                if features.get("has_practical_exercises", False):
                    feature_bonus += 0.15

                # Calculate final score
                final_score = (
                    base_score * 0.4
                    + content_type_bonus
                    + difficulty_score * 0.2
                    + time_score * 0.1
                    + feature_bonus
                )

                # Create article schema
                article = ArticleSchema(
                    id=article_data["id"],
                    title=article_data["title"],
                    url=article_data["url"],
                    published_at=article_data["published_at"],
                    feed_id=article_data["feed_id"],
                    tinkering_index=article_data.get("tinkering_index", 0),
                    ai_summary=article_data.get("ai_summary", ""),
                    content="",  # Not needed for recommendations
                )

                reasoning = f"Learning value: {base_score:.2f}, Content match: {content_type_bonus:.2f}, Features: {feature_bonus:.2f}"

                scored_articles.append(
                    ScoredArticle(article=article, score=final_score, reasoning=reasoning)
                )

            except Exception as e:
                logger.error(
                    f"Failed to score article {candidate.get('article_id', 'unknown')}: {e}"
                )
                continue

        return sorted(scored_articles, key=lambda x: x.score, reverse=True)

    def _calculate_difficulty_score(
        self, article_difficulty: int, user_progression: float
    ) -> float:
        """Calculate how well article difficulty matches user progression."""
        # Convert user progression (0-1) to difficulty level (1-4)
        target_difficulty = 1 + (user_progression * 3)

        # Calculate distance from target
        distance = abs(article_difficulty - target_difficulty)

        # Convert to score (closer = higher score)
        if distance <= 0.5:
            return 1.0
        elif distance <= 1.0:
            return 0.8
        elif distance <= 1.5:
            return 0.6
        else:
            return 0.4

    async def _apply_final_ranking(
        self, scored_articles: List[ScoredArticle], limit: int
    ) -> List[Dict]:
        """Apply final ranking with diversity considerations."""
        try:
            # Group by content type for diversity
            type_groups = {}
            for article in scored_articles:
                # Get classification for content type
                result = (
                    self.supabase.client.table("article_classifications")
                    .select("content_type")
                    .eq("article_id", article.article.id)
                    .execute()
                )

                if result.data:
                    content_type = result.data[0]["content_type"]
                    if content_type not in type_groups:
                        type_groups[content_type] = []
                    type_groups[content_type].append(article)

            # Select diverse articles
            final_recommendations = []
            type_keys = list(type_groups.keys())
            type_index = 0

            while len(final_recommendations) < limit and any(type_groups.values()):
                current_type = type_keys[type_index % len(type_keys)]

                if type_groups[current_type]:
                    article = type_groups[current_type].pop(0)

                    # Get full classification data
                    classification_result = (
                        self.supabase.client.table("article_classifications")
                        .select("*")
                        .eq("article_id", article.article.id)
                        .execute()
                    )

                    recommendation = {
                        "article": {
                            "id": article.article.id,
                            "title": article.article.title,
                            "url": article.article.url,
                            "published_at": article.article.published_at,
                            "ai_summary": article.article.ai_summary,
                            "tinkering_index": article.article.tinkering_index,
                        },
                        "score": article.score,
                        "reasoning": article.reasoning,
                        "classification": classification_result.data[0]
                        if classification_result.data
                        else None,
                    }

                    final_recommendations.append(recommendation)

                type_index += 1

            return final_recommendations

        except Exception as e:
            logger.error(f"Failed to apply final ranking: {e}")
            return []

    async def update_user_preferences(self, user_id: str, preferences: Dict) -> bool:
        """Update user learning preferences."""
        try:
            self.supabase.client.table("user_learning_preferences").upsert(
                {"user_id": user_id, **preferences, "updated_at": "NOW()"}
            ).execute()

            return True

        except Exception as e:
            logger.error(f"Failed to update preferences for user {user_id}: {e}")
            return False
