"""
Unit tests for BaseRepository

Tests the base repository implementation including CRUD operations,
error handling, and query patterns.

Validates: Requirements 3.1, 3.2, 3.4
"""

from typing import Any
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from app.core.errors import DatabaseError, ErrorCode, NotFoundError, ValidationError
from app.repositories.base import BaseRepository


# Test entity class for repository testing
class TestEntity:
    """Simple test entity for repository tests."""

    def __init__(self, id: UUID, name: str, value: int):
        self.id = id
        self.name = name
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, TestEntity):
            return False
        return self.id == other.id and self.name == other.name and self.value == other.value


# Concrete repository implementation for testing
class TestRepository(BaseRepository[TestEntity]):
    """Test repository implementation."""

    def _map_to_entity(self, row: dict[str, Any]) -> TestEntity:
        """Map database row to TestEntity."""
        return TestEntity(id=UUID(row["id"]), name=row["name"], value=row["value"])

    def _validate_create_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate create data."""
        if "name" not in data:
            raise ValidationError(
                "Missing required field: name", error_code=ErrorCode.VALIDATION_MISSING_FIELD
            )
        return data

    def _validate_update_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate update data."""
        if "value" in data and not isinstance(data["value"], int):
            raise ValidationError(
                "Invalid field type: value must be integer",
                error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
            )
        return data


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client."""
    client = Mock()
    client.table = Mock(return_value=client)
    return client


@pytest.fixture
def test_repository(mock_supabase_client):
    """Create a test repository instance."""
    return TestRepository(mock_supabase_client, "test_entities")


class TestBaseRepositoryCreate:
    """Tests for create operation."""

    @pytest.mark.asyncio
    async def test_create_success(self, test_repository, mock_supabase_client):
        """Test successful entity creation."""
        # Arrange
        entity_id = uuid4()
        data = {"name": "test", "value": 42}

        mock_response = Mock()
        mock_response.data = [{"id": str(entity_id), "name": "test", "value": 42}]

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await test_repository.create(data)

        # Assert
        assert isinstance(result, TestEntity)
        assert result.id == entity_id
        assert result.name == "test"
        assert result.value == 42

        mock_supabase_client.table.assert_called_once_with("test_entities")
        mock_supabase_client.insert.assert_called_once_with(data)
        mock_supabase_client.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_validation_error(self, test_repository):
        """Test create with validation error."""
        # Arrange
        data = {"value": 42}  # Missing required 'name' field

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await test_repository.create(data)

        assert "Missing required field: name" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_no_data_returned(self, test_repository, mock_supabase_client):
        """Test create when no data is returned."""
        # Arrange
        data = {"name": "test", "value": 42}

        mock_response = Mock()
        mock_response.data = []

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await test_repository.create(data)

        assert "No data returned" in str(exc_info.value)


class TestBaseRepositoryGetById:
    """Tests for get_by_id operation."""

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, test_repository, mock_supabase_client):
        """Test successful entity retrieval by ID."""
        # Arrange
        entity_id = uuid4()

        mock_response = Mock()
        mock_response.data = [{"id": str(entity_id), "name": "test", "value": 42}]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await test_repository.get_by_id(entity_id)

        # Assert
        assert result is not None
        assert isinstance(result, TestEntity)
        assert result.id == entity_id
        assert result.name == "test"
        assert result.value == 42

        mock_supabase_client.table.assert_called_once_with("test_entities")
        mock_supabase_client.select.assert_called_once_with("*")
        mock_supabase_client.eq.assert_called_once_with("id", str(entity_id))

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, test_repository, mock_supabase_client):
        """Test get_by_id when entity not found."""
        # Arrange
        entity_id = uuid4()

        mock_response = Mock()
        mock_response.data = []

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await test_repository.get_by_id(entity_id)

        # Assert
        assert result is None


class TestBaseRepositoryGetByField:
    """Tests for get_by_field operation."""

    @pytest.mark.asyncio
    async def test_get_by_field_success(self, test_repository, mock_supabase_client):
        """Test successful entity retrieval by field."""
        # Arrange
        entity_id = uuid4()

        mock_response = Mock()
        mock_response.data = [{"id": str(entity_id), "name": "test", "value": 42}]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await test_repository.get_by_field("name", "test")

        # Assert
        assert result is not None
        assert isinstance(result, TestEntity)
        assert result.name == "test"

        mock_supabase_client.eq.assert_called_once_with("name", "test")
        mock_supabase_client.limit.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_by_field_not_found(self, test_repository, mock_supabase_client):
        """Test get_by_field when entity not found."""
        # Arrange
        mock_response = Mock()
        mock_response.data = []

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await test_repository.get_by_field("name", "nonexistent")

        # Assert
        assert result is None


class TestBaseRepositoryList:
    """Tests for list operation."""

    @pytest.mark.asyncio
    async def test_list_all(self, test_repository, mock_supabase_client):
        """Test listing all entities."""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {"id": str(uuid4()), "name": "test1", "value": 1},
            {"id": str(uuid4()), "name": "test2", "value": 2},
        ]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await test_repository.list()

        # Assert
        assert len(result) == 2
        assert all(isinstance(entity, TestEntity) for entity in result)
        assert result[0].name == "test1"
        assert result[1].name == "test2"

    @pytest.mark.asyncio
    async def test_list_with_filters(self, test_repository, mock_supabase_client):
        """Test listing with filters."""
        # Arrange
        mock_response = Mock()
        mock_response.data = [{"id": str(uuid4()), "name": "test", "value": 42}]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await test_repository.list(filters={"value": 42})

        # Assert
        assert len(result) == 1
        mock_supabase_client.eq.assert_called_once_with("value", 42)

    @pytest.mark.asyncio
    async def test_list_with_pagination(self, test_repository, mock_supabase_client):
        """Test listing with pagination."""
        # Arrange
        mock_response = Mock()
        mock_response.data = [{"id": str(uuid4()), "name": "test", "value": 42}]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.offset = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await test_repository.list(limit=10, offset=20)

        # Assert
        mock_supabase_client.limit.assert_called_once_with(10)
        mock_supabase_client.offset.assert_called_once_with(20)

    @pytest.mark.asyncio
    async def test_list_with_ordering(self, test_repository, mock_supabase_client):
        """Test listing with ordering."""
        # Arrange
        mock_response = Mock()
        mock_response.data = []

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.order = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        await test_repository.list(order_by="name", ascending=False)

        # Assert
        mock_supabase_client.order.assert_called_once_with("name", desc=True)


class TestBaseRepositoryUpdate:
    """Tests for update operation."""

    @pytest.mark.asyncio
    async def test_update_success(self, test_repository, mock_supabase_client):
        """Test successful entity update."""
        # Arrange
        entity_id = uuid4()
        data = {"value": 100}

        mock_response = Mock()
        mock_response.data = [{"id": str(entity_id), "name": "test", "value": 100}]

        mock_supabase_client.update = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await test_repository.update(entity_id, data)

        # Assert
        assert isinstance(result, TestEntity)
        assert result.value == 100

        mock_supabase_client.update.assert_called_once_with(data)
        mock_supabase_client.eq.assert_called_once_with("id", str(entity_id))

    @pytest.mark.asyncio
    async def test_update_not_found(self, test_repository, mock_supabase_client):
        """Test update when entity not found."""
        # Arrange
        entity_id = uuid4()
        data = {"value": 100}

        mock_response = Mock()
        mock_response.data = []

        mock_supabase_client.update = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            await test_repository.update(entity_id, data)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_validation_error(self, test_repository):
        """Test update with validation error."""
        # Arrange
        entity_id = uuid4()
        data = {"value": "not_an_integer"}  # Invalid type

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await test_repository.update(entity_id, data)

        assert "must be integer" in str(exc_info.value)


class TestBaseRepositoryDelete:
    """Tests for delete operation."""

    @pytest.mark.asyncio
    async def test_delete_success(self, test_repository, mock_supabase_client):
        """Test successful entity deletion."""
        # Arrange
        entity_id = uuid4()

        mock_response = Mock()
        mock_response.data = [{"id": str(entity_id)}]

        mock_supabase_client.delete = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await test_repository.delete(entity_id)

        # Assert
        assert result is True
        mock_supabase_client.delete.assert_called_once()
        mock_supabase_client.eq.assert_called_once_with("id", str(entity_id))

    @pytest.mark.asyncio
    async def test_delete_not_found(self, test_repository, mock_supabase_client):
        """Test delete when entity not found."""
        # Arrange
        entity_id = uuid4()

        mock_response = Mock()
        mock_response.data = []

        mock_supabase_client.delete = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await test_repository.delete(entity_id)

        # Assert
        assert result == False  # Use == instead of is for boolean comparison


class TestBaseRepositoryExists:
    """Tests for exists operation."""

    @pytest.mark.asyncio
    async def test_exists_true(self, test_repository, mock_supabase_client):
        """Test exists when entity exists."""
        # Arrange
        entity_id = uuid4()

        mock_response = Mock()
        mock_response.data = [{"id": str(entity_id)}]

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await test_repository.exists(entity_id)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, test_repository, mock_supabase_client):
        """Test exists when entity does not exist."""
        # Arrange
        entity_id = uuid4()

        mock_response = Mock()
        mock_response.data = []

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.limit = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await test_repository.exists(entity_id)

        # Assert
        assert result == False  # Use == instead of is for boolean comparison


class TestBaseRepositoryCount:
    """Tests for count operation."""

    @pytest.mark.asyncio
    async def test_count_all(self, test_repository, mock_supabase_client):
        """Test counting all entities."""
        # Arrange
        mock_response = Mock()
        mock_response.count = 42

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await test_repository.count()

        # Assert
        assert result == 42
        mock_supabase_client.select.assert_called_once_with("id", count="exact")

    @pytest.mark.asyncio
    async def test_count_with_filters(self, test_repository, mock_supabase_client):
        """Test counting with filters."""
        # Arrange
        mock_response = Mock()
        mock_response.count = 10

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(return_value=mock_response)

        # Act
        result = await test_repository.count(filters={"value": 42})

        # Assert
        assert result == 10
        mock_supabase_client.eq.assert_called_once_with("value", 42)


class TestBaseRepositoryErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_handle_duplicate_key_error(self, test_repository, mock_supabase_client):
        """Test handling of duplicate key constraint violation."""
        # Arrange
        data = {"name": "test", "value": 42}

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(
            side_effect=Exception("duplicate key value violates unique constraint")
        )

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await test_repository.create(data)

        assert "Duplicate entry" in str(exc_info.value)
        assert exc_info.value.error_code == ErrorCode.DB_CONSTRAINT_VIOLATION

    @pytest.mark.asyncio
    async def test_handle_foreign_key_error(self, test_repository, mock_supabase_client):
        """Test handling of foreign key constraint violation."""
        # Arrange
        data = {"name": "test", "value": 42}

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(
            side_effect=Exception("foreign key constraint violation")
        )

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await test_repository.create(data)

        assert "Invalid reference" in str(exc_info.value)
        assert exc_info.value.error_code == ErrorCode.DB_CONSTRAINT_VIOLATION

    @pytest.mark.asyncio
    async def test_handle_not_null_error(self, test_repository, mock_supabase_client):
        """Test handling of not null constraint violation."""
        # Arrange
        data = {"name": "test", "value": 42}

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(
            side_effect=Exception("null value in column violates not null constraint")
        )

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await test_repository.create(data)

        assert "Missing required field" in str(exc_info.value)
        assert exc_info.value.error_code == ErrorCode.DB_CONSTRAINT_VIOLATION

    @pytest.mark.asyncio
    async def test_handle_check_constraint_error(self, test_repository, mock_supabase_client):
        """Test handling of check constraint violation."""
        # Arrange
        data = {"name": "test", "value": 42}

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(side_effect=Exception("check constraint violation"))

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await test_repository.create(data)

        assert "Validation failed" in str(exc_info.value)
        assert exc_info.value.error_code == ErrorCode.DB_CONSTRAINT_VIOLATION

    @pytest.mark.asyncio
    async def test_handle_generic_database_error(self, test_repository, mock_supabase_client):
        """Test handling of generic database error."""
        # Arrange
        data = {"name": "test", "value": 42}

        mock_supabase_client.insert = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(side_effect=Exception("connection timeout"))

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await test_repository.create(data)

        assert "Database operation failed" in str(exc_info.value)
        assert exc_info.value.error_code == ErrorCode.DB_QUERY_FAILED

    @pytest.mark.asyncio
    async def test_get_by_id_database_error(self, test_repository, mock_supabase_client):
        """Test get_by_id with database error."""
        # Arrange
        entity_id = uuid4()

        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(side_effect=Exception("database connection lost"))

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await test_repository.get_by_id(entity_id)

        assert "Database operation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_database_error(self, test_repository, mock_supabase_client):
        """Test list with database error."""
        # Arrange
        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(side_effect=Exception("query timeout"))

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await test_repository.list()

        assert "Database operation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_database_error(self, test_repository, mock_supabase_client):
        """Test update with database error."""
        # Arrange
        entity_id = uuid4()
        data = {"value": 100}

        mock_supabase_client.update = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(side_effect=Exception("deadlock detected"))

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await test_repository.update(entity_id, data)

        assert "Database operation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_database_error(self, test_repository, mock_supabase_client):
        """Test delete with database error."""
        # Arrange
        entity_id = uuid4()

        mock_supabase_client.delete = Mock(return_value=mock_supabase_client)
        mock_supabase_client.eq = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(side_effect=Exception("permission denied"))

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await test_repository.delete(entity_id)

        assert "Database operation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_count_database_error(self, test_repository, mock_supabase_client):
        """Test count with database error."""
        # Arrange
        mock_supabase_client.select = Mock(return_value=mock_supabase_client)
        mock_supabase_client.execute = Mock(side_effect=Exception("table does not exist"))

        # Act & Assert
        with pytest.raises(DatabaseError) as exc_info:
            await test_repository.count()

        assert "Database operation failed" in str(exc_info.value)
