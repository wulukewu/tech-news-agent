# Preference Synchronization Implementation

## Overview

This document describes the implementation of Task 8.1: Preference Synchronization Mechanism. The implementation provides an event-driven system that ensures immediate synchronization between web and Discord interfaces and triggers scheduler updates when preferences change.

## Architecture

### Components

1. **PreferenceEventSystem** (`app/services/preference_event_system.py`)
   - Provides publish/subscribe mechanism for preference change events
   - Handles both async and sync callbacks
   - Gracefully handles callback exceptions

2. **PreferenceSynchronizationService** (`app/services/preference_synchronization_service.py`)
   - Subscribes to preference change events
   - Triggers scheduler updates when scheduling-related fields change
   - Handles both reschedule and cancel operations

3. **Enhanced PreferenceService** (`app/services/preference_service.py`)
   - Modified to emit events when preferences change
   - Tracks source of changes (web, discord, system)
   - Maintains backward compatibility

### Event Flow

```
User Updates Preferences (Web/Discord)
           ↓
    PreferenceService.update_preferences()
           ↓
    Database Update + Event Emission
           ↓
    PreferenceEventSystem.publish()
           ↓
    PreferenceSynchronizationService._handle_preference_change()
           ↓
    DynamicScheduler.reschedule_user_notification()
```

## Key Features

### 1. Event System for Preference Changes

- **Event Type**: `preference_changed`
- **Event Data**: `PreferenceChangeEvent` containing:
  - `user_id`: UUID of the user
  - `old_preferences`: Previous preferences (None for new users)
  - `new_preferences`: Updated preferences
  - `changed_fields`: List of fields that changed
  - `source`: Source of change (web, discord, system)
  - `timestamp`: When the event occurred

### 2. Immediate Synchronization

- Events are published immediately after database updates
- All subscribers receive events concurrently
- No polling or delayed synchronization

### 3. Scheduler Updates

The synchronization service automatically:

- **Reschedules** notifications when scheduling fields change (frequency, time, timezone, dm_enabled, email_enabled)
- **Cancels** notifications when frequency is set to "disabled"
- **Skips** updates for non-scheduling field changes

### 4. Source Tracking

All preference updates now include a `source` parameter:

- `"web"`: Updates from web interface
- `"discord"`: Updates from Discord commands
- `"system"`: System-generated updates (e.g., default preferences)

## Implementation Details

### Modified API Endpoints

**Web Interface** (`app/api/notifications.py`):

```python
# Before
updated_preferences = await preference_service.update_preferences(user_id, updates)

# After
updated_preferences = await preference_service.update_preferences(user_id, updates, source="web")
```

**Discord Commands** (`app/bot/cogs/notification_settings.py`):

```python
# Before
updated_preferences = await preference_service.update_preferences(user_id, updates)

# After
updated_preferences = await preference_service.update_preferences(user_id, updates, source="discord")
```

### Removed Manual Scheduler Calls

Previously, both web and Discord interfaces manually called the scheduler:

```python
# Removed from both interfaces
if dynamic_scheduler:
    await dynamic_scheduler.reschedule_user_notification(user_id, updated_preferences)
```

Now the event system handles all scheduler updates automatically.

### Application Initialization

The synchronization service is initialized in `app/main.py`:

```python
# Initialize preference synchronization service
try:
    from app.services.dynamic_scheduler import get_dynamic_scheduler
    dynamic_scheduler = get_dynamic_scheduler()
    initialize_preference_sync_service(dynamic_scheduler)
    logger.info("Preference synchronization service initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize preference synchronization service: {e}", exc_info=True)
```

## Benefits

### 1. Consistency

- All preference changes go through the same event system
- No risk of forgetting to update scheduler in new interfaces
- Consistent behavior across all interfaces

### 2. Maintainability

- Centralized synchronization logic
- Easy to add new subscribers (e.g., logging, analytics)
- Clear separation of concerns

### 3. Reliability

- Graceful error handling in event callbacks
- No blocking operations in event publishing
- Continues working even if scheduler is unavailable

### 4. Extensibility

- Easy to add new event types
- Simple to add new synchronization behaviors
- Supports both sync and async callbacks

## Testing

### Unit Tests

- `tests/unit/test_preference_synchronization.py`
- Tests event system functionality
- Tests synchronization service behavior
- Tests error handling

### Integration Tests

- `tests/integration/test_preference_synchronization_integration.py`
- Tests end-to-end synchronization flow
- Tests different preference change scenarios
- Tests source tracking

## Requirements Fulfilled

This implementation fulfills the following requirements:

- **8.1**: ✅ Event system for preference changes implemented
- **8.2**: ✅ Immediate synchronization between web and Discord interfaces
- **8.3**: ✅ Scheduler updates triggered on preference changes
- **8.4**: ✅ Consistent display of settings across all interfaces

## Usage Examples

### Adding a New Event Subscriber

```python
from app.services.preference_event_system import get_preference_event_system

async def log_preference_changes(event):
    logger.info(f"User {event.user_id} changed {event.changed_fields} via {event.source}")

event_system = get_preference_event_system()
event_system.subscribe("preference_changed", log_preference_changes)
```

### Manual Synchronization Trigger

```python
from app.services.preference_synchronization_service import get_preference_sync_service

sync_service = get_preference_sync_service()
await sync_service.trigger_manual_sync(user_id)
```

## Future Enhancements

1. **Event Persistence**: Store events for audit trails
2. **Event Replay**: Replay events for debugging or recovery
3. **Cross-Service Events**: Extend to other services beyond preferences
4. **Event Filtering**: Allow subscribers to filter events by criteria
5. **Metrics Collection**: Track event publishing and processing metrics
