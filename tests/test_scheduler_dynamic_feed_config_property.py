"""
Property-based tests for Scheduler dynamic feed configuration
Task 6.3: 撰寫動態配置的屬性測試

Property 17: Dynamic Feed Configuration
Validates Requirements: 16.2, 16.3

This test verifies that the scheduler correctly handles dynamic feed configuration:
- Feeds marked as is_active=false are excluded from execution
- New feeds marked as is_active=true are included in execution
- Feed changes are reflected without requiring restart
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.tasks.scheduler import background_fetch_job
from app.schemas.article import RSSSource, BatchResult


# Hypothesis strategies for generating test data

@st.composite
def feed_state_strategy(draw):
    """
    Generate random feed states for testing dynamic configuration.
    
    Returns a RSSSource with:
    - name: str
    - url: str (unique)
    - category: str
    - is_active: bool (implicitly through inclusion/exclusion)
    """
    feed_id = uuid4().hex[:8]
    categories = ['AI', 'DevOps', 'Web', 'Mobile', 'Security', 'Cloud']
    
    return RSSSource(
        name=f"Feed {feed_id}",
        url=f"https://feed-{feed_id}.com/rss",
        category=draw(st.sampled_from(categories))
    )


@st.composite
def feed_change_scenario_strategy(draw):
    """
    Generate a scenario with feed changes between executions.
    
    Returns a dict with:
    - initial_feeds: List[RSSSource] - feeds in first execution
    - updated_feeds: List[RSSSource] - feeds in second execution
    - added_feeds: List[RSSSource] - feeds added (in updated but not initial)
    - removed_feeds: List[RSSSource] - feeds removed (in initial but not updated)
    """
    # Generate initial feeds (1-10 feeds)
    num_initial = draw(st.integers(min_value=1, max_value=10))
    initial_feeds = [draw(feed_state_strategy()) for _ in range(num_initial)]
    
    # Decide how many feeds to keep, add, and remove
    num_to_keep = draw(st.integers(min_value=0, max_value=num_initial))
    num_to_add = draw(st.integers(min_value=0, max_value=5))
    
    # Keep some feeds from initial
    kept_feeds = initial_feeds[:num_to_keep]
    removed_feeds = initial_feeds[num_to_keep:]
    
    # Generate new feeds to add
    added_feeds = [draw(feed_state_strategy()) for _ in range(num_to_add)]
    
    # Updated feeds = kept + added
    updated_feeds = kept_feeds + added_feeds
    
    return {
        'initial_feeds': initial_feeds,
        'updated_feeds': updated_feeds,
        'added_feeds': added_feeds,
        'removed_feeds': removed_feeds
    }


# Feature: background-scheduler-ai-pipeline, Property 17: Dynamic Feed Configuration
@settings(
    max_examples=100,  # Minimum 100 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None  # Disable deadline for async operations
)
@given(
    scenario=feed_change_scenario_strategy()
)
@pytest.mark.asyncio
async def test_property_17_dynamic_feed_configuration(scenario):
    """
    Property 17: Dynamic Feed Configuration
    
    For any feed marked as is_active=false, it should not appear in the next
    scheduler execution. For any new feed added with is_active=true, it should
    appear in the next scheduler execution.
    
    This test simulates two consecutive executions with different feed configurations
    and verifies that the scheduler correctly picks up the changes.
    
    Validates: Requirements 16.2, 16.3
    """
    initial_feeds = scenario['initial_feeds']
    updated_feeds = scenario['updated_feeds']
    added_feeds = scenario['added_feeds']
    removed_feeds = scenario['removed_feeds']
    
    # Skip if no changes occurred
    if not added_feeds and not removed_feeds:
        return
    
    # Track which feeds were processed in each execution
    first_execution_feeds = set()
    second_execution_feeds = set()
    execution_count = 0
    
    # Mock dependencies
    with patch('app.tasks.scheduler.SupabaseService') as mock_supabase_class, \
         patch('app.tasks.scheduler.RSSService') as mock_rss_class, \
         patch('app.tasks.scheduler.LLMService') as mock_llm_class, \
         patch('app.tasks.scheduler.settings') as mock_settings:
        
        # Configure settings
        mock_settings.batch_size = 50
        mock_settings.batch_split_threshold = 100
        mock_settings.rss_fetch_days = 7
        mock_settings.timezone = 'UTC'
        mock_settings.scheduler_cron = '0 */6 * * *'
        mock_settings.scheduler_timezone = 'UTC'
        
        # Setup Supabase mock
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase
        
        # Mock get_active_feeds to return different feeds on each call
        async def mock_get_active_feeds():
            nonlocal execution_count
            execution_count += 1
            if execution_count == 1:
                return initial_feeds
            else:
                return updated_feeds
        
        mock_supabase.get_active_feeds.side_effect = mock_get_active_feeds
        
        # Mock get_unanalyzed_articles to return empty list
        mock_supabase.get_unanalyzed_articles.return_value = []
        
        # Setup RSS mock
        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss
        
        # Mock fetch_new_articles to track which feeds were processed
        async def mock_fetch_new_articles(feeds, supabase_service):
            nonlocal execution_count
            if execution_count == 1:
                for feed in feeds:
                    first_execution_feeds.add(feed.url)
            else:
                for feed in feeds:
                    second_execution_feeds.add(feed.url)
            return []  # Return no new articles
        
        mock_rss.fetch_new_articles.side_effect = mock_fetch_new_articles
        
        # Setup LLM mock
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.evaluate_batch.return_value = []
        
        # Mock insert_articles
        mock_supabase.insert_articles.return_value = BatchResult(
            inserted_count=0,
            updated_count=0,
            failed_count=0,
            failed_articles=[]
        )
        
        # Act: Run the background job twice (simulating two scheduled executions)
        await background_fetch_job()  # First execution
        await background_fetch_job()  # Second execution
    
    # Assert: Verify dynamic feed configuration behavior
    
    # Property 1: Removed feeds should not appear in second execution
    for removed_feed in removed_feeds:
        assert removed_feed.url not in second_execution_feeds, \
            f"Removed feed {removed_feed.url} should not appear in second execution"
    
    # Property 2: Added feeds should appear in second execution
    for added_feed in added_feeds:
        assert added_feed.url in second_execution_feeds, \
            f"Added feed {added_feed.url} should appear in second execution"
    
    # Property 3: Removed feeds should have appeared in first execution
    for removed_feed in removed_feeds:
        assert removed_feed.url in first_execution_feeds, \
            f"Removed feed {removed_feed.url} should have appeared in first execution"
    
    # Property 4: Added feeds should not have appeared in first execution
    for added_feed in added_feeds:
        assert added_feed.url not in first_execution_feeds, \
            f"Added feed {added_feed.url} should not have appeared in first execution"


# Feature: background-scheduler-ai-pipeline, Property 17: Dynamic Feed Configuration (Deactivation)
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None
)
@given(
    num_feeds=st.integers(min_value=2, max_value=10),
    num_to_deactivate=st.integers(min_value=1, max_value=5)
)
@pytest.mark.asyncio
async def test_property_17_feed_deactivation(num_feeds, num_to_deactivate):
    """
    Property 17: Dynamic Feed Configuration - Feed Deactivation
    
    For any set of feeds where some are marked as is_active=false,
    those feeds should not appear in the next execution.
    
    Validates: Requirements 16.2
    """
    # Ensure we don't try to deactivate more feeds than we have
    num_to_deactivate = min(num_to_deactivate, num_feeds - 1)
    
    # Generate initial feeds (all active)
    all_feeds = []
    for i in range(num_feeds):
        all_feeds.append(RSSSource(
            name=f"Feed {i}",
            url=f"https://feed-{uuid4().hex[:8]}.com/rss",
            category="AI"
        ))
    
    # Select feeds to deactivate
    deactivated_feeds = all_feeds[:num_to_deactivate]
    active_feeds = all_feeds[num_to_deactivate:]
    
    # Track which feeds were processed
    first_execution_feeds = set()
    second_execution_feeds = set()
    execution_count = 0
    
    # Mock dependencies
    with patch('app.tasks.scheduler.SupabaseService') as mock_supabase_class, \
         patch('app.tasks.scheduler.RSSService') as mock_rss_class, \
         patch('app.tasks.scheduler.LLMService') as mock_llm_class, \
         patch('app.tasks.scheduler.settings') as mock_settings:
        
        # Configure settings
        mock_settings.batch_size = 50
        mock_settings.batch_split_threshold = 100
        mock_settings.rss_fetch_days = 7
        mock_settings.timezone = 'UTC'
        mock_settings.scheduler_cron = '0 */6 * * *'
        mock_settings.scheduler_timezone = 'UTC'
        
        # Setup Supabase mock
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase
        
        # Mock get_active_feeds
        async def mock_get_active_feeds():
            nonlocal execution_count
            execution_count += 1
            if execution_count == 1:
                return all_feeds  # All feeds active
            else:
                return active_feeds  # Some feeds deactivated
        
        mock_supabase.get_active_feeds.side_effect = mock_get_active_feeds
        mock_supabase.get_unanalyzed_articles.return_value = []
        
        # Setup RSS mock
        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss
        
        async def mock_fetch_new_articles(feeds, supabase_service):
            nonlocal execution_count
            if execution_count == 1:
                for feed in feeds:
                    first_execution_feeds.add(feed.url)
            else:
                for feed in feeds:
                    second_execution_feeds.add(feed.url)
            return []
        
        mock_rss.fetch_new_articles.side_effect = mock_fetch_new_articles
        
        # Setup LLM mock
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.evaluate_batch.return_value = []
        
        mock_supabase.insert_articles.return_value = BatchResult(
            inserted_count=0,
            updated_count=0,
            failed_count=0,
            failed_articles=[]
        )
        
        # Act: Run the background job twice
        await background_fetch_job()  # First execution - all feeds
        await background_fetch_job()  # Second execution - some deactivated
    
    # Assert: Verify deactivation behavior
    
    # Property 1: All feeds should appear in first execution
    assert len(first_execution_feeds) == num_feeds, \
        f"Expected {num_feeds} feeds in first execution, got {len(first_execution_feeds)}"
    
    # Property 2: Only active feeds should appear in second execution
    assert len(second_execution_feeds) == len(active_feeds), \
        f"Expected {len(active_feeds)} active feeds in second execution, got {len(second_execution_feeds)}"
    
    # Property 3: Deactivated feeds should not appear in second execution
    for deactivated_feed in deactivated_feeds:
        assert deactivated_feed.url not in second_execution_feeds, \
            f"Deactivated feed {deactivated_feed.url} should not appear in second execution"
    
    # Property 4: Active feeds should appear in second execution
    for active_feed in active_feeds:
        assert active_feed.url in second_execution_feeds, \
            f"Active feed {active_feed.url} should appear in second execution"


# Feature: background-scheduler-ai-pipeline, Property 17: Dynamic Feed Configuration (Activation)
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None
)
@given(
    num_initial_feeds=st.integers(min_value=1, max_value=8),
    num_new_feeds=st.integers(min_value=1, max_value=5)
)
@pytest.mark.asyncio
async def test_property_17_feed_activation(num_initial_feeds, num_new_feeds):
    """
    Property 17: Dynamic Feed Configuration - Feed Activation
    
    For any new feed added with is_active=true, it should appear in the
    next scheduler execution without requiring restart.
    
    Validates: Requirements 16.3
    """
    # Generate initial feeds
    initial_feeds = []
    for i in range(num_initial_feeds):
        initial_feeds.append(RSSSource(
            name=f"Initial Feed {i}",
            url=f"https://initial-{uuid4().hex[:8]}.com/rss",
            category="AI"
        ))
    
    # Generate new feeds to add
    new_feeds = []
    for i in range(num_new_feeds):
        new_feeds.append(RSSSource(
            name=f"New Feed {i}",
            url=f"https://new-{uuid4().hex[:8]}.com/rss",
            category="DevOps"
        ))
    
    # Combined feeds for second execution
    all_feeds = initial_feeds + new_feeds
    
    # Track which feeds were processed
    first_execution_feeds = set()
    second_execution_feeds = set()
    execution_count = 0
    
    # Mock dependencies
    with patch('app.tasks.scheduler.SupabaseService') as mock_supabase_class, \
         patch('app.tasks.scheduler.RSSService') as mock_rss_class, \
         patch('app.tasks.scheduler.LLMService') as mock_llm_class, \
         patch('app.tasks.scheduler.settings') as mock_settings:
        
        # Configure settings
        mock_settings.batch_size = 50
        mock_settings.batch_split_threshold = 100
        mock_settings.rss_fetch_days = 7
        mock_settings.timezone = 'UTC'
        mock_settings.scheduler_cron = '0 */6 * * *'
        mock_settings.scheduler_timezone = 'UTC'
        
        # Setup Supabase mock
        mock_supabase = AsyncMock()
        mock_supabase_class.return_value = mock_supabase
        
        # Mock get_active_feeds
        async def mock_get_active_feeds():
            nonlocal execution_count
            execution_count += 1
            if execution_count == 1:
                return initial_feeds  # Only initial feeds
            else:
                return all_feeds  # Initial + new feeds
        
        mock_supabase.get_active_feeds.side_effect = mock_get_active_feeds
        mock_supabase.get_unanalyzed_articles.return_value = []
        
        # Setup RSS mock
        mock_rss = AsyncMock()
        mock_rss_class.return_value = mock_rss
        
        async def mock_fetch_new_articles(feeds, supabase_service):
            nonlocal execution_count
            if execution_count == 1:
                for feed in feeds:
                    first_execution_feeds.add(feed.url)
            else:
                for feed in feeds:
                    second_execution_feeds.add(feed.url)
            return []
        
        mock_rss.fetch_new_articles.side_effect = mock_fetch_new_articles
        
        # Setup LLM mock
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm
        mock_llm.evaluate_batch.return_value = []
        
        mock_supabase.insert_articles.return_value = BatchResult(
            inserted_count=0,
            updated_count=0,
            failed_count=0,
            failed_articles=[]
        )
        
        # Act: Run the background job twice
        await background_fetch_job()  # First execution - initial feeds only
        await background_fetch_job()  # Second execution - initial + new feeds
    
    # Assert: Verify activation behavior
    
    # Property 1: Only initial feeds should appear in first execution
    assert len(first_execution_feeds) == num_initial_feeds, \
        f"Expected {num_initial_feeds} feeds in first execution, got {len(first_execution_feeds)}"
    
    # Property 2: All feeds (initial + new) should appear in second execution
    assert len(second_execution_feeds) == len(all_feeds), \
        f"Expected {len(all_feeds)} feeds in second execution, got {len(second_execution_feeds)}"
    
    # Property 3: New feeds should not appear in first execution
    for new_feed in new_feeds:
        assert new_feed.url not in first_execution_feeds, \
            f"New feed {new_feed.url} should not appear in first execution"
    
    # Property 4: New feeds should appear in second execution
    for new_feed in new_feeds:
        assert new_feed.url in second_execution_feeds, \
            f"New feed {new_feed.url} should appear in second execution"
    
    # Property 5: Initial feeds should appear in both executions
    for initial_feed in initial_feeds:
        assert initial_feed.url in first_execution_feeds, \
            f"Initial feed {initial_feed.url} should appear in first execution"
        assert initial_feed.url in second_execution_feeds, \
            f"Initial feed {initial_feed.url} should appear in second execution"
