"""
Simple test for Task 9.2 error handling mechanisms without full app dependencies.
"""

import asyncio
import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.qa_agent.models import ResponseType
from app.qa_agent.qa_agent_controller import CircuitBreaker, RetryMechanism


async def test_retry_mechanism():
    """Test the retry mechanism with exponential backoff."""
    print("Testing retry mechanism...")

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
    print("✅ Retry mechanism test passed")


async def test_circuit_breaker():
    """Test the circuit breaker pattern."""
    print("Testing circuit breaker...")

    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    async def failing_operation():
        raise Exception("Test failure")

    # First two failures should be allowed
    for i in range(2):
        try:
            await cb.call(failing_operation)
        except Exception:
            pass

    assert cb.state == "OPEN"
    print(f"Circuit breaker opened after {cb.failure_count} failures")

    # Third call should be blocked
    try:
        await cb.call(failing_operation)
        assert False, "Should have been blocked by circuit breaker"
    except Exception as e:
        assert "Circuit breaker is OPEN" in str(e)

    print("✅ Circuit breaker test passed")


def test_response_types():
    """Test that new response types are available."""
    print("Testing response types...")

    # Check that new response types exist
    assert hasattr(ResponseType, "PARTIAL")
    assert hasattr(ResponseType, "SEARCH_RESULTS")
    assert ResponseType.PARTIAL == "partial"
    assert ResponseType.SEARCH_RESULTS == "search_results"

    print("✅ Response types test passed")


async def test_error_handling_features():
    """Test that error handling features are properly implemented."""
    print("Testing error handling features...")

    # Test that RetryMechanism handles non-transient errors correctly
    call_count = 0

    async def non_transient_error():
        nonlocal call_count
        call_count += 1
        raise ValueError("Non-transient error")

    try:
        await RetryMechanism.execute_with_retry(non_transient_error, max_retries=3)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    # Should only be called once (no retries for non-transient errors)
    assert call_count == 1

    print("✅ Error handling features test passed")


async def main():
    """Run all tests."""
    print("Running Task 9.2 Error Handling Tests")
    print("=" * 50)

    try:
        await test_retry_mechanism()
        await test_circuit_breaker()
        test_response_types()
        await test_error_handling_features()

        print("\n" + "=" * 50)
        print("🎉 All tests passed! Task 9.2 implementation is working correctly.")
        print("\nImplemented features:")
        print("- ✅ Retry mechanism with exponential backoff")
        print("- ✅ Circuit breaker pattern for external services")
        print("- ✅ New response types for partial results and search fallbacks")
        print("- ✅ Proper error classification and handling")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
