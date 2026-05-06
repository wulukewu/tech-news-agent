# Soft Delete Implementation

## Overview

This document describes the soft delete functionality implemented for critical entities in the Tech News Agent application. Soft delete preserves deleted records in the database by marking them with a `deleted_at` timestamp instead of permanently removing them, enabling audit trail preservation and data recovery.

**Validates: Requirements 14.5**

## What is Soft Delete?

Soft delete is a data management pattern where records are marked as deleted rather than being permanently removed from the database. This approach:

- **Preserves audit history**: Deleted records remain in the database for compliance and auditing
- **Enables data recovery**: Accidentally deleted records can be restored
- **Maintains referential integrity**: Related records can still reference deleted entities
- **Supports compliance**: Meets data retention policy requirements

## Implementation Details

### Database Schema Changes

The migration `005_add_soft_delete_support.sql` adds a `deleted_at` column to critical tables:

- `users.deleted_at` - Timestamp when user was soft-deleted
- `feeds.deleted_at` - Timestamp when feed was soft-deleted
- `articles.deleted_at` - Timestamp when article was soft-deleted
- `reading_list.deleted_at` - Timestamp when reading list item was soft-deleted

**Schema:**

```sql
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMPTZ DEFAULT NULL;
ALTER TABLE feeds ADD COLUMN deleted_at TIMESTAMPTZ DEFAULT NULL;
ALTER TABLE articles ADD COLUMN deleted_at TIMESTAMPTZ DEFAULT NULL;
ALTER TABLE reading_list ADD COLUMN deleted_at TIMESTAMPTZ DEFAULT NULL;
```

**Indexes:**
Partial indexes are created to efficiently filter out deleted records:

```sql
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_feeds_deleted_at ON feeds(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_articles_deleted_at ON articles(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_reading_list_deleted_at ON reading_list(deleted_at) WHERE deleted_at IS NULL;
```

### Repository Layer Changes

#### BaseRepository

The `BaseRepository` class has been enhanced with soft delete support:

**Constructor:**

```python
def __init__(self, client: Client, table_name: str, enable_audit_trail: bool = True, enable_soft_delete: bool = True):
    # enable_soft_delete controls whether delete operations use soft delete
```

**Key Methods:**

1. **`_apply_soft_delete_filter(query)`** - Applies filter to exclude soft-deleted records

   ```python
   # Adds: WHERE deleted_at IS NULL
   query = query.is_('deleted_at', 'null')
   ```

2. **`delete(entity_id)`** - Modified to perform soft delete by default

   ```python
   # Soft delete: Sets deleted_at timestamp
   delete_data = {'deleted_at': datetime.utcnow().isoformat()}
   response = self.client.table(self.table_name).update(delete_data).eq('id', str(entity_id)).execute()
   ```

3. **`restore(entity_id)`** - New method to restore soft-deleted entities

   ```python
   # Clears deleted_at timestamp
   restore_data = {'deleted_at': None}
   response = self.client.table(self.table_name).update(restore_data).eq('id', str(entity_id)).execute()
   ```

4. **`hard_delete(entity_id)`** - New method for permanent deletion
   ```python
   # Permanently removes record (use with caution!)
   response = self.client.table(self.table_name).delete().eq('id', str(entity_id)).execute()
   ```

**Query Methods:**
All query methods automatically exclude soft-deleted records:

- `get_by_id()` - Filters out deleted records
- `get_by_field()` - Filters out deleted records
- `list()` - Filters out deleted records
- `exists()` - Only checks non-deleted records
- `count()` - Only counts non-deleted records

### Entity Model Changes

All entity models have been updated to include the `deleted_at` field:

**User:**

```python
class User:
    def __init__(self, ..., deleted_at: Optional[datetime] = None):
        self.deleted_at = deleted_at
```

**Article:**

```python
class Article:
    def __init__(self, ..., deleted_at: Optional[datetime] = None):
        self.deleted_at = deleted_at
```

**ReadingListItem:**

```python
class ReadingListItem:
    def __init__(self, ..., deleted_at: Optional[datetime] = None):
        self.deleted_at = deleted_at
```

**Feed:**

```python
class Feed:
    def __init__(self, ..., deleted_at: Optional[datetime] = None):
        self.deleted_at = deleted_at
```

## Usage Examples

### Soft Delete an Entity

```python
# Delete a user (soft delete)
user_repo = UserRepository(client)
deleted = await user_repo.delete(user_id)
# User is marked as deleted but remains in database
```

### Restore a Soft-Deleted Entity

```python
# Restore a previously deleted user
user_repo = UserRepository(client)
restored_user = await user_repo.restore(user_id)
# User's deleted_at is cleared, entity is active again
```

### Permanently Delete an Entity

```python
# Permanently remove a user (use with caution!)
user_repo = UserRepository(client)
deleted = await user_repo.hard_delete(user_id)
# User is permanently removed from database
```

### Query Non-Deleted Entities

```python
# All query methods automatically exclude soft-deleted records
user_repo = UserRepository(client)

# Get by ID - returns None if deleted
user = await user_repo.get_by_id(user_id)

# List - excludes deleted records
users = await user_repo.list()

# Count - excludes deleted records
count = await user_repo.count()
```

### Disable Soft Delete for Specific Repository

```python
# Create repository with soft delete disabled
class MyRepository(BaseRepository[MyEntity]):
    def __init__(self, client: Client):
        super().__init__(client, "my_table", enable_soft_delete=False)
        # This repository will use hard delete by default
```

## Migration Guide

### Applying the Migration

1. **Run the migration script:**

   ```bash
   # Execute in Supabase Dashboard > SQL Editor
   # Or via CLI:
   psql -h <host> -U <user> -d <database> -f backend/scripts/migrations/005_add_soft_delete_support.sql
   ```

2. **Verify the migration:**
   ```sql
   -- Check that deleted_at columns exist
   SELECT column_name, data_type
   FROM information_schema.columns
   WHERE table_name IN ('users', 'feeds', 'articles', 'reading_list')
   AND column_name = 'deleted_at';
   ```

### Rolling Back the Migration

If needed, the migration can be rolled back:

```bash
psql -h <host> -U <user> -d <database> -f backend/scripts/migrations/005_add_soft_delete_support_rollback.sql
```

**Warning:** Rolling back will remove the `deleted_at` column and all soft delete information will be lost.

## Testing

Comprehensive tests are provided in `backend/tests/test_soft_delete.py`:

```bash
# Run soft delete tests
pytest backend/tests/test_soft_delete.py -v
```

**Test Coverage:**

- ✅ Delete sets deleted_at timestamp
- ✅ Get by ID excludes soft-deleted records
- ✅ List excludes soft-deleted records
- ✅ Restore clears deleted_at timestamp
- ✅ Restore fails if entity not deleted
- ✅ Hard delete permanently removes records
- ✅ Count excludes soft-deleted records
- ✅ Custom queries exclude soft-deleted records

## Best Practices

### When to Use Soft Delete

✅ **Use soft delete for:**

- User accounts (audit trail, compliance)
- Articles (content history, references)
- Reading list items (user activity history)
- Feeds (subscription history)

❌ **Don't use soft delete for:**

- Temporary data (sessions, cache)
- High-volume transactional data
- Data with no audit requirements

### Performance Considerations

1. **Indexes:** Partial indexes on `deleted_at IS NULL` ensure efficient queries
2. **Cleanup:** Periodically hard delete old soft-deleted records if needed
3. **Queries:** Always use repository methods to ensure soft delete filter is applied

### Security Considerations

1. **Access Control:** Ensure only authorized users can restore deleted entities
2. **Audit Logging:** Log all delete and restore operations
3. **Data Retention:** Define policies for how long soft-deleted data is retained

## Troubleshooting

### Issue: Deleted records still appearing in queries

**Solution:** Ensure you're using repository methods, not direct database queries. Repository methods automatically apply the soft delete filter.

```python
# ❌ Wrong - bypasses soft delete filter
response = client.table('users').select('*').execute()

# ✅ Correct - applies soft delete filter
users = await user_repo.list()
```

### Issue: Cannot restore entity

**Solution:** Check that:

1. Entity exists in database
2. Entity has `deleted_at` set (is actually deleted)
3. Soft delete is enabled for the repository

```python
# Check if entity is deleted
query = client.table('users').select('*').eq('id', user_id).execute()
if query.data and query.data[0].get('deleted_at'):
    # Entity is soft-deleted, can be restored
    await user_repo.restore(user_id)
```

### Issue: Need to query deleted records

**Solution:** Use direct database queries or create a custom repository method:

```python
# Custom method to get deleted entities
async def list_deleted(self) -> List[T]:
    query = self.client.table(self.table_name).select('*')
    query = query.not_.is_('deleted_at', 'null')  # Only deleted records
    response = query.execute()
    return [self._map_to_entity(row) for row in response.data]
```

## Future Enhancements

Potential improvements for the soft delete implementation:

1. **Cascade Soft Delete:** Automatically soft delete related entities
2. **Scheduled Cleanup:** Background job to hard delete old soft-deleted records
3. **Restore Cascade:** Restore related entities when parent is restored
4. **Soft Delete Audit Log:** Track who deleted and restored entities
5. **Retention Policies:** Configurable retention periods per entity type

## References

- Requirements: 14.5 (Database Audit and Integrity)
- Design: Property 9 (Soft Delete Preservation)
- Migration: `backend/scripts/migrations/005_add_soft_delete_support.sql`
- Tests: `backend/tests/test_soft_delete.py`
- Base Repository: `backend/app/repositories/base.py`
