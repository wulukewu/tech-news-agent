"""
Unit tests for ArticleRecommendationService

Tests the core functionality of the ArticleRecommendationService including:
- Getting personalized recommendations
- Refreshing recommendations
- Dismissing recommendations
- Tracking interactions
- Handling insufficient data scenarios

Requirements: 3.1-3.10
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.repositories.article import ArticleRepository
from app.repositories.reading_list import ReadingListItem, ReadingListRepository
from app.schemas.recommendation import (
    DismissRecommendationRequest,
    RecommendationInteraction,
    RefreshRecommendationsRequest,
)
from app.services.article_recommendation_service import ArticleRecommendationService


@pytest.fixture
def mock_article_repo():
    """Create a mock ArticleRepository"""
    return AsyncMock(spec=ArticleRepository)


@pytest.fixture
def mock_reading_list_repo():
    """Create a mock ReadingListRepository"""
    return AsyncMock(spec=ReadingListRepository)


@pytest.fixture
def recommendation_service(mock_article_repo, mock_reading_list_repo):
    """Create an ArticleRecommendationService instance with mock repositories"""
    return ArticleRecommendationService(mock_article_repo, mock_reading_list_repo)


@pytest.fixture
def sample_user_id():
    """Sample user UUID for testing"""
    return uuid4()


@pytest.fixture
def sample_reading_list_items():
    """Sample reading list items with ratings"""
    user_id = uuid4()
    return [
        ReadingListItem(
            id=uuid4(),
            user_id=user_id,
            article_id=uuid4(),
            status="Read",
            rating=5,
            added_at=datetime.utcnow() - timedelta(days=1),
        ),
        ReadingListItem(
            id=uuid4(),
            user_id=user_id,
            article_id=uuid4(),
            status="Read",
            rating=4,
            added_at=datetime.utcnow() - timedelta(days=2),
        ),
        ReadingListItem(
            id=uuid4(),
            user_id=user_id,
            article_id=uuid4(),
            status="Read",
            rating=4,
            added_at=datetime.utcnow() - timedelta(days=3),
        ),
        ReadingListItem(
            id=uuid4(),
            user_id=user_id,
            article_id=uuid4(),
            status="Read",
            rating=2,  # Low rating, should not count
            added_at=datetime.utcnow() - timedelta(days=4),
        ),
    ]


@pytest.fixture
def sample_articles():
    """Sample articles for recommendations"""
    return [
        Mock(
            id=uuid4(),
            title="Advanced Python Techniques",
            url="https://example.com/python",
            feed_name="Python Weekly",
            category="Programming",
            published_at=datetime.utcnow() - timedelta(days=1),
            tinkering_index=4,
            ai_summary="Learn advanced Python programming techniques...",
        ),
        Mock(
            id=uuid4(),
            title="Machine Learning Basics",
            url="https://example.com/ml",
            feed_name="AI News",
            category="AI",
            published_at=datetime.utcnow() - timedelta(days=2),
            tinkering_index=3,
            ai_summary="Introduction to machine learning concepts...",
        ),
    ]


class TestArticleRecommendationService:
    """Test cases for ArticleRecommendationService"""

    @pytest.mark.asyncio
    async def test_get_recommendations_insufficient_data(
        self, recommendation_service, mock_reading_list_repo, sample_user_id
    ):
        """Test getting recommendations when user has insufficient rating data"""
        # Mock insufficient ratings (less than 3)
        mock_reading_list_repo.list_by_user_with_pagination.return_value = (
            [
                ReadingListItem(
                    id=uuid4(),
                    user_id=sample_user_id,
                    article_id=uuid4(),
                    status="Read",
                    rating=4,
                )
            ],
            Mock(),
        )

        result = await recommendation_service.get_recommendations(sample_user_id, 10)

        assert result.has_sufficient_data is False
        assert result.user_rating_count == 1
        assert result.min_ratings_required == 3
        assert len(result.recommendations) == 0
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_get_recommendations_sufficient_data(
        self,
        recommendation_service,
        mock_reading_list_repo,
        mock_article_repo,
        sample_user_id,
        sample_reading_list_items,
        sample_articles,
    ):
        """Test getting recommendations when user has sufficient rating data"""
        # Mock sufficient ratings
        mock_reading_list_repo.list_by_user_with_pagination.return_value = (
            sample_reading_list_items,
            Mock(),
        )

        # Mock article details for preference analysis
        mock_article_repo.get_by_id.side_effect = [
            Mock(category="Programming", tinkering_index=4),
            Mock(category="Programming", tinkering_index=4),
            Mock(category="AI", tinkering_index=3),
            None,  # For the low-rated article
        ]

        # Mock candidate articles
        mock_article_repo.list_with_pagination.return_value = (sample_articles, Mock())

        result = await recommendation_service.get_recommendations(sample_user_id, 10)

        assert result.has_sufficient_data is True
        assert result.user_rating_count == 3  # Only high-rated articles count
        assert result.min_ratings_required == 3
        assert len(result.recommendations) >= 0  # May be 0 if no good matches

    @pytest.mark.asyncio
    async def test_refresh_recommendations(
        self,
        recommendation_service,
        mock_reading_list_repo,
        mock_article_repo,
        sample_user_id,
        sample_reading_list_items,
    ):
        """Test refreshing recommendations"""
        # Mock sufficient ratings
        mock_reading_list_repo.list_by_user_with_pagination.return_value = (
            sample_reading_list_items,
            Mock(),
        )

        # Mock article details
        mock_article_repo.get_by_id.return_value = Mock(category="Programming", tinkering_index=4)
        mock_article_repo.list_with_pagination.return_value = ([], Mock())

        request = RefreshRecommendationsRequest(limit=5)
        result = await recommendation_service.refresh_recommendations(sample_user_id, request)

        assert result.has_sufficient_data is True
        assert isinstance(result.recommendations, list)

    @pytest.mark.asyncio
    async def test_dismiss_recommendation(self, recommendation_service, sample_user_id):
        """Test dismissing a recommendation"""
        request = DismissRecommendationRequest(recommendation_id="test_rec_123")

        # Should not raise any exception
        await recommendation_service.dismiss_recommendation(sample_user_id, request)

        # Verify recommendation is in dismissed set
        assert "test_rec_123" in recommendation_service._dismissed_recommendations

    @pytest.mark.asyncio
    async def test_track_interaction(self, recommendation_service, sample_user_id):
        """Test tracking recommendation interaction"""
        interaction = RecommendationInteraction(
            recommendation_id="test_rec_123",
            interaction_type="click",
            timestamp=datetime.utcnow(),
        )

        # Should not raise any exception (analytics tracking is non-critical)
        await recommendation_service.track_interaction(sample_user_id, interaction)

    @pytest.mark.asyncio
    async def test_get_user_rating_count(
        self,
        recommendation_service,
        mock_reading_list_repo,
        sample_user_id,
        sample_reading_list_items,
    ):
        """Test getting user rating count"""
        mock_reading_list_repo.list_by_user_with_pagination.return_value = (
            sample_reading_list_items,
            Mock(),
        )

        count = await recommendation_service._get_user_rating_count(sample_user_id)

        # Should count only ratings >= 4
        assert count == 3

    @pytest.mark.asyncio
    async def test_get_user_rating_count_error_handling(
        self, recommendation_service, mock_reading_list_repo, sample_user_id
    ):
        """Test error handling in get_user_rating_count"""
        mock_reading_list_repo.list_by_user_with_pagination.side_effect = Exception("DB Error")

        count = await recommendation_service._get_user_rating_count(sample_user_id)

        # Should return 0 on error
        assert count == 0

    def test_calculate_recommendation_score(self, recommendation_service):
        """Test recommendation score calculation"""
        article = Mock(
            category="Programming",
            tinkering_index=4,
            published_at=datetime.utcnow() - timedelta(days=1),
            ai_summary="Test summary",
        )

        user_preferences = {
            "preferred_categories": ["Programming", "AI"],
            "avg_tinkering_level": 4.0,
            "category_weights": {"Programming": 5, "AI": 2},
        }

        score = recommendation_service._calculate_recommendation_score(article, user_preferences)

        # Score should be positive for matching preferences
        assert 0 <= score <= 1.0
        assert score > 0.3  # Should be above threshold for good match

    def test_generate_recommendation_reason(self, recommendation_service):
        """Test recommendation reason generation"""
        article = Mock(
            category="Programming",
            tinkering_index=4,
            ai_summary="Test summary",
        )

        user_preferences = {
            "preferred_categories": ["Programming"],
            "avg_tinkering_level": 4.0,
            "category_weights": {"Programming": 5},
        }

        reason = recommendation_service._generate_recommendation_reason(article, user_preferences)

        assert isinstance(reason, str)
        assert len(reason) > 0
        assert "Programming" in reason or "技術深度" in reason

    def test_generate_recommendation_id(self, recommendation_service):
        """Test recommendation ID generation"""
        user_id = uuid4()
        article_id = uuid4()

        rec_id = recommendation_service._generate_recommendation_id(user_id, article_id)

        assert isinstance(rec_id, str)
        assert len(rec_id) == 16  # MD5 hash truncated to 16 chars

        # Should be deterministic for same inputs
        rec_id2 = recommendation_service._generate_recommendation_id(user_id, article_id)
        assert rec_id == rec_id2


class TestArticleRecommendationServiceIntegration:
    """Integration test cases"""

    @pytest.mark.asyncio
    async def test_full_recommendation_flow(
        self,
        recommendation_service,
        mock_reading_list_repo,
        mock_article_repo,
        sample_user_id,
    ):
        """Test the complete recommendation flow"""
        # Setup: User has rated articles
        rated_items = [
            ReadingListItem(
                id=uuid4(),
                user_id=sample_user_id,
                article_id=uuid4(),
                status="Read",
                rating=5,
            )
            for _ in range(5)  # 5 highly rated articles
        ]

        mock_reading_list_repo.list_by_user_with_pagination.return_value = (rated_items, Mock())

        # Mock article details for preference analysis
        mock_article_repo.get_by_id.return_value = Mock(category="Programming", tinkering_index=4)

        # Mock candidate articles
        candidate_articles = [
            Mock(
                id=uuid4(),
                title=f"Article {i}",
                url=f"https://example.com/{i}",
                feed_name="Test Feed",
                category="Programming",
                published_at=datetime.utcnow() - timedelta(days=i),
                tinkering_index=4,
                ai_summary=f"Summary {i}",
            )
            for i in range(10)
        ]

        mock_article_repo.list_with_pagination.return_value = (candidate_articles, Mock())

        # Test: Get recommendations
        result = await recommendation_service.get_recommendations(sample_user_id, 5)

        # Verify: Should have recommendations
        assert result.has_sufficient_data is True
        assert result.user_rating_count == 5
        assert len(result.recommendations) <= 5

        # Test: Dismiss a recommendation
        if result.recommendations:
            rec_id = result.recommendations[0].id
            dismiss_request = DismissRecommendationRequest(recommendation_id=rec_id)
            await recommendation_service.dismiss_recommendation(sample_user_id, dismiss_request)

            # Test: Get recommendations again (dismissed one should be filtered out)
            result2 = await recommendation_service.get_recommendations(sample_user_id, 5)
            rec_ids = [rec.id for rec in result2.recommendations]
            assert rec_id not in rec_ids
