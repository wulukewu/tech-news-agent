"""
QA Agent Controller for Intelligent Q&A Agent

This module implements the QAAgentController class that serves as the central orchestrator
for the intelligent Q&A system. It coordinates all system components to process user queries
and generate responses within the 3-second performance requirement.

Requirements addressed:
- 6.2: Complete response generation should complete within 3 seconds
- 9.3: Implement query routing and component coordination
- 9.1, 9.2, 9.4, 9.5: Comprehensive error handling and fallback mechanisms
"""

import asyncio
import logging
import random
import time
from typing import Optional

from .constants import RetryConfig
from .embedding_service import EmbeddingError
from .vector_store import VectorStoreError

logger = logging.getLogger(__name__)


class RetryMechanism:
    """
    Comprehensive retry mechanism with exponential backoff for temporary errors.

    Implements Requirement 9.5: Automatic retry for transient errors.
    """

    @staticmethod
    async def execute_with_retry(
        operation,
        max_retries: int = RetryConfig.LLM_MAX_RETRIES,
        base_delay: float = RetryConfig.LLM_RETRY_DELAY_MS / 1000.0,
        backoff_multiplier: float = RetryConfig.LLM_RETRY_BACKOFF_MULTIPLIER,
        jitter: bool = True,
        transient_exceptions: tuple = (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
            VectorStoreError,
            EmbeddingError,
        ),
    ):
        """
        Execute an operation with exponential backoff retry.

        Args:
            operation: Async callable to execute
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between retries in seconds
            backoff_multiplier: Multiplier for exponential backoff
            jitter: Whether to add random jitter to delays
            transient_exceptions: Tuple of exceptions considered transient

        Returns:
            Result of the operation

        Raises:
            The last exception if all retries fail
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await operation()
            except transient_exceptions as e:
                last_exception = e

                if attempt == max_retries:
                    logger.error(f"Operation failed after {max_retries + 1} attempts: {e}")
                    break

                # Calculate delay with exponential backoff
                delay = base_delay * (backoff_multiplier**attempt)

                # Add jitter to prevent thundering herd
                if jitter:
                    delay *= 0.5 + random.random() * 0.5

                logger.warning(
                    f"Transient error on attempt {attempt + 1}/{max_retries + 1}, "
                    f"retrying in {delay:.2f}s: {e}"
                )

                await asyncio.sleep(delay)
            except Exception as e:
                # Non-transient error, don't retry
                logger.error(f"Non-transient error, not retrying: {e}")
                raise

        # All retries exhausted
        raise last_exception


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for external service failures.

    Implements part of Requirement 9.5: Automatic failure detection and recovery.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def call(self, operation):
        """Execute operation with circuit breaker protection."""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time < self.recovery_timeout:
                raise Exception("Circuit breaker is OPEN")
            else:
                self.state = "HALF_OPEN"

        try:
            result = await operation()
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Reset circuit breaker on successful operation."""
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self):
        """Handle failure and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class QAAgentControllerError(Exception):
    """Base exception for QA Agent Controller operations."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error
