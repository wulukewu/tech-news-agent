# Test Data Isolation

## Problem

Property-based tests using Hypothesis were creating feeds with randomly generated URLs in the Supabase database. When the application's scheduler ran, it attempted to fetch RSS feeds from these invalid URLs, resulting in DNS resolution errors flooding the logs.

Example error:

```
Failed to process feed 'Test Feed' at https://test-feed-{random}.com/rss.xml: [Errno -2] Name or service not known
```

## Root Cause

1. The `test_feed` fixture in `tests/conftest.py` was creating feeds with `is_active=True`
2. Property-based tests generated hundreds of random feed URLs
3. The application's scheduler called `get_active_feeds()` which returned all active feeds, including test feeds
4. The RSS service attempted to fetch from these invalid URLs

## Solution

### 1. Modified Test Fixture

Changed `tests/conftest.py` to create test feeds as inactive by default:

```python
result = test_supabase_client.table('feeds').insert({
    'name': 'Test Feed',
    'url': test_feed_url,
    'category': 'Test Category',
    'is_active': False  # Changed from True to False
}).execute()
```

This ensures that test feeds are not picked up by the scheduler or any code that queries for active feeds.

### 2. Cleanup Script

Created `scripts/cleanup_test_feeds.py` to remove existing test feeds from the database. This script:

- Identifies feeds with test URL patterns (`test-feed-*`, `feed-*`)
- Identifies feeds named 'Test Feed'
- Deletes them from the database

Run the cleanup script:

```bash
python3 scripts/cleanup_test_feeds.py
```

## Best Practices

### For Test Development

1. Always create test data as inactive unless specifically testing active feed behavior
2. Use the `cleanup_test_data` fixture to track and clean up test data
3. Ensure tests clean up after themselves, even if they fail

### For Property-Based Tests

1. Use `@settings(max_examples=5)` to limit the number of test cases
2. Mock external services (RSS fetching, HTTP requests) to avoid actual network calls
3. Use test-specific database or ensure proper isolation

### Database Separation

Consider using separate databases for:

- Development
- Testing
- Production

Set different `SUPABASE_URL` and `SUPABASE_KEY` in your `.env` files for each environment.

## Verification

After applying the fix:

1. Run the cleanup script to remove existing test feeds
2. Restart the application: `docker restart tech-news-agent`
3. Check logs to verify no more DNS errors: `docker logs tech-news-agent --tail 50`
4. Run tests to ensure they still pass: `pytest tests/`

## Related Files

- `tests/conftest.py` - Test fixtures
- `scripts/cleanup_test_feeds.py` - Cleanup script
- `app/tasks/scheduler.py` - Scheduler that fetches active feeds
- `app/services/rss_service.py` - RSS fetching service
