# Database Migrations

This directory contains database migration scripts for the Tech News Agent project.

## Migration Files

### 005_add_audit_trail_fields.sql

**Purpose**: Adds audit trail fields to critical database tables for tracking data modifications.

**Changes**:

- Adds `modified_by` field to: users, feeds, articles, reading_list, user_subscriptions
- Adds `updated_at` field to: users, feeds, articles, user_subscriptions (reading_list already had it)
- Creates/updates triggers to automatically update `updated_at` on row modifications
- Adds indexes on audit trail fields for query performance
- Adds column comments for documentation

**Rollback**: Use `005_add_audit_trail_fields_rollback.sql` to revert changes

**Requirements**: Validates Requirements 14.1, 14.4

## How to Apply Migrations

### Using Supabase Dashboard

1. Log in to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy the contents of the migration file
4. Paste into the SQL Editor
5. Click "Run" to execute the migration

### Using Supabase CLI

```bash
# Apply migration
supabase db push

# Or execute specific migration file
psql $DATABASE_URL -f backend/scripts/migrations/005_add_audit_trail_fields.sql
```

## How to Rollback Migrations

If you need to rollback a migration:

```bash
# Execute the rollback script
psql $DATABASE_URL -f backend/scripts/migrations/005_add_audit_trail_fields_rollback.sql
```

## Audit Trail Usage

After applying the audit trail migration, the repository layer automatically tracks:

1. **created_at**: Automatically set by database default when record is created
2. **updated_at**: Automatically updated by database trigger when record is modified
3. **modified_by**: Set by repository layer when `set_current_user()` is called

### Example Usage in Code

```python
from app.repositories.user import UserRepository
from app.core.database import get_supabase_client

# Initialize repository
client = get_supabase_client()
user_repo = UserRepository(client)

# Set current user for audit tracking
user_repo.set_current_user("discord_user_123")

# Create or update operations will now track modified_by
user = await user_repo.create({
    "discord_id": "new_user_456",
    "dm_notifications_enabled": True
})
# Result: modified_by will be set to "discord_user_123"

# Update operation
updated_user = await user_repo.update(user.id, {
    "dm_notifications_enabled": False
})
# Result: modified_by will be "discord_user_123", updated_at will be current timestamp
```

## Migration Checklist

When creating new migrations:

- [ ] Create forward migration file with descriptive name
- [ ] Create corresponding rollback file
- [ ] Test migration on local database
- [ ] Test rollback on local database
- [ ] Document changes in this README
- [ ] Reference requirement numbers in migration comments
- [ ] Add appropriate indexes for new fields
- [ ] Update entity models to include new fields
- [ ] Update repository mapping methods

## Migration Naming Convention

Migrations should follow the pattern:

```
{number}_{description}.sql
{number}_{description}_rollback.sql
```

Example:

- `005_add_audit_trail_fields.sql`
- `005_add_audit_trail_fields_rollback.sql`
