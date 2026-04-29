"""Retry and fallback strategies."""
import asyncio
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class RetryStrategy:
    """
    Retry strategy for transient errors.

    Supports:
    - Configurable max attempts
    - Exponential backoff
    - Specific exception types to retry

    Validates: Requirements 4.5
    """

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        retry_on: tuple = (ExternalServiceError, DatabaseError),
    ):
        """
        Initialize retry strategy.

        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            backoff_factor: Multiplier for exponential backoff
            max_delay: Maximum delay between retries
            retry_on: Tuple of exception types to retry on
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.retry_on = retry_on

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute (can be sync or async)
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        delay = self.initial_delay

        for attempt in range(1, self.max_attempts + 1):
            try:
                # Execute function (handle both sync and async)
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Success - log if retried
                if attempt > 1:
                    logger.info(
                        f"Retry succeeded on attempt {attempt}",
                        function=func.__name__,
                        attempts=attempt,
                    )

                return result

            except self.retry_on as e:
                last_exception = e

                if attempt < self.max_attempts:
                    logger.warning(
                        f"Retry attempt {attempt}/{self.max_attempts} failed",
                        function=func.__name__,
                        error=str(e),
                        next_delay=delay,
                    )

                    # Wait before retry
                    await asyncio.sleep(delay)

                    # Calculate next delay with exponential backoff
                    delay = min(delay * self.backoff_factor, self.max_delay)
                else:
                    logger.error(
                        f"All {self.max_attempts} retry attempts failed",
                        function=func.__name__,
                        error=str(e),
                        exc_info=True,
                    )

        # All retries failed - raise last exception
        raise last_exception


class FallbackStrategy:
    """
    Fallback strategy for graceful degradation.

    Provides fallback value or function when primary operation fails.

    Validates: Requirements 4.5
    """

    def __init__(self, fallback: Any | Callable, fallback_on: tuple = (AppException,)):
        """
        Initialize fallback strategy.

        Args:
            fallback: Fallback value or function to call
            fallback_on: Tuple of exception types to fallback on
        """
        self.fallback = fallback
        self.fallback_on = fallback_on

    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with fallback logic.

        Args:
            func: Function to execute (can be sync or async)
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result or fallback value
        """
        try:
            # Execute function (handle both sync and async)
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        except self.fallback_on as e:
            logger.warning(
                "Primary operation failed, using fallback",
                function=func.__name__,
                error=str(e),
                fallback_type="function" if callable(self.fallback) else "value",
            )

            # Return fallback value or call fallback function
            if callable(self.fallback):
                if asyncio.iscoroutinefunction(self.fallback):
                    return await self.fallback(*args, **kwargs)
                else:
                    return self.fallback(*args, **kwargs)
            else:
                return self.fallback


# ============================================================================
# Convenience Functions
# ============================================================================


def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retry_on: tuple = (ExternalServiceError, DatabaseError),
):
    """
    Decorator for adding retry logic to functions.

    Example:
        @with_retry(max_attempts=3)
        async def fetch_data():
            # ... code that might fail transiently
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        strategy = RetryStrategy(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            backoff_factor=backoff_factor,
            retry_on=retry_on,
        )

        async def wrapper(*args, **kwargs) -> T:
            return await strategy.execute(func, *args, **kwargs)

        return wrapper

    return decorator


def with_fallback(fallback: Any | Callable, fallback_on: tuple = (AppException,)):
    """
    Decorator for adding fallback logic to functions.

    Example:
        @with_fallback(fallback=[])
        async def get_recommendations():
            # ... code that might fail
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        strategy = FallbackStrategy(fallback=fallback, fallback_on=fallback_on)

        async def wrapper(*args, **kwargs) -> T:
            return await strategy.execute(func, *args, **kwargs)

        return wrapper

    return decorator
