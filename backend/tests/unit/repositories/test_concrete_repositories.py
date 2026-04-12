"""
Unit tests for concrete repository implementations

Tests the User, Article, ReadingList, and Feed repositories including
validation, entity mapping, and repository-specific methods.

Validates: Requirements 3.2, 3.4, 15.4
"""

from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.errors import DatabaseError, ErrorCode, ValidationError
from app.repositories.article import Article, ArticleRepository, PaginationMetadata
from app.repositories.feed import Feed, FeedRepository
from app.repositories.reading_list import ReadingListItem, ReadingListRepository
from app.repositories.user import User, UserRepository


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client."""
    client = Mock()
    client.table = Mock(return_value=client)
    return client


class TestUserRepository:
    """Tests for UserRepository."""

    @pytest.fixture
    def user_repository(self, mock_supabase_client):
        """Create a user repository instance."""
        return UserRepository(mock_supabase_client)

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_repository, mock_supabase_client):
        """Test successful user creation."""
        # Arrange
        user_id = uuid4()
        data = {"discord_id": "123456789"}

        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(user_id),
                "discord_id": "123456789",
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
        assert result.discord_id == "123456789"
        assert result.dm_notifications_enabled is True

    @pytest.mark.asyncio
    async def test_create_user_missing_discord_id(self, user_repository):
        """Test user creation with missing discord_id."""
        # Arrange
        data = {}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_repository.create(data)

        assert "discord_id" in str(exc_info.value)
        assert exc_info.value.error_code == ErrorCode.VALIDATION_MISSING_FIELD

    @pytest.mark.asyncio
    async def test_create_user_empty_discord_id(self, user_repository):
        """Test user creation with empty discord_id."""
        # Arrange
        data = {"discord_id": "   "}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_repository.create(data)

        assert "discord_id" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_by_discord_id(self, user_repository, mock_supabase_client):
        """Test retrieving user by discord_id."""
        # Arrange
        user_id = uuid4()

        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(user_id),
                "discord_id": "123456789",
                "dm_notifications_enabled": True,
                "created_at": datetime.utcnow().isoformat(),
            }
        ]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await user_repository.get_by_discord_id("123456789")

        # Assert
        assert result is not None
        assert result.discord_id == "123456789"


class TestArticleRepository:
    """Tests for ArticleRepository."""

    @pytest.fixture
    def article_repository(self, mock_supabase_client):
        """Create an article repository instance."""
        return ArticleRepository(mock_supabase_client)

    @pytest.mark.asyncio
    async def test_create_article_success(self, article_repository, mock_supabase_client):
        """Test successful article creation."""
        # Arrange
        article_id = uuid4()
        feed_id = uuid4()
        data = {
            "feed_id": feed_id,
            "title": "Test Article",
            "url": "https://example.com/article",
            "tinkering_index": 3,
        }

        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(article_id),
                "feed_id": str(feed_id),
                "title": "Test Article",
                "url": "https://example.com/article",
                "tinkering_index": 3,
                "created_at": datetime.utcnow().isoformat(),
            }
        ]

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await article_repository.create(data)

        # Assert
        assert isinstance(result, Article)
        assert result.title == "Test Article"
        assert result.tinkering_index == 3

    @pytest.mark.asyncio
    async def test_create_article_missing_required_fields(self, article_repository):
        """Test article creation with missing required fields."""
        # Arrange
        data = {"title": "Test"}  # Missing feed_id and url

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await article_repository.create(data)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_MISSING_FIELD

    @pytest.mark.asyncio
    async def test_create_article_invalid_tinkering_index(self, article_repository):
        """Test article creation with invalid tinkering_index."""
        # Arrange
        data = {
            "feed_id": uuid4(),
            "title": "Test",
            "url": "https://example.com",
            "tinkering_index": 10,  # Invalid: must be 1-5
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await article_repository.create(data)

        assert "tinkering_index" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_with_pagination(self, article_repository, mock_supabase_client):
        """Test listing articles with pagination."""
        # Arrange
        mock_count_response = Mock()
        mock_count_response.count = 50

        mock_list_response = Mock()
        mock_list_response.data = [
            {
                "id": str(uuid4()),
                "feed_id": str(uuid4()),
                "title": f"Article {i}",
                "url": f"https://example.com/{i}",
                "created_at": datetime.utcnow().isoformat(),
            }
            for i in range(20)
        ]

        # Mock count call
        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.offset = Mock(return_value=mock_supabase_client)
        mock_supabase_client.order = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(side_effect=[mock_count_response, mock_list_response])

        # Act
        articles, metadata = await article_repository.list_with_pagination(page=1, page_size=20)

        # Assert
        assert len(articles) == 20
        assert isinstance(metadata, PaginationMetadata)
        assert metadata.page == 1
        assert metadata.page_size == 20
        assert metadata.total_count == 50
        assert metadata.has_next_page is True
        assert metadata.has_previous_page is False


class TestReadingListRepository:
    """Tests for ReadingListRepository."""

    @pytest.fixture
    def reading_list_repository(self, mock_supabase_client):
        """Create a reading list repository instance."""
        return ReadingListRepository(mock_supabase_client)

    @pytest.mark.asyncio
    async def test_create_reading_list_item_success(
        self, reading_list_repository, mock_supabase_client
    ):
        """Test successful reading list item creation."""
        # Arrange
        item_id = uuid4()
        user_id = uuid4()
        article_id = uuid4()
        data = {"user_id": user_id, "article_id": article_id, "status": "Unread"}

        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(item_id),
                "user_id": str(user_id),
                "article_id": str(article_id),
                "status": "Unread",
                "rating": None,
                "added_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        ]

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await reading_list_repository.create(data)

        # Assert
        assert isinstance(result, ReadingListItem)
        assert result.status == "Unread"
        assert result.rating is None

    @pytest.mark.asyncio
    async def test_create_reading_list_item_invalid_status(self, reading_list_repository):
        """Test reading list item creation with invalid status."""
        # Arrange
        data = {"user_id": uuid4(), "article_id": uuid4(), "status": "InvalidStatus"}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await reading_list_repository.create(data)

        assert "status" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_reading_list_item_invalid_rating(self, reading_list_repository):
        """Test reading list item creation with invalid rating."""
        # Arrange
        data = {
            "user_id": uuid4(),
            "article_id": uuid4(),
            "status": "Read",
            "rating": 10,  # Invalid: must be 1-5
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await reading_list_repository.create(data)

        assert "rating" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_rating_allows_null(self, reading_list_repository):
        """Test that update_rating validation allows None to clear rating."""
        # Arrange
        data = {"rating": None}

        # Act
        validated = reading_list_repository._validate_update_data(data)

        # Assert
        assert validated["rating"] is None


class TestFeedRepository:
    """Tests for FeedRepository."""

    @pytest.fixture
    def feed_repository(self, mock_supabase_client):
        """Create a feed repository instance."""
        return FeedRepository(mock_supabase_client)

    @pytest.mark.asyncio
    async def test_create_feed_success(self, feed_repository, mock_supabase_client):
        """Test successful feed creation."""
        # Arrange
        feed_id = uuid4()
        data = {
            "name": "Tech News",
            "url": "https://example.com/feed.xml",
            "category": "Technology",
        }

        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(feed_id),
                "name": "Tech News",
                "url": "https://example.com/feed.xml",
                "category": "Technology",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
            }
        ]

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await feed_repository.create(data)

        # Assert
        assert isinstance(result, Feed)
        assert result.name == "Tech News"
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_create_feed_invalid_url(self, feed_repository):
        """Test feed creation with invalid URL."""
        # Arrange
        data = {"name": "Test Feed", "url": "not-a-valid-url", "category": "Test"}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await feed_repository.create(data)

        assert "url" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_deactivate_feed(self, feed_repository, mock_supabase_client):
        """Test feed deactivation."""
        # Arrange
        feed_id = uuid4()

        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(feed_id),
                "name": "Test Feed",
                "url": "https://example.com/feed.xml",
                "category": "Test",
                "is_active": False,
                "created_at": datetime.utcnow().isoformat(),
            }
        ]

        mock_supabase_client.update = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await feed_repository.deactivate(feed_id)

        # Assert
        assert result.is_active is False
        mock_supabase_client.update.assert_called_once_with({"is_active": False})


class TestPaginationMetadata:
    """Tests for PaginationMetadata."""

    def test_pagination_metadata_to_dict(self):
        """Test converting pagination metadata to dictionary."""
        # Arrange
        metadata = PaginationMetadata(
            page=2, page_size=20, total_count=100, has_next_page=True, has_previous_page=True
        )

        # Act
        result = metadata.to_dict()

        # Assert
        assert result == {
            "page": 2,
            "page_size": 20,
            "total_count": 100,
            "has_next_page": True,
            "has_previous_page": True,
        }


class TestUserRepositoryDatabaseFailures:
    """Tests for UserRepository database failure scenarios."""

    @pytest.fixture
    def user_repository(self, mock_supabase_client):
        """Create a user repository instance."""
        return UserRepository(mock_supabase_client)

    @pytest.mark.asyncio
    async def test_create_user_database_error(self, user_repository, mock_supabase_client):
        """Test user creation with database error."""
        # Arrange
        data = {"discord_id": "123456789"}

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(side_effect=Exception("connection timeout"))

        # Act & Assert
        with pytest.raises(DatabaseError):
            await user_repository.create(data)

    @pytest.mark.asyncio
    async def test_update_user_invalid_type(self, user_repository):
        """Test user update with invalid dm_notifications_enabled type."""
        # Arrange
        entity_id = uuid4()
        data = {"dm_notifications_enabled": "not_a_boolean"}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await user_repository.update(entity_id, data)

        assert "dm_notifications_enabled" in str(exc_info.value)
        assert "boolean" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_exists_by_discord_id_true(self, user_repository, mock_supabase_client):
        """Test exists_by_discord_id when user exists."""
        # Arrange
        user_id = uuid4()

        mock_response = Mock()
        mock_response.data = [
            {"id": str(user_id), "discord_id": "123456789", "dm_notifications_enabled": True}
        ]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await user_repository.exists_by_discord_id("123456789")

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_by_discord_id_false(self, user_repository, mock_supabase_client):
        """Test exists_by_discord_id when user does not exist."""
        # Arrange
        mock_response = Mock()
        mock_response.data = []

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await user_repository.exists_by_discord_id("nonexistent")

        # Assert
        assert result is False


class TestArticleRepositoryAdvanced:
    """Advanced tests for ArticleRepository."""

    @pytest.fixture
    def article_repository(self, mock_supabase_client):
        """Create an article repository instance."""
        return ArticleRepository(mock_supabase_client)

    @pytest.mark.asyncio
    async def test_create_article_title_too_long(self, article_repository):
        """Test article creation with title exceeding max length."""
        # Arrange
        data = {
            "feed_id": uuid4(),
            "title": "x" * 2001,  # Exceeds 2000 character limit
            "url": "https://example.com",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await article_repository.create(data)

        assert "title" in str(exc_info.value)
        assert "2000" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_article_ai_summary_too_long(self, article_repository):
        """Test article creation with ai_summary exceeding max length."""
        # Arrange
        data = {
            "feed_id": uuid4(),
            "title": "Test",
            "url": "https://example.com",
            "ai_summary": "x" * 5001,  # Exceeds 5000 character limit
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await article_repository.create(data)

        assert "ai_summary" in str(exc_info.value)
        assert "5000" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_article_title_too_long(self, article_repository):
        """Test article update with title exceeding max length."""
        # Arrange
        entity_id = uuid4()
        data = {"title": "x" * 2001}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await article_repository.update(entity_id, data)

        assert "title" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_with_pagination_invalid_page(self, article_repository):
        """Test list_with_pagination with invalid page number."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await article_repository.list_with_pagination(page=0)

        assert "page" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_with_pagination_invalid_page_size(self, article_repository):
        """Test list_with_pagination with invalid page size."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await article_repository.list_with_pagination(page_size=101)

        assert "page_size" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_with_pagination_last_page(self, article_repository, mock_supabase_client):
        """Test pagination metadata on last page."""
        # Arrange
        mock_count_response = Mock()
        mock_count_response.count = 45

        mock_list_response = Mock()
        mock_list_response.data = [
            {
                "id": str(uuid4()),
                "feed_id": str(uuid4()),
                "title": f"Article {i}",
                "url": f"https://example.com/{i}",
                "created_at": datetime.utcnow().isoformat(),
            }
            for i in range(5)
        ]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.offset = Mock(return_value=mock_supabase_client)
        mock_supabase_client.order = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(side_effect=[mock_count_response, mock_list_response])

        # Act
        articles, metadata = await article_repository.list_with_pagination(page=3, page_size=20)

        # Assert
        assert len(articles) == 5
        assert metadata.page == 3
        assert metadata.has_next_page is False
        assert metadata.has_previous_page is True

    @pytest.mark.asyncio
    async def test_list_by_feed(self, article_repository, mock_supabase_client):
        """Test listing articles by feed."""
        # Arrange
        feed_id = uuid4()

        mock_count_response = Mock()
        mock_count_response.count = 10

        mock_list_response = Mock()
        mock_list_response.data = [
            {
                "id": str(uuid4()),
                "feed_id": str(feed_id),
                "title": f"Article {i}",
                "url": f"https://example.com/{i}",
                "created_at": datetime.utcnow().isoformat(),
            }
            for i in range(10)
        ]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.offset = Mock(return_value=mock_supabase_client)
        mock_supabase_client.order = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(side_effect=[mock_count_response, mock_list_response])

        # Act
        articles, metadata = await article_repository.list_by_feed(feed_id)

        # Assert
        assert len(articles) == 10
        assert all(article.feed_id == feed_id for article in articles)

    @pytest.mark.asyncio
    async def test_get_by_url(self, article_repository, mock_supabase_client):
        """Test retrieving article by URL."""
        # Arrange
        article_id = uuid4()
        feed_id = uuid4()

        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(article_id),
                "feed_id": str(feed_id),
                "title": "Test Article",
                "url": "https://example.com/article",
                "created_at": datetime.utcnow().isoformat(),
            }
        ]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await article_repository.get_by_url("https://example.com/article")

        # Assert
        assert result is not None
        assert result.url == "https://example.com/article"


class TestReadingListRepositoryAdvanced:
    """Advanced tests for ReadingListRepository."""

    @pytest.fixture
    def reading_list_repository(self, mock_supabase_client):
        """Create a reading list repository instance."""
        return ReadingListRepository(mock_supabase_client)

    @pytest.mark.asyncio
    async def test_get_by_user_and_article_not_found(
        self, reading_list_repository, mock_supabase_client
    ):
        """Test get_by_user_and_article when item not found."""
        # Arrange
        user_id = uuid4()
        article_id = uuid4()

        mock_response = Mock()
        mock_response.data = []

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await reading_list_repository.get_by_user_and_article(user_id, article_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_list_by_user_with_status_filter(
        self, reading_list_repository, mock_supabase_client
    ):
        """Test listing reading list items with status filter."""
        # Arrange
        user_id = uuid4()

        mock_count_response = Mock()
        mock_count_response.count = 5

        mock_list_response = Mock()
        mock_list_response.data = [
            {
                "id": str(uuid4()),
                "user_id": str(user_id),
                "article_id": str(uuid4()),
                "status": "Read",
                "rating": None,
                "added_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            for _ in range(5)
        ]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.offset = Mock(return_value=mock_supabase_client)
        mock_supabase_client.order = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(side_effect=[mock_count_response, mock_list_response])

        # Act
        items, metadata = await reading_list_repository.list_by_user_with_pagination(
            user_id=user_id, status="Read"
        )

        # Assert
        assert len(items) == 5
        assert all(item.status == "Read" for item in items)

    @pytest.mark.asyncio
    async def test_list_by_user_with_rating_filter(
        self, reading_list_repository, mock_supabase_client
    ):
        """Test listing reading list items with rating filter."""
        # Arrange
        user_id = uuid4()

        mock_count_response = Mock()
        mock_count_response.count = 3

        mock_list_response = Mock()
        mock_list_response.data = [
            {
                "id": str(uuid4()),
                "user_id": str(user_id),
                "article_id": str(uuid4()),
                "status": "Read",
                "rating": 5,
                "added_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            for _ in range(3)
        ]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.offset = Mock(return_value=mock_supabase_client)
        mock_supabase_client.order = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(side_effect=[mock_count_response, mock_list_response])

        # Act
        items, metadata = await reading_list_repository.list_by_user_with_pagination(
            user_id=user_id, rating=5
        )

        # Assert
        assert len(items) == 3
        assert all(item.rating == 5 for item in items)

    @pytest.mark.asyncio
    async def test_list_by_user_invalid_status_filter(self, reading_list_repository):
        """Test listing with invalid status filter."""
        # Arrange
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await reading_list_repository.list_by_user_with_pagination(
                user_id=user_id, status="InvalidStatus"
            )

        assert "status" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_by_user_invalid_rating_filter(self, reading_list_repository):
        """Test listing with invalid rating filter."""
        # Arrange
        user_id = uuid4()

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await reading_list_repository.list_by_user_with_pagination(user_id=user_id, rating=10)

        assert "rating" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_status_not_found(self, reading_list_repository, mock_supabase_client):
        """Test update_status when item not found."""
        # Arrange
        user_id = uuid4()
        article_id = uuid4()

        mock_response = Mock()
        mock_response.data = []

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act & Assert
        from app.core.errors import NotFoundError

        with pytest.raises(NotFoundError):
            await reading_list_repository.update_status(user_id, article_id, "Read")

    @pytest.mark.asyncio
    async def test_update_rating_not_found(self, reading_list_repository, mock_supabase_client):
        """Test update_rating when item not found."""
        # Arrange
        user_id = uuid4()
        article_id = uuid4()

        mock_response = Mock()
        mock_response.data = []

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act & Assert
        from app.core.errors import NotFoundError

        with pytest.raises(NotFoundError):
            await reading_list_repository.update_rating(user_id, article_id, 5)


class TestFeedRepositoryAdvanced:
    """Advanced tests for FeedRepository."""

    @pytest.fixture
    def feed_repository(self, mock_supabase_client):
        """Create a feed repository instance."""
        return FeedRepository(mock_supabase_client)

    @pytest.mark.asyncio
    async def test_create_feed_missing_fields(self, feed_repository):
        """Test feed creation with missing required fields."""
        # Arrange
        data = {"name": "Test"}  # Missing url and category

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await feed_repository.create(data)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_MISSING_FIELD

    @pytest.mark.asyncio
    async def test_create_feed_empty_name(self, feed_repository):
        """Test feed creation with empty name."""
        # Arrange
        data = {"name": "   ", "url": "https://example.com/feed.xml", "category": "Test"}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await feed_repository.create(data)

        assert "name" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_feed_invalid_url(self, feed_repository):
        """Test feed update with invalid URL."""
        # Arrange
        entity_id = uuid4()
        data = {"url": "not-a-valid-url"}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await feed_repository.update(entity_id, data)

        assert "url" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_feed_invalid_is_active_type(self, feed_repository):
        """Test feed update with invalid is_active type."""
        # Arrange
        entity_id = uuid4()
        data = {"is_active": "not_a_boolean"}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await feed_repository.update(entity_id, data)

        assert "is_active" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_active_feeds(self, feed_repository, mock_supabase_client):
        """Test listing active feeds."""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(uuid4()),
                "name": f"Feed {i}",
                "url": f"https://example.com/feed{i}.xml",
                "category": "Tech",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
            }
            for i in range(5)
        ]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.offset = Mock(return_value=mock_supabase_client)
        mock_supabase_client.order = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await feed_repository.list_active_feeds()

        # Assert
        assert len(result) == 5
        assert all(feed.is_active for feed in result)

    @pytest.mark.asyncio
    async def test_list_by_category(self, feed_repository, mock_supabase_client):
        """Test listing feeds by category."""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(uuid4()),
                "name": f"Feed {i}",
                "url": f"https://example.com/feed{i}.xml",
                "category": "Technology",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
            }
            for i in range(3)
        ]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.order = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await feed_repository.list_by_category("Technology")

        # Assert
        assert len(result) == 3
        assert all(feed.category == "Technology" for feed in result)

    @pytest.mark.asyncio
    async def test_list_by_category_include_inactive(self, feed_repository, mock_supabase_client):
        """Test listing feeds by category including inactive."""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(uuid4()),
                "name": "Active Feed",
                "url": "https://example.com/feed1.xml",
                "category": "Tech",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
            },
            {
                "id": str(uuid4()),
                "name": "Inactive Feed",
                "url": "https://example.com/feed2.xml",
                "category": "Tech",
                "is_active": False,
                "created_at": datetime.utcnow().isoformat(),
            },
        ]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.order = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await feed_repository.list_by_category("Tech", include_inactive=True)

        # Assert
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_activate_feed(self, feed_repository, mock_supabase_client):
        """Test feed activation."""
        # Arrange
        feed_id = uuid4()

        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(feed_id),
                "name": "Test Feed",
                "url": "https://example.com/feed.xml",
                "category": "Test",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
            }
        ]

        mock_supabase_client.update = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await feed_repository.activate(feed_id)

        # Assert
        assert result.is_active is True
        mock_supabase_client.update.assert_called_once_with({"is_active": True})

    @pytest.mark.asyncio
    async def test_get_by_url(self, feed_repository, mock_supabase_client):
        """Test retrieving feed by URL."""
        # Arrange
        feed_id = uuid4()

        mock_response = Mock()
        mock_response.data = [
            {
                "id": str(feed_id),
                "name": "Test Feed",
                "url": "https://example.com/feed.xml",
                "category": "Test",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
            }
        ]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await feed_repository.get_by_url("https://example.com/feed.xml")

        # Assert
        assert result is not None
        assert result.url == "https://example.com/feed.xml"
