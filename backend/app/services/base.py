"""
Service Layer Base Interfaces and Patterns

This module defines the base interfaces and patterns for the service layer in the
Tech News Agent application. Services encapsulate business logic and orchestrate
operations across multiple repositories and external services.

The service layer follows Clean Architecture principles:
- Services depend on repository interfaces, not concrete implementations
- Services are injected with their dependencies (dependency injection pattern)
- Services handle business logic, validation, and orchestration
- Services do not directly access database clients

Architecture:
    API Routes → Controllers → Services → Repositories → Database

Service Responsibilities:
- Business logic and workflow orchestration
- Cross-repository operations and transactions
- Business rule validation
- Integration with external services (LLM, RSS, Notion, etc.)
- Error handling and logging at business logic level

Service Boundaries:
- Services SHALL NOT directly access database clients
- Services SHALL depend on repository interfaces for data access
- Services SHALL handle business-level errors and exceptions
- Services SHALL log business operations with appropriate context
- Services MAY call other services for complex workflows

Validates: Requirements 3.1, 3.3, 3.5
"""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from app.core.errors import ErrorCode
from app.core.logger import get_logger

# Generic type variable for service return types
T = TypeVar("T")


class IService(ABC):
    """
    Base service interface defining common service patterns.

    All services should inherit from this interface to ensure consistent
    patterns across the application. This interface establishes the contract
    for service initialization, dependency injection, and lifecycle management.

    Validates: Requirements 3.1, 3.5
    """

    @abstractmethod
    def __init__(self, **dependencies):
        """
        Initialize the service with its dependencies.

        Services should accept their dependencies (repositories, other services,
        external clients) as constructor parameters. This enables dependency
        injection and makes services testable.

        Example:
            def __init__(
                self,
                user_repo: IUserRepository,
                article_repo: IArticleRepository,
                logger: Optional[Logger] = None
            ):
                self.user_repo = user_repo
                self.article_repo = article_repo
                self.logger = logger or get_logger(__name__)

        Args:
            **dependencies: Service dependencies (repositories, clients, etc.)
        """
        pass


class BaseService(IService):
    """
    Base service implementation with common patterns.

    This class provides a concrete implementation of common service patterns
    including logging, error handling, and dependency management. Services
    should extend this class to inherit these patterns.

    The BaseService provides:
    - Structured logging with service context
    - Consistent error handling and wrapping
    - Dependency injection support
    - Service lifecycle management

    Example Usage:
        class ArticleService(BaseService):
            def __init__(
                self,
                article_repo: IArticleRepository,
                feed_repo: IFeedRepository
            ):
                super().__init__()
                self.article_repo = article_repo
                self.feed_repo = feed_repo
                self.logger = get_logger(f"{__name__}.ArticleService")

            async def get_article_with_feed(self, article_id: UUID) -> ArticleWithFeed:
                self.logger.info(
                    "Fetching article with feed",
                    article_id=str(article_id)
                )

                article = await self.article_repo.get_by_id(article_id)
                if not article:
                    raise ServiceError(
                        f"Article not found: {article_id}",
                        error_code=ErrorCode.RESOURCE_NOT_FOUND
                    )

                feed = await self.feed_repo.get_by_id(article.feed_id)

                return ArticleWithFeed(article=article, feed=feed)

    Validates: Requirements 3.1, 3.3, 3.5
    """

    def __init__(self):
        """
        Initialize the base service.

        Subclasses should call super().__init__() and then initialize their
        own dependencies and logger.
        """
        self._logger = None

    @property
    def logger(self):
        """
        Get the service logger.

        Returns a logger instance for this service. If not set, returns a
        default logger for the BaseService class.

        Returns:
            Logger instance
        """
        if self._logger is None:
            self._logger = get_logger(self.__class__.__name__)
        return self._logger

    @logger.setter
    def logger(self, logger):
        """
        Set the service logger.

        Args:
            logger: Logger instance to use for this service
        """
        self._logger = logger

    def _handle_error(
        self,
        error: Exception,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Handle and wrap service errors consistently.

        This method logs the error with context and wraps it in a ServiceError
        if it's not already a service-level error. This ensures consistent
        error handling across all services.

        Args:
            error: The original exception
            message: Human-readable error message
            error_code: Error code for the service error
            context: Additional context for debugging

        Raises:
            ServiceError: Wrapped error with context
        """
        self.logger.error(
            message,
            exc_info=True,
            error=str(error),
            error_type=type(error).__name__,
            **(context or {}),
        )

        # Import here to avoid circular dependency
        from app.core.errors import AppException, ServiceError

        # If it's already an AppException, re-raise it
        if isinstance(error, AppException):
            raise

        # Wrap other errors in ServiceError
        raise ServiceError(
            message,
            error_code=error_code,
            details={
                "original_error": str(error),
                "error_type": type(error).__name__,
                **(context or {}),
            },
            original_error=error,
        )


# Dependency Injection Pattern Documentation
"""
Dependency Injection Pattern for Services

The service layer uses constructor-based dependency injection to manage
dependencies. This pattern provides several benefits:

1. Testability: Services can be tested with mock repositories
2. Flexibility: Different implementations can be injected
3. Decoupling: Services depend on interfaces, not concrete classes
4. Clarity: Dependencies are explicit in the constructor

Example Service with Dependency Injection:

    from app.repositories.user import IUserRepository
    from app.repositories.article import IArticleRepository
    from app.services.base import BaseService

    class ReadingListService(BaseService):
        '''
        Service for managing user reading lists.

        This service orchestrates operations across user and article repositories
        to provide reading list functionality.
        '''

        def __init__(
            self,
            user_repo: IUserRepository,
            article_repo: IArticleRepository,
            reading_list_repo: IReadingListRepository
        ):
            '''
            Initialize the reading list service.

            Args:
                user_repo: Repository for user data access
                article_repo: Repository for article data access
                reading_list_repo: Repository for reading list data access
            '''
            super().__init__()
            self.user_repo = user_repo
            self.article_repo = article_repo
            self.reading_list_repo = reading_list_repo
            self.logger = get_logger(f"{__name__}.ReadingListService")

        async def add_to_reading_list(
            self,
            user_id: UUID,
            article_id: UUID
        ) -> ReadingListItem:
            '''
            Add an article to a user's reading list.

            This method demonstrates:
            - Using multiple repositories
            - Business logic validation
            - Error handling
            - Structured logging

            Args:
                user_id: UUID of the user
                article_id: UUID of the article

            Returns:
                Created reading list item

            Raises:
                ServiceError: If user or article not found, or if already in list
            '''
            self.logger.info(
                "Adding article to reading list",
                user_id=str(user_id),
                article_id=str(article_id)
            )

            try:
                # Validate user exists
                user = await self.user_repo.get_by_id(user_id)
                if not user:
                    raise ServiceError(
                        f"User not found: {user_id}",
                        error_code=ErrorCode.RESOURCE_NOT_FOUND,
                        details={"user_id": str(user_id)}
                    )

                # Validate article exists
                article = await self.article_repo.get_by_id(article_id)
                if not article:
                    raise ServiceError(
                        f"Article not found: {article_id}",
                        error_code=ErrorCode.RESOURCE_NOT_FOUND,
                        details={"article_id": str(article_id)}
                    )

                # Check if already in reading list
                existing = await self.reading_list_repo.get_by_user_and_article(
                    user_id, article_id
                )
                if existing:
                    raise ServiceError(
                        "Article already in reading list",
                        error_code=ErrorCode.VALIDATION_BUSINESS_RULE,
                        details={
                            "user_id": str(user_id),
                            "article_id": str(article_id)
                        }
                    )

                # Create reading list item
                item = await self.reading_list_repo.create({
                    "user_id": str(user_id),
                    "article_id": str(article_id),
                    "status": "Unread"
                })

                self.logger.info(
                    "Successfully added article to reading list",
                    user_id=str(user_id),
                    article_id=str(article_id),
                    item_id=str(item.id)
                )

                return item

            except ServiceError:
                raise
            except Exception as e:
                self._handle_error(
                    e,
                    "Failed to add article to reading list",
                    context={
                        "user_id": str(user_id),
                        "article_id": str(article_id)
                    }
                )

Dependency Injection in FastAPI Routes:

    from fastapi import APIRouter, Depends
    from app.core.dependencies import get_reading_list_service

    router = APIRouter()

    @router.post("/reading-list")
    async def add_to_reading_list(
        user_id: UUID,
        article_id: UUID,
        service: ReadingListService = Depends(get_reading_list_service)
    ):
        '''
        Add an article to the user's reading list.

        The service is injected via FastAPI's dependency injection system.
        '''
        item = await service.add_to_reading_list(user_id, article_id)
        return {"data": item}

Dependency Provider (app/core/dependencies.py):

    from app.repositories.user import UserRepository
    from app.repositories.article import ArticleRepository
    from app.repositories.reading_list import ReadingListRepository
    from app.services.reading_list import ReadingListService
    from app.core.database import get_supabase_client

    def get_reading_list_service() -> ReadingListService:
        '''
        Create and return a ReadingListService instance with dependencies.

        This function is used by FastAPI's dependency injection system.
        '''
        client = get_supabase_client()

        user_repo = UserRepository(client, "users")
        article_repo = ArticleRepository(client, "articles")
        reading_list_repo = ReadingListRepository(client, "reading_list")

        return ReadingListService(
            user_repo=user_repo,
            article_repo=article_repo,
            reading_list_repo=reading_list_repo
        )

Testing with Dependency Injection:

    import pytest
    from unittest.mock import AsyncMock, MagicMock
    from app.services.reading_list import ReadingListService

    @pytest.fixture
    def mock_user_repo():
        return AsyncMock()

    @pytest.fixture
    def mock_article_repo():
        return AsyncMock()

    @pytest.fixture
    def mock_reading_list_repo():
        return AsyncMock()

    @pytest.fixture
    def service(mock_user_repo, mock_article_repo, mock_reading_list_repo):
        return ReadingListService(
            user_repo=mock_user_repo,
            article_repo=mock_article_repo,
            reading_list_repo=mock_reading_list_repo
        )

    @pytest.mark.asyncio
    async def test_add_to_reading_list_success(
        service,
        mock_user_repo,
        mock_article_repo,
        mock_reading_list_repo
    ):
        # Arrange
        user_id = UUID("12345678-1234-1234-1234-123456789012")
        article_id = UUID("87654321-4321-4321-4321-210987654321")

        mock_user_repo.get_by_id.return_value = MagicMock(id=user_id)
        mock_article_repo.get_by_id.return_value = MagicMock(id=article_id)
        mock_reading_list_repo.get_by_user_and_article.return_value = None
        mock_reading_list_repo.create.return_value = MagicMock(
            id=UUID("11111111-1111-1111-1111-111111111111")
        )

        # Act
        result = await service.add_to_reading_list(user_id, article_id)

        # Assert
        assert result is not None
        mock_user_repo.get_by_id.assert_called_once_with(user_id)
        mock_article_repo.get_by_id.assert_called_once_with(article_id)
        mock_reading_list_repo.create.assert_called_once()
"""


# Service Responsibilities Documentation
"""
Service Layer Responsibilities and Boundaries

The service layer is responsible for:

1. Business Logic
   - Implement business rules and workflows
   - Validate business constraints
   - Orchestrate complex operations across multiple repositories
   - Transform data between domain models and DTOs

2. Transaction Management
   - Coordinate multi-repository operations
   - Ensure data consistency across operations
   - Handle rollback on failures

3. External Service Integration
   - Integrate with external APIs (LLM, RSS, Notion, etc.)
   - Handle external service errors and retries
   - Transform external data to internal models

4. Error Handling
   - Catch and wrap repository errors
   - Provide business-level error messages
   - Log errors with appropriate context

5. Logging and Monitoring
   - Log business operations with structured context
   - Track operation performance
   - Monitor business metrics

Service Boundaries:

DO:
✓ Depend on repository interfaces for data access
✓ Inject dependencies through constructor
✓ Validate business rules before calling repositories
✓ Log business operations with context
✓ Handle and wrap errors with business context
✓ Transform data between layers
✓ Orchestrate operations across multiple repositories
✓ Call other services for complex workflows

DON'T:
✗ Directly access database clients (use repositories instead)
✗ Contain database-specific logic (belongs in repositories)
✗ Depend on concrete repository implementations
✗ Handle HTTP requests/responses (belongs in controllers)
✗ Contain presentation logic (belongs in controllers)
✗ Directly manipulate database transactions (use repository methods)

Example Service Structure:

    class ArticleService(BaseService):
        '''Service for article management.'''

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

        async def create_article_with_summary(
            self,
            article_data: Dict[str, Any]
        ) -> Article:
            '''
            Create an article and generate AI summary.

            This demonstrates:
            - Business logic (generate summary)
            - Multi-service orchestration (article + LLM)
            - Error handling
            - Logging
            '''
            self.logger.info("Creating article with AI summary")

            try:
                # Validate feed exists
                feed = await self.feed_repo.get_by_id(article_data['feed_id'])
                if not feed:
                    raise ServiceError(
                        "Feed not found",
                        error_code=ErrorCode.RESOURCE_NOT_FOUND
                    )

                # Generate AI summary
                summary = await self.llm_service.generate_summary(
                    article_data['title'],
                    article_data.get('content', '')
                )

                # Create article with summary
                article_data['ai_summary'] = summary
                article = await self.article_repo.create(article_data)

                self.logger.info(
                    "Successfully created article with summary",
                    article_id=str(article.id)
                )

                return article

            except ServiceError:
                raise
            except Exception as e:
                self._handle_error(
                    e,
                    "Failed to create article with summary",
                    context={"article_data": article_data}
                )

Migration Strategy:

When refactoring existing services to use the repository layer:

1. Identify Direct Database Access
   - Find all places where service directly uses Supabase client
   - Example: self.client.table('articles').select('*')

2. Create Repository Interface
   - Define interface methods for required operations
   - Example: IArticleRepository.get_by_id()

3. Update Service Constructor
   - Add repository as dependency
   - Remove direct database client dependency
   - Example: def __init__(self, article_repo: IArticleRepository)

4. Replace Database Calls
   - Replace direct database calls with repository methods
   - Example: self.client.table('articles').select() → self.article_repo.list()

5. Update Tests
   - Mock repository instead of database client
   - Test business logic without database

6. Update Dependency Injection
   - Update dependency provider to inject repository
   - Example: get_article_service() creates repository and injects it

Example Migration:

    # Before (direct database access)
    class ArticleService:
        def __init__(self, supabase_client: Client):
            self.client = supabase_client

        async def get_article(self, article_id: UUID):
            response = self.client.table('articles') \\
                .select('*') \\
                .eq('id', str(article_id)) \\
                .execute()
            return response.data[0] if response.data else None

    # After (repository pattern)
    class ArticleService(BaseService):
        def __init__(self, article_repo: IArticleRepository):
            super().__init__()
            self.article_repo = article_repo
            self.logger = get_logger(f"{__name__}.ArticleService")

        async def get_article(self, article_id: UUID):
            self.logger.info("Fetching article", article_id=str(article_id))

            article = await self.article_repo.get_by_id(article_id)
            if not article:
                raise ServiceError(
                    f"Article not found: {article_id}",
                    error_code=ErrorCode.RESOURCE_NOT_FOUND
                )

            return article
"""
