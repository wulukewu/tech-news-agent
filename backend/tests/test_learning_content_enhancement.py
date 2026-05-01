"""
Unit tests for learning content enhancement system.
Tests classification logic, recommendation scoring, and API endpoints.
"""
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

# ── Task 2.3 / 2.2: ContentClassificationService fallback heuristics ──────────


class TestContentClassificationFallback:
    """Test heuristic classification without LLM calls."""

    def _make_service(self):
        from app.services.content_classification_service import ContentClassificationService

        svc = ContentClassificationService.__new__(ContentClassificationService)
        svc.llm = MagicMock()
        svc.supabase = MagicMock()
        svc.classification_cache = {}
        return svc

    def _make_article(self, title: str, category: str = ""):
        from app.schemas.article import ArticleSchema

        return ArticleSchema(
            id=uuid4(),
            title=title,
            url="https://example.com/article",
            feed_id=uuid4(),
            feed_name="Test Feed",
            category=category,
        )

    def test_tutorial_detected_by_title(self):
        from app.services.content_classification_service import ContentType

        svc = self._make_service()
        article = self._make_article("How to Build a REST API with FastAPI")
        result = svc._fallback_classification(article)
        assert result.content_type == ContentType.TUTORIAL
        assert result.learning_value_score >= 0.7

    def test_guide_detected_by_title(self):
        from app.services.content_classification_service import ContentType

        svc = self._make_service()
        article = self._make_article("A Complete Guide to Docker Networking")
        result = svc._fallback_classification(article)
        assert result.content_type == ContentType.GUIDE

    def test_news_is_default(self):
        from app.services.content_classification_service import ContentType

        svc = self._make_service()
        article = self._make_article("Some Random Tech Article")
        result = svc._fallback_classification(article)
        assert result.content_type == ContentType.NEWS
        assert result.learning_value_score <= 0.4

    def test_confidence_lower_for_fallback(self):
        svc = self._make_service()
        article = self._make_article("Introduction to Kubernetes")
        result = svc._fallback_classification(article)
        assert result.confidence_score < 1.0


# ── Task 3.1: ArticleRecommender content_type weighting ───────────────────────


class TestArticleRecommenderScoring:
    """Test that tutorial/guide articles score higher than news."""

    def _make_recommender(self):
        from app.qa_agent.learning_path.article_recommender import ArticleRecommender

        rec = ArticleRecommender.__new__(ArticleRecommender)
        rec.supabase = MagicMock()
        return rec

    def _make_article(self, title: str, content_type: str, tinkering_index: int = 3):
        from app.schemas.article import ArticleSchema

        a = ArticleSchema(
            id=uuid4(),
            title=title,
            url="https://example.com/a",
            feed_id=uuid4(),
            feed_name="Feed",
            category="Web Development & Programming",
            tinkering_index=tinkering_index,
        )
        a.content_type = content_type
        return a

    def _make_stage(self):
        from app.services.content_classification_service import DifficultyLevel

        skill = MagicMock()
        skill.name = "python"
        skill.tags = ["python", "programming"]
        skill.category = "web"
        skill.difficulty_level = DifficultyLevel.INTERMEDIATE

        stage = MagicMock()
        stage.stage_name = "Python Basics"
        stage.skills = [skill]
        return stage

    @pytest.mark.asyncio
    async def test_tutorial_scores_higher_than_news(self):
        rec = self._make_recommender()
        stage = self._make_stage()

        tutorial = self._make_article("Python Tutorial: Build a Web App", "tutorial")
        news = self._make_article("Python 3.13 Released", "news")

        tutorial_result = await rec._score_article(tutorial, stage, {})
        news_result = await rec._score_article(news, stage, {})

        assert tutorial_result is not None
        assert news_result is not None
        assert tutorial_result.relevance_score > news_result.relevance_score

    @pytest.mark.asyncio
    async def test_guide_scores_higher_than_news(self):
        rec = self._make_recommender()
        stage = self._make_stage()

        guide = self._make_article("Complete Guide to Python Async", "guide")
        news = self._make_article("Company Announces Python Partnership", "news")

        guide_result = await rec._score_article(guide, stage, {})
        news_result = await rec._score_article(news, stage, {})

        assert guide_result.relevance_score > news_result.relevance_score

    @pytest.mark.asyncio
    async def test_none_content_type_is_neutral(self):
        """Articles without content_type should not crash and get neutral score."""
        rec = self._make_recommender()
        stage = self._make_stage()

        article = self._make_article("Some Article", None)
        result = await rec._score_article(article, stage, {})
        assert result is not None


# ── Task 4.2: EnhancedRecommendationEngine quality feedback weighting ─────────


class TestEnhancedRecommendationQualityWeighting:
    """Test that user feedback quality scores affect recommendation ranking."""

    def _make_engine(self):
        from app.services.enhanced_recommendation_engine import EnhancedRecommendationEngine

        engine = EnhancedRecommendationEngine.__new__(EnhancedRecommendationEngine)
        engine.supabase = MagicMock()
        engine.classifier = MagicMock()
        return engine

    def _make_candidate(self, article_id: str, content_type: str = "tutorial") -> dict:
        return {
            "article_id": article_id,
            "content_type": content_type,
            "difficulty_level": 2,
            "learning_value_score": 0.8,
            "confidence_score": 0.9,
            "educational_features": {
                "has_code_examples": True,
                "has_step_by_step": True,
                "has_practical_exercises": False,
                "has_visual_aids": False,
                "estimated_reading_time": 15,
                "prerequisite_skills": [],
            },
            "articles": {
                "id": article_id,
                "title": "Test Article",
                "url": "https://example.com",
                "published_at": None,
                "feed_id": str(uuid4()),
                "tinkering_index": 3,
                "ai_summary": "Test summary",
            },
        }

    def _make_preferences(self):
        from app.services.content_classification_service import ContentType
        from app.services.enhanced_recommendation_engine import LearningPreferences

        return LearningPreferences(
            preferred_content_types=[ContentType.TUTORIAL, ContentType.GUIDE],
            preferred_difficulty_progression=0.5,
            learning_style="balanced",
            time_availability=30,
            completion_rate_threshold=0.8,
        )

    @pytest.mark.asyncio
    async def test_high_quality_article_scores_higher(self):
        engine = self._make_engine()
        prefs = self._make_preferences()

        high_id = str(uuid4())
        low_id = str(uuid4())

        # Mock quality metrics: high_id has good ratings, low_id has poor ratings
        def mock_quality_query(table_name):
            mock = MagicMock()
            mock.select.return_value = mock
            mock.in_.return_value = mock
            mock.execute.return_value = MagicMock(
                data=[
                    {"article_id": high_id, "average_rating": 5.0, "completion_rate": 0.9},
                    {"article_id": low_id, "average_rating": 1.0, "completion_rate": 0.1},
                ]
            )
            return mock

        engine.supabase.client.table = mock_quality_query

        candidates = [
            self._make_candidate(high_id),
            self._make_candidate(low_id),
        ]

        results = await engine._score_articles(candidates, prefs, "user-1")
        assert len(results) == 2
        # High quality article should rank first
        assert str(results[0].article.id) == high_id
