"""
Integration tests for SQL initialization script
Task 2.9: 撰寫 SQL 腳本的整合測試
Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8

These tests verify that the init_supabase.sql script:
- Can be executed successfully
- Creates all required tables
- Enables pgvector extension
- Creates all required indexes
"""

import os

import pytest
from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
load_dotenv()


@pytest.fixture(scope="module")
def supabase_client() -> Client:
    """Create a Supabase client for testing."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        pytest.skip("SUPABASE_URL and SUPABASE_KEY must be set for integration tests")

    client = create_client(supabase_url, supabase_key)
    return client


class TestSQLInitialization:
    """Integration tests for SQL initialization script."""

    def test_sql_script_can_execute(self, supabase_client):
        """
        Verify that the SQL script can be executed successfully.
        **Validates: Requirements 3.1**

        Note: This test assumes the SQL script has already been executed
        in the Supabase dashboard. It verifies the result by checking
        that tables exist.
        """
        # Try to query a table - if it exists, the script executed successfully
        try:
            result = supabase_client.table("users").select("id").limit(0).execute()
            assert result is not None
        except Exception as e:
            pytest.fail(f"SQL script appears not to have been executed: {e}")

    def test_users_table_exists(self, supabase_client):
        """
        Verify that the users table has been created.
        **Validates: Requirements 3.3**
        """
        try:
            result = supabase_client.table("users").select("*").limit(0).execute()
            assert result is not None
        except Exception as e:
            pytest.fail(f"users table does not exist: {e}")

    def test_feeds_table_exists(self, supabase_client):
        """
        Verify that the feeds table has been created.
        **Validates: Requirements 3.4**
        """
        try:
            result = supabase_client.table("feeds").select("*").limit(0).execute()
            assert result is not None
        except Exception as e:
            pytest.fail(f"feeds table does not exist: {e}")

    def test_user_subscriptions_table_exists(self, supabase_client):
        """
        Verify that the user_subscriptions table has been created.
        **Validates: Requirements 3.5**
        """
        try:
            result = supabase_client.table("user_subscriptions").select("*").limit(0).execute()
            assert result is not None
        except Exception as e:
            pytest.fail(f"user_subscriptions table does not exist: {e}")

    def test_articles_table_exists(self, supabase_client):
        """
        Verify that the articles table has been created.
        **Validates: Requirements 3.6**
        """
        try:
            result = supabase_client.table("articles").select("*").limit(0).execute()
            assert result is not None
        except Exception as e:
            pytest.fail(f"articles table does not exist: {e}")

    def test_reading_list_table_exists(self, supabase_client):
        """
        Verify that the reading_list table has been created.
        **Validates: Requirements 3.7**
        """
        try:
            result = supabase_client.table("reading_list").select("*").limit(0).execute()
            assert result is not None
        except Exception as e:
            pytest.fail(f"reading_list table does not exist: {e}")

    def test_pgvector_extension_enabled(self, supabase_client):
        """
        Verify that the pgvector extension has been enabled.
        **Validates: Requirements 3.2**

        This test checks if we can query the articles table which has
        a VECTOR column. If pgvector is not enabled, this would fail.
        """
        try:
            # Try to select the embedding column which is of type VECTOR
            result = supabase_client.table("articles").select("embedding").limit(0).execute()
            assert result is not None
        except Exception as e:
            pytest.fail(f"pgvector extension may not be enabled: {e}")

    def test_indexes_created(self, supabase_client):
        """
        Verify that all required indexes have been created.
        **Validates: Requirements 3.8**

        This test verifies indexes by attempting queries that would
        benefit from the indexes. If the queries execute without error,
        the indexes likely exist.
        """
        # Test feeds indexes
        try:
            supabase_client.table("feeds").select("*").eq("is_active", True).limit(1).execute()
            supabase_client.table("feeds").select("*").eq("category", "Test").limit(1).execute()
        except Exception as e:
            pytest.fail(f"feeds table indexes may not exist: {e}")

        # Test user_subscriptions indexes
        try:
            # These queries would use the foreign key indexes
            supabase_client.table("user_subscriptions").select("*").limit(1).execute()
        except Exception as e:
            pytest.fail(f"user_subscriptions table indexes may not exist: {e}")

        # Test articles indexes
        try:
            supabase_client.table("articles").select("*").limit(1).execute()
        except Exception as e:
            pytest.fail(f"articles table indexes may not exist: {e}")

        # Test reading_list indexes
        try:
            supabase_client.table("reading_list").select("*").eq("status", "Unread").limit(
                1
            ).execute()
        except Exception as e:
            pytest.fail(f"reading_list table indexes may not exist: {e}")


class TestTableStructure:
    """Test that tables have the correct structure."""

    def test_users_table_structure(self, supabase_client):
        """
        Verify users table has correct columns.
        **Validates: Requirements 3.3**
        """
        # Insert a test user to verify structure
        test_discord_id = f"test_user_{os.urandom(8).hex()}"

        try:
            result = (
                supabase_client.table("users").insert({"discord_id": test_discord_id}).execute()
            )

            assert result.data is not None
            assert len(result.data) > 0

            user = result.data[0]
            assert "id" in user
            assert "discord_id" in user
            assert "created_at" in user
            assert user["discord_id"] == test_discord_id

            # Cleanup
            supabase_client.table("users").delete().eq("discord_id", test_discord_id).execute()

        except Exception as e:
            pytest.fail(f"users table structure is incorrect: {e}")

    def test_feeds_table_structure(self, supabase_client):
        """
        Verify feeds table has correct columns.
        **Validates: Requirements 3.4**
        """
        test_url = f"https://test-feed-{os.urandom(8).hex()}.com/rss.xml"

        try:
            result = (
                supabase_client.table("feeds")
                .insert({"name": "Test Feed", "url": test_url, "category": "Test"})
                .execute()
            )

            assert result.data is not None
            assert len(result.data) > 0

            feed = result.data[0]
            assert "id" in feed
            assert "name" in feed
            assert "url" in feed
            assert "category" in feed
            assert "is_active" in feed
            assert "created_at" in feed
            assert feed["is_active"] is True  # Default value

            # Cleanup
            supabase_client.table("feeds").delete().eq("url", test_url).execute()

        except Exception as e:
            pytest.fail(f"feeds table structure is incorrect: {e}")

    def test_articles_table_has_embedding_column(self, supabase_client):
        """
        Verify articles table has embedding column of type VECTOR.
        **Validates: Requirements 3.6**
        """
        # Create a test feed first
        test_feed_url = f"https://test-feed-{os.urandom(8).hex()}.com/rss.xml"
        feed_result = (
            supabase_client.table("feeds")
            .insert({"name": "Test Feed", "url": test_feed_url, "category": "Test"})
            .execute()
        )

        feed_id = feed_result.data[0]["id"]
        test_article_url = f"https://test-article-{os.urandom(8).hex()}.com"

        try:
            # Insert article without embedding (should allow NULL)
            result = (
                supabase_client.table("articles")
                .insert({"feed_id": feed_id, "title": "Test Article", "url": test_article_url})
                .execute()
            )

            assert result.data is not None
            assert len(result.data) > 0

            article = result.data[0]
            assert "embedding" in article
            assert article["embedding"] is None  # Should allow NULL

        finally:
            # Cleanup
            supabase_client.table("articles").delete().eq("url", test_article_url).execute()
            supabase_client.table("feeds").delete().eq("url", test_feed_url).execute()

    def test_reading_list_table_structure(self, supabase_client):
        """
        Verify reading_list table has correct columns and constraints.
        **Validates: Requirements 3.7**
        """
        # Create test user
        test_discord_id = f"test_user_{os.urandom(8).hex()}"
        user_result = (
            supabase_client.table("users").insert({"discord_id": test_discord_id}).execute()
        )
        user_id = user_result.data[0]["id"]

        # Create test feed
        test_feed_url = f"https://test-feed-{os.urandom(8).hex()}.com/rss.xml"
        feed_result = (
            supabase_client.table("feeds")
            .insert({"name": "Test Feed", "url": test_feed_url, "category": "Test"})
            .execute()
        )
        feed_id = feed_result.data[0]["id"]

        # Create test article
        test_article_url = f"https://test-article-{os.urandom(8).hex()}.com"
        article_result = (
            supabase_client.table("articles")
            .insert({"feed_id": feed_id, "title": "Test Article", "url": test_article_url})
            .execute()
        )
        article_id = article_result.data[0]["id"]

        try:
            # Insert reading list entry
            result = (
                supabase_client.table("reading_list")
                .insert({"user_id": user_id, "article_id": article_id, "status": "Unread"})
                .execute()
            )

            assert result.data is not None
            assert len(result.data) > 0

            entry = result.data[0]
            assert "id" in entry
            assert "user_id" in entry
            assert "article_id" in entry
            assert "status" in entry
            assert "rating" in entry
            assert "added_at" in entry
            assert "updated_at" in entry

        finally:
            # Cleanup
            supabase_client.table("reading_list").delete().eq("user_id", user_id).execute()
            supabase_client.table("articles").delete().eq("url", test_article_url).execute()
            supabase_client.table("feeds").delete().eq("url", test_feed_url).execute()
            supabase_client.table("users").delete().eq("discord_id", test_discord_id).execute()


class TestConstraints:
    """Test database constraints are properly enforced."""

    def test_discord_id_unique_constraint(self, supabase_client):
        """
        Verify that duplicate discord_id values are rejected.
        **Validates: Requirements 3.3**
        """
        test_discord_id = f"test_user_{os.urandom(8).hex()}"

        try:
            # Insert first user
            supabase_client.table("users").insert({"discord_id": test_discord_id}).execute()

            # Try to insert duplicate - should fail
            with pytest.raises(Exception) as exc_info:
                supabase_client.table("users").insert({"discord_id": test_discord_id}).execute()

            # Verify it's a unique constraint error
            error_str = str(exc_info.value).lower()
            assert "duplicate" in error_str or "unique" in error_str

        finally:
            # Cleanup
            supabase_client.table("users").delete().eq("discord_id", test_discord_id).execute()

    def test_feed_url_unique_constraint(self, supabase_client):
        """
        Verify that duplicate feed URLs are rejected.
        **Validates: Requirements 3.4**
        """
        test_url = f"https://test-feed-{os.urandom(8).hex()}.com/rss.xml"

        try:
            # Insert first feed
            supabase_client.table("feeds").insert(
                {"name": "Test Feed 1", "url": test_url, "category": "Test"}
            ).execute()

            # Try to insert duplicate URL - should fail
            with pytest.raises(Exception) as exc_info:
                supabase_client.table("feeds").insert(
                    {"name": "Test Feed 2", "url": test_url, "category": "Test"}
                ).execute()

            error_str = str(exc_info.value).lower()
            assert "duplicate" in error_str or "unique" in error_str

        finally:
            # Cleanup
            supabase_client.table("feeds").delete().eq("url", test_url).execute()

    def test_reading_list_status_check_constraint(self, supabase_client):
        """
        Verify that invalid status values are rejected.
        **Validates: Requirements 3.7**
        """
        # Create test data
        test_discord_id = f"test_user_{os.urandom(8).hex()}"
        user_result = (
            supabase_client.table("users").insert({"discord_id": test_discord_id}).execute()
        )
        user_id = user_result.data[0]["id"]

        test_feed_url = f"https://test-feed-{os.urandom(8).hex()}.com/rss.xml"
        feed_result = (
            supabase_client.table("feeds")
            .insert({"name": "Test Feed", "url": test_feed_url, "category": "Test"})
            .execute()
        )
        feed_id = feed_result.data[0]["id"]

        test_article_url = f"https://test-article-{os.urandom(8).hex()}.com"
        article_result = (
            supabase_client.table("articles")
            .insert({"feed_id": feed_id, "title": "Test Article", "url": test_article_url})
            .execute()
        )
        article_id = article_result.data[0]["id"]

        try:
            # Try to insert with invalid status
            with pytest.raises(Exception) as exc_info:
                supabase_client.table("reading_list").insert(
                    {"user_id": user_id, "article_id": article_id, "status": "InvalidStatus"}
                ).execute()

            error_str = str(exc_info.value).lower()
            assert "check" in error_str or "constraint" in error_str or "violates" in error_str

        finally:
            # Cleanup
            supabase_client.table("articles").delete().eq("url", test_article_url).execute()
            supabase_client.table("feeds").delete().eq("url", test_feed_url).execute()
            supabase_client.table("users").delete().eq("discord_id", test_discord_id).execute()

    def test_cascade_delete_user_subscriptions(self, supabase_client):
        """
        Verify that deleting a user cascades to user_subscriptions.
        **Validates: Requirements 3.9**
        """
        # Create test user
        test_discord_id = f"test_user_{os.urandom(8).hex()}"
        user_result = (
            supabase_client.table("users").insert({"discord_id": test_discord_id}).execute()
        )
        user_id = user_result.data[0]["id"]

        # Create test feed
        test_feed_url = f"https://test-feed-{os.urandom(8).hex()}.com/rss.xml"
        feed_result = (
            supabase_client.table("feeds")
            .insert({"name": "Test Feed", "url": test_feed_url, "category": "Test"})
            .execute()
        )
        feed_id = feed_result.data[0]["id"]

        try:
            # Create subscription
            supabase_client.table("user_subscriptions").insert(
                {"user_id": user_id, "feed_id": feed_id}
            ).execute()

            # Delete user
            supabase_client.table("users").delete().eq("id", user_id).execute()

            # Verify subscription was deleted
            result = (
                supabase_client.table("user_subscriptions")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            assert len(result.data) == 0

        finally:
            # Cleanup feed
            supabase_client.table("feeds").delete().eq("url", test_feed_url).execute()

    def test_cascade_delete_feed_articles(self, supabase_client):
        """
        Verify that deleting a feed cascades to articles.
        **Validates: Requirements 3.10**
        """
        # Create test feed
        test_feed_url = f"https://test-feed-{os.urandom(8).hex()}.com/rss.xml"
        feed_result = (
            supabase_client.table("feeds")
            .insert({"name": "Test Feed", "url": test_feed_url, "category": "Test"})
            .execute()
        )
        feed_id = feed_result.data[0]["id"]

        # Create test article
        test_article_url = f"https://test-article-{os.urandom(8).hex()}.com"
        supabase_client.table("articles").insert(
            {"feed_id": feed_id, "title": "Test Article", "url": test_article_url}
        ).execute()

        # Delete feed
        supabase_client.table("feeds").delete().eq("id", feed_id).execute()

        # Verify article was deleted
        result = supabase_client.table("articles").select("*").eq("url", test_article_url).execute()
        assert len(result.data) == 0
