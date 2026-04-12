# Service Layer Documentation

## Overview

The service layer is the business logic layer in the Tech News Agent application. It sits between the API controllers and the repository layer, implementing business rules, orchestrating operations, and managing workflows.

## Architecture

```
API Routes → Controllers → Services → Repositories → Database
                              ↓
                    External Services (LLM, RSS, Notion)
```

## Service Layer Principles

### 1. Clean Architecture

Services follow Clean Architecture principles:

- **Depend on abstractions**: Services depend on repository interfaces, not concrete implementations
- **Dependency inversion**: Dependencies are injected, not created
- **Single responsibility**: Each service has a clear, focused purpose
- **Separation of concerns**: Business logic is separated from data access and presentation

### 2. Dependency Injection

All services use constructor-based dependency injection:

```python
class ArticleService(BaseService):
    def __init__(
        self,
        article_repo: IArticleRepository,
        feed_repo: IFeedRepository,
        llm_service: LLMService
    ):
        super().__init__()
        self.article_repo = article_repo
        self.feed_repo = feed_repo
        self.llm_service = llm_service
        self.logger = get_logger(f"{__name__}.ArticleService")
```

Benefits:

- **Testability**: Easy to mock dependencies in tests
- **Flexibility**: Can swap implementations without changing service code
- **Clarity**: Dependencies are explicit and visible
- **Decoupling**: Services don't know about concrete implementations

### 3. Repository Pattern

Services MUST use repositories for data access:

✅ **DO**: Use repository methods

```python
article = await self.article_repo.get_by_id(article_id)
articles = await self.article_repo.list(filters={"status": "published"})
```

❌ **DON'T**: Access database directly

```python
# WRONG - Don't do this!
response = self.client.table('articles').select('*').execute()
```

## Service Responsibilities

### What Services Should Do

1. **Business Logic**
   - Implement business rules and workflows
   - Validate business constraints
   - Transform data between layers

2. **Orchestration**
   - Coordinate operations across multiple repositories
   - Call external services (LLM, RSS, etc.)
   - Manage complex workflows

3. **Error Handling**
   - Catch and wrap repository errors
   - Provide business-level error messages
   - Log errors with context

4. **Logging**
   - Log business operations
   - Track operation performance
   - Include structured context

### What Services Should NOT Do

1. ❌ **Direct Database Access**
   - Don't use Supabase client directly
   - Use repositories instead

2. ❌ **HTTP Request/Response Handling**
   - Don't parse request bodies
   - Don't format HTTP responses
   - That's the controller's job

3. ❌ **Presentation Logic**
   - Don't format data for display
   - Return domain models, not view models

4. ❌ **Database-Specific Logic**
   - Don't write SQL queries
   - Don't handle database connections
   - That's the repository's job

## Creating a New Service

### Step 1: Define the Service Class

```python
from app.services.base import BaseService
from app.repositories.article import IArticleRepository
from app.core.logger import get_logger
from app.core.errors import ServiceError, ErrorCode

class ArticleService(BaseService):
    """
    Service for article management.

    This service handles:
    - Article creation and updates
    - AI summary generation
    - Article recommendations

    Requirements: 5.1, 5.2, 5.3
    """

    def __init__(
        self,
        article_repo: IArticleRepository,
        feed_repo: IFeedRepository
    ):
        """
        Initialize the article service.

        Args:
            article_repo: Repository for article data access
            feed_repo: Repository for feed data access
        """
        super().__init__()
        self.article_repo = article_repo
        self.feed_repo = feed_repo
        self.logger = get_logger(f"{__name__}.ArticleService")
```

### Step 2: Implement Business Methods

```python
    async def create_article(
        self,
        article_data: Dict[str, Any]
    ) -> Article:
        """
        Create a new article.

        Validates that the feed exists before creating the article.

        Args:
            article_data: Article data including feed_id, title, url, etc.

        Returns:
            Created article

        Raises:
            ServiceError: If feed not found or creation fails
        """
        self.logger.info(
            "Creating article",
            feed_id=article_data.get('feed_id'),
            title=article_data.get('title')
        )

        try:
            # Validate feed exists (business rule)
            feed = await self.feed_repo.get_by_id(article_data['feed_id'])
            if not feed:
                raise ServiceError(
                    f"Feed not found: {article_data['feed_id']}",
                    error_code=ErrorCode.RESOURCE_NOT_FOUND,
                    details={"feed_id": str(article_data['feed_id'])}
                )

            # Create article via repository
            article = await self.article_repo.create(article_data)

            self.logger.info(
                "Successfully created article",
                article_id=str(article.id),
                feed_id=str(article.feed_id)
            )

            return article

        except ServiceError:
            raise
        except Exception as e:
            self._handle_error(
                e,
                "Failed to create article",
                context={"article_data": article_data}
            )
```

### Step 3: Create Dependency Provider

Create or update `backend/app/core/dependencies.py`:

```python
from app.repositories.article import ArticleRepository
from app.repositories.feed import FeedRepository
from app.services.article import ArticleService
from app.core.database import get_supabase_client

def get_article_service() -> ArticleService:
    """
    Create and return an ArticleService instance with dependencies.

    This function is used by FastAPI's dependency injection system.
    """
    client = get_supabase_client()

    article_repo = ArticleRepository(client, "articles")
    feed_repo = FeedRepository(client, "feeds")

    return ArticleService(
        article_repo=article_repo,
        feed_repo=feed_repo
    )
```

### Step 4: Use in API Routes

```python
from fastapi import APIRouter, Depends
from app.services.article import ArticleService
from app.core.dependencies import get_article_service

router = APIRouter()

@router.post("/articles")
async def create_article(
    article_data: ArticleCreate,
    service: ArticleService = Depends(get_article_service)
):
    """Create a new article."""
    article = await service.create_article(article_data.dict())
    return {"data": article}
```

## Testing Services

### Unit Testing with Mocks

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from app.services.article import ArticleService
from app.core.errors import ServiceError, ErrorCode

@pytest.fixture
def mock_article_repo():
    return AsyncMock()

@pytest.fixture
def mock_feed_repo():
    return AsyncMock()

@pytest.fixture
def service(mock_article_repo, mock_feed_repo):
    return ArticleService(
        article_repo=mock_article_repo,
        feed_repo=mock_feed_repo
    )

@pytest.mark.asyncio
async def test_create_article_success(service, mock_article_repo, mock_feed_repo):
    # Arrange
    feed_id = UUID("12345678-1234-1234-1234-123456789012")
    article_data = {
        "feed_id": feed_id,
        "title": "Test Article",
        "url": "https://example.com/article"
    }

    mock_feed_repo.get_by_id.return_value = MagicMock(id=feed_id)
    mock_article_repo.create.return_value = MagicMock(
        id=UUID("87654321-4321-4321-4321-210987654321"),
        title="Test Article"
    )

    # Act
    result = await service.create_article(article_data)

    # Assert
    assert result is not None
    assert result.title == "Test Article"
    mock_feed_repo.get_by_id.assert_called_once_with(feed_id)
    mock_article_repo.create.assert_called_once_with(article_data)

@pytest.mark.asyncio
async def test_create_article_feed_not_found(service, mock_feed_repo):
    # Arrange
    article_data = {
        "feed_id": UUID("12345678-1234-1234-1234-123456789012"),
        "title": "Test Article"
    }
    mock_feed_repo.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(ServiceError) as exc_info:
        await service.create_article(article_data)

    assert exc_info.value.error_code == ErrorCode.RESOURCE_NOT_FOUND
    assert "Feed not found" in str(exc_info.value)
```

### Integration Testing

```python
import pytest
from app.services.article import ArticleService
from app.repositories.article import ArticleRepository
from app.repositories.feed import FeedRepository
from app.core.database import get_test_supabase_client

@pytest.fixture
def integration_service():
    """Create service with real repositories for integration testing."""
    client = get_test_supabase_client()

    article_repo = ArticleRepository(client, "articles")
    feed_repo = FeedRepository(client, "feeds")

    return ArticleService(
        article_repo=article_repo,
        feed_repo=feed_repo
    )

@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_article_integration(integration_service, test_feed):
    # Arrange
    article_data = {
        "feed_id": test_feed.id,
        "title": "Integration Test Article",
        "url": "https://example.com/integration-test"
    }

    # Act
    article = await integration_service.create_article(article_data)

    # Assert
    assert article is not None
    assert article.title == "Integration Test Article"
    assert article.feed_id == test_feed.id
```

## Error Handling

### Using BaseService Error Handling

```python
async def complex_operation(self, data: Dict[str, Any]) -> Result:
    """
    Perform a complex operation with proper error handling.
    """
    self.logger.info("Starting complex operation")

    try:
        # Business logic here
        result = await self._do_something(data)
        return result

    except ServiceError:
        # Re-raise service errors (already wrapped)
        raise

    except Exception as e:
        # Wrap other errors with context
        self._handle_error(
            e,
            "Failed to perform complex operation",
            error_code=ErrorCode.SERVICE_ERROR,
            context={"data": data}
        )
```

### Custom Error Handling

```python
async def validate_and_process(self, data: Dict[str, Any]) -> Result:
    """
    Validate data and process with custom error messages.
    """
    # Business rule validation
    if not data.get('required_field'):
        raise ServiceError(
            "Missing required field",
            error_code=ErrorCode.VALIDATION_BUSINESS_RULE,
            details={
                "field": "required_field",
                "message": "This field is required for processing"
            }
        )

    # Process data
    try:
        result = await self.repository.process(data)
        return result
    except Exception as e:
        self._handle_error(
            e,
            "Processing failed",
            context={"data": data}
        )
```

## Logging Best Practices

### Structured Logging

```python
# Good: Structured logging with context
self.logger.info(
    "Creating article",
    operation="create_article",
    feed_id=str(feed_id),
    title=title,
    user_id=str(user_id)
)

# Bad: Unstructured logging
self.logger.info(f"Creating article {title} for feed {feed_id}")
```

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about operations
- **WARNING**: Warning messages for recoverable issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors requiring immediate attention

```python
# DEBUG: Detailed debugging information
self.logger.debug(
    "Fetching articles from repository",
    filters=filters,
    limit=limit
)

# INFO: Normal operation
self.logger.info(
    "Successfully created article",
    article_id=str(article.id)
)

# WARNING: Recoverable issue
self.logger.warning(
    "Feed has no active subscriptions",
    feed_id=str(feed_id)
)

# ERROR: Operation failed
self.logger.error(
    "Failed to generate AI summary",
    exc_info=True,
    article_id=str(article_id),
    error=str(e)
)
```

## Migration Guide

### Migrating Existing Services

When refactoring existing services to use the repository pattern:

#### Step 1: Identify Direct Database Access

Find all places where the service directly uses the Supabase client:

```python
# Before
response = self.client.table('articles').select('*').eq('id', article_id).execute()
```

#### Step 2: Create Repository Methods

Ensure the repository has methods for the required operations:

```python
# In IArticleRepository
async def get_by_id(self, entity_id: UUID) -> Optional[Article]:
    """Get article by ID."""
    pass
```

#### Step 3: Update Service Constructor

Replace database client with repository:

```python
# Before
def __init__(self, supabase_client: Client):
    self.client = supabase_client

# After
def __init__(self, article_repo: IArticleRepository):
    super().__init__()
    self.article_repo = article_repo
    self.logger = get_logger(f"{__name__}.ArticleService")
```

#### Step 4: Replace Database Calls

Replace direct database calls with repository methods:

```python
# Before
response = self.client.table('articles').select('*').eq('id', article_id).execute()
article = response.data[0] if response.data else None

# After
article = await self.article_repo.get_by_id(article_id)
```

#### Step 5: Update Tests

Update tests to mock repositories instead of database client:

```python
# Before
@pytest.fixture
def service(mock_supabase_client):
    return ArticleService(mock_supabase_client)

# After
@pytest.fixture
def service(mock_article_repo):
    return ArticleService(mock_article_repo)
```

#### Step 6: Update Dependency Injection

Update the dependency provider:

```python
# Before
def get_article_service() -> ArticleService:
    client = get_supabase_client()
    return ArticleService(client)

# After
def get_article_service() -> ArticleService:
    client = get_supabase_client()
    article_repo = ArticleRepository(client, "articles")
    return ArticleService(article_repo)
```

## Common Patterns

### Multi-Repository Operations

```python
async def create_article_with_subscription(
    self,
    user_id: UUID,
    article_data: Dict[str, Any]
) -> Tuple[Article, Subscription]:
    """
    Create an article and automatically subscribe the user.

    This demonstrates coordinating operations across multiple repositories.
    """
    self.logger.info(
        "Creating article with subscription",
        user_id=str(user_id)
    )

    try:
        # Create article
        article = await self.article_repo.create(article_data)

        # Create subscription
        subscription = await self.subscription_repo.create({
            "user_id": str(user_id),
            "article_id": str(article.id)
        })

        self.logger.info(
            "Successfully created article with subscription",
            article_id=str(article.id),
            subscription_id=str(subscription.id)
        )

        return article, subscription

    except Exception as e:
        self._handle_error(
            e,
            "Failed to create article with subscription",
            context={
                "user_id": str(user_id),
                "article_data": article_data
            }
        )
```

### Calling Other Services

```python
async def create_article_with_summary(
    self,
    article_data: Dict[str, Any]
) -> Article:
    """
    Create an article and generate AI summary.

    This demonstrates calling another service (LLM service).
    """
    self.logger.info("Creating article with AI summary")

    try:
        # Generate summary using LLM service
        summary = await self.llm_service.generate_summary(
            article_data['title'],
            article_data.get('content', '')
        )

        # Add summary to article data
        article_data['ai_summary'] = summary

        # Create article
        article = await self.article_repo.create(article_data)

        self.logger.info(
            "Successfully created article with summary",
            article_id=str(article.id)
        )

        return article

    except Exception as e:
        self._handle_error(
            e,
            "Failed to create article with summary",
            context={"article_data": article_data}
        )
```

### Pagination Support

```python
async def list_articles_paginated(
    self,
    page: int = 1,
    page_size: int = 20,
    filters: Optional[Dict[str, Any]] = None
) -> PaginatedResult[Article]:
    """
    List articles with pagination.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        filters: Optional filters

    Returns:
        Paginated result with articles and metadata
    """
    self.logger.info(
        "Listing articles with pagination",
        page=page,
        page_size=page_size,
        filters=filters
    )

    try:
        # Calculate offset
        offset = (page - 1) * page_size

        # Get articles
        articles = await self.article_repo.list(
            filters=filters,
            limit=page_size,
            offset=offset,
            order_by="published_at",
            ascending=False
        )

        # Get total count
        total_count = await self.article_repo.count(filters=filters)

        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1

        return PaginatedResult(
            items=articles,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )

    except Exception as e:
        self._handle_error(
            e,
            "Failed to list articles",
            context={
                "page": page,
                "page_size": page_size,
                "filters": filters
            }
        )
```

## Summary

The service layer is the heart of the application's business logic. By following these patterns and principles, you can create maintainable, testable, and scalable services that properly separate concerns and follow Clean Architecture principles.

Key takeaways:

- ✅ Use dependency injection for all dependencies
- ✅ Depend on repository interfaces, not concrete implementations
- ✅ Handle errors consistently with proper logging
- ✅ Write comprehensive tests with mocked dependencies
- ✅ Keep services focused on business logic
- ❌ Never access the database directly
- ❌ Don't mix presentation logic with business logic
- ❌ Don't create dependencies inside services
