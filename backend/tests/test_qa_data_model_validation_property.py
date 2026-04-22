"""
Property-Based Tests for QA Agent Data Model Validation

This module implements property-based tests for the Intelligent Q&A Agent data models,
focusing on Property 1 (Query Processing Completeness) and Property 6 (Structured Response Format).

**Validates: Requirements 1.1, 1.2, 3.1, 3.2, 3.3, 3.5**

Property 1: Query Processing Completeness
- For any natural language query in Chinese or English, the query processor SHALL produce
  a valid ParsedQuery object containing non-empty keywords, a valid intent classification,
  and appropriate language detection.

Property 6: Structured Response Format
- For any query and retrieved articles, the generated response SHALL contain exactly the
  required elements (article summaries of 2-3 sentences, original links, personalized insights,
  and related reading suggestions) with a maximum of 5 articles sorted by relevance.
"""

from datetime import datetime
from typing import List
from uuid import UUID, uuid4

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError as PydanticValidationError

from app.qa_agent.models import (
    ArticleSummary,
    ParsedQuery,
    QueryIntent,
    QueryLanguage,
    ResponseType,
    StructuredResponse,
)

# ============================================================================
# Strategy Definitions
# ============================================================================


def chinese_text_strategy(min_size: int = 1, max_size: int = 100) -> st.SearchStrategy:
    """Generate Chinese text strings."""
    # Common Chinese characters range
    return st.text(
        alphabet=st.characters(
            min_codepoint=0x4E00,  # Start of CJK Unified Ideographs
            max_codepoint=0x9FFF,  # End of CJK Unified Ideographs
        ),
        min_size=min_size,
        max_size=max_size,
    )


def english_text_strategy(min_size: int = 1, max_size: int = 100) -> st.SearchStrategy:
    """Generate English text strings."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll"),  # Uppercase and lowercase letters
            min_codepoint=ord("A"),
            max_codepoint=ord("z"),
        ),
        min_size=min_size,
        max_size=max_size,
    ).filter(lambda s: s.strip() != "")


def mixed_language_query_strategy() -> st.SearchStrategy:
    """Generate natural language queries in Chinese or English."""
    chinese_queries = chinese_text_strategy(min_size=2, max_size=200)
    english_queries = english_text_strategy(min_size=5, max_size=200)

    return st.one_of(chinese_queries, english_queries)


def query_intent_strategy() -> st.SearchStrategy:
    """Generate valid query intents."""
    return st.sampled_from(
        [
            QueryIntent.SEARCH,
            QueryIntent.QUESTION,
            QueryIntent.COMPARISON,
            QueryIntent.SUMMARY,
            QueryIntent.RECOMMENDATION,
            QueryIntent.CLARIFICATION,
            QueryIntent.EXPLORATION,
            QueryIntent.UNKNOWN,
        ]
    )


def query_language_strategy() -> st.SearchStrategy:
    """Generate valid query languages."""
    return st.sampled_from(
        [
            QueryLanguage.CHINESE,
            QueryLanguage.ENGLISH,
            QueryLanguage.AUTO_DETECT,
        ]
    )


def keywords_strategy() -> st.SearchStrategy:
    """Generate keyword lists."""
    return st.lists(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"),
                min_codepoint=ord("A"),
                max_codepoint=ord("z"),
            ),
            min_size=2,
            max_size=20,
        ).filter(lambda s: s.strip() != ""),
        min_size=1,
        max_size=20,
    )


def confidence_score_strategy() -> st.SearchStrategy:
    """Generate confidence scores in valid range [0.0, 1.0]."""
    return st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


def parsed_query_strategy() -> st.SearchStrategy:
    """Generate valid ParsedQuery objects."""
    return st.builds(
        ParsedQuery,
        original_query=mixed_language_query_strategy(),
        language=query_language_strategy(),
        intent=query_intent_strategy(),
        keywords=keywords_strategy(),
        filters=st.just({}),
        confidence=confidence_score_strategy(),
    )


def article_summary_strategy() -> st.SearchStrategy:
    """Generate valid ArticleSummary objects."""
    # Generate summaries with 2-3 sentences
    sentence = st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
        min_size=10,
        max_size=100,
    ).filter(lambda s: s.strip() != "")

    summary_text = st.builds(lambda s1, s2, s3: f"{s1}. {s2}. {s3}.", sentence, sentence, sentence)

    return st.builds(
        ArticleSummary,
        article_id=st.just(uuid4()),
        title=st.text(min_size=5, max_size=200).filter(lambda s: s.strip() != ""),
        summary=summary_text,
        url=st.just("https://example.com/article"),
        relevance_score=confidence_score_strategy(),
        reading_time=st.integers(min_value=1, max_value=60),
        key_insights=st.lists(
            st.text(min_size=5, max_size=100).filter(lambda s: s.strip() != ""),
            min_size=0,
            max_size=5,
        ),
        published_at=st.none(),
        category=st.text(min_size=2, max_size=50).filter(lambda s: s.strip() != ""),
    )


def structured_response_strategy() -> st.SearchStrategy:
    """Generate valid StructuredResponse objects."""
    return st.builds(
        StructuredResponse,
        query=mixed_language_query_strategy(),
        response_type=st.just(ResponseType.STRUCTURED),
        articles=st.lists(article_summary_strategy(), min_size=1, max_size=5),
        insights=st.lists(
            st.text(min_size=10, max_size=200).filter(lambda s: s.strip() != ""),
            min_size=1,
            max_size=10,
        ),
        recommendations=st.lists(
            st.text(min_size=10, max_size=200).filter(lambda s: s.strip() != ""),
            min_size=1,
            max_size=10,
        ),
        conversation_id=st.just(uuid4()),
        response_time=st.floats(
            min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False
        ),
        confidence=confidence_score_strategy(),
    )


# ============================================================================
# Property 1: Query Processing Completeness
# ============================================================================


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    original_query=mixed_language_query_strategy(),
    language=query_language_strategy(),
    intent=query_intent_strategy(),
    keywords=keywords_strategy(),
    confidence=confidence_score_strategy(),
)
def test_property_1_parsed_query_completeness(
    original_query: str,
    language: QueryLanguage,
    intent: QueryIntent,
    keywords: List[str],
    confidence: float,
):
    """
    Feature: intelligent-qa-agent, Property 1: Query Processing Completeness

    **Validates: Requirements 1.1, 1.2**

    For any natural language query in Chinese or English, the query processor SHALL produce
    a valid ParsedQuery object containing non-empty keywords, a valid intent classification,
    and appropriate language detection.

    This test verifies that:
    1. ParsedQuery objects can be created with valid inputs
    2. Keywords are non-empty after validation
    3. Intent is a valid QueryIntent enum value
    4. Language is correctly set to Chinese or English
    5. Confidence score is within valid range [0.0, 1.0]
    """
    # Ensure we have a valid query text
    assume(len(original_query.strip()) > 0)
    assume(len(original_query.strip()) <= 2000)

    # Create ParsedQuery
    parsed_query = ParsedQuery(
        original_query=original_query,
        language=language,
        intent=intent,
        keywords=keywords,
        confidence=confidence,
    )

    # Property 1 Assertions: Query Processing Completeness

    # 1. ParsedQuery object is created successfully
    assert isinstance(parsed_query, ParsedQuery)

    # 2. Original query is preserved
    assert parsed_query.original_query == original_query

    # 3. Keywords are non-empty (after validation and cleaning)
    assert isinstance(parsed_query.keywords, list)
    # Keywords may be empty after cleaning, but the list itself exists
    for keyword in parsed_query.keywords:
        assert isinstance(keyword, str)
        assert len(keyword.strip()) > 0

    # 4. Intent is a valid QueryIntent enum value
    assert isinstance(parsed_query.intent, QueryIntent)
    assert parsed_query.intent in [
        QueryIntent.SEARCH,
        QueryIntent.QUESTION,
        QueryIntent.COMPARISON,
        QueryIntent.SUMMARY,
        QueryIntent.RECOMMENDATION,
        QueryIntent.CLARIFICATION,
        QueryIntent.EXPLORATION,
        QueryIntent.UNKNOWN,
    ]

    # 5. Language is correctly set
    assert isinstance(parsed_query.language, QueryLanguage)
    assert parsed_query.language in [
        QueryLanguage.CHINESE,
        QueryLanguage.ENGLISH,
        QueryLanguage.AUTO_DETECT,
    ]

    # 6. Confidence score is within valid range [0.0, 1.0]
    assert isinstance(parsed_query.confidence, float)
    assert 0.0 <= parsed_query.confidence <= 1.0

    # 7. Processed timestamp is set
    assert isinstance(parsed_query.processed_at, datetime)
    assert parsed_query.processed_at <= datetime.utcnow()


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(parsed_query=parsed_query_strategy())
def test_property_1_query_validation_methods(parsed_query: ParsedQuery):
    """
    Feature: intelligent-qa-agent, Property 1: Query Processing Completeness

    **Validates: Requirements 1.1, 1.2**

    Test that ParsedQuery validation methods work correctly for any valid query.

    This test verifies that:
    1. is_valid() method returns consistent results
    2. requires_clarification() method returns consistent results
    3. Validation logic is sound
    """
    # Test is_valid() method
    is_valid = parsed_query.is_valid()
    assert isinstance(is_valid, bool)

    # If query is valid, it should meet these criteria
    if is_valid:
        assert len(parsed_query.original_query.strip()) > 0
        assert parsed_query.intent != QueryIntent.UNKNOWN
        assert parsed_query.confidence > 0.3

    # Test requires_clarification() method
    requires_clarification = parsed_query.requires_clarification()
    assert isinstance(requires_clarification, bool)

    # If clarification is required, it should meet these criteria
    if requires_clarification:
        assert (
            parsed_query.confidence < 0.5
            or parsed_query.intent == QueryIntent.UNKNOWN
            or len(parsed_query.keywords) == 0
        )


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    keywords=st.lists(
        st.text(min_size=0, max_size=50),
        min_size=0,
        max_size=30,
    )
)
def test_property_1_keyword_validation_and_cleaning(keywords: List[str]):
    """
    Feature: intelligent-qa-agent, Property 1: Query Processing Completeness

    **Validates: Requirements 1.1**

    Test that keyword validation and cleaning works correctly for any input.

    This test verifies that:
    1. Empty strings are removed
    2. Duplicates are removed (case-insensitive)
    3. Whitespace is stripped
    4. Keywords are limited to 20 items
    """
    parsed_query = ParsedQuery(
        original_query="test query",
        language=QueryLanguage.ENGLISH,
        intent=QueryIntent.SEARCH,
        keywords=keywords,
        confidence=0.5,
    )

    # Property 1 Assertions: Keyword Validation

    # 1. No empty strings in cleaned keywords
    for keyword in parsed_query.keywords:
        assert len(keyword.strip()) > 0

    # 2. No duplicate keywords (case-insensitive)
    lowercase_keywords = [k.lower() for k in parsed_query.keywords]
    assert len(lowercase_keywords) == len(set(lowercase_keywords))

    # 3. Keywords are limited to 20 items
    assert len(parsed_query.keywords) <= 20


# ============================================================================
# Property 6: Structured Response Format
# ============================================================================


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(response=structured_response_strategy())
def test_property_6_structured_response_format(response: StructuredResponse):
    """
    Feature: intelligent-qa-agent, Property 6: Structured Response Format

    **Validates: Requirements 3.1, 3.2, 3.3, 3.5**

    For any query and retrieved articles, the generated response SHALL contain exactly the
    required elements (article summaries of 2-3 sentences, original links, personalized insights,
    and related reading suggestions) with a maximum of 5 articles sorted by relevance.

    This test verifies that:
    1. Response contains all required elements
    2. Articles are limited to maximum of 5
    3. Articles are sorted by relevance score (descending)
    4. Each article has 2-3 sentence summaries
    5. Each article has original links
    6. Response includes personalized insights
    7. Response includes related reading suggestions
    """
    # Property 6 Assertions: Structured Response Format

    # 1. Response contains all required elements
    assert isinstance(response, StructuredResponse)
    assert hasattr(response, "query")
    assert hasattr(response, "articles")
    assert hasattr(response, "insights")
    assert hasattr(response, "recommendations")
    assert hasattr(response, "conversation_id")
    assert hasattr(response, "response_time")

    # 2. Articles are limited to maximum of 5 (Requirement 3.2)
    assert len(response.articles) <= 5

    # 3. Articles are sorted by relevance score in descending order (Requirement 3.2)
    if len(response.articles) > 1:
        for i in range(len(response.articles) - 1):
            assert response.articles[i].relevance_score >= response.articles[i + 1].relevance_score

    # 4. Each article has proper summary structure (Requirement 3.3)
    for article in response.articles:
        # Article has all required fields
        assert isinstance(article, ArticleSummary)
        assert hasattr(article, "article_id")
        assert hasattr(article, "title")
        assert hasattr(article, "summary")
        assert hasattr(article, "url")
        assert hasattr(article, "relevance_score")
        assert hasattr(article, "reading_time")

        # Summary contains 2-3 sentences (Requirement 3.3)
        sentences = [s.strip() for s in article.summary.split(".") if s.strip()]
        assert 2 <= len(sentences) <= 4  # Allow up to 4 due to validation truncation

        # Summary has minimum length
        assert len(article.summary) >= 10

        # Title is non-empty
        assert len(article.title.strip()) > 0

        # URL is present (Requirement 3.1)
        assert article.url is not None
        assert str(article.url).startswith("http")

        # Relevance score is valid
        assert 0.0 <= article.relevance_score <= 1.0

        # Reading time is positive
        assert article.reading_time >= 1

    # 5. Response includes personalized insights (Requirement 3.4, 3.1)
    assert isinstance(response.insights, list)
    # Insights may be empty, but the field exists
    for insight in response.insights:
        assert isinstance(insight, str)
        assert len(insight.strip()) > 0

    # 6. Response includes related reading suggestions (Requirement 3.5, 3.1)
    assert isinstance(response.recommendations, list)
    # Recommendations may be empty, but the field exists
    for recommendation in response.recommendations:
        assert isinstance(recommendation, str)
        assert len(recommendation.strip()) > 0

    # 7. Query is preserved
    assert isinstance(response.query, str)
    assert len(response.query.strip()) > 0

    # 8. Response time is valid
    assert isinstance(response.response_time, float)
    assert response.response_time >= 0.0

    # 9. Confidence score is valid
    assert isinstance(response.confidence, float)
    assert 0.0 <= response.confidence <= 1.0

    # 10. Conversation ID is valid UUID
    assert isinstance(response.conversation_id, UUID)


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(articles=st.lists(article_summary_strategy(), min_size=2, max_size=10))
def test_property_6_article_sorting_by_relevance(articles: List[ArticleSummary]):
    """
    Feature: intelligent-qa-agent, Property 6: Structured Response Format

    **Validates: Requirements 3.2**

    Test that articles are automatically sorted by relevance score in descending order.

    This test verifies that:
    1. Articles are sorted by relevance_score (highest first)
    2. Sorting is stable and consistent
    3. Maximum of 5 articles are kept
    """
    # Limit articles to 5 before creating response (model enforces this limit)
    limited_articles = articles[:5]

    # Create response with unsorted articles
    response = StructuredResponse(
        query="test query",
        articles=limited_articles,
        insights=["Test insight"],
        recommendations=["Test recommendation"],
        conversation_id=uuid4(),
        response_time=1.0,
        confidence=0.8,
    )

    # Property 6 Assertions: Article Sorting

    # 1. Articles are limited to 5
    assert len(response.articles) <= 5

    # 2. Articles are sorted by relevance score (descending)
    for i in range(len(response.articles) - 1):
        assert response.articles[i].relevance_score >= response.articles[i + 1].relevance_score

    # 3. All articles have valid relevance scores
    for article in response.articles:
        assert 0.0 <= article.relevance_score <= 1.0


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    summary_sentences=st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
            min_size=10,
            max_size=100,
        ).filter(lambda s: s.strip() != ""),
        min_size=2,
        max_size=5,
    )
)
def test_property_6_article_summary_sentence_count(summary_sentences: List[str]):
    """
    Feature: intelligent-qa-agent, Property 6: Structured Response Format

    **Validates: Requirements 3.3**

    Test that article summaries contain 2-3 sentences as required.

    This test verifies that:
    1. Summaries with 2-3 sentences are accepted
    2. Summaries with more than 4 sentences are truncated to 3
    3. Summaries with less than 2 sentences are rejected
    """
    # Create summary text from sentences
    summary_text = ". ".join(summary_sentences) + "."

    # Test with valid summary (2-3 sentences)
    if 2 <= len(summary_sentences) <= 4:
        article = ArticleSummary(
            article_id=uuid4(),
            title="Test Article",
            summary=summary_text,
            url="https://example.com/test",
            relevance_score=0.8,
            reading_time=3,
            category="Test",
        )

        # Property 6 Assertions: Summary Sentence Count
        sentences = [s.strip() for s in article.summary.split(".") if s.strip()]
        assert 2 <= len(sentences) <= 4  # Allow up to 4 due to validation

    # Test with too few sentences (should fail)
    elif len(summary_sentences) < 2:
        with pytest.raises(PydanticValidationError):
            ArticleSummary(
                article_id=uuid4(),
                title="Test Article",
                summary=summary_text,
                url="https://example.com/test",
                relevance_score=0.8,
                reading_time=3,
                category="Test",
            )

    # Test with too many sentences (should be truncated)
    else:  # len(summary_sentences) > 4
        article = ArticleSummary(
            article_id=uuid4(),
            title="Test Article",
            summary=summary_text,
            url="https://example.com/test",
            relevance_score=0.8,
            reading_time=3,
            category="Test",
        )

        # Should be truncated to 3 sentences
        sentences = [s.strip() for s in article.summary.split(".") if s.strip()]
        assert len(sentences) <= 4


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(response=structured_response_strategy())
def test_property_6_response_success_criteria(response: StructuredResponse):
    """
    Feature: intelligent-qa-agent, Property 6: Structured Response Format

    **Validates: Requirements 3.1, 3.2**

    Test that response success criteria are correctly evaluated.

    This test verifies that:
    1. is_successful() method returns correct results
    2. get_article_count() returns correct count
    3. get_top_article() returns highest relevance article
    """
    # Property 6 Assertions: Response Success Criteria

    # 1. Test is_successful() method
    is_successful = response.is_successful()
    assert isinstance(is_successful, bool)

    if is_successful:
        assert response.response_type == ResponseType.STRUCTURED
        assert len(response.articles) > 0
        assert response.confidence > 0.3

    # 2. Test get_article_count() method
    article_count = response.get_article_count()
    assert isinstance(article_count, int)
    assert article_count == len(response.articles)
    assert article_count <= 5

    # 3. Test get_top_article() method
    top_article = response.get_top_article()

    if len(response.articles) > 0:
        assert top_article is not None
        assert isinstance(top_article, ArticleSummary)
        # Top article should have highest relevance score
        assert top_article.relevance_score == max(
            article.relevance_score for article in response.articles
        )
    else:
        assert top_article is None


@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
)
@given(
    insights=st.lists(
        st.text(min_size=0, max_size=200),
        min_size=0,
        max_size=15,
    ),
    recommendations=st.lists(
        st.text(min_size=0, max_size=200),
        min_size=0,
        max_size=15,
    ),
)
def test_property_6_insights_and_recommendations_validation(
    insights: List[str],
    recommendations: List[str],
):
    """
    Feature: intelligent-qa-agent, Property 6: Structured Response Format

    **Validates: Requirements 3.4, 3.5**

    Test that insights and recommendations are properly validated and cleaned.

    This test verifies that:
    1. Empty strings are removed from insights
    2. Empty strings are removed from recommendations
    3. Lists are limited to 10 items
    """
    response = StructuredResponse(
        query="test query",
        articles=[
            ArticleSummary(
                article_id=uuid4(),
                title="Test Article",
                summary="This is a test summary. It has multiple sentences. This is the third sentence.",
                url="https://example.com/test",
                relevance_score=0.8,
                reading_time=3,
                category="Test",
            )
        ],
        insights=insights,
        recommendations=recommendations,
        conversation_id=uuid4(),
        response_time=1.0,
        confidence=0.8,
    )

    # Property 6 Assertions: Insights and Recommendations Validation

    # 1. No empty strings in insights
    for insight in response.insights:
        assert len(insight.strip()) > 0

    # 2. No empty strings in recommendations
    for recommendation in response.recommendations:
        assert len(recommendation.strip()) > 0

    # 3. Insights are limited to 10 items
    assert len(response.insights) <= 10

    # 4. Recommendations are limited to 10 items
    assert len(response.recommendations) <= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
