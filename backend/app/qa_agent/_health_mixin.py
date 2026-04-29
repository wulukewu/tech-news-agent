"""Health check methods for QAAgentController."""
import logging

logger = logging.getLogger(__name__)


class HealthMixin:
    """Mixin providing system health check methods."""

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
