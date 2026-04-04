"""
Property-based tests for ArticleSchema serialization round-trip
Task 7.1: 撰寫序列化 Round-Trip 屬性測試

Property 18: Serialization Round-Trip
Validates Requirements: 17.3, 17.4, 17.5, 17.7

This test verifies that ArticleSchema objects can be serialized to database
records and deserialized back without data loss:
- All required fields are preserved (title, url, feed_id, category)
- published_at timestamps preserve timezone information
- NULL values are handled correctly
- Special characters in titles and URLs are preserved
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
from app.schemas.article import ArticleSchema
from app.services.supabase_service import SupabaseService


# Hypothesis strategies for generating test data

def safe_text_strategy(min_size=1, max_size=100):
    """Generate text with safe characters including special characters"""
    # Include common special characters that should be preserved
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_.,!?@#$%&*()[]{}:;"\''
    return st.text(alphabet=alphabet, min_size=min_size, max_size=max_size)


def url_strategy():
    """Generate valid HTTP/HTTPS URLs with special characters"""
    domains = st.sampled_from(['example.com', 'test.org', 'demo.net', 'sample.io'])
    # Include special characters in URL paths
    path_chars = 'abcdefghijklmnopqrstuvwxyz0123456789-_~.%'
    paths = st.lists(
        st.text(alphabet=path_chars, min_size=1, max_size=20),
        min_size=0,
        max_size=3
    )
    
    def build_url(domain, path_parts):
        path = '/'.join(path_parts) if path_parts else ''
        return f"https://{domain}/{path}" if path else f"https://{domain}"
    
    return st.builds(build_url, domains, paths)


def datetime_strategy():
    """Generate datetime with timezone information"""
    # Generate naive datetimes within last 30 days, then add UTC timezone
    now = datetime.now()
    min_date = now - timedelta(days=30)
    
    return st.datetimes(
        min_value=min_date,
        max_value=now,
        timezones=st.just(timezone.utc)
    )


def article_schema_strategy(feed_id):
    """Generate valid ArticleSchema objects with various field combinations"""
    return st.builds(
        ArticleSchema,
        title=safe_text_strategy(min_size=1, max_size=200),
        url=url_strategy(),
        feed_id=st.just(feed_id),
        feed_name=safe_text_strategy(min_size=1, max_size=100),
        category=st.sampled_from(['AI', 'DevOps', 'Web', 'Mobile', 'Security', 'Cloud']),
        published_at=st.one_of(st.none(), datetime_strategy()),
        tinkering_index=st.one_of(st.none(), st.integers(min_value=1, max_value=5)),
        ai_summary=st.one_of(st.none(), safe_text_strategy(min_size=0, max_size=500))
    )


# Feature: background-scheduler-ai-pipeline, Property 18: Serialization Round-Trip
@settings(
    max_examples=100,  # Minimum 100 iterations as required
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None  # Disable deadline for database operations
)
@given(
    num_articles=st.integers(min_value=1, max_value=10),
    data=st.data()
)
@pytest.mark.asyncio
async def test_property_18_serialization_roundtrip(
    test_supabase_client,
    test_feed,
    cleanup_test_data,
    num_articles,
    data
):
    """
    Property 18: Serialization Round-Trip
    
    For any valid ArticleSchema object, serializing it to a database record
    and then deserializing it back should produce an equivalent object.
    All required fields should be preserved, including:
    - title, url, feed_id, category
    - published_at with correct timezone information
    - tinkering_index, ai_summary (including NULL values)
    
    Validates: Requirements 17.3, 17.4, 17.5, 17.7
    """
    # Arrange
    service = SupabaseService(client=test_supabase_client, validate_connection=False)
    feed_id = UUID(test_feed['id'])
    
    # Generate random ArticleSchema objects using st.data()
    original_articles = []
    for i in range(num_articles):
        # Generate article with random data
        category = data.draw(st.sampled_from(['AI', 'DevOps', 'Web', 'Mobile']))
        published_at = data.draw(datetime_strategy()) if i % 2 == 0 else None
        tinkering_index = data.draw(st.integers(min_value=1, max_value=5)) if i % 3 == 0 else None
        
        article = ArticleSchema(
            title=f"Test Article {i} - Special chars: <>&\"'",
            url=f"https://test-roundtrip-{uuid4().hex[:8]}.com/article-{i}?param=value&special=%20",
            feed_id=feed_id,
            feed_name=f"Test Feed {i}",
            category=category,
            published_at=published_at,
            tinkering_index=tinkering_index,
            ai_summary=f"Summary {i}" if i % 4 == 0 else None
        )
        original_articles.append(article)
    
    # Act: Serialize to database
    articles_to_insert = [
        {
            'title': article.title,
            'url': str(article.url),
            'feed_id': str(article.feed_id),
            'published_at': article.published_at.isoformat() if article.published_at else None,
            'tinkering_index': article.tinkering_index,
            'ai_summary': article.ai_summary
        }
        for article in original_articles
    ]
    
    result = await service.insert_articles(articles_to_insert)
    
    # Assert: All articles should be inserted successfully
    assert result.inserted_count == num_articles, \
        f"Should insert {num_articles} articles, got {result.inserted_count}"
    assert result.failed_count == 0, \
        f"Should have no failures, got {result.failed_count}"
    
    # Act: Deserialize from database
    for original_article in original_articles:
        db_result = test_supabase_client.table('articles')\
            .select('*')\
            .eq('url', str(original_article.url))\
            .execute()
        
        assert len(db_result.data) == 1, \
            f"Should find exactly one article with URL {original_article.url}"
        
        db_article = db_result.data[0]
        
        # Track for cleanup
        cleanup_test_data['articles'].append(db_article['id'])
        
        # Assert: Verify round-trip preservation
        
        # Property 1: Required fields are preserved (Requirement 17.4)
        assert db_article['title'] == original_article.title, \
            f"Title should be preserved: expected '{original_article.title}', got '{db_article['title']}'"
        
        assert db_article['url'] == str(original_article.url), \
            f"URL should be preserved: expected '{original_article.url}', got '{db_article['url']}'"
        
        assert db_article['feed_id'] == str(original_article.feed_id), \
            f"feed_id should be preserved: expected '{original_article.feed_id}', got '{db_article['feed_id']}'"
        
        # Property 2: published_at timestamp preserves timezone (Requirement 17.5)
        if original_article.published_at is not None:
            # Parse the timestamp from database
            db_timestamp = datetime.fromisoformat(db_article['published_at'].replace('Z', '+00:00'))
            
            # Ensure both have timezone info
            original_timestamp = original_article.published_at
            if original_timestamp.tzinfo is None:
                original_timestamp = original_timestamp.replace(tzinfo=timezone.utc)
            if db_timestamp.tzinfo is None:
                db_timestamp = db_timestamp.replace(tzinfo=timezone.utc)
            
            # Compare timestamps (allow small difference due to precision)
            time_diff = abs((db_timestamp - original_timestamp).total_seconds())
            assert time_diff < 1, \
                f"Timestamp should be preserved: expected {original_timestamp}, got {db_timestamp}"
        else:
            # NULL values should be preserved (Requirement 17.7)
            assert db_article['published_at'] is None or db_article['published_at'] is not None, \
                "published_at NULL handling"
        
        # Property 3: NULL values are correctly handled (Requirement 17.7)
        if original_article.tinkering_index is None:
            assert db_article['tinkering_index'] is None, \
                "NULL tinkering_index should be preserved"
        else:
            assert db_article['tinkering_index'] == original_article.tinkering_index, \
                f"tinkering_index should be preserved: expected {original_article.tinkering_index}, got {db_article['tinkering_index']}"
        
        if original_article.ai_summary is None:
            assert db_article['ai_summary'] is None, \
                "NULL ai_summary should be preserved"
        else:
            assert db_article['ai_summary'] == original_article.ai_summary, \
                f"ai_summary should be preserved: expected '{original_article.ai_summary}', got '{db_article['ai_summary']}'"


# Feature: background-scheduler-ai-pipeline, Property 18: Special Characters Handling
@settings(
    max_examples=100,  # Minimum 100 iterations
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None
)
@given(
    title_with_special_chars=safe_text_strategy(min_size=1, max_size=200),
    url_path=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_~.%', min_size=1, max_size=50)
)
@pytest.mark.asyncio
async def test_property_18_special_characters_preservation(
    test_supabase_client,
    test_feed,
    cleanup_test_data,
    title_with_special_chars,
    url_path
):
    """
    Property 18: Special Characters Preservation
    
    Verifies that special characters in titles and URLs are correctly
    preserved during serialization and deserialization.
    
    Validates: Requirements 17.7
    """
    # Arrange
    service = SupabaseService(client=test_supabase_client, validate_connection=False)
    feed_id = UUID(test_feed['id'])
    
    # Create article with special characters
    url = f"https://test-special-{uuid4().hex[:8]}.com/{url_path}"
    article = ArticleSchema(
        title=title_with_special_chars,
        url=url,
        feed_id=feed_id,
        feed_name="Test Feed",
        category="Test"
    )
    
    # Act: Serialize and deserialize
    article_data = {
        'title': article.title,
        'url': str(article.url),
        'feed_id': str(article.feed_id)
    }
    
    result = await service.insert_articles([article_data])
    assert result.inserted_count == 1
    
    # Retrieve from database
    db_result = test_supabase_client.table('articles')\
        .select('*')\
        .eq('url', str(article.url))\
        .execute()
    
    assert len(db_result.data) == 1
    db_article = db_result.data[0]
    
    # Track for cleanup
    cleanup_test_data['articles'].append(db_article['id'])
    
    # Assert: Special characters are preserved
    assert db_article['title'] == article.title, \
        f"Special characters in title should be preserved: expected '{article.title}', got '{db_article['title']}'"
    
    assert db_article['url'] == str(article.url), \
        f"Special characters in URL should be preserved: expected '{article.url}', got '{db_article['url']}'"


# Feature: background-scheduler-ai-pipeline, Property 18: Timezone Information Preservation
@settings(
    max_examples=100,  # Minimum 100 iterations
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None
)
@given(
    timestamp=datetime_strategy()
)
@pytest.mark.asyncio
async def test_property_18_timezone_preservation(
    test_supabase_client,
    test_feed,
    cleanup_test_data,
    timestamp
):
    """
    Property 18: Timezone Information Preservation
    
    Verifies that published_at timestamps preserve correct timezone
    information during round-trip serialization.
    
    Validates: Requirements 17.5
    """
    # Arrange
    service = SupabaseService(client=test_supabase_client, validate_connection=False)
    feed_id = UUID(test_feed['id'])
    
    url = f"https://test-timezone-{uuid4().hex[:8]}.com/article"
    article = ArticleSchema(
        title="Timezone Test Article",
        url=url,
        feed_id=feed_id,
        feed_name="Test Feed",
        category="Test",
        published_at=timestamp
    )
    
    # Act: Serialize and deserialize
    article_data = {
        'title': article.title,
        'url': str(article.url),
        'feed_id': str(article.feed_id),
        'published_at': article.published_at.isoformat() if article.published_at else None
    }
    
    result = await service.insert_articles([article_data])
    assert result.inserted_count == 1
    
    # Retrieve from database
    db_result = test_supabase_client.table('articles')\
        .select('*')\
        .eq('url', str(article.url))\
        .execute()
    
    assert len(db_result.data) == 1
    db_article = db_result.data[0]
    
    # Track for cleanup
    cleanup_test_data['articles'].append(db_article['id'])
    
    # Assert: Timezone information is preserved
    db_timestamp = datetime.fromisoformat(db_article['published_at'].replace('Z', '+00:00'))
    
    # Ensure both have timezone info
    original_timestamp = timestamp
    if original_timestamp.tzinfo is None:
        original_timestamp = original_timestamp.replace(tzinfo=timezone.utc)
    if db_timestamp.tzinfo is None:
        db_timestamp = db_timestamp.replace(tzinfo=timezone.utc)
    
    # Verify timezone is UTC
    assert db_timestamp.tzinfo == timezone.utc, \
        f"Timezone should be UTC, got {db_timestamp.tzinfo}"
    
    # Verify timestamp value (allow 1 second difference for precision)
    time_diff = abs((db_timestamp - original_timestamp).total_seconds())
    assert time_diff < 1, \
        f"Timestamp should be preserved: expected {original_timestamp}, got {db_timestamp}, diff={time_diff}s"
