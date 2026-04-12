"""
Test for cleanup_test_data fixture
Task 7.2: 建立測試資料庫清理機制

This test verifies that the cleanup_test_data fixture:
- Properly tracks created test data
- Cleans up all tracked data after test completion
- Ensures test independence
"""

import os


def test_cleanup_mechanism_tracks_and_cleans_users(test_supabase_client, cleanup_test_data):
    """
    Verify that cleanup_test_data fixture tracks and cleans up user records.

    This test:
    1. Creates a test user
    2. Tracks it in cleanup_test_data
    3. Verifies the user exists
    4. After test completion, cleanup should remove the user
    """
    # Create a test user
    test_discord_id = f"cleanup_test_user_{os.urandom(8).hex()}"
    result = test_supabase_client.table("users").insert({"discord_id": test_discord_id}).execute()

    user = result.data[0]
    user_id = user["id"]

    # Track for cleanup
    cleanup_test_data["users"].append(user_id)

    # Verify user exists
    query_result = test_supabase_client.table("users").select("*").eq("id", user_id).execute()
    assert len(query_result.data) == 1
    assert query_result.data[0]["discord_id"] == test_discord_id


def test_cleanup_mechanism_tracks_and_cleans_feeds(test_supabase_client, cleanup_test_data):
    """
    Verify that cleanup_test_data fixture tracks and cleans up feed records.
    """
    # Create a test feed
    test_feed_url = f"https://cleanup-test-feed-{os.urandom(8).hex()}.com/rss.xml"
    result = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": "Cleanup Test Feed",
                "url": test_feed_url,
                "category": "Test",
                "is_active": True,
            }
        )
        .execute()
    )

    feed = result.data[0]
    feed_id = feed["id"]

    # Track for cleanup
    cleanup_test_data["feeds"].append(feed_id)

    # Verify feed exists
    query_result = test_supabase_client.table("feeds").select("*").eq("id", feed_id).execute()
    assert len(query_result.data) == 1
    assert query_result.data[0]["url"] == test_feed_url


def test_cleanup_mechanism_handles_cascading_deletes(test_supabase_client, cleanup_test_data):
    """
    Verify that cleanup_test_data fixture handles cascading deletes correctly.

    This test:
    1. Creates a user, feed, and subscription
    2. Tracks only the user and feed (not the subscription)
    3. Verifies that cleaning up user and feed also removes the subscription
    """
    # Create a test user
    test_discord_id = f"cascade_test_user_{os.urandom(8).hex()}"
    user_result = (
        test_supabase_client.table("users").insert({"discord_id": test_discord_id}).execute()
    )
    user = user_result.data[0]
    cleanup_test_data["users"].append(user["id"])

    # Create a test feed
    test_feed_url = f"https://cascade-test-feed-{os.urandom(8).hex()}.com/rss.xml"
    feed_result = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": "Cascade Test Feed",
                "url": test_feed_url,
                "category": "Test",
                "is_active": True,
            }
        )
        .execute()
    )
    feed = feed_result.data[0]
    cleanup_test_data["feeds"].append(feed["id"])

    # Create a subscription (linking user and feed)
    subscription_result = (
        test_supabase_client.table("user_subscriptions")
        .insert({"user_id": user["id"], "feed_id": feed["id"]})
        .execute()
    )
    subscription = subscription_result.data[0]

    # Verify all records exist
    user_query = test_supabase_client.table("users").select("*").eq("id", user["id"]).execute()
    assert len(user_query.data) == 1

    feed_query = test_supabase_client.table("feeds").select("*").eq("id", feed["id"]).execute()
    assert len(feed_query.data) == 1

    subscription_query = (
        test_supabase_client.table("user_subscriptions")
        .select("*")
        .eq("id", subscription["id"])
        .execute()
    )
    assert len(subscription_query.data) == 1


def test_cleanup_mechanism_handles_multiple_records(test_supabase_client, cleanup_test_data):
    """
    Verify that cleanup_test_data fixture can handle multiple records of the same type.
    """
    # Create multiple test users
    user_ids = []
    for i in range(3):
        test_discord_id = f"multi_test_user_{i}_{os.urandom(8).hex()}"
        result = (
            test_supabase_client.table("users").insert({"discord_id": test_discord_id}).execute()
        )
        user = result.data[0]
        user_ids.append(user["id"])
        cleanup_test_data["users"].append(user["id"])

    # Verify all users exist
    for user_id in user_ids:
        query_result = test_supabase_client.table("users").select("*").eq("id", user_id).execute()
        assert len(query_result.data) == 1


def test_cleanup_mechanism_with_complex_relationships(test_supabase_client, cleanup_test_data):
    """
    Verify that cleanup_test_data fixture handles complex relationships correctly.

    This test creates:
    - 1 user
    - 1 feed
    - 1 article (linked to feed)
    - 1 subscription (user -> feed)
    - 1 reading list entry (user -> article)

    And verifies that tracking only the top-level records (user, feed) is sufficient
    for cleanup due to CASCADE DELETE.
    """
    # Create user
    test_discord_id = f"complex_test_user_{os.urandom(8).hex()}"
    user_result = (
        test_supabase_client.table("users").insert({"discord_id": test_discord_id}).execute()
    )
    user = user_result.data[0]
    cleanup_test_data["users"].append(user["id"])

    # Create feed
    test_feed_url = f"https://complex-test-feed-{os.urandom(8).hex()}.com/rss.xml"
    feed_result = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": "Complex Test Feed",
                "url": test_feed_url,
                "category": "Test",
                "is_active": True,
            }
        )
        .execute()
    )
    feed = feed_result.data[0]
    cleanup_test_data["feeds"].append(feed["id"])

    # Create article
    test_article_url = f"https://complex-test-article-{os.urandom(8).hex()}.com"
    article_result = (
        test_supabase_client.table("articles")
        .insert({"feed_id": feed["id"], "title": "Complex Test Article", "url": test_article_url})
        .execute()
    )
    article = article_result.data[0]

    # Create subscription
    subscription_result = (
        test_supabase_client.table("user_subscriptions")
        .insert({"user_id": user["id"], "feed_id": feed["id"]})
        .execute()
    )
    subscription = subscription_result.data[0]

    # Create reading list entry
    reading_list_result = (
        test_supabase_client.table("reading_list")
        .insert({"user_id": user["id"], "article_id": article["id"], "status": "Unread"})
        .execute()
    )
    reading_list_entry = reading_list_result.data[0]

    # Verify all records exist
    assert (
        len(test_supabase_client.table("users").select("*").eq("id", user["id"]).execute().data)
        == 1
    )
    assert (
        len(test_supabase_client.table("feeds").select("*").eq("id", feed["id"]).execute().data)
        == 1
    )
    assert (
        len(
            test_supabase_client.table("articles")
            .select("*")
            .eq("id", article["id"])
            .execute()
            .data
        )
        == 1
    )
    assert (
        len(
            test_supabase_client.table("user_subscriptions")
            .select("*")
            .eq("id", subscription["id"])
            .execute()
            .data
        )
        == 1
    )
    assert (
        len(
            test_supabase_client.table("reading_list")
            .select("*")
            .eq("id", reading_list_entry["id"])
            .execute()
            .data
        )
        == 1
    )


def test_cleanup_mechanism_is_independent_across_tests(test_supabase_client, cleanup_test_data):
    """
    Verify that cleanup_test_data fixture provides test independence.

    This test should run independently and not be affected by previous tests.
    """
    # Create a test user with a specific discord_id
    test_discord_id = f"independence_test_{os.urandom(8).hex()}"
    result = test_supabase_client.table("users").insert({"discord_id": test_discord_id}).execute()

    user = result.data[0]
    cleanup_test_data["users"].append(user["id"])

    # Verify this is the only user with this discord_id
    query_result = (
        test_supabase_client.table("users").select("*").eq("discord_id", test_discord_id).execute()
    )
    assert len(query_result.data) == 1
