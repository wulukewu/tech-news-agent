# AnalyticsService Implementation Documentation

## Overview

This document describes the implementation of the AnalyticsService for the new-user-onboarding-system feature. The service provides comprehensive analytics tracking and reporting for user onboarding events.

## Files Created

1. **Service**: `backend/app/services/analytics_service.py`
2. **Schemas**: `backend/app/schemas/analytics.py`
3. **Tests**: `backend/tests/test_analytics_service.py`

## Requirements Validated

### Requirement 14.1: Log onboarding events to analytics table

✅ Implemented in `log_event()` method

- Logs all event types to analytics_events table
- Supports all required event types

### Requirement 14.3: Record timestamp, user_id, event_type, and event_data

✅ Implemented in `log_event()` method

- Records all required fields
- Automatically adds timestamp
- Stores event_data as JSONB

### Requirement 14.4: When user skips, log the step where they skipped

✅ Supported through event_data parameter

- event_data can include 'step' field
- Example: `{'step': 'recommendations', 'reason': 'user_clicked_skip'}`

### Requirement 14.5: Track time spent on each onboarding step

✅ Implemented in `get_average_time_per_step()` method

- Calculates average time per step
- Extracts time_spent_seconds from event_data
- Returns AverageTimePerStepResponse

### Requirement 14.6: Provide dashboard view of completion rates

✅ Implemented in multiple methods:

- `get_onboarding_completion_rate()` - Overall completion rate
- `get_drop_off_rates()` - Drop-off at each step
- `get_average_time_per_step()` - Time analysis

## Service Methods

### 1. log_event()

**Purpose**: Log analytics events to the database

**Signature**:

```python
async def log_event(
    self,
    user_id: UUID,
    event_type: str,
    event_data: Optional[Dict[str, Any]] = None
) -> None
```

**Supported Event Types**:

- `onboarding_started`
- `step_completed`
- `onboarding_skipped`
- `onboarding_finished`
- `tooltip_shown`
- `tooltip_skipped`
- `feed_subscribed_from_onboarding`

**Example Usage**:

```python
# Log onboarding started
await analytics_service.log_event(
    user_id=user_id,
    event_type='onboarding_started',
    event_data={'source': 'web'}
)

# Log step completed with time
await analytics_service.log_event(
    user_id=user_id,
    event_type='step_completed',
    event_data={
        'step': 'welcome',
        'time_spent_seconds': 45
    }
)

# Log onboarding skipped with step info
await analytics_service.log_event(
    user_id=user_id,
    event_type='onboarding_skipped',
    event_data={
        'step': 'recommendations',
        'reason': 'user_clicked_skip'
    }
)
```

### 2. get_onboarding_completion_rate()

**Purpose**: Calculate completion rate for a time period

**Signature**:

```python
async def get_onboarding_completion_rate(
    self,
    start_date: datetime,
    end_date: datetime
) -> OnboardingCompletionRateResponse
```

**Returns**:

```python
OnboardingCompletionRateResponse(
    completion_rate=75.5,  # Percentage
    total_users=100,
    completed_users=75,
    skipped_users=15,
    start_date=datetime(...),
    end_date=datetime(...)
)
```

**Example Usage**:

```python
from datetime import datetime, timezone

start = datetime(2024, 1, 1, tzinfo=timezone.utc)
end = datetime(2024, 1, 31, tzinfo=timezone.utc)

result = await analytics_service.get_onboarding_completion_rate(start, end)
print(f"Completion rate: {result.completion_rate}%")
print(f"Completed: {result.completed_users}/{result.total_users}")
```

### 3. get_drop_off_rates()

**Purpose**: Calculate drop-off rates at each onboarding step

**Signature**:

```python
async def get_drop_off_rates(self) -> DropOffRatesResponse
```

**Returns**:

```python
DropOffRatesResponse(
    drop_off_by_step={
        'welcome': 10.5,
        'recommendations': 15.2,
        'complete': 5.0
    },
    total_started=100
)
```

**Example Usage**:

```python
result = await analytics_service.get_drop_off_rates()

for step, rate in result.drop_off_by_step.items():
    print(f"{step}: {rate}% drop-off")
```

### 4. get_average_time_per_step()

**Purpose**: Calculate average time spent on each step

**Signature**:

```python
async def get_average_time_per_step(self) -> AverageTimePerStepResponse
```

**Returns**:

```python
AverageTimePerStepResponse(
    average_time_by_step={
        'welcome': 45.5,
        'recommendations': 120.3,
        'complete': 30.0
    },
    total_completions=75
)
```

**Example Usage**:

```python
result = await analytics_service.get_average_time_per_step()

for step, avg_time in result.average_time_by_step.items():
    print(f"{step}: {avg_time:.1f} seconds average")
```

## Pydantic Schemas

### LogAnalyticsEventRequest

Request model for logging events via API

### AnalyticsEvent

Complete event record model

### OnboardingCompletionRateResponse

Response for completion rate queries

### DropOffRatesResponse

Response for drop-off rate analysis

### AverageTimePerStepResponse

Response for time analysis

## Error Handling

All methods raise `AnalyticsServiceError` on failure:

- Database connection errors
- Query execution errors
- Data validation errors

Example:

```python
try:
    await analytics_service.log_event(user_id, 'onboarding_started')
except AnalyticsServiceError as e:
    logger.error(f"Failed to log event: {e}")
    # Handle error gracefully
```

## Testing

### Test Coverage: 18 Unit Tests

**Test Classes**:

1. `TestLogEvent` (6 tests)
   - Success cases
   - Empty data handling
   - All event types
   - Complex event data
   - Error handling

2. `TestGetOnboardingCompletionRate` (3 tests)
   - With data
   - No users
   - Database errors

3. `TestGetDropOffRates` (3 tests)
   - With data
   - No data
   - Database errors

4. `TestGetAverageTimePerStep` (4 tests)
   - With data
   - No data
   - Missing time data
   - Database errors

5. `TestEdgeCases` (2 tests)
   - Complex event data
   - 100% completion rate

**Run Tests**:

```bash
python3 -m pytest backend/tests/test_analytics_service.py -v
```

**Test Results**: ✅ All 18 tests passing

## Database Schema

The service uses the `analytics_events` table:

```sql
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_data JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**Indexes**:

- `idx_analytics_events_user_id` - Query by user
- `idx_analytics_events_event_type` - Query by event type
- `idx_analytics_events_created_at` - Time-based queries
- `idx_analytics_events_event_data` - JSONB queries (GIN index)

## Integration with Other Services

### OnboardingService Integration

```python
from app.services.analytics_service import AnalyticsService
from app.services.onboarding_service import OnboardingService

# Log when onboarding starts
await analytics_service.log_event(
    user_id=user_id,
    event_type='onboarding_started',
    event_data={'source': 'web'}
)

# Update onboarding progress
await onboarding_service.update_onboarding_progress(
    user_id=user_id,
    step='welcome',
    completed=True
)

# Log step completion
await analytics_service.log_event(
    user_id=user_id,
    event_type='step_completed',
    event_data={
        'step': 'welcome',
        'time_spent_seconds': 45
    }
)
```

### API Endpoint Integration

```python
from fastapi import APIRouter, Depends
from app.services.analytics_service import AnalyticsService

router = APIRouter()

@router.post("/api/analytics/event")
async def log_analytics_event(
    request: LogAnalyticsEventRequest,
    user_id: UUID = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    await analytics_service.log_event(
        user_id=user_id,
        event_type=request.event_type,
        event_data=request.event_data
    )
    return {"status": "success"}
```

## Performance Considerations

### Logging Performance

- Asynchronous operations
- Non-blocking database inserts
- Minimal validation overhead

### Query Performance

- Indexed queries for fast retrieval
- Efficient aggregation using database features
- Date range filtering for large datasets

### Optimization Tips

1. Use date ranges to limit query scope
2. Consider caching completion rates for dashboards
3. Batch event logging when possible
4. Monitor query performance with EXPLAIN ANALYZE

## Future Enhancements

1. **Real-time Analytics**
   - WebSocket updates for live dashboards
   - Streaming analytics processing

2. **Advanced Metrics**
   - Cohort analysis
   - Funnel visualization
   - Predictive churn modeling

3. **Export Capabilities**
   - CSV export for reports
   - Integration with BI tools
   - Automated email reports

4. **A/B Testing Support**
   - Variant tracking
   - Statistical significance testing
   - Automated winner selection

## Conclusion

The AnalyticsService provides a robust foundation for tracking and analyzing user onboarding behavior. With comprehensive event logging, completion rate tracking, drop-off analysis, and time tracking, it enables data-driven optimization of the onboarding experience.

All requirements (14.1, 14.3, 14.4, 14.5, 14.6) have been successfully implemented and validated through comprehensive unit testing.
