"""
User Profile Manager for Intelligent Q&A Agent

This module implements user profile analysis and learning functionality,
including reading history tracking, preference learning from query patterns,
and satisfaction feedback tracking for personalized recommendations.

Requirements: 8.1, 8.3, 8.5
"""

import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from .database import get_db_connection
from .models import QueryLanguage, UserProfile

logger = logging.getLogger(__name__)


from app.qa_agent._satisfaction_mixin import SatisfactionMixin


class UserProfileManagerError(Exception):
    """Base exception for UserProfileManager operations."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ReadingHistoryEntry:
    """Represents a single reading history entry with detailed tracking."""

    def __init__(
        self,
        article_id: UUID,
        read_at: datetime,
        read_duration_seconds: Optional[int] = None,
        completion_rate: Optional[float] = None,
        satisfaction_score: Optional[float] = None,
    ):
        self.article_id = article_id
        self.read_at = read_at
        self.read_duration_seconds = read_duration_seconds
        self.completion_rate = completion_rate  # 0.0 to 1.0
        self.satisfaction_score = satisfaction_score  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "article_id": str(self.article_id),
            "read_at": self.read_at.isoformat(),
            "read_duration_seconds": self.read_duration_seconds,
            "completion_rate": self.completion_rate,
            "satisfaction_score": self.satisfaction_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReadingHistoryEntry":
        """Create from dictionary."""
        return cls(
            article_id=UUID(data["article_id"]),
            read_at=datetime.fromisoformat(data["read_at"]),
            read_duration_seconds=data.get("read_duration_seconds"),
            completion_rate=data.get("completion_rate"),
            satisfaction_score=data.get("satisfaction_score"),
        )


class UserProfileManager(SatisfactionMixin):
    """
    Manages user profile operations including reading history tracking,
    preference learning, and satisfaction feedback analysis.

    Requirements: 8.1, 8.3, 8.5
    """

    def __init__(self):
        """Initialize the UserProfileManager."""
        self._preference_learning_threshold = 5  # Minimum interactions for learning
        self._satisfaction_weight = 0.7  # Weight for satisfaction in optimization
        self._recency_weight = 0.3  # Weight for recency in preference learning

    # ------------------------------------------------------------------
    # Reading History Tracking (Requirement 8.1)
    # ------------------------------------------------------------------

    async def track_article_view(
        self,
        user_id: UUID,
        article_id: UUID,
        read_duration_seconds: Optional[int] = None,
        completion_rate: Optional[float] = None,
    ) -> None:
        """
        Track when a user views an article with detailed metrics.

        Args:
            user_id: User identifier
            article_id: Article identifier
            read_duration_seconds: How long user spent reading (optional)
            completion_rate: Percentage of article read (0.0-1.0, optional)

        Validates: Requirement 8.1 - Track user reading history
        """
        try:
            async with get_db_connection() as conn:
                # Insert reading history entry
                await conn.execute(
                    """
                    INSERT INTO reading_history
                    (user_id, article_id, read_at, read_duration_seconds, completion_rate)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (user_id, article_id, read_at)
                    DO UPDATE SET
                        read_duration_seconds = EXCLUDED.read_duration_seconds,
                        completion_rate = EXCLUDED.completion_rate
                    """,
                    user_id,
                    article_id,
                    datetime.utcnow(),
                    read_duration_seconds,
                    completion_rate,
                )

                # Update user profile's reading history list
                await conn.execute(
                    """
                    UPDATE user_profiles
                    SET reading_history = array_append(
                        COALESCE(reading_history, ARRAY[]::jsonb[]),
                        $2::jsonb
                    ),
                    updated_at = $3
                    WHERE user_id = $1
                    """,
                    user_id,
                    f'"{article_id}"',  # JSON string format
                    datetime.utcnow(),
                )

                logger.info(
                    f"Tracked article view: user={user_id}, article={article_id}, "
                    f"duration={read_duration_seconds}s, completion={completion_rate}"
                )

        except Exception as e:
            logger.error(f"Failed to track article view: {e}", exc_info=True)
            raise UserProfileManagerError(f"Failed to track article view: {e}", original_error=e)

    async def get_reading_history(
        self,
        user_id: UUID,
        limit: int = 100,
        days_back: Optional[int] = None,
    ) -> List[ReadingHistoryEntry]:
        """
        Retrieve user's reading history with optional time filtering.

        Args:
            user_id: User identifier
            limit: Maximum number of entries to return
            days_back: Only return entries from last N days (optional)

        Returns:
            List of ReadingHistoryEntry objects sorted by recency

        Validates: Requirement 8.1 - Track user reading history
        """
        try:
            async with get_db_connection() as conn:
                query = """
                    SELECT article_id, read_at, read_duration_seconds,
                           completion_rate, satisfaction_score
                    FROM reading_history
                    WHERE user_id = $1
                """
                params = [user_id]

                if days_back:
                    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                    query += " AND read_at >= $2"
                    params.append(cutoff_date)

                query += " ORDER BY read_at DESC LIMIT $" + str(len(params) + 1)
                params.append(limit)

                rows = await conn.fetch(query, *params)

                return [
                    ReadingHistoryEntry(
                        article_id=row["article_id"],
                        read_at=row["read_at"],
                        read_duration_seconds=row["read_duration_seconds"],
                        completion_rate=row["completion_rate"],
                        satisfaction_score=row["satisfaction_score"],
                    )
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to get reading history: {e}", exc_info=True)
            raise UserProfileManagerError(f"Failed to get reading history: {e}", original_error=e)

    async def get_reading_statistics(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive reading statistics for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary containing reading statistics

        Validates: Requirement 8.1 - Track user reading history and preferences
        """
        try:
            async with get_db_connection() as conn:
                stats = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*) as total_articles_read,
                        AVG(read_duration_seconds) as avg_read_duration,
                        AVG(completion_rate) as avg_completion_rate,
                        AVG(satisfaction_score) as avg_satisfaction,
                        MAX(read_at) as last_read_at,
                        COUNT(DISTINCT DATE(read_at)) as reading_days
                    FROM reading_history
                    WHERE user_id = $1
                    """,
                    user_id,
                )

                return {
                    "total_articles_read": stats["total_articles_read"] or 0,
                    "avg_read_duration_seconds": float(stats["avg_read_duration"] or 0),
                    "avg_completion_rate": float(stats["avg_completion_rate"] or 0),
                    "avg_satisfaction": float(stats["avg_satisfaction"] or 0.5),
                    "last_read_at": stats["last_read_at"],
                    "reading_days": stats["reading_days"] or 0,
                }

        except Exception as e:
            logger.error(f"Failed to get reading statistics: {e}", exc_info=True)
            raise UserProfileManagerError(
                f"Failed to get reading statistics: {e}", original_error=e
            )

    # ------------------------------------------------------------------
    # Preference Learning (Requirement 8.3)
    # ------------------------------------------------------------------

    async def learn_preferences_from_queries(
        self, user_id: UUID, recent_queries: List[str]
    ) -> List[str]:
        """
        Learn user preferences from their query patterns.

        Analyzes query history to extract topics, technical depth preferences,
        and common themes.

        Args:
            user_id: User identifier
            recent_queries: List of recent query strings

        Returns:
            List of learned topic preferences

        Validates: Requirement 8.3 - Learn from user behavior patterns
        """
        if len(recent_queries) < self._preference_learning_threshold:
            logger.debug(
                f"Insufficient queries for learning: {len(recent_queries)} < "
                f"{self._preference_learning_threshold}"
            )
            return []

        try:
            # Extract keywords from queries
            all_keywords = []
            for query in recent_queries:
                keywords = self._extract_query_keywords(query)
                all_keywords.extend(keywords)

            # Count keyword frequency
            keyword_counts = Counter(all_keywords)

            # Identify top topics (keywords appearing multiple times)
            min_frequency = max(2, len(recent_queries) // 5)  # At least 20% of queries
            learned_topics = [
                keyword
                for keyword, count in keyword_counts.most_common(20)
                if count >= min_frequency
            ]

            logger.info(f"Learned {len(learned_topics)} topics from {len(recent_queries)} queries")

            return learned_topics

        except Exception as e:
            logger.error(f"Failed to learn preferences from queries: {e}", exc_info=True)
            return []

    async def learn_preferences_from_reading(self, user_id: UUID) -> Dict[str, Any]:
        """
        Learn user preferences from reading history patterns.

        Analyzes reading behavior including:
        - Preferred article categories
        - Technical depth preferences
        - Reading time patterns
        - Completion rates by topic

        Args:
            user_id: User identifier

        Returns:
            Dictionary containing learned preferences

        Validates: Requirement 8.3 - Learn from user behavior patterns
        """
        try:
            async with get_db_connection() as conn:
                # Get reading history with article metadata
                rows = await conn.fetch(
                    """
                    SELECT
                        rh.article_id,
                        rh.read_duration_seconds,
                        rh.completion_rate,
                        rh.satisfaction_score,
                        a.metadata
                    FROM reading_history rh
                    JOIN articles a ON rh.article_id = a.id
                    WHERE rh.user_id = $1
                    ORDER BY rh.read_at DESC
                    LIMIT 100
                    """,
                    user_id,
                )

                if not rows:
                    return {
                        "preferred_categories": [],
                        "preferred_technical_depth": "intermediate",
                        "avg_reading_time_seconds": 0,
                        "high_engagement_topics": [],
                    }

                # Analyze categories
                categories = []
                technical_depths = []
                reading_times = []
                high_engagement_articles = []

                for row in rows:
                    metadata = row["metadata"] or {}

                    # Extract category
                    if "category" in metadata:
                        categories.append(metadata["category"])

                    # Extract technical depth
                    if "technical_level" in metadata:
                        technical_depths.append(metadata["technical_level"])

                    # Track reading time
                    if row["read_duration_seconds"]:
                        reading_times.append(row["read_duration_seconds"])

                    # Identify high engagement (high completion + satisfaction)
                    completion = row["completion_rate"] or 0
                    satisfaction = row["satisfaction_score"] or 0
                    if completion > 0.7 and satisfaction > 0.7:
                        if "topics" in metadata:
                            high_engagement_articles.extend(metadata["topics"])

                # Calculate preferences
                category_counts = Counter(categories)
                preferred_categories = [cat for cat, _ in category_counts.most_common(5)]

                # Determine preferred technical depth
                depth_counts = Counter(technical_depths)
                preferred_depth = (
                    depth_counts.most_common(1)[0][0] if depth_counts else "intermediate"
                )

                # Calculate average reading time
                avg_reading_time = sum(reading_times) // len(reading_times) if reading_times else 0

                # Identify high engagement topics
                topic_counts = Counter(high_engagement_articles)
                high_engagement_topics = [topic for topic, _ in topic_counts.most_common(10)]

                learned_preferences = {
                    "preferred_categories": preferred_categories,
                    "preferred_technical_depth": preferred_depth,
                    "avg_reading_time_seconds": avg_reading_time,
                    "high_engagement_topics": high_engagement_topics,
                }

                logger.info(
                    f"Learned reading preferences for user {user_id}: "
                    f"{len(preferred_categories)} categories, "
                    f"{len(high_engagement_topics)} high-engagement topics"
                )

                return learned_preferences

        except Exception as e:
            logger.error(f"Failed to learn preferences from reading: {e}", exc_info=True)
            raise UserProfileManagerError(
                f"Failed to learn preferences from reading: {e}", original_error=e
            )

    async def update_user_preferences(
        self, user_id: UUID, learned_preferences: Dict[str, Any]
    ) -> None:
        """
        Update user profile with learned preferences.

        Args:
            user_id: User identifier
            learned_preferences: Dictionary of learned preferences

        Validates: Requirement 8.3 - Learn from user behavior patterns
        """
        try:
            async with get_db_connection() as conn:
                # Update preferred topics
                if "preferred_categories" in learned_preferences:
                    await conn.execute(
                        """
                        UPDATE user_profiles
                        SET preferred_topics = $2::jsonb,
                            updated_at = $3
                        WHERE user_id = $1
                        """,
                        user_id,
                        learned_preferences["preferred_categories"],
                        datetime.utcnow(),
                    )

                # Update interaction patterns
                if "preferred_technical_depth" in learned_preferences:
                    await conn.execute(
                        """
                        UPDATE user_profiles
                        SET interaction_patterns = jsonb_set(
                            COALESCE(interaction_patterns, '{}'::jsonb),
                            '{technical_depth}',
                            to_jsonb($2::text)
                        ),
                        updated_at = $3
                        WHERE user_id = $1
                        """,
                        user_id,
                        learned_preferences["preferred_technical_depth"],
                        datetime.utcnow(),
                    )

                logger.info(f"Updated preferences for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to update user preferences: {e}", exc_info=True)
            raise UserProfileManagerError(
                f"Failed to update user preferences: {e}", original_error=e
            )

    # ------------------------------------------------------------------
    # Satisfaction Feedback (Requirement 8.5)
    # ------------------------------------------------------------------

    async def record_satisfaction_feedback(
        self,
        user_id: UUID,
        article_id: UUID,
        satisfaction_score: float,
        feedback_type: str = "explicit",
    ) -> None:
        """
        Record user satisfaction feedback for an article.

        Args:
            user_id: User identifier
            article_id: Article identifier
            satisfaction_score: Satisfaction score (0.0-1.0)
            feedback_type: Type of feedback ("explicit" or "implicit")

        Validates: Requirement 8.5 - Track satisfaction feedback and optimize
        """
        if not 0.0 <= satisfaction_score <= 1.0:
            raise ValueError(f"Invalid satisfaction score: {satisfaction_score}")

        try:
            async with get_db_connection() as conn:
                # Update reading history with satisfaction score
                await conn.execute(
                    """
                    UPDATE reading_history
                    SET satisfaction_score = $3,
                        feedback_type = $4
                    WHERE user_id = $1 AND article_id = $2
                    """,
                    user_id,
                    article_id,
                    satisfaction_score,
                    feedback_type,
                )

                # Add to user profile's satisfaction scores
                await conn.execute(
                    """
                    UPDATE user_profiles
                    SET satisfaction_scores = array_append(
                        COALESCE(satisfaction_scores, ARRAY[]::float[]),
                        $2::float
                    ),
                    updated_at = $3
                    WHERE user_id = $1
                    """,
                    user_id,
                    satisfaction_score,
                    datetime.utcnow(),
                )

                logger.info(
                    f"Recorded {feedback_type} satisfaction feedback: "
                    f"user={user_id}, article={article_id}, score={satisfaction_score}"
                )

        except Exception as e:
            logger.error(f"Failed to record satisfaction feedback: {e}", exc_info=True)
            raise UserProfileManagerError(
                f"Failed to record satisfaction feedback: {e}", original_error=e
            )

    async def get_or_create_profile(self, user_id: UUID) -> UserProfile:
        """
        Get existing user profile or create a new one.

        Args:
            user_id: User identifier

        Returns:
            UserProfile object

        Validates: Requirements 8.1, 8.3, 8.5
        """
        try:
            async with get_db_connection() as conn:
                # Try to get existing profile
                row = await conn.fetchrow(
                    """
                    SELECT user_id, reading_history, preferred_topics,
                           language_preference, interaction_patterns,
                           query_history, satisfaction_scores,
                           created_at, updated_at
                    FROM user_profiles
                    WHERE user_id = $1
                    """,
                    user_id,
                )

                if row:
                    # Convert database row to UserProfile
                    return UserProfile(
                        user_id=row["user_id"],
                        reading_history=[UUID(aid) for aid in (row["reading_history"] or [])],
                        preferred_topics=row["preferred_topics"] or [],
                        language_preference=QueryLanguage(row["language_preference"] or "zh"),
                        interaction_patterns=row["interaction_patterns"] or {},
                        query_history=row["query_history"] or [],
                        satisfaction_scores=row["satisfaction_scores"] or [],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                else:
                    # Create new profile
                    now = datetime.utcnow()
                    await conn.execute(
                        """
                        INSERT INTO user_profiles
                        (user_id, reading_history, preferred_topics,
                         language_preference, interaction_patterns,
                         query_history, satisfaction_scores, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        """,
                        user_id,
                        [],
                        [],
                        "zh",
                        {},
                        [],
                        [],
                        now,
                        now,
                    )

                    return UserProfile(
                        user_id=user_id,
                        reading_history=[],
                        preferred_topics=[],
                        language_preference=QueryLanguage.CHINESE,
                        interaction_patterns={},
                        query_history=[],
                        satisfaction_scores=[],
                        created_at=now,
                        updated_at=now,
                    )

        except Exception as e:
            logger.error(f"Failed to get or create profile: {e}", exc_info=True)
            raise UserProfileManagerError(f"Failed to get or create profile: {e}", original_error=e)

    async def update_profile(self, profile: UserProfile) -> None:
        """
        Update user profile in database.

        Args:
            profile: UserProfile object to update

        Validates: Requirements 8.1, 8.3, 8.5
        """
        try:
            async with get_db_connection() as conn:
                await conn.execute(
                    """
                    UPDATE user_profiles
                    SET reading_history = $2,
                        preferred_topics = $3,
                        language_preference = $4,
                        interaction_patterns = $5,
                        query_history = $6,
                        satisfaction_scores = $7,
                        updated_at = $8
                    WHERE user_id = $1
                    """,
                    profile.user_id,
                    [str(aid) for aid in profile.reading_history],
                    profile.preferred_topics,
                    profile.language_preference.value,
                    profile.interaction_patterns,
                    profile.query_history,
                    profile.satisfaction_scores,
                    datetime.utcnow(),
                )

                logger.info(f"Updated profile for user {profile.user_id}")

        except Exception as e:
            logger.error(f"Failed to update profile: {e}", exc_info=True)
            raise UserProfileManagerError(f"Failed to update profile: {e}", original_error=e)

    # ------------------------------------------------------------------
    # Helper Methods
    # ------------------------------------------------------------------

    def _extract_query_keywords(self, query: str) -> List[str]:
        """
        Extract meaningful keywords from a query string.

        Args:
            query: Query string

        Returns:
            List of extracted keywords
        """
        import re

        # Stop words to filter out
        stop_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "of",
            "in",
            "on",
            "at",
            "to",
            "for",
            "with",
            "by",
            "from",
            "and",
            "or",
            "but",
            "not",
            "what",
            "how",
            "why",
            "when",
            "where",
            "who",
            "which",
            "的",
            "是",
            "了",
            "在",
            "和",
            "有",
            "我",
            "你",
            "他",
            "她",
        }

        # Remove punctuation and split
        clean_query = re.sub(r"[^\w\s]", " ", query)
        tokens = clean_query.lower().split()

        # Filter stop words and short tokens
        keywords = [t for t in tokens if len(t) >= 2 and t not in stop_words]

        return keywords


# Singleton instance
_user_profile_manager_instance: Optional[UserProfileManager] = None


def get_user_profile_manager() -> UserProfileManager:
    """
    Get or create a singleton UserProfileManager instance.

    Returns:
        UserProfileManager instance
    """
    global _user_profile_manager_instance
    if _user_profile_manager_instance is None:
        _user_profile_manager_instance = UserProfileManager()
    return _user_profile_manager_instance
