# Task 4.3 Implementation: 實作可配置的排程時間

## Summary

Successfully implemented configurable scheduler timing with environment variable support, CRON expression validation, and comprehensive testing.

## Changes Made

### 1. Configuration (`app/core/config.py`)

Added two new configuration fields to the `Settings` class:

- `scheduler_cron`: CRON expression for schedule (default: `"0 */6 * * *"` - every 6 hours)
- `scheduler_timezone`: Optional timezone override (defaults to `None`, falls back to `timezone`)

### 2. Scheduler (`app/tasks/scheduler.py`)

Enhanced `setup_scheduler()` function with:

- **Environment Variable Reading**: Reads `SCHEDULER_CRON` and `SCHEDULER_TIMEZONE` from environment
- **CRON Validation**: Validates CRON expression using `CronTrigger.from_crontab()`
- **Error Handling**: Raises `ValueError` with descriptive message for invalid CRON expressions
- **Startup Logging**: Logs configured schedule, timezone, and job name on successful initialization
- **Timezone Fallback**: Uses `scheduler_timezone` if set, otherwise falls back to general `timezone`

### 3. Environment Variables (`.env.example`)

Added documentation and examples for:

```bash
# CRON expression for background job schedule
SCHEDULER_CRON=0 */6 * * *

# Timezone for scheduler (optional)
# SCHEDULER_TIMEZONE=Asia/Taipei
```

Includes helpful comments with CRON format examples.

### 4. Tests

Created comprehensive test coverage:

#### Unit Tests (`tests/test_scheduler_config.py`)

- ✓ Default CRON expression usage
- ✓ Custom CRON expression acceptance
- ✓ Custom timezone configuration
- ✓ Timezone fallback behavior
- ✓ Invalid CRON expression rejection
- ✓ Invalid field values rejection
- ✓ Startup logging verification
- ✓ Various valid CRON expressions
- ✓ CronTrigger validation
- ✓ Settings defaults
- ✓ Environment variable reading

#### Integration Tests (`tests/test_scheduler_integration.py`)

- ✓ Initialization with environment variables
- ✓ Fail-fast on invalid CRON
- ✓ Default values when env vars not set

#### Manual Test (`tests/manual_scheduler_test.py`)

- Demonstrates default configuration
- Demonstrates custom configuration
- Demonstrates invalid configuration handling

**Total Test Coverage**: 17 automated tests + 3 manual tests = 20 tests

## Requirements Validated

✓ **Requirement 6.1**: Reads schedule configuration from environment variables
✓ **Requirement 6.2**: Supports CRON expression format
✓ **Requirement 6.3**: Defaults to running every 6 hours when not configured
✓ **Requirement 6.4**: Logs configured schedule on startup
✓ **Requirement 6.5**: Raises configuration error for invalid CRON expressions
✓ **Requirement 6.6**: Supports multiple timezone configurations

## Example Usage

### Default Configuration

```bash
# Uses default: every 6 hours in Asia/Taipei timezone
python main.py
```

### Custom Schedule

```bash
# Daily at midnight UTC
export SCHEDULER_CRON="0 0 * * *"
export SCHEDULER_TIMEZONE="UTC"
python main.py
```

### Every 30 Minutes

```bash
# Every 30 minutes in New York timezone
export SCHEDULER_CRON="*/30 * * * *"
export SCHEDULER_TIMEZONE="America/New_York"
python main.py
```

## Validation

All tests pass:

```bash
$ python3 -m pytest tests/test_scheduler_config.py tests/test_scheduler_integration.py -v
================================ 17 passed in 0.16s =================================

$ python3 tests/manual_scheduler_test.py
============================================================
All tests passed! ✓
============================================================
```

## Error Handling

Invalid CRON expressions are caught at startup:

```
ValueError: Invalid CRON expression 'invalid_cron': Wrong number of fields; got 1, expected 5
```

This ensures fail-fast behavior and prevents runtime issues.

## Logging Output

On successful initialization:

```
INFO: Scheduler configured successfully: CRON='0 */6 * * *', Timezone='Asia/Taipei', Job='background_fetch_job'
```

## Backward Compatibility

- Default values maintain existing behavior (every 6 hours)
- No breaking changes to existing code
- Environment variables are optional
- Existing tests continue to pass
