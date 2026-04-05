"""
Property-based tests for Scheduler CRON expression validation
Task 4.10: 撰寫 Scheduler 的屬性測試

Property 9: CRON Expression Validation
Validates Requirements: 6.2, 6.5

This test verifies that:
- Invalid CRON expressions raise configuration errors on startup
- Valid CRON expressions are accepted without error
- The scheduler validates CRON expressions before starting
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from unittest.mock import patch
from apscheduler.triggers.cron import CronTrigger

from app.tasks.scheduler import setup_scheduler, scheduler


# Hypothesis strategies for generating CRON expressions

def valid_cron_strategy():
    """
    Generate valid CRON expressions.
    
    CRON format: minute hour day month day_of_week
    - minute: 0-59
    - hour: 0-23
    - day: 1-31
    - month: 1-12
    - day_of_week: 0-6 (0=Sunday)
    
    Special characters: * (any), */n (every n), n-m (range), n,m (list)
    """
    # Common valid patterns
    valid_patterns = [
        # Every N hours
        "0 */6 * * *",      # Every 6 hours
        "0 */12 * * *",     # Every 12 hours
        "0 */1 * * *",      # Every hour
        "0 */2 * * *",      # Every 2 hours
        "0 */3 * * *",      # Every 3 hours
        "0 */4 * * *",      # Every 4 hours
        
        # Daily at specific times
        "0 0 * * *",        # Daily at midnight
        "0 9 * * *",        # Daily at 9am
        "0 12 * * *",       # Daily at noon
        "0 18 * * *",       # Daily at 6pm
        "30 14 * * *",      # Daily at 2:30pm
        
        # Every N minutes
        "*/30 * * * *",     # Every 30 minutes
        "*/15 * * * *",     # Every 15 minutes
        "*/5 * * * *",      # Every 5 minutes
        "*/10 * * * *",     # Every 10 minutes
        
        # Weekly patterns
        "0 9 * * 1",        # Every Monday at 9am
        "0 0 * * 0",        # Every Sunday at midnight
        "0 12 * * 1-5",     # Weekdays at noon
        "0 18 * * 5",       # Every Friday at 6pm
        
        # Monthly patterns
        "0 0 1 * *",        # First day of every month
        "0 0 15 * *",       # 15th of every month
        "0 9 1 1 *",        # January 1st at 9am
        
        # Complex patterns
        "0 0,12 * * *",     # Twice daily (midnight and noon)
        "0 9-17 * * 1-5",   # Every hour 9am-5pm on weekdays
        "*/20 * * * *",     # Every 20 minutes
    ]
    
    return st.sampled_from(valid_patterns)


def invalid_cron_strategy():
    """
    Generate invalid CRON expressions that should raise errors.
    
    Invalid patterns include:
    - Out of range values (minute > 59, hour > 23, etc.)
    - Wrong number of fields
    - Invalid syntax
    - Empty strings
    - Non-CRON strings
    """
    invalid_patterns = [
        # Out of range values
        "60 * * * *",       # Invalid minute (60)
        "* 24 * * *",       # Invalid hour (24)
        "* * 32 * *",       # Invalid day (32)
        "* * * 13 *",       # Invalid month (13)
        "* * * * 7",        # Invalid day_of_week (7)
        "100 * * * *",      # Way out of range minute
        "* 100 * * *",      # Way out of range hour
        
        # Wrong number of fields
        "* * * *",          # Too few fields (4 instead of 5)
        "* * * * * *",      # Too many fields (6 instead of 5)
        "*",                # Only one field
        "* *",              # Only two fields
        "* * *",            # Only three fields
        
        # Invalid syntax
        "invalid",          # Not a CRON expression
        "not a cron",       # Plain text
        "*/0 * * * *",      # Division by zero
        "a b c d e",        # Letters instead of numbers
        "** * * * *",       # Double asterisk
        "* * * * * * *",    # Too many fields
        
        # Empty and whitespace
        "",                 # Empty string
        "     ",            # Only whitespace
        
        # Invalid ranges
        "10-5 * * * *",     # Backwards range
        "* 20-10 * * *",    # Backwards range
        
        # Invalid step values
        "*/60 * * * *",     # Step larger than range
        "* */25 * * *",     # Step larger than range
        
        # Special invalid cases
        "? * * * *",        # Question mark (not standard in all implementations)
        "L * * * *",        # L (last) - not standard in all implementations
        "#3 * * * *",       # Hash - not standard in all implementations
    ]
    
    return st.sampled_from(invalid_patterns)


# Feature: background-scheduler-ai-pipeline, Property 9: CRON Expression Validation
@settings(
    max_examples=20,  # Use 20 iterations as specified in task details
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None  # Disable deadline for scheduler operations
)
@given(cron_expression=valid_cron_strategy())
def test_property_9_valid_cron_expressions_accepted(cron_expression):
    """
    Property 9: CRON Expression Validation (Valid Expressions)
    
    For any valid CRON expression, the scheduler should accept it without error.
    The setup_scheduler function should successfully configure the scheduler
    and add the background job.
    
    Validates: Requirements 6.2
    """
    # Arrange: Mock settings with valid CRON expression
    with patch('app.tasks.scheduler.settings') as mock_settings:
        mock_settings.scheduler_cron = cron_expression
        mock_settings.scheduler_timezone = None
        mock_settings.timezone = "UTC"
        
        # Clear any existing jobs
        scheduler.remove_all_jobs()
        
        # Act: Setup scheduler should not raise any exception
        try:
            setup_scheduler()
            setup_succeeded = True
            error_message = None
        except Exception as e:
            setup_succeeded = False
            error_message = str(e)
        
        # Assert: Valid CRON expression should be accepted
        assert setup_succeeded, \
            f"Valid CRON expression '{cron_expression}' was rejected with error: {error_message}"
        
        # Verify job was added successfully
        jobs = scheduler.get_jobs()
        assert len(jobs) >= 1, \
            f"No jobs were added for valid CRON expression '{cron_expression}'"
        
        # Verify the background_fetch job exists
        job = scheduler.get_job('background_fetch')
        assert job is not None, \
            f"background_fetch job was not created for valid CRON expression '{cron_expression}'"
        
        assert job.name == 'Background Article Fetch and Analysis', \
            f"Job name mismatch for CRON expression '{cron_expression}'"


# Feature: background-scheduler-ai-pipeline, Property 9: CRON Expression Validation
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None
)
@given(cron_expression=invalid_cron_strategy())
def test_property_9_invalid_cron_expressions_rejected(cron_expression):
    """
    Property 9: CRON Expression Validation (Invalid Expressions)
    
    For any invalid CRON expression, the scheduler should raise a configuration
    error on startup. The setup_scheduler function should fail with a ValueError
    that includes the invalid CRON expression in the error message.
    
    Validates: Requirements 6.5
    """
    # Arrange: Mock settings with invalid CRON expression
    with patch('app.tasks.scheduler.settings') as mock_settings:
        mock_settings.scheduler_cron = cron_expression
        mock_settings.scheduler_timezone = None
        mock_settings.timezone = "UTC"
        
        # Clear any existing jobs
        scheduler.remove_all_jobs()
        
        # Act & Assert: Setup scheduler should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            setup_scheduler()
        
        # Verify error message contains relevant information
        error_message = str(exc_info.value)
        
        assert "Invalid CRON expression" in error_message, \
            f"Error message should mention 'Invalid CRON expression', got: {error_message}"
        
        assert cron_expression in error_message, \
            f"Error message should include the invalid CRON expression '{cron_expression}', got: {error_message}"


# Feature: background-scheduler-ai-pipeline, Property 9: CRON Expression Validation
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None
)
@given(
    cron_expression=valid_cron_strategy(),
    timezone=st.sampled_from([
        "UTC",
        "Asia/Taipei",
        "America/New_York",
        "Europe/London",
        "Asia/Tokyo",
        "Australia/Sydney",
    ])
)
def test_property_9_valid_cron_with_various_timezones(cron_expression, timezone):
    """
    Property 9: CRON Expression Validation (With Timezones)
    
    For any valid CRON expression and any valid timezone, the scheduler
    should accept the configuration without error. This tests that CRON
    validation works correctly across different timezone configurations.
    
    Validates: Requirements 6.2, 6.6
    """
    # Arrange
    with patch('app.tasks.scheduler.settings') as mock_settings:
        mock_settings.scheduler_cron = cron_expression
        mock_settings.scheduler_timezone = timezone
        mock_settings.timezone = "UTC"
        
        # Clear any existing jobs
        scheduler.remove_all_jobs()
        
        # Act: Setup scheduler should not raise
        try:
            setup_scheduler()
            setup_succeeded = True
            error_message = None
        except Exception as e:
            setup_succeeded = False
            error_message = str(e)
        
        # Assert
        assert setup_succeeded, \
            f"Valid CRON '{cron_expression}' with timezone '{timezone}' was rejected: {error_message}"
        
        # Verify job was added
        job = scheduler.get_job('background_fetch')
        assert job is not None, \
            f"Job not created for CRON '{cron_expression}' with timezone '{timezone}'"


# Feature: background-scheduler-ai-pipeline, Property 9: CRON Expression Validation
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None
)
@given(cron_expression=valid_cron_strategy())
def test_property_9_cron_trigger_creation(cron_expression):
    """
    Property 9: CRON Expression Validation (CronTrigger Creation)
    
    For any valid CRON expression, creating a CronTrigger should succeed.
    This tests the underlying validation mechanism used by the scheduler.
    
    Validates: Requirements 6.2
    """
    # Act: Create CronTrigger should not raise
    try:
        trigger = CronTrigger.from_crontab(cron_expression, timezone="UTC")
        creation_succeeded = True
        error_message = None
    except Exception as e:
        creation_succeeded = False
        error_message = str(e)
        trigger = None
    
    # Assert
    assert creation_succeeded, \
        f"CronTrigger creation failed for valid CRON '{cron_expression}': {error_message}"
    
    assert trigger is not None, \
        f"CronTrigger should not be None for valid CRON '{cron_expression}'"


# Feature: background-scheduler-ai-pipeline, Property 9: CRON Expression Validation
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None
)
@given(cron_expression=invalid_cron_strategy())
def test_property_9_cron_trigger_rejection(cron_expression):
    """
    Property 9: CRON Expression Validation (CronTrigger Rejection)
    
    For any invalid CRON expression, creating a CronTrigger should raise
    an exception (ValueError or TypeError). This tests the underlying
    validation mechanism.
    
    Validates: Requirements 6.5
    """
    # Act & Assert: CronTrigger creation should raise
    with pytest.raises((ValueError, TypeError)) as exc_info:
        CronTrigger.from_crontab(cron_expression, timezone="UTC")
    
    # Verify an exception was raised
    assert exc_info.value is not None, \
        f"CronTrigger should reject invalid CRON '{cron_expression}'"


# Feature: background-scheduler-ai-pipeline, Property 9: CRON Expression Validation
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None
)
@given(
    cron_expression=st.one_of(valid_cron_strategy(), invalid_cron_strategy()),
    is_valid=st.booleans()
)
def test_property_9_validation_consistency(cron_expression, is_valid):
    """
    Property 9: CRON Expression Validation (Consistency)
    
    The validation behavior should be consistent: if CronTrigger.from_crontab
    accepts an expression, setup_scheduler should also accept it. If
    CronTrigger rejects it, setup_scheduler should also reject it.
    
    Validates: Requirements 6.2, 6.5
    """
    # First, check if CronTrigger accepts the expression
    try:
        CronTrigger.from_crontab(cron_expression, timezone="UTC")
        cron_trigger_accepts = True
    except (ValueError, TypeError):
        cron_trigger_accepts = False
    
    # Now check if setup_scheduler accepts it
    with patch('app.tasks.scheduler.settings') as mock_settings:
        mock_settings.scheduler_cron = cron_expression
        mock_settings.scheduler_timezone = None
        mock_settings.timezone = "UTC"
        
        scheduler.remove_all_jobs()
        
        try:
            setup_scheduler()
            setup_scheduler_accepts = True
        except ValueError:
            setup_scheduler_accepts = False
    
    # Assert: Both should have the same behavior
    assert cron_trigger_accepts == setup_scheduler_accepts, \
        f"Validation inconsistency for CRON '{cron_expression}': " \
        f"CronTrigger accepts={cron_trigger_accepts}, " \
        f"setup_scheduler accepts={setup_scheduler_accepts}"


# Feature: background-scheduler-ai-pipeline, Property 9: CRON Expression Validation
@settings(
    max_examples=20,  # Use 20 iterations as specified
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.filter_too_much],
    deadline=None
)
@given(cron_expression=valid_cron_strategy())
def test_property_9_scheduler_accepts_and_creates_job(cron_expression):
    """
    Property 9: CRON Expression Validation (Job Creation)
    
    For any valid CRON expression, the scheduler should successfully create
    a job with the correct ID and name. This verifies that valid CRON
    expressions result in properly configured scheduler jobs.
    
    Validates: Requirements 6.2
    """
    # Arrange: Mock settings with valid CRON expression
    with patch('app.tasks.scheduler.settings') as mock_settings:
        mock_settings.scheduler_cron = cron_expression
        mock_settings.scheduler_timezone = None
        mock_settings.timezone = "UTC"
        
        # Clear any existing jobs to ensure clean state
        scheduler.remove_all_jobs()
        
        # Act: Setup scheduler
        setup_scheduler()
        
        # Assert: Job should be created with correct properties
        job = scheduler.get_job('background_fetch')
        
        assert job is not None, \
            f"Job should be created for valid CRON '{cron_expression}'"
        
        assert job.id == 'background_fetch', \
            f"Job ID should be 'background_fetch', got '{job.id}'"
        
        assert job.name == 'Background Article Fetch and Analysis', \
            f"Job name mismatch for CRON '{cron_expression}'"
        
        # Verify the job has a trigger configured
        assert job.trigger is not None, \
            f"Job should have a trigger configured for CRON '{cron_expression}'"
