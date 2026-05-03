# Test Fixtures Documentation

## Overview

This document describes the test fixtures available in `conftest.py` for the Supabase Migration Phase 1 tests.

## Hypothesis Configuration

Hypothesis is configured with the following profiles:

- **default**: 20 examples, normal verbosity
- **ci**: 100 examples, verbose output (for CI/CD pipelines)
- **dev**: 10 examples, normal verbosity (for faster local development)
- **debug**: 5 examples, verbose output (for debugging failing tests)

To use a different profile, set the `HYPOTHESIS_PROFILE` environment variable:

```bash
# Use the dev profile for faster tests during development
export HYPOTHESIS_PROFILE=dev
pytest tests/

# Use the ci profile for thorough testing
export HYPOTHESIS_PROFILE=ci
pytest tests/
```

## Available Fixtures

### Database Connection Fixtures

#### `supabase_url` (session scope)

Returns the Supabase URL from the `SUPABASE_URL` environment variable. Skips tests if not set.

#### `supabase_key` (session scope)

Returns the Supabase key from the `SUPABASE_KEY` environment variable. Skips tests if not set.

#### `test_supabase_client` (function scope)

Provides a fresh Supabase client for each test function.

**Usage:**

```python
def test_something(test_supabase_client):
    result = test_supabase_client.table('users').select('*').execute()
    assert result is not None
```

### Data Fixtures

All data fixtures automatically clean up after the test completes, ensuring test isolation.

#### `test_user` (function scope)

Creates a test user with a unique `discord_id`.

**Returns:** User record dict with keys: `id`, `discord_id`, `created_at`

**Usage:**

```python
def test_user_operations(test_user):
    user_id = test_user['id']
    discord_id = test_user['discord_id']
    # ... test logic
```

**Cleanup:** Automatically deletes the user (cascades to subscriptions and reading_list)

#### `test_feed` (function scope)

Creates a test feed with a unique URL.

**Returns:** Feed record dict with keys: `id`, `name`, `url`, `category`, `is_active`, `created_at`

**Usage:**

```python
def test_feed_operations(test_feed):
    feed_id = test_feed['id']
    feed_url = test_feed['url']
    # ... test logic
```

**Cleanup:** Automatically deletes the feed (cascades to articles)

#### `test_article` (function scope)

Creates a test article linked to a test feed. Depends on `test_feed` fixture.

**Returns:** Article record dict with keys: `id`, `feed_id`, `title`, `url`, `published_at`, `tinkering_index`, `ai_summary`, `embedding`, `created_at`

**Usage:**

```python
def test_article_operations(test_article):
    article_id = test_article['id']
    article_url = test_article['url']
    # ... test logic
```

**Cleanup:** Automatically deletes the article (cascades to reading_list)

#### `test_subscription` (function scope)

Creates a test subscription linking a user to a feed. Depends on `test_user` and `test_feed` fixtures.

**Returns:** Subscription record dict with keys: `id`, `user_id`, `feed_id`, `subscribed_at`

**Usage:**

```python
def test_subscription_operations(test_subscription, test_user, test_feed):
    subscription_id = test_subscription['id']
    assert test_subscription['user_id'] == test_user['id']
    assert test_subscription['feed_id'] == test_feed['id']
    # ... test logic
```

**Cleanup:** Automatically deletes the subscription

#### `test_reading_list_entry` (function scope)

Creates a test reading list entry linking a user to an article. Depends on `test_user` and `test_article` fixtures.

**Returns:** Reading list entry dict with keys: `id`, `user_id`, `article_id`, `status`, `rating`, `added_at`, `updated_at`

**Usage:**

```python
def test_reading_list_operations(test_reading_list_entry, test_user, test_article):
    entry_id = test_reading_list_entry['id']
    assert test_reading_list_entry['user_id'] == test_user['id']
    assert test_reading_list_entry['article_id'] == test_article['id']
    assert test_reading_list_entry['status'] == 'Unread'
    # ... test logic
```

**Cleanup:** Automatically deletes the reading list entry

## Fixture Dependencies

The fixtures have the following dependency relationships:

```
test_supabase_client
├── test_user
│   ├── test_subscription (also depends on test_feed)
│   └── test_reading_list_entry (also depends on test_article)
├── test_feed
│   ├── test_article
│   │   └── test_reading_list_entry (also depends on test_user)
│   └── test_subscription (also depends on test_user)
```

## Example: Property-Based Test

Here's an example of how to use these fixtures with Hypothesis for property-based testing:

```python
from hypothesis import given, strategies as st
import pytest

@given(discord_id=st.text(min_size=1, max_size=100))
def test_discord_id_uniqueness(test_supabase_client, discord_id):
    """
    Property: For any discord_id, attempting to insert two users with the same
    discord_id should result in the second insertion failing.

    **Validates: Requirements 6.1**
    """
    # Insert first user
    user1 = test_supabase_client.table('users').insert({
        'discord_id': discord_id
    }).execute()

    # Attempt to insert duplicate - should fail
    with pytest.raises(Exception, match="duplicate key"):
        test_supabase_client.table('users').insert({
            'discord_id': discord_id
        }).execute()

    # Cleanup
    test_supabase_client.table('users').delete().eq('id', user1.data[0]['id']).execute()
```

## Best Practices

1. **Use fixtures for test data**: Always use the provided fixtures instead of creating data manually. This ensures proper cleanup and test isolation.

2. **Combine fixtures**: You can use multiple fixtures in a single test. Pytest will handle the dependency resolution automatically.

3. **Cleanup is automatic**: Don't manually delete test data in your tests. The fixtures handle cleanup automatically.

4. **Test isolation**: Each test gets fresh data. Tests don't interfere with each other.

5. **Environment variables**: Make sure `SUPABASE_URL` and `SUPABASE_KEY` are set in your `.env` file before running tests.

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run only property-based tests
pytest tests/ -v -k "property"

# Run with coverage
pytest tests/ --cov=app --cov=scripts --cov-report=html

# Run with a specific Hypothesis profile
HYPOTHESIS_PROFILE=ci pytest tests/ -v
```
