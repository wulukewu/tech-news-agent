"""
Property-based tests for LLMService error handling
Task 3.5: 撰寫 LLM Service 的屬性測試

Property 5: LLM Error Handling
Validates Requirements: 3.7, 8.2

This test verifies that the LLM service correctly handles API errors:
- When Groq API returns an error for a specific article, set tinkering_index and ai_summary to NULL
- Continue processing remaining articles after a failure
- All articles are returned (successful and failed)
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from app.schemas.article import AIAnalysis, ArticleSchema
from app.services.llm_service import LLMService

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


# Feature: background-scheduler-ai-pipeline, Property 5: LLM Error Handling
@settings(
    max_examples=20,  # Use 20 iterations as specified in task details
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,  # Disable deadline for async operations
)
@given(
    num_articles=st.integers(min_value=2, max_value=15),
    num_api_failures=st.integers(min_value=1, max_value=10),
)
@pytest.mark.asyncio
async def test_property_5_llm_error_handling(num_articles, num_api_failures):
    """
    Property 5: LLM Error Handling

    For any article where the Groq API returns an error, the LLM service should
    set tinkering_index = NULL and ai_summary = NULL for that article, and
    continue processing remaining articles.

    Validates: Requirements 3.7, 8.2
    """
    # Ensure we have a valid test case (at least one failure, but not all)
    assume(num_api_failures < num_articles)
    assume(num_api_failures >= 1)

    # Arrange: Create test data
    service = LLMService.__new__(LLMService)

    # Generate unique articles
    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-error-{uuid4().hex[:8]}.com/article-{i}"
        article = ArticleSchema(
            title=f"Test Article {i}",
            url=unique_url,
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
            tinkering_index=None,
            ai_summary=None,
        )
        articles.append(article)

    # Randomly select which articles will have API failures
    import random

    failing_indices = set(random.sample(range(num_articles), num_api_failures))

    # Mock evaluate_article to fail for specific articles
    call_count = 0

    async def mock_evaluate_article(article):
        nonlocal call_count
        current_index = call_count
        call_count += 1

        if current_index in failing_indices:
            # Simulate Groq API error
            raise Exception(f"Groq API error: Rate limit exceeded for article {current_index}")

        # Simulate successful evaluation
        return AIAnalysis(
            is_hardcore=True,
            reason="Test reason",
            actionable_takeaway="Test takeaway",
            tinkering_index=3,
        )

    # Mock generate_summary to succeed for all (to isolate evaluation failures)
    async def mock_generate_summary(article):
        return f"Summary for {article.title}"

    service.evaluate_article = mock_evaluate_article
    service.generate_summary = mock_generate_summary

    # Act: Call evaluate_batch
    result = await service.evaluate_batch(articles)

    # Assert: Verify error handling properties

    # Property 1: All articles should be returned (no articles dropped due to errors)
    assert len(result) == len(articles), (
        f"Output has {len(result)} articles, expected {len(articles)}. "
        f"Errors should not cause articles to be dropped."
    )

    # Property 2: Output should contain the same articles (by URL)
    input_urls = {str(article.url) for article in articles}
    output_urls = {str(article.url) for article in result}
    assert (
        input_urls == output_urls
    ), f"Output URLs {output_urls} don't match input URLs {input_urls}"

    # Property 3: For articles with API failures, tinkering_index should be NULL
    # Property 4: For articles with API failures, ai_analysis should be NULL
    # Property 5: For successful articles, tinkering_index should have a value
    failed_count = 0
    success_count = 0

    for i, article in enumerate(result):
        article_index = int(str(article.url).split("-")[-1])

        if article_index in failing_indices:
            # Failed evaluation: tinkering_index and ai_analysis should be NULL
            assert article.tinkering_index is None, (
                f"Article {i} (API failed) has tinkering_index={article.tinkering_index}, "
                f"expected None. Requirement 3.7: Set NULL on API failure."
            )
            assert article.ai_analysis is None, (
                f"Article {i} (API failed) has ai_analysis={article.ai_analysis}, "
                f"expected None. Requirement 3.7: Set NULL on API failure."
            )
            failed_count += 1
        else:
            # Successful evaluation: tinkering_index should have a value
            assert article.tinkering_index is not None, (
                f"Article {i} (API succeeded) has tinkering_index=None, expected a value. "
                f"Requirement 8.2: Continue processing remaining articles."
            )
            assert article.ai_analysis is not None, (
                f"Article {i} (API succeeded) has ai_analysis=None, expected a value. "
                f"Requirement 8.2: Continue processing remaining articles."
            )
            assert (
                article.ai_analysis.tinkering_index == 3
            ), f"Article {i} has tinkering_index={article.ai_analysis.tinkering_index}, expected 3"
            success_count += 1

    # Property 6: The number of failed and successful articles should match expectations
    assert (
        failed_count == num_api_failures
    ), f"Expected {num_api_failures} failed articles, got {failed_count}"
    assert success_count == (
        num_articles - num_api_failures
    ), f"Expected {num_articles - num_api_failures} successful articles, got {success_count}"

    # Property 7: All articles should have ai_summary (summary generation succeeds in this test)
    # This verifies that summary generation continues even after evaluation failures
    for i, article in enumerate(result):
        assert article.ai_summary is not None, (
            f"Article {i} has ai_summary=None. "
            f"Requirement 8.2: Processing should continue for remaining articles."
        )


# Feature: background-scheduler-ai-pipeline, Property 5: LLM Error Handling (Summary Failures)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(
    num_articles=st.integers(min_value=2, max_value=15),
    num_summary_failures=st.integers(min_value=1, max_value=10),
)
@pytest.mark.asyncio
async def test_property_5_llm_error_handling_summary_failures(num_articles, num_summary_failures):
    """
    Property 5: LLM Error Handling (Summary Failures)

    When summary generation fails for specific articles, the LLM service should
    set ai_summary = NULL for those articles and continue processing remaining articles.

    Validates: Requirements 3.7, 8.2
    """
    # Ensure valid test case
    assume(num_summary_failures < num_articles)
    assume(num_summary_failures >= 1)

    # Arrange
    service = LLMService.__new__(LLMService)

    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-summary-error-{uuid4().hex[:8]}.com/article-{i}"
        article = ArticleSchema(
            title=f"Summary Error Article {i}",
            url=unique_url,
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
            tinkering_index=None,
            ai_summary=None,
        )
        articles.append(article)

    # Randomly select which summaries will fail
    import random

    failing_summary_indices = set(random.sample(range(num_articles), num_summary_failures))

    # Mock evaluate_article to always succeed
    async def mock_evaluate_article(article):
        return AIAnalysis(
            is_hardcore=True,
            reason="Test reason",
            actionable_takeaway="Test takeaway",
            tinkering_index=4,
        )

    # Mock generate_summary to fail for specific articles
    summary_call_count = 0

    async def mock_generate_summary(article):
        nonlocal summary_call_count
        current_index = summary_call_count
        summary_call_count += 1

        if current_index in failing_summary_indices:
            # Simulate Groq API error for summary generation
            raise Exception(f"Groq API error: Timeout for summary generation {current_index}")

        return f"Summary for {article.title}"

    service.evaluate_article = mock_evaluate_article
    service.generate_summary = mock_generate_summary

    # Act
    result = await service.evaluate_batch(articles)

    # Assert

    # Property 1: All articles should be returned
    assert len(result) == num_articles, f"Expected {num_articles} articles, got {len(result)}"

    # Property 2: All articles should have tinkering_index (evaluation succeeded)
    for article in result:
        assert (
            article.tinkering_index is not None
        ), f"Article {article.title} has NULL tinkering_index"
        assert article.tinkering_index == 4

    # Property 3: Articles with summary failures should have NULL ai_summary
    # Property 4: Articles with successful summaries should have populated ai_summary
    failed_summary_count = 0
    success_summary_count = 0

    for i, article in enumerate(result):
        if i in failing_summary_indices:
            assert article.ai_summary is None, (
                f"Article {i} (summary failed) has ai_summary={article.ai_summary}, "
                f"expected None. Requirement 3.7: Set NULL on API failure."
            )
            failed_summary_count += 1
        else:
            assert article.ai_summary is not None, (
                f"Article {i} (summary succeeded) has NULL ai_summary. "
                f"Requirement 8.2: Continue processing remaining articles."
            )
            assert "Summary for" in article.ai_summary
            success_summary_count += 1

    # Property 5: Counts should match expectations
    assert failed_summary_count == num_summary_failures
    assert success_summary_count == (num_articles - num_summary_failures)


# Feature: background-scheduler-ai-pipeline, Property 5: LLM Error Handling (Both Failures)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None,
)
@given(
    num_articles=st.integers(min_value=3, max_value=15),
    num_eval_failures=st.integers(min_value=1, max_value=5),
    num_summary_failures=st.integers(min_value=1, max_value=5),
)
@pytest.mark.asyncio
async def test_property_5_llm_error_handling_both_failures(
    num_articles, num_eval_failures, num_summary_failures
):
    """
    Property 5: LLM Error Handling (Both Evaluation and Summary Failures)

    When both evaluation and summary generation fail for different articles,
    the service should handle each failure independently and continue processing.

    Validates: Requirements 3.7, 8.2
    """
    # Ensure valid test case
    assume(num_eval_failures < num_articles)
    assume(num_summary_failures < num_articles)
    assume(num_eval_failures + num_summary_failures < num_articles)  # At least one fully successful

    # Arrange
    service = LLMService.__new__(LLMService)

    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-both-error-{uuid4().hex[:8]}.com/article-{i}"
        article = ArticleSchema(
            title=f"Both Error Article {i}",
            url=unique_url,
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
            tinkering_index=None,
            ai_summary=None,
        )
        articles.append(article)

    # Randomly select which operations will fail
    import random

    failing_eval_indices = set(random.sample(range(num_articles), num_eval_failures))

    # For summary failures, select from articles that didn't fail evaluation
    remaining_indices = [i for i in range(num_articles) if i not in failing_eval_indices]
    num_summary_to_fail = min(num_summary_failures, len(remaining_indices))
    failing_summary_indices = set(random.sample(remaining_indices, num_summary_to_fail))

    # Mock evaluate_article
    eval_call_count = 0

    async def mock_evaluate_article(article):
        nonlocal eval_call_count
        current_index = eval_call_count
        eval_call_count += 1

        if current_index in failing_eval_indices:
            raise Exception(f"Groq API error: Evaluation failed for article {current_index}")

        return AIAnalysis(
            is_hardcore=True,
            reason="Test reason",
            actionable_takeaway="Test takeaway",
            tinkering_index=3,
        )

    # Mock generate_summary
    summary_call_count = 0

    async def mock_generate_summary(article):
        nonlocal summary_call_count
        current_index = summary_call_count
        summary_call_count += 1

        if current_index in failing_summary_indices:
            raise Exception(f"Groq API error: Summary failed for article {current_index}")

        return f"Summary for {article.title}"

    service.evaluate_article = mock_evaluate_article
    service.generate_summary = mock_generate_summary

    # Act
    result = await service.evaluate_batch(articles)

    # Assert

    # Property 1: All articles should be returned
    assert len(result) == num_articles

    # Property 2: Verify each article's state based on which operations failed
    for i, article in enumerate(result):
        if i in failing_eval_indices:
            # Evaluation failed: both fields should be NULL
            assert (
                article.tinkering_index is None
            ), f"Article {i} (eval failed) should have NULL tinkering_index"
            assert (
                article.ai_analysis is None
            ), f"Article {i} (eval failed) should have NULL ai_analysis"
            # Summary should still be attempted and succeed (since eval failed, summary is independent)
            assert (
                article.ai_summary is not None
            ), f"Article {i} (eval failed) should still have ai_summary"
        elif i in failing_summary_indices:
            # Evaluation succeeded, summary failed
            assert (
                article.tinkering_index is not None
            ), f"Article {i} (eval succeeded) should have tinkering_index"
            assert (
                article.ai_summary is None
            ), f"Article {i} (summary failed) should have NULL ai_summary"
        else:
            # Both succeeded
            assert (
                article.tinkering_index is not None
            ), f"Article {i} (both succeeded) should have tinkering_index"
            assert (
                article.ai_summary is not None
            ), f"Article {i} (both succeeded) should have ai_summary"


# Feature: background-scheduler-ai-pipeline, Property 5: LLM Error Handling (All Fail)
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
@given(num_articles=st.integers(min_value=1, max_value=15))
@pytest.mark.asyncio
async def test_property_5_llm_error_handling_all_fail(num_articles):
    """
    Property 5: LLM Error Handling (All Fail)

    When all API calls fail, all articles should still be returned with
    NULL values for tinkering_index and ai_summary.

    Validates: Requirements 3.7, 8.2
    """
    # Arrange
    service = LLMService.__new__(LLMService)

    articles = []
    for i in range(num_articles):
        unique_url = f"https://test-all-fail-{uuid4().hex[:8]}.com/article-{i}"
        article = ArticleSchema(
            title=f"All Fail Article {i}",
            url=unique_url,
            feed_id=uuid4(),
            feed_name="Test Feed",
            category="AI",
            published_at=datetime.now(UTC),
            tinkering_index=None,
            ai_summary=None,
        )
        articles.append(article)

    # Mock both methods to always fail
    async def mock_evaluate_article(article):
        raise Exception("Groq API error: Service unavailable")

    async def mock_generate_summary(article):
        raise Exception("Groq API error: Service unavailable")

    service.evaluate_article = mock_evaluate_article
    service.generate_summary = mock_generate_summary

    # Act
    result = await service.evaluate_batch(articles)

    # Assert

    # Property 1: All articles should be returned (no articles dropped)
    assert len(result) == num_articles, (
        f"Expected {num_articles} articles, got {len(result)}. "
        f"Requirement 8.2: Continue processing all articles even when all fail."
    )

    # Property 2: All articles should have NULL fields
    for article in result:
        assert article.tinkering_index is None, (
            f"Article {article.title} has tinkering_index={article.tinkering_index}, "
            f"expected None. Requirement 3.7: Set NULL on API failure."
        )
        assert article.ai_summary is None, (
            f"Article {article.title} has ai_summary={article.ai_summary}, "
            f"expected None. Requirement 3.7: Set NULL on API failure."
        )
        assert (
            article.ai_analysis is None
        ), f"Article {article.title} has ai_analysis={article.ai_analysis}, expected None"
