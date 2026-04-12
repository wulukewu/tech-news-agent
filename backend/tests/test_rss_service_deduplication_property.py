"""
Property-based tests for RSSService article deduplication
Task 2.3: 撰寫 RSS Service 的屬性測試

Property 2: Article Deduplication Correctness
Validates Requirements: 2.3, 2.4, 2.5

This test verifies that the RSS service correctly filters out articles that
already exist in the database:
- Articles with URLs already in database should not appear in output
- Articles with URLs not in database should appear in output
- Output should contain exactly the new articles (no more, no less)
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from app.schemas.article import ArticleSchema, RSSSource
from app.services.rss_service import RSSService

# Hypothesis strategies for generating test data


def valid_url_strategy():
    """Generate valid HTTP/HTTPS URLs for articles"""
    domains = st.sampled_from(["example.com", "test.org", "demo.net", "sample.io", "news.com"])
    paths = st.lists(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-", min_size=1, max_size=15),
        min_size=1,
        max_size=3,
    )

    def build_url(domain, path_parts):
        path = "/".join(path_parts)
        return f"https://{domain}/{path}"

    return st.builds(build_url, domains, paths)


def article_strategy():
    """Generate valid ArticleSchema objects"""
    return st.builds(
        ArticleSchema,
        title=st.text(min_size=1, max_size=200),
        url=valid_url_strategy(),
        feed_id=st.uuids(),
        feed_name=st.text(min_size=1, max_size=50),
        category=st.sampled_from(["AI", "DevOps", "Web", "Mobile", "Security"]),
        published_at=st.just(datetime.now(UTC)),
        tinkering_index=st.none(),
        ai_summary=st.none(),
        embedding=st.none(),
    )


def rss_source_strategy():
    """Generate valid RSSSource objects"""
    return st.builds(
        RSSSource,
        name=st.text(min_size=1, max_size=50),
        url=valid_url_strategy(),
        category=st.sampled_from(["AI", "DevOps", "Web", "Mobile", "Security"]),
    )


# Feature: background-scheduler-ai-pipeline, Property 2: Article Deduplication Correctness
@settings(
    max_examples=20,  # Use 20 iterations as specified in task details
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,  # Disable deadline for async operations
)
@given(
    num_fetched_articles=st.integers(min_value=1, max_value=20),
    num_existing_urls=st.integers(min_value=0, max_value=15),
)
@pytest.mark.asyncio
async def test_property_2_article_deduplication_correctness(
    num_fetched_articles, num_existing_urls
):
    """
    Property 2: Article Deduplication Correctness

    For any list of fetched articles and any database state, the RSS service
    should return only articles whose URLs do not exist in the database.
    Specifically:
    - Articles with URLs already in database should not appear in output
    - Articles with URLs not in database should appear in output
    - Output should contain exactly the new articles (no more, no less)

    Validates: Requirements 2.3, 2.4, 2.5
    """
    # Ensure we have a valid test case
    assume(num_existing_urls <= num_fetched_articles)

    # Arrange: Create test data
    service = RSSService(days_to_fetch=7)
    sources = [RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")]

    # Generate unique articles with distinct URLs
    fetched_articles = []
    all_urls = set()

    for i in range(num_fetched_articles):
        # Generate unique URL for this test
        unique_url = f"https://test-dedup-{uuid4().hex[:8]}.com/article-{i}"
        all_urls.add(unique_url)

        article = ArticleSchema(
            title=f"Test Article {i}",
            url=unique_url,
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
        )
        fetched_articles.append(article)

    # Select which URLs already exist in database
    existing_urls = set(list(all_urls)[:num_existing_urls])
    new_urls = all_urls - existing_urls

    # Mock fetch_all_feeds to return our generated articles
    with patch.object(service, "fetch_all_feeds", AsyncMock(return_value=fetched_articles)):
        # Mock supabase service to return existence based on our existing_urls set
        mock_supabase = AsyncMock()
        mock_supabase.check_article_exists = AsyncMock(side_effect=lambda url: url in existing_urls)

        # Act: Call fetch_new_articles
        result = await service.fetch_new_articles(sources, mock_supabase)

    # Assert: Verify deduplication properties

    # Property 1: Output should only contain articles with URLs NOT in database
    result_urls = {str(article.url) for article in result}
    for url in result_urls:
        assert (
            url not in existing_urls
        ), f"Output contains existing URL {url}, should be filtered out"

    # Property 2: Output should contain ALL articles with URLs not in database
    for url in new_urls:
        assert url in result_urls, f"Output missing new URL {url}, should be included"

    # Property 3: Output should contain exactly the new articles (no more, no less)
    expected_count = len(new_urls)
    actual_count = len(result)
    assert (
        actual_count == expected_count
    ), f"Expected {expected_count} new articles, got {actual_count}"

    # Property 4: No duplicates in output
    assert len(result_urls) == len(result), "Output contains duplicate articles"

    # Property 5: check_article_exists should be called for each fetched article
    assert mock_supabase.check_article_exists.call_count == num_fetched_articles, (
        f"check_article_exists should be called {num_fetched_articles} times, "
        f"was called {mock_supabase.check_article_exists.call_count} times"
    )


# Feature: background-scheduler-ai-pipeline, Property 2: Article Deduplication Correctness (All New)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(num_articles=st.integers(min_value=1, max_value=20))
@pytest.mark.asyncio
async def test_property_2_all_articles_new(num_articles):
    """
    Property 2: Article Deduplication Correctness (All New)

    When no articles exist in the database, all fetched articles should be
    returned as new articles.

    Validates: Requirements 2.4, 2.5
    """
    # Arrange
    service = RSSService(days_to_fetch=7)
    sources = [RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")]

    # Generate unique articles
    fetched_articles = []
    for i in range(num_articles):
        unique_url = f"https://test-allnew-{uuid4().hex[:8]}.com/article-{i}"
        article = ArticleSchema(
            title=f"Test Article {i}",
            url=unique_url,
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
        )
        fetched_articles.append(article)

    # Mock fetch_all_feeds
    with patch.object(service, "fetch_all_feeds", AsyncMock(return_value=fetched_articles)):
        # Mock supabase: no articles exist
        mock_supabase = AsyncMock()
        mock_supabase.check_article_exists = AsyncMock(return_value=False)

        # Act
        result = await service.fetch_new_articles(sources, mock_supabase)

    # Assert: All articles should be returned
    assert (
        len(result) == num_articles
    ), f"Expected all {num_articles} articles to be new, got {len(result)}"

    # Verify all original articles are in result
    result_urls = {str(article.url) for article in result}
    for article in fetched_articles:
        assert str(article.url) in result_urls, f"Article {article.url} should be in result"


# Feature: background-scheduler-ai-pipeline, Property 2: Article Deduplication Correctness (All Existing)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(num_articles=st.integers(min_value=1, max_value=20))
@pytest.mark.asyncio
async def test_property_2_all_articles_existing(num_articles):
    """
    Property 2: Article Deduplication Correctness (All Existing)

    When all fetched articles already exist in the database, no articles
    should be returned (empty list).

    Validates: Requirements 2.3, 2.5
    """
    # Arrange
    service = RSSService(days_to_fetch=7)
    sources = [RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")]

    # Generate unique articles
    fetched_articles = []
    for i in range(num_articles):
        unique_url = f"https://test-allexist-{uuid4().hex[:8]}.com/article-{i}"
        article = ArticleSchema(
            title=f"Test Article {i}",
            url=unique_url,
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
        )
        fetched_articles.append(article)

    # Mock fetch_all_feeds
    with patch.object(service, "fetch_all_feeds", AsyncMock(return_value=fetched_articles)):
        # Mock supabase: all articles exist
        mock_supabase = AsyncMock()
        mock_supabase.check_article_exists = AsyncMock(return_value=True)

        # Act
        result = await service.fetch_new_articles(sources, mock_supabase)

    # Assert: No articles should be returned
    assert len(result) == 0, f"Expected 0 articles when all exist, got {len(result)}"


# Feature: background-scheduler-ai-pipeline, Property 2: Article Deduplication Correctness (With Failures)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(
    num_articles=st.integers(min_value=3, max_value=20),
    num_check_failures=st.integers(min_value=1, max_value=5),
)
@pytest.mark.asyncio
async def test_property_2_deduplication_with_check_failures(num_articles, num_check_failures):
    """
    Property 2: Article Deduplication Correctness (With Check Failures)

    When check_article_exists fails for some articles, those articles should
    be included in the output (fail-safe behavior to avoid losing data).
    Other articles should still be deduplicated correctly.

    Validates: Requirements 2.3, 2.4, 2.5, 2.7
    """
    # Ensure we have enough articles for failures
    assume(num_check_failures < num_articles)

    # Arrange
    service = RSSService(days_to_fetch=7)
    sources = [RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")]

    # Generate unique articles
    fetched_articles = []
    all_urls = []
    for i in range(num_articles):
        unique_url = f"https://test-failures-{uuid4().hex[:8]}.com/article-{i}"
        all_urls.append(unique_url)
        article = ArticleSchema(
            title=f"Test Article {i}",
            url=unique_url,
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
        )
        fetched_articles.append(article)

    # Select URLs that will fail check, exist, and are new
    failing_urls = set(all_urls[:num_check_failures])
    # Split remaining URLs between existing and new
    remaining_urls = all_urls[num_check_failures:]
    mid_point = len(remaining_urls) // 2
    existing_urls = set(remaining_urls[:mid_point])
    new_urls = set(remaining_urls[mid_point:])

    # Mock fetch_all_feeds
    with patch.object(service, "fetch_all_feeds", AsyncMock(return_value=fetched_articles)):
        # Mock supabase with mixed behavior
        mock_supabase = AsyncMock()

        def check_side_effect(url):
            if url in failing_urls:
                raise Exception("Database check failed")
            return url in existing_urls

        mock_supabase.check_article_exists = AsyncMock(side_effect=check_side_effect)

        # Act
        result = await service.fetch_new_articles(sources, mock_supabase)

    # Assert: Result should include new URLs and failed check URLs (fail-safe)
    result_urls = {str(article.url) for article in result}

    # Property 1: Failed checks should be included (fail-safe)
    for url in failing_urls:
        assert url in result_urls, f"URL {url} with failed check should be included (fail-safe)"

    # Property 2: New URLs should be included
    for url in new_urls:
        assert url in result_urls, f"New URL {url} should be included"

    # Property 3: Existing URLs should NOT be included
    for url in existing_urls:
        assert url not in result_urls, f"Existing URL {url} should be filtered out"

    # Property 4: Count should match expected
    expected_count = len(failing_urls) + len(new_urls)
    actual_count = len(result)
    assert (
        actual_count == expected_count
    ), f"Expected {expected_count} articles (failed checks + new), got {actual_count}"


# Feature: background-scheduler-ai-pipeline, Property 2: Article Deduplication Correctness (Empty Fetch)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(num_existing_in_db=st.integers(min_value=0, max_value=100))
@pytest.mark.asyncio
async def test_property_2_empty_fetch_result(num_existing_in_db):
    """
    Property 2: Article Deduplication Correctness (Empty Fetch)

    When fetch_all_feeds returns no articles, the result should be an empty
    list regardless of database state. check_article_exists should not be
    called.

    Validates: Requirements 2.5
    """
    # Arrange
    service = RSSService(days_to_fetch=7)
    sources = [RSSSource(name="Test Feed", url="https://example.com/feed", category="AI")]

    # Mock fetch_all_feeds to return empty list
    with patch.object(service, "fetch_all_feeds", AsyncMock(return_value=[])):
        # Mock supabase
        mock_supabase = AsyncMock()
        mock_supabase.check_article_exists = AsyncMock(return_value=True)

        # Act
        result = await service.fetch_new_articles(sources, mock_supabase)

    # Assert: Result should be empty
    assert len(result) == 0, f"Expected empty result when no articles fetched, got {len(result)}"

    # Property: check_article_exists should not be called
    assert (
        mock_supabase.check_article_exists.call_count == 0
    ), "check_article_exists should not be called when no articles fetched"
