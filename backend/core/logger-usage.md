# Centralized Logging System - Usage Guide

## Overview

The centralized logging system provides structured logging with consistent format, multiple log levels, automatic request context injection, and log filtering capabilities.

## Features

- **Structured JSON Logs**: All logs are formatted as JSON with consistent fields
- **Multiple Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Request Context**: Automatic injection of `request_id` and `user_id` into logs
- **Extra Fields**: Support for custom fields in log entries
- **Exception Tracking**: Automatic exception traceback capture
- **Source Location**: ERROR and CRITICAL logs include file, line, and function info

## Quick Start

### 1. Basic Usage

```python
from app.core.logger import get_logger

# Create logger (typically at module level)
logger = get_logger(__name__)

# Log messages
logger.info("Application started")
logger.debug("Debug information", extra_field="value")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
logger.critical("Critical failure")
```

### 2. Logging with Extra Fields

```python
logger.info(
    "User logged in",
    user_id="123",
    action="login",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0"
)
```

**Output:**

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "level": "INFO",
  "logger": "app.services.auth",
  "message": "User logged in",
  "extra": {
    "user_id": "123",
    "action": "login",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0"
  }
}
```

### 3. Error Logging with Exception

```python
try:
    result = risky_operation()
except Exception as e:
    logger.error(
        "Operation failed",
        exc_info=True,
        operation="risky_operation",
        input_data=input_value
    )
```

**Output:**

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "level": "ERROR",
  "logger": "app.services.processor",
  "message": "Operation failed",
  "exception": "Traceback (most recent call last):\n  File ...",
  "extra": {
    "operation": "risky_operation",
    "input_data": "some_value"
  },
  "source": {
    "file": "/app/services/processor.py",
    "line": 42,
    "function": "process_data"
  }
}
```

## Request Context Middleware

### Setup in FastAPI

Add the middleware to your FastAPI application:

```python
from fastapi import FastAPI
from app.core.logger import RequestContextMiddleware

app = FastAPI()

# Add middleware (should be added AFTER auth middleware)
app.add_middleware(RequestContextMiddleware)
```

### Middleware Order

The logging middleware should be added **after** authentication middleware so it can capture the `user_id`:

```python
# Correct order
app.add_middleware(RequestContextMiddleware)  # Logging (runs second)
app.add_middleware(AuthMiddleware)            # Auth (runs first)
```

### Automatic Context Injection

Once the middleware is active, all logs within a request will automatically include:

- `request_id`: Unique identifier for the request (from `X-Request-ID` header or auto-generated)
- `user_id`: User identifier from `request.state.user_id` (if set by auth middleware)

**Example log with context:**

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "level": "INFO",
  "logger": "app.api.articles",
  "message": "Article created",
  "context": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user-123"
  },
  "extra": {
    "article_id": "article-456",
    "title": "New Article"
  }
}
```

## Log Levels

### When to Use Each Level

| Level        | Use Case                                                           | Example                                                   |
| ------------ | ------------------------------------------------------------------ | --------------------------------------------------------- |
| **DEBUG**    | Detailed diagnostic information                                    | Variable values, function entry/exit                      |
| **INFO**     | General informational messages                                     | User actions, system events                               |
| **WARNING**  | Warning messages for potentially harmful situations                | Deprecated API usage, fallback behavior                   |
| **ERROR**    | Error events that might still allow the application to continue    | Failed API calls, validation errors                       |
| **CRITICAL** | Very severe error events that might cause the application to abort | Database connection failure, critical service unavailable |

### Setting Log Level

```python
import logging
from app.core.logger import get_logger

# Create logger with specific level
logger = get_logger(__name__, level=logging.DEBUG)

# Change level dynamically
logger.set_level(logging.WARNING)
```

## Integration Examples

### Service Layer

```python
from app.core.logger import get_logger

logger = get_logger(__name__)

class ArticleService:
    def create_article(self, user_id: str, title: str, content: str):
        logger.info(
            "Creating article",
            user_id=user_id,
            title=title,
            content_length=len(content)
        )

        try:
            article = self.repository.create(user_id, title, content)
            logger.info(
                "Article created successfully",
                article_id=article.id,
                user_id=user_id
            )
            return article
        except Exception as e:
            logger.error(
                "Failed to create article",
                exc_info=True,
                user_id=user_id,
                title=title
            )
            raise
```

### API Endpoint

```python
from fastapi import APIRouter, Request
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/articles")
async def create_article(request: Request, data: ArticleCreate):
    logger.info(
        "Article creation request received",
        title=data.title,
        tags=data.tags
    )

    try:
        article = article_service.create_article(
            user_id=request.state.user_id,
            title=data.title,
            content=data.content
        )

        logger.info(
            "Article creation successful",
            article_id=article.id
        )

        return {"article": article}
    except ValidationError as e:
        logger.warning(
            "Article validation failed",
            errors=e.errors()
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Article creation failed",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Background Task

```python
from app.core.logger import get_logger

logger = get_logger(__name__)

async def process_rss_feeds():
    logger.info("Starting RSS feed processing")

    feeds = await get_active_feeds()
    logger.info(f"Processing {len(feeds)} feeds", feed_count=len(feeds))

    for feed in feeds:
        try:
            logger.debug(
                "Processing feed",
                feed_id=feed.id,
                feed_url=feed.url
            )

            articles = await fetch_feed(feed.url)
            logger.info(
                "Feed processed",
                feed_id=feed.id,
                article_count=len(articles)
            )
        except Exception as e:
            logger.error(
                "Feed processing failed",
                exc_info=True,
                feed_id=feed.id,
                feed_url=feed.url
            )

    logger.info("RSS feed processing completed")
```

## Log Format Reference

### Standard Fields (Always Present)

- `timestamp`: ISO 8601 format with UTC timezone
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logger`: Logger name (typically module name)
- `message`: Log message

### Optional Fields

- `context`: Request context (present when logging within a request)
  - `request_id`: Unique request identifier
  - `user_id`: User identifier (if authenticated)
- `extra`: Custom fields passed to logger
- `exception`: Exception traceback (when `exc_info=True`)
- `source`: Source location (for ERROR and CRITICAL levels)
  - `file`: File path
  - `line`: Line number
  - `function`: Function name

## Best Practices

### 1. Use Appropriate Log Levels

```python
# Good
logger.info("User logged in", user_id=user_id)
logger.error("Database connection failed", exc_info=True)

# Bad
logger.error("User logged in")  # Not an error
logger.info("Critical system failure")  # Should be ERROR or CRITICAL
```

### 2. Include Relevant Context

```python
# Good
logger.error(
    "Failed to process article",
    exc_info=True,
    article_id=article_id,
    user_id=user_id,
    operation="summarize"
)

# Bad
logger.error("Failed")  # No context
```

### 3. Use Structured Fields Instead of String Formatting

```python
# Good
logger.info("User action", user_id=user_id, action="login")

# Bad
logger.info(f"User {user_id} performed action login")
```

### 4. Log Exceptions with Traceback

```python
# Good
try:
    risky_operation()
except Exception:
    logger.error("Operation failed", exc_info=True)

# Bad
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")  # No traceback
```

### 5. Avoid Logging Sensitive Data

```python
# Good
logger.info("User authenticated", user_id=user_id)

# Bad
logger.info("User authenticated", password=password)  # Never log passwords
```

## Troubleshooting

### Logs Not Showing Request Context

**Problem**: Logs don't include `request_id` or `user_id`

**Solution**: Ensure `RequestContextMiddleware` is added to your FastAPI app:

```python
app.add_middleware(RequestContextMiddleware)
```

### User ID Not Captured

**Problem**: `user_id` is `null` in logs even for authenticated requests

**Solution**: Ensure auth middleware sets `request.state.user_id` and runs **before** logging middleware:

```python
# In auth middleware
request.state.user_id = user.id

# Middleware order
app.add_middleware(RequestContextMiddleware)  # Second
app.add_middleware(AuthMiddleware)            # First
```

### Logs Too Verbose

**Problem**: Too many DEBUG logs in production

**Solution**: Set appropriate log level:

```python
import logging
from app.core.logger import set_global_log_level

# In production
set_global_log_level(logging.INFO)

# In development
set_global_log_level(logging.DEBUG)
```

## Migration from Old Logging

### Before (Standard Logging)

```python
import logging

logger = logging.getLogger(__name__)
logger.info(f"User {user_id} logged in")
```

### After (Structured Logging)

```python
from app.core.logger import get_logger

logger = get_logger(__name__)
logger.info("User logged in", user_id=user_id)
```

## Performance Considerations

- Structured logging has minimal overhead (~5-10% compared to standard logging)
- JSON serialization is fast for typical log volumes
- Context variables use Python's `contextvars` for thread-safe, async-safe storage
- Log filtering happens at the logger level, so disabled logs have near-zero cost
