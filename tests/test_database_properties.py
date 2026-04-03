"""
Property-Based Tests for Supabase Migration Phase 1
Tasks 6.1-6.17: Database Schema Correctness Properties

This module contains 17 property-based tests that verify the correctness
of the database schema, constraints, and behaviors using Hypothesis.

Each test validates specific requirements from the design document and
runs with a minimum of 100 iterations to ensure robustness.
"""
import os
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from supabase import Client
from datetime import datetime
import time


# Custom strategy for generating valid text (no null bytes, printable characters)
def valid_text(min_size=1, max_size=100):
    """Generate valid text without null bytes or control characters."""
    return st.text(
        alphabet=st.characters(blacklist_categories=('Cc', 'Cs'), blacklist_characters='\x00'),
        min_size=min_size,
        max_size=max_size
    ).filter(lambda x: x.strip())


# ============================================================================
# Property 1: User Deletion Cascades (Task 6.1)
# ============================================================================

@given(
    discord_id=valid_text(min_size=1, max_size=100),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_1_user_deletion_cascades(test_supabase_client: Client, test_feed, discord_id):
    """
    **Validates: Requirements 3.9**
    
    Property 1: User Deletion Cascades
    
    For any user record with related subscriptions and reading list entries,
    when the user is deleted, all related records in user_subscriptions and
    reading_list tables should be automatically deleted.
    """
    # Create unique discord_id to avoid conflicts
    unique_discord_id = f"{discord_id}_{os.urandom(4).hex()}"
    
    # Create user
    user_result = test_supabase_client.table('users').insert({
        'discord_id': unique_discord_id
    }).execute()
    user = user_result.data[0]
    user_id = user['id']
    
    # Create subscription
    subscription_result = test_supabase_client.table('user_subscriptions').insert({
        'user_id': user_id,
        'feed_id': test_feed['id']
    }).execute()
    subscription_id = subscription_result.data[0]['id']
    
    # Create article for reading list
    article_url = f"https://test-article-{os.urandom(8).hex()}.com"
    article_result = test_supabase_client.table('articles').insert({
        'feed_id': test_feed['id'],
        'title': 'Test Article',
        'url': article_url
    }).execute()
    article_id = article_result.data[0]['id']
    
    # Create reading list entry
    reading_list_result = test_supabase_client.table('reading_list').insert({
        'user_id': user_id,
        'article_id': article_id,
        'status': 'Unread'
    }).execute()
    reading_list_id = reading_list_result.data[0]['id']
    
    # Delete user
    test_supabase_client.table('users').delete().eq('id', user_id).execute()
    
    # Verify subscription was cascade deleted
    subscription_check = test_supabase_client.table('user_subscriptions')\
        .select('*').eq('id', subscription_id).execute()
    assert len(subscription_check.data) == 0, "Subscription should be cascade deleted"
    
    # Verify reading list entry was cascade deleted
    reading_list_check = test_supabase_client.table('reading_list')\
        .select('*').eq('id', reading_list_id).execute()
    assert len(reading_list_check.data) == 0, "Reading list entry should be cascade deleted"
    
    # Cleanup article
    test_supabase_client.table('articles').delete().eq('id', article_id).execute()


# ============================================================================
# Property 2: Feed Deletion Cascades (Task 6.2)
# ============================================================================

@given(
    feed_name=valid_text(min_size=1, max_size=100),
    category=valid_text(min_size=1, max_size=50),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_2_feed_deletion_cascades(test_supabase_client: Client, feed_name, category):
    """
    **Validates: Requirements 3.10**
    
    Property 2: Feed Deletion Cascades
    
    For any feed record with related articles, when the feed is deleted,
    all related records in the articles table should be automatically deleted.
    """
    # Create unique feed URL
    feed_url = f"https://test-feed-{os.urandom(8).hex()}.com/rss.xml"
    
    # Create feed
    feed_result = test_supabase_client.table('feeds').insert({
        'name': feed_name,
        'url': feed_url,
        'category': category,
        'is_active': True
    }).execute()
    feed = feed_result.data[0]
    feed_id = feed['id']
    
    # Create articles
    article_url_1 = f"https://test-article-{os.urandom(8).hex()}.com"
    article_url_2 = f"https://test-article-{os.urandom(8).hex()}.com"
    
    article_1_result = test_supabase_client.table('articles').insert({
        'feed_id': feed_id,
        'title': 'Test Article 1',
        'url': article_url_1
    }).execute()
    article_1_id = article_1_result.data[0]['id']
    
    article_2_result = test_supabase_client.table('articles').insert({
        'feed_id': feed_id,
        'title': 'Test Article 2',
        'url': article_url_2
    }).execute()
    article_2_id = article_2_result.data[0]['id']
    
    # Delete feed
    test_supabase_client.table('feeds').delete().eq('id', feed_id).execute()
    
    # Verify articles were cascade deleted
    article_1_check = test_supabase_client.table('articles')\
        .select('*').eq('id', article_1_id).execute()
    assert len(article_1_check.data) == 0, "Article 1 should be cascade deleted"
    
    article_2_check = test_supabase_client.table('articles')\
        .select('*').eq('id', article_2_id).execute()
    assert len(article_2_check.data) == 0, "Article 2 should be cascade deleted"


# ============================================================================
# Property 3: Article Deletion Cascades (Task 6.3)
# ============================================================================

@given(
    article_title=valid_text(min_size=1, max_size=200),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_3_article_deletion_cascades(test_supabase_client: Client, test_user, test_feed, article_title):
    """
    **Validates: Requirements 3.11**
    
    Property 3: Article Deletion Cascades
    
    For any article record with related reading list entries, when the article
    is deleted, all related records in the reading_list table should be
    automatically deleted.
    """
    # Create unique article URL
    article_url = f"https://test-article-{os.urandom(8).hex()}.com"
    
    # Create article
    article_result = test_supabase_client.table('articles').insert({
        'feed_id': test_feed['id'],
        'title': article_title,
        'url': article_url
    }).execute()
    article = article_result.data[0]
    article_id = article['id']
    
    # Create reading list entry
    reading_list_result = test_supabase_client.table('reading_list').insert({
        'user_id': test_user['id'],
        'article_id': article_id,
        'status': 'Unread'
    }).execute()
    reading_list_id = reading_list_result.data[0]['id']
    
    # Delete article
    test_supabase_client.table('articles').delete().eq('id', article_id).execute()
    
    # Verify reading list entry was cascade deleted
    reading_list_check = test_supabase_client.table('reading_list')\
        .select('*').eq('id', reading_list_id).execute()
    assert len(reading_list_check.data) == 0, "Reading list entry should be cascade deleted"


# ============================================================================
# Property 4: Discord ID Uniqueness (Task 6.4)
# ============================================================================

@given(
    discord_id=valid_text(min_size=1, max_size=100),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_4_discord_id_uniqueness(test_supabase_client: Client, discord_id):
    """
    **Validates: Requirements 6.1**
    
    Property 4: Discord ID Uniqueness
    
    For any two user records with the same discord_id value, the database
    should reject the second insertion with a unique constraint violation.
    """
    # Create unique discord_id to avoid conflicts with other tests
    unique_discord_id = f"{discord_id}_{os.urandom(4).hex()}"
    
    # Insert first user - should succeed
    user_1_result = test_supabase_client.table('users').insert({
        'discord_id': unique_discord_id
    }).execute()
    user_1_id = user_1_result.data[0]['id']
    
    # Attempt to insert second user with same discord_id - should fail
    try:
        test_supabase_client.table('users').insert({
            'discord_id': unique_discord_id
        }).execute()
        pytest.fail("Second user insertion should have failed with unique constraint violation")
    except Exception as e:
        error_msg = str(e).lower()
        assert 'duplicate' in error_msg or 'unique' in error_msg or 'constraint' in error_msg, \
            f"Expected unique constraint error, got: {e}"
    
    # Cleanup
    test_supabase_client.table('users').delete().eq('id', user_1_id).execute()


# ============================================================================
# Property 5: Subscription Uniqueness (Task 6.5)
# ============================================================================

@given(
    dummy=st.just(None)  # No random data needed, using fixtures
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_5_subscription_uniqueness(test_supabase_client: Client, test_user, test_feed, dummy):
    """
    **Validates: Requirements 6.4**
    
    Property 5: Subscription Uniqueness
    
    For any user and feed combination, attempting to create duplicate
    subscriptions (same user_id and feed_id) should be rejected by the
    database with a unique constraint violation.
    """
    # Create first subscription - should succeed
    subscription_1_result = test_supabase_client.table('user_subscriptions').insert({
        'user_id': test_user['id'],
        'feed_id': test_feed['id']
    }).execute()
    subscription_1_id = subscription_1_result.data[0]['id']
    
    # Attempt to create duplicate subscription - should fail
    try:
        test_supabase_client.table('user_subscriptions').insert({
            'user_id': test_user['id'],
            'feed_id': test_feed['id']
        }).execute()
        pytest.fail("Duplicate subscription insertion should have failed")
    except Exception as e:
        error_msg = str(e).lower()
        assert 'duplicate' in error_msg or 'unique' in error_msg or 'constraint' in error_msg, \
            f"Expected unique constraint error, got: {e}"
    
    # Cleanup
    test_supabase_client.table('user_subscriptions').delete().eq('id', subscription_1_id).execute()


# ============================================================================
# Property 6: Reading List Entry Uniqueness (Task 6.6)
# ============================================================================

@given(
    dummy=st.just(None)  # No random data needed, using fixtures
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_6_reading_list_entry_uniqueness(test_supabase_client: Client, test_user, test_article, dummy):
    """
    **Validates: Requirements 6.5**
    
    Property 6: Reading List Entry Uniqueness
    
    For any user and article combination, attempting to create duplicate
    reading list entries (same user_id and article_id) should be rejected
    by the database with a unique constraint violation.
    """
    # Create first reading list entry - should succeed
    entry_1_result = test_supabase_client.table('reading_list').insert({
        'user_id': test_user['id'],
        'article_id': test_article['id'],
        'status': 'Unread'
    }).execute()
    entry_1_id = entry_1_result.data[0]['id']
    
    # Attempt to create duplicate entry - should fail
    try:
        test_supabase_client.table('reading_list').insert({
            'user_id': test_user['id'],
            'article_id': test_article['id'],
            'status': 'Read'
        }).execute()
        pytest.fail("Duplicate reading list entry insertion should have failed")
    except Exception as e:
        error_msg = str(e).lower()
        assert 'duplicate' in error_msg or 'unique' in error_msg or 'constraint' in error_msg, \
            f"Expected unique constraint error, got: {e}"
    
    # Cleanup
    test_supabase_client.table('reading_list').delete().eq('id', entry_1_id).execute()


# ============================================================================
# Property 7: Feed URL Uniqueness (Task 6.7)
# ============================================================================

@given(
    feed_name=valid_text(min_size=1, max_size=100),
    category=valid_text(min_size=1, max_size=50),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_7_feed_url_uniqueness(test_supabase_client: Client, feed_name, category):
    """
    **Validates: Requirements 7.3**
    
    Property 7: Feed URL Uniqueness
    
    For any two feed records with the same URL value, the database should
    reject the second insertion with a unique constraint violation.
    """
    # Create unique feed URL
    feed_url = f"https://test-feed-{os.urandom(8).hex()}.com/rss.xml"
    
    # Insert first feed - should succeed
    feed_1_result = test_supabase_client.table('feeds').insert({
        'name': feed_name,
        'url': feed_url,
        'category': category,
        'is_active': True
    }).execute()
    feed_1_id = feed_1_result.data[0]['id']
    
    # Attempt to insert second feed with same URL - should fail
    try:
        test_supabase_client.table('feeds').insert({
            'name': f"{feed_name} 2",
            'url': feed_url,
            'category': category,
            'is_active': True
        }).execute()
        pytest.fail("Second feed insertion with duplicate URL should have failed")
    except Exception as e:
        error_msg = str(e).lower()
        assert 'duplicate' in error_msg or 'unique' in error_msg or 'constraint' in error_msg, \
            f"Expected unique constraint error, got: {e}"
    
    # Cleanup
    test_supabase_client.table('feeds').delete().eq('id', feed_1_id).execute()


# ============================================================================
# Property 8: Article URL Uniqueness (Task 6.8)
# ============================================================================

@given(
    article_title=valid_text(min_size=1, max_size=200),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_8_article_url_uniqueness(test_supabase_client: Client, test_feed, article_title):
    """
    **Validates: Requirements 7.4**
    
    Property 8: Article URL Uniqueness
    
    For any two article records with the same URL value, the database should
    reject the second insertion with a unique constraint violation.
    """
    # Create unique article URL
    article_url = f"https://test-article-{os.urandom(8).hex()}.com"
    
    # Insert first article - should succeed
    article_1_result = test_supabase_client.table('articles').insert({
        'feed_id': test_feed['id'],
        'title': article_title,
        'url': article_url
    }).execute()
    article_1_id = article_1_result.data[0]['id']
    
    # Attempt to insert second article with same URL - should fail
    try:
        test_supabase_client.table('articles').insert({
            'feed_id': test_feed['id'],
            'title': f"{article_title} 2",
            'url': article_url
        }).execute()
        pytest.fail("Second article insertion with duplicate URL should have failed")
    except Exception as e:
        error_msg = str(e).lower()
        assert 'duplicate' in error_msg or 'unique' in error_msg or 'constraint' in error_msg, \
            f"Expected unique constraint error, got: {e}"
    
    # Cleanup
    test_supabase_client.table('articles').delete().eq('id', article_1_id).execute()



# ============================================================================
# Property 9: Shared Feed References (Task 6.9)
# ============================================================================

@given(
    num_users=st.integers(min_value=2, max_value=5),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_9_shared_feed_references(test_supabase_client: Client, test_feed, num_users):
    """
    **Validates: Requirements 7.5**
    
    Property 9: Shared Feed References
    
    For any feed that multiple users subscribe to, all subscription records
    should reference the same feed_id in the feeds table, ensuring no
    duplicate feed records exist.
    """
    user_ids = []
    subscription_ids = []
    
    # Create multiple users
    for i in range(num_users):
        discord_id = f"test_user_{os.urandom(8).hex()}"
        user_result = test_supabase_client.table('users').insert({
            'discord_id': discord_id
        }).execute()
        user_ids.append(user_result.data[0]['id'])
    
    # Subscribe all users to the same feed
    for user_id in user_ids:
        subscription_result = test_supabase_client.table('user_subscriptions').insert({
            'user_id': user_id,
            'feed_id': test_feed['id']
        }).execute()
        subscription_ids.append(subscription_result.data[0]['id'])
    
    # Verify all subscriptions reference the same feed_id
    for subscription_id in subscription_ids:
        subscription = test_supabase_client.table('user_subscriptions')\
            .select('feed_id').eq('id', subscription_id).execute()
        assert subscription.data[0]['feed_id'] == test_feed['id'], \
            "All subscriptions should reference the same feed_id"
    
    # Verify only one feed record exists with this URL
    feeds = test_supabase_client.table('feeds')\
        .select('*').eq('url', test_feed['url']).execute()
    assert len(feeds.data) == 1, "Only one feed record should exist for this URL"
    
    # Cleanup
    for subscription_id in subscription_ids:
        test_supabase_client.table('user_subscriptions').delete().eq('id', subscription_id).execute()
    for user_id in user_ids:
        test_supabase_client.table('users').delete().eq('id', user_id).execute()


# ============================================================================
# Property 10: Required Field Validation (Task 6.10)
# ============================================================================

@given(
    dummy=st.just(None)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_10_required_field_validation(test_supabase_client: Client, test_feed, dummy):
    """
    **Validates: Requirements 9.3, 9.4, 9.5, 9.6, 9.7, 9.8**
    
    Property 10: Required Field Validation
    
    For any insertion attempt where a NOT NULL field is provided as NULL,
    the database should reject the insertion with a NOT NULL constraint violation.
    """
    # Test users.discord_id NOT NULL
    try:
        test_supabase_client.table('users').insert({
            'discord_id': None
        }).execute()
        pytest.fail("User insertion with NULL discord_id should have failed")
    except Exception as e:
        error_msg = str(e).lower()
        assert 'null' in error_msg or 'not null' in error_msg or 'violates' in error_msg, \
            f"Expected NOT NULL constraint error, got: {e}"
    
    # Test feeds.name NOT NULL
    try:
        test_supabase_client.table('feeds').insert({
            'name': None,
            'url': f"https://test-{os.urandom(8).hex()}.com",
            'category': 'Test'
        }).execute()
        pytest.fail("Feed insertion with NULL name should have failed")
    except Exception as e:
        error_msg = str(e).lower()
        assert 'null' in error_msg or 'not null' in error_msg or 'violates' in error_msg, \
            f"Expected NOT NULL constraint error, got: {e}"
    
    # Test feeds.url NOT NULL
    try:
        test_supabase_client.table('feeds').insert({
            'name': 'Test Feed',
            'url': None,
            'category': 'Test'
        }).execute()
        pytest.fail("Feed insertion with NULL url should have failed")
    except Exception as e:
        error_msg = str(e).lower()
        assert 'null' in error_msg or 'not null' in error_msg or 'violates' in error_msg, \
            f"Expected NOT NULL constraint error, got: {e}"
    
    # Test feeds.category NOT NULL
    try:
        test_supabase_client.table('feeds').insert({
            'name': 'Test Feed',
            'url': f"https://test-{os.urandom(8).hex()}.com",
            'category': None
        }).execute()
        pytest.fail("Feed insertion with NULL category should have failed")
    except Exception as e:
        error_msg = str(e).lower()
        assert 'null' in error_msg or 'not null' in error_msg or 'violates' in error_msg, \
            f"Expected NOT NULL constraint error, got: {e}"
    
    # Test articles.title NOT NULL
    try:
        test_supabase_client.table('articles').insert({
            'feed_id': test_feed['id'],
            'title': None,
            'url': f"https://test-{os.urandom(8).hex()}.com"
        }).execute()
        pytest.fail("Article insertion with NULL title should have failed")
    except Exception as e:
        error_msg = str(e).lower()
        assert 'null' in error_msg or 'not null' in error_msg or 'violates' in error_msg, \
            f"Expected NOT NULL constraint error, got: {e}"
    
    # Test articles.url NOT NULL
    try:
        test_supabase_client.table('articles').insert({
            'feed_id': test_feed['id'],
            'title': 'Test Article',
            'url': None
        }).execute()
        pytest.fail("Article insertion with NULL url should have failed")
    except Exception as e:
        error_msg = str(e).lower()
        assert 'null' in error_msg or 'not null' in error_msg or 'violates' in error_msg, \
            f"Expected NOT NULL constraint error, got: {e}"


# ============================================================================
# Property 11: Timestamp Auto-Population (Task 6.11)
# ============================================================================

@given(
    discord_id=valid_text(min_size=1, max_size=100),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_11_timestamp_auto_population(test_supabase_client: Client, test_feed, discord_id):
    """
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.6, 8.7**
    
    Property 11: Timestamp Auto-Population
    
    For any record inserted without explicitly providing timestamp values,
    the database should automatically populate created_at (or subscribed_at/
    added_at/updated_at) with the current timestamp.
    """
    unique_discord_id = f"{discord_id}_{os.urandom(4).hex()}"
    
    # Test users.created_at auto-population
    user_result = test_supabase_client.table('users').insert({
        'discord_id': unique_discord_id
    }).execute()
    user = user_result.data[0]
    assert user['created_at'] is not None, "users.created_at should be auto-populated"
    
    # Test feeds.created_at auto-population
    feed_url = f"https://test-feed-{os.urandom(8).hex()}.com/rss.xml"
    feed_result = test_supabase_client.table('feeds').insert({
        'name': 'Test Feed',
        'url': feed_url,
        'category': 'Test'
    }).execute()
    feed = feed_result.data[0]
    assert feed['created_at'] is not None, "feeds.created_at should be auto-populated"
    
    # Test user_subscriptions.subscribed_at auto-population
    subscription_result = test_supabase_client.table('user_subscriptions').insert({
        'user_id': user['id'],
        'feed_id': test_feed['id']
    }).execute()
    subscription = subscription_result.data[0]
    assert subscription['subscribed_at'] is not None, "user_subscriptions.subscribed_at should be auto-populated"
    
    # Test articles.created_at auto-population
    article_url = f"https://test-article-{os.urandom(8).hex()}.com"
    article_result = test_supabase_client.table('articles').insert({
        'feed_id': test_feed['id'],
        'title': 'Test Article',
        'url': article_url
    }).execute()
    article = article_result.data[0]
    assert article['created_at'] is not None, "articles.created_at should be auto-populated"
    
    # Test reading_list.added_at and updated_at auto-population
    reading_list_result = test_supabase_client.table('reading_list').insert({
        'user_id': user['id'],
        'article_id': article['id'],
        'status': 'Unread'
    }).execute()
    reading_list = reading_list_result.data[0]
    assert reading_list['added_at'] is not None, "reading_list.added_at should be auto-populated"
    assert reading_list['updated_at'] is not None, "reading_list.updated_at should be auto-populated"
    
    # Cleanup
    test_supabase_client.table('reading_list').delete().eq('id', reading_list['id']).execute()
    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()
    test_supabase_client.table('user_subscriptions').delete().eq('id', subscription['id']).execute()
    test_supabase_client.table('feeds').delete().eq('id', feed['id']).execute()
    test_supabase_client.table('users').delete().eq('id', user['id']).execute()


# ============================================================================
# Property 12: Reading List Status Validation (Task 6.12)
# ============================================================================

@given(
    status=valid_text(min_size=1, max_size=50).filter(
        lambda s: s not in ['Unread', 'Read', 'Archived']
    )
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_12_reading_list_status_validation(test_supabase_client: Client, test_user, test_article, status):
    """
    **Validates: Requirements 9.1**
    
    Property 12: Reading List Status Validation
    
    For any reading list entry with a status value not in the set
    {'Unread', 'Read', 'Archived'}, the database should reject the
    insertion or update with a CHECK constraint violation.
    """
    # Attempt to insert reading list entry with invalid status
    try:
        test_supabase_client.table('reading_list').insert({
            'user_id': test_user['id'],
            'article_id': test_article['id'],
            'status': status
        }).execute()
        pytest.fail(f"Reading list insertion with invalid status '{status}' should have failed")
    except Exception as e:
        error_msg = str(e).lower()
        assert 'check' in error_msg or 'constraint' in error_msg or 'violat' in error_msg, \
            f"Expected CHECK constraint error, got: {e}"


# ============================================================================
# Property 13: Rating Range Validation (Task 6.13)
# ============================================================================

@given(
    rating=st.integers(min_value=-1000, max_value=1000).filter(lambda r: r < 1 or r > 5)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_13_rating_range_validation(test_supabase_client: Client, test_user, test_article, rating):
    """
    **Validates: Requirements 9.2**
    
    Property 13: Rating Range Validation
    
    For any reading list entry with a rating value outside the range [1, 5],
    the database should reject the insertion or update with a CHECK
    constraint violation.
    """
    # Attempt to insert reading list entry with invalid rating
    try:
        test_supabase_client.table('reading_list').insert({
            'user_id': test_user['id'],
            'article_id': test_article['id'],
            'status': 'Unread',
            'rating': rating
        }).execute()
        pytest.fail(f"Reading list insertion with invalid rating {rating} should have failed")
    except Exception as e:
        error_msg = str(e).lower()
        # Accept either CHECK constraint error or integer range error
        assert 'check' in error_msg or 'constraint' in error_msg or 'violat' in error_msg or 'out of range' in error_msg, \
            f"Expected CHECK constraint or range error, got: {e}"


# ============================================================================
# Property 14: Embedding NULL Tolerance (Task 6.14)
# ============================================================================

@given(
    article_title=valid_text(min_size=1, max_size=200),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_14_embedding_null_tolerance(test_supabase_client: Client, test_feed, article_title):
    """
    **Validates: Requirements 5.4**
    
    Property 14: Embedding NULL Tolerance
    
    For any article inserted without an embedding value (NULL), the insertion
    should succeed, allowing articles to exist before embeddings are generated.
    """
    # Create unique article URL
    article_url = f"https://test-article-{os.urandom(8).hex()}.com"
    
    # Insert article without embedding - should succeed
    article_result = test_supabase_client.table('articles').insert({
        'feed_id': test_feed['id'],
        'title': article_title,
        'url': article_url,
        'embedding': None  # Explicitly set to NULL
    }).execute()
    article = article_result.data[0]
    
    # Verify article was created successfully
    assert article['id'] is not None, "Article should be created successfully"
    assert article['embedding'] is None, "Embedding should be NULL"
    
    # Cleanup
    test_supabase_client.table('articles').delete().eq('id', article['id']).execute()



# ============================================================================
# Property 15: Seed Script Active Flag (Task 6.15)
# ============================================================================

@given(
    dummy=st.just(None)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_15_seed_script_active_flag(test_supabase_client: Client, dummy):
    """
    **Validates: Requirements 4.7**
    
    Property 15: Seed Script Active Flag
    
    For any feed inserted by the seed script, the is_active field should
    be set to true.
    """
    # Query all feeds that match the seed script pattern
    # We'll check feeds from known categories used in seed script
    seed_categories = ['前端開發', '自架服務', 'AI 應用']
    
    for category in seed_categories:
        feeds = test_supabase_client.table('feeds')\
            .select('*').eq('category', category).execute()
        
        # If feeds exist in this category, verify they have is_active = true
        for feed in feeds.data:
            assert feed['is_active'] is True, \
                f"Feed '{feed['name']}' should have is_active=true"


# ============================================================================
# Property 16: Seed Script Duplicate Handling (Task 6.16)
# ============================================================================

@given(
    feed_name=valid_text(min_size=1, max_size=100),
    category=valid_text(min_size=1, max_size=50),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_16_seed_script_duplicate_handling(test_supabase_client: Client, feed_name, category):
    """
    **Validates: Requirements 4.8**
    
    Property 16: Seed Script Duplicate Handling
    
    For any feed URL that already exists in the database, when the seed
    script attempts to insert it, the script should skip that feed and
    continue processing remaining feeds without crashing.
    """
    # Create a feed with a unique URL
    feed_url = f"https://test-feed-{os.urandom(8).hex()}.com/rss.xml"
    
    feed_result = test_supabase_client.table('feeds').insert({
        'name': feed_name,
        'url': feed_url,
        'category': category,
        'is_active': True
    }).execute()
    feed_id = feed_result.data[0]['id']
    
    # Simulate seed script behavior: try to insert duplicate, catch error, continue
    try:
        test_supabase_client.table('feeds').insert({
            'name': f"{feed_name} Duplicate",
            'url': feed_url,  # Same URL
            'category': category,
            'is_active': True
        }).execute()
        pytest.fail("Duplicate feed insertion should have failed")
    except Exception as e:
        # This is expected - seed script should catch this and continue
        error_msg = str(e).lower()
        assert 'duplicate' in error_msg or 'unique' in error_msg, \
            f"Expected duplicate key error, got: {e}"
    
    # Verify original feed still exists
    feed_check = test_supabase_client.table('feeds')\
        .select('*').eq('id', feed_id).execute()
    assert len(feed_check.data) == 1, "Original feed should still exist"
    
    # Cleanup
    test_supabase_client.table('feeds').delete().eq('id', feed_id).execute()



# ============================================================================
# Property 17: Updated Timestamp Trigger (Task 6.17)
# ============================================================================

@given(
    dummy=st.just(None)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_property_17_updated_timestamp_trigger(test_supabase_client: Client, test_user, test_article, dummy):
    """
    **Validates: Requirements 8.8**
    
    Property 17: Updated Timestamp Trigger
    
    For any reading_list record that is modified (UPDATE operation), the
    updated_at timestamp should be automatically updated to the current time.
    """
    # Create reading list entry
    reading_list_result = test_supabase_client.table('reading_list').insert({
        'user_id': test_user['id'],
        'article_id': test_article['id'],
        'status': 'Unread'
    }).execute()
    reading_list = reading_list_result.data[0]
    reading_list_id = reading_list['id']
    initial_updated_at = reading_list['updated_at']
    
    # Wait a moment to ensure timestamp difference
    time.sleep(1)
    
    # Update the reading list entry
    update_result = test_supabase_client.table('reading_list')\
        .update({'status': 'Read'})\
        .eq('id', reading_list_id)\
        .execute()
    
    # Fetch the updated record
    updated_reading_list = test_supabase_client.table('reading_list')\
        .select('*').eq('id', reading_list_id).execute()
    
    assert len(updated_reading_list.data) == 1, "Reading list entry should exist"
    new_updated_at = updated_reading_list.data[0]['updated_at']
    
    # Verify updated_at has changed
    assert new_updated_at != initial_updated_at, \
        "updated_at should be automatically updated on modification"
    
    # Verify new timestamp is later than initial timestamp
    from datetime import datetime
    initial_dt = datetime.fromisoformat(initial_updated_at.replace('Z', '+00:00'))
    new_dt = datetime.fromisoformat(new_updated_at.replace('Z', '+00:00'))
    assert new_dt > initial_dt, \
        "New updated_at should be later than initial updated_at"
    
    # Cleanup
    test_supabase_client.table('reading_list').delete().eq('id', reading_list_id).execute()
