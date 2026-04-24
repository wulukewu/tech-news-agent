# Bug 1: DM Notification Duplicates - Counterexamples

## Summary

Bug Condition 1 has been **CONFIRMED** through property-based testing. The bug exploration tests successfully demonstrated that DM notifications send duplicate articles to users.

## Test Results

All 3 bug exploration tests **FAILED** on unfixed code (as expected), confirming the bug exists:

### Test 1: Basic Duplicate Detection

**Status**: ❌ FAILED (confirms bug exists)

**Scenario**:

- User has subscription to 1 feed
- 3 articles exist in last 7 days
- First DM notification sent
- Second DM notification sent (same time window)

**Expected Behavior**:

- Second notification should have 0 articles (all were sent in first notification)

**Actual Behavior**:

- Second notification contains all 3 articles again (100% duplicates)

**Counterexample**:

```
First notification: 3 articles
Second notification: 3 articles (all duplicates)
Duplicate URLs:
- https://test-article-0-1775457304.644534.com/
- https://test-article-1-1775457304.644534.com/
- https://test-article-2-1775457304.644534.com/
```

### Test 2: Property Test Across Multiple Scenarios

**Status**: ❌ FAILED (confirms bug exists)

**Scenarios Tested**:

1. article_count=1, days_back=1 → 1 duplicate article
2. article_count=3, days_back=2 → 3 duplicate articles
3. article_count=5, days_back=3 → 5 duplicate articles
4. article_count=10, days_back=5 → 10 duplicate articles

**Pattern Observed**:

- **100% duplication rate** across all scenarios
- Every article sent in first notification is sent again in second notification
- No filtering or exclusion of previously sent articles

**Counterexample (Scenario 1)**:

```
article_count=1, days_back=1
First notification: 1 article
Second notification: 1 article (duplicate)
Duplicate URL: https://test-article-0-1775457306.836382-1-1.com/
```

### Test 3: New Articles Added Between Notifications

**Status**: ❌ FAILED (confirms bug exists)

**Scenario**:

- First notification: 3 initial articles sent
- 2 new articles added to feed
- Second notification sent

**Expected Behavior**:

- Second notification should have 2 new articles only
- Old articles should be excluded

**Actual Behavior**:

- Second notification contains 5 articles (3 old + 2 new)
- All 3 old articles are duplicated

**Counterexample**:

```
First notification: 3 articles
New articles added: 2 articles
Second notification: 5 articles (3 duplicates + 2 new)

Duplicate URLs:
- https://test-article-initial-0-1775457308.639968.com/
- https://test-article-initial-1-1775457308.639968.com/
- https://test-article-initial-2-1775457308.639968.com/
```

## Root Cause Analysis

The counterexamples confirm the hypothesized root cause:

### 1. Missing Tracking Table

- ❌ No `dm_sent_articles` table exists in database schema
- ❌ No mechanism to record which articles have been sent to which users

### 2. No Deduplication Logic

- ❌ `get_user_articles()` method does not check for previously sent articles
- ❌ No LEFT JOIN to exclude articles from `dm_sent_articles` table
- ❌ Query only filters by: feed subscriptions, time window (7 days), tinkering_index

### 3. No Recording After Send

- ❌ `send_personalized_digest()` does not record sent articles after successful DM
- ❌ No call to track article IDs after `await user.send(embed=embed)` succeeds

## Code Evidence

### Current `get_user_articles()` Query

```python
response = self.client.table('articles')\
    .select('id, title, url, published_at, tinkering_index, ai_summary, feed_id, feeds(category)')\
    .in_('feed_id', feed_ids)\
    .gte('published_at', cutoff_date.isoformat())\
    .not_.is_('tinkering_index', 'null')\
    .order('tinkering_index', desc=True)\
    .limit(limit)\
    .execute()
```

**Missing**: LEFT JOIN with `dm_sent_articles` to exclude previously sent articles

### Current `send_personalized_digest()` Flow

```python
await user.send(embed=embed)
logger.info(f"Successfully sent digest DM to user {discord_id}")
return True
```

**Missing**: Call to `record_sent_articles(discord_id, article_ids)` after successful send

## Impact

This bug causes:

- **Notification Fatigue**: Users receive the same articles repeatedly
- **Poor User Experience**: Weekly digests contain no new content
- **Wasted Resources**: DM notifications sent with duplicate content
- **Loss of Trust**: Users may disable notifications or ignore them

## Next Steps

The bug exploration phase is **COMPLETE**. The counterexamples provide clear evidence that:

1. ✅ Bug exists and is reproducible
2. ✅ Root cause hypothesis is correct
3. ✅ Test cases are ready to validate the fix

**Ready to proceed to implementation phase (Task 7)**.

## Test File Location

`backend/tests/test_dm_notification_duplicates.py`

## Validation Requirements

After fix implementation, these same tests should **PASS**, confirming:

- No duplicate articles are sent in subsequent notifications
- Only new articles are included when new content is available
- Sent articles are properly tracked and excluded
