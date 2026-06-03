from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.auth import get_current_user
from app.main import app


class TestArticlesDetailAPI:
    """Test cases for the GET /api/articles/{article_id} endpoint."""

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Override auth dependency for all tests."""
        app.dependency_overrides[get_current_user] = lambda: {"user_id": "test_user_123"}
        yield
        app.dependency_overrides.pop(get_current_user, None)

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch("app.api.articles.SupabaseService")
    def test_get_article_success(self, mock_supabase_service_class, client):
        """Test fetching a single article by ID successfully."""
        mock_service = MagicMock()
        mock_supabase_service_class.return_value = mock_service

        article_id = "c6264ff4-bf91-4df2-841f-824c084cf734"

        # Mock articles table select response
        mock_article_execute = MagicMock()
        mock_article_execute.data = [
            {
                "id": article_id,
                "title": "Next.js 15 Released",
                "url": "https://nextjs.org/blog/next-15",
                "published_at": "2026-05-29T03:00:00+00:00",
                "tinkering_index": 5,
                "ai_summary": "Next.js 15 comes with amazing features.",
                "actionable_takeaway": "Upgrade to Next.js 15 for faster loading.",
                "feeds": {"name": "Next.js Blog", "category": "Frontend"},
            }
        ]

        # Mock reading list response
        mock_reading_list_execute = MagicMock()
        mock_reading_list_execute.data = [{"status": "unread"}]

        # Set up mock execute return values using side effects based on table name
        mock_table = mock_service.client.table

        # Prepare mock builders
        mock_execute_1 = MagicMock()
        mock_execute_1.execute.return_value = mock_article_execute
        mock_eq_1 = MagicMock()
        mock_eq_1.eq.return_value = mock_execute_1
        mock_select_1 = MagicMock()
        mock_select_1.select.return_value = mock_eq_1

        mock_eq_2 = MagicMock()
        mock_eq_2.eq.return_value = mock_eq_2
        mock_eq_2.execute.return_value = mock_reading_list_execute
        mock_select_2 = MagicMock()
        mock_select_2.select.return_value = mock_eq_2

        def mock_table_side_effect(table_name):
            if table_name == "articles":
                return mock_select_1
            elif table_name == "reading_list":
                return mock_select_2
            return MagicMock()

        mock_table.side_effect = mock_table_side_effect

        response = client.get(f"/api/articles/{article_id}")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["title"] == "Next.js 15 Released"
        assert json_data["data"]["feedName"] == "Next.js Blog"
        assert json_data["data"]["category"] == "Frontend"
        assert json_data["data"]["tinkeringIndex"] == 5
        assert json_data["data"]["isInReadingList"] is True
        assert json_data["data"]["readStatus"] == "unread"

    @patch("app.api.articles.SupabaseService")
    def test_get_article_not_found(self, mock_supabase_service_class, client):
        """Test fetching a single article that does not exist."""
        mock_service = MagicMock()
        mock_supabase_service_class.return_value = mock_service

        article_id = "c6264ff4-bf91-4df2-841f-824c084cf734"

        # Mock articles table select response (empty)
        mock_article_execute = MagicMock()
        mock_article_execute.data = []

        mock_table = mock_service.client.table
        mock_execute_1 = MagicMock()
        mock_execute_1.execute.return_value = mock_article_execute
        mock_eq_1 = MagicMock()
        mock_eq_1.eq.return_value = mock_execute_1
        mock_select_1 = MagicMock()
        mock_select_1.select.return_value = mock_eq_1

        mock_table.return_value = mock_select_1

        response = client.get(f"/api/articles/{article_id}")

        assert response.status_code == 404
        assert response.json()["error"] == "Article not found"

    @patch("app.api.articles.SupabaseService")
    def test_get_article_image_url_fallback(self, mock_supabase_service_class, client):
        """Test fetching a single article by ID when database doesn't have image_url column."""
        mock_service = MagicMock()
        mock_supabase_service_class.return_value = mock_service

        article_id = "c6264ff4-bf91-4df2-841f-824c084cf734"

        # Mock articles table select response
        mock_article_execute = MagicMock()
        mock_article_execute.data = [
            {
                "id": article_id,
                "title": "Next.js 15 Released",
                "url": "https://nextjs.org/blog/next-15",
                "published_at": "2026-05-29T03:00:00+00:00",
                "tinkering_index": 5,
                "ai_summary": "Next.js 15 comes with amazing features.",
                "actionable_takeaway": "Upgrade to Next.js 15 for faster loading.",
                "feeds": {"name": "Next.js Blog", "category": "Frontend"},
            }
        ]

        # The first call to execute() raises exception, the second call returns mock_article_execute
        mock_eq = MagicMock()
        mock_eq.execute.side_effect = [
            Exception("column articles.image_url does not exist"),
            mock_article_execute,
        ]

        mock_eq.eq.return_value = mock_eq
        mock_select = MagicMock()
        mock_select.select.return_value = mock_eq
        mock_service.client.table.return_value = mock_select

        # Mock reading list response
        mock_reading_list_execute = MagicMock()
        mock_reading_list_execute.data = []
        mock_reading_list_eq = MagicMock()
        mock_reading_list_eq.eq.return_value = mock_reading_list_eq
        mock_reading_list_eq.execute.return_value = mock_reading_list_execute
        mock_reading_list_select = MagicMock()
        mock_reading_list_select.select.return_value = mock_reading_list_eq

        def mock_table_side_effect(table_name):
            if table_name == "articles":
                return mock_select
            elif table_name == "reading_list":
                return mock_reading_list_select
            return MagicMock()

        mock_service.client.table.side_effect = mock_table_side_effect

        response = client.get(f"/api/articles/{article_id}")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["title"] == "Next.js 15 Released"
        assert json_data["data"].get("image_url") is None
