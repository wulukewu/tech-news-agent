from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.auth import get_current_user
from app.main import app


class MockResponse:
    def __init__(self, data=None, count=None):
        self.data = data
        self.count = count


class ChainableMock:
    def __init__(self, execute_side_effect=None, execute_return_value=None):
        self.execute_side_effect = execute_side_effect
        self.execute_return_value = execute_return_value
        self._execute_call_count = 0

    def execute(self, *args, **kwargs):
        if self.execute_side_effect:
            if isinstance(self.execute_side_effect, list):
                val = self.execute_side_effect[self._execute_call_count]
                self._execute_call_count += 1
                if isinstance(val, Exception):
                    raise val
                return val
            elif isinstance(self.execute_side_effect, Exception):
                raise self.execute_side_effect
        return self.execute_return_value

    @property
    def not_(self):
        return self

    def __getattr__(self, name):
        return lambda *args, **kwargs: self


class TestArticlesMeFallback:
    """Test cases for the GET /api/articles/me endpoint fallback logic."""

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
    def test_get_my_articles_image_url_fallback(self, mock_supabase_service_class, client):
        """Test fetching articles list when database doesn't have image_url column."""
        mock_service = MagicMock()
        mock_supabase_service_class.return_value = mock_service

        # Mock responses
        mock_subs_resp = MockResponse(data=[{"feed_id": 1}])
        mock_articles_resp = MockResponse(
            data=[
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
        )
        mock_count_resp = MockResponse(count=1)

        # Build mock objects using ChainableMock
        mock_subs_query = ChainableMock(execute_return_value=mock_subs_resp)
        mock_count_query = ChainableMock(execute_return_value=mock_count_resp)

        # This query will fail on the first run, and succeed on the second run (the fallback query)
        mock_articles_query = ChainableMock(
            execute_side_effect=[
                Exception("column articles.image_url does not exist"),
                mock_articles_resp,
            ]
        )

        mock_rl_query = ChainableMock(execute_return_value=MockResponse(data=[]))

        def mock_table_side_effect(table_name):
            if table_name == "user_subscriptions":
                return mock_subs_query
            elif table_name == "articles":
                # Route select to count or articles query depending on count param
                class ArticlesTableMock:
                    def select(self, *args, **kwargs):
                        if "count" in kwargs:
                            return mock_count_query
                        return mock_articles_query

                    def __getattr__(self, name):
                        return lambda *args, **kwargs: self

                return ArticlesTableMock()
            elif table_name == "reading_list":
                return mock_rl_query
            return ChainableMock()

        mock_service.client.table.side_effect = mock_table_side_effect

        response = client.get("/api/articles/me?page=1&page_size=20")

        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert len(json_data["data"]) == 1
        assert json_data["data"][0]["title"] == "Next.js 15 Released"
        assert json_data["data"][0].get("imageUrl") is None
