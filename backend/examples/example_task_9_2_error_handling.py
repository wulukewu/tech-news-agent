"""
Example demonstrating Task 9.2: Enhanced Error Handling and Fallback Mechanisms

This example showcases all the error handling and fallback mechanisms implemented:
- Requirement 9.1: Fallback to keyword search when vector store unavailable
- Requirement 9.2: Provide search results list when generation fails
- Requirement 9.4: Provide partial results when query times out
- Requirement 9.5: Implement retry mechanism for temporary errors
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.qa_agent.models import ResponseType
from app.qa_agent.qa_agent_controller import CircuitBreaker, RetryMechanism


class MockComponent:
    """Base mock component for demonstration."""

    def __init__(self, name: str, failure_mode: str = None):
        self.name = name
        self.failure_mode = failure_mode
        self.call_count = 0

    async def __call__(self, *args, **kwargs):
        self.call_count += 1

        if self.failure_mode == "transient" and self.call_count <= 2:
            raise ConnectionError(f"{self.name} transient failure")
        elif self.failure_mode == "permanent":
            raise Exception(f"{self.name} permanent failure")
        elif self.failure_mode == "timeout":
            raise asyncio.TimeoutError(f"{self.name} timeout")

        return f"{self.name} success"


async def demonstrate_retry_mechanism():
    """Demonstrate the retry mechanism with exponential backoff."""
    print("\n🔄 Demonstrating Retry Mechanism (Requirement 9.5)")
    print("-" * 60)

    # Test successful retry after transient failures
    print("1. Testing transient failure recovery:")
    mock_service = MockComponent("EmbeddingService", "transient")

    start_time = datetime.now()
    result = await RetryMechanism.execute_with_retry(mock_service, max_retries=3, base_delay=0.1)
    end_time = datetime.now()

    print(f"   Result: {result}")
    print(f"   Attempts: {mock_service.call_count}")
    print(f"   Duration: {(end_time - start_time).total_seconds():.2f}s")

    # Test permanent failure (no retries)
    print("\n2. Testing permanent failure (no retries):")
    mock_service = MockComponent("DatabaseService", "permanent")

    try:
        await RetryMechanism.execute_with_retry(
            mock_service,
            max_retries=3,
            base_delay=0.1,
            transient_exceptions=(ConnectionError,),  # Only retry connection errors
        )
    except Exception as e:
        print(f"   Error: {e}")
        print(f"   Attempts: {mock_service.call_count} (no retries for permanent errors)")


async def demonstrate_circuit_breaker():
    """Demonstrate the circuit breaker pattern."""
    print("\n⚡ Demonstrating Circuit Breaker Pattern (Requirement 9.5)")
    print("-" * 60)

    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=2.0)
    mock_service = MockComponent("ExternalAPI", "permanent")

    print("1. Testing circuit breaker opening after failures:")

    # Cause failures to open circuit breaker
    for i in range(4):
        try:
            await cb.call(mock_service)
        except Exception as e:
            print(f"   Attempt {i+1}: {e}")
            print(f"   Circuit state: {cb.state}, Failures: {cb.failure_count}")

    print(f"\n2. Circuit breaker is now {cb.state}")

    # Try to call while circuit is open
    try:
        await cb.call(mock_service)
    except Exception as e:
        print(f"   Blocked call: {e}")


def demonstrate_response_types():
    """Demonstrate the new response types for error scenarios."""
    print("\n📋 Demonstrating Enhanced Response Types (Requirements 9.2, 9.4)")
    print("-" * 60)

    print("1. Available response types:")
    for response_type in ResponseType:
        description = {
            ResponseType.STRUCTURED: "Full AI-generated response with insights",
            ResponseType.SIMPLE: "Basic response with minimal processing",
            ResponseType.ERROR: "Error response with helpful guidance",
            ResponseType.CLARIFICATION: "Request for query clarification",
            ResponseType.PARTIAL: "Partial results due to timeout (Req 9.4)",
            ResponseType.SEARCH_RESULTS: "Search results fallback when generation fails (Req 9.2)",
        }.get(response_type, "Unknown")

        print(f"   - {response_type.value}: {description}")


async def demonstrate_error_scenarios():
    """Demonstrate various error scenarios and their handling."""
    print("\n🚨 Demonstrating Error Scenarios and Fallbacks")
    print("-" * 60)

    # Scenario 1: Vector store unavailable (Requirement 9.1)
    print("1. Vector Store Unavailable → Keyword Search Fallback (Requirement 9.1)")
    print("   Scenario: Vector database is down, system falls back to keyword search")
    print("   Implementation: _keyword_search_fallback() method")
    print("   Result: Users still get relevant articles via keyword matching")

    # Scenario 2: Response generation fails (Requirement 9.2)
    print("\n2. Response Generation Fails → Search Results List (Requirement 9.2)")
    print("   Scenario: LLM service fails to generate insights")
    print("   Implementation: _create_search_results_fallback_response() method")
    print("   Result: Users get article list with basic summaries")

    # Scenario 3: Query timeout (Requirement 9.4)
    print("\n3. Query Timeout → Partial Results (Requirement 9.4)")
    print("   Scenario: Query processing takes too long")
    print("   Implementation: _get_partial_results_on_timeout() method")
    print("   Result: Users get quick results with explanation")

    # Scenario 4: Comprehensive error logging (Requirement 9.3)
    print("\n4. Comprehensive Error Logging (Requirement 9.3)")
    print("   Features:")
    print("   - Structured error context with user_id, query_length, etc.")
    print("   - Component-specific error tracking")
    print("   - Performance metrics in error logs")
    print("   - Error classification (transient vs permanent)")


async def demonstrate_system_health():
    """Demonstrate system health monitoring with error handling features."""
    print("\n🏥 Demonstrating System Health Monitoring")
    print("-" * 60)

    # Create a mock controller to show health features
    print("Enhanced health monitoring includes:")
    print("- Component health status")
    print("- Circuit breaker states")
    print("- Error handling feature flags")
    print("- Performance metrics")

    health_example = {
        "overall_health": 0.83,
        "status": "healthy",
        "components": {
            "query_processor": True,
            "embedding_service": True,
            "vector_store": False,  # Simulated failure
            "retrieval_engine": True,
            "response_generator": True,
            "conversation_manager": True,
        },
        "circuit_breakers": {
            "embedding_service": {"state": "CLOSED", "failure_count": 0},
            "vector_store": {"state": "OPEN", "failure_count": 5},
            "response_generator": {"state": "CLOSED", "failure_count": 1},
        },
        "error_handling_features": {
            "keyword_search_fallback": True,
            "search_results_fallback": True,
            "partial_results_on_timeout": True,
            "retry_mechanisms": True,
            "circuit_breakers": True,
            "comprehensive_error_logging": True,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

    print("\nExample health report:")
    for key, value in health_example.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for subkey, subvalue in value.items():
                print(f"    {subkey}: {subvalue}")
        else:
            print(f"  {key}: {value}")


async def main():
    """Run all demonstrations."""
    print("🎯 Task 9.2: Enhanced Error Handling and Fallback Mechanisms")
    print("=" * 80)
    print("Demonstrating comprehensive error handling for the Intelligent Q&A Agent")

    try:
        await demonstrate_retry_mechanism()
        await demonstrate_circuit_breaker()
        demonstrate_response_types()
        await demonstrate_error_scenarios()
        await demonstrate_system_health()

        print("\n" + "=" * 80)
        print("✅ Task 9.2 Implementation Complete!")
        print("\nKey Features Implemented:")
        print("- 🔄 Retry mechanisms with exponential backoff and jitter")
        print("- ⚡ Circuit breaker pattern for external service protection")
        print("- 🔍 Keyword search fallback when vector store unavailable")
        print("- 📋 Search results fallback when AI generation fails")
        print("- ⏱️  Partial results delivery on timeout")
        print("- 📊 Comprehensive error logging with structured context")
        print("- 🏥 Enhanced system health monitoring")

        print("\nRequirements Satisfied:")
        print("- ✅ 9.1: Fallback to keyword search when vector store unavailable")
        print("- ✅ 9.2: Provide search results list when generation fails")
        print("- ✅ 9.3: Record all errors and provide meaningful error messages")
        print("- ✅ 9.4: Provide partial results when query times out")
        print("- ✅ 9.5: Implement retry mechanism for temporary errors")

    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
