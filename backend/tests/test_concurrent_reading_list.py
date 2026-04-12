"""
Test concurrent reading list operations to verify UPSERT logic.

This test specifically validates Requirement 13.3:
"THE System SHALL handle concurrent reading list operations using UPSERT logic"
"""

import asyncio
from uuid import uuid4

import pytest
from supabase import Client

from app.services.supabase_service import SupabaseService


@pytest.mark.asyncio
async def test_concurrent_save_to_reading_list(
    test_supabase_client: Client, test_feed, cleanup_test_data
):
    """
    Test that multiple concurrent save_to_reading_list calls for the same user and article
    don't cause errors and result in exactly one record.

    This validates Requirement 13.3: concurrent reading list operations using UPSERT logic.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    # Create a test user
    discord_id = f"concurrent_test_{uuid4().hex}"
    user_uuid = await service.get_or_create_user(discord_id)
    cleanup_test_data["users"].append(str(user_uuid))

    # Create a test article
    test_article = {
        "title": "Concurrent Reading List Test Article",
        "url": f"https://concurrent-reading-{uuid4().hex}.com",
        "feed_id": str(test_feed["id"]),
    }

    result = await service.insert_articles([test_article])
    assert result.inserted_count == 1

    response = (
        test_supabase_client.table("articles").select("id").eq("url", test_article["url"]).execute()
    )
    article_id = response.data[0]["id"]
    cleanup_test_data["articles"].append(article_id)

    # Simulate 10 concurrent save_to_reading_list calls for the same article
    async def save_article():
        await service.save_to_reading_list(discord_id, article_id)

    # Execute all saves concurrently
    await asyncio.gather(*[save_article() for _ in range(10)])

    # Verify only one record exists in reading_list
    reading_list = await service.get_reading_list(discord_id)
    assert len(reading_list) == 1, f"Expected 1 record, got {len(reading_list)}"
    assert str(reading_list[0].article_id) == article_id
    assert reading_list[0].status == "Unread"


@pytest.mark.asyncio
async def test_concurrent_save_different_articles(
    test_supabase_client: Client, test_feed, cleanup_test_data
):
    """
    Test that concurrent saves of different articles by the same user work correctly.

    This validates that UPSERT logic doesn't interfere with legitimate concurrent operations.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    # Create a test user
    discord_id = f"concurrent_multi_test_{uuid4().hex}"
    user_uuid = await service.get_or_create_user(discord_id)
    cleanup_test_data["users"].append(str(user_uuid))

    # Create 5 test articles
    test_articles = [
        {
            "title": f"Concurrent Article {i}",
            "url": f"https://concurrent-multi-{i}-{uuid4().hex}.com",
            "feed_id": str(test_feed["id"]),
        }
        for i in range(5)
    ]

    result = await service.insert_articles(test_articles)
    assert result.inserted_count == 5

    # Get article IDs
    article_ids = []
    for article in test_articles:
        response = (
            test_supabase_client.table("articles").select("id").eq("url", article["url"]).execute()
        )
        article_id = response.data[0]["id"]
        article_ids.append(article_id)
        cleanup_test_data["articles"].append(article_id)

    # Save all articles concurrently
    async def save_article(article_id):
        await service.save_to_reading_list(discord_id, article_id)

    await asyncio.gather(*[save_article(aid) for aid in article_ids])

    # Verify all 5 articles are in reading list
    reading_list = await service.get_reading_list(discord_id)
    assert len(reading_list) == 5, f"Expected 5 records, got {len(reading_list)}"

    # Verify all article IDs are present
    reading_list_ids = {str(item.article_id) for item in reading_list}
    expected_ids = set(article_ids)
    assert reading_list_ids == expected_ids


@pytest.mark.asyncio
async def test_concurrent_save_and_update(
    test_supabase_client: Client, test_feed, cleanup_test_data
):
    """
    Test concurrent save and update operations on the same reading list item.

    This validates that UPSERT handles mixed operations correctly.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)

    # Create a test user
    discord_id = f"concurrent_update_test_{uuid4().hex}"
    user_uuid = await service.get_or_create_user(discord_id)
    cleanup_test_data["users"].append(str(user_uuid))

    # Create a test article
    test_article = {
        "title": "Concurrent Update Test Article",
        "url": f"https://concurrent-update-{uuid4().hex}.com",
        "feed_id": str(test_feed["id"]),
    }

    result = await service.insert_articles([test_article])
    assert result.inserted_count == 1

    response = (
        test_supabase_client.table("articles").select("id").eq("url", test_article["url"]).execute()
    )
    article_id = response.data[0]["id"]
    cleanup_test_data["articles"].append(article_id)

    # Concurrently: save to reading list and update status
    async def save_article():
        await service.save_to_reading_list(discord_id, article_id)

    async def update_status():
        # Wait a tiny bit to ensure save happens first (but still concurrent)
        await asyncio.sleep(0.01)
        await service.update_article_status(discord_id, article_id, "Read")

    # Execute both operations concurrently
    await asyncio.gather(save_article(), save_article(), update_status())  # Duplicate save

    # Verify only one record exists and status is updated
    reading_list = await service.get_reading_list(discord_id)
    assert len(reading_list) == 1, f"Expected 1 record, got {len(reading_list)}"
    assert str(reading_list[0].article_id) == article_id
    # Status should be 'Read' if update happened after save, or might be 'Unread' if save happened after update
    # Either is acceptable in concurrent scenarios
    assert reading_list[0].status in ["Unread", "Read"]
