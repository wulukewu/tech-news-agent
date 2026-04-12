"""
Test reading_list table schema matches design specifications.
Task 1.1: 建立 reading_list 資料表
"""

import os

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from supabase import Client

# Add unique test ID for cascade tests
pytest.test_id = os.urandom(4).hex()


class TestReadingListSchema:
    """Test reading_list table schema and constraints."""

    def test_reading_list_table_exists(self, test_supabase_client: Client):
        """Verify reading_list table exists."""
        # Query the table to ensure it exists
        response = test_supabase_client.table("reading_list").select("*").limit(0).execute()
        assert response is not None

    def test_reading_list_columns_exist(
        self, test_supabase_client: Client, test_user, test_article
    ):
        """Verify all required columns exist."""
        # Insert a test record
        data = {
            "user_id": str(test_user["id"]),
            "article_id": str(test_article["id"]),
            "status": "Unread",
            "rating": 5,
        }

        response = test_supabase_client.table("reading_list").insert(data).execute()
        assert len(response.data) == 1

        record = response.data[0]

        # Verify all columns exist
        assert "id" in record
        assert "user_id" in record
        assert "article_id" in record
        assert "status" in record
        assert "rating" in record
        assert "added_at" in record
        assert "updated_at" in record

    def test_status_default_value(self, test_supabase_client: Client, test_user, test_article):
        """Verify status defaults to 'Unread' when not specified."""
        data = {
            "user_id": str(test_user["id"]),
            "article_id": str(test_article["id"]),
            # Note: status not specified
        }

        response = test_supabase_client.table("reading_list").insert(data).execute()
        assert len(response.data) == 1
        assert response.data[0]["status"] == "Unread"

    def test_unique_constraint_user_article(
        self, test_supabase_client: Client, test_user, test_article
    ):
        """Verify (user_id, article_id) unique constraint."""
        data = {
            "user_id": str(test_user["id"]),
            "article_id": str(test_article["id"]),
            "status": "Unread",
        }

        # First insert should succeed
        response1 = test_supabase_client.table("reading_list").insert(data).execute()
        assert len(response1.data) == 1

        # Second insert with same user_id and article_id should fail
        # But we can use upsert to update instead
        data["rating"] = 5
        response2 = (
            test_supabase_client.table("reading_list")
            .upsert(data, on_conflict="user_id,article_id")
            .execute()
        )
        assert len(response2.data) == 1
        assert response2.data[0]["rating"] == 5

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(status=st.sampled_from(["Unread", "Read", "Archived"]))
    def test_status_check_constraint_valid(
        self, test_supabase_client: Client, test_user, test_article, status
    ):
        """Property: Valid status values are accepted."""
        # Generate unique article for each test iteration
        import uuid

        unique_article_url = f"https://test-{uuid.uuid4()}.com"
        article_data = {
            "feed_id": str(test_article["feed_id"]),
            "title": f"Test Article {uuid.uuid4()}",
            "url": unique_article_url,
        }
        article_response = test_supabase_client.table("articles").insert(article_data).execute()
        unique_article_id = article_response.data[0]["id"]

        try:
            data = {
                "user_id": str(test_user["id"]),
                "article_id": str(unique_article_id),
                "status": status,
            }

            response = test_supabase_client.table("reading_list").insert(data).execute()
            assert len(response.data) == 1
            assert response.data[0]["status"] == status
        finally:
            # Cleanup
            test_supabase_client.table("articles").delete().eq("id", unique_article_id).execute()

    def test_status_check_constraint_invalid(
        self, test_supabase_client: Client, test_user, test_article
    ):
        """Verify invalid status values are rejected."""
        data = {
            "user_id": str(test_user["id"]),
            "article_id": str(test_article["id"]),
            "status": "InvalidStatus",
        }

        with pytest.raises(Exception):  # Should raise constraint violation
            test_supabase_client.table("reading_list").insert(data).execute()

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(rating=st.integers(min_value=1, max_value=5))
    def test_rating_check_constraint_valid(
        self, test_supabase_client: Client, test_user, test_article, rating
    ):
        """Property: Valid rating values (1-5) are accepted."""
        # Generate unique article for each test iteration
        import uuid

        unique_article_url = f"https://test-{uuid.uuid4()}.com"
        article_data = {
            "feed_id": str(test_article["feed_id"]),
            "title": f"Test Article {uuid.uuid4()}",
            "url": unique_article_url,
        }
        article_response = test_supabase_client.table("articles").insert(article_data).execute()
        unique_article_id = article_response.data[0]["id"]

        try:
            data = {
                "user_id": str(test_user["id"]),
                "article_id": str(unique_article_id),
                "status": "Unread",
                "rating": rating,
            }

            response = test_supabase_client.table("reading_list").insert(data).execute()
            assert len(response.data) == 1
            assert response.data[0]["rating"] == rating
        finally:
            # Cleanup
            test_supabase_client.table("articles").delete().eq("id", unique_article_id).execute()

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(rating=st.integers().filter(lambda x: x < 1 or x > 5))
    def test_rating_check_constraint_invalid(
        self, test_supabase_client: Client, test_user, test_article, rating
    ):
        """Property: Invalid rating values are rejected."""
        # Generate unique article for each test iteration
        import uuid

        unique_article_url = f"https://test-{uuid.uuid4()}.com"
        article_data = {
            "feed_id": str(test_article["feed_id"]),
            "title": f"Test Article {uuid.uuid4()}",
            "url": unique_article_url,
        }
        article_response = test_supabase_client.table("articles").insert(article_data).execute()
        unique_article_id = article_response.data[0]["id"]

        try:
            data = {
                "user_id": str(test_user["id"]),
                "article_id": str(unique_article_id),
                "status": "Unread",
                "rating": rating,
            }

            with pytest.raises(Exception):  # Should raise constraint violation
                test_supabase_client.table("reading_list").insert(data).execute()
        finally:
            # Cleanup
            test_supabase_client.table("articles").delete().eq("id", unique_article_id).execute()

    def test_rating_null_allowed(self, test_supabase_client: Client, test_user, test_article):
        """Verify rating can be NULL."""
        data = {
            "user_id": str(test_user["id"]),
            "article_id": str(test_article["id"]),
            "status": "Unread",
            "rating": None,
        }

        response = test_supabase_client.table("reading_list").insert(data).execute()
        assert len(response.data) == 1
        assert response.data[0]["rating"] is None

    def test_foreign_key_user_id(self, test_supabase_client: Client, test_article):
        """Verify foreign key constraint on user_id."""
        import uuid

        data = {
            "user_id": str(uuid.uuid4()),  # Non-existent user
            "article_id": str(test_article["id"]),
            "status": "Unread",
        }

        with pytest.raises(Exception):  # Should raise foreign key violation
            test_supabase_client.table("reading_list").insert(data).execute()

    def test_foreign_key_article_id(self, test_supabase_client: Client, test_user):
        """Verify foreign key constraint on article_id."""
        import uuid

        data = {
            "user_id": str(test_user["id"]),
            "article_id": str(uuid.uuid4()),  # Non-existent article
            "status": "Unread",
        }

        with pytest.raises(Exception):  # Should raise foreign key violation
            test_supabase_client.table("reading_list").insert(data).execute()

    def test_updated_at_trigger(self, test_supabase_client: Client, test_user, test_article):
        """Verify updated_at is automatically updated on modification."""
        import time

        # Insert initial record
        data = {
            "user_id": str(test_user["id"]),
            "article_id": str(test_article["id"]),
            "status": "Unread",
        }

        response1 = test_supabase_client.table("reading_list").insert(data).execute()
        initial_updated_at = response1.data[0]["updated_at"]
        record_id = response1.data[0]["id"]

        # Wait a moment to ensure timestamp difference
        time.sleep(0.1)

        # Update the record
        response2 = (
            test_supabase_client.table("reading_list")
            .update({"status": "Read"})
            .eq("id", record_id)
            .execute()
        )

        updated_updated_at = response2.data[0]["updated_at"]

        # Verify updated_at changed
        assert updated_updated_at > initial_updated_at

    def test_cascade_delete_user(self, test_supabase_client: Client, test_article):
        """Verify ON DELETE CASCADE for user_id."""
        # Create a temporary user
        user_data = {"discord_id": f"test_cascade_user_{pytest.test_id}"}
        user_response = test_supabase_client.table("users").insert(user_data).execute()
        temp_user_id = user_response.data[0]["id"]

        # Create reading list entry
        reading_list_data = {
            "user_id": str(temp_user_id),
            "article_id": str(test_article["id"]),
            "status": "Unread",
        }
        test_supabase_client.table("reading_list").insert(reading_list_data).execute()

        # Delete the user
        test_supabase_client.table("users").delete().eq("id", temp_user_id).execute()

        # Verify reading list entry was also deleted
        check_response = (
            test_supabase_client.table("reading_list")
            .select("*")
            .eq("user_id", str(temp_user_id))
            .execute()
        )

        assert len(check_response.data) == 0

    def test_cascade_delete_article(self, test_supabase_client: Client, test_user, test_feed):
        """Verify ON DELETE CASCADE for article_id."""
        # Create a temporary article
        article_data = {
            "feed_id": str(test_feed["id"]),
            "title": f"Test Cascade Article {pytest.test_id}",
            "url": f"https://example.com/cascade/{pytest.test_id}",
            "published_at": "2024-01-01T00:00:00Z",
        }
        article_response = test_supabase_client.table("articles").insert(article_data).execute()
        temp_article_id = article_response.data[0]["id"]

        # Create reading list entry
        reading_list_data = {
            "user_id": str(test_user["id"]),
            "article_id": str(temp_article_id),
            "status": "Unread",
        }
        test_supabase_client.table("reading_list").insert(reading_list_data).execute()

        # Delete the article
        test_supabase_client.table("articles").delete().eq("id", temp_article_id).execute()

        # Verify reading list entry was also deleted
        check_response = (
            test_supabase_client.table("reading_list")
            .select("*")
            .eq("article_id", str(temp_article_id))
            .execute()
        )

        assert len(check_response.data) == 0
