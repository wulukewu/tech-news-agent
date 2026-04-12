"""
Comprehensive Property-Based Tests for Supabase Migration Phase 1
Task 6: 實作所有屬性測試

This module contains all 17 property-based tests validating the database schema,
constraints, and behaviors defined in the design document.

Each test uses Hypothesis for property-based testing and includes:
- Feature tag: supabase-migration-phase1
- Property number and description
- Requirement validation reference
- Proper cleanup using fixtures
"""

import os
import time
from datetime import UTC, datetime

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st


# Helper function for generating valid UTF-8 text (ASCII printable range)
def safe_text(min_size=1, max_size=100):
    """Generate valid UTF-8 text without surrogate pairs or control characters."""
    return st.text(
        min_size=min_size,
        max_size=max_size,
        alphabet=st.characters(min_codepoint=32, max_codepoint=126),
    )


# ============================================================================
# Property 1: User Deletion Cascades
# ============================================================================


# Feature: supabase-migration-phase1, Property 1: User Deletion Cascades
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(discord_id=safe_text(min_size=1, max_size=100), feed_url=safe_text(min_size=1, max_size=50))
def test_property_1_user_deletion_cascades(
    test_supabase_client, cleanup_test_data, discord_id, feed_url
):
    """
    Property 1: User Deletion Cascades

    For any user record with related subscriptions and reading list entries,
    when the user is deleted, all related records in user_subscriptions and
    reading_list tables should be automatically deleted.

    **Validates: Requirements 3.9**
    """
    # Create unique identifiers
    unique_discord_id = f"{discord_id}_{os.urandom(4).hex()}"
    unique_feed_url = f"https://{os.urandom(4).hex()}-{feed_url.replace('://', '-')}.com/rss"

    # Create user
    user_result = (
        test_supabase_client.table("users").insert({"discord_id": unique_discord_id}).execute()
    )
    user = user_result.data[0]
    cleanup_test_data["users"].append(user["id"])

    # Create feed
    feed_result = (
        test_supabase_client.table("feeds")
        .insert({"name": "Test Feed", "url": unique_feed_url, "category": "Test"})
        .execute()
    )
    feed = feed_result.data[0]
    cleanup_test_data["feeds"].append(feed["id"])

    # Create subscription
    subscription_result = (
        test_supabase_client.table("user_subscriptions")
        .insert({"user_id": user["id"], "feed_id": feed["id"]})
        .execute()
    )
    subscription = subscription_result.data[0]

    # Create article
    article_url = f"https://article-{os.urandom(4).hex()}.com"
    article_result = (
        test_supabase_client.table("articles")
        .insert({"feed_id": feed["id"], "title": "Test Article", "url": article_url})
        .execute()
    )
    article = article_result.data[0]
    cleanup_test_data["articles"].append(article["id"])

    # Create reading list entry
    reading_list_result = (
        test_supabase_client.table("reading_list")
        .insert({"user_id": user["id"], "article_id": article["id"], "status": "Unread"})
        .execute()
    )
    reading_list_entry = reading_list_result.data[0]

    # Delete user
    test_supabase_client.table("users").delete().eq("id", user["id"]).execute()

    # Verify subscription was cascade deleted
    subscription_check = (
        test_supabase_client.table("user_subscriptions")
        .select("*")
        .eq("id", subscription["id"])
        .execute()
    )
    assert len(subscription_check.data) == 0, "Subscription should be cascade deleted"

    # Verify reading list entry was cascade deleted
    reading_list_check = (
        test_supabase_client.table("reading_list")
        .select("*")
        .eq("id", reading_list_entry["id"])
        .execute()
    )
    assert len(reading_list_check.data) == 0, "Reading list entry should be cascade deleted"


# ============================================================================
# Property 2: Feed Deletion Cascades
# ============================================================================


# Feature: supabase-migration-phase1, Property 2: Feed Deletion Cascades
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(feed_url=safe_text(min_size=1, max_size=50))
def test_property_2_feed_deletion_cascades(test_supabase_client, cleanup_test_data, feed_url):
    """
    Property 2: Feed Deletion Cascades

    For any feed record with related articles, when the feed is deleted,
    all related records in the articles table should be automatically deleted.

    **Validates: Requirements 3.10**
    """
    # Create unique feed URL
    unique_feed_url = f"https://{os.urandom(4).hex()}-{feed_url.replace('://', '-')}.com/rss"

    # Create feed
    feed_result = (
        test_supabase_client.table("feeds")
        .insert({"name": "Test Feed", "url": unique_feed_url, "category": "Test"})
        .execute()
    )
    feed = feed_result.data[0]
    cleanup_test_data["feeds"].append(feed["id"])

    # Create article
    article_url = f"https://article-{os.urandom(4).hex()}.com"
    article_result = (
        test_supabase_client.table("articles")
        .insert({"feed_id": feed["id"], "title": "Test Article", "url": article_url})
        .execute()
    )
    article = article_result.data[0]

    # Delete feed
    test_supabase_client.table("feeds").delete().eq("id", feed["id"]).execute()

    # Verify article was cascade deleted
    article_check = (
        test_supabase_client.table("articles").select("*").eq("id", article["id"]).execute()
    )
    assert len(article_check.data) == 0, "Article should be cascade deleted"


# ============================================================================
# Property 3: Article Deletion Cascades
# ============================================================================


# Feature: supabase-migration-phase1, Property 3: Article Deletion Cascades
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(discord_id=safe_text(min_size=1, max_size=100))
def test_property_3_article_deletion_cascades(test_supabase_client, cleanup_test_data, discord_id):
    """
    Property 3: Article Deletion Cascades

    For any article record with related reading list entries, when the article
    is deleted, all related records in the reading_list table should be
    automatically deleted.

    **Validates: Requirements 3.11**
    """
    # Create unique identifiers
    unique_discord_id = f"{discord_id}_{os.urandom(4).hex()}"
    unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"
    unique_article_url = f"https://article-{os.urandom(4).hex()}.com"

    # Create user
    user_result = (
        test_supabase_client.table("users").insert({"discord_id": unique_discord_id}).execute()
    )
    user = user_result.data[0]
    cleanup_test_data["users"].append(user["id"])

    # Create feed
    feed_result = (
        test_supabase_client.table("feeds")
        .insert({"name": "Test Feed", "url": unique_feed_url, "category": "Test"})
        .execute()
    )
    feed = feed_result.data[0]
    cleanup_test_data["feeds"].append(feed["id"])

    # Create article
    article_result = (
        test_supabase_client.table("articles")
        .insert({"feed_id": feed["id"], "title": "Test Article", "url": unique_article_url})
        .execute()
    )
    article = article_result.data[0]
    cleanup_test_data["articles"].append(article["id"])

    # Create reading list entry
    reading_list_result = (
        test_supabase_client.table("reading_list")
        .insert({"user_id": user["id"], "article_id": article["id"], "status": "Unread"})
        .execute()
    )
    reading_list_entry = reading_list_result.data[0]

    # Delete article
    test_supabase_client.table("articles").delete().eq("id", article["id"]).execute()

    # Verify reading list entry was cascade deleted
    reading_list_check = (
        test_supabase_client.table("reading_list")
        .select("*")
        .eq("id", reading_list_entry["id"])
        .execute()
    )
    assert len(reading_list_check.data) == 0, "Reading list entry should be cascade deleted"


# ============================================================================
# Property 4: Discord ID Uniqueness
# ============================================================================


# Feature: supabase-migration-phase1, Property 4: Discord ID Uniqueness
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(discord_id=safe_text(min_size=1, max_size=100))
def test_property_4_discord_id_uniqueness(test_supabase_client, cleanup_test_data, discord_id):
    """
    Property 4: Discord ID Uniqueness

    For any two user records with the same discord_id value, the database
    should reject the second insertion with a unique constraint violation.

    **Validates: Requirements 6.1**
    """
    # Create unique discord_id
    unique_discord_id = f"{discord_id}_{os.urandom(4).hex()}"

    # Insert first user
    user1_result = (
        test_supabase_client.table("users").insert({"discord_id": unique_discord_id}).execute()
    )
    user1 = user1_result.data[0]
    cleanup_test_data["users"].append(user1["id"])

    # Attempt to insert second user with same discord_id (should fail)
    with pytest.raises(Exception) as exc_info:
        test_supabase_client.table("users").insert({"discord_id": unique_discord_id}).execute()

    # Verify it's a unique constraint violation
    error_message = str(exc_info.value).lower()
    assert (
        "duplicate" in error_message or "unique" in error_message
    ), "Should raise unique constraint violation"


# ============================================================================
# Property 5: Subscription Uniqueness
# ============================================================================


# Feature: supabase-migration-phase1, Property 5: Subscription Uniqueness
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(discord_id=safe_text(min_size=1, max_size=100))
def test_property_5_subscription_uniqueness(test_supabase_client, cleanup_test_data, discord_id):
    """
    Property 5: Subscription Uniqueness

    For any user and feed combination, attempting to create duplicate
    subscriptions (same user_id and feed_id) should be rejected by the
    database with a unique constraint violation.

    **Validates: Requirements 6.4**
    """
    # Create unique identifiers
    unique_discord_id = f"{discord_id}_{os.urandom(4).hex()}"
    unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"

    # Create user
    user_result = (
        test_supabase_client.table("users").insert({"discord_id": unique_discord_id}).execute()
    )
    user = user_result.data[0]
    cleanup_test_data["users"].append(user["id"])

    # Create feed
    feed_result = (
        test_supabase_client.table("feeds")
        .insert({"name": "Test Feed", "url": unique_feed_url, "category": "Test"})
        .execute()
    )
    feed = feed_result.data[0]
    cleanup_test_data["feeds"].append(feed["id"])

    # Create first subscription
    subscription1_result = (
        test_supabase_client.table("user_subscriptions")
        .insert({"user_id": user["id"], "feed_id": feed["id"]})
        .execute()
    )
    subscription1 = subscription1_result.data[0]
    cleanup_test_data["subscriptions"].append(subscription1["id"])

    # Attempt to create duplicate subscription (should fail)
    with pytest.raises(Exception) as exc_info:
        test_supabase_client.table("user_subscriptions").insert(
            {"user_id": user["id"], "feed_id": feed["id"]}
        ).execute()

    # Verify it's a unique constraint violation
    error_message = str(exc_info.value).lower()
    assert (
        "duplicate" in error_message or "unique" in error_message
    ), "Should raise unique constraint violation"


# ============================================================================
# Property 6: Reading List Entry Uniqueness
# ============================================================================


# Feature: supabase-migration-phase1, Property 6: Reading List Entry Uniqueness
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(discord_id=safe_text(min_size=1, max_size=100))
def test_property_6_reading_list_entry_uniqueness(
    test_supabase_client, cleanup_test_data, discord_id
):
    """
    Property 6: Reading List Entry Uniqueness

    For any user and article combination, attempting to create duplicate
    reading list entries (same user_id and article_id) should be rejected
    by the database with a unique constraint violation.

    **Validates: Requirements 6.5**
    """
    # Create unique identifiers
    unique_discord_id = f"{discord_id}_{os.urandom(4).hex()}"
    unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"
    unique_article_url = f"https://article-{os.urandom(4).hex()}.com"

    # Create user
    user_result = (
        test_supabase_client.table("users").insert({"discord_id": unique_discord_id}).execute()
    )
    user = user_result.data[0]
    cleanup_test_data["users"].append(user["id"])

    # Create feed
    feed_result = (
        test_supabase_client.table("feeds")
        .insert({"name": "Test Feed", "url": unique_feed_url, "category": "Test"})
        .execute()
    )
    feed = feed_result.data[0]
    cleanup_test_data["feeds"].append(feed["id"])

    # Create article
    article_result = (
        test_supabase_client.table("articles")
        .insert({"feed_id": feed["id"], "title": "Test Article", "url": unique_article_url})
        .execute()
    )
    article = article_result.data[0]
    cleanup_test_data["articles"].append(article["id"])

    # Create first reading list entry
    entry1_result = (
        test_supabase_client.table("reading_list")
        .insert({"user_id": user["id"], "article_id": article["id"], "status": "Unread"})
        .execute()
    )
    entry1 = entry1_result.data[0]
    cleanup_test_data["reading_list"].append(entry1["id"])

    # Attempt to create duplicate reading list entry (should fail)
    with pytest.raises(Exception) as exc_info:
        test_supabase_client.table("reading_list").insert(
            {"user_id": user["id"], "article_id": article["id"], "status": "Read"}
        ).execute()

    # Verify it's a unique constraint violation
    error_message = str(exc_info.value).lower()
    assert (
        "duplicate" in error_message or "unique" in error_message
    ), "Should raise unique constraint violation"


# ============================================================================
# Property 7: Feed URL Uniqueness
# ============================================================================


# Feature: supabase-migration-phase1, Property 7: Feed URL Uniqueness
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(feed_url=safe_text(min_size=1, max_size=50))
def test_property_7_feed_url_uniqueness(test_supabase_client, cleanup_test_data, feed_url):
    """
    Property 7: Feed URL Uniqueness

    For any two feed records with the same URL value, the database should
    reject the second insertion with a unique constraint violation.

    **Validates: Requirements 7.3**
    """
    # Create unique feed URL
    unique_feed_url = f"https://{os.urandom(4).hex()}-{feed_url.replace('://', '-')}.com/rss"

    # Insert first feed
    feed1_result = (
        test_supabase_client.table("feeds")
        .insert({"name": "Test Feed 1", "url": unique_feed_url, "category": "Test"})
        .execute()
    )
    feed1 = feed1_result.data[0]
    cleanup_test_data["feeds"].append(feed1["id"])

    # Attempt to insert second feed with same URL (should fail)
    with pytest.raises(Exception) as exc_info:
        test_supabase_client.table("feeds").insert(
            {"name": "Test Feed 2", "url": unique_feed_url, "category": "Test"}
        ).execute()

    # Verify it's a unique constraint violation
    error_message = str(exc_info.value).lower()
    assert (
        "duplicate" in error_message or "unique" in error_message
    ), "Should raise unique constraint violation"


# ============================================================================
# Property 8: Article URL Uniqueness
# ============================================================================


# Feature: supabase-migration-phase1, Property 8: Article URL Uniqueness
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(article_url=safe_text(min_size=1, max_size=50))
def test_property_8_article_url_uniqueness(test_supabase_client, cleanup_test_data, article_url):
    """
    Property 8: Article URL Uniqueness

    For any two article records with the same URL value, the database should
    reject the second insertion with a unique constraint violation.

    **Validates: Requirements 7.4**
    """
    # Create unique identifiers
    unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"
    unique_article_url = f"https://{os.urandom(4).hex()}-{article_url.replace('://', '-')}.com"

    # Create feed
    feed_result = (
        test_supabase_client.table("feeds")
        .insert({"name": "Test Feed", "url": unique_feed_url, "category": "Test"})
        .execute()
    )
    feed = feed_result.data[0]
    cleanup_test_data["feeds"].append(feed["id"])

    # Insert first article
    article1_result = (
        test_supabase_client.table("articles")
        .insert({"feed_id": feed["id"], "title": "Test Article 1", "url": unique_article_url})
        .execute()
    )
    article1 = article1_result.data[0]
    cleanup_test_data["articles"].append(article1["id"])

    # Attempt to insert second article with same URL (should fail)
    with pytest.raises(Exception) as exc_info:
        test_supabase_client.table("articles").insert(
            {"feed_id": feed["id"], "title": "Test Article 2", "url": unique_article_url}
        ).execute()

    # Verify it's a unique constraint violation
    error_message = str(exc_info.value).lower()
    assert (
        "duplicate" in error_message or "unique" in error_message
    ), "Should raise unique constraint violation"


# ============================================================================
# Property 9: Shared Feed References
# ============================================================================


# Feature: supabase-migration-phase1, Property 9: Shared Feed References
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(
    discord_id1=safe_text(min_size=1, max_size=100), discord_id2=safe_text(min_size=1, max_size=100)
)
def test_property_9_shared_feed_references(
    test_supabase_client, cleanup_test_data, discord_id1, discord_id2
):
    """
    Property 9: Shared Feed References

    For any feed that multiple users subscribe to, all subscription records
    should reference the same feed_id in the feeds table, ensuring no
    duplicate feed records exist.

    **Validates: Requirements 7.5**
    """
    # Create unique identifiers
    unique_discord_id1 = f"{discord_id1}_{os.urandom(4).hex()}"
    unique_discord_id2 = f"{discord_id2}_{os.urandom(4).hex()}"
    unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"

    # Ensure discord IDs are different
    assume(unique_discord_id1 != unique_discord_id2)

    # Create two users
    user1_result = (
        test_supabase_client.table("users").insert({"discord_id": unique_discord_id1}).execute()
    )
    user1 = user1_result.data[0]
    cleanup_test_data["users"].append(user1["id"])

    user2_result = (
        test_supabase_client.table("users").insert({"discord_id": unique_discord_id2}).execute()
    )
    user2 = user2_result.data[0]
    cleanup_test_data["users"].append(user2["id"])

    # Create one feed
    feed_result = (
        test_supabase_client.table("feeds")
        .insert({"name": "Shared Feed", "url": unique_feed_url, "category": "Test"})
        .execute()
    )
    feed = feed_result.data[0]
    cleanup_test_data["feeds"].append(feed["id"])

    # Both users subscribe to the same feed
    subscription1_result = (
        test_supabase_client.table("user_subscriptions")
        .insert({"user_id": user1["id"], "feed_id": feed["id"]})
        .execute()
    )
    subscription1 = subscription1_result.data[0]
    cleanup_test_data["subscriptions"].append(subscription1["id"])

    subscription2_result = (
        test_supabase_client.table("user_subscriptions")
        .insert({"user_id": user2["id"], "feed_id": feed["id"]})
        .execute()
    )
    subscription2 = subscription2_result.data[0]
    cleanup_test_data["subscriptions"].append(subscription2["id"])

    # Verify both subscriptions reference the same feed_id
    assert (
        subscription1["feed_id"] == subscription2["feed_id"]
    ), "Both subscriptions should reference the same feed_id"
    assert subscription1["feed_id"] == feed["id"], "Subscriptions should reference the created feed"

    # Verify only one feed exists with this URL
    feeds_check = (
        test_supabase_client.table("feeds").select("*").eq("url", unique_feed_url).execute()
    )
    assert len(feeds_check.data) == 1, "Only one feed should exist with this URL"


# ============================================================================
# Property 10: Required Field Validation
# ============================================================================


# Feature: supabase-migration-phase1, Property 10: Required Field Validation
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(
    field_choice=st.sampled_from(
        ["discord_id", "feed_name", "feed_url", "feed_category", "article_title", "article_url"]
    )
)
def test_property_10_required_field_validation(
    test_supabase_client, cleanup_test_data, field_choice
):
    """
    Property 10: Required Field Validation

    For any insertion attempt where a NOT NULL field (discord_id, feed name,
    feed url, feed category, article title, article url) is provided as NULL,
    the database should reject the insertion with a NOT NULL constraint violation.

    **Validates: Requirements 9.3, 9.4, 9.5, 9.6, 9.7, 9.8**
    """
    if field_choice == "discord_id":
        # Attempt to insert user without discord_id
        with pytest.raises(Exception) as exc_info:
            test_supabase_client.table("users").insert({}).execute()
        error_message = str(exc_info.value).lower()
        assert (
            "null" in error_message or "required" in error_message or "violates" in error_message
        ), "Should raise NOT NULL constraint violation"

    elif field_choice == "feed_name":
        # Attempt to insert feed without name
        unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"
        with pytest.raises(Exception) as exc_info:
            test_supabase_client.table("feeds").insert(
                {"url": unique_feed_url, "category": "Test"}
            ).execute()
        error_message = str(exc_info.value).lower()
        assert (
            "null" in error_message or "required" in error_message or "violates" in error_message
        ), "Should raise NOT NULL constraint violation"

    elif field_choice == "feed_url":
        # Attempt to insert feed without url
        with pytest.raises(Exception) as exc_info:
            test_supabase_client.table("feeds").insert(
                {"name": "Test Feed", "category": "Test"}
            ).execute()
        error_message = str(exc_info.value).lower()
        assert (
            "null" in error_message or "required" in error_message or "violates" in error_message
        ), "Should raise NOT NULL constraint violation"

    elif field_choice == "feed_category":
        # Attempt to insert feed without category
        unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"
        with pytest.raises(Exception) as exc_info:
            test_supabase_client.table("feeds").insert(
                {"name": "Test Feed", "url": unique_feed_url}
            ).execute()
        error_message = str(exc_info.value).lower()
        assert (
            "null" in error_message or "required" in error_message or "violates" in error_message
        ), "Should raise NOT NULL constraint violation"

    elif field_choice == "article_title":
        # Create feed first
        unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"
        feed_result = (
            test_supabase_client.table("feeds")
            .insert({"name": "Test Feed", "url": unique_feed_url, "category": "Test"})
            .execute()
        )
        feed = feed_result.data[0]
        cleanup_test_data["feeds"].append(feed["id"])

        # Attempt to insert article without title
        unique_article_url = f"https://article-{os.urandom(4).hex()}.com"
        with pytest.raises(Exception) as exc_info:
            test_supabase_client.table("articles").insert(
                {"feed_id": feed["id"], "url": unique_article_url}
            ).execute()
        error_message = str(exc_info.value).lower()
        assert (
            "null" in error_message or "required" in error_message or "violates" in error_message
        ), "Should raise NOT NULL constraint violation"

    elif field_choice == "article_url":
        # Create feed first
        unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"
        feed_result = (
            test_supabase_client.table("feeds")
            .insert({"name": "Test Feed", "url": unique_feed_url, "category": "Test"})
            .execute()
        )
        feed = feed_result.data[0]
        cleanup_test_data["feeds"].append(feed["id"])

        # Attempt to insert article without url
        with pytest.raises(Exception) as exc_info:
            test_supabase_client.table("articles").insert(
                {"feed_id": feed["id"], "title": "Test Article"}
            ).execute()
        error_message = str(exc_info.value).lower()
        assert (
            "null" in error_message or "required" in error_message or "violates" in error_message
        ), "Should raise NOT NULL constraint violation"


# ============================================================================
# Property 11: Timestamp Auto-Population
# ============================================================================


# Feature: supabase-migration-phase1, Property 11: Timestamp Auto-Population
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(
    table_choice=st.sampled_from(
        ["users", "feeds", "user_subscriptions", "articles", "reading_list"]
    )
)
def test_property_11_timestamp_auto_population(
    test_supabase_client, cleanup_test_data, table_choice
):
    """
    Property 11: Timestamp Auto-Population

    For any record inserted into users, feeds, user_subscriptions, articles,
    or reading_list tables without explicitly providing timestamp values,
    the database should automatically populate created_at (or subscribed_at/
    added_at/updated_at) with the current timestamp.

    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.6, 8.7**
    """
    before_insert = datetime.now(UTC)

    if table_choice == "users":
        unique_discord_id = f"test_user_{os.urandom(4).hex()}"
        result = (
            test_supabase_client.table("users").insert({"discord_id": unique_discord_id}).execute()
        )
        record = result.data[0]
        cleanup_test_data["users"].append(record["id"])

        # Verify created_at is auto-populated
        assert record["created_at"] is not None, "created_at should be auto-populated"
        created_at = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
        assert created_at >= before_insert, "created_at should be recent"

    elif table_choice == "feeds":
        unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"
        result = (
            test_supabase_client.table("feeds")
            .insert({"name": "Test Feed", "url": unique_feed_url, "category": "Test"})
            .execute()
        )
        record = result.data[0]
        cleanup_test_data["feeds"].append(record["id"])

        # Verify created_at is auto-populated
        assert record["created_at"] is not None, "created_at should be auto-populated"
        created_at = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
        assert created_at >= before_insert, "created_at should be recent"

    elif table_choice == "user_subscriptions":
        # Create user and feed first
        unique_discord_id = f"test_user_{os.urandom(4).hex()}"
        user_result = (
            test_supabase_client.table("users").insert({"discord_id": unique_discord_id}).execute()
        )
        user = user_result.data[0]
        cleanup_test_data["users"].append(user["id"])

        unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"
        feed_result = (
            test_supabase_client.table("feeds")
            .insert({"name": "Test Feed", "url": unique_feed_url, "category": "Test"})
            .execute()
        )
        feed = feed_result.data[0]
        cleanup_test_data["feeds"].append(feed["id"])

        result = (
            test_supabase_client.table("user_subscriptions")
            .insert({"user_id": user["id"], "feed_id": feed["id"]})
            .execute()
        )
        record = result.data[0]
        cleanup_test_data["subscriptions"].append(record["id"])

        # Verify subscribed_at is auto-populated
        assert record["subscribed_at"] is not None, "subscribed_at should be auto-populated"
        subscribed_at = datetime.fromisoformat(record["subscribed_at"].replace("Z", "+00:00"))
        assert subscribed_at >= before_insert, "subscribed_at should be recent"

    elif table_choice == "articles":
        # Create feed first
        unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"
        feed_result = (
            test_supabase_client.table("feeds")
            .insert({"name": "Test Feed", "url": unique_feed_url, "category": "Test"})
            .execute()
        )
        feed = feed_result.data[0]
        cleanup_test_data["feeds"].append(feed["id"])

        unique_article_url = f"https://article-{os.urandom(4).hex()}.com"
        result = (
            test_supabase_client.table("articles")
            .insert({"feed_id": feed["id"], "title": "Test Article", "url": unique_article_url})
            .execute()
        )
        record = result.data[0]
        cleanup_test_data["articles"].append(record["id"])

        # Verify created_at is auto-populated
        assert record["created_at"] is not None, "created_at should be auto-populated"
        created_at = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
        assert created_at >= before_insert, "created_at should be recent"

    elif table_choice == "reading_list":
        # Create user, feed, and article first
        unique_discord_id = f"test_user_{os.urandom(4).hex()}"
        user_result = (
            test_supabase_client.table("users").insert({"discord_id": unique_discord_id}).execute()
        )
        user = user_result.data[0]
        cleanup_test_data["users"].append(user["id"])

        unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"
        feed_result = (
            test_supabase_client.table("feeds")
            .insert({"name": "Test Feed", "url": unique_feed_url, "category": "Test"})
            .execute()
        )
        feed = feed_result.data[0]
        cleanup_test_data["feeds"].append(feed["id"])

        unique_article_url = f"https://article-{os.urandom(4).hex()}.com"
        article_result = (
            test_supabase_client.table("articles")
            .insert({"feed_id": feed["id"], "title": "Test Article", "url": unique_article_url})
            .execute()
        )
        article = article_result.data[0]
        cleanup_test_data["articles"].append(article["id"])

        result = (
            test_supabase_client.table("reading_list")
            .insert({"user_id": user["id"], "article_id": article["id"], "status": "Unread"})
            .execute()
        )
        record = result.data[0]
        cleanup_test_data["reading_list"].append(record["id"])

        # Verify added_at and updated_at are auto-populated
        assert record["added_at"] is not None, "added_at should be auto-populated"
        assert record["updated_at"] is not None, "updated_at should be auto-populated"
        added_at = datetime.fromisoformat(record["added_at"].replace("Z", "+00:00"))
        updated_at = datetime.fromisoformat(record["updated_at"].replace("Z", "+00:00"))
        assert added_at >= before_insert, "added_at should be recent"
        assert updated_at >= before_insert, "updated_at should be recent"


# ============================================================================
# Property 12: Reading List Status Validation
# ============================================================================


# Feature: supabase-migration-phase1, Property 12: Reading List Status Validation
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(
    status=safe_text(min_size=1, max_size=50).filter(
        lambda s: s not in ["Unread", "Read", "Archived"]
    )
)
def test_property_12_reading_list_status_validation(
    test_supabase_client, cleanup_test_data, status
):
    """
    Property 12: Reading List Status Validation

    For any reading list entry with a status value not in the set
    {'Unread', 'Read', 'Archived'}, the database should reject the
    insertion or update with a CHECK constraint violation.

    **Validates: Requirements 9.1**
    """
    # Create user, feed, and article first
    unique_discord_id = f"test_user_{os.urandom(4).hex()}"
    user_result = (
        test_supabase_client.table("users").insert({"discord_id": unique_discord_id}).execute()
    )
    user = user_result.data[0]
    cleanup_test_data["users"].append(user["id"])

    unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"
    feed_result = (
        test_supabase_client.table("feeds")
        .insert({"name": "Test Feed", "url": unique_feed_url, "category": "Test"})
        .execute()
    )
    feed = feed_result.data[0]
    cleanup_test_data["feeds"].append(feed["id"])

    unique_article_url = f"https://article-{os.urandom(4).hex()}.com"
    article_result = (
        test_supabase_client.table("articles")
        .insert({"feed_id": feed["id"], "title": "Test Article", "url": unique_article_url})
        .execute()
    )
    article = article_result.data[0]
    cleanup_test_data["articles"].append(article["id"])

    # Attempt to insert reading list entry with invalid status (should fail)
    with pytest.raises(Exception) as exc_info:
        test_supabase_client.table("reading_list").insert(
            {"user_id": user["id"], "article_id": article["id"], "status": status}
        ).execute()

    # Verify it's a CHECK constraint violation
    error_message = str(exc_info.value).lower()
    assert (
        "check" in error_message or "constraint" in error_message or "violates" in error_message
    ), "Should raise CHECK constraint violation"


# ============================================================================
# Property 13: Rating Range Validation
# ============================================================================


# Feature: supabase-migration-phase1, Property 13: Rating Range Validation
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(rating=st.integers().filter(lambda r: r < 1 or r > 5))
def test_property_13_rating_range_validation(test_supabase_client, cleanup_test_data, rating):
    """
    Property 13: Rating Range Validation

    For any reading list entry with a rating value outside the range [1, 5],
    the database should reject the insertion or update with a CHECK
    constraint violation.

    **Validates: Requirements 9.2**
    """
    # Create user, feed, and article first
    unique_discord_id = f"test_user_{os.urandom(4).hex()}"
    user_result = (
        test_supabase_client.table("users").insert({"discord_id": unique_discord_id}).execute()
    )
    user = user_result.data[0]
    cleanup_test_data["users"].append(user["id"])

    unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"
    feed_result = (
        test_supabase_client.table("feeds")
        .insert({"name": "Test Feed", "url": unique_feed_url, "category": "Test"})
        .execute()
    )
    feed = feed_result.data[0]
    cleanup_test_data["feeds"].append(feed["id"])

    unique_article_url = f"https://article-{os.urandom(4).hex()}.com"
    article_result = (
        test_supabase_client.table("articles")
        .insert({"feed_id": feed["id"], "title": "Test Article", "url": unique_article_url})
        .execute()
    )
    article = article_result.data[0]
    cleanup_test_data["articles"].append(article["id"])

    # Attempt to insert reading list entry with invalid rating (should fail)
    with pytest.raises(Exception) as exc_info:
        test_supabase_client.table("reading_list").insert(
            {
                "user_id": user["id"],
                "article_id": article["id"],
                "status": "Unread",
                "rating": rating,
            }
        ).execute()

    # Verify it's a CHECK constraint violation
    error_message = str(exc_info.value).lower()
    assert (
        "check" in error_message or "constraint" in error_message or "violates" in error_message
    ), "Should raise CHECK constraint violation"


# ============================================================================
# Property 14: Embedding NULL Tolerance
# ============================================================================


# Feature: supabase-migration-phase1, Property 14: Embedding NULL Tolerance
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(article_title=safe_text(min_size=1, max_size=200))
def test_property_14_embedding_null_tolerance(
    test_supabase_client, cleanup_test_data, article_title
):
    """
    Property 14: Embedding NULL Tolerance

    For any article inserted without an embedding value (NULL), the insertion
    should succeed, allowing articles to exist before embeddings are generated.

    **Validates: Requirements 5.4**
    """
    # Create feed first
    unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"
    feed_result = (
        test_supabase_client.table("feeds")
        .insert({"name": "Test Feed", "url": unique_feed_url, "category": "Test"})
        .execute()
    )
    feed = feed_result.data[0]
    cleanup_test_data["feeds"].append(feed["id"])

    # Insert article without embedding (should succeed)
    unique_article_url = f"https://article-{os.urandom(4).hex()}.com"
    article_result = (
        test_supabase_client.table("articles")
        .insert(
            {
                "feed_id": feed["id"],
                "title": article_title,
                "url": unique_article_url,
                # Note: embedding is NOT provided (NULL)
            }
        )
        .execute()
    )
    article = article_result.data[0]
    cleanup_test_data["articles"].append(article["id"])

    # Verify article was created successfully
    assert article["id"] is not None, "Article should be created"
    assert article["title"] == article_title, "Article title should match"
    assert article["embedding"] is None, "Embedding should be NULL"


# ============================================================================
# Property 15: Seed Script Active Flag
# ============================================================================


# Feature: supabase-migration-phase1, Property 15: Seed Script Active Flag
def test_property_15_seed_script_active_flag(test_supabase_client, cleanup_test_data):
    """
    Property 15: Seed Script Active Flag

    For any feed inserted by the seed script, the is_active field should
    be set to true.

    **Validates: Requirements 4.7**

    Note: This test simulates seed script behavior by inserting feeds
    with is_active=true and verifying the default behavior.
    """
    # Simulate seed script insertion
    unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"
    feed_result = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": "Seed Feed",
                "url": unique_feed_url,
                "category": "Test",
                "is_active": True,  # Seed script explicitly sets this
            }
        )
        .execute()
    )
    feed = feed_result.data[0]
    cleanup_test_data["feeds"].append(feed["id"])

    # Verify is_active is true
    assert feed["is_active"] is True, "Seed script should set is_active to true"

    # Also test default behavior (when is_active is not provided)
    unique_feed_url2 = f"https://feed-{os.urandom(4).hex()}.com/rss"
    feed_result2 = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": "Default Feed",
                "url": unique_feed_url2,
                "category": "Test",
                # is_active not provided, should default to true
            }
        )
        .execute()
    )
    feed2 = feed_result2.data[0]
    cleanup_test_data["feeds"].append(feed2["id"])

    # Verify default is_active is true
    assert feed2["is_active"] is True, "Default is_active should be true"


# ============================================================================
# Property 16: Seed Script Duplicate Handling
# ============================================================================


# Feature: supabase-migration-phase1, Property 16: Seed Script Duplicate Handling
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(feed_url=safe_text(min_size=1, max_size=50))
def test_property_16_seed_script_duplicate_handling(
    test_supabase_client, cleanup_test_data, feed_url
):
    """
    Property 16: Seed Script Duplicate Handling

    For any feed URL that already exists in the database, when the seed
    script attempts to insert it, the script should skip that feed and
    continue processing remaining feeds without crashing.

    **Validates: Requirements 4.8**

    Note: This test simulates seed script behavior by attempting to insert
    duplicate feeds and verifying proper error handling.
    """
    # Create unique feed URL
    unique_feed_url = f"https://{os.urandom(4).hex()}-{feed_url.replace('://', '-')}.com/rss"

    # Insert first feed (should succeed)
    feed1_result = (
        test_supabase_client.table("feeds")
        .insert(
            {"name": "Original Feed", "url": unique_feed_url, "category": "Test", "is_active": True}
        )
        .execute()
    )
    feed1 = feed1_result.data[0]
    cleanup_test_data["feeds"].append(feed1["id"])

    # Simulate seed script attempting to insert duplicate (should fail gracefully)
    try:
        test_supabase_client.table("feeds").insert(
            {
                "name": "Duplicate Feed",
                "url": unique_feed_url,
                "category": "Test",
                "is_active": True,
            }
        ).execute()
        # If no exception, fail the test
        pytest.fail("Should have raised exception for duplicate URL")
    except Exception as e:
        # Verify it's a duplicate key error
        error_message = str(e).lower()
        assert (
            "duplicate" in error_message or "unique" in error_message
        ), "Should raise duplicate key error"

        # Seed script should catch this and continue
        # Verify original feed still exists
        feed_check = test_supabase_client.table("feeds").select("*").eq("id", feed1["id"]).execute()
        assert len(feed_check.data) == 1, "Original feed should still exist"

        # Verify only one feed with this URL exists
        url_check = (
            test_supabase_client.table("feeds").select("*").eq("url", unique_feed_url).execute()
        )
        assert len(url_check.data) == 1, "Only one feed should exist with this URL"


# ============================================================================
# Property 17: Updated Timestamp Trigger
# ============================================================================


# Feature: supabase-migration-phase1, Property 17: Updated Timestamp Trigger
@settings(
    max_examples=5,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
)
@given(
    initial_status=st.sampled_from(["Unread", "Read", "Archived"]),
    updated_status=st.sampled_from(["Unread", "Read", "Archived"]),
)
def test_property_17_updated_timestamp_trigger(
    test_supabase_client, cleanup_test_data, initial_status, updated_status
):
    """
    Property 17: Updated Timestamp Trigger

    For any reading_list record that is modified (UPDATE operation), the
    updated_at timestamp should be automatically updated to the current time.

    **Validates: Requirements 8.8**
    """
    # Ensure statuses are different to trigger an actual update
    assume(initial_status != updated_status)

    # Create user, feed, and article first
    unique_discord_id = f"test_user_{os.urandom(4).hex()}"
    user_result = (
        test_supabase_client.table("users").insert({"discord_id": unique_discord_id}).execute()
    )
    user = user_result.data[0]
    cleanup_test_data["users"].append(user["id"])

    unique_feed_url = f"https://feed-{os.urandom(4).hex()}.com/rss"
    feed_result = (
        test_supabase_client.table("feeds")
        .insert({"name": "Test Feed", "url": unique_feed_url, "category": "Test"})
        .execute()
    )
    feed = feed_result.data[0]
    cleanup_test_data["feeds"].append(feed["id"])

    unique_article_url = f"https://article-{os.urandom(4).hex()}.com"
    article_result = (
        test_supabase_client.table("articles")
        .insert({"feed_id": feed["id"], "title": "Test Article", "url": unique_article_url})
        .execute()
    )
    article = article_result.data[0]
    cleanup_test_data["articles"].append(article["id"])

    # Create reading list entry with initial status
    entry_result = (
        test_supabase_client.table("reading_list")
        .insert({"user_id": user["id"], "article_id": article["id"], "status": initial_status})
        .execute()
    )
    entry = entry_result.data[0]
    cleanup_test_data["reading_list"].append(entry["id"])

    # Record initial updated_at timestamp
    initial_updated_at = datetime.fromisoformat(entry["updated_at"].replace("Z", "+00:00"))

    # Wait a moment to ensure timestamp difference
    time.sleep(0.1)

    # Update the reading list entry
    update_result = (
        test_supabase_client.table("reading_list")
        .update({"status": updated_status})
        .eq("id", entry["id"])
        .execute()
    )
    updated_entry = update_result.data[0]

    # Verify updated_at was automatically updated
    new_updated_at = datetime.fromisoformat(updated_entry["updated_at"].replace("Z", "+00:00"))

    assert (
        new_updated_at > initial_updated_at
    ), "updated_at should be automatically updated to a later timestamp"
    assert updated_entry["status"] == updated_status, "Status should be updated to new value"
