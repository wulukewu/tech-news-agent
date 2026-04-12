"""
Unit tests for audit trail functionality

Tests the automatic tracking of created_at, updated_at, and modified_by fields
in repository operations.

Validates: Requirements 14.1, 14.4
"""

from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.repositories.article import Article, ArticleRepository
from app.repositories.feed import Feed, FeedRepository
from app.repositories.user import User, UserRepository


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client."""
    client = Mock()
    client.table = Mock(return_value=client)
    return client


class TestAuditTrailTracking:
    """Tests for audit trail field tracking."""

    @pytest.fixture
    def user_repository(self, mock_supabase_client):
        """Create a user repository instance."""
        return UserRepository(mock_supabase_client)

    @pytest.mark.asyncio
    async def test_create_with_current_user_sets_modified_by(
        self, user_repository, mock_supabase_client
    ):
        """Test that create operation includes modified_by when current user is set."""
        # Arrange
        user_id = uuid4()
        current_user = "discord_user_123456789"
        data = {"discord_id": "new_user_987654321"}

        # Set current user for audit tracking
        user_repository.set_current_user(current_user)

        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(user_id),
                "discord_id": "new_user_987654321",
                "dm_notifications_enabled": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "modified_by": current_user,
            }
        ]

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await user_repository.create(data)

        # Assert
        assert isinstance(result, User)
        assert result.modified_by == current_user

        # Verify that modified_by was included in the insert call
        insert_call = mock_supabase_client.insert.call_args
        inserted_data = insert_call[0][0]
        assert inserted_data["modified_by"] == current_user

    @pytest.mark.asyncio
    async def test_create_without_current_user_no_modified_by(
        self, user_repository, mock_supabase_client
    ):
        """Test that create operation works without modified_by when current user is not set."""
        # Arrange
        user_id = uuid4()
        data = {"discord_id": "new_user_987654321"}

        # Do NOT set current user

        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(user_id),
                "discord_id": "new_user_987654321",
                "dm_notifications_enabled": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "modified_by": None,
            }
        ]

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await user_repository.create(data)

        # Assert
        assert isinstance(result, User)
        assert result.modified_by is None

        # Verify that modified_by was NOT included in the insert call
        insert_call = mock_supabase_client.insert.call_args
        inserted_data = insert_call[0][0]
        assert "modified_by" not in inserted_data

    @pytest.mark.asyncio
    async def test_update_with_current_user_sets_modified_by(
        self, user_repository, mock_supabase_client
    ):
        """Test that update operation includes modified_by when current user is set."""
        # Arrange
        user_id = uuid4()
        current_user = "discord_user_123456789"
        update_data = {"dm_notifications_enabled": False}

        # Set current user for audit tracking
        user_repository.set_current_user(current_user)

        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(user_id),
                "discord_id": "existing_user",
                "dm_notifications_enabled": False,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "modified_by": current_user,
            }
        ]

        mock_supabase_client.update = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await user_repository.update(user_id, update_data)

        # Assert
        assert isinstance(result, User)
        assert result.modified_by == current_user

        # Verify that modified_by was included in the update call
        update_call = mock_supabase_client.update.call_args
        updated_data = update_call[0][0]
        assert updated_data["modified_by"] == current_user

    @pytest.mark.asyncio
    async def test_get_current_user(self, user_repository):
        """Test getting the current user."""
        # Arrange
        current_user = "discord_user_123456789"

        # Act
        user_repository.set_current_user(current_user)
        result = user_repository.get_current_user()

        # Assert
        assert result == current_user

    @pytest.mark.asyncio
    async def test_set_current_user_to_none(self, user_repository):
        """Test setting current user to None for system operations."""
        # Arrange & Act
        user_repository.set_current_user("user_123")
        user_repository.set_current_user(None)
        result = user_repository.get_current_user()

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_audit_trail_disabled(self, mock_supabase_client):
        """Test that audit trail can be disabled."""
        # Arrange
        user_id = uuid4()
        data = {"discord_id": "new_user_987654321"}

        # Create repository with audit trail disabled
        user_repository = UserRepository(mock_supabase_client)
        user_repository.enable_audit_trail = False
        user_repository.set_current_user("discord_user_123456789")

        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(user_id),
                "discord_id": "new_user_987654321",
                "dm_notifications_enabled": True,
                "created_at": datetime.utcnow().isoformat(),
            }
        ]

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await user_repository.create(data)

        # Assert
        assert isinstance(result, User)

        # Verify that modified_by was NOT included even though current user was set
        insert_call = mock_supabase_client.insert.call_args
        inserted_data = insert_call[0][0]
        assert "modified_by" not in inserted_data


class TestAuditTrailAcrossRepositories:
    """Tests to verify audit trail works across different repository types."""

    @pytest.fixture
    def article_repository(self, mock_supabase_client):
        """Create an article repository instance."""
        return ArticleRepository(mock_supabase_client)

    @pytest.fixture
    def feed_repository(self, mock_supabase_client):
        """Create a feed repository instance."""
        return FeedRepository(mock_supabase_client)

    @pytest.mark.asyncio
    async def test_article_repository_audit_trail(self, article_repository, mock_supabase_client):
        """Test audit trail in ArticleRepository."""
        # Arrange
        article_id = uuid4()
        feed_id = uuid4()
        current_user = "discord_user_123456789"
        data = {
            "feed_id": str(feed_id),
            "title": "Test Article",
            "url": "https://example.com/article",
        }

        article_repository.set_current_user(current_user)

        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(article_id),
                "feed_id": str(feed_id),
                "title": "Test Article",
                "url": "https://example.com/article",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "modified_by": current_user,
            }
        ]

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await article_repository.create(data)

        # Assert
        assert isinstance(result, Article)
        assert result.modified_by == current_user

    @pytest.mark.asyncio
    async def test_feed_repository_audit_trail(self, feed_repository, mock_supabase_client):
        """Test audit trail in FeedRepository."""
        # Arrange
        feed_id = uuid4()
        current_user = "discord_user_123456789"
        data = {
            "name": "Test Feed",
            "url": "https://example.com/feed.xml",
            "category": "Technology",
        }

        feed_repository.set_current_user(current_user)

        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(feed_id),
                "name": "Test Feed",
                "url": "https://example.com/feed.xml",
                "category": "Technology",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "modified_by": current_user,
            }
        ]

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await feed_repository.create(data)

        # Assert
        assert isinstance(result, Feed)
        assert result.modified_by == current_user

    @pytest.mark.asyncio
    async def test_system_operations_use_system_identifier(
        self, feed_repository, mock_supabase_client
    ):
        """Test that system operations can use a system identifier."""
        # Arrange
        feed_id = uuid4()
        system_identifier = "system"
        data = {
            "name": "Test Feed",
            "url": "https://example.com/feed.xml",
            "category": "Technology",
        }

        feed_repository.set_current_user(system_identifier)

        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(feed_id),
                "name": "Test Feed",
                "url": "https://example.com/feed.xml",
                "category": "Technology",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "modified_by": system_identifier,
            }
        ]

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await feed_repository.create(data)

        # Assert
        assert isinstance(result, Feed)
        assert result.modified_by == system_identifier
