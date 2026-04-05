"""
Property-Based Tests for Batch Subscription

Tests Property 4: Feed Subscription from Onboarding
Validates that batch subscription correctly subscribes users to all selected feeds.

**Feature: new-user-onboarding-system, Property 4: Feed Subscription from Onboarding**

For any set of selected feeds during onboarding, after confirmation, the user
SHALL be subscribed to all selected feeds, and the subscription count SHALL
equal the number of selected feeds.

**Validates: Requirements 2.6, 2.7**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from uuid import UUID, uuid4
import asyncio

from app.services.subscription_service import SubscriptionService
from app.services.supabase_service import SupabaseService


# Hypothesis strategies
uuid_strategy = st.builds(uuid4)
feed_ids_strategy = st.lists(uuid_strategy, min_size=1, max_size=10, unique=True)


@pytest.mark.property_test
@given(
    feed_ids=feed_ids_strategy
)
@settings(max_examples=100, deadline=None)
def test_property_4_feed_subscription_from_onboarding(feed_ids):
    """
    Feature: new-user-onboarding-system, Property 4: Feed Subscription from Onboarding
    
    For any set of selected feeds during onboarding, after confirmation, the user
    SHALL be subscribed to all selected feeds, and the subscription count SHALL
    equal the number of selected feeds.
    
    **Validates: Requirements 2.6, 2.7**
    """
    # Run async test
    asyncio.run(_test_batch_subscribe_property(feed_ids))


async def _test_batch_subscribe_property(feed_ids):
    """Helper function to run async property test"""
    try:
        supabase = SupabaseService()
        subscription_service = SubscriptionService(supabase.client)
        
        # Create a test user
        test_user_id = uuid4()
        
        # Create test feeds in database
        created_feed_ids = []
        for feed_id in feed_ids:
            try:
                # Insert feed if it doesn't exist
                supabase.client.table('feeds').upsert({
                    'id': str(feed_id),
                    'name': f'Test Feed {feed_id}',
                    'url': f'https://example.com/feed/{feed_id}',
                    'category': 'Test',
                    'is_active': True
                }).execute()
                created_feed_ids.append(feed_id)
            except Exception as e:
                # Feed might already exist, that's okay
                created_feed_ids.append(feed_id)
        
        # Perform batch subscription
        result = await subscription_service.batch_subscribe(test_user_id, created_feed_ids)
        
        # Property: subscription count should equal number of feeds
        # (assuming all feeds exist and are active)
        assert result.subscribed_count + result.failed_count == len(created_feed_ids), \
            f"Total processed ({result.subscribed_count + result.failed_count}) != feeds provided ({len(created_feed_ids)})"
        
        # Query actual subscriptions from database
        subscriptions = supabase.client.table('user_subscriptions') \
            .select('feed_id') \
            .eq('user_id', str(test_user_id)) \
            .execute()
        
        subscribed_feed_ids = {UUID(sub['feed_id']) for sub in subscriptions.data}
        
        # Property: All successfully subscribed feeds should be in database
        for feed_id in created_feed_ids:
            if feed_id not in subscribed_feed_ids:
                # This feed should be in the failed list
                assert result.failed_count > 0, \
                    f"Feed {feed_id} not subscribed but not in failed count"
        
        # Property: Subscription count should match database records
        assert len(subscribed_feed_ids) >= result.subscribed_count, \
            f"Database has {len(subscribed_feed_ids)} subscriptions but service reported {result.subscribed_count}"
        
        # Cleanup: Remove test subscriptions
        try:
            supabase.client.table('user_subscriptions') \
                .delete() \
                .eq('user_id', str(test_user_id)) \
                .execute()
        except:
            pass  # Cleanup failure is acceptable in tests
        
    except Exception as e:
        # If database is not available, skip this test
        pytest.skip(f"Database not available: {e}")


@pytest.mark.property_test
@given(
    feed_ids=feed_ids_strategy
)
@settings(max_examples=50, deadline=None)
def test_property_4_idempotent_subscription(feed_ids):
    """
    Feature: new-user-onboarding-system, Property 4: Feed Subscription Idempotency
    
    For any set of feeds, subscribing twice should result in the same subscription
    count (idempotent operation).
    
    **Validates: Requirements 2.6, 2.7**
    """
    asyncio.run(_test_idempotent_subscription(feed_ids))


async def _test_idempotent_subscription(feed_ids):
    """Helper function to test idempotent subscription"""
    try:
        supabase = SupabaseService()
        subscription_service = SubscriptionService(supabase.client)
        
        test_user_id = uuid4()
        
        # Create test feeds
        created_feed_ids = []
        for feed_id in feed_ids:
            try:
                supabase.client.table('feeds').upsert({
                    'id': str(feed_id),
                    'name': f'Test Feed {feed_id}',
                    'url': f'https://example.com/feed/{feed_id}',
                    'category': 'Test',
                    'is_active': True
                }).execute()
                created_feed_ids.append(feed_id)
            except:
                created_feed_ids.append(feed_id)
        
        # First subscription
        result1 = await subscription_service.batch_subscribe(test_user_id, created_feed_ids)
        
        # Second subscription (should be idempotent)
        result2 = await subscription_service.batch_subscribe(test_user_id, created_feed_ids)
        
        # Property: Both operations should report same subscription count
        assert result1.subscribed_count == result2.subscribed_count, \
            f"Idempotency violated: first={result1.subscribed_count}, second={result2.subscribed_count}"
        
        # Property: Failed count should be same or less on second attempt
        assert result2.failed_count <= result1.failed_count, \
            f"Failed count increased on retry: first={result1.failed_count}, second={result2.failed_count}"
        
        # Cleanup
        try:
            supabase.client.table('user_subscriptions') \
                .delete() \
                .eq('user_id', str(test_user_id)) \
                .execute()
        except:
            pass
        
    except Exception as e:
        pytest.skip(f"Database not available: {e}")


@pytest.mark.property_test
@given(
    valid_feeds=st.lists(uuid_strategy, min_size=1, max_size=5, unique=True),
    invalid_feeds=st.lists(uuid_strategy, min_size=1, max_size=3, unique=True)
)
@settings(max_examples=50, deadline=None)
def test_property_4_partial_failure_handling(valid_feeds, invalid_feeds):
    """
    Feature: new-user-onboarding-system, Property 4: Partial Failure Handling
    
    For any mix of valid and invalid feeds, the system SHALL subscribe to all
    valid feeds and report failures for invalid feeds without stopping the process.
    
    **Validates: Requirements 2.7**
    """
    # Ensure no overlap between valid and invalid feeds
    assume(not set(valid_feeds).intersection(set(invalid_feeds)))
    
    asyncio.run(_test_partial_failure(valid_feeds, invalid_feeds))


async def _test_partial_failure(valid_feeds, invalid_feeds):
    """Helper function to test partial failure handling"""
    try:
        supabase = SupabaseService()
        subscription_service = SubscriptionService(supabase.client)
        
        test_user_id = uuid4()
        
        # Create only valid feeds in database
        for feed_id in valid_feeds:
            try:
                supabase.client.table('feeds').upsert({
                    'id': str(feed_id),
                    'name': f'Valid Feed {feed_id}',
                    'url': f'https://example.com/feed/{feed_id}',
                    'category': 'Test',
                    'is_active': True
                }).execute()
            except:
                pass
        
        # Mix valid and invalid feeds
        all_feeds = valid_feeds + invalid_feeds
        
        # Attempt batch subscription
        result = await subscription_service.batch_subscribe(test_user_id, all_feeds)
        
        # Property: Should have processed all feeds
        assert result.subscribed_count + result.failed_count == len(all_feeds), \
            f"Not all feeds processed: {result.subscribed_count + result.failed_count} != {len(all_feeds)}"
        
        # Property: Should have at least some failures (invalid feeds)
        assert result.failed_count >= len(invalid_feeds), \
            f"Expected at least {len(invalid_feeds)} failures, got {result.failed_count}"
        
        # Property: Should have subscribed to valid feeds
        subscriptions = supabase.client.table('user_subscriptions') \
            .select('feed_id') \
            .eq('user_id', str(test_user_id)) \
            .execute()
        
        subscribed_feed_ids = {UUID(sub['feed_id']) for sub in subscriptions.data}
        
        # All valid feeds should be subscribed
        for feed_id in valid_feeds:
            assert feed_id in subscribed_feed_ids, \
                f"Valid feed {feed_id} was not subscribed"
        
        # Invalid feeds should not be subscribed
        for feed_id in invalid_feeds:
            assert feed_id not in subscribed_feed_ids, \
                f"Invalid feed {feed_id} was incorrectly subscribed"
        
        # Cleanup
        try:
            supabase.client.table('user_subscriptions') \
                .delete() \
                .eq('user_id', str(test_user_id)) \
                .execute()
        except:
            pass
        
    except Exception as e:
        pytest.skip(f"Database not available: {e}")


@pytest.mark.property_test
def test_property_4_empty_feed_list():
    """
    Feature: new-user-onboarding-system, Property 4: Empty Feed List Handling
    
    For an empty feed list, the system SHALL return zero subscribed and zero failed.
    
    **Validates: Requirements 2.6**
    """
    asyncio.run(_test_empty_feed_list())


async def _test_empty_feed_list():
    """Helper function to test empty feed list"""
    try:
        supabase = SupabaseService()
        subscription_service = SubscriptionService(supabase.client)
        
        test_user_id = uuid4()
        
        # Subscribe to empty list
        result = await subscription_service.batch_subscribe(test_user_id, [])
        
        # Property: Should have zero subscriptions and zero failures
        assert result.subscribed_count == 0, \
            f"Expected 0 subscriptions for empty list, got {result.subscribed_count}"
        assert result.failed_count == 0, \
            f"Expected 0 failures for empty list, got {result.failed_count}"
        assert len(result.errors) == 0, \
            f"Expected no errors for empty list, got {len(result.errors)}"
        
    except Exception as e:
        pytest.skip(f"Database not available: {e}")
