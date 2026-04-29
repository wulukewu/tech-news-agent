"""
Article Recommender

Recommends relevant articles based on current learning stage and user preferences.
Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 9.1, 9.2, 9.3, 9.4, 9.5
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from app.qa_agent.learning_path.path_generator import LearningPath, LearningStage
from app.schemas.article import ArticleSchema
from app.services.supabase_service import SupabaseService


@dataclass
class RecommendedArticle:
    """Article with recommendation metadata"""

    article: ArticleSchema
    relevance_score: float
    difficulty_match: float
    reason: str
    stage_name: str


class ArticleRecommender:
    """
    Intelligent article recommendation engine for learning paths.
    Considers current stage, difficulty level, and user preferences.
    """

    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service

    async def get_recommendations(
        self,
        user_id: str,
        learning_path: LearningPath,
        current_stage_order: int = 1,
        limit: int = 10,
        target_skill: str = "",
    ) -> List[RecommendedArticle]:
        """
        Get article recommendations for current learning stage.

        Args:
            user_id: User ID for personalization
            learning_path: User's learning path
            current_stage_order: Current stage (1-based)
            limit: Maximum number of recommendations

        Returns:
            List of recommended articles with metadata
        """
        # Get current stage
        current_stage = self._get_stage_by_order(learning_path, current_stage_order)
        if not current_stage:
            return []

        # Get user's reading history and preferences
        user_preferences = await self._get_user_preferences(user_id)
        read_articles = await self._get_read_articles(user_id)

        # Find relevant articles for current stage skills
        candidate_articles = await self._find_relevant_articles(current_stage, target_skill)

        # If no candidates found, fall back to top articles
        if not candidate_articles:
            candidate_articles = await self._find_fallback_articles(set())

        # Score and rank articles
        scored_articles = []
        for article in candidate_articles:
            score_data = await self._score_article(article, current_stage, user_preferences)
            if score_data:
                scored_articles.append(score_data)

        # Sort by relevance score and return top N
        scored_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored_articles[:limit]

    def _get_stage_by_order(
        self, learning_path: LearningPath, stage_order: int
    ) -> Optional[LearningStage]:
        """Get stage by order number, fallback to first stage if not found"""
        for stage in learning_path.stages:
            if stage.stage_order == stage_order:
                return stage
        # Fallback: return the stage with the lowest order
        if learning_path.stages:
            return min(learning_path.stages, key=lambda s: s.stage_order)
        return None

    async def _get_user_preferences(self, user_id: str) -> Dict:
        """Get user reading preferences and patterns"""
        try:
            # Get user's rating patterns
            response = (
                self.supabase.client.table("reading_list")
                .select("article_id, rating, status")
                .eq("user_id", user_id)
                .not_.is_("rating", "null")
                .execute()
            )

            preferences = {
                "avg_rating": 0,
                "preferred_categories": [],
                "reading_frequency": 0,
                "difficulty_preference": 3,  # Default to intermediate
            }

            if response.data:
                ratings = [r["rating"] for r in response.data if r["rating"]]
                if ratings:
                    preferences["avg_rating"] = sum(ratings) / len(ratings)

            return preferences
        except Exception:
            return {
                "avg_rating": 0,
                "preferred_categories": [],
                "reading_frequency": 0,
                "difficulty_preference": 3,
            }

    async def _find_fallback_articles(self, exclude_ids: set) -> list:
        """Return top articles by tinkering_index, excluding already completed ones."""
        try:
            select_fields = "id, feed_id, title, url, published_at, tinkering_index, ai_summary, created_at, category"
            resp = (
                self.supabase.client.table("articles")
                .select(select_fields)
                .order("tinkering_index", desc=True)
                .limit(50)
                .execute()
            )
            articles = []
            for record in resp.data or []:
                if str(record["id"]) in exclude_ids:
                    continue
                try:
                    record.setdefault("feed_name", record.get("category") or "")
                    if isinstance(record.get("embedding"), str):
                        record["embedding"] = None
                    articles.append(ArticleSchema(**record))
                except Exception:
                    pass
            return articles[:20]
        except Exception:
            return []

    async def _get_read_articles(self, user_id: str) -> set:
        """Get set of article IDs user has already completed in learning progress"""
        try:
            response = (
                self.supabase.client.table("learning_progress")
                .select("article_id")
                .eq("user_id", user_id)
                .eq("status", "completed")
                .execute()
            )
            return {str(record["article_id"]) for record in response.data}
        except Exception:
            return set()

    async def _find_relevant_articles(
        self, stage: LearningStage, target_skill: str = ""
    ) -> List[ArticleSchema]:
        """Find articles relevant to current learning stage"""
        try:
            articles: List[ArticleSchema] = []
            seen_ids: set = set()

            def add_articles(records: list) -> None:
                for record in records:
                    if record["id"] not in seen_ids:
                        seen_ids.add(record["id"])
                        try:
                            # Normalize fields not present in plain articles query
                            record.setdefault("feed_name", record.get("category") or "")
                            if isinstance(record.get("embedding"), str):
                                record["embedding"] = None
                            articles.append(ArticleSchema(**record))
                        except Exception:
                            pass

            select_fields = "id, feed_id, title, url, published_at, tinkering_index, ai_summary, created_at, category"

            # 1. Search by skill names in title and ai_summary
            skill_names = [skill.name.replace("-", " ") for skill in stage.skills]
            for skill_name in skill_names:
                for field in ("title", "ai_summary"):
                    resp = (
                        self.supabase.client.table("articles")
                        .select(select_fields)
                        .ilike(field, f"%{skill_name}%")
                        .limit(20)
                        .execute()
                    )
                    add_articles(resp.data or [])

            # 2. Search by skill tags in category and ai_summary
            for skill in stage.skills:
                for tag in skill.tags:
                    for field in ("category", "ai_summary"):
                        resp = (
                            self.supabase.client.table("articles")
                            .select(select_fields)
                            .ilike(field, f"%{tag}%")
                            .limit(10)
                            .execute()
                        )
                        add_articles(resp.data or [])

            # 3. Fallback: use target_skill keyword against title + category
            if not articles and target_skill:
                for keyword in target_skill.replace("-", " ").split():
                    if len(keyword) < 3:
                        continue
                    for field in ("title", "ai_summary", "category"):
                        resp = (
                            self.supabase.client.table("articles")
                            .select(select_fields)
                            .ilike(field, f"%{keyword}%")
                            .order("tinkering_index", desc=True)
                            .limit(20)
                            .execute()
                        )
                        add_articles(resp.data or [])

            # 4. Last resort: top articles by tinkering_index
            if not articles:
                resp = (
                    self.supabase.client.table("articles")
                    .select(select_fields)
                    .order("tinkering_index", desc=True)
                    .limit(20)
                    .execute()
                )
                add_articles(resp.data or [])

            # 5. Absolute fallback: any recent articles
            if not articles:
                resp = (
                    self.supabase.client.table("articles")
                    .select(select_fields)
                    .order("created_at", desc=True)
                    .limit(20)
                    .execute()
                )
                add_articles(resp.data or [])

            return articles[:50]
        except Exception:
            return []

    async def _score_article(
        self, article: ArticleSchema, stage: LearningStage, user_preferences: Dict
    ) -> Optional[RecommendedArticle]:
        """Score article relevance for current stage"""
        try:
            # Base relevance score
            relevance_score = 0.0

            # Check title relevance to stage skills
            title_lower = article.title.lower()
            skill_matches = 0
            for skill in stage.skills:
                skill_terms = skill.name.replace("-", " ").split()
                for term in skill_terms:
                    if term in title_lower:
                        skill_matches += 1
                        relevance_score += 0.3

            # Check category relevance
            if article.category:
                category_lower = article.category.lower()
                for skill in stage.skills:
                    if skill.category in category_lower:
                        relevance_score += 0.2
                    for tag in skill.tags:
                        if tag in category_lower:
                            relevance_score += 0.1

            # Difficulty matching (prefer articles matching stage difficulty)
            article_difficulty = article.tinkering_index or 3
            if stage.skills:
                stage_difficulty = sum(
                    skill.difficulty_level.value for skill in stage.skills
                ) / len(stage.skills)
            else:
                stage_difficulty = 3
            difficulty_diff = abs(article_difficulty - stage_difficulty)
            difficulty_match = max(0, 1 - (difficulty_diff / 5))
            relevance_score += difficulty_match * 0.3 + 0.1  # base score so fallback articles pass

            # Boost recent articles slightly
            if article.published_at:
                from datetime import timezone

                now = datetime.now(timezone.utc)
                pub = article.published_at
                if pub.tzinfo is None:
                    pub = pub.replace(tzinfo=timezone.utc)
                days_old = (now - pub).days
                if days_old < 30:
                    relevance_score += 0.1

            # Only recommend if minimum relevance threshold met
            if relevance_score < 0.1:
                return None

            # Generate recommendation reason
            reason = self._generate_recommendation_reason(article, stage, skill_matches)

            return RecommendedArticle(
                article=article,
                relevance_score=relevance_score,
                difficulty_match=difficulty_match,
                reason=reason,
                stage_name=stage.stage_name,
            )

        except Exception:
            return None

    def _generate_recommendation_reason(
        self, article: ArticleSchema, stage: LearningStage, skill_matches: int
    ) -> str:
        """Generate human-readable recommendation reason"""
        if skill_matches > 0:
            return f"這篇文章涵蓋了你在{stage.stage_name}階段需要學習的技能"
        elif article.category and any(
            skill.category in article.category.lower() for skill in stage.skills
        ):
            return f"這篇文章屬於{stage.stage_name}階段的相關領域"
        else:
            return f"推薦給{stage.stage_name}階段學習"

    async def mark_article_completed(self, user_id: str, article_id: str, goal_id: str) -> None:
        """Mark an article as completed in learning progress"""
        try:
            self.supabase.client.table("learning_progress").upsert(
                {
                    "user_id": user_id,
                    "goal_id": goal_id,
                    "article_id": article_id,
                    "status": "completed",
                    "completion_percentage": 100,
                    "completed_at": datetime.now().isoformat(),
                },
                on_conflict="user_id,goal_id,article_id",
            ).execute()
        except Exception as e:
            raise Exception(f"Failed to mark article completed: {e}")

    async def get_next_recommendations(
        self, user_id: str, goal_id: str
    ) -> List[RecommendedArticle]:
        """Get next set of recommendations after completing articles"""
        # This would analyze completed articles and suggest next logical steps
        # For now, return empty list - can be enhanced later
        return []
