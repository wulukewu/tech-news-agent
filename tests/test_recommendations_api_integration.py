"""
Integration tests for Recommendations API endpoints

Tests the recommended feeds endpoint with category grouping and subscription status.

**Validates: Requirements 2.1, 4.1**
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from uuid import uuid4

from app.main import app
from app.api.auth import create_access_token


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def auth_token():
    """Create a valid authentication token"""
    user_id = uuid4()
    discord_id = "test_user_recommendations_123"
    
    with patch("app.api.auth.settings") as mock_settings:
        mock_settings.jwt_secret = "test_secret_at_least_32_characters_long"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_expiration_days = 7
        
        token = create_access_token(user_id=user_id, discord_id=discord_id)
        return token


@pytest.fixture
def mock_supabase():
    """Mock Supabase service"""
    with patch("app.services.supabase_service.SupabaseService") as mock_service:
        mock_instance = mock_service.return_value
        mock_instance.get_or_create_user = AsyncMock(return_value=uuid4())
        yield mock_service


@pytest.fixture
def mock_recommendation_service():
    """Mock RecommendationService"""
    with patch("app.api.recommendations.RecommendationService") as mock_service:
        yield mock_service


def test_get_recommended_feeds_unauthorized(client):
    """
    Test getting recommended feeds without authentication
    
    **Validates: JWT authentication requirement**
    """
    response = client.get("/api/feeds/recommended")
    
    # Should return 401 Unauthorized
    assert response.status_code == 401


def test_get_recommended_feeds_success(client, auth_token, mock_supabase, mock_recommendation_service):
    """
    Test successfully getting recommended feeds
    
    **Validates: Requirements 2.1, 4.1**
    """
    from app.schemas.recommendation import RecommendedFeed
    
    # Mock recommended feeds
    mock_feeds = [
        RecommendedFeed(
            id=uuid4(),
            name="Hacker News",
            url="https://news.ycombinator.com/rss",
            category="Tech News",
            description="最熱門的科技新聞和討論",
            is_recommended=True,
            recommendation_priority=100,
            is_subscribed=False
        ),
        RecommendedFeed(
            id=uuid4(),
            name="OpenAI Blog",
            url="https://openai.com/blog/rss",
            category="AI",
            description="OpenAI 官方部落格",
            is_recommended=True,
            recommendation_priority=95,
            is_subscribed=True
        ),
        RecommendedFeed(
            id=uuid4(),
            name="CSS-Tricks",
            url="https://css-tricks.com/feed/",
            category="Web Development",
            description="前端開發技巧和教學",
            is_recommended=True,
            recommendation_priority=90,
            is_subscribed=False
        )
    ]
    
    mock_instance = mock_recommendation_service.return_value
    mock_instance.get_recommended_feeds = AsyncMock(return_value=mock_feeds)
    
    response = client.get(
        "/api/feeds/recommended",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Should return recommended feeds
    data = response.json()
    assert "feeds" in data
    assert "grouped_by_category" in data
    assert "total_count" in data
    
    # Should have 3 feeds
    assert data["total_count"] == 3
    assert len(data["feeds"]) == 3
    
    # Should be grouped by category
    assert "Tech News" in data["grouped_by_category"]
    assert "AI" in data["grouped_by_category"]
    assert "Web Development" in data["grouped_by_category"]
    
    # Each category should have correct feeds
    assert len(data["grouped_by_category"]["Tech News"]) == 1
    assert len(data["grouped_by_category"]["AI"]) == 1
    assert len(data["grouped_by_category"]["Web Development"]) == 1
    
    # Should include subscription status
    ai_feed = data["grouped_by_category"]["AI"][0]
    assert ai_feed["is_subscribed"] is True
    
    tech_news_feed = data["grouped_by_category"]["Tech News"][0]
    assert tech_news_feed["is_subscribed"] is False


def test_get_recommended_feeds_empty(client, auth_token, mock_supabase, mock_recommendation_service):
    """
    Test getting recommended feeds when none exist
    
    **Validates: Empty state handling**
    """
    mock_instance = mock_recommendation_service.return_value
    mock_instance.get_recommended_feeds = AsyncMock(return_value=[])
    
    response = client.get(
        "/api/feeds/recommended",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Should return empty lists
    data = response.json()
    assert data["total_count"] == 0
    assert len(data["feeds"]) == 0
    assert len(data["grouped_by_category"]) == 0


def test_get_recommended_feeds_sorted_by_priority(client, auth_token, mock_supabase, mock_recommendation_service):
    """
    Test that recommended feeds are sorted by priority
    
    **Validates: Requirements 12.1, 12.4**
    """
    from app.schemas.recommendation import RecommendedFeed
    
    # Mock feeds with different priorities
    mock_feeds = [
        RecommendedFeed(
            id=uuid4(),
            name="High Priority Feed",
            url="https://example.com/high",
            category="AI",
            description="High priority",
            is_recommended=True,
            recommendation_priority=100,
            is_subscribed=False
        ),
        RecommendedFeed(
            id=uuid4(),
            name="Medium Priority Feed",
            url="https://example.com/medium",
            category="AI",
            description="Medium priority",
            is_recommended=True,
            recommendation_priority=50,
            is_subscribed=False
        ),
        RecommendedFeed(
            id=uuid4(),
            name="Low Priority Feed",
            url="https://example.com/low",
            category="AI",
            description="Low priority",
            is_recommended=True,
            recommendation_priority=10,
            is_subscribed=False
        )
    ]
    
    mock_instance = mock_recommendation_service.return_value
    mock_instance.get_recommended_feeds = AsyncMock(return_value=mock_feeds)
    
    response = client.get(
        "/api/feeds/recommended",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Feeds should be in priority order (highest first)
    data = response.json()
    feeds = data["feeds"]
    assert feeds[0]["recommendation_priority"] == 100
    assert feeds[1]["recommendation_priority"] == 50
    assert feeds[2]["recommendation_priority"] == 10


def test_error_handling_service_failure(client, auth_token, mock_supabase, mock_recommendation_service):
    """
    Test error handling when RecommendationService fails
    
    **Validates: Error handling**
    """
    from app.services.recommendation_service import RecommendationServiceError
    
    mock_instance = mock_recommendation_service.return_value
    mock_instance.get_recommended_feeds = AsyncMock(
        side_effect=RecommendationServiceError("Database error")
    )
    
    response = client.get(
        "/api/feeds/recommended",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should return 500 Internal Server Error
    assert response.status_code == 500
    
    # Should return user-friendly error message
    data = response.json()
    assert "detail" in data
    assert "無法取得推薦來源" in data["detail"]


def test_recommended_feeds_with_multiple_categories(client, auth_token, mock_supabase, mock_recommendation_service):
    """
    Test recommended feeds with multiple categories
    
    **Validates: Category grouping functionality**
    """
    from app.schemas.recommendation import RecommendedFeed
    
    # Create feeds across multiple categories
    categories = ["AI", "Web Development", "Security", "DevOps", "Mobile"]
    mock_feeds = []
    
    for i, category in enumerate(categories):
        for j in range(2):  # 2 feeds per category
            mock_feeds.append(RecommendedFeed(
                id=uuid4(),
                name=f"{category} Feed {j+1}",
                url=f"https://example.com/{category.lower()}/{j}",
                category=category,
                description=f"{category} feed description",
                is_recommended=True,
                recommendation_priority=100 - (i * 10) - j,
                is_subscribed=False
            ))
    
    mock_instance = mock_recommendation_service.return_value
    mock_instance.get_recommended_feeds = AsyncMock(return_value=mock_feeds)
    
    response = client.get(
        "/api/feeds/recommended",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Should have all categories
    data = response.json()
    assert len(data["grouped_by_category"]) == 5
    
    # Each category should have 2 feeds
    for category in categories:
        assert category in data["grouped_by_category"]
        assert len(data["grouped_by_category"][category]) == 2
    
    # Total count should be correct
    assert data["total_count"] == 10
