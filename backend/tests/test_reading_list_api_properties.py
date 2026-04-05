"""
Property-based tests for Reading List API endpoints.

Tests Properties 1, 2, and 21 from the design document.
Uses Hypothesis to verify correctness properties across all valid inputs.

Feature: cross-platform-feature-parity
"""

import pytest
import asyncio
from uuid import uuid4, UUID
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from app.services.supabase_service import SupabaseService
from app.core.exceptions import SupabaseServiceError


# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

def discord_id_strategy():
    """Generate valid Discord IDs (numeric strings)."""
    return st.integers(min_value=100000, max_value=999999).map(lambda x: f"test_user_{x}")


def article_id_strategy():
    """Generate valid article UUIDs."""
    return st.just(uuid4())


# ---------------------------------------------------------------------------
# Property 1: 閱讀清單加入操作
# Feature: cross-platform-feature-parity, Property 1: 閱讀清單加入操作
# Validates: Requirements 1.1, 1.3, 6.1
# ---------------------------------------------------------------------------

@given(
    discord_id=discord_id_strategy(),
    article_id=article_id_strategy()
)
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_1_add_to_reading_list(discord_id, article_id, test_supabase_client):
    """
    Property 1: For any 用戶和文章，當用戶將文章加入閱讀清單後，
    查詢該用戶的閱讀清單應包含該文章。

    **Validates: Requirements 1.1, 1.3, 6.1**
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)
    
    # Setup: Create test user and article
    user_uuid = await service.get_or_create_user(discord_id)
    
    # Create a test feed first
    feed_response = test_supabase_client.table('feeds').insert({
        'name': f'Test Feed {discord_id}',
        'url': f'https://example.com/feed/{discord_id}',
        'category': 'Test',
        'is_active': True
    }).execute()
    feed_id = feed_response.data[0]['id']
    
    # Create a test article
    test_supabase_client.table('articles').insert({
        'id': str(article_id),
        'title': f'Test Article {article_id}',
        'url': f'https://example.com/article/{article_id}',
        'feed_id': feed_id,
        'tinkering_index': 3
    }).execute()
    
    try:
        # Action: Add article to reading list
        await service.save_to_reading_list(discord_id, article_id)
        
        # Verification: Query reading list
        reading_list = await service.get_reading_list(discord_id)
        
        # Assert: Article should be in the reading list
        article_ids = [item.article_id for item in reading_list]
        assert article_id in article_ids, (
            f"Article {article_id} not found in reading list after adding. "
            f"Reading list contains: {article_ids}"
        )
        
    finally:
        # Cleanup
        try:
            test_supabase_client.table('reading_list')\
                .delete()\
                .eq('user_id', str(user_uuid))\
                .eq('article_id', str(article_id))\
                .execute()
            test_supabase_client.table('articles').delete().eq('id', str(article_id)).execute()
            test_supabase_client.table('feeds').delete().eq('id', feed_id).execute()
            test_supabase_client.table('users').delete().eq('id', str(user_uuid)).execute()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Property 2: 閱讀清單移除操作
# Feature: cross-platform-feature-parity, Property 2: 閱讀清單移除操作
# Validates: Requirements 1.6, 6.6
# ---------------------------------------------------------------------------

@given(
    discord_id=discord_id_strategy(),
    article_id=article_id_strategy()
)
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_2_remove_from_reading_list(discord_id, article_id, test_supabase_client):
    """
    Property 2: For any 用戶和文章，當用戶從閱讀清單移除文章後，
    查詢該用戶的閱讀清單不應包含該文章。

    **Validates: Requirements 1.6, 6.6**
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)
    
    # Setup: Create test user and article
    user_uuid = await service.get_or_create_user(discord_id)
    
    # Create a test feed first
    feed_response = test_supabase_client.table('feeds').insert({
        'name': f'Test Feed {discord_id}',
        'url': f'https://example.com/feed/{discord_id}',
        'category': 'Test',
        'is_active': True
    }).execute()
    feed_id = feed_response.data[0]['id']
    
    # Create a test article
    test_supabase_client.table('articles').insert({
        'id': str(article_id),
        'title': f'Test Article {article_id}',
        'url': f'https://example.com/article/{article_id}',
        'feed_id': feed_id,
        'tinkering_index': 3
    }).execute()
    
    try:
        # Setup: Add article to reading list first
        await service.save_to_reading_list(discord_id, article_id)
        
        # Verify it was added
        reading_list_before = await service.get_reading_list(discord_id)
        article_ids_before = [item.article_id for item in reading_list_before]
        assert article_id in article_ids_before, "Setup failed: Article not in reading list"
        
        # Action: Remove article from reading list
        test_supabase_client.table('reading_list')\
            .delete()\
            .eq('user_id', str(user_uuid))\
            .eq('article_id', str(article_id))\
            .execute()
        
        # Verification: Query reading list
        reading_list_after = await service.get_reading_list(discord_id)
        
        # Assert: Article should NOT be in the reading list
        article_ids_after = [item.article_id for item in reading_list_after]
        assert article_id not in article_ids_after, (
            f"Article {article_id} still found in reading list after removal. "
            f"Reading list contains: {article_ids_after}"
        )
        
    finally:
        # Cleanup
        try:
            test_supabase_client.table('reading_list')\
                .delete()\
                .eq('user_id', str(user_uuid))\
                .eq('article_id', str(article_id))\
                .execute()
            test_supabase_client.table('articles').delete().eq('id', str(article_id)).execute()
            test_supabase_client.table('feeds').delete().eq('id', feed_id).execute()
            test_supabase_client.table('users').delete().eq('id', str(user_uuid)).execute()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Property 21: 閱讀清單冪等性
# Feature: cross-platform-feature-parity, Property 21: 閱讀清單冪等性
# Validates: Requirements 6.7, 6.8
# ---------------------------------------------------------------------------

@given(
    discord_id=discord_id_strategy(),
    article_id=article_id_strategy(),
    repeat_count=st.integers(min_value=2, max_value=5)
)
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_21_reading_list_idempotence(
    discord_id, article_id, repeat_count, test_supabase_client
):
    """
    Property 21: For any 用戶和文章，重複將相同文章加入閱讀清單
    應只產生一條記錄，且 (user_id, article_id) 組合應保持唯一。

    **Validates: Requirements 6.7, 6.8**
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)
    
    # Setup: Create test user and article
    user_uuid = await service.get_or_create_user(discord_id)
    
    # Create a test feed first
    feed_response = test_supabase_client.table('feeds').insert({
        'name': f'Test Feed {discord_id}',
        'url': f'https://example.com/feed/{discord_id}',
        'category': 'Test',
        'is_active': True
    }).execute()
    feed_id = feed_response.data[0]['id']
    
    # Create a test article
    test_supabase_client.table('articles').insert({
        'id': str(article_id),
        'title': f'Test Article {article_id}',
        'url': f'https://example.com/article/{article_id}',
        'feed_id': feed_id,
        'tinkering_index': 3
    }).execute()
    
    try:
        # Action: Add the same article multiple times
        for i in range(repeat_count):
            await service.save_to_reading_list(discord_id, article_id)
        
        # Verification: Query reading list
        reading_list = await service.get_reading_list(discord_id)
        
        # Assert: Should only have ONE record for this article
        matching_items = [item for item in reading_list if item.article_id == article_id]
        assert len(matching_items) == 1, (
            f"Expected exactly 1 record after {repeat_count} additions, "
            f"but found {len(matching_items)} records. "
            f"This violates the idempotence property (Requirements 6.7, 6.8)."
        )
        
        # Additional verification: Check database directly for uniqueness
        db_records = test_supabase_client.table('reading_list')\
            .select('*')\
            .eq('user_id', str(user_uuid))\
            .eq('article_id', str(article_id))\
            .execute()
        
        assert len(db_records.data) == 1, (
            f"Database contains {len(db_records.data)} records for "
            f"(user_id={user_uuid}, article_id={article_id}), expected 1. "
            f"This violates the UNIQUE constraint (user_id, article_id)."
        )
        
    finally:
        # Cleanup
        try:
            test_supabase_client.table('reading_list')\
                .delete()\
                .eq('user_id', str(user_uuid))\
                .eq('article_id', str(article_id))\
                .execute()
            test_supabase_client.table('articles').delete().eq('id', str(article_id)).execute()
            test_supabase_client.table('feeds').delete().eq('id', feed_id).execute()
            test_supabase_client.table('users').delete().eq('id', str(user_uuid)).execute()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Additional Edge Case Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_empty_reading_list(test_supabase_client):
    """
    Edge case: Query reading list for a user with no items.
    Should return an empty list without errors.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)
    discord_id = f"test_empty_{uuid4().hex[:8]}"
    
    try:
        # Query reading list for new user (should be empty)
        reading_list = await service.get_reading_list(discord_id)
        
        assert isinstance(reading_list, list), "Reading list should be a list"
        assert len(reading_list) == 0, "Reading list should be empty for new user"
        
    finally:
        # Cleanup
        try:
            user_uuid = await service.get_or_create_user(discord_id)
            test_supabase_client.table('users').delete().eq('id', str(user_uuid)).execute()
        except Exception:
            pass


@pytest.mark.asyncio
async def test_add_nonexistent_article_fails(test_supabase_client):
    """
    Edge case: Attempting to add a non-existent article should fail gracefully.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)
    discord_id = f"test_nonexistent_{uuid4().hex[:8]}"
    nonexistent_article_id = uuid4()
    
    try:
        # Attempt to add non-existent article
        with pytest.raises(Exception):  # Should raise some error (foreign key constraint)
            await service.save_to_reading_list(discord_id, nonexistent_article_id)
            
    finally:
        # Cleanup
        try:
            user_uuid = await service.get_or_create_user(discord_id)
            test_supabase_client.table('users').delete().eq('id', str(user_uuid)).execute()
        except Exception:
            pass


@pytest.mark.asyncio
async def test_reading_list_sorted_by_added_at(test_supabase_client):
    """
    Requirement 1.4: Reading list should be sorted by added_at descending.
    Most recently added articles should appear first.
    """
    service = SupabaseService(client=test_supabase_client, validate_connection=False)
    discord_id = f"test_sort_{uuid4().hex[:8]}"
    
    # Setup: Create test user
    user_uuid = await service.get_or_create_user(discord_id)
    
    # Create a test feed
    feed_response = test_supabase_client.table('feeds').insert({
        'name': f'Test Feed {discord_id}',
        'url': f'https://example.com/feed/{discord_id}',
        'category': 'Test',
        'is_active': True
    }).execute()
    feed_id = feed_response.data[0]['id']
    
    # Create multiple articles and add them to reading list
    article_ids = []
    for i in range(3):
        article_id = uuid4()
        article_ids.append(article_id)
        
        test_supabase_client.table('articles').insert({
            'id': str(article_id),
            'title': f'Test Article {i}',
            'url': f'https://example.com/article/{article_id}',
            'feed_id': feed_id,
            'tinkering_index': 3
        }).execute()
        
        await service.save_to_reading_list(discord_id, article_id)
        
        # Small delay to ensure different timestamps
        await asyncio.sleep(0.1)
    
    try:
        # Query reading list
        reading_list = await service.get_reading_list(discord_id)
        
        # Verify sorting: most recent first
        assert len(reading_list) == 3, f"Expected 3 items, got {len(reading_list)}"
        
        # Check that added_at timestamps are in descending order
        for i in range(len(reading_list) - 1):
            assert reading_list[i].added_at >= reading_list[i + 1].added_at, (
                f"Reading list not sorted by added_at descending. "
                f"Item {i} added_at: {reading_list[i].added_at}, "
                f"Item {i+1} added_at: {reading_list[i + 1].added_at}"
            )
        
    finally:
        # Cleanup
        try:
            for article_id in article_ids:
                test_supabase_client.table('reading_list')\
                    .delete()\
                    .eq('user_id', str(user_uuid))\
                    .eq('article_id', str(article_id))\
                    .execute()
                test_supabase_client.table('articles').delete().eq('id', str(article_id)).execute()
            test_supabase_client.table('feeds').delete().eq('id', feed_id).execute()
            test_supabase_client.table('users').delete().eq('id', str(user_uuid)).execute()
        except Exception:
            pass
