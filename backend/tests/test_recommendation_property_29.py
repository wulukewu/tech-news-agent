"""
Property-Based Test for Recommendation Service - Property 29

**Validates: Requirements 12.1, 12.4**

Property 29: Recommended Feeds Query
For any query for recommended feeds, the system SHALL filter feeds WHERE
is_recommended = true, and SHALL order results by recommendation_priority
in descending order.

This test uses Hypothesis to generate random feed data and verify that
the recommendation query correctly filters and sorts feeds.

**PREREQUISITE**: Migration 003 must be applied before running these tests.
To apply the migration, copy and paste the SQL from:
scripts/migrations/003_extend_feeds_table_for_recommendations.sql
into the Supabase SQL Editor and execute it.
"""

import pytest
from uuid import uuid4
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from supabase import create_client

from app.services.recommendation_service import RecommendationService, RecommendationServiceError
from app.schemas.recommendation import RecommendedFeed


# Load environment and check if migration is applied
load_dotenv()
_migration_applied = False

try:
    _url = os.getenv('SUPABASE_URL')
    _key = os.getenv('SUPABASE_KEY')
    if _url and _key:
        _client = create_client(_url, _key)
        _client.table('feeds').select('is_recommended').limit(1).execute()
        _migration_applied = True
except Exception:
    pass

# Skip all tests in this module if migration not applied
pytestmark = pytest.mark.skipif(
    not _migration_applied,
    reason="Migration 003 not applied. Please apply scripts/migrations/003_extend_feeds_table_for_recommendations.sql via Supabase SQL Editor."
)


# Strategy for generating feed categories
feed_categories = st.sampled_from(['AI', 'Web Development', 'Security', 'DevOps', 'Data Science'])

# Strategy for generating recommendation priorities (0-1000)
recommendation_priorities = st.integers(min_value=0, max_value=1000)


@pytest.mark.asyncio
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    is_recommended=st.booleans(),
    priority=recommendation_priorities
)
async def test_property_29_recommended_feeds_filtering(
    test_supabase_client,
    is_recommended,
    priority
):
    """
    Property 29: Recommended Feeds Query - Filtering
    
    For any feed with is_recommended flag, the system SHALL include it in
    recommended feeds query if and only if is_recommended = true.
    
    Test Strategy:
    1. Generate random is_recommended flag and priority
    2. Create a feed with these properties
    3. Query recommended feeds
    4. Verify feed is included only if is_recommended = true
    """
    # Arrange
    service = RecommendationService(test_supabase_client)
    
    # Create a test feed with random properties
    test_feed_url = f"https://test-feed-{uuid4().hex}.com/rss.xml"
    feed_result = test_supabase_client.table('feeds').insert({
        'name': f'Test Feed {uuid4().hex[:8]}',
        'url': test_feed_url,
        'category': 'Test Category',
        'is_active': False,
        'is_recommended': is_recommended,
        'recommendation_priority': priority,
        'description': 'Test feed for property testing'
    }).execute()
    
    feed = feed_result.data[0]
    feed_id = feed['id']
    
    try:
        # Act - Query recommended feeds
        recommended_feeds = await service.get_recommended_feeds()
        
        # Assert - Verify filtering
        feed_ids = [str(f.id) for f in recommended_feeds]
        
        if is_recommended:
            assert feed_id in feed_ids, \
                f"Feed with is_recommended=True should be included in recommended feeds"
        else:
            assert feed_id not in feed_ids, \
                f"Feed with is_recommended=False should NOT be included in recommended feeds"
    
    finally:
        # Cleanup
        test_supabase_client.table('feeds').delete().eq('id', feed_id).execute()


@pytest.mark.asyncio
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    priorities=st.lists(
        recommendation_priorities,
        min_size=2,
        max_size=10,
        unique=True
    )
)
async def test_property_29_recommended_feeds_ordering(
    test_supabase_client,
    priorities
):
    """
    Property 29: Recommended Feeds Query - Ordering
    
    For any set of recommended feeds with different priorities, the system
    SHALL order results by recommendation_priority in descending order
    (highest priority first).
    
    Test Strategy:
    1. Generate a list of unique priorities
    2. Create multiple recommended feeds with these priorities
    3. Query recommended feeds
    4. Verify feeds are ordered by priority (descending)
    """
    # Arrange
    service = RecommendationService(test_supabase_client)
    created_feed_ids = []
    
    try:
        # Create multiple recommended feeds with different priorities
        for priority in priorities:
            test_feed_url = f"https://test-feed-{uuid4().hex}.com/rss.xml"
            feed_result = test_supabase_client.table('feeds').insert({
                'name': f'Test Feed Priority {priority}',
                'url': test_feed_url,
                'category': 'Test Category',
                'is_active': False,
                'is_recommended': True,
                'recommendation_priority': priority,
                'description': f'Test feed with priority {priority}'
            }).execute()
            
            created_feed_ids.append(feed_result.data[0]['id'])
        
        # Act - Query recommended feeds
        recommended_feeds = await service.get_recommended_feeds()
        
        # Filter to only our test feeds
        test_feeds = [
            f for f in recommended_feeds
            if str(f.id) in created_feed_ids
        ]
        
        # Assert - Verify ordering (descending by priority)
        assert len(test_feeds) == len(priorities), \
            f"Expected {len(priorities)} test feeds, got {len(test_feeds)}"
        
        # Extract priorities from returned feeds
        returned_priorities = [f.recommendation_priority for f in test_feeds]
        
        # Verify they are in descending order
        expected_priorities = sorted(priorities, reverse=True)
        assert returned_priorities == expected_priorities, \
            f"Feeds should be ordered by priority (descending). " \
            f"Expected {expected_priorities}, got {returned_priorities}"
    
    finally:
        # Cleanup
        for feed_id in created_feed_ids:
            try:
                test_supabase_client.table('feeds').delete().eq('id', feed_id).execute()
            except Exception:
                pass


@pytest.mark.asyncio
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_recommended=st.integers(min_value=0, max_value=5),
    num_not_recommended=st.integers(min_value=0, max_value=5)
)
async def test_property_29_recommended_feeds_count(
    test_supabase_client,
    num_recommended,
    num_not_recommended
):
    """
    Property 29: Recommended Feeds Query - Count Accuracy
    
    For any combination of recommended and non-recommended feeds, the query
    SHALL return exactly the number of feeds where is_recommended = true.
    
    Test Strategy:
    1. Generate random counts of recommended and non-recommended feeds
    2. Create feeds with these properties
    3. Query recommended feeds
    4. Verify count matches number of is_recommended = true feeds
    """
    # Arrange
    service = RecommendationService(test_supabase_client)
    created_feed_ids = []
    
    try:
        # Create recommended feeds
        for i in range(num_recommended):
            test_feed_url = f"https://test-feed-rec-{uuid4().hex}.com/rss.xml"
            feed_result = test_supabase_client.table('feeds').insert({
                'name': f'Recommended Feed {i}',
                'url': test_feed_url,
                'category': 'Test Category',
                'is_active': False,
                'is_recommended': True,
                'recommendation_priority': i * 10,
                'description': 'Recommended test feed'
            }).execute()
            
            created_feed_ids.append(feed_result.data[0]['id'])
        
        # Create non-recommended feeds
        for i in range(num_not_recommended):
            test_feed_url = f"https://test-feed-notrec-{uuid4().hex}.com/rss.xml"
            feed_result = test_supabase_client.table('feeds').insert({
                'name': f'Not Recommended Feed {i}',
                'url': test_feed_url,
                'category': 'Test Category',
                'is_active': False,
                'is_recommended': False,
                'recommendation_priority': 0,
                'description': 'Non-recommended test feed'
            }).execute()
            
            created_feed_ids.append(feed_result.data[0]['id'])
        
        # Act - Query recommended feeds
        recommended_feeds = await service.get_recommended_feeds()
        
        # Filter to only our test feeds
        test_feeds = [
            f for f in recommended_feeds
            if str(f.id) in created_feed_ids
        ]
        
        # Assert - Verify count
        assert len(test_feeds) == num_recommended, \
            f"Expected {num_recommended} recommended feeds, got {len(test_feeds)}"
        
        # Verify all returned feeds have is_recommended = True
        for feed in test_feeds:
            assert feed.is_recommended is True, \
                f"All returned feeds should have is_recommended=True"
    
    finally:
        # Cleanup
        for feed_id in created_feed_ids:
            try:
                test_supabase_client.table('feeds').delete().eq('id', feed_id).execute()
            except Exception:
                pass


@pytest.mark.asyncio
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    category=feed_categories,
    priority=recommendation_priorities
)
async def test_property_29_recommended_feeds_with_category(
    test_supabase_client,
    category,
    priority
):
    """
    Property 29: Recommended Feeds Query - Category Preservation
    
    For any recommended feed with a category, the system SHALL preserve
    the category information in the query results.
    
    Test Strategy:
    1. Generate random category and priority
    2. Create a recommended feed with these properties
    3. Query recommended feeds
    4. Verify category is preserved in results
    """
    # Arrange
    service = RecommendationService(test_supabase_client)
    
    # Create a recommended feed with category
    test_feed_url = f"https://test-feed-{uuid4().hex}.com/rss.xml"
    feed_result = test_supabase_client.table('feeds').insert({
        'name': f'Test Feed {category}',
        'url': test_feed_url,
        'category': category,
        'is_active': False,
        'is_recommended': True,
        'recommendation_priority': priority,
        'description': f'Test feed in {category} category'
    }).execute()
    
    feed = feed_result.data[0]
    feed_id = feed['id']
    
    try:
        # Act - Query recommended feeds
        recommended_feeds = await service.get_recommended_feeds()
        
        # Find our test feed
        test_feed = next(
            (f for f in recommended_feeds if str(f.id) == feed_id),
            None
        )
        
        # Assert - Verify category is preserved
        assert test_feed is not None, \
            "Recommended feed should be in query results"
        
        assert test_feed.category == category, \
            f"Expected category '{category}', got '{test_feed.category}'"
        
        assert test_feed.recommendation_priority == priority, \
            f"Expected priority {priority}, got {test_feed.recommendation_priority}"
    
    finally:
        # Cleanup
        test_supabase_client.table('feeds').delete().eq('id', feed_id).execute()


@pytest.mark.asyncio
async def test_property_29_empty_recommended_feeds(
    test_supabase_client
):
    """
    Property 29: Recommended Feeds Query - Empty Result Handling
    
    When no feeds have is_recommended = true, the system SHALL return
    an empty list (not an error).
    
    Test Strategy:
    1. Ensure no recommended feeds exist (or create only non-recommended)
    2. Query recommended feeds
    3. Verify empty list is returned without errors
    """
    # Arrange
    service = RecommendationService(test_supabase_client)
    created_feed_ids = []
    
    try:
        # Create only non-recommended feeds
        for i in range(3):
            test_feed_url = f"https://test-feed-notrec-{uuid4().hex}.com/rss.xml"
            feed_result = test_supabase_client.table('feeds').insert({
                'name': f'Not Recommended Feed {i}',
                'url': test_feed_url,
                'category': 'Test Category',
                'is_active': False,
                'is_recommended': False,
                'recommendation_priority': 0
            }).execute()
            
            created_feed_ids.append(feed_result.data[0]['id'])
        
        # Act - Query recommended feeds
        recommended_feeds = await service.get_recommended_feeds()
        
        # Filter to only our test feeds
        test_feeds = [
            f for f in recommended_feeds
            if str(f.id) in created_feed_ids
        ]
        
        # Assert - Verify empty result
        assert len(test_feeds) == 0, \
            "Should return empty list when no recommended feeds exist"
        
        # Verify the query itself returns a list (not None or error)
        assert isinstance(recommended_feeds, list), \
            "Query should return a list even when empty"
    
    finally:
        # Cleanup
        for feed_id in created_feed_ids:
            try:
                test_supabase_client.table('feeds').delete().eq('id', feed_id).execute()
            except Exception:
                pass


@pytest.mark.asyncio
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    priorities=st.lists(
        recommendation_priorities,
        min_size=3,
        max_size=8
    )
)
async def test_property_29_recommended_feeds_stable_sort(
    test_supabase_client,
    priorities
):
    """
    Property 29: Recommended Feeds Query - Stable Sort with Duplicate Priorities
    
    For any set of recommended feeds with duplicate priorities, the system
    SHALL maintain a consistent ordering (stable sort).
    
    Test Strategy:
    1. Generate a list of priorities (may include duplicates)
    2. Create recommended feeds with these priorities
    3. Query recommended feeds multiple times
    4. Verify ordering is consistent across queries
    """
    # Arrange
    service = RecommendationService(test_supabase_client)
    created_feed_ids = []
    
    try:
        # Create recommended feeds with potentially duplicate priorities
        for i, priority in enumerate(priorities):
            test_feed_url = f"https://test-feed-{uuid4().hex}.com/rss.xml"
            feed_result = test_supabase_client.table('feeds').insert({
                'name': f'Test Feed {i} Priority {priority}',
                'url': test_feed_url,
                'category': 'Test Category',
                'is_active': False,
                'is_recommended': True,
                'recommendation_priority': priority,
                'description': f'Test feed {i} with priority {priority}'
            }).execute()
            
            created_feed_ids.append(feed_result.data[0]['id'])
        
        # Act - Query recommended feeds multiple times
        first_query = await service.get_recommended_feeds()
        second_query = await service.get_recommended_feeds()
        
        # Filter to only our test feeds
        first_test_feeds = [
            f for f in first_query
            if str(f.id) in created_feed_ids
        ]
        second_test_feeds = [
            f for f in second_query
            if str(f.id) in created_feed_ids
        ]
        
        # Assert - Verify consistent ordering
        first_priorities = [f.recommendation_priority for f in first_test_feeds]
        second_priorities = [f.recommendation_priority for f in second_test_feeds]
        
        # Verify both queries return same number of feeds
        assert len(first_test_feeds) == len(priorities), \
            f"Expected {len(priorities)} feeds in first query"
        assert len(second_test_feeds) == len(priorities), \
            f"Expected {len(priorities)} feeds in second query"
        
        # Verify priorities are in descending order
        assert first_priorities == sorted(first_priorities, reverse=True), \
            "First query should return feeds in descending priority order"
        assert second_priorities == sorted(second_priorities, reverse=True), \
            "Second query should return feeds in descending priority order"
        
        # Verify ordering is consistent between queries
        first_ids = [str(f.id) for f in first_test_feeds]
        second_ids = [str(f.id) for f in second_test_feeds]
        assert first_ids == second_ids, \
            "Ordering should be consistent across multiple queries"
    
    finally:
        # Cleanup
        for feed_id in created_feed_ids:
            try:
                test_supabase_client.table('feeds').delete().eq('id', feed_id).execute()
            except Exception:
                pass


@pytest.mark.asyncio
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    priority=recommendation_priorities
)
async def test_property_29_recommended_feeds_data_completeness(
    test_supabase_client,
    priority
):
    """
    Property 29: Recommended Feeds Query - Data Completeness
    
    For any recommended feed, the query SHALL return all required fields:
    id, name, url, category, description, is_recommended, recommendation_priority.
    
    Test Strategy:
    1. Generate random priority
    2. Create a recommended feed with all fields
    3. Query recommended feeds
    4. Verify all fields are present and correct in results
    """
    # Arrange
    service = RecommendationService(test_supabase_client)
    
    # Create a recommended feed with all fields
    test_feed_url = f"https://test-feed-{uuid4().hex}.com/rss.xml"
    test_name = f'Complete Test Feed {uuid4().hex[:8]}'
    test_category = 'Test Category'
    test_description = 'Complete test feed with all fields'
    
    feed_result = test_supabase_client.table('feeds').insert({
        'name': test_name,
        'url': test_feed_url,
        'category': test_category,
        'is_active': False,
        'is_recommended': True,
        'recommendation_priority': priority,
        'description': test_description
    }).execute()
    
    feed = feed_result.data[0]
    feed_id = feed['id']
    
    try:
        # Act - Query recommended feeds
        recommended_feeds = await service.get_recommended_feeds()
        
        # Find our test feed
        test_feed = next(
            (f for f in recommended_feeds if str(f.id) == feed_id),
            None
        )
        
        # Assert - Verify all fields are present and correct
        assert test_feed is not None, \
            "Recommended feed should be in query results"
        
        assert test_feed.name == test_name, \
            f"Expected name '{test_name}', got '{test_feed.name}'"
        
        assert test_feed.url == test_feed_url, \
            f"Expected url '{test_feed_url}', got '{test_feed.url}'"
        
        assert test_feed.category == test_category, \
            f"Expected category '{test_category}', got '{test_feed.category}'"
        
        assert test_feed.description == test_description, \
            f"Expected description '{test_description}', got '{test_feed.description}'"
        
        assert test_feed.is_recommended is True, \
            "is_recommended should be True"
        
        assert test_feed.recommendation_priority == priority, \
            f"Expected priority {priority}, got {test_feed.recommendation_priority}"
        
        # Verify the feed is a RecommendedFeed instance
        assert isinstance(test_feed, RecommendedFeed), \
            f"Expected RecommendedFeed instance, got {type(test_feed)}"
    
    finally:
        # Cleanup
        test_supabase_client.table('feeds').delete().eq('id', feed_id).execute()
