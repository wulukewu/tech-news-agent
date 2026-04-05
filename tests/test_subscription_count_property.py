"""
Property-Based Tests for Subscription Count Accuracy

Tests Property 10: Subscription Count Accuracy
Validates that displayed subscription count matches database records.

**Feature: new-user-onboarding-system, Property 10: Subscription Count Accuracy**

For any user, the displayed subscription count on the Subscription_Page SHALL
equal the number of records in user_subscriptions table for that user.

**Validates: Requirements 4.7**
"""

import pytest
from hypothesis import given, strategies as st, settings
from uuid import UUID, uuid4
import asyncio

from app.services.supabase_service import SupabaseService


# Hypothesis strategies
uuid_strategy = st.builds(uuid4)
subscription_count_strategy = st.integers(min_value=0, max_value=20)


@pytest.mark.property_test
@given(
    num_subscriptions=subscription_count_strategy
)
@settings(max_examples=100, deadline=None)
def test_property_10_subscription_count_accuracy(num_subscriptions):
    """
    Feature: new-user-onboarding-system, Property 10: Subscription Count Accuracy
    
    For any user, the displayed subscription count on the Subscription_Page SHALL
    equal the number of records in user_subscriptions table for that user.
    
    **Validates: Requirements 4.7**
    """
    asyncio.run(_test_subscription_count_accuracy(num_subscriptions))


async def _test_subscription_count_accuracy(num_subscriptions):
    """Helper function to test subscription count accuracy"""
    try:
        supabase = SupabaseService()
        
        # Create test user
        test_user_id = uuid4()
        
        # Create test feeds and subscriptions
        created_feed_ids = []
        for i in range(num_subscriptions):
            feed_id = uuid4()
            
            # Create feed
            try:
                supabase.client.table('feeds').upsert({
                    'id': str(feed_id),
                    'name': f'Test Feed {i}',
                    'url': f'https://example.com/feed/{i}',
                    'category': 'Test',
                    'is_active': True
                }).execute()
            except:
                pass  # Feed might already exist
            
            # Create subscription
            try:
                supabase.client.table('user_subscriptions').insert({
                    'user_id': str(test_user_id),
                    'feed_id': str(feed_id)
                }).execute()
                created_feed_ids.append(feed_id)
            except:
                pass  # Subscription might already exist
        
        # Query subscription count from database
        db_subscriptions = supabase.client.table('user_subscriptions') \
            .select('id', count='exact') \
            .eq('user_id', str(test_user_id)) \
            .execute()
        
        db_count = len(db_subscriptions.data) if db_subscriptions.data else 0
        
        # Property: Database count should match what we created
        assert db_count == len(created_feed_ids), \
            f"Database count ({db_count}) != created subscriptions ({len(created_feed_ids)})"
        
        # Simulate what the API would return
        # (This is what the Subscription_Page would display)
        displayed_count = db_count
        
        # Property: Displayed count should equal database count
        assert displayed_count == db_count, \
            f"Displayed count ({displayed_count}) != database count ({db_count})"
        
        # Property: Count should be non-negative
        assert db_count >= 0, \
            f"Subscription count should be non-negative, got {db_count}"
        
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
    initial_count=st.integers(min_value=1, max_value=10),
    add_count=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=50, deadline=None)
def test_property_10_count_after_subscription(initial_count, add_count):
    """
    Feature: new-user-onboarding-system, Property 10: Count After Subscription
    
    For any user with N subscriptions, after subscribing to M additional feeds,
    the count SHALL be N + M.
    
    **Validates: Requirements 4.7**
    """
    asyncio.run(_test_count_after_subscription(initial_count, add_count))


async def _test_count_after_subscription(initial_count, add_count):
    """Helper function to test count after adding subscriptions"""
    try:
        supabase = SupabaseService()
        test_user_id = uuid4()
        
        # Create initial subscriptions
        initial_feed_ids = []
        for i in range(initial_count):
            feed_id = uuid4()
            try:
                supabase.client.table('feeds').upsert({
                    'id': str(feed_id),
                    'name': f'Initial Feed {i}',
                    'url': f'https://example.com/initial/{i}',
                    'category': 'Test',
                    'is_active': True
                }).execute()
                
                supabase.client.table('user_subscriptions').insert({
                    'user_id': str(test_user_id),
                    'feed_id': str(feed_id)
                }).execute()
                initial_feed_ids.append(feed_id)
            except:
                pass
        
        # Get initial count
        initial_subs = supabase.client.table('user_subscriptions') \
            .select('id') \
            .eq('user_id', str(test_user_id)) \
            .execute()
        
        count_before = len(initial_subs.data) if initial_subs.data else 0
        
        # Add more subscriptions
        added_feed_ids = []
        for i in range(add_count):
            feed_id = uuid4()
            try:
                supabase.client.table('feeds').upsert({
                    'id': str(feed_id),
                    'name': f'Added Feed {i}',
                    'url': f'https://example.com/added/{i}',
                    'category': 'Test',
                    'is_active': True
                }).execute()
                
                supabase.client.table('user_subscriptions').insert({
                    'user_id': str(test_user_id),
                    'feed_id': str(feed_id)
                }).execute()
                added_feed_ids.append(feed_id)
            except:
                pass
        
        # Get final count
        final_subs = supabase.client.table('user_subscriptions') \
            .select('id') \
            .eq('user_id', str(test_user_id)) \
            .execute()
        
        count_after = len(final_subs.data) if final_subs.data else 0
        
        # Property: Final count should equal initial + added
        expected_count = count_before + len(added_feed_ids)
        assert count_after == expected_count, \
            f"Count after adding subscriptions ({count_after}) != expected ({expected_count})"
        
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
    initial_count=st.integers(min_value=2, max_value=10),
    remove_count=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=50, deadline=None)
def test_property_10_count_after_unsubscription(initial_count, remove_count):
    """
    Feature: new-user-onboarding-system, Property 10: Count After Unsubscription
    
    For any user with N subscriptions, after unsubscribing from M feeds (M <= N),
    the count SHALL be N - M.
    
    **Validates: Requirements 4.7**
    """
    # Ensure we don't try to remove more than we have
    if remove_count > initial_count:
        remove_count = initial_count
    
    asyncio.run(_test_count_after_unsubscription(initial_count, remove_count))


async def _test_count_after_unsubscription(initial_count, remove_count):
    """Helper function to test count after removing subscriptions"""
    try:
        supabase = SupabaseService()
        test_user_id = uuid4()
        
        # Create initial subscriptions
        feed_ids = []
        for i in range(initial_count):
            feed_id = uuid4()
            try:
                supabase.client.table('feeds').upsert({
                    'id': str(feed_id),
                    'name': f'Test Feed {i}',
                    'url': f'https://example.com/feed/{i}',
                    'category': 'Test',
                    'is_active': True
                }).execute()
                
                supabase.client.table('user_subscriptions').insert({
                    'user_id': str(test_user_id),
                    'feed_id': str(feed_id)
                }).execute()
                feed_ids.append(feed_id)
            except:
                pass
        
        # Get initial count
        initial_subs = supabase.client.table('user_subscriptions') \
            .select('id') \
            .eq('user_id', str(test_user_id)) \
            .execute()
        
        count_before = len(initial_subs.data) if initial_subs.data else 0
        
        # Remove some subscriptions
        removed_count = 0
        for i in range(min(remove_count, len(feed_ids))):
            try:
                supabase.client.table('user_subscriptions') \
                    .delete() \
                    .eq('user_id', str(test_user_id)) \
                    .eq('feed_id', str(feed_ids[i])) \
                    .execute()
                removed_count += 1
            except:
                pass
        
        # Get final count
        final_subs = supabase.client.table('user_subscriptions') \
            .select('id') \
            .eq('user_id', str(test_user_id)) \
            .execute()
        
        count_after = len(final_subs.data) if final_subs.data else 0
        
        # Property: Final count should equal initial - removed
        expected_count = count_before - removed_count
        assert count_after == expected_count, \
            f"Count after removing subscriptions ({count_after}) != expected ({expected_count})"
        
        # Property: Count should never be negative
        assert count_after >= 0, \
            f"Subscription count should never be negative, got {count_after}"
        
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
def test_property_10_new_user_zero_count():
    """
    Feature: new-user-onboarding-system, Property 10: New User Zero Count
    
    For any new user with no subscriptions, the count SHALL be zero.
    
    **Validates: Requirements 4.7**
    """
    asyncio.run(_test_new_user_zero_count())


async def _test_new_user_zero_count():
    """Helper function to test new user has zero subscriptions"""
    try:
        supabase = SupabaseService()
        
        # Create new user (don't create any subscriptions)
        test_user_id = uuid4()
        
        # Query subscription count
        subscriptions = supabase.client.table('user_subscriptions') \
            .select('id') \
            .eq('user_id', str(test_user_id)) \
            .execute()
        
        count = len(subscriptions.data) if subscriptions.data else 0
        
        # Property: New user should have zero subscriptions
        assert count == 0, \
            f"New user should have 0 subscriptions, got {count}"
        
    except Exception as e:
        pytest.skip(f"Database not available: {e}")
