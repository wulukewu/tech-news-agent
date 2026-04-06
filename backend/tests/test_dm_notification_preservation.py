"""
Preservation Property Tests: DM Notification Behavior
======================================================

This test is designed to run on UNFIXED code to establish baseline behavior
that must be preserved after implementing the fix.

**Property 2: Preservation** - Non-Buggy DM Notification Behavior

For users with NO previously sent articles (first-time users), the system must:
- Return all articles in the time window (last 7 days)
- Filter by subscribed feeds only
- Limit results to max 20 articles
- Order by tinkering_index DESC

IMPORTANT: Follow observation-first methodology
- These tests capture the CURRENT behavior on unfixed code
- They should PASS on unfixed code (establishing baseline)
- They should PASS on fixed code (confirming preservation)

Expected Outcome: Tests PASS (confirms baseline behavior to preserve)

Validates: Requirements 3.1, 3.2, 3.3
"""

import pytest
from datetime import datetime, timezone, timedelta
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from app.services.supabase_service import SupabaseService


class TestDMNotificationPreservation:
    """
    Preservation Property Tests: Non-Buggy DM Notification Behavior
    
    **Property 2: Preservation** - For first-time users (no sent articles),
    the system SHALL produce the same result as the original function.
    
    These tests verify that the fix does NOT break existing behavior for
    users who have never received DM notifications before.
    """
    
    @pytest.mark.asyncio
    async def test_preservation_first_time_user_gets_all_articles_in_time_window(
        self,
        test_supabase_client,
        test_user,
        test_feed
    ):
        """
        Preservation Test: First-time users get all articles in time window
        
        Observed Behavior on UNFIXED code:
        - New users (no sent articles) get all articles published in last 7 days
        - No filtering by sent status (because no articles have been sent yet)
        
        This behavior MUST be preserved after the fix.
        
        **Validates: Requirements 3.1, 3.2**
        """
        # Setup: Create subscription
        test_supabase_client.table('user_subscriptions').insert({
            'user_id': test_user['id'],
            'feed_id': test_feed['id']
        }).execute()
        
        # Setup: Create 5 articles in the last 7 days
        now = datetime.now(timezone.utc)
        articles_created = []
        for i in range(5):
            article_url = f"https://test-preservation-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'Preservation Test Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=i)).isoformat(),
                'tinkering_index': 5 - (i % 5)  # Valid range 1-5, descending order
            }).execute()
            articles_created.append(result.data[0])
        
        try:
            # Query articles for first-time user (no sent articles)
            supabase_service = SupabaseService()
            articles = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            # Preservation Property: First-time user gets ALL articles in time window
            assert len(articles) == 5, (
                f"Preservation violation: First-time user should get all 5 articles "
                f"in time window, but got {len(articles)} articles"
            )
            
            # Verify all created articles are returned
            # Normalize URLs by removing trailing slashes for comparison
            returned_urls = {str(article.url).rstrip('/') for article in articles}
            expected_urls = {article['url'].rstrip('/') for article in articles_created}
            
            assert returned_urls == expected_urls, (
                f"Preservation violation: Returned articles don't match created articles. "
                f"Expected: {expected_urls}, Got: {returned_urls}"
            )
            
        finally:
            # Cleanup
            for article in articles_created:
                try:
                    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                except Exception:
                    pass
    
    @pytest.mark.asyncio
    async def test_preservation_subscription_filtering_preserved(
        self,
        test_supabase_client,
        test_user
    ):
        """
        Preservation Test: Only subscribed feeds are included
        
        Observed Behavior on UNFIXED code:
        - Only articles from subscribed feeds are returned
        - Articles from non-subscribed feeds are excluded
        
        This behavior MUST be preserved after the fix.
        
        **Validates: Requirement 3.1**
        """
        # Setup: Create two feeds
        feed1_url = f"https://test-feed-1-{datetime.now(timezone.utc).timestamp()}.com/rss.xml"
        feed1 = test_supabase_client.table('feeds').insert({
            'name': 'Subscribed Feed',
            'url': feed1_url,
            'category': 'Tech',
            'is_active': False
        }).execute().data[0]
        
        feed2_url = f"https://test-feed-2-{datetime.now(timezone.utc).timestamp()}.com/rss.xml"
        feed2 = test_supabase_client.table('feeds').insert({
            'name': 'Non-Subscribed Feed',
            'url': feed2_url,
            'category': 'Tech',
            'is_active': False
        }).execute().data[0]
        
        # Setup: Subscribe to feed1 only
        test_supabase_client.table('user_subscriptions').insert({
            'user_id': test_user['id'],
            'feed_id': feed1['id']
        }).execute()
        
        # Setup: Create articles in both feeds
        now = datetime.now(timezone.utc)
        articles_created = []
        
        # 3 articles in subscribed feed
        for i in range(3):
            article_url = f"https://test-subscribed-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': feed1['id'],
                'title': f'Subscribed Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=i)).isoformat(),
                'tinkering_index': 3  # Valid range 1-5
            }).execute()
            articles_created.append(result.data[0])
        
        # 2 articles in non-subscribed feed
        for i in range(2):
            article_url = f"https://test-non-subscribed-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': feed2['id'],
                'title': f'Non-Subscribed Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=i)).isoformat(),
                'tinkering_index': 3  # Valid range 1-5
            }).execute()
            articles_created.append(result.data[0])
        
        try:
            # Query articles
            supabase_service = SupabaseService()
            articles = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            # Preservation Property: Only subscribed feed articles are returned
            assert len(articles) == 3, (
                f"Preservation violation: Should only get 3 articles from subscribed feed, "
                f"but got {len(articles)} articles"
            )
            
            # Verify all returned articles are from subscribed feed
            for article in articles:
                assert str(article.feed_id) == feed1['id'], (
                    f"Preservation violation: Article {article.url} is from non-subscribed feed"
                )
            
        finally:
            # Cleanup
            for article in articles_created:
                try:
                    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                except Exception:
                    pass
            try:
                test_supabase_client.table('feeds').delete().eq('id', feed1['id']).execute()
            except Exception:
                pass
            try:
                test_supabase_client.table('feeds').delete().eq('id', feed2['id']).execute()
            except Exception:
                pass
    
    @pytest.mark.asyncio
    async def test_preservation_time_window_filtering_preserved(
        self,
        test_supabase_client,
        test_user,
        test_feed
    ):
        """
        Preservation Test: Time window filtering (last 7 days) is preserved
        
        Observed Behavior on UNFIXED code:
        - Only articles published in the last 7 days are returned
        - Older articles are excluded
        
        This behavior MUST be preserved after the fix.
        
        **Validates: Requirement 3.2**
        """
        # Setup: Create subscription
        test_supabase_client.table('user_subscriptions').insert({
            'user_id': test_user['id'],
            'feed_id': test_feed['id']
        }).execute()
        
        # Setup: Create articles at different time points
        now = datetime.now(timezone.utc)
        articles_created = []
        
        # 3 articles within last 7 days (should be included)
        for i in range(3):
            article_url = f"https://test-recent-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'Recent Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=i)).isoformat(),
                'tinkering_index': 3  # Valid range 1-5
            }).execute()
            articles_created.append(result.data[0])
        
        # 2 articles older than 7 days (should be excluded)
        for i in range(2):
            article_url = f"https://test-old-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'Old Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=8 + i)).isoformat(),
                'tinkering_index': 3  # Valid range 1-5
            }).execute()
            articles_created.append(result.data[0])
        
        try:
            # Query articles with 7-day window
            supabase_service = SupabaseService()
            articles = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            # Preservation Property: Only articles within 7-day window are returned
            assert len(articles) == 3, (
                f"Preservation violation: Should only get 3 articles within 7-day window, "
                f"but got {len(articles)} articles"
            )
            
            # Verify all returned articles are within time window
            cutoff_date = now - timedelta(days=7)
            for article in articles:
                assert article.published_at >= cutoff_date, (
                    f"Preservation violation: Article {article.url} published at "
                    f"{article.published_at} is older than 7 days (cutoff: {cutoff_date})"
                )
            
        finally:
            # Cleanup
            for article in articles_created:
                try:
                    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                except Exception:
                    pass
    
    @pytest.mark.asyncio
    async def test_preservation_limit_20_articles_preserved(
        self,
        test_supabase_client,
        test_user,
        test_feed
    ):
        """
        Preservation Test: Limit (20 articles max) is preserved
        
        Observed Behavior on UNFIXED code:
        - Maximum 20 articles are returned
        - Even if more articles exist, only 20 are returned
        
        This behavior MUST be preserved after the fix.
        
        **Validates: Requirement 3.3**
        """
        # Setup: Create subscription
        test_supabase_client.table('user_subscriptions').insert({
            'user_id': test_user['id'],
            'feed_id': test_feed['id']
        }).execute()
        
        # Setup: Create 25 articles (more than limit)
        now = datetime.now(timezone.utc)
        articles_created = []
        for i in range(25):
            article_url = f"https://test-limit-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'Limit Test Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(hours=i)).isoformat(),
                'tinkering_index': 5 - (i % 5)  # Valid range 1-5, cycling pattern
            }).execute()
            articles_created.append(result.data[0])
        
        try:
            # Query articles with limit=20
            supabase_service = SupabaseService()
            articles = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            # Preservation Property: Maximum 20 articles are returned
            assert len(articles) == 20, (
                f"Preservation violation: Should get maximum 20 articles, "
                f"but got {len(articles)} articles"
            )
            
        finally:
            # Cleanup
            for article in articles_created:
                try:
                    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                except Exception:
                    pass
    
    @pytest.mark.asyncio
    async def test_preservation_ordering_by_tinkering_index_desc_preserved(
        self,
        test_supabase_client,
        test_user,
        test_feed
    ):
        """
        Preservation Test: Ordering (tinkering_index DESC) is preserved
        
        Observed Behavior on UNFIXED code:
        - Articles are ordered by tinkering_index in descending order
        - Highest tinkering_index appears first
        
        This behavior MUST be preserved after the fix.
        
        **Validates: Requirement 3.3**
        """
        # Setup: Create subscription
        test_supabase_client.table('user_subscriptions').insert({
            'user_id': test_user['id'],
            'feed_id': test_feed['id']
        }).execute()
        
        # Setup: Create articles with specific tinkering_index values
        now = datetime.now(timezone.utc)
        articles_created = []
        tinkering_indices = [3, 5, 1, 4, 2]  # Intentionally unordered, all valid (1-5)
        
        for i, tinkering_index in enumerate(tinkering_indices):
            article_url = f"https://test-order-{i}-{now.timestamp()}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'Order Test Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(hours=i)).isoformat(),
                'tinkering_index': tinkering_index
            }).execute()
            articles_created.append(result.data[0])
        
        try:
            # Query articles
            supabase_service = SupabaseService()
            articles = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            # Preservation Property: Articles are ordered by tinkering_index DESC
            assert len(articles) == 5, f"Should get 5 articles, got {len(articles)}"
            
            # Verify descending order
            tinkering_values = [article.tinkering_index for article in articles]
            expected_order = sorted(tinkering_indices, reverse=True)  # [5, 4, 3, 2, 1]
            
            assert tinkering_values == expected_order, (
                f"Preservation violation: Articles not ordered by tinkering_index DESC. "
                f"Expected: {expected_order}, Got: {tinkering_values}"
            )
            
        finally:
            # Cleanup
            for article in articles_created:
                try:
                    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                except Exception:
                    pass
    
    @pytest.mark.asyncio
    @given(
        article_count=st.integers(min_value=1, max_value=15),
        days_back=st.integers(min_value=0, max_value=6)
    )
    @settings(
        max_examples=5,
        deadline=None,  # Disable deadline for database operations
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    async def test_preservation_property_first_time_user_behavior(
        self,
        test_supabase_client,
        test_user,
        test_feed,
        article_count,
        days_back
    ):
        """
        Property-Based Preservation Test: First-time user behavior across scenarios
        
        **Property 2: Preservation** - For any first-time user (no sent articles),
        the system SHALL return all articles in the time window from subscribed feeds.
        
        This property-based test generates many scenarios to verify preservation
        across different combinations of article counts and time windows.
        
        **Validates: Requirements 3.1, 3.2, 3.3**
        """
        # Setup: Create subscription
        test_supabase_client.table('user_subscriptions').upsert({
            'user_id': test_user['id'],
            'feed_id': test_feed['id']
        }, on_conflict='user_id,feed_id').execute()
        
        # Setup: Create articles
        now = datetime.now(timezone.utc)
        articles_created = []
        
        for i in range(article_count):
            article_url = f"https://test-pbt-{i}-{now.timestamp()}-{article_count}-{days_back}.com"
            result = test_supabase_client.table('articles').insert({
                'feed_id': test_feed['id'],
                'title': f'PBT Article {i}',
                'url': article_url,
                'published_at': (now - timedelta(days=days_back)).isoformat(),
                'tinkering_index': 1 + (i % 5)  # Valid range 1-5, cycling pattern
            }).execute()
            articles_created.append(result.data[0])
        
        try:
            # Query articles for first-time user
            supabase_service = SupabaseService()
            articles = await supabase_service.get_user_articles(
                discord_id=test_user['discord_id'],
                days=7,
                limit=20
            )
            
            # Preservation Property: First-time user gets all articles in time window
            # (up to limit of 20)
            expected_count = min(article_count, 20)
            
            # Filter to only count articles we created (not from other tests)
            # Normalize URLs by removing trailing slashes for comparison
            created_urls = {article['url'].rstrip('/') for article in articles_created}
            returned_urls = {str(article.url).rstrip('/') for article in articles}
            our_articles = created_urls.intersection(returned_urls)
            
            assert len(our_articles) == expected_count, (
                f"Preservation violation: First-time user should get {expected_count} articles, "
                f"but got {len(our_articles)} articles. "
                f"article_count={article_count}, days_back={days_back}"
            )
            
        finally:
            # Cleanup
            for article in articles_created:
                try:
                    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
                except Exception:
                    pass
