"""
Property-based tests for SupabaseService.insert_articles method
Task 1.4: 撰寫 Supabase Service 增強功能的屬性測試

Property 6: Article Insertion Idempotence
Validates Requirements: 4.2, 4.3, 4.4

This test verifies that inserting the same URL multiple times doesn't create
duplicate records, and that UPSERT behavior works correctly:
- New URLs are inserted
- Existing URLs are updated
- No duplicate URL entries are created
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from uuid import uuid4
from app.services.supabase_service import SupabaseService


# Hypothesis strategies for generating test data
def valid_url_strategy():
    """Generate valid HTTP/HTTPS URLs"""
    domains = st.sampled_from(['example.com', 'test.org', 'demo.net', 'sample.io'])
    paths = st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-', min_size=1, max_size=20),
        min_size=0,
        max_size=3
    )
    
    def build_url(domain, path_parts):
        path = '/'.join(path_parts) if path_parts else ''
        return f"https://{domain}/{path}" if path else f"https://{domain}"
    
    return st.builds(build_url, domains, paths)


def article_data_strategy(feed_id):
    """Generate valid article data dictionaries"""
    return st.builds(
        lambda title, url: {
            'title': title,
            'url': url,
            'feed_id': str(feed_id)
        },
        title=st.text(min_size=1, max_size=200),
        url=valid_url_strategy()
    )


# Feature: background-scheduler-ai-pipeline, Property 6: Article Insertion Idempotence
@settings(
    max_examples=20,  # Use 20 iterations for faster test execution
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None  # Disable deadline for database operations
)
@given(
    num_unique_articles=st.integers(min_value=1, max_value=10),
    num_duplicate_insertions=st.integers(min_value=2, max_value=5)
)
@pytest.mark.asyncio
async def test_property_6_article_insertion_idempotence(
    test_supabase_client,
    test_feed,
    cleanup_test_data,
    num_unique_articles,
    num_duplicate_insertions
):
    """
    Property 6: Article Insertion Idempotence
    
    For any article, inserting it multiple times with the same URL should not
    create duplicate records. The UPSERT operation should:
    - Insert a new record if the URL doesn't exist
    - Update the existing record if the URL already exists
    - Never create duplicate URL entries
    
    Validates: Requirements 4.2, 4.3, 4.4
    """
    # Arrange
    service = SupabaseService(client=test_supabase_client, validate_connection=False)
    feed_id = test_feed['id']
    
    # Generate unique articles with distinct URLs
    articles = []
    urls_used = set()
    
    for i in range(num_unique_articles):
        # Generate a unique URL for this test
        unique_url = f"https://test-idempotence-{uuid4().hex[:8]}.com/article-{i}"
        urls_used.add(unique_url)
        
        article = {
            'title': f'Test Article {i}',
            'url': unique_url,
            'feed_id': str(feed_id)
        }
        articles.append(article)
    
    # Act: Insert the same articles multiple times
    all_results = []
    for insertion_round in range(num_duplicate_insertions):
        # Modify titles slightly to test update behavior
        articles_to_insert = [
            {
                **article,
                'title': f"{article['title']} - Round {insertion_round}"
            }
            for article in articles
        ]
        
        result = await service.insert_articles(articles_to_insert)
        all_results.append(result)
    
    # Assert: Verify idempotence properties
    
    # Property 1: First insertion should insert all articles
    first_result = all_results[0]
    assert first_result.inserted_count == num_unique_articles, \
        f"First insertion should insert {num_unique_articles} articles, got {first_result.inserted_count}"
    assert first_result.updated_count == 0, \
        f"First insertion should not update any articles, got {first_result.updated_count}"
    assert first_result.failed_count == 0, \
        f"First insertion should not fail, got {first_result.failed_count} failures"
    
    # Property 2: Subsequent insertions should update existing articles
    for i, result in enumerate(all_results[1:], start=2):
        assert result.inserted_count == 0, \
            f"Insertion round {i} should not insert new articles, got {result.inserted_count}"
        assert result.updated_count == num_unique_articles, \
            f"Insertion round {i} should update {num_unique_articles} articles, got {result.updated_count}"
        assert result.failed_count == 0, \
            f"Insertion round {i} should not fail, got {result.failed_count} failures"
    
    # Property 3: Database should contain exactly num_unique_articles records (no duplicates)
    for url in urls_used:
        db_result = test_supabase_client.table('articles').select('*').eq('url', url).execute()
        assert len(db_result.data) == 1, \
            f"URL {url} should appear exactly once in database, found {len(db_result.data)} times"
        
        # Track for cleanup
        if db_result.data:
            cleanup_test_data['articles'].append(db_result.data[0]['id'])
    
    # Property 4: Final titles should reflect the last update
    final_round = num_duplicate_insertions - 1
    for article in articles:
        url = article['url']
        db_result = test_supabase_client.table('articles').select('title').eq('url', url).execute()
        # Extract the article index from the original title
        original_title = article['title']  # e.g., 'Test Article 0'
        expected_title = f"{original_title} - Round {final_round}"
        actual_title = db_result.data[0]['title']
        assert actual_title == expected_title, \
            f"Article should have title from last update, expected '{expected_title}', got '{actual_title}'"


# Feature: background-scheduler-ai-pipeline, Property 6: Article Insertion Idempotence (Mixed Operations)
@settings(
    max_examples=20,  # Use 20 iterations for faster test execution
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None
)
@given(
    num_new_articles=st.integers(min_value=1, max_value=5),
    num_existing_articles=st.integers(min_value=1, max_value=5)
)
@pytest.mark.asyncio
async def test_property_6_mixed_insert_and_update(
    test_supabase_client,
    test_feed,
    cleanup_test_data,
    num_new_articles,
    num_existing_articles
):
    """
    Property 6: Article Insertion Idempotence (Mixed Operations)
    
    When inserting a batch containing both new and existing articles:
    - New articles should be inserted
    - Existing articles should be updated
    - The counts should be accurate
    - No duplicates should be created
    
    Validates: Requirements 4.2, 4.3, 4.4
    """
    # Arrange
    service = SupabaseService(client=test_supabase_client, validate_connection=False)
    feed_id = test_feed['id']
    
    # Step 1: Create some existing articles
    existing_articles = []
    for i in range(num_existing_articles):
        url = f"https://test-mixed-{uuid4().hex[:8]}.com/existing-{i}"
        article = {
            'title': f'Existing Article {i}',
            'url': url,
            'feed_id': str(feed_id)
        }
        existing_articles.append(article)
    
    # Insert existing articles
    first_result = await service.insert_articles(existing_articles)
    assert first_result.inserted_count == num_existing_articles
    
    # Track existing article URLs
    existing_urls = {article['url'] for article in existing_articles}
    
    # Step 2: Create a mixed batch (some new, some existing)
    mixed_batch = []
    
    # Add updated versions of existing articles
    for i, article in enumerate(existing_articles):
        updated_article = {
            **article,
            'title': f'Updated Article {i}'
        }
        mixed_batch.append(updated_article)
    
    # Add new articles
    new_articles = []
    for i in range(num_new_articles):
        url = f"https://test-mixed-{uuid4().hex[:8]}.com/new-{i}"
        article = {
            'title': f'New Article {i}',
            'url': url,
            'feed_id': str(feed_id)
        }
        new_articles.append(article)
        mixed_batch.append(article)
    
    new_urls = {article['url'] for article in new_articles}
    
    # Act: Insert mixed batch
    mixed_result = await service.insert_articles(mixed_batch)
    
    # Assert: Verify correct behavior
    
    # Property 1: Counts should be accurate
    assert mixed_result.inserted_count == num_new_articles, \
        f"Should insert {num_new_articles} new articles, got {mixed_result.inserted_count}"
    assert mixed_result.updated_count == num_existing_articles, \
        f"Should update {num_existing_articles} existing articles, got {mixed_result.updated_count}"
    assert mixed_result.failed_count == 0, \
        f"Should have no failures, got {mixed_result.failed_count}"
    
    # Property 2: Total processed should equal batch size
    assert mixed_result.total_processed == len(mixed_batch), \
        f"Total processed should be {len(mixed_batch)}, got {mixed_result.total_processed}"
    
    # Property 3: No duplicate URLs in database
    all_urls = existing_urls | new_urls
    for url in all_urls:
        db_result = test_supabase_client.table('articles').select('*').eq('url', url).execute()
        assert len(db_result.data) == 1, \
            f"URL {url} should appear exactly once, found {len(db_result.data)} times"
        
        # Track for cleanup
        if db_result.data:
            cleanup_test_data['articles'].append(db_result.data[0]['id'])
    
    # Property 4: Existing articles should have updated titles
    for i, article in enumerate(existing_articles):
        db_result = test_supabase_client.table('articles').select('title').eq('url', article['url']).execute()
        expected_title = f'Updated Article {i}'
        actual_title = db_result.data[0]['title']
        assert actual_title == expected_title, \
            f"Existing article {i} should be updated, expected '{expected_title}', got '{actual_title}'"
    
    # Property 5: New articles should exist with correct titles
    for i, article in enumerate(new_articles):
        db_result = test_supabase_client.table('articles').select('title').eq('url', article['url']).execute()
        assert len(db_result.data) == 1, f"New article {i} should exist in database"
        expected_title = f'New Article {i}'
        actual_title = db_result.data[0]['title']
        assert actual_title == expected_title, \
            f"New article {i} should have correct title, expected '{expected_title}', got '{actual_title}'"


# Feature: background-scheduler-ai-pipeline, Property 6: Article Insertion Idempotence (Concurrent-like)
@settings(
    max_examples=20,  # Use 20 iterations for faster test execution
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None
)
@given(
    num_insertions=st.integers(min_value=2, max_value=10)
)
@pytest.mark.asyncio
async def test_property_6_rapid_duplicate_insertions(
    test_supabase_client,
    test_feed,
    cleanup_test_data,
    num_insertions
):
    """
    Property 6: Article Insertion Idempotence (Rapid Duplicate Insertions)
    
    Simulates rapid duplicate insertions (like concurrent requests) to verify
    that UPSERT handles them correctly without creating duplicates.
    
    Validates: Requirements 4.2, 4.3, 4.4
    """
    # Arrange
    service = SupabaseService(client=test_supabase_client, validate_connection=False)
    feed_id = test_feed['id']
    
    # Create a single article
    url = f"https://test-rapid-{uuid4().hex[:8]}.com/article"
    article = {
        'title': 'Original Title',
        'url': url,
        'feed_id': str(feed_id)
    }
    
    # Act: Insert the same article multiple times rapidly
    results = []
    for i in range(num_insertions):
        # Modify title to simulate updates
        article_to_insert = {
            **article,
            'title': f'Title Version {i}'
        }
        result = await service.insert_articles([article_to_insert])
        results.append(result)
    
    # Assert: Verify idempotence
    
    # Property 1: First insertion should insert, rest should update
    assert results[0].inserted_count == 1, "First insertion should insert the article"
    assert results[0].updated_count == 0, "First insertion should not update"
    
    for i, result in enumerate(results[1:], start=2):
        assert result.inserted_count == 0, f"Insertion {i} should not insert"
        assert result.updated_count == 1, f"Insertion {i} should update"
        assert result.failed_count == 0, f"Insertion {i} should not fail"
    
    # Property 2: Database should contain exactly one record
    db_result = test_supabase_client.table('articles').select('*').eq('url', url).execute()
    assert len(db_result.data) == 1, \
        f"Should have exactly 1 article with URL {url}, found {len(db_result.data)}"
    
    # Track for cleanup
    if db_result.data:
        cleanup_test_data['articles'].append(db_result.data[0]['id'])
    
    # Property 3: Final title should be from last insertion
    expected_title = f'Title Version {num_insertions - 1}'
    actual_title = db_result.data[0]['title']
    assert actual_title == expected_title, \
        f"Final title should be '{expected_title}', got '{actual_title}'"


# Feature: background-scheduler-ai-pipeline, Property 6: Article Insertion Idempotence (With Optional Fields)
@settings(
    max_examples=20,  # Use 20 iterations for faster test execution
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None
)
@given(
    has_tinkering_index=st.booleans(),
    has_ai_summary=st.booleans(),
    tinkering_index=st.one_of(st.none(), st.integers(min_value=1, max_value=5)),
    num_updates=st.integers(min_value=1, max_value=5)
)
@pytest.mark.asyncio
async def test_property_6_upsert_with_optional_fields(
    test_supabase_client,
    test_feed,
    cleanup_test_data,
    has_tinkering_index,
    has_ai_summary,
    tinkering_index,
    num_updates
):
    """
    Property 6: Article Insertion Idempotence (With Optional Fields)
    
    Verifies that UPSERT correctly handles optional fields like tinkering_index
    and ai_summary during updates.
    
    Validates: Requirements 4.2, 4.3, 4.4
    """
    # Arrange
    service = SupabaseService(client=test_supabase_client, validate_connection=False)
    feed_id = test_feed['id']
    
    url = f"https://test-optional-{uuid4().hex[:8]}.com/article"
    
    # Initial article without optional fields
    initial_article = {
        'title': 'Initial Article',
        'url': url,
        'feed_id': str(feed_id)
    }
    
    # Insert initial article
    initial_result = await service.insert_articles([initial_article])
    assert initial_result.inserted_count == 1
    
    # Act: Update with optional fields
    for i in range(num_updates):
        updated_article = {
            'title': f'Updated Article {i}',
            'url': url,
            'feed_id': str(feed_id)
        }
        
        if has_tinkering_index and tinkering_index is not None:
            updated_article['tinkering_index'] = tinkering_index
        
        if has_ai_summary:
            updated_article['ai_summary'] = f'AI Summary Version {i}'
        
        result = await service.insert_articles([updated_article])
        
        # Assert: Should update, not insert
        assert result.inserted_count == 0, f"Update {i} should not insert"
        assert result.updated_count == 1, f"Update {i} should update"
        assert result.failed_count == 0, f"Update {i} should not fail"
    
    # Assert: Verify final state
    db_result = test_supabase_client.table('articles').select('*').eq('url', url).execute()
    assert len(db_result.data) == 1, "Should have exactly one article"
    
    article_data = db_result.data[0]
    
    # Track for cleanup
    cleanup_test_data['articles'].append(article_data['id'])
    
    # Property 1: No duplicates
    assert len(db_result.data) == 1, "Should not create duplicates"
    
    # Property 2: Title should be from last update
    expected_title = f'Updated Article {num_updates - 1}'
    assert article_data['title'] == expected_title, \
        f"Title should be '{expected_title}', got '{article_data['title']}'"
    
    # Property 3: Optional fields should be set if provided
    if has_tinkering_index and tinkering_index is not None:
        assert article_data['tinkering_index'] == tinkering_index, \
            f"tinkering_index should be {tinkering_index}, got {article_data['tinkering_index']}"
    
    if has_ai_summary:
        expected_summary = f'AI Summary Version {num_updates - 1}'
        assert article_data['ai_summary'] == expected_summary, \
            f"ai_summary should be '{expected_summary}', got '{article_data['ai_summary']}'"
