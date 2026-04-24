# Task 6.2 Implementation Notes: 處理 bot 重啟後的互動

## Overview

This task enhances the persistent views implementation from Task 6.1 to better handle bot restart scenarios. The focus is on improving custom_id parsing, database data reloading, message context loss handling, and comprehensive logging of post-restart interactions.

## Implementation Details

### 1. Enhanced Custom ID Parsing (`app/bot/cogs/persistent_views.py`)

Created a centralized `parse_article_id_from_custom_id()` helper function:

```python
def parse_article_id_from_custom_id(custom_id: str, prefix: str) -> UUID:
    """
    Parse article_id from custom_id.

    Args:
        custom_id: The custom_id string (e.g., "read_later_123e4567-...")
        prefix: The expected prefix (e.g., "read_later_")

    Returns:
        UUID: The parsed article_id

    Raises:
        ValueError: If custom_id format is invalid or UUID is malformed
    """
    if not custom_id.startswith(prefix):
        raise ValueError(f"Invalid custom_id format: expected prefix '{prefix}', got '{custom_id}'")

    article_id_str = custom_id[len(prefix):]
    return UUID(article_id_str)
```

**Benefits:**

- Centralized parsing logic reduces code duplication
- Consistent error handling across all button types
- Clear validation of custom_id format
- Type-safe UUID extraction

### 2. Comprehensive Post-Restart Logging

Created a `log_persistent_interaction()` helper function that logs all persistent view interactions with full context:

```python
def log_persistent_interaction(
    user_id: str,
    action: str,
    article_id: UUID,
    custom_id: str,
    success: bool = True,
    error: str = None
):
    """
    Log persistent view interactions with comprehensive context.

    This helps track interactions that occur after bot restarts,
    including custom_id parsing, database operations, and error handling.
    """
    log_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'user_id': user_id,
        'action': action,
        'article_id': str(article_id),
        'custom_id': custom_id,
        'success': success,
        'interaction_type': 'persistent_view',
    }

    if error:
        log_data['error'] = error
        logger.error(f"Persistent interaction failed: {action} | ...", extra=log_data)
    else:
        logger.info(f"Persistent interaction: {action} | ...", extra=log_data)
```

**Log Data Structure:**

- `timestamp`: ISO 8601 timestamp with timezone
- `user_id`: Discord user ID
- `action`: Action type (read_later, mark_read, rate, deep_dive)
- `article_id`: Article UUID
- `custom_id`: Full custom_id from interaction
- `success`: Boolean indicating operation success
- `interaction_type`: Always "persistent_view" for filtering
- `error`: Error message (only present on failure)

**Benefits:**

- Structured logging enables easy filtering and analysis
- Timestamps help track when interactions occur after restarts
- Full context aids in debugging post-restart issues
- Separate success/failure logging with appropriate levels

### 3. Enhanced Message Context Loss Handling

Updated all persistent button callbacks to handle message context loss more gracefully:

```python
# Disable the button (handle message context loss)
self.disabled = True
try:
    await interaction.message.edit(view=self.view)
except discord.NotFound:
    # Original message was deleted - this is expected after bot restart
    logger.info(
        f"Message not found when disabling button (likely deleted) | "
        f"User: {discord_id} | Article: {article_id}"
    )
except discord.HTTPException as e:
    # Other Discord API errors (rate limit, permissions, etc.)
    logger.warning(
        f"Failed to edit message: {e} | "
        f"User: {discord_id} | Article: {article_id}"
    )
```

**Improvements:**

- Separate handling for `NotFound` (expected) vs `HTTPException` (unexpected)
- Informative logging for both cases
- Operation continues successfully even if message edit fails
- User still receives confirmation message

### 4. Database Reloading in PersistentDeepDiveButton

The `PersistentDeepDiveButton` already implemented database reloading in Task 6.1, but Task 6.2 enhanced it with:

- Better error handling for missing articles
- Comprehensive logging of database operations
- Clear documentation of the reload process

**Flow:**

1. Parse `article_id` from `custom_id`
2. Query database for article by ID
3. Handle missing article gracefully
4. Reconstruct `ArticleSchema` object from database data
5. Generate deep dive analysis
6. Log the entire operation

### 5. Updated All Persistent Button Callbacks

All four persistent button types now follow a consistent pattern:

**PersistentReadLaterButton:**

- Parse custom_id → Save to reading list → Handle message edit → Log interaction

**PersistentMarkReadButton:**

- Parse custom_id → Update status → Handle message edit → Log interaction

**PersistentRatingSelect:**

- Parse custom_id → Update rating → Log interaction

**PersistentDeepDiveButton:**

- Parse custom_id → Reload article from DB → Generate analysis → Log interaction

**Common Error Handling:**

- `ValueError`: Invalid custom_id or UUID format
- `SupabaseServiceError`: Database operation failed
- `Exception`: Unexpected errors

All errors are logged with full context and user receives appropriate error message.

## Testing

Created comprehensive test suite in `tests/bot/test_task_6_2_post_restart_interactions.py`:

### Test Coverage

**1. Custom ID Parsing Tests (6 tests)**

- ✅ Parse read_later custom_id
- ✅ Parse mark_read custom_id
- ✅ Parse rate custom_id
- ✅ Parse deep_dive custom_id
- ✅ Handle invalid prefix
- ✅ Handle invalid UUID

**2. Database Reloading Tests (2 tests)**

- ✅ Deep dive reloads article from database
- ✅ Deep dive handles missing article

**3. Message Context Loss Tests (2 tests)**

- ✅ Handle message not found (NotFound exception)
- ✅ Handle HTTP exception (rate limit, permissions)

**4. Post-Restart Logging Tests (3 tests)**

- ✅ Log successful interaction with full context
- ✅ Log failed interaction with error details
- ✅ Verify log data structure

**5. End-to-End Tests (1 test)**

- ✅ Complete post-restart workflow (parse → reload → action → handle context loss → log)

**Total: 14 tests, all passing**

## Requirements Satisfied

This implementation satisfies the following requirements:

### Requirement 14.3: Stable custom_id patterns

- ✅ Centralized parsing function ensures consistent format
- ✅ Format: `{action}_{article_id}` (e.g., `read_later_123e4567-...`)
- ✅ UUID-based IDs are stable and reconstructable

### Requirement 14.4: Retrieve data from database after restart

- ✅ PersistentDeepDiveButton fetches article from database
- ✅ All buttons use article_id to perform database operations
- ✅ No in-memory state required

### Requirement 14.5: Handle message context loss

- ✅ Separate handling for NotFound vs HTTPException
- ✅ Operations succeed even if message edit fails
- ✅ User always receives confirmation/error message
- ✅ Comprehensive logging of context loss scenarios

### Additional Improvements

**Logging (Requirement 17.1-17.6):**

- ✅ All interactions logged with user_id and action
- ✅ Structured log data for easy filtering
- ✅ Appropriate log levels (INFO for success, ERROR for failure)
- ✅ Full context including timestamps and custom_ids

**Error Handling (Requirement 12.1-12.6):**

- ✅ All errors logged with full context
- ✅ User-friendly error messages in Traditional Chinese
- ✅ No internal error details exposed to users
- ✅ Graceful degradation on failures

## How It Works After Bot Restart

### Scenario: User clicks "稍後閱讀" button after bot restart

1. **Discord sends interaction** → Bot receives interaction with custom_id
2. **Parse custom_id** → Extract article_id using `parse_article_id_from_custom_id()`
3. **Database operation** → Save article to reading list using article_id
4. **Handle message edit** → Try to disable button, catch NotFound/HTTPException
5. **Log interaction** → Record full context with `log_persistent_interaction()`
6. **User feedback** → Send confirmation message

**Key Points:**

- No in-memory state required
- All data fetched from database using article_id
- Message context loss handled gracefully
- Full audit trail via logging

### Scenario: User clicks "深度分析" button after bot restart

1. **Discord sends interaction** → Bot receives interaction with custom_id
2. **Parse custom_id** → Extract article_id
3. **Reload article** → Query database for article by ID
4. **Reconstruct object** → Create ArticleSchema from database data
5. **Generate analysis** → Call LLM service with reconstructed article
6. **Log interaction** → Record full context
7. **User feedback** → Send deep dive analysis

**Key Points:**

- Article data completely reloaded from database
- No dependency on original message or in-memory state
- Missing articles handled gracefully
- Full audit trail via logging

## Comparison with Task 6.1

| Aspect               | Task 6.1                | Task 6.2                                        |
| -------------------- | ----------------------- | ----------------------------------------------- |
| Custom ID parsing    | Inline in each callback | Centralized helper function                     |
| Logging              | Basic logger.info/error | Structured logging with full context            |
| Message context loss | Simple try/except       | Separate handling for NotFound vs HTTPException |
| Database reloading   | Only in DeepDiveButton  | Documented and tested                           |
| Error handling       | Basic                   | Comprehensive with specific error types         |
| Testing              | 8 basic tests           | 14 comprehensive tests                          |

## Future Improvements

Potential enhancements for future iterations:

1. **Metrics tracking**: Track button click rates, success rates, error rates
2. **Performance monitoring**: Log operation duration for database queries
3. **Retry logic**: Automatic retry for transient database errors
4. **Batch operations**: Support bulk actions on multiple articles
5. **User notifications**: Notify users of failed operations via DM

## Conclusion

Task 6.2 successfully enhances the persistent views implementation with:

- Robust custom_id parsing
- Comprehensive post-restart logging
- Graceful message context loss handling
- Well-tested database reloading

All requirements (14.3, 14.4, 14.5) are satisfied, and the system now provides a complete audit trail of all post-restart interactions.
