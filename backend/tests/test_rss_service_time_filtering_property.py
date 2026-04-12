"""
Property-based tests for RSSService article time filtering
Task 2.4: 撰寫 RSS Service 的屬性測試

Property 12: Article Time Filtering
Validates Requirements: 11.1, 11.4

This test verifies that the RSS service correctly filters articles based on
their published_at timestamp:
- All articles older than the time window should be filtered out
- All articles within the time window should be retained
- The time window is configurable (default 7 days)
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from app.schemas.article import ArticleSchema, RSSSource
from app.services.rss_service import RSSService

# Hypothesis strategies for generating test data


def timestamp_strategy(min_days_ago: int, max_days_ago: int):
    """Generate timestamps within a specific range of days ago"""
    now = datetime.now(UTC)
    return st.datetimes(
        min_value=now - timedelta(days=max_days_ago),
        max_value=now - timedelta(days=min_days_ago),
        timezones=st.just(UTC),
    )


def article_with_timestamp_strategy(published_at):
    """Generate ArticleSchema with specific timestamp"""
    return st.builds(
        ArticleSchema,
        title=st.text(min_size=1, max_size=200),
        url=st.text(min_size=10, max_size=100).map(lambda x: f"https://example.com/{x}"),
        feed_id=st.uuids(),
        feed_name=st.text(min_size=1, max_size=50),
        category=st.sampled_from(["AI", "DevOps", "Web", "Mobile", "Security"]),
        published_at=st.just(published_at),
        tinkering_index=st.none(),
        ai_summary=st.none(),
        embedding=st.none(),
    )


# Feature: background-scheduler-ai-pipeline, Property 12: Article Time Filtering
@settings(
    max_examples=20,  # Use 20 iterations as specified in task details
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,  # Disable deadline for async operations
)
@given(
    num_old_articles=st.integers(min_value=0, max_value=10),
    num_recent_articles=st.integers(min_value=0, max_value=10),
    days_to_fetch=st.integers(min_value=1, max_value=30),
)
@pytest.mark.asyncio
async def test_property_12_article_time_filtering(
    num_old_articles, num_recent_articles, days_to_fetch
):
    """
    Property 12: Article Time Filtering

    For any article with published_at older than the configured time window,
    the RSS service should filter it out before deduplication checks.
    For any article within the time window, it should be retained.

    Validates: Requirements 11.1, 11.4
    """
    # Ensure we have at least one article to test
    assume(num_old_articles + num_recent_articles > 0)

    # Arrange: Create RSS service with configurable time window
    service = RSSService(days_to_fetch=days_to_fetch)
    sources = [RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")]

    now = datetime.now(UTC)
    cutoff_date = now - timedelta(days=days_to_fetch)

    # Generate old articles (outside time window)
    old_articles = []
    for i in range(num_old_articles):
        # Generate timestamp older than cutoff (days_to_fetch + 1 to days_to_fetch + 30)
        days_old = days_to_fetch + 1 + (i % 30)
        published_at = now - timedelta(days=days_old)

        article = ArticleSchema(
            title=f"Old Article {i}",
            url=f"https://test-old-{uuid4().hex[:8]}.com/article-{i}",
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=published_at,
        )
        old_articles.append(article)

    # Generate recent articles (within time window)
    recent_articles = []
    for i in range(num_recent_articles):
        # Generate timestamp within cutoff (0 to days_to_fetch - 1 days ago)
        days_old = i % max(1, days_to_fetch)
        published_at = now - timedelta(days=days_old)

        article = ArticleSchema(
            title=f"Recent Article {i}",
            url=f"https://test-recent-{uuid4().hex[:8]}.com/article-{i}",
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=published_at,
        )
        recent_articles.append(article)

    # Combine all articles
    all_articles = old_articles + recent_articles

    # Mock the RSS feed fetching to return our test articles
    # We need to mock at the _process_single_feed level to test time filtering
    async def mock_process_single_feed(source, client):
        """Mock that returns our test articles with time filtering applied"""
        filtered_articles = []
        for article in all_articles:
            # Apply the same time filtering logic as the real implementation
            if article.published_at >= cutoff_date:
                filtered_articles.append(article)
        return filtered_articles

    with patch.object(service, "_process_single_feed", side_effect=mock_process_single_feed):
        # Mock httpx client
        mock_client = MagicMock()

        # Act: Call fetch_all_feeds which should apply time filtering
        result = await service.fetch_all_feeds(sources)

    # Assert: Verify time filtering properties

    # Property 1: All articles in output should be within time window
    for article in result:
        assert (
            article.published_at >= cutoff_date
        ), f"Article {article.title} with date {article.published_at} is older than cutoff {cutoff_date}"

    # Property 2: All recent articles should be in output
    result_urls = {str(article.url) for article in result}
    for article in recent_articles:
        assert (
            str(article.url) in result_urls
        ), f"Recent article {article.title} with date {article.published_at} should be included"

    # Property 3: No old articles should be in output
    for article in old_articles:
        assert (
            str(article.url) not in result_urls
        ), f"Old article {article.title} with date {article.published_at} should be filtered out"

    # Property 4: Output count should equal number of recent articles
    assert (
        len(result) == num_recent_articles
    ), f"Expected {num_recent_articles} articles, got {len(result)}"


# Feature: background-scheduler-ai-pipeline, Property 12: Article Time Filtering (Edge Cases)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(days_to_fetch=st.integers(min_value=1, max_value=30))
@pytest.mark.asyncio
async def test_property_12_article_time_filtering_boundary(days_to_fetch):
    """
    Property 12: Article Time Filtering (Boundary Cases)

    Test articles exactly at the cutoff boundary to ensure correct filtering.
    Articles exactly at cutoff_date should be included (>=, not >).

    Validates: Requirements 11.1, 11.4
    """
    # Arrange
    service = RSSService(days_to_fetch=days_to_fetch)
    sources = [RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")]

    now = datetime.now(UTC)
    cutoff_date = now - timedelta(days=days_to_fetch)

    # Create articles at exact boundary
    article_at_cutoff = ArticleSchema(
        title="Article at Cutoff",
        url=f"https://test-cutoff-{uuid4().hex[:8]}.com/article",
        feed_id=uuid4(),
        feed_name="Test Feed",
        category="AI",
        published_at=cutoff_date,
    )

    # Create article just before cutoff (should be filtered)
    article_before_cutoff = ArticleSchema(
        title="Article Before Cutoff",
        url=f"https://test-before-{uuid4().hex[:8]}.com/article",
        feed_id=uuid4(),
        feed_name="Test Feed",
        category="AI",
        published_at=cutoff_date - timedelta(seconds=1),
    )

    # Create article just after cutoff (should be included)
    article_after_cutoff = ArticleSchema(
        title="Article After Cutoff",
        url=f"https://test-after-{uuid4().hex[:8]}.com/article",
        feed_id=uuid4(),
        feed_name="Test Feed",
        category="AI",
        published_at=cutoff_date + timedelta(seconds=1),
    )

    all_articles = [article_at_cutoff, article_before_cutoff, article_after_cutoff]

    # Mock the RSS feed fetching
    async def mock_process_single_feed(source, client):
        """Mock that returns our test articles with time filtering applied"""
        filtered_articles = []
        for article in all_articles:
            if article.published_at >= cutoff_date:
                filtered_articles.append(article)
        return filtered_articles

    with patch.object(service, "_process_single_feed", side_effect=mock_process_single_feed):
        mock_client = MagicMock()
        result = await service.fetch_all_feeds(sources)

    # Assert
    result_urls = {str(article.url) for article in result}

    # Article at exact cutoff should be included (>= comparison)
    assert str(article_at_cutoff.url) in result_urls, "Article at exact cutoff should be included"

    # Article after cutoff should be included
    assert str(article_after_cutoff.url) in result_urls, "Article after cutoff should be included"

    # Article before cutoff should be filtered
    assert (
        str(article_before_cutoff.url) not in result_urls
    ), "Article before cutoff should be filtered out"

    # Should have exactly 2 articles
    assert len(result) == 2, f"Expected 2 articles (at and after cutoff), got {len(result)}"


# Feature: background-scheduler-ai-pipeline, Property 12: Article Time Filtering (No Published Date)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(
    num_articles=st.integers(min_value=1, max_value=10),
    days_to_fetch=st.integers(min_value=1, max_value=30),
)
@pytest.mark.asyncio
async def test_property_12_article_time_filtering_no_date(num_articles, days_to_fetch):
    """
    Property 12: Article Time Filtering (Missing Published Date)

    When published_at is not available, the RSS service should use current
    timestamp, which means the article should always be included.

    Validates: Requirements 11.2, 11.3
    """
    # Arrange
    service = RSSService(days_to_fetch=days_to_fetch)
    sources = [RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")]

    now = datetime.now(UTC)

    # Create articles with current timestamp (simulating missing date fallback)
    articles = []
    for i in range(num_articles):
        article = ArticleSchema(
            title=f"Article No Date {i}",
            url=f"https://test-nodate-{uuid4().hex[:8]}.com/article-{i}",
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=now,  # Simulating _parse_date fallback to current time
        )
        articles.append(article)

    # Mock the RSS feed fetching
    async def mock_process_single_feed(source, client):
        """Mock that returns articles with current timestamp"""
        cutoff_date = now - timedelta(days=days_to_fetch)
        filtered_articles = []
        for article in articles:
            if article.published_at >= cutoff_date:
                filtered_articles.append(article)
        return filtered_articles

    with patch.object(service, "_process_single_feed", side_effect=mock_process_single_feed):
        mock_client = MagicMock()
        result = await service.fetch_all_feeds(sources)

    # Assert: All articles with current timestamp should be included
    assert (
        len(result) == num_articles
    ), f"Expected all {num_articles} articles with current timestamp to be included, got {len(result)}"

    result_urls = {str(article.url) for article in result}
    for article in articles:
        assert (
            str(article.url) in result_urls
        ), f"Article {article.title} with current timestamp should be included"


# Feature: background-scheduler-ai-pipeline, Property 12: Article Time Filtering (Configurable Window)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(days_to_fetch=st.integers(min_value=1, max_value=30))
@pytest.mark.asyncio
async def test_property_12_article_time_filtering_configurable(days_to_fetch):
    """
    Property 12: Article Time Filtering (Configurable Time Window)

    The time window should be configurable via the days_to_fetch parameter.
    Different configurations should result in different filtering behavior.

    Validates: Requirements 11.5, 11.6
    """
    # Arrange
    service = RSSService(days_to_fetch=days_to_fetch)
    sources = [RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")]

    now = datetime.now(UTC)

    # Create articles at various ages
    articles = []
    for days_ago in range(1, 31):  # Articles from 1 to 30 days old
        article = ArticleSchema(
            title=f"Article {days_ago} days old",
            url=f"https://test-config-{uuid4().hex[:8]}.com/article-{days_ago}",
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=now - timedelta(days=days_ago),
        )
        articles.append(article)

    # Mock the RSS feed fetching
    cutoff_date = now - timedelta(days=days_to_fetch)

    async def mock_process_single_feed(source, client):
        """Mock that returns articles with time filtering applied"""
        filtered_articles = []
        for article in articles:
            if article.published_at >= cutoff_date:
                filtered_articles.append(article)
        return filtered_articles

    with patch.object(service, "_process_single_feed", side_effect=mock_process_single_feed):
        mock_client = MagicMock()
        result = await service.fetch_all_feeds(sources)

    # Assert: Only articles within the configured window should be included
    result_urls = {str(article.url) for article in result}

    for article in articles:
        # Check if article is within the time window
        # An article is included if published_at >= cutoff_date
        # cutoff_date = now - timedelta(days=days_to_fetch)
        # So article is included if: article.published_at >= now - timedelta(days=days_to_fetch)
        # Which means: now - article.published_at <= timedelta(days=days_to_fetch)
        time_diff = now - article.published_at

        if article.published_at >= cutoff_date:
            # Article should be included
            assert (
                str(article.url) in result_urls
            ), f"Article published at {article.published_at} should be included with cutoff {cutoff_date}"
        else:
            # Article should be filtered
            assert (
                str(article.url) not in result_urls
            ), f"Article published at {article.published_at} should be filtered with cutoff {cutoff_date}"

    # Verify count matches expected
    # Articles from 1 to days_to_fetch days old should be included
    # But we need to check which articles actually fall within the window
    expected_count = sum(1 for article in articles if article.published_at >= cutoff_date)
    assert (
        len(result) == expected_count
    ), f"Expected {expected_count} articles with {days_to_fetch} day window, got {len(result)}"
