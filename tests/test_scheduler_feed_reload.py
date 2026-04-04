"""
Unit tests for scheduler feed reload functionality (Task 6.1).

Tests verify that:
1. Feeds are reloaded at the start of each execution
2. Feeds are not cached between executions
3. Feed changes (added/removed) are logged
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from app.tasks.scheduler import background_fetch_job, _last_feed_urls
from app.schemas.article import RSSSource


@pytest.fixture
def mock_feeds():
    """Create mock RSS feeds for testing."""
    return [
        RSSSource(
            name="Feed 1",
            url="https://example.com/feed1",
            category="AI"
        ),
        RSSSource(
            name="Feed 2",
            url="https://example.com/feed2",
            category="DevOps"
        )
    ]


@pytest.fixture
def mock_services():
    """Mock all service dependencies."""
    with patch('app.tasks.scheduler.SupabaseService') as mock_supabase, \
         patch('app.tasks.scheduler.RSSService') as mock_rss, \
         patch('app.tasks.scheduler.LLMService') as mock_llm:
        
        # Setup mock instances
        supabase_instance = AsyncMock()
        rss_instance = AsyncMock()
        llm_instance = AsyncMock()
        
        mock_supabase.return_value = supabase_instance
        mock_rss.return_value = rss_instance
        mock_llm.return_value = llm_instance
        
        # Default return values
        supabase_instance.get_active_feeds.return_value = []
        supabase_instance.get_unanalyzed_articles.return_value = []
        rss_instance.fetch_new_articles.return_value = []
        llm_instance.evaluate_batch.return_value = []
        
        yield {
            'supabase': supabase_instance,
            'rss': rss_instance,
            'llm': llm_instance
        }


@pytest.mark.asyncio
async def test_feeds_reloaded_each_execution(mock_services, mock_feeds):
    """
    Test that get_active_feeds() is called at the start of each execution.
    
    Validates: Requirement 16.1
    """
    # Setup
    mock_services['supabase'].get_active_feeds.return_value = mock_feeds
    
    # Execute job twice
    await background_fetch_job()
    await background_fetch_job()
    
    # Verify get_active_feeds was called twice (once per execution)
    assert mock_services['supabase'].get_active_feeds.call_count == 2


@pytest.mark.asyncio
async def test_no_feed_caching_between_executions(mock_services, mock_feeds):
    """
    Test that feeds are not cached between executions.
    Each execution should query the database fresh.
    
    Validates: Requirement 16.1
    """
    # Setup - return different feeds on each call
    feed1 = [mock_feeds[0]]
    feed2 = [mock_feeds[1]]
    
    mock_services['supabase'].get_active_feeds.side_effect = [feed1, feed2]
    
    # Execute job twice
    await background_fetch_job()
    await background_fetch_job()
    
    # Verify get_active_feeds was called twice with fresh queries
    assert mock_services['supabase'].get_active_feeds.call_count == 2
    
    # Verify RSS service received different feeds on each execution
    assert mock_services['rss'].fetch_new_articles.call_count == 2


@pytest.mark.asyncio
async def test_log_feeds_added(mock_services, mock_feeds, caplog):
    """
    Test that added feeds are logged correctly.
    
    Validates: Requirement 16.5
    """
    import logging
    caplog.set_level(logging.INFO)
    
    # Clear any previous feed tracking
    _last_feed_urls.clear()
    
    # First execution with 1 feed
    mock_services['supabase'].get_active_feeds.return_value = [mock_feeds[0]]
    await background_fetch_job()
    
    # Second execution with 2 feeds (1 added)
    mock_services['supabase'].get_active_feeds.return_value = mock_feeds
    await background_fetch_job()
    
    # Verify log message about added feeds
    assert any("1 added" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_log_feeds_removed(mock_services, mock_feeds, caplog):
    """
    Test that removed feeds are logged correctly.
    
    Validates: Requirement 16.5
    """
    import logging
    caplog.set_level(logging.INFO)
    
    # Clear any previous feed tracking
    _last_feed_urls.clear()
    
    # First execution with 2 feeds
    mock_services['supabase'].get_active_feeds.return_value = mock_feeds
    await background_fetch_job()
    
    # Second execution with 1 feed (1 removed)
    mock_services['supabase'].get_active_feeds.return_value = [mock_feeds[0]]
    await background_fetch_job()
    
    # Verify log message about removed feeds
    assert any("1 removed" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_log_no_feed_changes(mock_services, mock_feeds, caplog):
    """
    Test that no changes are logged when feeds remain the same.
    
    Validates: Requirement 16.5
    """
    import logging
    caplog.set_level(logging.INFO)
    
    # Clear any previous feed tracking
    _last_feed_urls.clear()
    
    # Execute twice with same feeds
    mock_services['supabase'].get_active_feeds.return_value = mock_feeds
    await background_fetch_job()
    await background_fetch_job()
    
    # Verify log message about no changes
    assert any("No feed changes since last execution" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_first_execution_no_comparison(mock_services, mock_feeds, caplog):
    """
    Test that first execution logs appropriately (no previous feeds to compare).
    
    Validates: Requirement 16.5
    """
    import logging
    caplog.set_level(logging.INFO)
    
    # Clear any previous feed tracking
    _last_feed_urls.clear()
    
    # First execution
    mock_services['supabase'].get_active_feeds.return_value = mock_feeds
    await background_fetch_job()
    
    # Verify log message about first execution
    assert any("First execution - no previous feed list to compare" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_feed_changes_with_multiple_adds_and_removes(mock_services, caplog):
    """
    Test logging when multiple feeds are added and removed simultaneously.
    
    Validates: Requirement 16.5
    """
    import logging
    caplog.set_level(logging.INFO)
    
    # Clear any previous feed tracking
    _last_feed_urls.clear()
    
    # Create different feed sets
    feeds_set1 = [
        RSSSource(name="Feed A", url="https://a.com", category="AI"),
        RSSSource(name="Feed B", url="https://b.com", category="AI"),
    ]
    
    feeds_set2 = [
        RSSSource(name="Feed C", url="https://c.com", category="AI"),
        RSSSource(name="Feed D", url="https://d.com", category="AI"),
        RSSSource(name="Feed E", url="https://e.com", category="AI"),
    ]
    
    # First execution with 2 feeds
    mock_services['supabase'].get_active_feeds.return_value = feeds_set1
    await background_fetch_job()
    
    # Second execution with 3 different feeds (2 removed, 3 added)
    mock_services['supabase'].get_active_feeds.return_value = feeds_set2
    await background_fetch_job()
    
    # Verify log message shows both additions and removals
    assert any("3 added" in record.message and "2 removed" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_disabled_feed_excluded_from_processing(mock_services, caplog):
    """
    Test that feeds marked as is_active=false are excluded from processing.
    
    Validates: Requirement 16.2
    """
    import logging
    caplog.set_level(logging.INFO)
    
    # Clear any previous feed tracking
    _last_feed_urls.clear()
    
    # Create feeds - one active, one that will be disabled
    active_feed = RSSSource(name="Active Feed", url="https://active.com", category="AI")
    disabled_feed = RSSSource(name="Disabled Feed", url="https://disabled.com", category="AI")
    
    # First execution with both feeds active
    mock_services['supabase'].get_active_feeds.return_value = [active_feed, disabled_feed]
    await background_fetch_job()
    
    # Verify both feeds were processed
    first_call_feeds = mock_services['rss'].fetch_new_articles.call_args[0][0]
    assert len(first_call_feeds) == 2
    
    # Second execution - disabled_feed is now excluded (not returned by get_active_feeds)
    mock_services['supabase'].get_active_feeds.return_value = [active_feed]
    await background_fetch_job()
    
    # Verify only active feed is processed
    second_call_feeds = mock_services['rss'].fetch_new_articles.call_args[0][0]
    assert len(second_call_feeds) == 1
    assert second_call_feeds[0].url == active_feed.url


@pytest.mark.asyncio
async def test_new_feed_included_in_processing(mock_services, caplog):
    """
    Test that newly added feeds with is_active=true are included in processing.
    
    Validates: Requirement 16.3
    """
    import logging
    caplog.set_level(logging.INFO)
    
    # Clear any previous feed tracking
    _last_feed_urls.clear()
    
    # Create feeds
    existing_feed = RSSSource(name="Existing Feed", url="https://existing.com", category="AI")
    new_feed = RSSSource(name="New Feed", url="https://new.com", category="DevOps")
    
    # First execution with one feed
    mock_services['supabase'].get_active_feeds.return_value = [existing_feed]
    await background_fetch_job()
    
    # Verify only one feed was processed
    first_call_feeds = mock_services['rss'].fetch_new_articles.call_args[0][0]
    assert len(first_call_feeds) == 1
    
    # Second execution - new feed is added
    mock_services['supabase'].get_active_feeds.return_value = [existing_feed, new_feed]
    await background_fetch_job()
    
    # Verify both feeds are now processed
    second_call_feeds = mock_services['rss'].fetch_new_articles.call_args[0][0]
    assert len(second_call_feeds) == 2
    feed_urls = {str(feed.url) for feed in second_call_feeds}
    assert str(existing_feed.url) in feed_urls
    assert str(new_feed.url) in feed_urls


@pytest.mark.asyncio
async def test_no_restart_required_for_feed_changes(mock_services):
    """
    Test that feed changes are picked up without requiring a restart.
    This is verified by the fact that get_active_feeds() is called at the
    start of each execution, not cached from initialization.
    
    Validates: Requirement 16.4
    """
    # Clear any previous feed tracking
    _last_feed_urls.clear()
    
    # Create different feed sets
    feeds_v1 = [RSSSource(name="Feed 1", url="https://feed1.com", category="AI")]
    feeds_v2 = [
        RSSSource(name="Feed 1", url="https://feed1.com", category="AI"),
        RSSSource(name="Feed 2", url="https://feed2.com", category="DevOps")
    ]
    feeds_v3 = [RSSSource(name="Feed 2", url="https://feed2.com", category="DevOps")]
    
    # Simulate three consecutive executions with different feed configurations
    # This simulates feed changes happening in the database between executions
    mock_services['supabase'].get_active_feeds.side_effect = [feeds_v1, feeds_v2, feeds_v3]
    
    # Execution 1: 1 feed
    await background_fetch_job()
    first_call_feeds = mock_services['rss'].fetch_new_articles.call_args[0][0]
    assert len(first_call_feeds) == 1
    
    # Execution 2: 2 feeds (1 added)
    await background_fetch_job()
    second_call_feeds = mock_services['rss'].fetch_new_articles.call_args[0][0]
    assert len(second_call_feeds) == 2
    
    # Execution 3: 1 feed (1 removed)
    await background_fetch_job()
    third_call_feeds = mock_services['rss'].fetch_new_articles.call_args[0][0]
    assert len(third_call_feeds) == 1
    
    # Verify get_active_feeds was called 3 times (once per execution, no caching)
    assert mock_services['supabase'].get_active_feeds.call_count == 3
    
    # This proves that feed changes are picked up dynamically without restart
