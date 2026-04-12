"""
Property-Based Tests for SupabaseService Context Manager
Task 3.4: 撰寫 context manager 的屬性測試

This module contains property-based tests that verify the correctness
of the SupabaseService context manager using Hypothesis.

**Validates: Requirements 17.3**
"""

from unittest.mock import MagicMock

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.services.supabase_service import SupabaseService

# ============================================================================
# Property 36: Context Manager Resource Cleanup (Task 3.4)
# ============================================================================


@given(
    should_raise_exception=st.booleans(),
    exception_type=st.sampled_from([ValueError, RuntimeError, KeyError, TypeError]),
)
@settings(
    max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@pytest.mark.asyncio
async def test_property_36_context_manager_resource_cleanup(should_raise_exception, exception_type):
    """
    **Validates: Requirements 17.3**

    Property 36: Context Manager Resource Cleanup

    For any usage of SupabaseService as an async context manager, resources
    should be automatically cleaned up when exiting the context, regardless
    of whether an exception occurred.

    This property verifies that:
    1. Resources are cleaned up in normal execution (no exception)
    2. Resources are cleaned up even when an exception occurs
    3. The close() method is always called when exiting the context
    """
    # Arrange: Create mock client
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
        MagicMock()
    )

    # Track if close was called
    close_called = False

    async def mock_close():
        nonlocal close_called
        close_called = True

    # Act & Assert
    if should_raise_exception:
        # Test with exception
        with pytest.raises(exception_type):
            async with SupabaseService(client=mock_client) as service:
                # Mock the close method to track calls
                service.close = mock_close

                # Raise an exception inside the context
                raise exception_type("Test exception")

        # Verify close was called even with exception
        assert (
            close_called
        ), f"close() should be called even when {exception_type.__name__} is raised"

    else:
        # Test without exception (normal execution)
        async with SupabaseService(client=mock_client) as service:
            # Mock the close method to track calls
            service.close = mock_close

            # Normal execution - no exception
            assert service is not None

        # Verify close was called in normal execution
        assert close_called, "close() should be called in normal execution"


@given(num_operations=st.integers(min_value=0, max_value=10))
@settings(
    max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@pytest.mark.asyncio
async def test_property_36_context_manager_cleanup_after_operations(num_operations):
    """
    **Validates: Requirements 17.3**

    Property 36: Context Manager Resource Cleanup (with operations)

    For any number of operations performed within the context manager,
    resources should be cleaned up when exiting the context.

    This property verifies that cleanup happens regardless of how many
    operations were performed inside the context.
    """
    # Arrange: Create mock client
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
        MagicMock()
    )

    # Track if close was called
    close_called = False

    async def mock_close():
        nonlocal close_called
        close_called = True

    # Act
    async with SupabaseService(client=mock_client) as service:
        # Mock the close method to track calls
        service.close = mock_close

        # Perform some number of operations
        for _ in range(num_operations):
            # Simulate some operation
            _ = service.client

    # Assert: Verify close was called
    assert close_called, f"close() should be called after {num_operations} operations"


@given(exception_message=st.text(min_size=1, max_size=100))
@settings(
    max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@pytest.mark.asyncio
async def test_property_36_context_manager_cleanup_with_various_exceptions(exception_message):
    """
    **Validates: Requirements 17.3**

    Property 36: Context Manager Resource Cleanup (various exception messages)

    For any exception message raised within the context manager,
    resources should be cleaned up when exiting the context.

    This property verifies that cleanup happens regardless of the
    exception message content.
    """
    # Arrange: Create mock client
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
        MagicMock()
    )

    # Track if close was called
    close_called = False

    async def mock_close():
        nonlocal close_called
        close_called = True

    # Act & Assert
    with pytest.raises(ValueError):
        async with SupabaseService(client=mock_client) as service:
            # Mock the close method to track calls
            service.close = mock_close

            # Raise an exception with the generated message
            raise ValueError(exception_message)

    # Verify close was called
    assert (
        close_called
    ), f"close() should be called even with exception message: {exception_message[:50]}"


@given(nested_level=st.integers(min_value=1, max_value=3))
@settings(
    max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@pytest.mark.asyncio
async def test_property_36_context_manager_nested_contexts(nested_level):
    """
    **Validates: Requirements 17.3**

    Property 36: Context Manager Resource Cleanup (nested contexts)

    For any level of nested context managers, each context should
    properly clean up its resources when exiting.

    This property verifies that cleanup happens correctly even with
    nested context managers.
    """
    # Track close calls for each level
    close_calls = []

    async def create_mock_close(level):
        async def mock_close():
            close_calls.append(level)

        return mock_close

    # Create nested contexts
    async def create_nested_context(level):
        if level == 0:
            return

        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            MagicMock()
        )

        async with SupabaseService(client=mock_client) as service:
            service.close = await create_mock_close(level)
            await create_nested_context(level - 1)

    # Act
    await create_nested_context(nested_level)

    # Assert: Verify all levels were closed
    assert (
        len(close_calls) == nested_level
    ), f"All {nested_level} nested contexts should call close()"

    # Verify they were closed in reverse order (inner to outer)
    expected_order = list(range(1, nested_level + 1))
    assert (
        close_calls == expected_order
    ), f"Contexts should be closed in order: {expected_order}, got: {close_calls}"


@given(use_context_manager=st.booleans())
@settings(
    max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@pytest.mark.asyncio
async def test_property_36_context_manager_vs_manual_close(use_context_manager):
    """
    **Validates: Requirements 17.3**

    Property 36: Context Manager Resource Cleanup (comparison with manual close)

    For any usage pattern (context manager vs manual close), resources
    should be properly cleaned up.

    This property verifies that both usage patterns result in proper cleanup.
    """
    # Arrange: Create mock client
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
        MagicMock()
    )

    # Track if close was called
    close_called = False

    async def mock_close():
        nonlocal close_called
        close_called = True

    # Act
    if use_context_manager:
        # Use context manager
        async with SupabaseService(client=mock_client) as service:
            service.close = mock_close
    else:
        # Manual close
        service = SupabaseService(client=mock_client)
        service.close = mock_close
        await service.close()

    # Assert: Verify close was called in both cases
    assert close_called, f"close() should be called with use_context_manager={use_context_manager}"


@given(has_exception=st.booleans())
@settings(
    max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
@pytest.mark.asyncio
async def test_property_36_context_manager_exception_timing(has_exception):
    """
    **Validates: Requirements 17.3**

    Property 36: Context Manager Resource Cleanup (exception timing)

    For any execution path (with or without exception in body), the context
    manager should properly clean up resources.

    This property verifies that __aexit__ is called and cleanup happens
    regardless of whether an exception occurs in the body.
    """
    # Arrange: Create mock client
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
        MagicMock()
    )

    # Track if close was called
    close_called = False

    async def mock_close():
        nonlocal close_called
        close_called = True

    # Act & Assert
    if has_exception:
        # Exception in body - __aexit__ will be called
        with pytest.raises(ValueError):
            async with SupabaseService(client=mock_client) as service:
                service.close = mock_close
                raise ValueError("Exception in body")

        # close() should be called because __aexit__ was reached
        assert close_called, "close() should be called if exception in body"

    else:
        # No exception - normal flow
        async with SupabaseService(client=mock_client) as service:
            service.close = mock_close

        # close() should be called in normal flow
        assert close_called, "close() should be called in normal flow"
