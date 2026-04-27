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
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .constants import RetryConfig
from .conversation_manager import ConversationManager
from .embedding_service import EmbeddingError, EmbeddingService
from .models import (
    ArticleMatch,
    ArticleSummary,
    ConversationContext,
    ParsedQuery,
    QueryIntent,
    QueryLanguage,
    ResponseType,
    StructuredResponse,
    UserProfile,
)
from .query_processor import QueryProcessor, QueryValidationResult
from .response_generator import ResponseGenerator, ResponseGeneratorError
from .retrieval_engine import RetrievalEngine, RetrievalEngineError
from .vector_store import VectorStore, VectorStoreError, get_vector_store

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


class QAAgentController:
    """
    Central orchestrator for the intelligent Q&A system.

    Coordinates all system components to process user queries and generate responses:
    - Routes queries through the processing pipeline
    - Manages component coordination and error handling
    - Implements fallback mechanisms for reliability
    - Ensures performance requirements are met (3-second response time)

    Requirements: 6.2, 9.1, 9.2, 9.3, 9.4, 9.5
    """

    def __init__(
        self,
        query_processor: Optional[QueryProcessor] = None,
        retrieval_engine: Optional[RetrievalEngine] = None,
        response_generator: Optional[ResponseGenerator] = None,
        conversation_manager: Optional[ConversationManager] = None,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStore] = None,
    ):
        """
        Initialize the QA Agent Controller with all required components.

        Args:
            query_processor: Optional QueryProcessor instance
            retrieval_engine: Optional RetrievalEngine instance
            response_generator: Optional ResponseGenerator instance
            conversation_manager: Optional ConversationManager instance
            embedding_service: Optional EmbeddingService instance
            vector_store: Optional VectorStore instance
        """
        # Initialize components (create defaults if not provided)
        self.query_processor = query_processor or QueryProcessor()
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or get_vector_store()
        self.retrieval_engine = retrieval_engine or RetrievalEngine(self.vector_store)
        self.response_generator = response_generator or ResponseGenerator()
        self.conversation_manager = conversation_manager or ConversationManager()

        # Performance tracking
        self.max_response_time = 3.0  # Requirement 6.2: 3-second limit
        self.fallback_timeout = 2.5  # Start fallback if approaching limit

        # Component health tracking
        self._component_health = {
            "query_processor": True,
            "embedding_service": True,
            "vector_store": True,
            "retrieval_engine": True,
            "response_generator": True,
            "conversation_manager": True,
        }

        # Circuit breakers for external services (Requirement 9.5)
        self._circuit_breakers = {
            "embedding_service": CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=30.0,
                expected_exception=EmbeddingError,
            ),
            "vector_store": CircuitBreaker(
                failure_threshold=3,
                recovery_timeout=20.0,
                expected_exception=VectorStoreError,
            ),
            "response_generator": CircuitBreaker(
                failure_threshold=5,
                recovery_timeout=30.0,
                expected_exception=ResponseGeneratorError,
            ),
        }

        # Retry mechanism instance
        self.retry_mechanism = RetryMechanism()

    async def process_query(
        self,
        user_id: str,
        query: str,
        conversation_id: Optional[str] = None,
        user_profile: Optional[UserProfile] = None,
    ) -> StructuredResponse:
        """
        Process a user query and generate a structured response.

        This is the main entry point for the Q&A system. It orchestrates all components
        to provide a complete response within the 3-second performance requirement.

        Args:
            user_id: User identifier for access isolation and personalization
            query: User's natural language query
            conversation_id: Optional conversation ID for multi-turn conversations
            user_profile: Optional user profile for personalization

        Returns:
            StructuredResponse with articles, insights, and recommendations

        Raises:
            QAAgentControllerError: If query processing fails completely

        Requirements: 6.2, 9.3, 9.1, 9.2, 9.4, 9.5
        """
        start_time = time.time()
        error_context = {
            "user_id": user_id,
            "query_length": len(query),
            "conversation_id": conversation_id,
            "has_user_profile": user_profile is not None,
        }

        try:
            logger.info(f"Processing query for user {user_id}: {query[:100]}...")

            # Step 1: Validate query (fast operation)
            validation_result = await self._validate_query_with_timeout(query, timeout=0.2)
            if not validation_result.is_valid:
                error_context["validation_error"] = validation_result.error_message
                logger.warning(
                    f"Query validation failed: {validation_result.error_message}",
                    extra=error_context,
                )
                return self._create_error_response(
                    query=query,
                    error_message=validation_result.error_message,
                    suggestions=validation_result.suggestions,
                    conversation_id=conversation_id,
                    response_time=time.time() - start_time,
                )

            # Step 2: Get or create conversation context
            context = await self._get_conversation_context(user_id, conversation_id)
            error_context["context_retrieved"] = context is not None

            # Step 3: Parse query with context (with timeout)
            parsed_query = await self._parse_query_with_timeout(query, context, timeout=0.5)
            error_context["query_parsed"] = True
            error_context["query_intent"] = (
                parsed_query.intent.value if parsed_query.intent else None
            )

            # Step 4: Check if context should be reset
            if context and await self._should_reset_context(context, query):
                await self.conversation_manager.reset_context(
                    str(context.conversation_id),
                    new_topic=self._extract_topic_from_parsed_query(parsed_query),
                )
                # Refresh context after reset
                context = await self.conversation_manager.get_context(str(context.conversation_id))
                error_context["context_reset"] = True

            # Step 5: Generate query embedding (with timeout and retry)
            try:
                query_vector = await self._generate_embedding_with_timeout(query, timeout=0.5)
                error_context["embedding_generated"] = True
            except QAAgentControllerError as e:
                error_context["embedding_error"] = str(e)
                logger.error(f"Embedding generation failed: {e}", extra=error_context)
                # Continue with keyword-only search
                query_vector = []

            # Step 6: Retrieve relevant articles (with timeout and fallback)
            articles = await self._retrieve_articles_with_fallback(
                query=query,
                query_vector=query_vector,
                user_id=user_id,
                user_profile=user_profile,
                timeout=1.0,
            )
            error_context["articles_found"] = len(articles)

            # Step 7: Generate structured response (with timeout and fallback)
            response = await self._generate_response_with_fallback(
                query=query,
                articles=articles,
                context=context,
                user_profile=user_profile,
                timeout=1.0,
            )
            error_context["response_generated"] = True
            error_context["response_type"] = response.response_type

            # Step 8: Update conversation context
            if context:
                try:
                    await self._update_conversation_context(context, query, parsed_query, response)
                    error_context["context_updated"] = True
                except Exception as e:
                    error_context["context_update_error"] = str(e)
                    logger.warning(
                        f"Failed to update conversation context: {e}", extra=error_context
                    )

            # Step 9: Set final response time and validate performance
            total_time = time.time() - start_time
            response.response_time = total_time
            error_context["total_time"] = total_time

            if total_time > self.max_response_time:
                logger.warning(
                    f"Response time exceeded limit: {total_time:.2f}s > {self.max_response_time}s",
                    extra=error_context,
                )

            # Log successful completion with metrics
            logger.info(f"Query processed successfully in {total_time:.2f}s", extra=error_context)
            return response

        except asyncio.TimeoutError:
            # Handle timeout gracefully (Requirement 9.4)
            total_time = time.time() - start_time
            error_context["timeout_error"] = True
            error_context["total_time"] = total_time
            logger.error(f"Query processing timed out after {total_time:.2f}s", extra=error_context)
            return self._create_timeout_response(query, conversation_id, total_time)

        except Exception as e:
            # Comprehensive error logging (Requirement 9.3)
            total_time = time.time() - start_time
            error_context["unexpected_error"] = str(e)
            error_context["error_type"] = type(e).__name__
            error_context["total_time"] = total_time
            logger.error(
                f"Query processing failed after {total_time:.2f}s: {e}",
                extra=error_context,
                exc_info=True,
            )
            return self._create_fallback_response(query, conversation_id, total_time, e)

    async def continue_conversation(
        self,
        user_id: str,
        query: str,
        conversation_id: str,
        user_profile: Optional[UserProfile] = None,
    ) -> StructuredResponse:
        """
        Continue an existing conversation with a follow-up query.

        This method is optimized for multi-turn conversations and includes
        enhanced context understanding for follow-up questions.

        Args:
            user_id: User identifier
            query: Follow-up query
            conversation_id: Existing conversation ID
            user_profile: Optional user profile for personalization

        Returns:
            StructuredResponse with contextual understanding

        Requirements: 4.2, 4.3
        """
        logger.info(f"Continuing conversation {conversation_id} for user {user_id}")

        # Use the main process_query method with the existing conversation_id
        return await self.process_query(
            user_id=user_id,
            query=query,
            conversation_id=conversation_id,
            user_profile=user_profile,
        )

    async def get_conversation_history(
        self, user_id: str, conversation_id: str
    ) -> Optional[ConversationContext]:
        """
        Retrieve conversation history for a user.

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier

        Returns:
            ConversationContext if found, None otherwise
        """
        try:
            context = await self.conversation_manager.get_context(conversation_id)

            # Verify user ownership
            if context and str(context.user_id) != user_id:
                logger.warning(
                    f"User {user_id} attempted to access conversation {conversation_id} owned by {context.user_id}"
                )
                return None

            return context

        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return None

    async def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """
        Delete a conversation for a user.

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Verify user ownership first
            context = await self.conversation_manager.get_context(conversation_id)
            if context and str(context.user_id) != user_id:
                logger.warning(
                    f"User {user_id} attempted to delete conversation {conversation_id} owned by {context.user_id}"
                )
                return False

            return await self.conversation_manager.delete_conversation(conversation_id)

        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            return False

    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health status for monitoring.

        Returns:
            Dictionary with component health status, performance metrics, and circuit breaker states

        Requirements: 9.3, 9.5
        """
        try:
            # Test each component
            health_checks = await asyncio.gather(
                self._check_query_processor_health(),
                self._check_embedding_service_health(),
                self._check_vector_store_health(),
                self._check_retrieval_engine_health(),
                self._check_response_generator_health(),
                self._check_conversation_manager_health(),
                return_exceptions=True,
            )

            components = [
                "query_processor",
                "embedding_service",
                "vector_store",
                "retrieval_engine",
                "response_generator",
                "conversation_manager",
            ]

            # Update component health status
            for i, result in enumerate(health_checks):
                component = components[i]
                self._component_health[component] = not isinstance(result, Exception)

            # Calculate overall health
            healthy_components = sum(1 for status in self._component_health.values() if status)
            total_components = len(self._component_health)
            overall_health = healthy_components / total_components

            # Get circuit breaker states
            circuit_breaker_states = {
                name: {
                    "state": cb.state,
                    "failure_count": cb.failure_count,
                    "last_failure_time": cb.last_failure_time,
                }
                for name, cb in self._circuit_breakers.items()
            }

            return {
                "overall_health": overall_health,
                "status": (
                    "healthy"
                    if overall_health >= 0.8
                    else "degraded"
                    if overall_health >= 0.5
                    else "unhealthy"
                ),
                "components": self._component_health.copy(),
                "circuit_breakers": circuit_breaker_states,
                "timestamp": datetime.utcnow().isoformat(),
                "healthy_components": healthy_components,
                "total_components": total_components,
                "error_handling_features": {
                    "keyword_search_fallback": True,
                    "search_results_fallback": True,
                    "partial_results_on_timeout": True,
                    "retry_mechanisms": True,
                    "circuit_breakers": True,
                    "comprehensive_error_logging": True,
                },
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "overall_health": 0.0,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    # Private helper methods for component coordination

    async def _validate_query_with_timeout(
        self, query: str, timeout: float
    ) -> QueryValidationResult:
        """Validate query with timeout protection."""
        try:
            return await asyncio.wait_for(
                self.query_processor.validate_query(query), timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Query validation timed out after {timeout}s")
            # Return basic validation
            if not query or not query.strip():
                return QueryValidationResult(
                    is_valid=False,
                    error_message="Query cannot be empty",
                )
            return QueryValidationResult(is_valid=True)
        except Exception as e:
            logger.error(f"Query validation failed: {e}")
            return QueryValidationResult(is_valid=True)  # Allow processing to continue

    async def _parse_query_with_timeout(
        self, query: str, context: Optional[ConversationContext], timeout: float
    ) -> ParsedQuery:
        """Parse query with timeout protection."""
        try:
            if context:
                # Expand query with context for better understanding
                expanded_query = await asyncio.wait_for(
                    self.query_processor.expand_query(query, context), timeout=timeout / 2
                )
                return await asyncio.wait_for(
                    self.query_processor.parse_query(expanded_query, context=context),
                    timeout=timeout / 2,
                )
            else:
                return await asyncio.wait_for(
                    self.query_processor.parse_query(query), timeout=timeout
                )
        except asyncio.TimeoutError:
            logger.warning(f"Query parsing timed out after {timeout}s")
            # Return basic parsed query
            return ParsedQuery(
                original_query=query,
                language=QueryLanguage.AUTO_DETECT,
                intent=QueryIntent.SEARCH,
                keywords=query.split()[:10],  # Simple keyword extraction
                confidence=0.5,
            )
        except Exception as e:
            logger.error(f"Query parsing failed: {e}")
            # Return fallback parsed query
            return ParsedQuery(
                original_query=query,
                language=QueryLanguage.AUTO_DETECT,
                intent=QueryIntent.SEARCH,
                keywords=query.split()[:10],
                confidence=0.3,
            )

    async def _generate_embedding_with_timeout(self, query: str, timeout: float) -> List[float]:
        """
        Generate query embedding with timeout protection and retry mechanism.

        Implements Requirements 9.5: Retry mechanism for temporary errors.
        """
        try:
            # Use circuit breaker and retry mechanism
            async def embedding_operation():
                return await asyncio.wait_for(
                    self.embedding_service.generate_embedding(query), timeout=timeout
                )

            return await self._circuit_breakers["embedding_service"].call(
                lambda: self.retry_mechanism.execute_with_retry(
                    embedding_operation,
                    max_retries=RetryConfig.LLM_MAX_RETRIES,
                    base_delay=RetryConfig.LLM_RETRY_DELAY_MS / 1000.0,
                )
            )

        except asyncio.TimeoutError:
            logger.warning(f"Embedding generation timed out after {timeout}s")
            raise QAAgentControllerError("Embedding generation timed out")
        except EmbeddingError as e:
            logger.error(f"Embedding service error: {e}")
            raise QAAgentControllerError("Embedding generation failed", e)
        except Exception as e:
            logger.error(f"Unexpected embedding error: {e}")
            raise QAAgentControllerError("Embedding generation failed", e)

    async def _retrieve_articles_with_fallback(
        self,
        query: str,
        query_vector: List[float],
        user_id: str,
        user_profile: Optional[UserProfile],
        timeout: float,
    ) -> List[ArticleMatch]:
        """
        Retrieve articles with comprehensive fallback mechanisms.

        Implements Requirements:
        - 9.1: Fallback to keyword search when vector store unavailable
        - 9.4: Provide partial results when query times out
        - 9.5: Retry mechanism for temporary errors
        """
        try:
            # Try intelligent search first with retry mechanism
            async def intelligent_search_operation():
                return await asyncio.wait_for(
                    self.retrieval_engine.intelligent_search(
                        query=query,
                        query_vector=query_vector,
                        user_id=user_id,
                        user_profile=user_profile,
                        limit=10,
                        min_results=3,
                        use_expansion=True,
                        use_personalization=bool(user_profile),
                        use_cache=True,
                    ),
                    timeout=timeout,
                )

            search_result = await self._circuit_breakers["vector_store"].call(
                lambda: self.retry_mechanism.execute_with_retry(
                    intelligent_search_operation,
                    max_retries=RetryConfig.VECTOR_MAX_RETRIES,
                    base_delay=RetryConfig.VECTOR_RETRY_DELAY_MS / 1000.0,
                )
            )

            articles = search_result["results"]

            if len(articles) >= 1:  # At least one result
                logger.debug(f"Intelligent search returned {len(articles)} articles")
                return articles

            # Fallback 1: Try basic semantic search with retry
            logger.info("Falling back to basic semantic search")

            async def semantic_search_operation():
                return await asyncio.wait_for(
                    self.retrieval_engine.semantic_search(
                        query_vector=query_vector,
                        user_id=user_id,
                        limit=5,
                        threshold=0.3,  # Lower threshold for fallback
                    ),
                    timeout=timeout / 2,
                )

            articles = await self.retry_mechanism.execute_with_retry(
                semantic_search_operation,
                max_retries=2,
            )

            if articles:
                return articles

            # Fallback 2: Keyword search when vector store unavailable (Requirement 9.1)
            logger.warning("Vector search failed, falling back to keyword search")
            return await self._keyword_search_fallback(query, user_id, timeout / 3)

        except asyncio.TimeoutError:
            logger.warning(f"Article retrieval timed out after {timeout}s")
            # Requirement 9.4: Provide partial results when query times out
            return await self._get_partial_results_on_timeout(query, user_id, timeout / 4)

        except (RetrievalEngineError, VectorStoreError) as e:
            logger.error(f"Retrieval error: {e}")
            # Requirement 9.1: Fallback to keyword search when vector store unavailable
            return await self._keyword_search_fallback(query, user_id, timeout / 2)

        except Exception as e:
            logger.error(f"Unexpected retrieval error: {e}")
            # Last resort: try keyword search
            return await self._keyword_search_fallback(query, user_id, timeout / 2)

    async def _keyword_search_fallback(
        self, query: str, user_id: str, timeout: float
    ) -> List[ArticleMatch]:
        """
        Fallback to keyword-based search when vector store is unavailable.

        Implements Requirement 9.1: Fallback to keyword search when vector store unavailable.
        """
        try:
            logger.info("Executing keyword search fallback")

            # Extract keywords from query
            keywords = self._extract_simple_keywords(query)
            if not keywords:
                logger.warning("No keywords extracted from query")
                return []

            # Use the retrieval engine's keyword expansion method
            async def keyword_search_operation():
                return await asyncio.wait_for(
                    self.retrieval_engine._expand_by_keywords(
                        query_text=query,
                        user_uuid=UUID(user_id),
                        existing_ids=set(),
                        limit=5,
                    ),
                    timeout=timeout,
                )

            results = await self.retry_mechanism.execute_with_retry(
                keyword_search_operation,
                max_retries=2,
                base_delay=0.1,
            )

            logger.info(f"Keyword search fallback returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Keyword search fallback failed: {e}")
            return []

    async def _get_partial_results_on_timeout(
        self, query: str, user_id: str, timeout: float
    ) -> List[ArticleMatch]:
        """
        Get partial results when query times out.

        Implements Requirement 9.4: Provide partial results when query times out.
        """
        try:
            logger.info("Getting partial results due to timeout")

            # Try a very quick keyword search with minimal processing
            keywords = self._extract_simple_keywords(query)[:3]  # Limit to 3 keywords

            if not keywords:
                return []

            # Quick and dirty search with very low timeout
            async def quick_search():
                return await asyncio.wait_for(
                    self.retrieval_engine._expand_by_keywords(
                        query_text=" ".join(keywords),
                        user_uuid=UUID(user_id),
                        existing_ids=set(),
                        limit=3,  # Fewer results for speed
                    ),
                    timeout=min(timeout, 0.5),  # Very short timeout
                )

            results = await quick_search()
            logger.info(f"Partial results: found {len(results)} articles")
            return results

        except Exception as e:
            logger.warning(f"Failed to get partial results: {e}")
            return []

    def _extract_simple_keywords(self, query: str) -> List[str]:
        """
        Extract simple keywords from query for fallback search.

        This is a simplified version for fallback scenarios.
        """
        import re

        # Simple stop words (subset for performance)
        stop_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "of",
            "in",
            "on",
            "at",
            "to",
            "for",
            "with",
            "by",
            "from",
            "and",
            "or",
            "but",
            "not",
            "what",
            "how",
            "why",
            "when",
            "的",
            "是",
            "了",
            "在",
            "和",
            "有",
            "我",
            "你",
            "他",
            "她",
        }

        # Clean and split
        clean_query = re.sub(r"[^\w\s]", " ", query.lower())
        tokens = clean_query.split()

        # Filter and return
        return [t for t in tokens if len(t) >= 2 and t not in stop_words][:10]

    async def _generate_response_with_fallback(
        self,
        query: str,
        articles: List[ArticleMatch],
        context: Optional[ConversationContext],
        user_profile: Optional[UserProfile],
        timeout: float,
    ) -> StructuredResponse:
        """
        Generate response with comprehensive fallback mechanisms.

        Implements Requirements:
        - 9.2: Provide search results list when generation fails
        - 9.4: Provide partial results when query times out
        - 9.5: Retry mechanism for temporary errors
        """
        try:
            # Try full response generation with retry mechanism
            async def response_generation_operation():
                return await asyncio.wait_for(
                    self.response_generator.generate_response(
                        query=query,
                        articles=articles,
                        context=context,
                        user_profile=user_profile,
                    ),
                    timeout=timeout,
                )

            response = await self._circuit_breakers["response_generator"].call(
                lambda: self.retry_mechanism.execute_with_retry(
                    response_generation_operation,
                    max_retries=RetryConfig.LLM_MAX_RETRIES,
                    base_delay=RetryConfig.LLM_RETRY_DELAY_MS / 1000.0,
                )
            )

            # Ensure conversation_id is set
            if not response.conversation_id and context:
                response.conversation_id = context.conversation_id
            elif not response.conversation_id:
                response.conversation_id = uuid4()

            return response

        except asyncio.TimeoutError:
            logger.warning(f"Response generation timed out after {timeout}s")
            # Requirement 9.4: Provide partial results when query times out
            return self._create_timeout_fallback_response(query, articles, context)

        except ResponseGeneratorError as e:
            logger.error(f"Response generation error: {e}")
            # Requirement 9.2: Provide search results list when generation fails
            return self._create_search_results_fallback_response(query, articles, context, str(e))

        except Exception as e:
            logger.error(f"Unexpected response generation error: {e}")
            # Requirement 9.2: Provide search results list when generation fails
            return self._create_search_results_fallback_response(query, articles, context, str(e))

    async def _get_conversation_context(
        self, user_id: str, conversation_id: Optional[str]
    ) -> Optional[ConversationContext]:
        """Get or create conversation context."""
        try:
            if conversation_id:
                # Try to get existing conversation
                context = await self.conversation_manager.get_context(conversation_id)

                # Verify user ownership
                if context and str(context.user_id) != user_id:
                    logger.warning(
                        f"User {user_id} attempted to access conversation {conversation_id} owned by {context.user_id}"
                    )
                    return None

                return context
            else:
                # Create new conversation
                new_conversation_id = await self.conversation_manager.create_conversation(
                    UUID(user_id)
                )
                return await self.conversation_manager.get_context(new_conversation_id)

        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return None

    async def _should_reset_context(self, context: ConversationContext, new_query: str) -> bool:
        """Determine if conversation context should be reset."""
        try:
            return await self.conversation_manager.should_reset_context(
                str(context.conversation_id), new_query
            )
        except Exception as e:
            logger.error(f"Failed to check context reset: {e}")
            return False  # Default to not resetting on error

    async def _update_conversation_context(
        self,
        context: ConversationContext,
        query: str,
        parsed_query: ParsedQuery,
        response: StructuredResponse,
    ) -> None:
        """Update conversation context with new turn."""
        try:
            await self.conversation_manager.add_turn(
                conversation_id=str(context.conversation_id),
                query=query,
                parsed_query=parsed_query,
                response=response,
            )
        except Exception as e:
            logger.error(f"Failed to update conversation context: {e}")
            # Don't raise - this is not critical for the response

    def _extract_topic_from_parsed_query(self, parsed_query: ParsedQuery) -> Optional[str]:
        """Extract topic from parsed query for context reset."""
        if parsed_query.keywords:
            return " ".join(parsed_query.keywords[:3])
        return None

    # Fallback response creation methods

    def _create_error_response(
        self,
        query: str,
        error_message: str,
        suggestions: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
        response_time: float = 0.0,
    ) -> StructuredResponse:
        """Create an error response for invalid queries."""
        return StructuredResponse(
            query=query,
            response_type=ResponseType.ERROR,
            articles=[],
            insights=[error_message],
            recommendations=suggestions or [],
            conversation_id=UUID(conversation_id) if conversation_id else uuid4(),
            response_time=response_time,
            confidence=0.0,
        )

    def _create_timeout_response(
        self, query: str, conversation_id: Optional[str], response_time: float
    ) -> StructuredResponse:
        """Create a timeout response."""
        return StructuredResponse(
            query=query,
            response_type=ResponseType.ERROR,
            articles=[],
            insights=["Request timed out. Please try a simpler query or try again later."],
            recommendations=[
                "Try breaking your question into smaller parts",
                "Use more specific keywords",
                "Try again in a moment",
            ],
            conversation_id=UUID(conversation_id) if conversation_id else uuid4(),
            response_time=response_time,
            confidence=0.0,
        )

    def _create_fallback_response(
        self,
        query: str,
        conversation_id: Optional[str],
        response_time: float,
        error: Exception,
    ) -> StructuredResponse:
        """Create a fallback response when processing fails."""
        return StructuredResponse(
            query=query,
            response_type=ResponseType.ERROR,
            articles=[],
            insights=[
                "I'm having trouble processing your request right now.",
                "Please try rephrasing your question or try again later.",
            ],
            recommendations=[
                "Try using different keywords",
                "Make your question more specific",
                "Check back in a few minutes",
            ],
            conversation_id=UUID(conversation_id) if conversation_id else uuid4(),
            response_time=response_time,
            confidence=0.0,
        )

    def _create_timeout_fallback_response(
        self,
        query: str,
        articles: List[ArticleMatch],
        context: Optional[ConversationContext],
    ) -> StructuredResponse:
        """
        Create a fallback response when response generation times out.

        Implements Requirement 9.4: Provide partial results and explain situation when query times out.
        """
        # Create basic article summaries without LLM
        basic_summaries = []
        for article in articles[:3]:  # Limit to 3 for timeout scenario
            summary = ArticleSummary(
                article_id=article.article_id,
                title=article.title,
                summary=self._create_basic_summary(article),
                url=article.url,
                relevance_score=article.similarity_score,
                reading_time=article.get_reading_time_estimate(),
                published_at=article.published_at,
                category=article.category,
            )
            basic_summaries.append(summary)

        # Create timeout-specific insights
        timeout_insights = [
            f"Found {len(articles)} relevant articles but detailed analysis timed out.",
            "Here are the most relevant articles with basic summaries:",
        ]

        # Add article titles for quick reference
        if basic_summaries:
            timeout_insights.append(
                "Articles: " + ", ".join([f'"{s.title}"' for s in basic_summaries[:3]])
            )

        return StructuredResponse(
            query=query,
            response_type=ResponseType.PARTIAL,  # Indicates partial results
            articles=basic_summaries,
            insights=timeout_insights,
            recommendations=[
                "Try a more specific query for faster results",
                "Break complex questions into simpler parts",
                "The articles above contain relevant information",
            ],
            conversation_id=context.conversation_id if context else uuid4(),
            response_time=0.0,  # Will be set by caller
            confidence=0.6,
        )

    def _create_search_results_fallback_response(
        self,
        query: str,
        articles: List[ArticleMatch],
        context: Optional[ConversationContext],
        error_message: str,
    ) -> StructuredResponse:
        """
        Create a fallback response providing search results list when generation fails.

        Implements Requirement 9.2: Provide search results list as alternative when generation fails.
        """
        # Convert articles to basic summaries
        search_results = []
        for article in articles[:5]:  # Show up to 5 results
            summary = ArticleSummary(
                article_id=article.article_id,
                title=article.title,
                summary=self._create_basic_summary(article),
                url=article.url,
                relevance_score=article.similarity_score,
                reading_time=article.get_reading_time_estimate(),
                published_at=article.published_at,
                category=article.category,
            )
            search_results.append(summary)

        # Create informative insights about the search results
        insights = [
            f"I found {len(articles)} articles related to your query but couldn't generate detailed insights.",
            "Here are the search results with basic information:",
        ]

        # Add relevance information
        if search_results:
            insights.append(
                f'Most relevant: "{search_results[0].title}" (relevance: {search_results[0].relevance_score:.2f})'
            )

        return StructuredResponse(
            query=query,
            response_type=ResponseType.SEARCH_RESULTS,  # Indicates search results fallback
            articles=search_results,
            insights=insights,
            recommendations=[
                "Click on the article links above to read the full content",
                "Try rephrasing your question for better AI analysis",
                "The articles are sorted by relevance to your query",
            ],
            conversation_id=context.conversation_id if context else uuid4(),
            response_time=0.0,  # Will be set by caller
            confidence=0.4,  # Lower confidence for fallback
        )

    def _create_basic_summary(self, article: ArticleMatch) -> str:
        """
        Create a basic summary from article content without LLM.

        This is used when LLM-based summarization fails or times out.
        """
        # Use the content preview if available
        if hasattr(article, "content_preview") and article.content_preview:
            preview = article.content_preview
        else:
            # Fallback to metadata or title
            preview = article.metadata.get("description", "") or article.title

        # Truncate to reasonable length
        if len(preview) > 200:
            preview = preview[:197] + "..."

        return preview or "Article content available at the provided link."

    def _create_error_fallback_response(
        self,
        query: str,
        articles: List[ArticleMatch],
        context: Optional[ConversationContext],
        error_message: str,
    ) -> StructuredResponse:
        """
        Create a fallback response when response generation fails completely.

        This is used when even the search results fallback fails.
        """
        return StructuredResponse(
            query=query,
            response_type=ResponseType.ERROR,
            articles=[],  # No articles if we can't process them at all
            insights=[
                "I'm having trouble processing your request right now.",
                f"Found {len(articles)} potentially relevant articles but couldn't analyze them.",
                "Please try rephrasing your question or try again later.",
            ],
            recommendations=[
                "Try using more specific keywords",
                "Break down complex questions into simpler parts",
                "Check back in a few minutes",
            ],
            conversation_id=context.conversation_id if context else uuid4(),
            response_time=0.0,  # Will be set by caller
            confidence=0.1,  # Very low confidence for error state
        )

    # Component health check methods

    async def _check_query_processor_health(self) -> bool:
        """Check query processor health."""
        try:
            test_query = "test query"
            result = await asyncio.wait_for(
                self.query_processor.parse_query(test_query), timeout=1.0
            )
            return result is not None
        except Exception:
            return False

    async def _check_embedding_service_health(self) -> bool:
        """Check embedding service health."""
        try:
            test_text = "test"
            result = await asyncio.wait_for(
                self.embedding_service.generate_embedding(test_text), timeout=2.0
            )
            return len(result) > 0
        except Exception:
            return False

    async def _check_vector_store_health(self) -> bool:
        """Check vector store health."""
        try:
            # Try a simple search with dummy vector
            dummy_vector = [0.0] * 1536
            await asyncio.wait_for(
                self.vector_store.search_similar(
                    query_vector=dummy_vector,
                    user_id=uuid4(),
                    limit=1,
                    threshold=0.9,  # High threshold to avoid real results
                ),
                timeout=1.0,
            )
            return True
        except Exception:
            return False

    async def _check_retrieval_engine_health(self) -> bool:
        """Check retrieval engine health."""
        try:
            dummy_vector = [0.0] * 1536
            result = await asyncio.wait_for(
                self.retrieval_engine.semantic_search(
                    query_vector=dummy_vector,
                    user_id="test-user",
                    limit=1,
                    threshold=0.9,  # High threshold to avoid real results
                ),
                timeout=1.0,
            )
            return isinstance(result, list)
        except Exception:
            return False

    async def _check_response_generator_health(self) -> bool:
        """Check response generator health."""
        try:
            # This is a basic check - in production you might want a more thorough test
            return hasattr(self.response_generator, "generate_response")
        except Exception:
            return False

    async def _check_conversation_manager_health(self) -> bool:
        """Check conversation manager health."""
        try:
            # Try to get a non-existent conversation (should return None, not error)
            result = await asyncio.wait_for(
                self.conversation_manager.get_context("non-existent-id"), timeout=1.0
            )
            return result is None  # Expected result for non-existent conversation
        except Exception:
            return False
