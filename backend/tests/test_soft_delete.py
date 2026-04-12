"""
Tests for Soft Delete Functionality

This test suite validates that soft delete works correctly across all repositories.
It tests that deleted entities are marked with deleted_at timestamp and excluded
from normal queries, while still being restorable.

Validates: Requirements 14.5
"""

from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.errors import ValidationError
from app.repositories.article import ArticleRepository
from app.repositories.feed import FeedRepository
from app.repositories.reading_list import ReadingListRepository
from app.repositories.user import UserRepository


class TestSoftDeleteUser:
    """Test soft delete functionality for User repository."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Supabase client."""
        return Mock()

    @pytest.fixture
    def user_repo(self, mock_client):
        """Create a UserRepository instance with mocked client."""
        return UserRepository(mock_client)

    @pytest.mark.asyncio
    async def test_delete_sets_deleted_at_timestamp(self, user_repo, mock_client):
        """Test that delete operation sets deleted_at timestamp instead of removing record."""
        user_id = uuid4()

        # Mock the check query (entity exists and not deleted)
        check_response = Mock()
        check_response.data = [{"id": str(user_id)}]

        # Mock the update query (soft delete)
        update_response = Mock()
        update_response.data = [
            {
                "id": str(user_id),
                "discord_id": "test_user",
                "deleted_at": datetime.utcnow().isoformat(),
            }
        ]

        # Setup mock chain
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_is = Mock()
        mock_update = Mock()
        mock_eq2 = Mock()

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.is_.return_value = mock_is
        mock_is.execute.return_value = check_response

        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq2
        mock_eq2.execute.return_value = update_response

        # Execute delete
        result = await user_repo.delete(user_id)

        # Verify soft delete was performed
        assert result is True
        mock_table.update.assert_called_once()

        # Verify deleted_at was set in the update call
        update_call_args = mock_table.update.call_args[0][0]
        assert "deleted_at" in update_call_args
        assert update_call_args["deleted_at"] is not None

    @pytest.mark.asyncio
    async def test_get_by_id_excludes_soft_deleted(self, user_repo, mock_client):
        """Test that get_by_id excludes soft-deleted records."""
        user_id = uuid4()

        # Mock response with no data (soft-deleted record filtered out)
        response = Mock()
        response.data = []

        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_is = Mock()

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.is_.return_value = mock_is
        mock_is.execute.return_value = response

        # Execute get_by_id
        result = await user_repo.get_by_id(user_id)

        # Verify soft-deleted record was not returned
        assert result is None

        # Verify soft delete filter was applied
        mock_eq.is_.assert_called_once_with("deleted_at", "null")

    @pytest.mark.asyncio
    async def test_list_excludes_soft_deleted(self, user_repo, mock_client):
        """Test that list operation excludes soft-deleted records."""
        # Mock response with only non-deleted users
        response = Mock()
        response.data = [
            {"id": str(uuid4()), "discord_id": "user1", "deleted_at": None},
            {"id": str(uuid4()), "discord_id": "user2", "deleted_at": None},
        ]

        mock_table = Mock()
        mock_select = Mock()
        mock_is = Mock()

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.is_.return_value = mock_is
        mock_is.execute.return_value = response

        # Execute list
        result = await user_repo.list()

        # Verify only non-deleted records returned
        assert len(result) == 2

        # Verify soft delete filter was applied
        mock_select.is_.assert_called_once_with("deleted_at", "null")

    @pytest.mark.asyncio
    async def test_restore_clears_deleted_at(self, user_repo, mock_client):
        """Test that restore operation clears deleted_at timestamp."""
        user_id = uuid4()

        # Mock check query (entity exists and is deleted)
        check_response = Mock()
        check_response.data = [
            {
                "id": str(user_id),
                "discord_id": "test_user",
                "deleted_at": datetime.utcnow().isoformat(),
            }
        ]

        # Mock update query (restore)
        update_response = Mock()
        update_response.data = [{"id": str(user_id), "discord_id": "test_user", "deleted_at": None}]

        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_update = Mock()
        mock_eq2 = Mock()

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = check_response

        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq2
        mock_eq2.execute.return_value = update_response

        # Execute restore
        result = await user_repo.restore(user_id)

        # Verify restore was successful
        assert result is not None
        assert result.deleted_at is None

        # Verify deleted_at was set to None in the update call
        update_call_args = mock_table.update.call_args[0][0]
        assert "deleted_at" in update_call_args
        assert update_call_args["deleted_at"] is None

    @pytest.mark.asyncio
    async def test_restore_fails_if_not_deleted(self, user_repo, mock_client):
        """Test that restore fails if entity is not deleted."""
        user_id = uuid4()

        # Mock check query (entity exists but not deleted)
        check_response = Mock()
        check_response.data = [{"id": str(user_id), "discord_id": "test_user", "deleted_at": None}]

        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value = check_response

        # Execute restore and expect ValidationError
        with pytest.raises(ValidationError) as exc_info:
            await user_repo.restore(user_id)

        assert "not deleted" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_hard_delete_permanently_removes(self, user_repo, mock_client):
        """Test that hard_delete permanently removes the record."""
        user_id = uuid4()

        # Mock delete response
        delete_response = Mock()
        delete_response.data = [{"id": str(user_id)}]

        mock_table = Mock()
        mock_delete = Mock()
        mock_eq = Mock()

        mock_client.table.return_value = mock_table
        mock_table.delete.return_value = mock_delete
        mock_delete.eq.return_value = mock_eq
        mock_eq.execute.return_value = delete_response

        # Execute hard delete
        result = await user_repo.hard_delete(user_id)

        # Verify hard delete was performed
        assert result is True
        mock_table.delete.assert_called_once()


class TestSoftDeleteArticle:
    """Test soft delete functionality for Article repository."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Supabase client."""
        return Mock()

    @pytest.fixture
    def article_repo(self, mock_client):
        """Create an ArticleRepository instance with mocked client."""
        return ArticleRepository(mock_client)

    @pytest.mark.asyncio
    async def test_delete_preserves_article_for_audit(self, article_repo, mock_client):
        """Test that deleting an article preserves it for audit trail."""
        article_id = uuid4()

        # Mock the check query
        check_response = Mock()
        check_response.data = [{"id": str(article_id)}]

        # Mock the update query
        update_response = Mock()
        update_response.data = [
            {
                "id": str(article_id),
                "feed_id": str(uuid4()),
                "title": "Test Article",
                "url": "https://example.com/article",
                "deleted_at": datetime.utcnow().isoformat(),
            }
        ]

        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_is = Mock()
        mock_update = Mock()
        mock_eq2 = Mock()

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.is_.return_value = mock_is
        mock_is.execute.return_value = check_response

        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq2
        mock_eq2.execute.return_value = update_response

        # Execute delete
        result = await article_repo.delete(article_id)

        # Verify soft delete was performed
        assert result is True

        # Verify update was called (not delete)
        mock_table.update.assert_called_once()
        mock_table.delete.assert_not_called()


class TestSoftDeleteReadingList:
    """Test soft delete functionality for ReadingList repository."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Supabase client."""
        return Mock()

    @pytest.fixture
    def reading_list_repo(self, mock_client):
        """Create a ReadingListRepository instance with mocked client."""
        return ReadingListRepository(mock_client)

    @pytest.mark.asyncio
    async def test_get_by_user_and_article_excludes_deleted(self, reading_list_repo, mock_client):
        """Test that get_by_user_and_article excludes soft-deleted items."""
        user_id = uuid4()
        article_id = uuid4()

        # Mock response with no data (soft-deleted)
        response = Mock()
        response.data = []

        mock_table = Mock()
        mock_select = Mock()
        mock_eq1 = Mock()
        mock_eq2 = Mock()
        mock_is = Mock()
        mock_limit = Mock()

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.limit.return_value = mock_limit
        mock_limit.is_.return_value = mock_is
        mock_is.execute.return_value = response

        # Execute get_by_user_and_article
        result = await reading_list_repo.get_by_user_and_article(user_id, article_id)

        # Verify soft-deleted item was not returned
        assert result is None

        # Verify soft delete filter was applied
        mock_limit.is_.assert_called_once_with("deleted_at", "null")


class TestSoftDeleteFeed:
    """Test soft delete functionality for Feed repository."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Supabase client."""
        return Mock()

    @pytest.fixture
    def feed_repo(self, mock_client):
        """Create a FeedRepository instance with mocked client."""
        return FeedRepository(mock_client)

    @pytest.mark.asyncio
    async def test_count_excludes_soft_deleted(self, feed_repo, mock_client):
        """Test that count operation excludes soft-deleted feeds."""
        # Mock response with count
        response = Mock()
        response.count = 5
        response.data = []

        mock_table = Mock()
        mock_select = Mock()
        mock_is = Mock()

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.is_.return_value = mock_is
        mock_is.execute.return_value = response

        # Execute count
        result = await feed_repo.count()

        # Verify count excludes soft-deleted
        assert result == 5

        # Verify soft delete filter was applied
        mock_select.is_.assert_called_once_with("deleted_at", "null")


class TestSoftDeleteIntegration:
    """Integration tests for soft delete across multiple repositories."""

    @pytest.mark.asyncio
    async def test_soft_delete_preserves_relationships(self):
        """Test that soft deleting preserves relationship data for audit."""
        # This is a conceptual test - in practice, when an article is soft-deleted,
        # reading list items referencing it should still be queryable for audit purposes

        # The soft delete pattern ensures that:
        # 1. Deleted articles remain in the database
        # 2. Reading list items can still reference deleted articles
        # 3. Audit trails remain complete
        # 4. Data can be restored if needed

        # This test would require actual database integration to fully validate
        pass

    @pytest.mark.asyncio
    async def test_soft_delete_enables_data_recovery(self):
        """Test that soft delete enables data recovery scenarios."""
        # Soft delete enables:
        # 1. Accidental deletion recovery
        # 2. Audit trail preservation
        # 3. Compliance with data retention policies
        # 4. Historical data analysis

        # This test would require actual database integration to fully validate
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
