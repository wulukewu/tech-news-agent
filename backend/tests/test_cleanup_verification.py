"""
Verification test for cleanup_test_data fixture
Task 7.2: 建立測試資料庫清理機制

This test verifies that the cleanup mechanism actually removes data from the database
after test completion, ensuring test independence.
"""
import pytest
import os


# Store IDs from first test to verify they're cleaned up in second test
_test_user_id = None
_test_feed_id = None


def test_01_create_data_and_track_ids(test_supabase_client, cleanup_test_data):
    """
    First test: Create data and store IDs for verification in next test.
    """
    global _test_user_id, _test_feed_id
    
    # Create a test user
    test_discord_id = f"verification_user_{os.urandom(8).hex()}"
    user_result = test_supabase_client.table('users').insert({
        'discord_id': test_discord_id
    }).execute()
    user = user_result.data[0]
    _test_user_id = user['id']
    cleanup_test_data['users'].append(user['id'])
    
    # Create a test feed
    test_feed_url = f"https://verification-feed-{os.urandom(8).hex()}.com/rss.xml"
    feed_result = test_supabase_client.table('feeds').insert({
        'name': 'Verification Feed',
        'url': test_feed_url,
        'category': 'Test',
        'is_active': True
    }).execute()
    feed = feed_result.data[0]
    _test_feed_id = feed['id']
    cleanup_test_data['feeds'].append(feed['id'])
    
    # Verify data exists
    user_query = test_supabase_client.table('users').select('*').eq('id', _test_user_id).execute()
    assert len(user_query.data) == 1
    
    feed_query = test_supabase_client.table('feeds').select('*').eq('id', _test_feed_id).execute()
    assert len(feed_query.data) == 1


def test_02_verify_data_was_cleaned_up(test_supabase_client):
    """
    Second test: Verify that data from previous test was cleaned up.
    
    This test runs after test_01_create_data_and_track_ids and verifies
    that the cleanup mechanism successfully removed the data.
    """
    global _test_user_id, _test_feed_id
    
    # Skip if IDs weren't set (test order issue)
    if _test_user_id is None or _test_feed_id is None:
        pytest.skip("Previous test didn't run or set IDs")
    
    # Verify user was cleaned up
    user_query = test_supabase_client.table('users').select('*').eq('id', _test_user_id).execute()
    assert len(user_query.data) == 0, f"User {_test_user_id} should have been cleaned up"
    
    # Verify feed was cleaned up
    feed_query = test_supabase_client.table('feeds').select('*').eq('id', _test_feed_id).execute()
    assert len(feed_query.data) == 0, f"Feed {_test_feed_id} should have been cleaned up"
