"""
Integration tests for recommendations API endpoints

Tests the complete flow from API endpoints to services and repositories.
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {"user_id": "test_user_123", "discord_id": "discord_123", "username": "testuser"}


class TestRecommendationsAPI:
    """Integration tests for recommendations API"""

    @patch("app.api.recommendations.get_current_user")
    @patch("app.api.recommendations.SupabaseService")
    @patch("app.api.recommendations.ArticleRecommendationService")
    def test_get_recommendations_success(
        self, mock_service_class, mock_supabase_class, mock_get_user, client, mock_user
    ):
        """Test successful retrieval of recommendations"""
        # Setup mocks
        mock_get_user.return_value = mock_user

        mock_supabase = Mock()
        mock_supabase.get_or_create_user.return_value = uuid4()
        mock_supabase_class.return_value = mock_supabase

        mock_service = AsyncMock()
        mock_response = Mock()
        mock_response.recommendations = []
        mock_response.total_count = 0
        mock_response.has_sufficient_data = False
        mock_response.min_ratings_required = 3
        mock_response.user_rating_count = 1

        mock_service.get_recommendations.return_value = mock_response
        mock_service_class.return_value = mock_service

        # Make request
        response = client.get("/api/v1/recommendations")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["total_count"] == 0
        assert data["data"]["has_sufficient_data"] is False

    @patch("app.api.recommendations.get_current_user")
    @patch("app.api.recommendations.SupabaseService")
    @patch("app.api.recommendations.ArticleRecommendationService")
    def test_refresh_recommendations_success(
        self, mock_service_class, mock_supabase_class, mock_get_user, client, mock_user
    ):
        """Test successful refresh of recommendations"""
        # Setup mocks
        mock_get_user.return_value = mock_user

        mock_supabase = Mock()
        mock_supabase.get_or_create_user.return_value = uuid4()
        mock_supabase_class.return_value = mock_supabase

        mock_service = AsyncMock()
        mock_response = Mock()
        mock_response.recommendations = []
        mock_response.total_count = 0
        mock_response.has_sufficient_data = True
        mock_response.min_ratings_required = 3
        mock_response.user_rating_count = 5

        mock_service.refresh_recommendations.return_value = mock_response
        mock_service_class.return_value = mock_service

        # Make request
        response = client.post("/api/v1/recommendations/refresh", json={"limit": 10})

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["has_sufficient_data"] is True

    @patch("app.api.recommendations.get_current_user")
    @patch("app.api.recommendations.SupabaseService")
    @patch("app.api.recommendations.ArticleRecommendationService")
    def test_dismiss_recommendation_success(
        self, mock_service_class, mock_supabase_class, mock_get_user, client, mock_user
    ):
        """Test successful dismissal of recommendation"""
        # Setup mocks
        mock_get_user.return_value = mock_user

        mock_supabase = Mock()
        mock_supabase.get_or_create_user.return_value = uuid4()
        mock_supabase_class.return_value = mock_supabase

        mock_service = AsyncMock()
        mock_service.dismiss_recommendation.return_value = None
        mock_service_class.return_value = mock_service

        # Make request
        response = client.post(
            "/api/v1/recommendations/dismiss", json={"recommendationId": "test_rec_123"}
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "message" in data["data"]

    @patch("app.api.recommendations.get_current_user")
    @patch("app.api.recommendations.SupabaseService")
    @patch("app.api.recommendations.ArticleRecommendationService")
    def test_track_interaction_success(
        self, mock_service_class, mock_supabase_class, mock_get_user, client, mock_user
    ):
        """Test successful tracking of recommendation interaction"""
        # Setup mocks
        mock_get_user.return_value = mock_user

        mock_supabase = Mock()
        mock_supabase.get_or_create_user.return_value = uuid4()
        mock_supabase_class.return_value = mock_supabase

        mock_service = AsyncMock()
        mock_service.track_interaction.return_value = None
        mock_service_class.return_value = mock_service

        # Make request
        response = client.post(
            "/api/v1/recommendations/track",
            json={
                "recommendationId": "test_rec_123",
                "interaction_type": "click",
                "timestamp": "2024-01-01T00:00:00Z",
            },
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "message" in data["data"]

    def test_get_recommendations_unauthorized(self, client):
        """Test recommendations endpoint without authentication"""
        response = client.get("/api/v1/recommendations")

        # Should return 401 or 403 (depending on auth implementation)
        assert response.status_code in [401, 403]

    @patch("app.api.recommendations.get_current_user")
    @patch("app.api.recommendations.SupabaseService")
    @patch("app.api.recommendations.ArticleRecommendationService")
    def test_get_recommendations_service_error(
        self, mock_service_class, mock_supabase_class, mock_get_user, client, mock_user
    ):
        """Test handling of service errors"""
        # Setup mocks
        mock_get_user.return_value = mock_user

        mock_supabase = Mock()
        mock_supabase.get_or_create_user.return_value = uuid4()
        mock_supabase_class.return_value = mock_supabase

        mock_service = AsyncMock()
        mock_service.get_recommendations.side_effect = Exception("Service error")
        mock_service_class.return_value = mock_service

        # Make request
        response = client.get("/api/v1/recommendations")

        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "系統錯誤" in data["detail"]
