from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestArticlesPublicAPI:
    """Test cases for the public recommended articles API endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch("app.api.articles.SupabaseService")
    def test_get_public_recommended_articles_success(self, mock_supabase_service_class, client):
        """Test fetching public recommended articles successfully."""
        from app.api.articles import PUBLIC_RECOMMENDED_CACHE

        # Reset cache for test isolation
        PUBLIC_RECOMMENDED_CACHE["data"] = []
        PUBLIC_RECOMMENDED_CACHE["updated_at"] = 0.0
        PUBLIC_RECOMMENDED_CACHE["is_updating"] = False

        # Setup mock Supabase client response
        mock_service = MagicMock()
        mock_supabase_service_class.return_value = mock_service

        mock_execute_result = MagicMock()
        # Mock articles table select response
        mock_execute_result.data = [
            {
                "id": "c6264ff4-bf91-4df2-841f-824c084cf734",
                "title": "Next.js 15 Released",
                "url": "https://nextjs.org/blog/next-15",
                "published_at": "2026-05-29T03:00:00+00:00",
                "tinkering_index": 5,
                "ai_summary": "Next.js 15 comes with amazing features.",
                "actionable_takeaway": "Upgrade to Next.js 15 for faster loading.",
                "feeds": {"name": "Next.js Blog", "category": "Frontend"},
            }
        ]

        # Configure mock_service.client.table().select()...execute()
        mock_table = mock_service.client.table
        mock_select = mock_table.return_value.select
        mock_not_ = mock_select.return_value.not_
        mock_is_ = mock_not_.is_
        mock_order = mock_is_.return_value.order
        mock_limit = mock_order.return_value.limit
        mock_limit.return_value.execute.return_value = mock_execute_result

        # Request public recommended articles
        response = client.get("/api/articles/public/recommended?limit=3")

        # Assertions
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert len(json_data["data"]) == 1
        article = json_data["data"][0]
        assert article["title"] == "Next.js 15 Released"
        assert article["feed_name"] == "Next.js Blog"
        assert article["category"] == "Frontend"
        assert article["tinkering_index"] == 5
        assert article["is_in_reading_list"] is False

    @patch("app.api.articles.SupabaseService")
    def test_get_public_recommended_articles_caching(self, mock_supabase_service_class, client):
        """Test that caching returns cached response and refreshes correctly in background."""
        import time

        from app.api.articles import PUBLIC_RECOMMENDED_CACHE

        # Reset cache for test isolation
        PUBLIC_RECOMMENDED_CACHE["data"] = []
        PUBLIC_RECOMMENDED_CACHE["updated_at"] = 0.0
        PUBLIC_RECOMMENDED_CACHE["is_updating"] = False

        # Setup mock Supabase client response
        mock_service = MagicMock()
        mock_supabase_service_class.return_value = mock_service

        mock_execute_result_1 = MagicMock()
        mock_execute_result_1.data = [
            {
                "id": "c6264ff4-bf91-4df2-841f-824c084cf734",
                "title": "First Version",
                "url": "https://example.com/1",
                "published_at": "2026-05-29T03:00:00+00:00",
                "tinkering_index": 5,
                "ai_summary": "First Summary",
                "actionable_takeaway": "Takeaway 1",
                "feeds": {"name": "Example", "category": "Tech"},
            }
        ]

        mock_table = mock_service.client.table
        mock_select = mock_table.return_value.select
        mock_not_ = mock_select.return_value.not_
        mock_is_ = mock_not_.is_
        mock_order = mock_is_.return_value.order
        mock_limit = mock_order.return_value.limit
        mock_limit.return_value.execute.return_value = mock_execute_result_1

        # 1. Cold start: First request hits database
        response_1 = client.get("/api/articles/public/recommended?limit=3")
        assert response_1.status_code == 200
        data_1 = response_1.json()["data"]
        assert len(data_1) == 1
        assert data_1[0]["title"] == "First Version"
        assert mock_limit.return_value.execute.call_count == 1

        # 2. Warm cache request (within 60 seconds): Returns cached data instantly without calling database
        response_2 = client.get("/api/articles/public/recommended?limit=3")
        assert response_2.status_code == 200
        data_2 = response_2.json()["data"]
        assert data_2[0]["title"] == "First Version"
        # Database execute call count should still be 1 because it loaded from cache
        assert mock_limit.return_value.execute.call_count == 1

        # 3. Expired cache: Simulate cache expiration (> 60 seconds)
        PUBLIC_RECOMMENDED_CACHE["updated_at"] = time.time() - 65.0

        # Change mock response for second DB fetch (revalidation)
        mock_execute_result_2 = MagicMock()
        mock_execute_result_2.data = [
            {
                "id": "c6264ff4-bf91-4df2-841f-824c084cf734",
                "title": "Second Version",
                "url": "https://example.com/2",
                "published_at": "2026-05-29T03:00:00+00:00",
                "tinkering_index": 5,
                "ai_summary": "Second Summary",
                "actionable_takeaway": "Takeaway 2",
                "feeds": {"name": "Example", "category": "Tech"},
            }
        ]
        # We need mock_limit.return_value.execute to return the new data on subsequent calls
        mock_limit.return_value.execute.return_value = mock_execute_result_2

        # Expired cache request should return stale cache (First Version) instantly,
        # but trigger a background task to refresh the cache.
        response_3 = client.get("/api/articles/public/recommended?limit=3")
        assert response_3.status_code == 200
        data_3 = response_3.json()["data"]
        # Instant response must be the STALE data (First Version)
        assert data_3[0]["title"] == "First Version"

        # Give background asyncio task a tiny fraction of a second to run and complete
        time.sleep(0.1)

        # Now cache should be updated with Second Version, and future requests will see it
        response_4 = client.get("/api/articles/public/recommended?limit=3")
        assert response_4.status_code == 200
        data_4 = response_4.json()["data"]
        assert data_4[0]["title"] == "Second Version"
