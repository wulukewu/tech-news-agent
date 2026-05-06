# OnboardingService Documentation

## Overview

The `OnboardingService` manages user onboarding progress and state for the new user onboarding system. It provides methods to track onboarding steps, mark completion or skip status, and reset the onboarding flow.

## Requirements

This service implements the following requirements:

- **1.4**: Track onboarding progress in user_preferences table
- **1.5**: Mark onboarding as completed with timestamp
- **1.6**: Allow users to skip onboarding
- **10.3**: Update user preferences for onboarding state
- **10.6**: Reset onboarding state

## Installation

The service requires:

- Python 3.11+
- Supabase client
- Pydantic models from `app.schemas.onboarding`

## Usage

### Initialize the Service

```python
from supabase import create_client
from app.services.onboarding_service import OnboardingService

# Create Supabase client
supabase_client = create_client(supabase_url, supabase_key)

# Initialize service
onboarding_service = OnboardingService(supabase_client)
```

### Get Onboarding Status

Retrieve the current onboarding status for a user. If the user doesn't have preferences, creates default record.

```python
from uuid import UUID

user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
status = await onboarding_service.get_onboarding_status(user_id)

print(f"Completed: {status.onboarding_completed}")
print(f"Current Step: {status.onboarding_step}")
print(f"Skipped: {status.onboarding_skipped}")
print(f"Tooltip Tour Completed: {status.tooltip_tour_completed}")
```

### Update Onboarding Progress

Update the user's current step in the onboarding flow.

```python
# User completes the welcome step
await onboarding_service.update_onboarding_progress(
    user_id=user_id,
    step='welcome',
    completed=True
)

# User moves to recommendations step
await onboarding_service.update_onboarding_progress(
    user_id=user_id,
    step='recommendations',
    completed=True
)
```

### Mark Onboarding as Completed

Mark the entire onboarding flow as completed.

```python
await onboarding_service.mark_onboarding_completed(user_id)
```

This sets:

- `onboarding_completed` = True
- `onboarding_completed_at` = current timestamp
- `onboarding_step` = 'complete'

### Mark Onboarding as Skipped

Allow users to skip the onboarding flow.

```python
await onboarding_service.mark_onboarding_skipped(user_id)
```

This sets `onboarding_skipped` = True, preventing the onboarding modal from showing again.

### Reset Onboarding

Reset the onboarding state to allow users to go through the flow again.

```python
await onboarding_service.reset_onboarding(user_id)
```

This clears:

- `onboarding_completed` → False
- `onboarding_step` → None
- `onboarding_skipped` → False
- `onboarding_started_at` → None
- `onboarding_completed_at` → None

## Data Models

### OnboardingStatus

Response model for onboarding status:

```python
class OnboardingStatus(BaseModel):
    onboarding_completed: bool
    onboarding_step: Optional[str]
    onboarding_skipped: bool
    tooltip_tour_completed: bool
```

### UserPreferences

Complete user preferences model:

```python
class UserPreferences(BaseModel):
    id: UUID
    user_id: UUID
    onboarding_completed: bool
    onboarding_step: Optional[str]
    onboarding_skipped: bool
    onboarding_started_at: Optional[datetime]
    onboarding_completed_at: Optional[datetime]
    tooltip_tour_completed: bool
    tooltip_tour_skipped: bool
    preferred_language: str
    created_at: datetime
    updated_at: datetime
```

## Error Handling

All methods raise `OnboardingServiceError` on failure:

```python
from app.services.onboarding_service import OnboardingServiceError

try:
    status = await onboarding_service.get_onboarding_status(user_id)
except OnboardingServiceError as e:
    logger.error(f"Failed to get onboarding status: {e}")
    # Handle error appropriately
```

## Database Schema

The service interacts with the `user_preferences` table:

```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE NOT NULL,

    -- Onboarding progress
    onboarding_completed BOOLEAN DEFAULT false,
    onboarding_step TEXT,
    onboarding_skipped BOOLEAN DEFAULT false,
    onboarding_started_at TIMESTAMPTZ,
    onboarding_completed_at TIMESTAMPTZ,

    -- Tooltip tour
    tooltip_tour_completed BOOLEAN DEFAULT false,
    tooltip_tour_skipped BOOLEAN DEFAULT false,

    -- Language preference
    preferred_language TEXT DEFAULT 'zh-TW',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

## Testing

The service includes comprehensive unit and integration tests:

```bash
# Run unit tests
pytest backend/tests/test_onboarding_service.py -v

# Run integration tests
pytest backend/tests/test_onboarding_service_integration.py -v

# Run all onboarding tests
pytest backend/tests/test_onboarding_service*.py -v
```

## Example: Complete Onboarding Flow

```python
from uuid import UUID
from app.services.onboarding_service import OnboardingService

async def complete_onboarding_flow(user_id: UUID, onboarding_service: OnboardingService):
    """Example of a complete onboarding flow"""

    # 1. Check initial status
    status = await onboarding_service.get_onboarding_status(user_id)
    if status.onboarding_completed or status.onboarding_skipped:
        print("User has already completed or skipped onboarding")
        return

    # 2. User views welcome screen
    await onboarding_service.update_onboarding_progress(user_id, 'welcome', True)

    # 3. User selects recommended feeds
    await onboarding_service.update_onboarding_progress(user_id, 'recommendations', True)

    # 4. User completes onboarding
    await onboarding_service.mark_onboarding_completed(user_id)

    print("Onboarding completed successfully!")

async def skip_onboarding_flow(user_id: UUID, onboarding_service: OnboardingService):
    """Example of skipping onboarding"""

    # User clicks "稍後再說" button
    await onboarding_service.mark_onboarding_skipped(user_id)

    print("Onboarding skipped")
```

## Next Steps

After implementing the OnboardingService, the next tasks are:

1. **Task 2.2-2.6**: Write property-based tests for OnboardingService
2. **Task 3.1**: Implement RecommendationService
3. **Task 4.1**: Implement AnalyticsService
4. **Task 5.1**: Create API endpoints for onboarding

## Related Files

- Service: `backend/app/services/onboarding_service.py`
- Schemas: `backend/app/schemas/onboarding.py`
- Unit Tests: `backend/tests/test_onboarding_service.py`
- Integration Tests: `backend/tests/test_onboarding_service_integration.py`
- Migration: `scripts/migrations/002_create_user_preferences_table.sql`
