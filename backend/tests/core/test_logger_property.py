"""
Property-Based Tests for Structured Logging System

This module contains property-based tests using Hypothesis to validate
the structured logging system's behavior across a wide range of inputs.

**Validates: Requirements 5.1, 5.3**
"""

import json
import logging

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.core.logger import (
    StructuredLogger,
    get_logger,
    request_id_var,
    user_id_var,
)

# ============================================================================
# Test Strategies
# ============================================================================


@st.composite
def log_message_strategy(draw):
    """Generate valid log messages."""
    return draw(st.text(min_size=1, max_size=500))


@st.composite
def log_level_strategy(draw):
    """Generate valid log levels."""
    return draw(
        st.sampled_from(
            [
                logging.DEBUG,
                logging.INFO,
                logging.WARNING,
                logging.ERROR,
                logging.CRITICAL,
            ]
        )
    )


@st.composite
def request_id_strategy(draw):
    """Generate valid request IDs."""
    # UUID-like format or custom format
    format_type = draw(st.sampled_from(["uuid", "custom"]))
    if format_type == "uuid":
        import uuid

        return str(uuid.uuid4())
    else:
        prefix = draw(st.sampled_from(["req", "request", "trace"]))
        suffix = draw(
            st.text(
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=48),
                min_size=8,
                max_size=20,
            )
        )
        return f"{prefix}-{suffix}"


@st.composite
def user_id_strategy(draw):
    """Generate valid user IDs."""
    # UUID-like format or numeric ID
    format_type = draw(st.sampled_from(["uuid", "numeric", "string"]))
    if format_type == "uuid":
        import uuid

        return str(uuid.uuid4())
    elif format_type == "numeric":
        return str(draw(st.integers(min_value=1, max_value=999999999)))
    else:
        prefix = draw(st.sampled_from(["user", "usr", "u"]))
        suffix = draw(
            st.text(
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=48),
                min_size=4,
                max_size=15,
            )
        )
        return f"{prefix}-{suffix}"


@st.composite
def extra_fields_strategy(draw):
    """Generate extra fields for logging."""
    # Reserved field names that should not be used as extra fields
    reserved_names = {"level", "message", "exc_info", "extra", "stack_info"}

    num_fields = draw(st.integers(min_value=0, max_value=5))
    fields = {}
    for _ in range(num_fields):
        key = draw(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Ll",), min_codepoint=97, max_codepoint=122
                ),
                min_size=3,
                max_size=15,
            )
        )
        # Skip reserved field names
        if key in reserved_names:
            continue

        value_type = draw(st.sampled_from(["string", "int", "bool"]))
        if value_type == "string":
            value = draw(st.text(min_size=1, max_size=50))
        elif value_type == "int":
            value = draw(st.integers(min_value=-1000, max_value=1000))
        else:
            value = draw(st.booleans())
        fields[key] = value
    return fields


@st.composite
def logger_name_strategy(draw):
    """Generate valid logger names."""
    # Module-like names
    parts = draw(
        st.lists(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Ll",), min_codepoint=97, max_codepoint=122
                ),
                min_size=3,
                max_size=10,
            ),
            min_size=1,
            max_size=4,
        )
    )
    return ".".join(parts)


# ============================================================================
# Property 4: Structured Logging with Context
# ============================================================================


@given(
    message=log_message_strategy(),
    level=log_level_strategy(),
    logger_name=logger_name_strategy(),
)
@settings(
    max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_4_logs_always_contain_required_fields(message, level, logger_name, capsys):
    """
    **Property 4: Structured Logging with Context**

    For any log entry created in backend services, the log SHALL include
    structured fields (timestamp, level, message).

    **Validates: Requirements 5.1**
    """
    # Create logger
    logger = StructuredLogger(logger_name, level=logging.DEBUG)

    # Log message at the specified level
    if level == logging.DEBUG:
        logger.debug(message)
    elif level == logging.INFO:
        logger.info(message)
    elif level == logging.WARNING:
        logger.warning(message)
    elif level == logging.ERROR:
        logger.error(message)
    elif level == logging.CRITICAL:
        logger.critical(message)

    # Capture output
    captured = capsys.readouterr()
    output = captured.out.strip()

    # Skip if no output (level filtering)
    if not output:
        return

    # Parse JSON log
    log_data = json.loads(output)

    # Verify required structured fields are present
    assert "timestamp" in log_data, "Log must contain timestamp field"
    assert "level" in log_data, "Log must contain level field"
    assert "logger" in log_data, "Log must contain logger field"
    assert "message" in log_data, "Log must contain message field"

    # Verify field values
    assert log_data["logger"] == logger_name
    assert log_data["message"] == message
    assert log_data["level"] == logging.getLevelName(level)

    # Verify timestamp is ISO 8601 format
    assert log_data["timestamp"].endswith("Z"), "Timestamp must be in UTC (end with Z)"
    assert "T" in log_data["timestamp"], "Timestamp must be ISO 8601 format"


@given(
    message=log_message_strategy(),
    level=log_level_strategy(),
    request_id=st.one_of(st.none(), request_id_strategy()),
    user_id=st.one_of(st.none(), user_id_strategy()),
)
@settings(
    max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_4_logs_include_request_context_when_available(
    message, level, request_id, user_id, capsys
):
    """
    **Property 4: Structured Logging with Context**

    For any log entry created in backend services, the log SHALL include
    request context (user_id, request_id) when available.

    **Validates: Requirements 5.3**
    """
    # Set request context
    request_id_token = request_id_var.set(request_id)
    user_id_token = user_id_var.set(user_id)

    try:
        # Create logger
        logger = StructuredLogger("test_logger", level=logging.DEBUG)

        # Log message at the specified level
        if level == logging.DEBUG:
            logger.debug(message)
        elif level == logging.INFO:
            logger.info(message)
        elif level == logging.WARNING:
            logger.warning(message)
        elif level == logging.ERROR:
            logger.error(message)
        elif level == logging.CRITICAL:
            logger.critical(message)

        # Capture output
        captured = capsys.readouterr()
        output = captured.out.strip()

        # Skip if no output (level filtering)
        if not output:
            return

        # Parse JSON log
        log_data = json.loads(output)

        # Verify context inclusion based on availability
        if request_id is not None or user_id is not None:
            assert (
                "context" in log_data
            ), "Log must contain context when request context is available"

            if request_id is not None:
                assert (
                    "request_id" in log_data["context"]
                ), "Context must contain request_id when set"
                assert log_data["context"]["request_id"] == request_id

            if user_id is not None:
                assert "user_id" in log_data["context"], "Context must contain user_id when set"
                assert log_data["context"]["user_id"] == user_id
        else:
            # When no context is set, context field should not be present
            assert (
                "context" not in log_data
            ), "Log should not contain context when no context is available"

    finally:
        # Reset context variables
        request_id_var.reset(request_id_token)
        user_id_var.reset(user_id_token)


@given(
    message=log_message_strategy(),
    extra_fields=extra_fields_strategy(),
)
@settings(
    max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_4_logs_preserve_extra_fields(message, extra_fields, capsys):
    """
    **Property 4: Structured Logging with Context**

    For any log entry with extra fields, the log SHALL include those
    extra fields in the structured output.

    **Validates: Requirements 5.1**
    """
    # Create logger
    logger = StructuredLogger("test_logger", level=logging.DEBUG)

    # Log message with extra fields
    logger.info(message, **extra_fields)

    # Capture output
    captured = capsys.readouterr()
    output = captured.out.strip()

    # Parse JSON log
    log_data = json.loads(output)

    # Verify extra fields are present if any were provided
    if extra_fields:
        assert "extra" in log_data, "Log must contain extra field when extra fields are provided"
        for key, value in extra_fields.items():
            assert key in log_data["extra"], f"Extra field '{key}' must be present in log"
            assert log_data["extra"][key] == value, f"Extra field '{key}' must have correct value"
    else:
        # When no extra fields, extra field should not be present
        assert (
            "extra" not in log_data
        ), "Log should not contain extra field when no extra fields provided"


@given(
    message=log_message_strategy(),
    level=st.sampled_from([logging.ERROR, logging.CRITICAL]),
)
@settings(
    max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_4_error_logs_include_source_location(message, level, capsys):
    """
    **Property 4: Structured Logging with Context**

    For any ERROR or CRITICAL log entry, the log SHALL include source
    location information (file, line, function).

    **Validates: Requirements 5.1**
    """
    # Create logger
    logger = StructuredLogger("test_logger", level=logging.DEBUG)

    # Log message at ERROR or CRITICAL level
    if level == logging.ERROR:
        logger.error(message)
    else:
        logger.critical(message)

    # Capture output
    captured = capsys.readouterr()
    output = captured.out.strip()

    # Parse JSON log
    log_data = json.loads(output)

    # Verify source location is present for ERROR/CRITICAL
    assert "source" in log_data, "ERROR/CRITICAL logs must contain source location"
    assert "file" in log_data["source"], "Source must contain file path"
    assert "line" in log_data["source"], "Source must contain line number"
    assert "function" in log_data["source"], "Source must contain function name"

    # Verify source fields have valid values
    assert isinstance(log_data["source"]["file"], str)
    assert isinstance(log_data["source"]["line"], int)
    assert isinstance(log_data["source"]["function"], str)
    assert log_data["source"]["line"] > 0


@given(
    message=log_message_strategy(),
    level=st.sampled_from([logging.DEBUG, logging.INFO, logging.WARNING]),
)
@settings(
    max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_4_non_error_logs_exclude_source_location(message, level, capsys):
    """
    **Property 4: Structured Logging with Context**

    For any DEBUG, INFO, or WARNING log entry, the log SHALL NOT include
    source location information to reduce log verbosity.

    **Validates: Requirements 5.1**
    """
    # Create logger
    logger = StructuredLogger("test_logger", level=logging.DEBUG)

    # Log message at non-error level
    if level == logging.DEBUG:
        logger.debug(message)
    elif level == logging.INFO:
        logger.info(message)
    else:
        logger.warning(message)

    # Capture output
    captured = capsys.readouterr()
    output = captured.out.strip()

    # Parse JSON log
    log_data = json.loads(output)

    # Verify source location is NOT present for non-error logs
    assert "source" not in log_data, "DEBUG/INFO/WARNING logs should not contain source location"


@given(
    message=log_message_strategy(),
    request_id=request_id_strategy(),
    user_id=user_id_strategy(),
    extra_fields=extra_fields_strategy(),
)
@settings(
    max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_4_complete_log_structure_with_all_fields(
    message, request_id, user_id, extra_fields, capsys
):
    """
    **Property 4: Structured Logging with Context**

    For any log entry with full context and extra fields, the log SHALL
    include all structured fields in a consistent JSON format.

    **Validates: Requirements 5.1, 5.3**
    """
    # Set request context
    request_id_token = request_id_var.set(request_id)
    user_id_token = user_id_var.set(user_id)

    try:
        # Create logger
        logger = StructuredLogger("test_logger", level=logging.DEBUG)

        # Log message with extra fields
        logger.info(message, **extra_fields)

        # Capture output
        captured = capsys.readouterr()
        output = captured.out.strip()

        # Parse JSON log - should not raise exception
        log_data = json.loads(output)

        # Verify all expected fields are present
        assert "timestamp" in log_data
        assert "level" in log_data
        assert "logger" in log_data
        assert "message" in log_data
        assert "context" in log_data

        # Verify context contains request context
        assert log_data["context"]["request_id"] == request_id
        assert log_data["context"]["user_id"] == user_id

        # Verify extra fields if provided
        if extra_fields:
            assert "extra" in log_data
            for key, value in extra_fields.items():
                assert log_data["extra"][key] == value

        # Verify JSON structure is valid and parseable
        assert isinstance(log_data, dict)

    finally:
        # Reset context variables
        request_id_var.reset(request_id_token)
        user_id_var.reset(user_id_token)


@given(
    messages=st.lists(log_message_strategy(), min_size=2, max_size=10),
    request_id=request_id_strategy(),
)
@settings(
    max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_4_context_consistency_across_multiple_logs(messages, request_id, capsys):
    """
    **Property 4: Structured Logging with Context**

    For any sequence of log entries within the same request context,
    all logs SHALL include the same request context.

    **Validates: Requirements 5.3**
    """
    # Set request context
    request_id_token = request_id_var.set(request_id)

    try:
        # Create logger
        logger = StructuredLogger("test_logger", level=logging.DEBUG)

        # Log multiple messages
        for message in messages:
            logger.info(message)

        # Capture output
        captured = capsys.readouterr()
        output_lines = [line for line in captured.out.strip().split("\n") if line]

        # Verify we have the expected number of log lines
        assert len(output_lines) == len(messages)

        # Parse all logs and verify consistent context
        for output_line in output_lines:
            log_data = json.loads(output_line)

            # Verify context is present and consistent
            assert "context" in log_data
            assert "request_id" in log_data["context"]
            assert log_data["context"]["request_id"] == request_id

    finally:
        # Reset context variables
        request_id_var.reset(request_id_token)


@given(
    message=log_message_strategy(),
    logger_name=logger_name_strategy(),
)
@settings(
    max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None
)
def test_property_4_get_logger_returns_valid_structured_logger(message, logger_name, capsys):
    """
    **Property 4: Structured Logging with Context**

    For any logger name, get_logger SHALL return a StructuredLogger that
    produces valid structured logs.

    **Validates: Requirements 5.1**
    """
    # Get logger using convenience function
    logger = get_logger(logger_name)

    # Verify it's a StructuredLogger instance
    assert isinstance(logger, StructuredLogger)

    # Log a message
    logger.info(message)

    # Capture output
    captured = capsys.readouterr()
    output = captured.out.strip()

    # Parse JSON log
    log_data = json.loads(output)

    # Verify structured fields
    assert "timestamp" in log_data
    assert "level" in log_data
    assert "logger" in log_data
    assert "message" in log_data
    assert log_data["logger"] == logger_name
    assert log_data["message"] == message
