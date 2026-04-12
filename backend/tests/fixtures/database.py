"""
Database-related test fixtures.

Provides fixtures for database setup, teardown, and common test data.
"""

from typing import Any

import pytest


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing without database connection."""
    from unittest.mock import MagicMock

    client = MagicMock()
    client.table.return_value = client
    client.select.return_value = client
    client.insert.return_value = client
    client.update.return_value = client
    client.delete.return_value = client
    client.eq.return_value = client
    client.execute.return_value = MagicMock(data=[], count=0)

    return client


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Sample user data for testing."""
    return {
        "id": "test-user-123",
        "discord_id": "123456789",
        "username": "testuser",
        "email": "test@example.com",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_article_data() -> dict[str, Any]:
    """Sample article data for testing."""
    return {
        "id": "article-123",
        "title": "Test Article",
        "url": "https://example.com/article",
        "content": "Test content",
        "published_at": "2024-01-01T00:00:00Z",
        "feed_id": "feed-123",
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_feed_data() -> dict[str, Any]:
    """Sample feed data for testing."""
    return {
        "id": "feed-123",
        "name": "Test Feed",
        "url": "https://example.com/feed.xml",
        "category": "technology",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
    }
