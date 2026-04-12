# Bot Logging and Error Handling Integration

## Overview

This document describes the integration of centralized logging and unified error handling into Discord bot cogs, completed as part of Task 13.3.

## Changes Made

### 1. Replaced Standard Logging with Structured Logging

All bot cogs now use the centralized structured logging system from `app.core.logger`:

**Before:**

```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"User {user_id} executed command")
```

**After:**

```python
from app.core.logger import get_logger
logger = get_logger(__name__)
logger.info("User executed command", user_id=user_id, command="news_now")
```

### 2. Enhanced Error Handling with User-Friendly Messages

All error handlers now provide:

- Clear error indicators (❌)
- Actionable suggestions (💡 建議)
- Appropriate log levels (error, critical)
- Structured context (user_id, command, error details)

**Example:**

```python
except SupabaseServiceError as e:
    logger.error(
        "Database error in /news_now command",
        user_id=str(interaction.user.id),
        command="news_now",
        error=str(e),
        exc_info=True
    )
    await interaction.followup.send(
        "❌ 無法取得文章資料，請稍後再試。\n"
        "💡 建議：資料庫連線可能暫時中斷，請稍後再試或聯繫管理員。",
        ephemeral=True
    )
```

### 3. Consistent Logging Patterns

All bot commands now follow consistent logging patterns:

1. **Command Start**: Log when command is triggered

   ```python
   logger.info(
       "Command /news_now triggered",
       user_id=str(interaction.user.id),
       command="news_now"
   )
   ```

2. **Success**: Log successful operations

   ```python
   logger.info(
       "Successfully sent news_now response",
       user_id=str(interaction.user.id),
       article_count=len(articles)
   )
   ```

3. **Errors**: Log errors with appropriate severity

   ```python
   logger.error(
       "Database error in /news_now command",
       user_id=str(interaction.user.id),
       command="news_now",
       error=str(e),
       exc_info=True
   )
   ```

4. **Critical Errors**: Use critical level for unexpected errors
   ```python
   logger.critical(
       "Unexpected error in /news_now command",
       user_id=str(interaction.user.id),
       command="news_now",
       error=str(e),
       error_type=type(e).__name__,
       exc_info=True
   )
   ```

## Updated Cogs

### 1. NewsCommands (`news_commands.py`)

- ✅ Structured logging with user context
- ✅ User-friendly error messages with suggestions
- ✅ Appropriate log levels (info, error, critical)

### 2. SubscriptionCommands (`subscription_commands.py`)

- ✅ Structured logging for all commands (add_feed, list_feeds, unsubscribe_feed)
- ✅ User-friendly error messages with actionable suggestions
- ✅ Validation error handling with clear messages

### 3. ReadingListCog (`reading_list.py`)

- ✅ Structured logging for commands and UI components
- ✅ Error handling in buttons (MarkAsReadButton) and selects (RatingSelect)
- ✅ LLM service error handling with user-friendly messages

### 4. AdminCommands (`admin_commands.py`)

- ✅ Structured logging for admin operations
- ✅ Scheduler status logging with health metrics
- ✅ User-friendly error messages for admin failures

### 5. NotificationSettings (`notification_settings.py`)

- ✅ Structured logging for notification settings
- ✅ User-friendly error messages with suggestions
- ✅ Success/failure logging with context

## Log Output Format

All logs are now output in structured JSON format:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "level": "INFO",
  "logger": "app.bot.cogs.news_commands",
  "message": "Command /news_now triggered",
  "extra": {
    "user_id": "123456789",
    "command": "news_now"
  }
}
```

For errors, additional fields are included:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "level": "ERROR",
  "logger": "app.bot.cogs.news_commands",
  "message": "Database error in /news_now command",
  "extra": {
    "user_id": "123456789",
    "command": "news_now",
    "error": "Connection timeout"
  },
  "exception": "Traceback (most recent call last):\n  ...",
  "source": {
    "file": "/app/bot/cogs/news_commands.py",
    "line": 42,
    "function": "news_now"
  }
}
```

## Requirements Validated

This implementation validates the following requirements:

### Requirement 4.4: Error Handler Logs All Errors

✅ All errors are logged with appropriate severity levels:

- `logger.error()` for expected errors (database, validation)
- `logger.critical()` for unexpected errors
- `exc_info=True` for exception tracebacks

### Requirement 5.3: Logger Includes Request Context

✅ All logs include user context:

- `user_id`: Discord user ID
- `command`: Command name
- Additional context: article_id, feed_id, rating, etc.

### Requirement 13.1: Clear Error Messages with Actionable Suggestions

✅ All error messages include:

- Clear error indicator (❌)
- User-friendly description
- Actionable suggestion (💡 建議)
- Next steps for the user

## Testing

Integration tests verify:

1. ✅ All cogs use structured logger
2. ✅ Logger produces JSON output
3. ✅ Error messages include actionable suggestions
4. ✅ Logs include user context

Run tests:

```bash
python3 -m pytest backend/tests/test_bot_logging_integration.py -v
```

## Benefits

1. **Consistent Logging**: All bot commands use the same logging format
2. **Better Debugging**: Structured logs are easier to search and analyze
3. **User Experience**: Clear error messages help users understand what went wrong
4. **Monitoring**: JSON logs can be easily ingested by log aggregation tools
5. **Traceability**: User context in logs helps track user actions and issues

## Migration Notes

- No breaking changes to bot functionality
- All existing commands work as before
- Error messages are now more user-friendly
- Logs are now structured JSON instead of plain text

## Future Improvements

1. Add request_id tracking for bot commands (similar to API requests)
2. Implement log aggregation and monitoring dashboard
3. Add performance metrics logging (command execution time)
4. Create alerts for critical errors
5. Add user feedback mechanism for error messages
