"""
Test suite for Task 9.2: Enhanced Error Handling and Fallback Mechanisms

This test suite validates the comprehensive error handling and fallback mechanisms
implemented in the QAAgentController, ensuring compliance with requirements:
- 9.1: Fallback to keyword search when vector store unavailable
- 9.2: Provide search results list when generation fails
- 9.4: Provide partial results when query times out
- 9.5: Implement retry mechanism for temporary errors
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from .embedding_service import EmbeddingError
from .models import (
    ArticleMatch,
    ParsedQuery,
    QueryIntent,
    QueryLanguage,
    ResponseType,
    StructuredResponse,
)
from .qa_agent_controller import CircuitBreaker, QAAgentController, RetryMechanism
from .response_generator import ResponseGeneratorError
from .vector_store import VectorStoreError


class TestRetryMechanism:
    """Test the retry mechanism implementation."""

    @pytest.mark.asyncio
    async def test_successful_operation_no_retry(self):
        """Test that successful operations don't trigger retries."""
        call_count = 0

        async def successful_operation():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await RetryMechanism.execute_with_retry(successful_operation, max_retries=3)

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_transient_error_retry_success(self):
        """Test retry mechanism with transient errors that eventually succeed."""
        call_count = 0

        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Transient error")
            return "success"

        result = await RetryMechanism.execute_with_retry(
            failing_then_success, max_retries=3, base_delay=0.01  # Fast for testing
        )

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exhausted(self):
        """Test that max retries are respected."""
        call_count = 0

        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise VectorStoreError("Always fails")

        with pytest.raises(VectorStoreError):
            await RetryMechanism.execute_with_retry(always_fails, max_retries=2, base_delay=0.01)

        assert call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_non_transient_error_no_retry(self):
        """Test that non-transient errors don't trigger retries."""
        call_count = 0

        async def non_transient_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Non-transient error")

        with pytest.raises(ValueError):
            await RetryMechanism.execute_with_retry(non_transient_error, max_retries=3)

        assert call_count == 1  # No retries


class TestCircuitBreaker:
    """Test the circuit breaker implementation."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)

        async def successful_operation():
            return "success"

        result = await cb.call(successful_operation)
        assert result == "success"
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)

        async def failing_operation():
            raise Exception("Test failure")

        # First two failures should be allowed
        for _ in range(2):
            with pytest.raises(Exception):
                await cb.call(failing_operation)

        assert cb.state == "OPEN"

        # Third call should be blocked by circuit breaker
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await cb.call(failing_operation)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker recovery to half-open state."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

        async def failing_operation():
            raise Exception("Test failure")

        async def successful_operation():
            return "success"

        # Trigger circuit breaker to open
        with pytest.raises(Exception):
            await cb.call(failing_operation)

        assert cb.state == "OPEN"

        # Wait for recovery timeout
        await asyncio.sleep(0.2)

        # Next call should succeed and close circuit
        result = await cb.call(successful_operation)
        assert result == "success"
        assert cb.state == "CLOSED"


class TestEnhancedErrorHandling:
    """Test enhanced error handling in QAAgentController."""

    @pytest.fixture
    def mock_controller(self):
        """Create a QAAgentController with mocked components."""
        controller = QAAgentController()

        # Mock all components
        controller.query_processor = AsyncMock()
        controller.embedding_service = AsyncMock()
        controller.vector_store = AsyncMock()
        controller.retrieval_engine = AsyncMock()
        controller.response_generator = AsyncMock()
        controller.conversation_manager = AsyncMock()

        return controller

    @pytest.mark.asyncio
    async def test_keyword_search_fallback_on_vector_store_failure(self, mock_controller):
        """
        Test Requirement 9.1: Fallback to keyword search when vector store unavailable.
        """
        # Setup mocks
        mock_controller.query_processor.validate_query.return_value = MagicMock(is_valid=True)
        mock_controller.query_processor.parse_query.return_value = ParsedQuery(
            original_query="test query",
            language=QueryLanguage.EN,
            intent=QueryIntent.SEARCH,
            keywords=["test", "query"],
            confidence=0.8,
        )

        # Mock embedding generation success
        mock_controller.embedding_service.generate_embedding.return_value = [0.1] * 1536

        # Mock vector store failure, then keyword search success
        mock_controller.retrieval_engine.intelligent_search.side_effect = VectorStoreError(
            "Vector store unavailable"
        )
        mock_controller.retrieval_engine.semantic_search.side_effect = VectorStoreError(
            "Vector store unavailable"
        )
        mock_controller.retrieval_engine._expand_by_keywords.return_value = [
            ArticleMatch(
                article_id=str(uuid4()),
                title="Test Article",
                content_preview="Test content",
                similarity_score=0.7,
                url="http://example.com",
                metadata={"category": "test"},
            )
        ]

        # Mock response generation
        mock_controller.response_generator.generate_response.return_value = StructuredResponse(
            query="test query",
            response_type=ResponseType.STRUCTURED,
            articles=[],
            insights=["Test insight"],
            recommendations=["Test recommendation"],
            conversation_id=uuid4(),
            response_time=0.5,
            confidence=0.8,
        )

        # Execute query
        response = await mock_controller.process_query(user_id=str(uuid4()), query="test query")

        # Verify keyword search was called as fallback
        mock_controller.retrieval_engine._expand_by_keywords.assert_called()
        assert response.response_type in [ResponseType.STRUCTURED, ResponseType.SEARCH_RESULTS]

    @pytest.mark.asyncio
    async def test_search_results_fallback_on_generation_failure(self, mock_controller):
        """
        Test Requirement 9.2: Provide search results list when generation fails.
        """
        # Setup mocks for successful retrieval
        mock_controller.query_processor.validate_query.return_value = MagicMock(is_valid=True)
        mock_controller.query_processor.parse_query.return_value = ParsedQuery(
            original_query="test query",
            language=QueryLanguage.EN,
            intent=QueryIntent.SEARCH,
            keywords=["test", "query"],
            confidence=0.8,
        )

        mock_controller.embedding_service.generate_embedding.return_value = [0.1] * 1536

        # Mock successful article retrieval
        test_articles = [
            ArticleMatch(
                article_id=str(uuid4()),
                title="Test Article 1",
                content_preview="Test content 1",
                similarity_score=0.9,
                url="http://example.com/1",
                metadata={"category": "test"},
            ),
            ArticleMatch(
                article_id=str(uuid4()),
                title="Test Article 2",
                content_preview="Test content 2",
                similarity_score=0.8,
                url="http://example.com/2",
                metadata={"category": "test"},
            ),
        ]

        mock_controller.retrieval_engine.intelligent_search.return_value = {
            "results": test_articles,
            "total_found": len(test_articles),
        }

        # Mock response generation failure
        mock_controller.response_generator.generate_response.side_effect = ResponseGeneratorError(
            "Generation failed"
        )

        # Execute query
        response = await mock_controller.process_query(user_id=str(uuid4()), query="test query")

        # Verify search results fallback was used
        assert response.response_type == ResponseType.SEARCH_RESULTS
        assert len(response.articles) > 0
        assert "search results" in " ".join(response.insights).lower()

    @pytest.mark.asyncio
    async def test_partial_results_on_timeout(self, mock_controller):
        """
        Test Requirement 9.4: Provide partial results when query times out.
        """
        # Setup mocks
        mock_controller.query_processor.validate_query.return_value = MagicMock(is_valid=True)
        mock_controller.query_processor.parse_query.return_value = ParsedQuery(
            original_query="test query",
            language=QueryLanguage.EN,
            intent=QueryIntent.SEARCH,
            keywords=["test", "query"],
            confidence=0.8,
        )

        mock_controller.embedding_service.generate_embedding.return_value = [0.1] * 1536

        # Mock timeout in response generation
        mock_controller.retrieval_engine.intelligent_search.return_value = {
            "results": [
                ArticleMatch(
                    article_id=str(uuid4()),
                    title="Test Article",
                    content_preview="Test content",
                    similarity_score=0.8,
                    url="http://example.com",
                    metadata={"category": "test"},
                )
            ],
            "total_found": 1,
        }

        mock_controller.response_generator.generate_response.side_effect = asyncio.TimeoutError(
            "Generation timed out"
        )

        # Execute query
        response = await mock_controller.process_query(user_id=str(uuid4()), query="test query")

        # Verify partial results were provided
        assert response.response_type == ResponseType.PARTIAL
        assert "timed out" in " ".join(response.insights).lower()
        assert len(response.articles) > 0  # Should have basic summaries

    @pytest.mark.asyncio
    async def test_retry_mechanism_integration(self, mock_controller):
        """
        Test Requirement 9.5: Retry mechanism for temporary errors.
        """
        # Setup mocks
        mock_controller.query_processor.validate_query.return_value = MagicMock(is_valid=True)
        mock_controller.query_processor.parse_query.return_value = ParsedQuery(
            original_query="test query",
            language=QueryLanguage.EN,
            intent=QueryIntent.SEARCH,
            keywords=["test", "query"],
            confidence=0.8,
        )

        # Mock embedding service with transient failures then success
        call_count = 0

        async def embedding_with_retries(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise EmbeddingError("Transient error")
            return [0.1] * 1536

        mock_controller.embedding_service.generate_embedding.side_effect = embedding_with_retries

        # Mock successful retrieval and response
        mock_controller.retrieval_engine.intelligent_search.return_value = {
            "results": [],
            "total_found": 0,
        }
        mock_controller.response_generator.generate_response.return_value = StructuredResponse(
            query="test query",
            response_type=ResponseType.STRUCTURED,
            articles=[],
            insights=["Test insight"],
            recommendations=["Test recommendation"],
            conversation_id=uuid4(),
            response_time=0.5,
            confidence=0.8,
        )

        # Execute query
        response = await mock_controller.process_query(user_id=str(uuid4()), query="test query")

        # Verify retry mechanism worked (should have been called 3 times)
        assert call_count == 3
        assert response.response_type == ResponseType.STRUCTURED

    @pytest.mark.asyncio
    async def test_comprehensive_error_logging(self, mock_controller):
        """
        Test Requirement 9.3: Record all errors and provide meaningful error messages.
        """
        # Setup mocks for failure scenario
        mock_controller.query_processor.validate_query.return_value = MagicMock(is_valid=True)
        mock_controller.query_processor.parse_query.side_effect = Exception("Parsing failed")

        with patch("backend.app.qa_agent.qa_agent_controller.logger") as mock_logger:
            # Execute query that will fail
            response = await mock_controller.process_query(user_id=str(uuid4()), query="test query")

            # Verify comprehensive error logging
            mock_logger.error.assert_called()
            error_call = mock_logger.error.call_args

            # Check that error context was logged
            assert "extra" in error_call.kwargs
            error_context = error_call.kwargs["extra"]
            assert "user_id" in error_context
            assert "query_length" in error_context
            assert "error_type" in error_context

            # Verify response is error type
            assert response.response_type == ResponseType.ERROR

    @pytest.mark.asyncio
    async def test_system_health_with_circuit_breakers(self, mock_controller):
        """Test system health reporting includes circuit breaker states."""
        # Mock component health checks
        mock_controller._check_query_processor_health.return_value = True
        mock_controller._check_embedding_service_health.return_value = True
        mock_controller._check_vector_store_health.return_value = True
        mock_controller._check_retrieval_engine_health.return_value = True
        mock_controller._check_response_generator_health.return_value = True
        mock_controller._check_conversation_manager_health.return_value = True

        # Get system health
        health = await mock_controller.get_system_health()

        # Verify circuit breaker information is included
        assert "circuit_breakers" in health
        assert "embedding_service" in health["circuit_breakers"]
        assert "vector_store" in health["circuit_breakers"]
        assert "response_generator" in health["circuit_breakers"]

        # Verify error handling features are reported
        assert "error_handling_features" in health
        features = health["error_handling_features"]
        assert features["keyword_search_fallback"] is True
        assert features["search_results_fallback"] is True
        assert features["partial_results_on_timeout"] is True
        assert features["retry_mechanisms"] is True
        assert features["circuit_breakers"] is True
        assert features["comprehensive_error_logging"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
