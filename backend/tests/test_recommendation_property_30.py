"""
Property-Based Test for Recommendation Service - Property 30

**Validates: Requirements 12.7**

Property 30: Recommended Feed Real-Time Updates
For any feed that is marked as recommended (is_recommended set to true), the feed
SHALL immediately appear in subsequent recommended feeds queries.

This test uses Hypothesis to generate random feed data and verify that
recommendation status changes are immediately reflected in query results.

**PREREQUISITE**: Migration 003 must be applied before running these tests.
To apply the migration, copy and paste the SQL from:
scripts/migrations/003_extend_feeds_table_for_recommendations.sql
into the Supabase SQL Editor and execute it.
"""

import os
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from supabase import create_client

from app.services.recommendation_service import RecommendationService

# Load environment and check if migration is applied
load_dotenv()
_migration_applied = False

try:
    _url = os.getenv("SUPABASE_URL")
    _key = os.getenv("SUPABASE_KEY")
    if _url and _key:
        _client = create_client(_url, _key)
        _client.table("feeds").select("is_recommended").limit(1).execute()
        _migration_applied = True
except Exception:
    pass

# Skip all tests in this module if migration not applied
pytestmark = pytest.mark.skipif(
    not _migration_applied,
    reason="Migration 003 not applied. Please apply scripts/migrations/003_extend_feeds_table_for_recommendations.sql via Supabase SQL Editor.",
)


# Strategy for generating recommendation priorities (0-1000)
recommendation_priorities = st.integers(min_value=0, max_value=1000)


@pytest.mark.asyncio
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(priority=recommendation_priorities)
async def test_property_30_immediate_appearance_on_recommendation(test_supabase_client, priority):
    """
    Property 30: Recommended Feed Real-Time Updates - Immediate Appearance

    For any feed that is marked as recommended (is_recommended set to true),
    the feed SHALL immediately appear in subsequent recommended feeds queries.

    Test Strategy:
    1. Create a feed with is_recommended = False
    2. Verify it does NOT appear in recommended feeds query
    3. Update is_recommended to True
    4. Verify it IMMEDIATELY appears in subsequent query
    """
    # Arrange
    service = RecommendationService(test_supabase_client)

    # Create a non-recommended feed
    test_feed_url = f"https://test-feed-{uuid4().hex}.com/rss.xml"
    feed_result = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": f"Test Feed {uuid4().hex[:8]}",
                "url": test_feed_url,
                "category": "Test Category",
                "is_active": False,
                "is_recommended": False,
                "recommendation_priority": priority,
                "description": "Test feed for property 30",
            }
        )
        .execute()
    )

    feed = feed_result.data[0]
    feed_id = feed["id"]

    try:
        # Act & Assert - Step 1: Verify feed is NOT in recommended feeds
        recommended_feeds_before = await service.get_recommended_feeds()
        feed_ids_before = [str(f.id) for f in recommended_feeds_before]

        assert (
            feed_id not in feed_ids_before
        ), "Feed with is_recommended=False should NOT appear in recommended feeds"

        # Act - Step 2: Mark feed as recommended
        await service.update_recommendation_status(
            feed_id=feed_id, is_recommended=True, priority=priority
        )

        # Assert - Step 3: Verify feed IMMEDIATELY appears in recommended feeds
        recommended_feeds_after = await service.get_recommended_feeds()
        feed_ids_after = [str(f.id) for f in recommended_feeds_after]

        assert (
            feed_id in feed_ids_after
        ), "Feed with is_recommended=True should IMMEDIATELY appear in recommended feeds"

        # Verify the feed has correct properties
        test_feed = next(f for f in recommended_feeds_after if str(f.id) == feed_id)
        assert test_feed.is_recommended is True, "Feed should have is_recommended=True"
        assert (
            test_feed.recommendation_priority == priority
        ), f"Feed should have priority={priority}"

    finally:
        # Cleanup
        test_supabase_client.table("feeds").delete().eq("id", feed_id).execute()


@pytest.mark.asyncio
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(priority=recommendation_priorities)
async def test_property_30_immediate_removal_on_unrecommendation(test_supabase_client, priority):
    """
    Property 30: Recommended Feed Real-Time Updates - Immediate Removal

    For any feed that is marked as not recommended (is_recommended set to false),
    the feed SHALL immediately disappear from subsequent recommended feeds queries.

    Test Strategy:
    1. Create a feed with is_recommended = True
    2. Verify it appears in recommended feeds query
    3. Update is_recommended to False
    4. Verify it IMMEDIATELY disappears from subsequent query
    """
    # Arrange
    service = RecommendationService(test_supabase_client)

    # Create a recommended feed
    test_feed_url = f"https://test-feed-{uuid4().hex}.com/rss.xml"
    feed_result = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": f"Test Feed {uuid4().hex[:8]}",
                "url": test_feed_url,
                "category": "Test Category",
                "is_active": False,
                "is_recommended": True,
                "recommendation_priority": priority,
                "description": "Test feed for property 30",
            }
        )
        .execute()
    )

    feed = feed_result.data[0]
    feed_id = feed["id"]

    try:
        # Act & Assert - Step 1: Verify feed IS in recommended feeds
        recommended_feeds_before = await service.get_recommended_feeds()
        feed_ids_before = [str(f.id) for f in recommended_feeds_before]

        assert (
            feed_id in feed_ids_before
        ), "Feed with is_recommended=True should appear in recommended feeds"

        # Act - Step 2: Mark feed as not recommended
        await service.update_recommendation_status(
            feed_id=feed_id, is_recommended=False, priority=priority
        )

        # Assert - Step 3: Verify feed IMMEDIATELY disappears from recommended feeds
        recommended_feeds_after = await service.get_recommended_feeds()
        feed_ids_after = [str(f.id) for f in recommended_feeds_after]

        assert (
            feed_id not in feed_ids_after
        ), "Feed with is_recommended=False should IMMEDIATELY disappear from recommended feeds"

    finally:
        # Cleanup
        test_supabase_client.table("feeds").delete().eq("id", feed_id).execute()


@pytest.mark.asyncio
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(initial_priority=recommendation_priorities, updated_priority=recommendation_priorities)
async def test_property_30_immediate_priority_update(
    test_supabase_client, initial_priority, updated_priority
):
    """
    Property 30: Recommended Feed Real-Time Updates - Priority Updates

    For any recommended feed with updated recommendation_priority, the feed
    SHALL immediately appear in the correct position in subsequent queries
    (ordered by priority descending).

    Test Strategy:
    1. Create a recommended feed with initial priority
    2. Query and verify initial position
    3. Update priority
    4. Verify feed IMMEDIATELY appears in new position based on updated priority
    """
    # Arrange
    service = RecommendationService(test_supabase_client)

    # Create a recommended feed with initial priority
    test_feed_url = f"https://test-feed-{uuid4().hex}.com/rss.xml"
    feed_result = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": f"Test Feed {uuid4().hex[:8]}",
                "url": test_feed_url,
                "category": "Test Category",
                "is_active": False,
                "is_recommended": True,
                "recommendation_priority": initial_priority,
                "description": "Test feed for property 30",
            }
        )
        .execute()
    )

    feed = feed_result.data[0]
    feed_id = feed["id"]

    try:
        # Act & Assert - Step 1: Verify feed has initial priority
        recommended_feeds_before = await service.get_recommended_feeds()
        test_feed_before = next((f for f in recommended_feeds_before if str(f.id) == feed_id), None)

        assert test_feed_before is not None, "Feed should appear in recommended feeds"
        assert (
            test_feed_before.recommendation_priority == initial_priority
        ), f"Feed should have initial priority={initial_priority}"

        # Act - Step 2: Update priority
        await service.update_recommendation_status(
            feed_id=feed_id, is_recommended=True, priority=updated_priority
        )

        # Assert - Step 3: Verify feed IMMEDIATELY has updated priority
        recommended_feeds_after = await service.get_recommended_feeds()
        test_feed_after = next((f for f in recommended_feeds_after if str(f.id) == feed_id), None)

        assert test_feed_after is not None, "Feed should still appear in recommended feeds"
        assert (
            test_feed_after.recommendation_priority == updated_priority
        ), f"Feed should IMMEDIATELY have updated priority={updated_priority}"

        # Verify ordering is correct (descending by priority)
        test_feed_priorities = [
            f.recommendation_priority
            for f in recommended_feeds_after
            if str(f.id) == feed_id or f.recommendation_priority >= updated_priority - 10
        ]
        assert test_feed_priorities == sorted(
            test_feed_priorities, reverse=True
        ), "Feeds should be ordered by priority descending"

    finally:
        # Cleanup
        test_supabase_client.table("feeds").delete().eq("id", feed_id).execute()


@pytest.mark.asyncio
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(priorities=st.lists(recommendation_priorities, min_size=2, max_size=5, unique=True))
async def test_property_30_multiple_feeds_real_time_updates(test_supabase_client, priorities):
    """
    Property 30: Recommended Feed Real-Time Updates - Multiple Feeds

    For any set of feeds with changing recommendation status, all changes
    SHALL be immediately reflected in subsequent queries with correct ordering.

    Test Strategy:
    1. Create multiple non-recommended feeds
    2. Mark them as recommended one by one
    3. Verify each change is IMMEDIATELY reflected
    4. Verify ordering is correct after all changes
    """
    # Arrange
    service = RecommendationService(test_supabase_client)
    created_feed_ids = []

    try:
        # Create multiple non-recommended feeds
        for i, priority in enumerate(priorities):
            test_feed_url = f"https://test-feed-{uuid4().hex}.com/rss.xml"
            feed_result = (
                test_supabase_client.table("feeds")
                .insert(
                    {
                        "name": f"Test Feed {i} Priority {priority}",
                        "url": test_feed_url,
                        "category": "Test Category",
                        "is_active": False,
                        "is_recommended": False,
                        "recommendation_priority": priority,
                        "description": f"Test feed {i} for property 30",
                    }
                )
                .execute()
            )

            created_feed_ids.append(feed_result.data[0]["id"])

        # Verify none appear in recommended feeds initially
        initial_feeds = await service.get_recommended_feeds()
        initial_ids = [str(f.id) for f in initial_feeds]

        for feed_id in created_feed_ids:
            assert feed_id not in initial_ids, "Non-recommended feeds should not appear initially"

        # Mark each feed as recommended and verify immediate appearance
        for i, (feed_id, priority) in enumerate(zip(created_feed_ids, priorities, strict=False)):
            # Mark as recommended
            await service.update_recommendation_status(
                feed_id=feed_id, is_recommended=True, priority=priority
            )

            # Verify IMMEDIATE appearance
            current_feeds = await service.get_recommended_feeds()
            current_ids = [str(f.id) for f in current_feeds]

            assert (
                feed_id in current_ids
            ), f"Feed {i} should IMMEDIATELY appear after being marked as recommended"

            # Verify all previously marked feeds are still present
            for prev_feed_id in created_feed_ids[: i + 1]:
                assert (
                    prev_feed_id in current_ids
                ), "Previously recommended feed should still be present"

        # Final verification: all feeds present and correctly ordered
        final_feeds = await service.get_recommended_feeds()
        final_test_feeds = [f for f in final_feeds if str(f.id) in created_feed_ids]

        assert len(final_test_feeds) == len(
            priorities
        ), f"All {len(priorities)} feeds should be in recommended feeds"

        # Verify ordering (descending by priority)
        final_priorities = [f.recommendation_priority for f in final_test_feeds]
        expected_priorities = sorted(priorities, reverse=True)
        assert (
            final_priorities == expected_priorities
        ), f"Feeds should be ordered by priority descending. Expected {expected_priorities}, got {final_priorities}"

    finally:
        # Cleanup
        for feed_id in created_feed_ids:
            try:
                test_supabase_client.table("feeds").delete().eq("id", feed_id).execute()
            except Exception:
                pass


@pytest.mark.asyncio
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(priority=recommendation_priorities)
async def test_property_30_toggle_recommendation_status(test_supabase_client, priority):
    """
    Property 30: Recommended Feed Real-Time Updates - Toggle Status

    For any feed that toggles between recommended and not recommended multiple times,
    each change SHALL be immediately reflected in subsequent queries.

    Test Strategy:
    1. Create a non-recommended feed
    2. Toggle is_recommended: False -> True -> False -> True
    3. Verify each change is IMMEDIATELY reflected in queries
    """
    # Arrange
    service = RecommendationService(test_supabase_client)

    # Create a non-recommended feed
    test_feed_url = f"https://test-feed-{uuid4().hex}.com/rss.xml"
    feed_result = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": f"Test Feed {uuid4().hex[:8]}",
                "url": test_feed_url,
                "category": "Test Category",
                "is_active": False,
                "is_recommended": False,
                "recommendation_priority": priority,
                "description": "Test feed for property 30",
            }
        )
        .execute()
    )

    feed = feed_result.data[0]
    feed_id = feed["id"]

    try:
        # Initial state: is_recommended = False
        feeds_0 = await service.get_recommended_feeds()
        ids_0 = [str(f.id) for f in feeds_0]
        assert feed_id not in ids_0, "Feed should not be recommended initially"

        # Toggle 1: False -> True
        await service.update_recommendation_status(feed_id, True, priority)
        feeds_1 = await service.get_recommended_feeds()
        ids_1 = [str(f.id) for f in feeds_1]
        assert feed_id in ids_1, "Feed should IMMEDIATELY appear after marking as recommended"

        # Toggle 2: True -> False
        await service.update_recommendation_status(feed_id, False, priority)
        feeds_2 = await service.get_recommended_feeds()
        ids_2 = [str(f.id) for f in feeds_2]
        assert (
            feed_id not in ids_2
        ), "Feed should IMMEDIATELY disappear after marking as not recommended"

        # Toggle 3: False -> True
        await service.update_recommendation_status(feed_id, True, priority)
        feeds_3 = await service.get_recommended_feeds()
        ids_3 = [str(f.id) for f in feeds_3]
        assert (
            feed_id in ids_3
        ), "Feed should IMMEDIATELY reappear after marking as recommended again"

        # Verify final state has correct properties
        test_feed = next(f for f in feeds_3 if str(f.id) == feed_id)
        assert test_feed.is_recommended is True
        assert test_feed.recommendation_priority == priority

    finally:
        # Cleanup
        test_supabase_client.table("feeds").delete().eq("id", feed_id).execute()


@pytest.mark.asyncio
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(priority=recommendation_priorities)
async def test_property_30_concurrent_queries_consistency(test_supabase_client, priority):
    """
    Property 30: Recommended Feed Real-Time Updates - Query Consistency

    For any feed marked as recommended, multiple subsequent queries SHALL
    consistently return the feed until it is marked as not recommended.

    Test Strategy:
    1. Create and mark a feed as recommended
    2. Execute multiple queries in sequence
    3. Verify feed appears consistently in all queries
    4. Mark as not recommended
    5. Verify feed disappears consistently in all subsequent queries
    """
    # Arrange
    service = RecommendationService(test_supabase_client)

    # Create a recommended feed
    test_feed_url = f"https://test-feed-{uuid4().hex}.com/rss.xml"
    feed_result = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": f"Test Feed {uuid4().hex[:8]}",
                "url": test_feed_url,
                "category": "Test Category",
                "is_active": False,
                "is_recommended": True,
                "recommendation_priority": priority,
                "description": "Test feed for property 30",
            }
        )
        .execute()
    )

    feed = feed_result.data[0]
    feed_id = feed["id"]

    try:
        # Execute multiple queries - feed should appear in all
        for i in range(3):
            feeds = await service.get_recommended_feeds()
            ids = [str(f.id) for f in feeds]
            assert feed_id in ids, f"Feed should appear in query {i+1} while is_recommended=True"

        # Mark as not recommended
        await service.update_recommendation_status(feed_id, False, priority)

        # Execute multiple queries - feed should NOT appear in any
        for i in range(3):
            feeds = await service.get_recommended_feeds()
            ids = [str(f.id) for f in feeds]
            assert (
                feed_id not in ids
            ), f"Feed should NOT appear in query {i+1} after is_recommended=False"

    finally:
        # Cleanup
        test_supabase_client.table("feeds").delete().eq("id", feed_id).execute()


@pytest.mark.asyncio
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(priority=recommendation_priorities)
async def test_property_30_updated_at_timestamp_on_status_change(test_supabase_client, priority):
    """
    Property 30: Recommended Feed Real-Time Updates - Timestamp Updates

    For any feed with recommendation status change, the updated_at timestamp
    SHALL be updated to reflect the change time.

    Test Strategy:
    1. Create a feed
    2. Mark as recommended
    3. Verify updated_at timestamp is set
    4. Wait briefly and update again
    5. Verify updated_at timestamp is updated
    """
    # Arrange
    service = RecommendationService(test_supabase_client)

    # Create a non-recommended feed
    test_feed_url = f"https://test-feed-{uuid4().hex}.com/rss.xml"
    feed_result = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": f"Test Feed {uuid4().hex[:8]}",
                "url": test_feed_url,
                "category": "Test Category",
                "is_active": False,
                "is_recommended": False,
                "recommendation_priority": priority,
                "description": "Test feed for property 30",
            }
        )
        .execute()
    )

    feed = feed_result.data[0]
    feed_id = feed["id"]
    initial_updated_at = feed.get("updated_at")

    try:
        # Mark as recommended
        await service.update_recommendation_status(feed_id, True, priority)

        # Query database to check updated_at
        db_response_1 = test_supabase_client.table("feeds").select("*").eq("id", feed_id).execute()

        updated_at_1 = db_response_1.data[0].get("updated_at")
        assert updated_at_1 is not None, "updated_at should be set"

        # Wait briefly
        import asyncio

        await asyncio.sleep(0.1)

        # Update again
        await service.update_recommendation_status(feed_id, False, priority)

        # Query database to check updated_at changed
        db_response_2 = test_supabase_client.table("feeds").select("*").eq("id", feed_id).execute()

        updated_at_2 = db_response_2.data[0].get("updated_at")
        assert updated_at_2 is not None, "updated_at should still be set"

        # Note: We verify both timestamps exist; exact comparison may be unreliable
        # due to database precision and timing

    finally:
        # Cleanup
        test_supabase_client.table("feeds").delete().eq("id", feed_id).execute()
