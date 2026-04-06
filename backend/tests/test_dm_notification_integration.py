"""
Integration Test: DM Notification Flow
=======================================

This integration test verifies the complete DM notification flow works correctly
after the fix for Bug 1 (DM Notification Duplicates).

Test Coverage:
- Full flow: query articles → send DM → record sent articles → query again
- Multiple users receiving notifications simultaneously
- Weekly digest schedule with overlapping time windows
- Sent articles persist across service restarts
- Edge cases: empty sent articles, all articles sent, partial overlap

Validates: Requirements 2.1, 2.2, 3.1, 3.2, 3.3

IMPORTANT: These tests require the dm_sent_articles table migration to be applied.
If tests fail with "Could not find the table 'public.dm_sent_articles'", run:
    python3 tests/apply_dm_sent_articles_migration.py
And apply the SQL in Supabase SQL Editor.
"""

import pytest
import asyncio
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.supabase_service import SupabaseService
from app.services.dm_notification_service import DMNotificationService


# Check if migration is applied
def check_migration_applied():
    """Check if dm_sent_articles table exists"""
    try:
        from supabase import create_client
        from dotenv import load_dotenv
        load_dotenv()
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key or "dummy" in url.lower():
            return False
        
        client = create_client(url, key)
        client.table('dm_sent_articles').select('id').limit(1).execute()
        return True
    except Exception:
        return False


# Skip all tests if migration not applied
pytestmark = pytest.mark.skipif(
    not check_migration_applied(),
    reason="dm_sent_articles table migration not applied. Run: python3 tests/apply_dm_sent_articles_migration.py"
)


class TestDMNotificationIntegration:
    """
    Integration tests for DM notification flow
    
    These tests verify the complete end-to-end flow of DM notifications,
    including article querying, DM sending, tracking, and deduplication.
    """
    
    @pytest.mark.asyncio
    async def test_full_dm_notification_flow(
        self,
        test_supabase_client,
        test_user,
        test_feed
    ):
        """
        Integration Test: Full DM notification flow
        
        Test Strategy:
        1. Create user with subscription and articles
        2. Query articles (should return all articles)
        3. Simulate sending DM and recording sent articles
        4. Query articles again (should return no articles - all were sent)
        5. Add new articles
        6. Query articles again (should return only new articles)
        
        **Validates: Requirements 2.1, 2.2, 3.1, 3.2, 3.3**
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
            article_url = f"https://test-integration-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'Integration Test Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=i)).isoformat(),
                'tinkering_index': 5 - i
            }).execute()
            initial_articles.append(result.data[0])
        
        new_articles = []
        try:
            supabase_service = SupabaseService()
            
            # Step 1: First query - should return all 3 articles
            first_query = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            assert len(first_query) == 3, (
                f"First query should return 3 articles, got {len(first_query)}"
            )
            
            # Step 2: Record sent articles (simulating DM send)
            article_ids = [str(article.id) for article in first_query]
            await supabase_service.record_sent_articles(
                discord_id=test_user['discord_id'],
                article_ids=article_ids
            )
            
            # Step 3: Second query - should return 0 articles (all were sent)
            second_query = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            assert len(second_query) == 0, (
                f"Second query should return 0 articles (all were sent), "
                f"got {len(second_query)} articles"
            )
            
            # Step 4: Add 2 new articles
            for i in range(2):
                article_url = f"https://test-integration-new-{i}-{now.timestamp()}.com"
                result = test_supabase_client.table('articles').insert({
                    'feed_id': test_feed['id'],
                    'title': f'New Integration Article {i}',
                    'url': article_url,
                    'published_at': now.isoformat(),
                    'tinkering_index': 5
                }).execute()
                new_articles.append(result.data[0])
            
            # Step 5: Third query - should return only 2 new articles
            third_query = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            assert len(third_query) == 2, (
                f"Third query should return 2 new articles, got {len(third_query)} articles"
            )
            
            # Verify the returned articles are the new ones
            third_query_urls = {article.url for article in third_query}
            new_article_urls = {article['url'] for article in new_articles}
            
            assert third_query_urls == new_article_urls, (
                f"Third query should return only new articles. "
                f"Expected: {new_article_urls}, Got: {third_query_urls}"
            )
            
        finally:
            # Cleanup
            for article in initial_articles + new_articles:
                try:
                    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                except Exception:
                    pass
    
    @pytest.mark.asyncio
    async def test_multiple_users_simultaneous_notifications(
        self,
        test_supabase_client,
        test_feed
    ):
        """
        Integration Test: Multiple users receiving notifications simultaneously
        
        Test Strategy:
        1. Create 3 users with subscriptions
        2. Create articles
        3. Send notifications to all users simultaneously
        4. Verify each user's sent articles are tracked independently
        5. Verify subsequent queries exclude sent articles per user
        
        **Validates: Requirements 2.1, 2.2**
        """
        # Setup: Create 3 test users
        users = []
        for i in range(3):
            discord_id = f"test_multi_user_{i}_{datetime.now(timezone.utc).timestamp()}"
            result = test_supabase_client.table('users').insert({
                'discord_id': discord_id
            }).execute()
            users.append(result.data[0])
        
        # Setup: Create subscriptions for all users
        for user in users:
            test_supabase_client.table('user_subscriptions').insert({
                'user_id': user['id'],
                'feed_id': test_feed['id']
            }).execute()
        
        # Setup: Create 5 articles
        now = datetime.now(timezone.utc)
        articles = []
        for i in range(5):
            article_url = f"https://test-multi-user-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'Multi-User Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=i)).isoformat(),
                'tinkering_index': 5 - i
            }).execute()
            articles.append(result.data[0])
        
        try:
            supabase_service = SupabaseService()
            
            # Simulate simultaneous notifications to all users
            async def send_to_user(user):
                # Query articles
                user_articles = await supabase_service.get_user_articles(
                    discord_id=user['discord_id'],
                    days=7,
                    limit=20
                )
                
                # Record sent articles
                article_ids = [str(article.id) for article in user_articles]
                await supabase_service.record_sent_articles(
                    discord_id=user['discord_id'],
                    article_ids=article_ids
                )
                
                return len(user_articles)
            
            # Send to all users concurrently
            results = await asyncio.gather(*[send_to_user(user) for user in users])
            
            # Verify all users received 5 articles
            assert all(count == 5 for count in results), (
                f"All users should receive 5 articles, got: {results}"
            )
            
            # Verify subsequent queries return 0 articles for each user
            for user in users:
                subsequent_query = await supabase_service.get_user_articles(
                    discord_id=user['discord_id'],
                    days=7,
                    limit=20
                )
                
                assert len(subsequent_query) == 0, (
                    f"User {user['discord_id']} should have 0 articles after notification, "
                    f"got {len(subsequent_query)} articles"
                )
            
        finally:
            # Cleanup
            for article in articles:
                try:
                    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                except Exception:
                    pass
            for user in users:
                try:
                    test_supabase_client.table('users').delete().eq('id', user['id']).execute()
                except Exception:
                    pass
    
    @pytest.mark.asyncio
    async def test_weekly_digest_overlapping_time_windows(
        self,
        test_supabase_client,
        test_user,
        test_feed
    ):
        """
        Integration Test: Weekly digest schedule with overlapping time windows
        
        Test Strategy:
        1. Create articles spanning 14 days
        2. Send first notification (7-day window)
        3. Wait (simulated) and send second notification (7-day window)
        4. Verify overlapping articles are not sent twice
        
        **Validates: Requirements 2.1, 2.2, 3.2**
        """
        # Setup: Create subscription
        test_supabase_client.table('user_subscriptions').insert({
            'user_id': test_user['id'],
            'feed_id': test_feed['id']
        }).execute()
        
        # Setup: Create articles spanning 14 days
        now = datetime.now(timezone.utc)
        articles = []
        
        # Week 1 articles (days 7-13 ago)
        for i in range(3):
            article_url = f"https://test-week1-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'Week 1 Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=7 + i)).isoformat(),
                'tinkering_index': 5
            }).execute()
            articles.append(result.data[0])
        
        # Week 2 articles (days 0-6 ago) - these overlap with next week's window
        for i in range(3):
            article_url = f"https://test-week2-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'Week 2 Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=i)).isoformat(),
                'tinkering_index': 5
            }).execute()
            articles.append(result.data[0])
        
        try:
            supabase_service = SupabaseService()
            
            # First notification (should get all 6 articles within 7-day window)
            first_notification = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            # Only Week 2 articles should be in the 7-day window
            assert len(first_notification) == 3, (
                f"First notification should have 3 articles (Week 2 only), "
                f"got {len(first_notification)}"
            )
            
            # Record sent articles
            article_ids = [str(article.id) for article in first_notification]
            await supabase_service.record_sent_articles(
                discord_id=test_user['discord_id'],
                article_ids=article_ids
            )
            
            # Second notification (same 7-day window, should get 0 articles)
            second_notification = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            assert len(second_notification) == 0, (
                f"Second notification should have 0 articles (all were sent), "
                f"got {len(second_notification)} articles"
            )
            
        finally:
            # Cleanup
            for article in articles:
                try:
                    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                except Exception:
                    pass
    
    @pytest.mark.asyncio
    async def test_sent_articles_persist_across_service_restarts(
        self,
        test_supabase_client,
        test_user,
        test_feed
    ):
        """
        Integration Test: Sent articles persist across service restarts
        
        Test Strategy:
        1. Create articles and send notification
        2. Record sent articles
        3. Create new SupabaseService instance (simulating restart)
        4. Query articles with new instance
        5. Verify sent articles are still excluded
        
        **Validates: Requirements 2.1, 2.2**
        """
        # Setup: Create subscription
        test_supabase_client.table('user_subscriptions').insert({
            'user_id': test_user['id'],
            'feed_id': test_feed['id']
        }).execute()
        
        # Setup: Create articles
        now = datetime.now(timezone.utc)
        articles = []
        for i in range(3):
            article_url = f"https://test-persist-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'Persist Test Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=i)).isoformat(),
                'tinkering_index': 5
            }).execute()
            articles.append(result.data[0])
        
        try:
            # First service instance
            service1 = SupabaseService()
            
            # Query and record sent articles
            first_query = await service1.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            assert len(first_query) == 3
            
            article_ids = [str(article.id) for article in first_query]
            await service1.record_sent_articles(
                discord_id=test_user['discord_id'],
                article_ids=article_ids
            )
            
            # Simulate service restart by creating new instance
            service2 = SupabaseService()
            
            # Query with new instance - should still exclude sent articles
            second_query = await service2.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            assert len(second_query) == 0, (
                f"After service restart, sent articles should still be excluded. "
                f"Expected 0 articles, got {len(second_query)}"
            )
            
        finally:
            # Cleanup
            for article in articles:
                try:
                    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                except Exception:
                    pass
    
    @pytest.mark.asyncio
    async def test_edge_case_empty_sent_articles(
        self,
        test_supabase_client,
        test_user,
        test_feed
    ):
        """
        Integration Test: Edge case - empty sent articles
        
        Test Strategy:
        1. Create user with no sent articles history
        2. Query articles
        3. Verify all articles are returned (no exclusions)
        
        **Validates: Requirements 3.1, 3.2, 3.3**
        """
        # Setup: Create subscription
        test_supabase_client.table('user_subscriptions').insert({
            'user_id': test_user['id'],
            'feed_id': test_feed['id']
        }).execute()
        
        # Setup: Create articles
        now = datetime.now(timezone.utc)
        articles = []
        for i in range(5):
            article_url = f"https://test-empty-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'Empty Test Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=i)).isoformat(),
                'tinkering_index': 5
            }).execute()
            articles.append(result.data[0])
        
        try:
            supabase_service = SupabaseService()
            
            # Query articles (user has no sent articles history)
            query_result = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            # Should return all 5 articles
            assert len(query_result) == 5, (
                f"User with no sent articles should get all 5 articles, "
                f"got {len(query_result)}"
            )
            
        finally:
            # Cleanup
            for article in articles:
                try:
                    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                except Exception:
                    pass
    
    @pytest.mark.asyncio
    async def test_edge_case_all_articles_sent(
        self,
        test_supabase_client,
        test_user,
        test_feed
    ):
        """
        Integration Test: Edge case - all articles already sent
        
        Test Strategy:
        1. Create articles and mark all as sent
        2. Query articles
        3. Verify no articles are returned
        
        **Validates: Requirements 2.1, 2.2**
        """
        # Setup: Create subscription
        test_supabase_client.table('user_subscriptions').insert({
            'user_id': test_user['id'],
            'feed_id': test_feed['id']
        }).execute()
        
        # Setup: Create articles
        now = datetime.now(timezone.utc)
        articles = []
        for i in range(3):
            article_url = f"https://test-all-sent-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'All Sent Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=i)).isoformat(),
                'tinkering_index': 5
            }).execute()
            articles.append(result.data[0])
        
        try:
            supabase_service = SupabaseService()
            
            # Mark all articles as sent
            article_ids = [article['id'] for article in articles]
            await supabase_service.record_sent_articles(
                discord_id=test_user['discord_id'],
                article_ids=article_ids
            )
            
            # Query articles
            query_result = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            # Should return 0 articles
            assert len(query_result) == 0, (
                f"User with all articles sent should get 0 articles, "
                f"got {len(query_result)}"
            )
            
        finally:
            # Cleanup
            for article in articles:
                try:
                    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                except Exception:
                    pass
    
    @pytest.mark.asyncio
    async def test_edge_case_partial_overlap(
        self,
        test_supabase_client,
        test_user,
        test_feed
    ):
        """
        Integration Test: Edge case - partial overlap of sent articles
        
        Test Strategy:
        1. Create 5 articles
        2. Send notification with 3 articles
        3. Query again
        4. Verify only 2 unsent articles are returned
        
        **Validates: Requirements 2.1, 2.2**
        """
        # Setup: Create subscription
        test_supabase_client.table('user_subscriptions').insert({
            'user_id': test_user['id'],
            'feed_id': test_feed['id']
        }).execute()
        
        # Setup: Create 5 articles
        now = datetime.now(timezone.utc)
        articles = []
        for i in range(5):
            article_url = f"https://test-partial-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'Partial Overlap Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=i)).isoformat(),
                'tinkering_index': 5 - i
            }).execute()
            articles.append(result.data[0])
        
        try:
            supabase_service = SupabaseService()
            
            # Query all articles
            first_query = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            assert len(first_query) == 5
            
            # Mark only first 3 articles as sent
            sent_article_ids = [str(first_query[i].id) for i in range(3)]
            await supabase_service.record_sent_articles(
                discord_id=test_user['discord_id'],
                article_ids=sent_article_ids
            )
            
            # Query again
            second_query = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            # Should return only 2 unsent articles
            assert len(second_query) == 2, (
                f"After sending 3 of 5 articles, should have 2 remaining, "
                f"got {len(second_query)}"
            )
            
            # Verify the returned articles are the unsent ones
            second_query_ids = {str(article.id) for article in second_query}
            sent_ids_set = set(sent_article_ids)
            
            # No overlap between sent and returned
            assert len(second_query_ids.intersection(sent_ids_set)) == 0, (
                f"Returned articles should not include sent articles"
            )
            
        finally:
            # Cleanup
            for article in articles:
                try:
                    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                except Exception:
                    pass
    
    @pytest.mark.asyncio
    async def test_dm_notification_service_integration(
        self,
        test_supabase_client,
        test_feed
    ):
        """
        Integration Test: DMNotificationService with mocked Discord bot
        
        Test Strategy:
        1. Create user with numeric discord_id (required by Discord API)
        2. Create mock Discord bot
        3. Create DMNotificationService
        4. Send personalized digest
        5. Verify articles are recorded as sent
        6. Verify subsequent queries exclude sent articles
        
        **Validates: Requirements 2.1, 2.2**
        """
        # Setup: Create user with numeric discord_id (Discord IDs are integers)
        numeric_discord_id = "123456789012345678"  # Valid Discord ID format
        result = test_supabase_client.table('users').insert({
            'discord_id': numeric_discord_id
        }).execute()
        test_user = result.data[0]
        
        # Setup: Create subscription
        test_supabase_client.table('user_subscriptions').insert({
            'user_id': test_user['id'],
            'feed_id': test_feed['id']
        }).execute()
        
        # Setup: Create articles
        now = datetime.now(timezone.utc)
        articles = []
        for i in range(3):
            article_url = f"https://test-dm-service-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'DM Service Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=i)).isoformat(),
                'tinkering_index': 5
            }).execute()
            articles.append(result.data[0])
        
        try:
            # Create mock Discord bot and user
            mock_bot = MagicMock()
            mock_discord_user = AsyncMock()
            mock_discord_user.send = AsyncMock()
            mock_bot.fetch_user = AsyncMock(return_value=mock_discord_user)
            
            # Create DM notification service
            dm_service = DMNotificationService(mock_bot)
            
            # Send personalized digest
            success = await dm_service.send_personalized_digest(numeric_discord_id)
            
            assert success, "DM notification should succeed"
            
            # Verify Discord user was fetched
            mock_bot.fetch_user.assert_called_once_with(int(numeric_discord_id))
            
            # Verify DM was sent
            mock_discord_user.send.assert_called_once()
            
            # Verify articles are recorded as sent
            supabase_service = SupabaseService()
            subsequent_query = await supabase_service.get_user_articles(
                discord_id=numeric_discord_id,
                days=7,
                limit=20
            )
            
            assert len(subsequent_query) == 0, (
                f"After DM notification, all articles should be marked as sent. "
                f"Expected 0 articles, got {len(subsequent_query)}"
            )
            
        finally:
            # Cleanup
            for article in articles:
                try:
                    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                except Exception:
                    pass
            try:
                test_supabase_client.table('users').delete().eq('id', test_user['id']).execute()
            except Exception:
                pass
