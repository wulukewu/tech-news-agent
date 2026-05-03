# Repository Layer

This directory contains the repository pattern implementation for data access abstraction.

## Overview

The repository layer provides a clean interface between the service layer and the database, encapsulating all database-specific logic and providing consistent CRUD operations.

## Architecture

```
Service Layer
     ↓
IRepository (Interface)
     ↓
BaseRepository (Base Implementation)
     ↓
Concrete Repositories (e.g., UserRepository, ArticleRepository)
     ↓
Database (Supabase)
```

## Key Components

### `IRepository[T]`

Generic interface defining the contract for all repositories:

- `create(data)` - Create a new entity
- `get_by_id(entity_id)` - Retrieve entity by ID
- `get_by_field(field, value)` - Retrieve entity by field value
- `list(filters, limit, offset, order_by)` - List entities with filtering and pagination
- `update(entity_id, data)` - Update an existing entity
- `delete(entity_id)` - Delete an entity
- `exists(entity_id)` - Check if entity exists
- `count(filters)` - Count entities matching filters

### `BaseRepository[T]`

Base implementation providing:

- Common CRUD operations
- Error handling and wrapping
- Structured logging
- Query building patterns
- Constraint violation detection

## Creating a Concrete Repository

To create a repository for a specific entity:

```python
from uuid import UUID
from typing import Dict, Any
from app.repositories.base import BaseRepository
from app.schemas.user import User

class UserRepository(BaseRepository[User]):
    """Repository for User entities."""

    def __init__(self, client):
        super().__init__(client, "users")

    def _map_to_entity(self, row: Dict[str, Any]) -> User:
        """Map database row to User entity."""
        return User(
            id=UUID(row['id']),
            discord_id=row['discord_id'],
            created_at=row['created_at']
        )

    def _validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data before creating a user."""
        if 'discord_id' not in data:
            raise ValidationError(
                "Missing required field: discord_id",
                error_code=ErrorCode.VALIDATION_MISSING_FIELD
            )
        return data

    def _validate_update_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data before updating a user."""
        # Add custom validation logic
        return data
```

## Usage in Services

Services should depend on repository interfaces, not concrete implementations:

```python
from app.repositories.base import IRepository
from app.schemas.user import User

class UserService:
    """Service for user operations."""

    def __init__(self, user_repository: IRepository[User]):
        self.user_repo = user_repository

    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return await self.user_repo.get_by_id(user_id)

    async def create_user(self, discord_id: str) -> User:
        """Create a new user."""
        data = {"discord_id": discord_id}
        return await self.user_repo.create(data)
```

## Error Handling

The repository layer automatically handles database errors and wraps them in appropriate exception types:

- `DatabaseError` - Generic database errors
- `NotFoundError` - Entity not found
- `ValidationError` - Data validation failures

Constraint violations are detected and wrapped with specific error messages:

- Duplicate key → "Duplicate entry: {field} already exists"
- Foreign key → "Invalid reference: {reference} does not exist"
- Not null → "Missing required field: '{field}' cannot be null"
- Check constraint → "Validation failed: {constraint}"

## Logging

All repository operations are automatically logged with structured context:

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "logger": "app.repositories.base.UserRepository",
  "message": "Creating users entity",
  "extra": {
    "operation": "create",
    "table": "users"
  }
}
```

## Testing

Use mocks for testing services that depend on repositories:

```python
from unittest.mock import Mock
import pytest

@pytest.fixture
def mock_user_repository():
    repo = Mock(spec=IRepository)
    return repo

@pytest.mark.asyncio
async def test_get_user(mock_user_repository):
    # Arrange
    user_id = uuid4()
    expected_user = User(id=user_id, discord_id="123")
    mock_user_repository.get_by_id.return_value = expected_user

    service = UserService(mock_user_repository)

    # Act
    result = await service.get_user(user_id)

    # Assert
    assert result == expected_user
    mock_user_repository.get_by_id.assert_called_once_with(user_id)
```

## Benefits

1. **Separation of Concerns** - Services focus on business logic, repositories handle data access
2. **Testability** - Easy to mock repositories for service testing
3. **Consistency** - All data access follows the same patterns
4. **Error Handling** - Centralized database error handling
5. **Logging** - Automatic structured logging for all operations
6. **Type Safety** - Generic types ensure type-safe operations
7. **Maintainability** - Database changes isolated to repository layer

## Migration Strategy

When migrating existing code to use repositories:

1. Create concrete repository for the entity
2. Update service to accept repository in constructor
3. Replace direct database calls with repository methods
4. Update tests to use repository mocks
5. Verify functionality with integration tests

## Next Steps

- Create concrete repositories for each entity (User, Article, Feed, etc.)
- Update services to use repositories instead of direct database access
- Add integration tests for repository implementations
- Document entity-specific repository methods
