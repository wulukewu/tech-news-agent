"""
Property-based tests for LLMService batch processing
Task 3.4: 撰寫 LLM Service 的屬性測試

Property 4: LLM Batch Processing Completeness
Validates Requirements: 3.2, 3.3, 3.9

This test verifies that the LLM service correctly processes all articles in a batch:
- Output contains the same articles as input
- For successful analyses, tinkering_index and ai_summary have values
- For failed analyses, these fields are NULL
- All articles are returned (successful and failed)
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from app.services.llm_service import LLMService
from app.schemas.article import ArticleSchema, AIAnalysis


# Hypothesis strategies for generating test data

def valid_url_strategy():
    """Generate valid HTTP/HTTPS URLs for articles"""
    domains = st.sampled_from(['example.com', 'test.org', 'demo.net', 'sample.io', 'news.com'])
    paths = st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-', min_size=1, max_size=15),
        min_size=1,
        max_size=3
    )
    
    def build_url(domain, path_parts):
        path = '/'.join(path_parts)
        return f"https://{domain}/{path}"
    
    return st.builds(build_url, domains, paths)


def article_strategy():
    """Generate valid ArticleSchema objects with NULL tinkering_index and ai_summary"""
    return st.builds(
        ArticleSchema,
        title=st.text(min_size=1, max_size=200),
        url=valid_url_strategy(),
        feed_id=st.uuids(),
        feed_name=st.text(min_size=1, max_size=50),
        category=st.sampled_from(['AI', 'DevOps', 'Web', 'Mobile', 'Security']),
        published_at=st.just(datetime.now(timezone.utc)),
        tinkering_index=st.none(),  # Start with NULL
        ai_summary=st.none(),  # Start with NULL
        embedding=st.none()
    )


# Feature: background-scheduler-ai-pipeline, Property 4: LLM Batch Processing Completeness
@settings(
    max_examples=20,  # Use 20 iterations as specified in task details
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None  # Disable deadline for async operations
)
@given(
    num_articles=st.integers(min_value=1, max_value=15),
    num_failures=st.integers(min_value=0, max_value=10)
)
@pytest.mark.asyncio
async def test_property_4_llm_batch_processing_completeness(
    num_articles,
    num_failures
):
    """
    Property 4: LLM Batch Processing Completeness
    
    For any list of articles submitted for LLM analysis, the output should
    contain the same articles with analysis fields populated. For articles
    where API calls succeed, tinkering_index and ai_summary should have values.
    For articles where API calls fail, these fields should be NULL.
    
    Validates: Requirements 3.2, 3.3, 3.9
    """
    # Ensure we have a valid test case
    assume(num_failures <= num_articles)
    
    # Arrange: Create test data
    service = LLMService.__new__(LLMService)
    
    # Generate unique articles
    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-batch-{uuid4().hex[:8]}.com/article-{i}"
        article = ArticleSchema(
            title=f'Test Article {i}',
            url=unique_url,
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(timezone.utc),
            tinkering_index=None,
            ai_summary=None
        )
        articles.append(article)
    
    # Determine which articles will fail (first num_failures articles)
    failing_indices = set(range(num_failures))
    
    # Mock evaluate_article to succeed or fail based on index
    call_count = 0
    
    async def mock_evaluate_article(article):
        nonlocal call_count
        current_index = call_count
        call_count += 1
        
        if current_index in failing_indices:
            # Simulate API failure
            raise Exception(f"API error for article {current_index}")
        
        # Simulate successful evaluation
        return AIAnalysis(
            is_hardcore=True,
            reason="Test reason",
            actionable_takeaway="Test takeaway",
            tinkering_index=3
        )
    
    # Mock generate_summary to always succeed
    async def mock_generate_summary(article):
        # Check if this article's evaluation failed
        article_index = int(str(article.url).split('-')[-1])
        if article_index in failing_indices:
            # If evaluation failed, summary should still be attempted
            return f"Summary for {article.title}"
        return f"Summary for {article.title}"
    
    service.evaluate_article = mock_evaluate_article
    service.generate_summary = mock_generate_summary
    
    # Act: Call evaluate_batch
    result = await service.evaluate_batch(articles)
    
    # Assert: Verify batch processing properties
    
    # Property 1: Output should contain the same number of articles as input
    assert len(result) == len(articles), \
        f"Output has {len(result)} articles, expected {len(articles)}"
    
    # Property 2: Output should contain the same articles (by URL)
    input_urls = {str(article.url) for article in articles}
    output_urls = {str(article.url) for article in result}
    assert input_urls == output_urls, \
        f"Output URLs {output_urls} don't match input URLs {input_urls}"
    
    # Property 3: For successful analyses, tinkering_index should have a value
    # Property 4: For failed analyses, tinkering_index should be NULL
    for i, article in enumerate(result):
        article_index = int(str(article.url).split('-')[-1])
        
        if article_index in failing_indices:
            # Failed evaluation: tinkering_index should be NULL
            assert article.tinkering_index is None, \
                f"Article {i} (failed) has tinkering_index={article.tinkering_index}, expected None"
            assert article.ai_analysis is None, \
                f"Article {i} (failed) has ai_analysis={article.ai_analysis}, expected None"
        else:
            # Successful evaluation: tinkering_index should have a value
            assert article.tinkering_index is not None, \
                f"Article {i} (successful) has tinkering_index=None, expected a value"
            assert article.ai_analysis is not None, \
                f"Article {i} (successful) has ai_analysis=None, expected a value"
            assert article.ai_analysis.tinkering_index == 3, \
                f"Article {i} has tinkering_index={article.ai_analysis.tinkering_index}, expected 3"
    
    # Property 5: All articles should have ai_summary (summary generation doesn't fail in this test)
    for i, article in enumerate(result):
        assert article.ai_summary is not None, \
            f"Article {i} has ai_summary=None, expected a value"
        assert "Summary for" in article.ai_summary, \
            f"Article {i} has unexpected ai_summary: {article.ai_summary}"


# Feature: background-scheduler-ai-pipeline, Property 4: LLM Batch Processing Completeness (All Succeed)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None
)
@given(
    num_articles=st.integers(min_value=1, max_value=15)
)
@pytest.mark.asyncio
async def test_property_4_llm_batch_all_succeed(num_articles):
    """
    Property 4: LLM Batch Processing Completeness (All Succeed)
    
    When all API calls succeed, all articles should have populated
    tinkering_index and ai_summary fields.
    
    Validates: Requirements 3.2, 3.3
    """
    # Arrange
    service = LLMService.__new__(LLMService)
    
    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-success-{uuid4().hex[:8]}.com/article-{i}"
        article = ArticleSchema(
            title=f'Success Article {i}',
            url=unique_url,
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(timezone.utc),
            tinkering_index=None,
            ai_summary=None
        )
        articles.append(article)
    
    # Mock both methods to always succeed
    async def mock_evaluate_article(article):
        return AIAnalysis(
            is_hardcore=True,
            reason="Test reason",
            actionable_takeaway="Test takeaway",
            tinkering_index=4
        )
    
    async def mock_generate_summary(article):
        return f"Summary for {article.title}"
    
    service.evaluate_article = mock_evaluate_article
    service.generate_summary = mock_generate_summary
    
    # Act
    result = await service.evaluate_batch(articles)
    
    # Assert: All articles should have both fields populated
    assert len(result) == num_articles
    
    for article in result:
        assert article.tinkering_index is not None, \
            f"Article {article.title} has NULL tinkering_index"
        assert article.tinkering_index == 4, \
            f"Article {article.title} has tinkering_index={article.tinkering_index}, expected 4"
        assert article.ai_summary is not None, \
            f"Article {article.title} has NULL ai_summary"
        assert "Summary for" in article.ai_summary


# Feature: background-scheduler-ai-pipeline, Property 4: LLM Batch Processing Completeness (All Fail)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None
)
@given(
    num_articles=st.integers(min_value=1, max_value=15)
)
@pytest.mark.asyncio
async def test_property_4_llm_batch_all_fail(num_articles):
    """
    Property 4: LLM Batch Processing Completeness (All Fail)
    
    When all API calls fail, all articles should have NULL tinkering_index
    and ai_summary fields, but all articles should still be returned.
    
    Validates: Requirements 3.7, 3.9
    """
    # Arrange
    service = LLMService.__new__(LLMService)
    
    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-fail-{uuid4().hex[:8]}.com/article-{i}"
        article = ArticleSchema(
            title=f'Fail Article {i}',
            url=unique_url,
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(timezone.utc),
            tinkering_index=None,
            ai_summary=None
        )
        articles.append(article)
    
    # Mock both methods to always fail
    async def mock_evaluate_article(article):
        raise Exception("API error")
    
    async def mock_generate_summary(article):
        raise Exception("Summary API error")
    
    service.evaluate_article = mock_evaluate_article
    service.generate_summary = mock_generate_summary
    
    # Act
    result = await service.evaluate_batch(articles)
    
    # Assert: All articles should be returned with NULL fields
    assert len(result) == num_articles, \
        f"Expected {num_articles} articles, got {len(result)}"
    
    for article in result:
        assert article.tinkering_index is None, \
            f"Article {article.title} has tinkering_index={article.tinkering_index}, expected None"
        assert article.ai_summary is None, \
            f"Article {article.title} has ai_summary={article.ai_summary}, expected None"


# Feature: background-scheduler-ai-pipeline, Property 4: LLM Batch Processing Completeness (Summary Fails)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None
)
@given(
    num_articles=st.integers(min_value=1, max_value=15),
    num_summary_failures=st.integers(min_value=0, max_value=10)
)
@pytest.mark.asyncio
async def test_property_4_llm_batch_summary_failures(num_articles, num_summary_failures):
    """
    Property 4: LLM Batch Processing Completeness (Summary Fails)
    
    When summary generation fails but evaluation succeeds, articles should
    have tinkering_index populated but ai_summary as NULL.
    
    Validates: Requirements 3.2, 3.3, 3.9
    """
    # Ensure valid test case
    assume(num_summary_failures <= num_articles)
    
    # Arrange
    service = LLMService.__new__(LLMService)
    
    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-summary-fail-{uuid4().hex[:8]}.com/article-{i}"
        article = ArticleSchema(
            title=f'Summary Fail Article {i}',
            url=unique_url,
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(timezone.utc),
            tinkering_index=None,
            ai_summary=None
        )
        articles.append(article)
    
    # Determine which summaries will fail
    failing_summary_indices = set(range(num_summary_failures))
    
    # Mock evaluate_article to always succeed
    async def mock_evaluate_article(article):
        return AIAnalysis(
            is_hardcore=True,
            reason="Test reason",
            actionable_takeaway="Test takeaway",
            tinkering_index=3
        )
    
    # Mock generate_summary to fail for specific articles
    summary_call_count = 0
    
    async def mock_generate_summary(article):
        nonlocal summary_call_count
        current_index = summary_call_count
        summary_call_count += 1
        
        if current_index in failing_summary_indices:
            raise Exception("Summary API error")
        
        return f"Summary for {article.title}"
    
    service.evaluate_article = mock_evaluate_article
    service.generate_summary = mock_generate_summary
    
    # Act
    result = await service.evaluate_batch(articles)
    
    # Assert
    assert len(result) == num_articles
    
    for i, article in enumerate(result):
        # All should have tinkering_index (evaluation succeeded)
        assert article.tinkering_index is not None, \
            f"Article {i} has NULL tinkering_index"
        assert article.tinkering_index == 3
        
        # Check ai_summary based on whether it failed
        if i in failing_summary_indices:
            assert article.ai_summary is None, \
                f"Article {i} (summary failed) has ai_summary={article.ai_summary}, expected None"
        else:
            assert article.ai_summary is not None, \
                f"Article {i} (summary succeeded) has NULL ai_summary"


# Feature: background-scheduler-ai-pipeline, Property 4: LLM Batch Processing Completeness (Empty Batch)
@pytest.mark.asyncio
async def test_property_4_llm_batch_empty():
    """
    Property 4: LLM Batch Processing Completeness (Empty Batch)
    
    When given an empty list of articles, evaluate_batch should return
    an empty list without calling any API methods.
    
    Validates: Requirements 3.1
    """
    # Arrange
    service = LLMService.__new__(LLMService)
    
    # Mock methods to track if they're called
    evaluate_called = False
    summary_called = False
    
    async def mock_evaluate_article(article):
        nonlocal evaluate_called
        evaluate_called = True
        return AIAnalysis(
            is_hardcore=True,
            reason="Test",
            actionable_takeaway="Test",
            tinkering_index=3
        )
    
    async def mock_generate_summary(article):
        nonlocal summary_called
        summary_called = True
        return "Summary"
    
    service.evaluate_article = mock_evaluate_article
    service.generate_summary = mock_generate_summary
    
    # Act
    result = await service.evaluate_batch([])
    
    # Assert
    assert result == [], "Empty input should return empty list"
    assert not evaluate_called, "evaluate_article should not be called for empty batch"
    assert not summary_called, "generate_summary should not be called for empty batch"
