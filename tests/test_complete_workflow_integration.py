"""
Integration tests for complete workflow from article insertion to reading list management.
Task 15.1: 撰寫完整工作流程的整合測試

Tests the complete workflow:
- User creation
- Feed queries
- Article insertion (batch operations)
- Reading list management (save, update status, update rating)
- Reading list queries
- Subscription management

Uses real Supabase connection (test environment).
Tests multi-user scenarios and concurrent operations.
"""
import pytest
import os
import asyncio
from uuid import uuid4
from datetime import datetime
from supabase import Client

from app.services.supabase_service import SupabaseService
from app.core.exceptions import SupabaseServiceError


@pytest.mark.integration
class TestCompleteWorkflow:
    """Test complete workflow from article insertion to reading list management."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_single_user(
        self,
        test_supabase_client: Client,
        test_feed,
        cleanup_test_data
    ):
        """
        Test complete workflow for a single user:
        1. Create user
        2. Query active feeds
        3. Insert articles
        4. Save to reading list
        5. Update status
        6. Update rating
        7. Query reading list
        8. Query highly rated articles
        
        **Validates: Requirements 3.1-3.5, 4.1-4.6, 5.1-5.9, 6.1-6.8, 7.1-7.8, 8.1-8.8, 9.1-9.9, 10.1-10.8**
        """
        service = SupabaseService(client=test_supabase_client, validate_connection=False)
        
        # 1. Create user
        discord_id = f"test_user_{uuid4().hex}"
        user_uuid = await service.get_or_create_user(discord_id)
        cleanup_test_data['users'].append(str(user_uuid))
        
        assert user_uuid is not None
        
        # Verify idempotency
        user_uuid_2 = await service.get_or_create_user(discord_id)
        assert user_uuid == user_uuid_2
        
        # 2. Query active feeds
        feeds = await service.get_active_feeds()
        assert isinstance(feeds, list)
        assert len(feeds) > 0  # test_feed should be active
        
        # 3. Insert articles (batch operation)
        articles = [
            {
                'title': f'Test Article {i}',
                'url': f'https://test-article-{uuid4().hex}.com',
                'feed_id': str(test_feed['id']),
                'tinkering_index': i % 5 + 1,
                'ai_summary': f'Summary for article {i}'
            }
            for i in range(5)
        ]
        
        result = await service.insert_articles(articles)
        assert result.inserted_count == 5
        assert result.updated_count == 0
        assert result.failed_count == 0
        
        # Track articles for cleanup
        for article in articles:
            response = test_supabase_client.table('articles').select('id').eq('url', article['url']).execute()
            if response.data:
                cleanup_test_data['articles'].append(response.data[0]['id'])
        
        # 4. Save articles to reading list
        article_ids = []
        for article in articles:
            response = test_supabase_client.table('articles').select('id').eq('url', article['url']).execute()
            article_id = response.data[0]['id']
            article_ids.append(article_id)
            
            await service.save_to_reading_list(discord_id, article_id)
        
        # 5. Update status for some articles
        await service.update_article_status(discord_id, article_ids[0], 'Read')
        await service.update_article_status(discord_id, article_ids[1], 'Archived')
        
        # 6. Update rating for some articles
        await service.update_article_rating(discord_id, article_ids[0], 5)
        await service.update_article_rating(discord_id, article_ids[1], 4)
        await service.update_article_rating(discord_id, article_ids[2], 3)
        
        # 7. Query reading list
        all_items = await service.get_reading_list(discord_id)
        assert len(all_items) == 5
        
        # Verify ordering (newest first)
        for i in range(len(all_items) - 1):
            assert all_items[i].added_at >= all_items[i + 1].added_at
        
        # Query with status filter
        read_items = await service.get_reading_list(discord_id, status='Read')
        assert len(read_items) == 1
        assert read_items[0].status == 'Read'
        
        archived_items = await service.get_reading_list(discord_id, status='Archived')
        assert len(archived_items) == 1
        assert archived_items[0].status == 'Archived'
        
        unread_items = await service.get_reading_list(discord_id, status='Unread')
        assert len(unread_items) == 3
        
        # 8. Query highly rated articles
        highly_rated = await service.get_highly_rated_articles(discord_id, threshold=4)
        assert len(highly_rated) == 2
        
        # Verify ordering (rating desc, then added_at desc)
        assert highly_rated[0].rating >= highly_rated[1].rating
    
    @pytest.mark.asyncio
    async def test_multi_user_data_isolation(
        self,
        test_supabase_client: Client,
        test_feed,
        cleanup_test_data
    ):
        """
        Test that multiple users have isolated data:
        - Each user sees only their own reading list
        - Each user sees only their own subscriptions
        - Articles are shared but reading list entries are isolated
        
        **Validates: Requirements 3.1-3.5, 6.1-6.8, 9.1-9.9, 11.1-11.9, 12.1-12.7**
        """
        service = SupabaseService(client=test_supabase_client, validate_connection=False)
        
        # Create two users
        user1_discord_id = f"test_user_1_{uuid4().hex}"
        user2_discord_id = f"test_user_2_{uuid4().hex}"
        
        user1_uuid = await service.get_or_create_user(user1_discord_id)
        user2_uuid = await service.get_or_create_user(user2_discord_id)
        
        cleanup_test_data['users'].extend([str(user1_uuid), str(user2_uuid)])
        
        # Insert shared articles
        articles = [
            {
                'title': f'Shared Article {i}',
                'url': f'https://shared-article-{uuid4().hex}.com',
                'feed_id': str(test_feed['id'])
            }
            for i in range(3)
        ]
        
        result = await service.insert_articles(articles)
        assert result.inserted_count == 3
        
        # Track articles for cleanup
        article_ids = []
        for article in articles:
            response = test_supabase_client.table('articles').select('id').eq('url', article['url']).execute()
            article_id = response.data[0]['id']
            article_ids.append(article_id)
            cleanup_test_data['articles'].append(article_id)
        
        # User 1 saves articles 0 and 1
        await service.save_to_reading_list(user1_discord_id, article_ids[0])
        await service.save_to_reading_list(user1_discord_id, article_ids[1])
        
        # User 2 saves articles 1 and 2
        await service.save_to_reading_list(user2_discord_id, article_ids[1])
        await service.save_to_reading_list(user2_discord_id, article_ids[2])
        
        # Verify data isolation
        user1_reading_list = await service.get_reading_list(user1_discord_id)
        user2_reading_list = await service.get_reading_list(user2_discord_id)
        
        assert len(user1_reading_list) == 2
        assert len(user2_reading_list) == 2
        
        user1_article_ids = {str(item.article_id) for item in user1_reading_list}
        user2_article_ids = {str(item.article_id) for item in user2_reading_list}
        
        assert article_ids[0] in user1_article_ids
        assert article_ids[1] in user1_article_ids
        assert article_ids[0] not in user2_article_ids
        
        assert article_ids[1] in user2_article_ids
        assert article_ids[2] in user2_article_ids
        assert article_ids[2] not in user1_article_ids
        
        # Test subscription isolation
        await service.subscribe_to_feed(user1_discord_id, test_feed['id'])
        
        user1_subscriptions = await service.get_user_subscriptions(user1_discord_id)
        user2_subscriptions = await service.get_user_subscriptions(user2_discord_id)
        
        assert len(user1_subscriptions) == 1
        assert len(user2_subscriptions) == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(
        self,
        test_supabase_client: Client,
        test_feed,
        cleanup_test_data
    ):
        """
        Test concurrent operations:
        - Multiple users creating accounts simultaneously
        - Multiple users saving the same article simultaneously
        - Batch article insertion with concurrent updates
        
        **Validates: Requirements 3.1-3.5, 5.1-5.9, 6.1-6.8, 15.1-15.6**
        """
        service = SupabaseService(client=test_supabase_client, validate_connection=False)
        
        # Test 1: Concurrent user creation
        discord_ids = [f"concurrent_user_{i}_{uuid4().hex}" for i in range(10)]
        
        async def create_user(discord_id):
            return await service.get_or_create_user(discord_id)
        
        user_uuids = await asyncio.gather(*[create_user(did) for did in discord_ids])
        
        # Verify all users created
        assert len(user_uuids) == 10
        assert len(set(str(u) for u in user_uuids)) == 10  # All unique
        
        cleanup_test_data['users'].extend([str(u) for u in user_uuids])
        
        # Test 2: Concurrent article insertion
        articles_batch_1 = [
            {
                'title': f'Concurrent Article {i}',
                'url': f'https://concurrent-{uuid4().hex}.com',
                'feed_id': str(test_feed['id'])
            }
            for i in range(20)
        ]
        
        articles_batch_2 = [
            {
                'title': f'Concurrent Article {i} Updated',
                'url': article['url'],  # Same URL to test UPSERT
                'feed_id': str(test_feed['id'])
            }
            for i, article in enumerate(articles_batch_1[:10])
        ]
        
        # Insert both batches concurrently
        results = await asyncio.gather(
            service.insert_articles(articles_batch_1),
            service.insert_articles(articles_batch_2)
        )
        
        # Verify results
        total_inserted = sum(r.inserted_count for r in results)
        total_updated = sum(r.updated_count for r in results)
        total_failed = sum(r.failed_count for r in results)
        
        assert total_inserted + total_updated == 30  # 20 new + 10 updates
        assert total_failed == 0
        
        # Track articles for cleanup
        for article in articles_batch_1:
            response = test_supabase_client.table('articles').select('id').eq('url', article['url']).execute()
            if response.data:
                cleanup_test_data['articles'].append(response.data[0]['id'])
        
        # Test 3: Multiple users saving same article concurrently
        test_article = {
            'title': 'Shared Concurrent Article',
            'url': f'https://shared-concurrent-{uuid4().hex}.com',
            'feed_id': str(test_feed['id'])
        }
        
        result = await service.insert_articles([test_article])
        assert result.inserted_count == 1
        
        response = test_supabase_client.table('articles').select('id').eq('url', test_article['url']).execute()
        article_id = response.data[0]['id']
        cleanup_test_data['articles'].append(article_id)
        
        # All users save the same article concurrently
        async def save_article(discord_id):
            return await service.save_to_reading_list(discord_id, article_id)
        
        await asyncio.gather(*[save_article(did) for did in discord_ids])
        
        # Verify all users have the article in their reading list
        for discord_id in discord_ids:
            reading_list = await service.get_reading_list(discord_id)
            assert len(reading_list) == 1
            assert str(reading_list[0].article_id) == article_id
    
    @pytest.mark.asyncio
    async def test_subscription_management_workflow(
        self,
        test_supabase_client: Client,
        test_feed,
        cleanup_test_data
    ):
        """
        Test complete subscription management workflow:
        1. Subscribe to feed
        2. Query subscriptions
        3. Verify idempotency
        4. Unsubscribe from feed
        5. Verify unsubscription
        
        **Validates: Requirements 11.1-11.9, 12.1-12.7**
        """
        service = SupabaseService(client=test_supabase_client, validate_connection=False)
        
        discord_id = f"test_user_{uuid4().hex}"
        user_uuid = await service.get_or_create_user(discord_id)
        cleanup_test_data['users'].append(str(user_uuid))
        
        # Create additional test feeds
        test_feeds = []
        for i in range(3):
            feed_url = f"https://test-feed-{uuid4().hex}.com/rss.xml"
            feed_result = test_supabase_client.table('feeds').insert({
                'name': f'Test Feed {i}',
                'url': feed_url,
                'category': f'Category {i}',
                'is_active': True
            }).execute()
            test_feeds.append(feed_result.data[0])
            cleanup_test_data['feeds'].append(feed_result.data[0]['id'])
        
        # 1. Subscribe to feeds
        for feed in test_feeds:
            await service.subscribe_to_feed(discord_id, feed['id'])
        
        # 2. Query subscriptions
        subscriptions = await service.get_user_subscriptions(discord_id)
        assert len(subscriptions) == 3
        
        # Verify ordering (newest first)
        for i in range(len(subscriptions) - 1):
            assert subscriptions[i].subscribed_at >= subscriptions[i + 1].subscribed_at
        
        # 3. Test idempotency - subscribe again
        await service.subscribe_to_feed(discord_id, test_feeds[0]['id'])
        subscriptions = await service.get_user_subscriptions(discord_id)
        assert len(subscriptions) == 3  # Still 3, not 4
        
        # 4. Unsubscribe from one feed
        await service.unsubscribe_from_feed(discord_id, test_feeds[0]['id'])
        
        # 5. Verify unsubscription
        subscriptions = await service.get_user_subscriptions(discord_id)
        assert len(subscriptions) == 2
        
        subscription_feed_ids = {str(sub.feed_id) for sub in subscriptions}
        assert test_feeds[0]['id'] not in subscription_feed_ids
        assert test_feeds[1]['id'] in subscription_feed_ids
        assert test_feeds[2]['id'] in subscription_feed_ids
        
        # Test unsubscribe idempotency
        await service.unsubscribe_from_feed(discord_id, test_feeds[0]['id'])
        subscriptions = await service.get_user_subscriptions(discord_id)
        assert len(subscriptions) == 2  # Still 2
    
    @pytest.mark.asyncio
    async def test_batch_operations_with_partial_failures(
        self,
        test_supabase_client: Client,
        test_feed,
        cleanup_test_data
    ):
        """
        Test batch operations handle partial failures gracefully:
        - Some articles succeed, some fail
        - Failed articles are tracked
        - Successful articles are processed
        
        **Validates: Requirements 5.1-5.9, 15.1-15.4**
        """
        service = SupabaseService(client=test_supabase_client, validate_connection=False)
        
        # Mix of valid and invalid articles
        articles = [
            # Valid articles
            {
                'title': 'Valid Article 1',
                'url': f'https://valid-1-{uuid4().hex}.com',
                'feed_id': str(test_feed['id'])
            },
            # Invalid: missing URL
            {
                'title': 'Invalid Article - No URL',
                'feed_id': str(test_feed['id'])
            },
            # Valid article
            {
                'title': 'Valid Article 2',
                'url': f'https://valid-2-{uuid4().hex}.com',
                'feed_id': str(test_feed['id'])
            },
            # Invalid: bad URL format
            {
                'title': 'Invalid Article - Bad URL',
                'url': 'not-a-valid-url',
                'feed_id': str(test_feed['id'])
            },
            # Valid article
            {
                'title': 'Valid Article 3',
                'url': f'https://valid-3-{uuid4().hex}.com',
                'feed_id': str(test_feed['id'])
            },
        ]
        
        result = await service.insert_articles(articles)
        
        # Verify partial success
        assert result.inserted_count == 3
        assert result.failed_count == 2
        assert len(result.failed_articles) == 2
        
        # Verify failed articles are tracked
        for failed in result.failed_articles:
            assert 'article' in failed
            assert 'error' in failed
            assert 'error_type' in failed
        
        # Track successful articles for cleanup
        for article in articles:
            if 'url' in article and article['url'].startswith('https://valid'):
                response = test_supabase_client.table('articles').select('id').eq('url', article['url']).execute()
                if response.data:
                    cleanup_test_data['articles'].append(response.data[0]['id'])
    
    @pytest.mark.asyncio
    async def test_article_upsert_behavior(
        self,
        test_supabase_client: Client,
        test_feed,
        cleanup_test_data
    ):
        """
        Test article UPSERT behavior:
        - First insert creates new article
        - Second insert with same URL updates existing article
        - Updated fields are reflected
        
        **Validates: Requirements 5.1-5.9**
        """
        service = SupabaseService(client=test_supabase_client, validate_connection=False)
        
        article_url = f'https://upsert-test-{uuid4().hex}.com'
        
        # First insert
        article_v1 = {
            'title': 'Original Title',
            'url': article_url,
            'feed_id': str(test_feed['id']),
            'tinkering_index': 3,
            'ai_summary': 'Original summary'
        }
        
        result1 = await service.insert_articles([article_v1])
        assert result1.inserted_count == 1
        assert result1.updated_count == 0
        
        # Get article ID for cleanup
        response = test_supabase_client.table('articles').select('id, title, tinkering_index, ai_summary').eq('url', article_url).execute()
        article_id = response.data[0]['id']
        cleanup_test_data['articles'].append(article_id)
        
        assert response.data[0]['title'] == 'Original Title'
        assert response.data[0]['tinkering_index'] == 3
        assert response.data[0]['ai_summary'] == 'Original summary'
        
        # Second insert with same URL (update)
        article_v2 = {
            'title': 'Updated Title',
            'url': article_url,
            'feed_id': str(test_feed['id']),
            'tinkering_index': 5,
            'ai_summary': 'Updated summary'
        }
        
        result2 = await service.insert_articles([article_v2])
        assert result2.inserted_count == 0
        assert result2.updated_count == 1
        
        # Verify update
        response = test_supabase_client.table('articles').select('id, title, tinkering_index, ai_summary').eq('url', article_url).execute()
        assert len(response.data) == 1  # Still only one article
        assert response.data[0]['id'] == article_id  # Same ID
        assert response.data[0]['title'] == 'Updated Title'
        assert response.data[0]['tinkering_index'] == 5
        assert response.data[0]['ai_summary'] == 'Updated summary'
    
    @pytest.mark.asyncio
    async def test_reading_list_status_transitions(
        self,
        test_supabase_client: Client,
        test_feed,
        test_article,
        cleanup_test_data
    ):
        """
        Test reading list status transitions:
        - Unread -> Read -> Archived
        - Verify updated_at changes
        - Verify status filtering works at each stage
        
        **Validates: Requirements 7.1-7.8, 9.1-9.9**
        """
        service = SupabaseService(client=test_supabase_client, validate_connection=False)
        
        discord_id = f"test_user_{uuid4().hex}"
        user_uuid = await service.get_or_create_user(discord_id)
        cleanup_test_data['users'].append(str(user_uuid))
        
        article_id = test_article['id']
        
        # Save to reading list (initial status: Unread)
        await service.save_to_reading_list(discord_id, article_id)
        
        reading_list = await service.get_reading_list(discord_id)
        assert len(reading_list) == 1
        assert reading_list[0].status == 'Unread'
        initial_updated_at = reading_list[0].updated_at
        
        # Wait a moment to ensure timestamp difference
        await asyncio.sleep(0.1)
        
        # Transition to Read
        await service.update_article_status(discord_id, article_id, 'Read')
        
        reading_list = await service.get_reading_list(discord_id)
        assert reading_list[0].status == 'Read'
        assert reading_list[0].updated_at > initial_updated_at
        
        # Verify filtering
        read_items = await service.get_reading_list(discord_id, status='Read')
        assert len(read_items) == 1
        
        unread_items = await service.get_reading_list(discord_id, status='Unread')
        assert len(unread_items) == 0
        
        # Wait a moment
        await asyncio.sleep(0.1)
        read_updated_at = reading_list[0].updated_at
        
        # Transition to Archived
        await service.update_article_status(discord_id, article_id, 'Archived')
        
        reading_list = await service.get_reading_list(discord_id)
        assert reading_list[0].status == 'Archived'
        assert reading_list[0].updated_at > read_updated_at
        
        # Verify filtering
        archived_items = await service.get_reading_list(discord_id, status='Archived')
        assert len(archived_items) == 1
        
        read_items = await service.get_reading_list(discord_id, status='Read')
        assert len(read_items) == 0
    
    @pytest.mark.asyncio
    async def test_rating_workflow(
        self,
        test_supabase_client: Client,
        test_feed,
        cleanup_test_data
    ):
        """
        Test rating workflow:
        - Add multiple articles with different ratings
        - Query highly rated articles with different thresholds
        - Verify ordering (rating desc, then added_at desc)
        
        **Validates: Requirements 8.1-8.8, 10.1-10.8**
        """
        service = SupabaseService(client=test_supabase_client, validate_connection=False)
        
        discord_id = f"test_user_{uuid4().hex}"
        user_uuid = await service.get_or_create_user(discord_id)
        cleanup_test_data['users'].append(str(user_uuid))
        
        # Create articles with different ratings
        articles = []
        ratings = [5, 4, 3, 5, 2, 4, 1]
        
        for i, rating in enumerate(ratings):
            article = {
                'title': f'Article {i} - Rating {rating}',
                'url': f'https://rating-test-{uuid4().hex}.com',
                'feed_id': str(test_feed['id'])
            }
            articles.append(article)
        
        result = await service.insert_articles(articles)
        assert result.inserted_count == len(articles)
        
        # Get article IDs and save to reading list with ratings
        for i, article in enumerate(articles):
            response = test_supabase_client.table('articles').select('id').eq('url', article['url']).execute()
            article_id = response.data[0]['id']
            cleanup_test_data['articles'].append(article_id)
            
            await service.save_to_reading_list(discord_id, article_id)
            await service.update_article_rating(discord_id, article_id, ratings[i])
            
            # Small delay to ensure different added_at timestamps
            await asyncio.sleep(0.01)
        
        # Query highly rated (>= 4)
        highly_rated_4 = await service.get_highly_rated_articles(discord_id, threshold=4)
        assert len(highly_rated_4) == 4  # Two 5s and two 4s
        
        # Verify ordering: rating desc, then added_at desc
        for i in range(len(highly_rated_4) - 1):
            if highly_rated_4[i].rating == highly_rated_4[i + 1].rating:
                # Same rating, check added_at ordering
                assert highly_rated_4[i].added_at >= highly_rated_4[i + 1].added_at
            else:
                # Different rating, check rating ordering
                assert highly_rated_4[i].rating > highly_rated_4[i + 1].rating
        
        # Query highly rated (>= 5)
        highly_rated_5 = await service.get_highly_rated_articles(discord_id, threshold=5)
        assert len(highly_rated_5) == 2
        assert all(item.rating == 5 for item in highly_rated_5)
        
        # Query highly rated (>= 3)
        highly_rated_3 = await service.get_highly_rated_articles(discord_id, threshold=3)
        assert len(highly_rated_3) == 5  # 5, 4, 3, 5, 4
