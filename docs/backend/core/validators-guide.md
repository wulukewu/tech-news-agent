# Business Rule Validation Layer

This document describes the business rule validation layer implemented in `validators.py`.

## Overview

The business rule validation layer provides centralized validation of domain-specific rules before data persistence. This ensures data integrity and consistency across the application by enforcing business rules at both the application and database levels.

**Validates: Requirements 14.2, 14.3**

## Architecture

### Two-Layer Validation Strategy

The validation system uses a two-layer approach:

1. **Application Layer** (`validators.py`): Validates business rules in Python before database operations
2. **Database Layer** (migration 006): Enforces constraints at the database level as a safety net

This dual-layer approach provides:

- Early validation with clear error messages
- Database-level safety net for data integrity
- Consistent validation across all entry points

### Validation Flow

```
User Input
    ↓
Repository.create() / Repository.update()
    ↓
_validate_business_rules_create/update()  ← Business rule validation
    ↓
_validate_create_data() / _validate_update_data()  ← Format validation
    ↓
Database Operation
    ↓
Database Constraints  ← Final safety check
```

## Validators

### BusinessRuleValidator (Base Class)

Provides common validation patterns:

- `validate_required_field()`: Check field existence and type
- `validate_string_length()`: Validate string length constraints
- `validate_integer_range()`: Validate integer range constraints
- `validate_enum_value()`: Validate value is in allowed set

### UserValidator

Validates user-related business rules:

- **Discord ID Format**: Must be numeric, 17-20 digits (Discord snowflake format)
- **DM Notifications**: Must be boolean if provided

**Methods:**

- `validate_discord_id()`: Validate Discord ID format
- `validate_user_create()`: Validate user creation data
- `validate_user_update()`: Validate user update data

### FeedValidator

Validates feed-related business rules:

- **Name**: Non-empty, max 255 characters
- **URL**: Must start with http:// or https://, max 2048 characters
- **Category**: Non-empty, max 100 characters
- **Is Active**: Must be boolean if provided

**Methods:**

- `validate_url_format()`: Validate URL format
- `validate_feed_create()`: Validate feed creation data
- `validate_feed_update()`: Validate feed update data

### ArticleValidator

Validates article-related business rules:

- **Title**: Non-empty, max 2000 characters
- **URL**: Non-empty, max 2048 characters
- **Tinkering Index**: Integer 1-5 if provided
- **AI Summary**: Max 5000 characters if provided
- **Deep Summary**: Max 10000 characters if provided
- **Published At**: Must be datetime or ISO string if provided

**Methods:**

- `validate_article_create()`: Validate article creation data
- `validate_article_update()`: Validate article update data

### ReadingListValidator

Validates reading list-related business rules:

- **Status**: Must be one of 'Unread', 'Read', 'Archived'
- **Rating**: Integer 1-5 or null
- **User ID**: Required for creation
- **Article ID**: Required for creation

**Methods:**

- `validate_reading_list_create()`: Validate reading list item creation
- `validate_reading_list_update()`: Validate reading list item update
- `validate_status_transition()`: Validate status transitions (placeholder for future rules)

## Integration with Repositories

Each repository integrates validators by overriding two methods:

```python
def _validate_business_rules_create(self, data: Dict[str, Any]) -> None:
    """Validate business rules before creating an entity."""
    EntityValidator.validate_entity_create(data)

def _validate_business_rules_update(self, data: Dict[str, Any]) -> None:
    """Validate business rules before updating an entity."""
    EntityValidator.validate_entity_update(data)
```

These methods are called automatically by the base repository before persistence.

## Database Constraints

Migration 006 adds database-level constraints that mirror the business rules:

### Users Table

- `check_users_discord_id_not_empty`: Discord ID cannot be empty
- `check_users_discord_id_numeric`: Discord ID must be numeric
- `check_users_discord_id_length`: Discord ID must be 17-20 digits

### Feeds Table

- `check_feeds_name_not_empty`: Name cannot be empty
- `check_feeds_name_length`: Name max 255 characters
- `check_feeds_url_not_empty`: URL cannot be empty
- `check_feeds_url_protocol`: URL must start with http:// or https://
- `check_feeds_url_length`: URL max 2048 characters
- `check_feeds_category_not_empty`: Category cannot be empty
- `check_feeds_category_length`: Category max 100 characters

### Articles Table

- `check_articles_title_not_empty`: Title cannot be empty
- `check_articles_title_length`: Title max 2000 characters
- `check_articles_url_not_empty`: URL cannot be empty
- `check_articles_url_length`: URL max 2048 characters
- `check_articles_tinkering_index_range`: Tinkering index 1-5 if not null
- `check_articles_ai_summary_length`: AI summary max 5000 characters
- `check_articles_deep_summary_length`: Deep summary max 10000 characters

### Reading List Table

- Status CHECK constraint: Status must be 'Unread', 'Read', or 'Archived'
- Rating CHECK constraint: Rating must be 1-5 if not null
- NOT NULL constraints on user_id, article_id, status

## Error Handling

Validation errors raise `ValidationError` with:

- Clear error message describing what went wrong
- Error code (e.g., `VALIDATION_MISSING_FIELD`, `VALIDATION_INVALID_FORMAT`)
- Details dictionary with context (field name, value, constraints)

Example:

```python
raise ValidationError(
    "Invalid discord_id: must be 17-20 digits",
    error_code=ErrorCode.VALIDATION_INVALID_FORMAT,
    details={"field": "discord_id", "length": len(discord_id)}
)
```

## Usage Examples

### Creating a User

```python
from app.repositories.user import UserRepository

user_repo = UserRepository(supabase_client)

# Valid data - passes validation
user = await user_repo.create({
    'discord_id': '123456789012345678',  # 18 digits
    'dm_notifications_enabled': True
})

# Invalid data - raises ValidationError
try:
    user = await user_repo.create({
        'discord_id': '123',  # Too short
        'dm_notifications_enabled': True
    })
except ValidationError as e:
    print(e.message)  # "Invalid discord_id: must be 17-20 digits"
    print(e.details)  # {"field": "discord_id", "length": 3}
```

### Creating an Article

```python
from app.repositories.article import ArticleRepository

article_repo = ArticleRepository(supabase_client)

# Valid data - passes validation
article = await article_repo.create({
    'feed_id': feed_uuid,
    'title': 'New AI Breakthrough',
    'url': 'https://example.com/article',
    'tinkering_index': 4
})

# Invalid data - raises ValidationError
try:
    article = await article_repo.create({
        'feed_id': feed_uuid,
        'title': 'New AI Breakthrough',
        'url': 'https://example.com/article',
        'tinkering_index': 10  # Out of range
    })
except ValidationError as e:
    print(e.message)  # "Invalid tinkering_index: must be at most 5"
```

## Testing

Business rule validators should be tested with:

1. **Unit Tests**: Test each validator method with valid and invalid inputs
2. **Integration Tests**: Test validation through repository operations
3. **Property-Based Tests**: Test validation properties hold across all inputs

Example property test:

```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=1, max_value=5))
def test_valid_tinkering_index_accepted(tinkering_index):
    """Valid tinkering index values (1-5) should be accepted."""
    data = {
        'feed_id': str(uuid4()),
        'title': 'Test Article',
        'url': 'https://example.com/test',
        'tinkering_index': tinkering_index
    }
    # Should not raise
    ArticleValidator.validate_article_create(data)
```

## Extending Validators

To add new business rules:

1. Add validation method to appropriate validator class
2. Call the method from `_validate_business_rules_create/update()`
3. Add corresponding database constraint in a new migration
4. Update this documentation
5. Add tests for the new rule

Example:

```python
class ArticleValidator(BusinessRuleValidator):
    @staticmethod
    def validate_publication_date(published_at: datetime) -> None:
        """Validate article publication date is not in the future."""
        if published_at > datetime.utcnow():
            raise ValidationError(
                "Invalid published_at: cannot be in the future",
                error_code=ErrorCode.VALIDATION_BUSINESS_RULE,
                details={"field": "published_at", "value": published_at}
            )
```

## Migration Guide

To apply the database constraints:

```bash
# Apply migration
psql -h <host> -U <user> -d <database> -f backend/scripts/migrations/006_add_business_rule_constraints.sql

# Rollback if needed
psql -h <host> -U <user> -d <database> -f backend/scripts/migrations/006_add_business_rule_constraints_rollback.sql
```

## Benefits

1. **Data Integrity**: Ensures data meets business rules before persistence
2. **Clear Errors**: Provides actionable error messages for invalid data
3. **Centralized Logic**: Business rules defined in one place
4. **Database Safety**: Database constraints provide final safety net
5. **Testability**: Validators can be tested independently
6. **Maintainability**: Easy to update rules as requirements change

## Related Files

- `backend/app/core/validators.py`: Validator implementations
- `backend/app/repositories/base.py`: Base repository with validation integration
- `backend/app/repositories/*.py`: Concrete repositories using validators
- `backend/scripts/migrations/006_add_business_rule_constraints.sql`: Database constraints
- `backend/scripts/migrations/006_add_business_rule_constraints_rollback.sql`: Rollback script
