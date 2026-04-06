"""
Bug Condition Exploration Test: DM Notification Duplicates
===========================================================

This test is designed to run on UNFIXED code to confirm Bug 1 exists.

Bug Condition 1: DM Notifications Send Duplicate Articles
- User has subscriptions to feeds
- Articles exist in the last 7 days timeframe
- Articles are NOT filtered by sent status
- Same articles appear in multiple DM notifications

Expected Behavior (what the test asserts):
- For any DM notification request where articles have been previously sent,
  the system SHALL exclude those articles from the result set

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.

Expected Outcome: Test FAILS (this is correct - it proves the bug exists)

Validates: Requirements 1.1, 1.2, 2.1, 2.2
"""

import pytest
from datetime import datetime, timezone, timedelta
from hypothesis import given, strategies as st, settings, HealthCheck
from app.services.supabase_service import SupabaseService


class TestDMNotificationDuplicates:
    """
    Bug Condition Exploration: DM notifications send duplicate articles
    
    **Property 1: Bug Condition** - DM Notifications Send Duplicate Articles
    
    This test encodes the EXPECTED behavior (no duplicates).
    On unfixed code, this test will FAIL because duplicates ARE sent.
    After the fix is implemented, this test will PASS.
    """
    
    @pytest.mark.asyncio
    async def test_bug_condition_dm_notifications_send_duplicates(
        self,
        test_supabase_client,
        test_user,
        test_feed
    ):
        """
        Bug Condition Exploration: Verify that get_user_articles returns
        duplicate articles when called multiple times (proving the bug exists).
        
        Test Strategy:
        1. Create a user with a subscription to a feed
        2. Create 3 articles in the last 7 days
        3. Call get_user_articles() to simulate first DM notification
        4. Call get_user_articles() again to simulate second DM notification
        5. Assert that NO duplicates are returned (expected behavior)
        
        EXPECTED OUTCOME ON UNFIXED CODE: FAIL
        - The second call returns the same 3 articles (duplicates)
        - This proves the bug exists
        
        EXPECTED OUTCOME ON FIXED CODE: PASS
        - The second call returns 0 articles (no duplicates)
        - This proves the fix works
        
        **Validates: Requirements 1.1, 1.2, 2.1, 2.2**
        """
        # Setup: Create subscription
        test_supabase_client.table('user_subscriptions').insert({
            'user_id': test_user['id'],
            'feed_id': test_feed['id']
        }).execute()
        
        # Setup: Create 3 articles in the last 7 days
        now = datetime.now(timezone.utc)
        articles_created = []
        for i in range(3):
            article_url = f"https://test-article-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'Test Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=i)).isoformat(),
                'tinkering_index': 5 - i  # Descending order
            }).execute()
            articles_created.append(result.data[0])
        
        try:
            # Simulate first DM notification
            supabase_service = SupabaseService()
            first_notification_articles = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            # Verify first notification has 3 articles
            assert len(first_notification_articles) == 3, (
                f"First notification should have 3 articles, got {len(first_notification_articles)}"
            )
            
            # Extract article URLs from first notification
            first_notification_urls = {article.url for article in first_notification_articles}
            
            # Simulate second DM notification (same user, same time window)
            second_notification_articles = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            # Extract article URLs from second notification
            second_notification_urls = {article.url for article in second_notification_articles}
            
            # EXPECTED BEHAVIOR: No duplicates should be sent
            # The second notification should exclude articles from the first notification
            duplicates = first_notification_urls.intersection(second_notification_urls)
            
            # This assertion encodes the EXPECTED behavior (no duplicates)
            # On UNFIXED code, this will FAIL because duplicates ARE sent
            # On FIXED code, this will PASS because duplicates are excluded
            assert len(duplicates) == 0, (
                f"Bug Condition 1 confirmed: DM notifications send duplicate articles. "
                f"Found {len(duplicates)} duplicate articles in second notification: {duplicates}. "
                f"First notification had {len(first_notification_articles)} articles, "
                f"second notification had {len(second_notification_articles)} articles. "
                f"Expected: second notification should have 0 articles (all were sent in first notification)."
            )
            
            # Additional assertion: second notification should be empty
            assert len(second_notification_articles) == 0, (
                f"Bug Condition 1 confirmed: Second notification should have 0 articles "
                f"(all were sent in first notification), but got {len(second_notification_articles)} articles."
            )
            
        finally:
            # Cleanup: Delete articles
            for article in articles_created:
                try:
                    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                except Exception:
                    pass
    
    @pytest.mark.asyncio
    async def test_property_dm_notifications_exclude_sent_articles_simple(
        self,
        test_supabase_client,
        test_user,
        test_feed
    ):
        """
        Simplified Property-Based Test: Verify duplicate detection across
        multiple scenarios without using Hypothesis fixtures.
        
        **Property 1: Bug Condition** - DM Notifications Send Duplicate Articles
        
        This test manually tests multiple scenarios to verify the expected behavior.
        
        EXPECTED OUTCOME ON UNFIXED CODE: FAIL
        - Multiple scenarios will show duplicates are sent
        
        EXPECTED OUTCOME ON FIXED CODE: PASS
        - No duplicates found in any scenario
        
        **Validates: Requirements 2.1, 2.2**
        """
        # Test multiple scenarios manually
        scenarios = [
            (1, 1),  # 1 article, 1 day back
            (3, 2),  # 3 articles, 2 days back
            (5, 3),  # 5 articles, 3 days back
            (10, 5), # 10 articles, 5 days back
        ]
        
        for article_count, days_back in scenarios:
            # Setup: Create subscription (use upsert to avoid duplicates)
            test_supabase_client.table('user_subscriptions').upsert({
                'user_id': test_user['id'],
                'feed_id': test_feed['id']
            }, on_conflict='user_id,feed_id').execute()
            
            # Setup: Create articles
            now = datetime.now(timezone.utc)
            articles_created = []
            for i in range(article_count):
                article_url = f"https://test-article-{i}-{now.timestamp()}-{article_count}-{days_back}.com"
                result = test_supabase_client.table('articles').insert({
                    'feed_id': test_feed['id'],
                    'title': f'Test Article {i}',
                    'url': article_url,
                    'published_at': (now - timedelta(days=days_back)).isoformat(),
                    'tinkering_index': 5
                }).execute()
                articles_created.append(result.data[0])
            
            try:
                # Simulate first DM notification
                supabase_service = SupabaseService()
                first_articles = await supabase_service.get_user_articles(
                    discord_id=test_user['discord_id'],
                    days=7,
                    limit=20
                )
                
                first_urls = {article.url for article in first_articles}
                
                # Simulate second DM notification
                second_articles = await supabase_service.get_user_articles(
                    discord_id=test_user['discord_id'],
                    days=7,
                    limit=20
                )
                
                second_urls = {article.url for article in second_articles}
                
                # Property: No duplicates should be sent
                duplicates = first_urls.intersection(second_urls)
                
                assert len(duplicates) == 0, (
                    f"Property violation: DM notifications sent {len(duplicates)} duplicate articles. "
                    f"article_count={article_count}, days_back={days_back}, "
                    f"first_notification={len(first_articles)} articles, "
                    f"second_notification={len(second_articles)} articles, "
                    f"duplicates={duplicates}"
                )
                
            finally:
                # Cleanup: Delete articles
                for article in articles_created:
                    try:
                        test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                    except Exception:
                        pass
    
    @pytest.mark.asyncio
    async def test_bug_condition_new_articles_added_between_notifications(
        self,
        test_supabase_client,
        test_user,
        test_feed
    ):
        """
        Bug Condition Exploration: Verify behavior when new articles are added
        between notifications.
        
        Test Strategy:
        1. Create 3 articles and send first notification
        2. Add 2 new articles
        3. Send second notification
        4. Assert that ONLY the 2 new articles are returned (expected behavior)
        
        EXPECTED OUTCOME ON UNFIXED CODE: FAIL
        - The second notification returns all 5 articles (3 old + 2 new)
        - This proves the bug exists
        
        EXPECTED OUTCOME ON FIXED CODE: PASS
        - The second notification returns only 2 new articles
        - This proves the fix works
        
        **Validates: Requirements 2.1, 2.2**
        """
        # Setup: Create subscription
        test_supabase_client.table('user_subscriptions').insert({
            'user_id': test_user['id'],
            'feed_id': test_feed['id']
        }).execute()
        
        # Setup: Create 3 initial articles
        now = datetime.now(timezone.utc)
        initial_articles = []
        for i in range(3):
            article_url = f"https://test-article-initial-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'Initial Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=i)).isoformat(),
                'tinkering_index': 5
            }).execute()
            initial_articles.append(result.data[0])
        
        new_articles = []
        try:
            # Simulate first DM notification
            supabase_service = SupabaseService()
            first_notification = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            assert len(first_notification) == 3, (
                f"First notification should have 3 articles, got {len(first_notification)}"
            )
            
            first_urls = {article.url for article in first_notification}
            
            # Add 2 new articles
            for i in range(2):
                article_url = f"https://test-article-new-{i}-{now.timestamp()}.com"
                result = test_supabase_client.table('articles').insert({
                    'feed_id': test_feed['id'],
                    'title': f'New Article {i}',
                    'url': article_url,
                    'published_at': now.isoformat(),
                    'tinkering_index': 5
                }).execute()
                new_articles.append(result.data[0])
            
            # Simulate second DM notification
            second_notification = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            second_urls = {article.url for article in second_notification}
            
            # EXPECTED BEHAVIOR: Only new articles should be returned
            # Old articles should be excluded
            old_articles_in_second = first_urls.intersection(second_urls)
            
            assert len(old_articles_in_second) == 0, (
                f"Bug Condition 1 confirmed: Second notification contains {len(old_articles_in_second)} "
                f"old articles that were already sent: {old_articles_in_second}"
            )
            
            # Second notification should have exactly 2 articles (the new ones)
            assert len(second_notification) == 2, (
                f"Bug Condition 1 confirmed: Second notification should have 2 new articles, "
                f"got {len(second_notification)} articles. "
                f"Expected: only new articles, not old ones."
            )
            
        finally:
            # Cleanup: Delete articles
            for article in initial_articles + new_articles:
                try:
                    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                except Exception:
                    pass
