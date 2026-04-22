# Audit Trail Usage Guide

This guide explains how to use the audit trail functionality implemented in the repository layer.

## Overview

The audit trail system automatically tracks:

- **created_at**: When a record was created (set by database default)
- **updated_at**: When a record was last modified (updated by database trigger)
- **modified_by**: Which user made the modification (set by repository layer)

## Affected Tables

The following tables have audit trail fields:

- `users`
- `feeds`
- `articles`
- `reading_list`
- `user_subscriptions`

## Database Schema

Each critical table now includes:

```sql
created_at TIMESTAMPTZ DEFAULT now()  -- Automatically set on insert
updated_at TIMESTAMPTZ DEFAULT now()  -- Automatically updated on modification
modified_by TEXT                       -- Discord ID of user who made the change
```

## Repository Usage

### Setting the Current User

Before performing create or update operations, set the current user to track who is making the modification:

```python
from app.repositories.user import UserRepository
from app.core.database import get_supabase_client

# Initialize repository
client = get_supabase_client()
user_repo = UserRepository(client)

# Set current user (Discord ID)
user_repo.set_current_user("discord_user_123456789")
```

### Create Operations

When creating a new record, the `modified_by` field will be automatically populated:

```python
# Set current user first
user_repo.set_current_user("discord_user_123456789")

# Create user
new_user = await user_repo.create({
    "discord_id": "new_user_987654321",
    "dm_notifications_enabled": True
})

# Result:
# - created_at: Set by database to current timestamp
# - updated_at: Set by database to current timestamp
# - modified_by: "discord_user_123456789"
```

### Update Operations

When updating a record, the `modified_by` and `updated_at` fields are automatically updated:

```python
# Set current user first
user_repo.set_current_user("discord_user_123456789")

# Update user
updated_user = await user_repo.update(user_id, {
    "dm_notifications_enabled": False
})

# Result:
# - updated_at: Updated by database trigger to current timestamp
# - modified_by: "discord_user_123456789"
```

### System Operations

For system-initiated operations (e.g., automated tasks, migrations), you can either:

1. **Set a system identifier**:

```python
user_repo.set_current_user("system")
```

2. **Leave it unset** (modified_by will be NULL):

```python
user_repo.set_current_user(None)
```

## Middleware Integration

For API endpoints, you should set the current user in middleware based on the authenticated user:

```python
from fastapi import Request
from app.core.auth import get_current_user_from_token

async def audit_trail_middleware(request: Request, call_next):
    """Middleware to set current user for audit trail tracking."""

    # Extract user from authentication token
    user = await get_current_user_from_token(request)

    if user:
        # Set current user in all repositories
        # This would typically be done through dependency injection
        request.state.current_user_id = user.discord_id

    response = await call_next(request)
    return response
```

## Dependency Injection Pattern

For better integration with FastAPI, use dependency injection:

```python
from fastapi import Depends, Request
from app.repositories.user import UserRepository
from app.core.database import get_supabase_client

def get_user_repository(request: Request) -> UserRepository:
    """Get user repository with current user set."""
    client = get_supabase_client()
    repo = UserRepository(client)

    # Set current user from request state (set by middleware)
    if hasattr(request.state, 'current_user_id'):
        repo.set_current_user(request.state.current_user_id)

    return repo

# Use in endpoint
@app.post("/users")
async def create_user(
    data: UserCreateSchema,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Create a new user with automatic audit trail tracking."""
    user = await user_repo.create(data.dict())
    return user
```

## Querying Audit Trail Data

You can query audit trail fields like any other field:

```python
# Get all users modified by a specific user
users = await user_repo.list(
    filters={"modified_by": "discord_user_123456789"}
)

# Get recently updated articles
from datetime import datetime, timedelta
recent_cutoff = datetime.utcnow() - timedelta(hours=24)

# Note: For timestamp filtering, you'll need to use raw queries
# or extend the repository with custom methods
```

## Custom Repository Methods for Audit Queries

You can add custom methods to repositories for common audit queries:

```python
class UserRepository(BaseRepository[User]):
    async def get_recently_modified(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[User]:
        """Get users modified in the last N hours."""
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() - timedelta(hours=hours)

        response = self.client.table(self.table_name) \
            .select('*') \
            .gte('updated_at', cutoff.isoformat()) \
            .order('updated_at', desc=True) \
            .limit(limit) \
            .execute()

        return [self._map_to_entity(row) for row in response.data]

    async def get_modifications_by_user(
        self,
        discord_id: str,
        limit: int = 100
    ) -> List[User]:
        """Get all users modified by a specific user."""
        return await self.list(
            filters={"modified_by": discord_id},
            limit=limit,
            order_by="updated_at",
            ascending=False
        )
```

## Disabling Audit Trail

If you need to disable audit trail tracking for a specific repository (e.g., for testing):

```python
# Disable audit trail when initializing repository
user_repo = UserRepository(client)
user_repo.enable_audit_trail = False

# Or create a custom repository class
class UserRepositoryNoAudit(UserRepository):
    def __init__(self, client: Client):
        super().__init__(client)
        self.enable_audit_trail = False
```

## Best Practices

1. **Always set current user in API endpoints**: Use middleware or dependency injection to automatically set the current user for all repository operations.

2. **Use Discord IDs for modified_by**: Store the Discord ID (not the UUID) in the `modified_by` field for consistency with the user identification system.

3. **Handle system operations appropriately**: For automated tasks, use a consistent system identifier like "system", "cron", or "migration".

4. **Don't override timestamps manually**: Let the database handle `created_at` and `updated_at` automatically unless you have a specific reason to override them.

5. **Query audit fields for debugging**: Use the audit trail fields to debug issues and understand the history of data changes.

6. **Consider privacy implications**: The `modified_by` field contains user identifiers. Ensure this data is handled according to your privacy policy.

## Migration

To apply the audit trail migration to your database:

```bash
# Using psql
psql $DATABASE_URL -f backend/scripts/migrations/005_add_audit_trail_fields.sql

# Or using Supabase Dashboard
# 1. Go to SQL Editor
# 2. Copy contents of 005_add_audit_trail_fields.sql
# 3. Execute the script
```

To rollback:

```bash
psql $DATABASE_URL -f backend/scripts/migrations/005_add_audit_trail_fields_rollback.sql
```

## Troubleshooting

### modified_by is always NULL

**Cause**: Current user is not being set before repository operations.

**Solution**: Call `repository.set_current_user(discord_id)` before create/update operations.

### updated_at is not updating

**Cause**: Database trigger may not be installed or may have failed.

**Solution**: Re-run the migration script to ensure triggers are created:

```sql
-- Check if trigger exists
SELECT * FROM pg_trigger WHERE tgname = 'update_users_updated_at';

-- Recreate trigger if needed
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Tests failing after migration

**Cause**: Tests may be checking exact field counts or not expecting new fields.

**Solution**: Update test assertions to handle optional audit fields:

```python
# Before
assert len(user.__dict__) == 4

# After
assert user.id is not None
assert user.discord_id == "123456789"
# Don't assert on exact field count
```

## Related Documentation

- [Database Migrations README](../scripts/migrations/README.md)
- [Repository Pattern Documentation](./repository_pattern.md)
- [Requirements 14.1, 14.4](../../.kiro/specs/project-architecture-refactoring/requirements.md)
