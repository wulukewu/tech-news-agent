"""
Unit tests for RSSService.fetch_new_articles method
Task 2.1: 實作 fetch_new_articles 方法

Tests cover:
- Fetching articles and filtering out existing ones
- Handling empty article lists
- Handling database check failures
- Logging statistics
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.schemas.article import ArticleSchema, RSSSource
from app.services.rss_service import RSSService


def make_article(url: str, title: str = "Test Article") -> ArticleSchema:
    """Helper to create a test ArticleSchema"""
    return ArticleSchema(
        title=title,
        url=url,
        feed_id=uuid4(),
        feed_name="Test Feed",
        category="AI",
        published_at=datetime.now(UTC),
    )


def make_source(
    name: str = "TestFeed", url: str = "https://example.com/feed.xml", category: str = "AI"
) -> RSSSource:
    """Helper to create a test RSSSource"""
    return RSSSource(name=name, url=url, category=category)


class TestFetchNewArticles:
    """測試 fetch_new_articles 方法"""

    @pytest.mark.asyncio
    async def test_returns_only_new_articles(self):
        """fetch_new_articles should filter out articles that already exist in database"""
        # Arrange
        service = RSSService(days_to_fetch=7)
        sources = [make_source()]

        # Mock articles: 3 total, 1 existing, 2 new
        article1 = make_article("https://example.com/article1", "Article 1")
        article2 = make_article("https://example.com/article2", "Article 2")
        article3 = make_article("https://example.com/article3", "Article 3")

        # Mock fetch_all_feeds to return 3 articles
        with patch.object(
            service, "fetch_all_feeds", AsyncMock(return_value=[article1, article2, article3])
        ):
            # Mock supabase service: article2 exists, others don't
            mock_supabase = AsyncMock()
            mock_supabase.check_article_exists = AsyncMock(
                side_effect=lambda url: url == "https://example.com/article2"
            )

            # Act
            result = await service.fetch_new_articles(sources, mock_supabase)

        # Assert
        assert len(result) == 2
        assert article1 in result
        assert article3 in result
        assert article2 not in result

        # Verify check_article_exists was called for each article
        assert mock_supabase.check_article_exists.call_count == 3

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_articles_fetched(self):
        """fetch_new_articles should return empty list when fetch_all_feeds returns nothing"""
        # Arrange
        service = RSSService(days_to_fetch=7)
        sources = [make_source()]

        # Mock fetch_all_feeds to return empty list
        with patch.object(service, "fetch_all_feeds", AsyncMock(return_value=[])):
            mock_supabase = AsyncMock()

            # Act
            result = await service.fetch_new_articles(sources, mock_supabase)

        # Assert
        assert result == []
        # Should not call check_article_exists when no articles
        mock_supabase.check_article_exists.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_all_articles_when_none_exist(self):
        """fetch_new_articles should return all articles when none exist in database"""
        # Arrange
        service = RSSService(days_to_fetch=7)
        sources = [make_source()]

        article1 = make_article("https://example.com/article1", "Article 1")
        article2 = make_article("https://example.com/article2", "Article 2")

        # Mock fetch_all_feeds to return 2 articles
        with patch.object(service, "fetch_all_feeds", AsyncMock(return_value=[article1, article2])):
            # Mock supabase service: no articles exist
            mock_supabase = AsyncMock()
            mock_supabase.check_article_exists = AsyncMock(return_value=False)

            # Act
            result = await service.fetch_new_articles(sources, mock_supabase)

        # Assert
        assert len(result) == 2
        assert article1 in result
        assert article2 in result

    @pytest.mark.asyncio
    async def test_continues_on_check_failure(self):
        """fetch_new_articles should continue processing when check_article_exists fails for one article"""
        # Arrange
        service = RSSService(days_to_fetch=7)
        sources = [make_source()]

        article1 = make_article("https://example.com/article1", "Article 1")
        article2 = make_article("https://example.com/article2", "Article 2")
        article3 = make_article("https://example.com/article3", "Article 3")

        # Mock fetch_all_feeds to return 3 articles
        with patch.object(
            service, "fetch_all_feeds", AsyncMock(return_value=[article1, article2, article3])
        ):
            # Mock supabase service: article2 check fails, others succeed
            mock_supabase = AsyncMock()

            async def check_side_effect(url):
                if url == "https://example.com/article2":
                    raise Exception("Database error")
                return False

            mock_supabase.check_article_exists = AsyncMock(side_effect=check_side_effect)

            # Act
            result = await service.fetch_new_articles(sources, mock_supabase)

        # Assert - should include all 3 articles (failed check assumes new)
        assert len(result) == 3
        assert article1 in result
        assert article2 in result  # Included despite check failure
        assert article3 in result

    @pytest.mark.asyncio
    async def test_logs_statistics(self):
        """fetch_new_articles should log total fetched, existing, and new counts"""
        # Arrange
        service = RSSService(days_to_fetch=7)
        sources = [make_source()]

        article1 = make_article("https://example.com/article1", "Article 1")
        article2 = make_article("https://example.com/article2", "Article 2")
        article3 = make_article("https://example.com/article3", "Article 3")

        # Mock fetch_all_feeds to return 3 articles
        with patch.object(
            service, "fetch_all_feeds", AsyncMock(return_value=[article1, article2, article3])
        ):
            # Mock supabase service: article2 exists
            mock_supabase = AsyncMock()
            mock_supabase.check_article_exists = AsyncMock(
                side_effect=lambda url: url == "https://example.com/article2"
            )

            # Act
            with patch("app.services.rss_service.logger") as mock_logger:
                result = await service.fetch_new_articles(sources, mock_supabase)

            # Assert - verify logging calls
            # Should log: starting, fetched count, and final statistics
            assert mock_logger.info.call_count >= 3

            # Check that statistics are logged
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("Total fetched: 3" in str(call) for call in log_calls)
            assert any("Already existing: 1" in str(call) for call in log_calls)
            assert any("New articles: 2" in str(call) for call in log_calls)
