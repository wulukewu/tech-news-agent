"""
Property-Based Tests for SupabaseServiceError
Task 1.2: 撰寫 SupabaseServiceError 的屬性測試

This module contains property-based tests that verify the correctness
of the SupabaseServiceError exception class using Hypothesis.

The tests validate that database exceptions are properly wrapped with
descriptive messages and that original error context is preserved.
"""

from typing import Optional

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.core.exceptions import SupabaseServiceError


# Custom strategies for generating test data
def valid_text(min_size=1, max_size=200):
    """Generate valid text without null bytes or control characters."""
    return st.text(
        alphabet=st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters="\x00"),
        min_size=min_size,
        max_size=max_size,
    ).filter(lambda x: x.strip())


@st.composite
def exception_messages(draw):
    """Generate realistic exception messages."""
    return draw(valid_text(min_size=5, max_size=200))


@st.composite
def context_dicts(draw):
    """Generate context dictionaries with various key-value pairs."""
    # Generate 0-5 key-value pairs
    num_items = draw(st.integers(min_value=0, max_value=5))
    context = {}

    for _ in range(num_items):
        key = draw(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=97, max_codepoint=122
                ),
                min_size=1,
                max_size=20,
            )
        )
        value = draw(
            st.one_of(st.text(min_size=0, max_size=100), st.integers(), st.booleans(), st.none())
        )
        context[key] = value

    return context


@st.composite
def original_exceptions(draw):
    """Generate various types of exceptions that might occur in database operations."""
    exception_type = draw(
        st.sampled_from(
            [ValueError, RuntimeError, ConnectionError, TimeoutError, KeyError, AttributeError]
        )
    )
    message = draw(exception_messages())
    return exception_type(message)


# ============================================================================
# Feature: data-access-layer-refactor, Property 27: Exception Wrapping
# ============================================================================


@given(
    message=exception_messages(),
    original_error=st.one_of(st.none(), original_exceptions()),
    context=st.one_of(st.none(), context_dicts()),
)
@settings(max_examples=5, deadline=None)
def test_property_27_exception_wrapping_preserves_original_error(
    message: str, original_error: Optional[Exception], context: Optional[dict]
):
    """
    **Validates: Requirements 13.8**

    Property 27: Exception Wrapping

    For any database exception raised during operations, it should be caught
    and wrapped in a SupabaseServiceError with a descriptive message and the
    original exception preserved.

    This test verifies that:
    1. The SupabaseServiceError can be created with any message
    2. The original exception is preserved in the original_error attribute
    3. The context information is properly stored
    4. The error can be converted to a string representation
    """
    # Create SupabaseServiceError with the given parameters
    error = SupabaseServiceError(message=message, original_error=original_error, context=context)

    # Verify message is preserved
    assert error.message == message, "Error message should be preserved"

    # Verify original error is preserved
    assert error.original_error == original_error, "Original error should be preserved"

    # Verify context is preserved (should be empty dict if None was passed)
    expected_context = context if context is not None else {}
    assert error.context == expected_context, "Context should be preserved or default to empty dict"

    # Verify the error can be converted to string without raising exceptions
    error_str = str(error)
    assert isinstance(error_str, str), "Error should be convertible to string"
    assert message in error_str, "Error string should contain the message"

    # Verify original error appears in string representation if present
    if original_error is not None:
        assert "Original error:" in error_str, "Error string should mention original error"
        assert (
            str(original_error) in error_str
        ), "Error string should contain original error details"

    # Verify context appears in string representation if present
    if context:
        assert "Context:" in error_str, "Error string should mention context"


@given(message=exception_messages(), original_error=original_exceptions())
@settings(max_examples=5, deadline=None)
def test_property_27_exception_wrapping_maintains_exception_chain(
    message: str, original_error: Exception
):
    """
    **Validates: Requirements 13.8**

    Property 27: Exception Wrapping (Exception Chain)

    For any database exception, when wrapped in SupabaseServiceError,
    the original exception should be accessible and the error should
    maintain proper exception semantics.

    This test verifies that:
    1. The wrapped exception is a proper Exception instance
    2. The original exception type and message are preserved
    3. The wrapped exception can be raised and caught
    4. The original exception details remain accessible after wrapping
    """
    # Create wrapped error
    wrapped_error = SupabaseServiceError(
        message=message, original_error=original_error, context={"operation": "test_operation"}
    )

    # Verify it's an Exception instance
    assert isinstance(wrapped_error, Exception), "SupabaseServiceError should be an Exception"

    # Verify original error is accessible
    assert (
        wrapped_error.original_error is original_error
    ), "Original error should be the same object"

    # Verify original error type is preserved
    assert type(wrapped_error.original_error) == type(
        original_error
    ), "Original error type should be preserved"

    # Verify original error message is preserved
    assert str(wrapped_error.original_error) == str(
        original_error
    ), "Original error message should be preserved"

    # Verify the wrapped error can be raised and caught
    with pytest.raises(SupabaseServiceError) as exc_info:
        raise wrapped_error

    caught_error = exc_info.value
    assert caught_error.message == message, "Caught error should have the same message"
    assert (
        caught_error.original_error is original_error
    ), "Caught error should have the same original error"


@given(message=exception_messages(), context=context_dicts())
@settings(max_examples=5, deadline=None)
def test_property_27_exception_wrapping_stores_context_information(message: str, context: dict):
    """
    **Validates: Requirements 13.8**

    Property 27: Exception Wrapping (Context Storage)

    For any database exception, when wrapped in SupabaseServiceError,
    the context information should be properly stored and accessible.

    This test verifies that:
    1. Context dictionary is stored correctly
    2. All context keys and values are preserved
    3. Context can be accessed after exception creation
    4. Empty context is handled correctly
    """
    # Create error with context
    error = SupabaseServiceError(message=message, original_error=None, context=context)

    # Verify context is stored
    assert error.context == context, "Context should be stored exactly as provided"

    # Verify all context keys are accessible
    for key, value in context.items():
        assert key in error.context, f"Context key '{key}' should be present"
        assert error.context[key] == value, f"Context value for '{key}' should match"

    # Verify context is a dict
    assert isinstance(error.context, dict), "Context should be a dictionary"


@given(message=exception_messages())
@settings(max_examples=5, deadline=None)
def test_property_27_exception_wrapping_handles_missing_context(message: str):
    """
    **Validates: Requirements 13.8**

    Property 27: Exception Wrapping (Default Context)

    For any database exception wrapped without explicit context,
    the SupabaseServiceError should default to an empty context dictionary.

    This test verifies that:
    1. None context is converted to empty dict
    2. Missing context parameter defaults to empty dict
    3. The error remains functional without context
    """
    # Create error without context (None)
    error_with_none = SupabaseServiceError(message=message, original_error=None, context=None)

    assert error_with_none.context == {}, "None context should default to empty dict"
    assert isinstance(error_with_none.context, dict), "Context should be a dict even when None"

    # Create error without context parameter
    error_without_context = SupabaseServiceError(message=message)

    assert error_without_context.context == {}, "Missing context should default to empty dict"
    assert isinstance(
        error_without_context.context, dict
    ), "Context should be a dict even when omitted"


@given(
    message=exception_messages(),
    original_error=st.one_of(st.none(), original_exceptions()),
    context=st.one_of(st.none(), context_dicts()),
)
@settings(max_examples=5, deadline=None)
def test_property_27_exception_wrapping_string_representation_format(
    message: str, original_error: Optional[Exception], context: Optional[dict]
):
    """
    **Validates: Requirements 13.8**

    Property 27: Exception Wrapping (String Representation)

    For any SupabaseServiceError, the string representation should be
    well-formatted and contain all relevant information separated by pipes.

    This test verifies that:
    1. The string representation is properly formatted
    2. Components are separated by " | "
    3. All non-empty components are included
    4. The format is consistent and parseable
    """
    error = SupabaseServiceError(message=message, original_error=original_error, context=context)

    error_str = str(error)

    # Verify message is always first
    assert error_str.startswith(message), "Error string should start with the message"

    # Count expected components
    expected_components = 1  # message is always present
    if context:
        expected_components += 1
    if original_error is not None:
        expected_components += 1

    # Verify components are separated by " | "
    if expected_components > 1:
        assert " | " in error_str, "Multiple components should be separated by ' | '"
        components = error_str.split(" | ")
        assert (
            len(components) == expected_components
        ), f"Should have {expected_components} components"

    # Verify each component is non-empty
    if " | " in error_str:
        components = error_str.split(" | ")
        for component in components:
            assert component.strip(), "Each component should be non-empty"
