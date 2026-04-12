"""
Property-based tests for SupabaseService CRUD operations
Tasks 6.2, 7.2, 8.3, 9.2, 9.4, 9.6, 10.2, 10.4, 12.2, 12.4, 12.6

This module tests the correctness properties of all CRUD operations:
- User management (get_or_create_user)
- Feed queries (get_active_feeds)
- Article batch insert (insert_articles)
- Reading list management (save, update status, update rating)
- Reading list queries (get_reading_list, get_highly_rated_articles)
- Subscription management (subscribe, unsubscribe, get_user_subscriptions)
"""

from uuid import UUID, uuid4

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite

from app.services.supabase_service import SupabaseService

# Custom strategies for generating test data


@composite
def discord_ids(draw):
    """Generate valid Discord IDs (ASCII printable characters only to avoid UTF-8 encoding issues)"""
    # Use ASCII printable characters (32-126) to avoid Unicode surrogate pairs
    text_part = draw(
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(
                min_codepoint=32, max_codepoint=126, blacklist_characters="\x00\n\r"
            ),
        )
    )
    return f"discord_{text_part}"


@composite
def valid_urls(draw):
    """Generate valid HTTP/HTTPS URLs"""
    protocol = draw(st.sampled_from(["http", "https"]))
    domain = draw(st.text(min_size=3, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"))
    tld = draw(st.sampled_from(["com", "org", "net", "io"]))
    path = draw(
        st.text(min_size=0, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_/")
    )
    return f"{protocol}://{domain}.{tld}/{path}"


@composite
def valid_articles(draw, feed_id=None):
    """Generate valid article data"""
    if feed_id is None:
        feed_id = str(uuid4())

    return {
        "title": draw(
            st.text(
                min_size=1,
                max_size=200,
                alphabet=st.characters(
                    min_codepoint=32, max_codepoint=126, blacklist_characters="\x00"
                ),
            )
        ),
        "url": draw(valid_urls()),
        "feed_id": feed_id,
        "feed_name": draw(
            st.text(
                min_size=1,
                max_size=50,
                alphabet=st.characters(
                    min_codepoint=32, max_codepoint=126, blacklist_characters="\x00"
                ),
            )
        ),
        "category": draw(st.sampled_from(["Tech", "AI", "Programming", "DevOps"])),
        "tinkering_index": draw(st.one_of(st.none(), st.integers(min_value=1, max_value=5))),
        "ai_summary": draw(
            st.one_of(
                st.none(),
                st.text(
                    max_size=500,
                    alphabet=st.characters(
                        min_codepoint=32, max_codepoint=126, blacklist_characters="\x00"
                    ),
                ),
            )
        ),
    }


@composite
def ratings(draw):
    """Generate valid ratings (1-5)"""
    return draw(st.integers(min_value=1, max_value=5))


@composite
def statuses(draw):
    """Generate valid statuses with various cases"""
    return draw(st.sampled_from(["Unread", "Read", "Archived", "unread", "READ", "archived"]))


# Property 2: User Creation Idempotency
# Feature: data-access-layer-refactor, Property 2: User Creation Idempotency
@settings(
    max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@given(discord_id=discord_ids())
@pytest.mark.asyncio
async def test_user_creation_idempotency(test_supabase_client, cleanup_test_data, discord_id):
    """
    **Validates: Requirements 3.2, 3.3, 3.4**

    For any discord_id, calling get_or_create_user multiple times
    should always return the same UUID without creating duplicate user records.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    # First call
    uuid1 = await service.get_or_create_user(discord_id)
    assert isinstance(uuid1, UUID)
    cleanup_test_data["users"].append(str(uuid1))

    # Second call
    uuid2 = await service.get_or_create_user(discord_id)
    assert isinstance(uuid2, UUID)

    # Should return the same UUID
    assert uuid1 == uuid2

    # Verify only one record in database
    users = test_supabase_client.table("users").select("*").eq("discord_id", discord_id).execute()
    assert len(users.data) == 1


# Property 3: Active Feeds Filtering
# Feature: data-access-layer-refactor, Property 3: Active Feeds Filtering
@pytest.mark.asyncio
async def test_active_feeds_filtering(test_supabase_client, cleanup_test_data):
    """
    **Validates: Requirements 4.2, 4.3**

    For any database state containing both active and inactive feeds,
    get_active_feeds should return only feeds where is_active is true.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    # Create active and inactive feeds
    active_feed = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": "Active Feed",
                "url": f"https://active-{uuid4()}.com/rss",
                "category": "Tech",
                "is_active": True,
            }
        )
        .execute()
        .data[0]
    )
    cleanup_test_data["feeds"].append(active_feed["id"])

    inactive_feed = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": "Inactive Feed",
                "url": f"https://inactive-{uuid4()}.com/rss",
                "category": "Tech",
                "is_active": False,
            }
        )
        .execute()
        .data[0]
    )
    cleanup_test_data["feeds"].append(inactive_feed["id"])

    # Get active feeds
    feeds = await service.get_active_feeds()

    # Should only return active feeds
    feed_urls = [feed.url for feed in feeds]
    assert active_feed["url"] in [str(url) for url in feed_urls]
    assert inactive_feed["url"] not in [str(url) for url in feed_urls]


# Property 4: Active Feeds Ordering
# Feature: data-access-layer-refactor, Property 4: Active Feeds Ordering
@pytest.mark.asyncio
async def test_active_feeds_ordering(test_supabase_client, cleanup_test_data):
    """
    **Validates: Requirements 4.4**

    For any result set from get_active_feeds, the results should be
    ordered first by category, then by name within each category.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    # Create feeds with different categories and names
    feeds_data = [
        {"name": "B Feed", "category": "AI", "url": f"https://b-ai-{uuid4()}.com/rss"},
        {"name": "A Feed", "category": "AI", "url": f"https://a-ai-{uuid4()}.com/rss"},
        {"name": "C Feed", "category": "Tech", "url": f"https://c-tech-{uuid4()}.com/rss"},
        {"name": "A Feed", "category": "Tech", "url": f"https://a-tech-{uuid4()}.com/rss"},
    ]

    for feed_data in feeds_data:
        feed = (
            test_supabase_client.table("feeds")
            .insert({**feed_data, "is_active": True})
            .execute()
            .data[0]
        )
        cleanup_test_data["feeds"].append(feed["id"])

    # Get active feeds
    feeds = await service.get_active_feeds()

    # Extract categories and names
    feed_tuples = [(feed.category, feed.name) for feed in feeds if feed.category in ["AI", "Tech"]]

    # Verify ordering
    assert feed_tuples == sorted(feed_tuples)


# Property 5: Article UPSERT Idempotency
# Feature: data-access-layer-refactor, Property 5: Article UPSERT Idempotency
@settings(
    max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@given(article_data=valid_articles())
@pytest.mark.asyncio
async def test_article_upsert_idempotency(
    test_supabase_client, test_feed, cleanup_test_data, article_data
):
    """
    **Validates: Requirements 5.2, 5.3, 5.4**

    For any article data, inserting it multiple times based on URL
    should result in only one article record in the database.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    # Use test_feed's ID
    article_data["feed_id"] = test_feed["id"]

    # Clean up any existing article with this URL before testing
    existing = (
        test_supabase_client.table("articles").select("id").eq("url", article_data["url"]).execute()
    )
    for article in existing.data:
        test_supabase_client.table("articles").delete().eq("id", article["id"]).execute()

    # First insert
    result1 = await service.insert_articles([article_data])
    assert result1.inserted_count == 1

    # Modify title and insert again with same URL
    article_updated = {**article_data, "title": "Updated Title"}
    result2 = await service.insert_articles([article_updated])
    assert result2.updated_count == 1
    assert result2.inserted_count == 0

    # Verify only one record in database
    articles = (
        test_supabase_client.table("articles").select("*").eq("url", article_data["url"]).execute()
    )
    assert len(articles.data) == 1
    assert articles.data[0]["title"] == "Updated Title"

    # Track for cleanup
    cleanup_test_data["articles"].append(articles.data[0]["id"])


# Property 7: Batch Operation Statistics Accuracy
# Feature: data-access-layer-refactor, Property 7: Batch Operation Statistics Accuracy
@pytest.mark.asyncio
async def test_batch_operation_statistics_accuracy(
    test_supabase_client, test_feed, cleanup_test_data
):
    """
    **Validates: Requirements 5.7, 15.4**

    For any batch of articles processed by insert_articles, the returned
    BatchResult counts should accurately reflect the actual database operations.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    # Create articles with some valid and some invalid
    articles = [
        {
            "title": "Valid Article 1",
            "url": f"https://valid1-{uuid4()}.com",
            "feed_id": test_feed["id"],
            "feed_name": "Test Feed",
            "category": "Tech",
        },
        {
            "title": "Valid Article 2",
            "url": f"https://valid2-{uuid4()}.com",
            "feed_id": test_feed["id"],
            "feed_name": "Test Feed",
            "category": "Tech",
        },
        {
            "title": "Invalid Article",
            "url": "not-a-valid-url",  # Invalid URL
            "feed_id": test_feed["id"],
            "feed_name": "Test Feed",
            "category": "Tech",
        },
    ]

    result = await service.insert_articles(articles)

    # Verify statistics
    assert result.inserted_count == 2
    assert result.failed_count == 1
    assert result.total_processed == 3
    assert len(result.failed_articles) == 1

    # Track for cleanup
    for article in articles[:2]:
        articles_in_db = (
            test_supabase_client.table("articles").select("id").eq("url", article["url"]).execute()
        )
        if articles_in_db.data:
            cleanup_test_data["articles"].append(articles_in_db.data[0]["id"])


# Property 8: Reading List UPSERT Idempotency
# Feature: data-access-layer-refactor, Property 8: Reading List UPSERT Idempotency
@settings(
    max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@given(discord_id=discord_ids())
@pytest.mark.asyncio
async def test_reading_list_upsert_idempotency(
    test_supabase_client, test_article, cleanup_test_data, discord_id
):
    """
    **Validates: Requirements 6.3, 6.4**

    For any user and article combination, calling save_to_reading_list
    multiple times should not create duplicate entries.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    article_id = UUID(test_article["id"])

    # First save
    await service.save_to_reading_list(discord_id, article_id)

    # Second save
    await service.save_to_reading_list(discord_id, article_id)

    # Get user UUID for verification
    user_uuid = await service.get_or_create_user(discord_id)
    cleanup_test_data["users"].append(str(user_uuid))

    # Verify only one entry
    entries = (
        test_supabase_client.table("reading_list")
        .select("*")
        .eq("user_id", str(user_uuid))
        .eq("article_id", str(article_id))
        .execute()
    )

    assert len(entries.data) == 1
    cleanup_test_data["reading_list"].append(entries.data[0]["id"])


# Property 9: Reading List Initial Status
# Feature: data-access-layer-refactor, Property 9: Reading List Initial Status
@settings(
    max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@given(discord_id=discord_ids())
@pytest.mark.asyncio
async def test_reading_list_initial_status(
    test_supabase_client, test_article, cleanup_test_data, discord_id
):
    """
    **Validates: Requirements 6.5**

    For any new reading list entry created by save_to_reading_list,
    the initial status should be 'Unread'.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    article_id = UUID(test_article["id"])

    # Save to reading list
    await service.save_to_reading_list(discord_id, article_id)

    # Get user UUID
    user_uuid = await service.get_or_create_user(discord_id)
    cleanup_test_data["users"].append(str(user_uuid))

    # Verify initial status
    entry = (
        test_supabase_client.table("reading_list")
        .select("*")
        .eq("user_id", str(user_uuid))
        .eq("article_id", str(article_id))
        .execute()
    )

    assert len(entry.data) == 1
    assert entry.data[0]["status"] == "Unread"
    cleanup_test_data["reading_list"].append(entry.data[0]["id"])


# Property 11: Status Validation (already tested in test_validation_helpers_property.py)
# Property 12: Status Update Persistence
# Feature: data-access-layer-refactor, Property 12: Status Update Persistence
@settings(
    max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@given(discord_id=discord_ids(), status=statuses())
@pytest.mark.asyncio
async def test_status_update_persistence(
    test_supabase_client, test_article, cleanup_test_data, discord_id, status
):
    """
    **Validates: Requirements 7.5, 7.6**

    For any valid status update via update_article_status, the database
    should reflect the new status value, and updated_at should be updated.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    article_id = UUID(test_article["id"])

    # Save to reading list first
    await service.save_to_reading_list(discord_id, article_id)

    # Get initial updated_at
    user_uuid = await service.get_or_create_user(discord_id)
    cleanup_test_data["users"].append(str(user_uuid))

    initial_entry = (
        test_supabase_client.table("reading_list")
        .select("updated_at")
        .eq("user_id", str(user_uuid))
        .eq("article_id", str(article_id))
        .execute()
    )

    initial_updated_at = initial_entry.data[0]["updated_at"]

    # Small delay to ensure timestamp difference
    import asyncio

    await asyncio.sleep(0.1)

    # Update status
    await service.update_article_status(discord_id, article_id, status)

    # Verify status and updated_at
    updated_entry = (
        test_supabase_client.table("reading_list")
        .select("*")
        .eq("user_id", str(user_uuid))
        .eq("article_id", str(article_id))
        .execute()
    )

    assert updated_entry.data[0]["status"] == status.strip().title()
    assert updated_entry.data[0]["updated_at"] >= initial_updated_at
    cleanup_test_data["reading_list"].append(updated_entry.data[0]["id"])


# Property 13: Rating Validation (already tested in test_validation_helpers_property.py)
# Property 14: Rating Update Persistence
# Feature: data-access-layer-refactor, Property 14: Rating Update Persistence
@settings(
    max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@given(discord_id=discord_ids(), rating=ratings())
@pytest.mark.asyncio
async def test_rating_update_persistence(
    test_supabase_client, test_article, cleanup_test_data, discord_id, rating
):
    """
    **Validates: Requirements 8.5, 8.6**

    For any valid rating update via update_article_rating, the database
    should reflect the new rating value, and updated_at should be updated.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    article_id = UUID(test_article["id"])

    # Save to reading list first
    await service.save_to_reading_list(discord_id, article_id)

    # Get initial updated_at
    user_uuid = await service.get_or_create_user(discord_id)
    cleanup_test_data["users"].append(str(user_uuid))

    initial_entry = (
        test_supabase_client.table("reading_list")
        .select("updated_at")
        .eq("user_id", str(user_uuid))
        .eq("article_id", str(article_id))
        .execute()
    )

    initial_updated_at = initial_entry.data[0]["updated_at"]

    # Small delay to ensure timestamp difference
    import asyncio

    await asyncio.sleep(0.1)

    # Update rating
    await service.update_article_rating(discord_id, article_id, rating)

    # Verify rating and updated_at
    updated_entry = (
        test_supabase_client.table("reading_list")
        .select("*")
        .eq("user_id", str(user_uuid))
        .eq("article_id", str(article_id))
        .execute()
    )

    assert updated_entry.data[0]["rating"] == rating
    assert updated_entry.data[0]["updated_at"] >= initial_updated_at
    cleanup_test_data["reading_list"].append(updated_entry.data[0]["id"])


# Property 15: Reading List Status Filtering
# Feature: data-access-layer-refactor, Property 15: Reading List Status Filtering
@pytest.mark.asyncio
async def test_reading_list_status_filtering(test_supabase_client, test_user, cleanup_test_data):
    """
    **Validates: Requirements 9.3**

    For any status filter provided to get_reading_list,
    all returned articles should have exactly that status value.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    discord_id = f"test_{uuid4()}"
    user_uuid = await service.get_or_create_user(discord_id)
    cleanup_test_data["users"].append(str(user_uuid))

    # Create test feed and articles with different statuses
    feed = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": "Test Feed",
                "url": f"https://test-{uuid4()}.com/rss",
                "category": "Tech",
                "is_active": True,
            }
        )
        .execute()
        .data[0]
    )
    cleanup_test_data["feeds"].append(feed["id"])

    statuses_to_test = ["Unread", "Read", "Archived"]
    for status in statuses_to_test:
        article = (
            test_supabase_client.table("articles")
            .insert(
                {
                    "feed_id": feed["id"],
                    "title": f"Article {status}",
                    "url": f"https://article-{status}-{uuid4()}.com",
                }
            )
            .execute()
            .data[0]
        )
        cleanup_test_data["articles"].append(article["id"])

        entry = (
            test_supabase_client.table("reading_list")
            .insert({"user_id": str(user_uuid), "article_id": article["id"], "status": status})
            .execute()
            .data[0]
        )
        cleanup_test_data["reading_list"].append(entry["id"])

    # Test filtering for each status
    for filter_status in statuses_to_test:
        results = await service.get_reading_list(discord_id, status=filter_status)
        assert all(item.status == filter_status for item in results)
        assert len(results) == 1


# Property 16: Reading List Complete Retrieval
# Feature: data-access-layer-refactor, Property 16: Reading List Complete Retrieval
@pytest.mark.asyncio
async def test_reading_list_complete_retrieval(test_supabase_client, cleanup_test_data):
    """
    **Validates: Requirements 9.4**

    For any user's reading list, calling get_reading_list without a status
    filter should return articles of all statuses.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    discord_id = f"test_{uuid4()}"
    user_uuid = await service.get_or_create_user(discord_id)
    cleanup_test_data["users"].append(str(user_uuid))

    # Create test feed and articles with different statuses
    feed = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": "Test Feed",
                "url": f"https://test-{uuid4()}.com/rss",
                "category": "Tech",
                "is_active": True,
            }
        )
        .execute()
        .data[0]
    )
    cleanup_test_data["feeds"].append(feed["id"])

    statuses = ["Unread", "Read", "Archived"]
    for status in statuses:
        article = (
            test_supabase_client.table("articles")
            .insert(
                {
                    "feed_id": feed["id"],
                    "title": f"Article {status}",
                    "url": f"https://article-{status}-{uuid4()}.com",
                }
            )
            .execute()
            .data[0]
        )
        cleanup_test_data["articles"].append(article["id"])

        entry = (
            test_supabase_client.table("reading_list")
            .insert({"user_id": str(user_uuid), "article_id": article["id"], "status": status})
            .execute()
            .data[0]
        )
        cleanup_test_data["reading_list"].append(entry["id"])

    # Get all articles without filter
    results = await service.get_reading_list(discord_id)

    # Should return all statuses
    result_statuses = {item.status for item in results}
    assert result_statuses == set(statuses)
    assert len(results) == 3


# Property 18: Reading List Ordering
# Feature: data-access-layer-refactor, Property 18: Reading List Ordering
@pytest.mark.asyncio
async def test_reading_list_ordering(test_supabase_client, cleanup_test_data):
    """
    **Validates: Requirements 9.6**

    For any result set from get_reading_list, the results should be
    ordered by added_at in descending order (newest first).
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    discord_id = f"test_{uuid4()}"
    user_uuid = await service.get_or_create_user(discord_id)
    cleanup_test_data["users"].append(str(user_uuid))

    # Create test feed
    feed = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": "Test Feed",
                "url": f"https://test-{uuid4()}.com/rss",
                "category": "Tech",
                "is_active": True,
            }
        )
        .execute()
        .data[0]
    )
    cleanup_test_data["feeds"].append(feed["id"])

    # Create multiple articles with delays to ensure different timestamps
    import asyncio

    for i in range(3):
        article = (
            test_supabase_client.table("articles")
            .insert(
                {
                    "feed_id": feed["id"],
                    "title": f"Article {i}",
                    "url": f"https://article-{i}-{uuid4()}.com",
                }
            )
            .execute()
            .data[0]
        )
        cleanup_test_data["articles"].append(article["id"])

        entry = (
            test_supabase_client.table("reading_list")
            .insert({"user_id": str(user_uuid), "article_id": article["id"], "status": "Unread"})
            .execute()
            .data[0]
        )
        cleanup_test_data["reading_list"].append(entry["id"])

        await asyncio.sleep(0.1)  # Small delay to ensure different timestamps

    # Get reading list
    results = await service.get_reading_list(discord_id)

    # Verify descending order
    added_at_list = [item.added_at for item in results]
    assert added_at_list == sorted(added_at_list, reverse=True)


# Property 19: Highly Rated Articles Threshold
# Feature: data-access-layer-refactor, Property 19: Highly Rated Articles Threshold
@pytest.mark.asyncio
async def test_highly_rated_articles_threshold(test_supabase_client, cleanup_test_data):
    """
    **Validates: Requirements 10.4, 10.5**

    For any threshold value, get_highly_rated_articles should return only
    articles with rating greater than or equal to that threshold.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    discord_id = f"test_{uuid4()}"
    user_uuid = await service.get_or_create_user(discord_id)
    cleanup_test_data["users"].append(str(user_uuid))

    # Create test feed
    feed = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": "Test Feed",
                "url": f"https://test-{uuid4()}.com/rss",
                "category": "Tech",
                "is_active": True,
            }
        )
        .execute()
        .data[0]
    )
    cleanup_test_data["feeds"].append(feed["id"])

    # Create articles with different ratings
    ratings = [1, 3, 4, 5]
    for rating in ratings:
        article = (
            test_supabase_client.table("articles")
            .insert(
                {
                    "feed_id": feed["id"],
                    "title": f"Article Rating {rating}",
                    "url": f"https://article-rating-{rating}-{uuid4()}.com",
                }
            )
            .execute()
            .data[0]
        )
        cleanup_test_data["articles"].append(article["id"])

        entry = (
            test_supabase_client.table("reading_list")
            .insert(
                {
                    "user_id": str(user_uuid),
                    "article_id": article["id"],
                    "status": "Read",
                    "rating": rating,
                }
            )
            .execute()
            .data[0]
        )
        cleanup_test_data["reading_list"].append(entry["id"])

    # Test with threshold 4
    results = await service.get_highly_rated_articles(discord_id, threshold=4)

    # Should only return articles with rating >= 4
    assert all(item.rating >= 4 for item in results)
    assert len(results) == 2  # ratings 4 and 5


# Property 20: Highly Rated Articles Ordering
# Feature: data-access-layer-refactor, Property 20: Highly Rated Articles Ordering
@pytest.mark.asyncio
async def test_highly_rated_articles_ordering(test_supabase_client, cleanup_test_data):
    """
    **Validates: Requirements 10.6**

    For any result set from get_highly_rated_articles, the results should be
    ordered first by rating descending, then by added_at descending.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    discord_id = f"test_{uuid4()}"
    user_uuid = await service.get_or_create_user(discord_id)
    cleanup_test_data["users"].append(str(user_uuid))

    # Create test feed
    feed = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": "Test Feed",
                "url": f"https://test-{uuid4()}.com/rss",
                "category": "Tech",
                "is_active": True,
            }
        )
        .execute()
        .data[0]
    )
    cleanup_test_data["feeds"].append(feed["id"])

    # Create articles with ratings in non-sorted order
    import asyncio

    test_data = [(4, "A"), (5, "B"), (4, "C"), (5, "D")]
    for rating, suffix in test_data:
        article = (
            test_supabase_client.table("articles")
            .insert(
                {
                    "feed_id": feed["id"],
                    "title": f"Article {suffix}",
                    "url": f"https://article-{suffix}-{uuid4()}.com",
                }
            )
            .execute()
            .data[0]
        )
        cleanup_test_data["articles"].append(article["id"])

        entry = (
            test_supabase_client.table("reading_list")
            .insert(
                {
                    "user_id": str(user_uuid),
                    "article_id": article["id"],
                    "status": "Read",
                    "rating": rating,
                }
            )
            .execute()
            .data[0]
        )
        cleanup_test_data["reading_list"].append(entry["id"])

        await asyncio.sleep(0.1)

    # Get highly rated articles
    results = await service.get_highly_rated_articles(discord_id, threshold=4)

    # Verify ordering: first by rating desc, then by added_at desc
    for i in range(len(results) - 1):
        if results[i].rating == results[i + 1].rating:
            # Same rating, check added_at descending
            assert results[i].added_at >= results[i + 1].added_at
        else:
            # Different rating, check rating descending
            assert results[i].rating > results[i + 1].rating


# Property 21: Subscription Idempotency
# Feature: data-access-layer-refactor, Property 21: Subscription Idempotency
@settings(
    max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@given(discord_id=discord_ids())
@pytest.mark.asyncio
async def test_subscription_idempotency(
    test_supabase_client, test_feed, cleanup_test_data, discord_id
):
    """
    **Validates: Requirements 11.3, 11.4**

    For any user and feed combination, calling subscribe_to_feed multiple
    times should not create duplicate subscription records.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    feed_id = UUID(test_feed["id"])

    # First subscription
    await service.subscribe_to_feed(discord_id, feed_id)

    # Second subscription
    await service.subscribe_to_feed(discord_id, feed_id)

    # Get user UUID
    user_uuid = await service.get_or_create_user(discord_id)
    cleanup_test_data["users"].append(str(user_uuid))

    # Verify only one subscription
    subscriptions = (
        test_supabase_client.table("user_subscriptions")
        .select("*")
        .eq("user_id", str(user_uuid))
        .eq("feed_id", str(feed_id))
        .execute()
    )

    assert len(subscriptions.data) == 1
    cleanup_test_data["subscriptions"].append(subscriptions.data[0]["id"])


# Property 22: Unsubscription Idempotency
# Feature: data-access-layer-refactor, Property 22: Unsubscription Idempotency
@settings(
    max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@given(discord_id=discord_ids())
@pytest.mark.asyncio
async def test_unsubscription_idempotency(
    test_supabase_client, test_feed, cleanup_test_data, discord_id
):
    """
    **Validates: Requirements 11.7, 11.8**

    For any user and feed combination, calling unsubscribe_from_feed should
    remove the subscription if it exists, and should complete without error
    if the subscription does not exist.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    feed_id = UUID(test_feed["id"])

    # Subscribe first
    await service.subscribe_to_feed(discord_id, feed_id)

    # Get user UUID
    user_uuid = await service.get_or_create_user(discord_id)
    cleanup_test_data["users"].append(str(user_uuid))

    # First unsubscribe
    await service.unsubscribe_from_feed(discord_id, feed_id)

    # Verify subscription removed
    subscriptions = (
        test_supabase_client.table("user_subscriptions")
        .select("*")
        .eq("user_id", str(user_uuid))
        .eq("feed_id", str(feed_id))
        .execute()
    )

    assert len(subscriptions.data) == 0

    # Second unsubscribe (should not raise error)
    await service.unsubscribe_from_feed(discord_id, feed_id)


# Property 24: User Subscriptions Ordering
# Feature: data-access-layer-refactor, Property 24: User Subscriptions Ordering
@pytest.mark.asyncio
async def test_user_subscriptions_ordering(test_supabase_client, cleanup_test_data):
    """
    **Validates: Requirements 12.4**

    For any result set from get_user_subscriptions, the results should be
    ordered by subscribed_at in descending order (newest first).
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    discord_id = f"test_{uuid4()}"
    user_uuid = await service.get_or_create_user(discord_id)
    cleanup_test_data["users"].append(str(user_uuid))

    # Create multiple feeds and subscribe with delays
    import asyncio

    for i in range(3):
        feed = (
            test_supabase_client.table("feeds")
            .insert(
                {
                    "name": f"Feed {i}",
                    "url": f"https://feed-{i}-{uuid4()}.com/rss",
                    "category": "Tech",
                    "is_active": True,
                }
            )
            .execute()
            .data[0]
        )
        cleanup_test_data["feeds"].append(feed["id"])

        await service.subscribe_to_feed(discord_id, UUID(feed["id"]))
        await asyncio.sleep(0.1)

    # Get subscriptions
    subscriptions = await service.get_user_subscriptions(discord_id)

    # Verify descending order
    subscribed_at_list = [sub.subscribed_at for sub in subscriptions]
    assert subscribed_at_list == sorted(subscribed_at_list, reverse=True)

    # Track subscriptions for cleanup
    for sub in subscriptions:
        subs_in_db = (
            test_supabase_client.table("user_subscriptions")
            .select("id")
            .eq("user_id", str(user_uuid))
            .eq("feed_id", str(sub.feed_id))
            .execute()
        )
        if subs_in_db.data:
            cleanup_test_data["subscriptions"].append(subs_in_db.data[0]["id"])
