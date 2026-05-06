# Test Database Cleanup Mechanism

**Task 7.2: 建立測試資料庫清理機制**

## Overview

The `cleanup_test_data` fixture provides a comprehensive test database cleanup mechanism that ensures test independence by automatically cleaning up all tracked test data after each test completes.

## Features

- **Automatic Cleanup**: All tracked data is automatically deleted after test completion
- **Cascade-Aware**: Handles foreign key relationships and CASCADE DELETE correctly
- **Test Independence**: Each test starts with a clean slate
- **Error Tolerant**: Ignores cleanup errors (e.g., records already deleted by CASCADE)

## Usage

### Basic Usage

```python
def test_something(test_supabase_client, cleanup_test_data):
    # Create test data
    user = test_supabase_client.table('users').insert({
        'discord_id': 'test_123'
    }).execute().data[0]

    # Track for cleanup
    cleanup_test_data['users'].append(user['id'])

    # Test logic here...
    # Cleanup happens automatically after test
```

### Tracking Multiple Records

```python
def test_multiple_records(test_supabase_client, cleanup_test_data):
    # Create multiple users
    for i in range(3):
        user = test_supabase_client.table('users').insert({
            'discord_id': f'test_user_{i}'
        }).execute().data[0]
        cleanup_test_data['users'].append(user['id'])

    # All users will be cleaned up automatically
```

### Complex Relationships

```python
def test_complex_relationships(test_supabase_client, cleanup_test_data):
    # Create user
    user = test_supabase_client.table('users').insert({
        'discord_id': 'test_user'
    }).execute().data[0]
    cleanup_test_data['users'].append(user['id'])

    # Create feed
    feed = test_supabase_client.table('feeds').insert({
        'name': 'Test Feed',
        'url': 'https://test.com/rss.xml',
        'category': 'Test'
    }).execute().data[0]
    cleanup_test_data['feeds'].append(feed['id'])

    # Create subscription (links user and feed)
    subscription = test_supabase_client.table('user_subscriptions').insert({
        'user_id': user['id'],
        'feed_id': feed['id']
    }).execute().data[0]
    # No need to track subscription - it will be deleted by CASCADE

    # Cleanup will handle all relationships correctly
```

## Available Tracking Lists

The `cleanup_test_data` fixture provides the following tracking lists:

- `cleanup_test_data['users']` - User IDs to clean up
- `cleanup_test_data['feeds']` - Feed IDs to clean up
- `cleanup_test_data['articles']` - Article IDs to clean up
- `cleanup_test_data['subscriptions']` - Subscription IDs to clean up
- `cleanup_test_data['reading_list']` - Reading list entry IDs to clean up

## Cleanup Order

The fixture cleans up data in the following order to respect foreign key constraints:

1. Reading list entries (no dependencies)
2. Subscriptions (no dependencies)
3. Articles (cascades to reading_list)
4. Feeds (cascades to articles and subscriptions)
5. Users (cascades to subscriptions and reading_list)

## CASCADE DELETE Behavior

Due to the database's CASCADE DELETE constraints, you typically only need to track top-level records:

- Tracking a **user** will automatically clean up their subscriptions and reading list entries
- Tracking a **feed** will automatically clean up its articles and subscriptions
- Tracking an **article** will automatically clean up its reading list entries

However, you can explicitly track child records if you prefer for clarity.

## Alternative: Using Existing Fixtures

For simple tests, you can use the existing fixtures that have built-in cleanup:

- `test_user` - Creates and cleans up a test user
- `test_feed` - Creates and cleans up a test feed
- `test_article` - Creates and cleans up a test article
- `test_subscription` - Creates and cleans up a test subscription
- `test_reading_list_entry` - Creates and cleans up a reading list entry

Example:

```python
def test_with_fixtures(test_user, test_feed):
    # test_user and test_feed are automatically created and cleaned up
    assert test_user['discord_id'] is not None
    assert test_feed['url'] is not None
```

## When to Use Each Approach

### Use `cleanup_test_data` when:

- You need to create multiple records of the same type
- You need fine-grained control over cleanup
- You're testing complex scenarios with many relationships
- You're writing property-based tests with Hypothesis

### Use existing fixtures when:

- You need a single instance of each type
- You want simpler test code
- You're writing straightforward unit tests

## Examples

See `tests/test_cleanup_mechanism.py` for comprehensive examples of using the cleanup mechanism.
