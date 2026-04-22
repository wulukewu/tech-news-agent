# Component Wiring Implementation

## Overview

This document describes the implementation of Task 9.1: Wire all components together. The implementation provides proper dependency injection, error propagation, and service coordination across all notification system components.

## Architecture

### Central Integration Service

The `NotificationSystemIntegration` class serves as the central hub that wires all components together:

```
NotificationSystemIntegration
├── PreferenceService (user preference management)
├── DynamicScheduler (notification scheduling)
├── NotificationService (multi-channel delivery)
├── LockManager (atomic locking)
└── PreferenceEventSystem (synchronization)
```

### Component Dependencies

**Dependency Injection Flow:**

1. **SupabaseService** → Database connectivity
2. **UserNotificationPreferencesRepository** → Data access layer
3. **PreferenceService** → Business logic for preferences
4. **LockManager** → Atomic notification locking
5. **NotificationService** → Multi-channel delivery (uses LockManager)
6. **DynamicScheduler** → Job scheduling
7. **PreferenceEventSystem** → Cross-component synchronization

### Service Initialization

**Application Startup Sequence (main.py):**

1. Validate configuration
2. Start APScheduler
3. Initialize notification system integration:
   - Get DynamicScheduler instance
   - Get SupabaseService instance
   - Initialize NotificationSystemIntegration with all dependencies
   - Initialize monitoring service
   - Initialize preference synchronization service
   - Run system initialization (migrate users, start scheduling)

## Key Integration Points

### 1. Preference Service ↔ Dynamic Scheduler

**Connection:** Event-driven synchronization via PreferenceEventSystem

```python
# PreferenceService emits events when preferences change
event = PreferenceChangeEvent(
    user_id=user_id,
    old_preferences=old_preferences,
    new_preferences=updated_preferences,
    changed_fields=changed_fields,
    source=source
)
await self.event_system.publish("preference_changed", event)

# Integration service handles events and updates scheduler
async def _handle_preference_change(self, event: PreferenceChangeEvent):
    if event.new_preferences.frequency == "disabled":
        await self.dynamic_scheduler.cancel_user_notification(event.user_id)
    else:
        await self.dynamic_scheduler.reschedule_user_notification(
            event.user_id, event.new_preferences
        )
```

### 2. Dynamic Scheduler ↔ Notification Service

**Connection:** Direct method calls for notification delivery

```python
# DynamicScheduler calls NotificationService for delivery
async def _execute_notification_job(self, user_id: UUID):
    # Get user preferences
    preferences = await self.preference_service.get_user_preferences(user_id)

    # Determine enabled channels
    channels = []
    if preferences.dm_enabled:
        channels.append(NotificationChannel("discord_dm", True))
    if preferences.email_enabled:
        channels.append(NotificationChannel("email", True))

    # Send via NotificationService
    results = await self.notification_service.send_notification(
        user_id=user_id,
        channels=channels,
        subject="Weekly Tech News Digest",
        articles=articles
    )
```

### 3. Notification Service ↔ Lock Manager

**Connection:** Atomic locking for multi-instance coordination

```python
# NotificationService uses LockManager for atomic operations
async def send_notification(self, user_id: UUID, channels: List[NotificationChannel]):
    # Acquire lock to prevent duplicate notifications
    lock = await self.lock_manager.acquire_notification_lock(
        user_id, "weekly_digest", scheduled_time
    )

    if not lock:
        # Another instance is handling this notification
        return [NotificationResult(False, "all", "Duplicate notification prevented")]

    try:
        # Send notifications to all channels
        results = []
        for channel in channels:
            result = await self._send_to_channel(user_id, channel)
            results.append(result)

        # Release lock with completion status
        await self.lock_manager.release_lock(lock.id, "completed")
        return results

    except Exception as e:
        # Release lock with failure status
        await self.lock_manager.release_lock(lock.id, "failed")
        raise
```

### 4. Cross-Interface Synchronization

**Connection:** Event system ensures consistency across web and Discord interfaces

```python
# Web API updates preferences with source tracking
updated_preferences = await preference_service.update_preferences(
    user_id, updates, source="web"
)

# Discord commands update preferences with source tracking
updated_preferences = await preference_service.update_preferences(
    user_id, updates, source="discord"
)

# Both trigger the same event system for synchronization
# No manual scheduler calls needed - handled automatically by events
```

## Error Propagation

### Service-Level Error Handling

Each service implements proper error handling and propagation:

```python
class NotificationSystemIntegration(BaseService):
    async def send_user_notification(self, user_id: UUID):
        try:
            # Coordinate notification delivery
            results = await self.notification_service.send_notification(...)
            return results
        except Exception as e:
            self._handle_error(
                e,
                "Failed to send coordinated user notification",
                error_code=ErrorCode.INTERNAL_ERROR,
                context={"user_id": str(user_id)}
            )
```

### Graceful Degradation

The system continues operating even when some components are unavailable:

```python
# Dynamic scheduler unavailable - log warning but continue
if not self.dynamic_scheduler:
    self.logger.warning("Dynamic scheduler not available")
    return False

# Bot client unavailable - skip Discord DM but continue with email
if not self.bot_client:
    self.logger.warning("Discord bot not available for DM")
    # Continue with other channels
```

## API Integration

### Unified API Interface

All notification operations go through the integration service:

```python
# API endpoints use integration service
@router.get("/user/{user_id}/status")
async def get_user_notification_status(user_id: str):
    integration_service = get_notification_system_integration()
    status = await integration_service.get_user_notification_status(user_uuid)
    return status

@router.post("/user/{user_id}/schedule")
async def schedule_user_notifications(user_id: str):
    integration_service = get_notification_system_integration()
    success = await integration_service.schedule_user_notifications(user_uuid)
    return {"success": success}
```

## System Health Monitoring

### Comprehensive Health Checks

The integration service provides system-wide health monitoring:

```python
async def get_system_health(self) -> Dict:
    health = {
        "overall_status": "healthy",
        "components": {},
        "statistics": {},
    }

    # Check each component
    health["components"]["preference_service"] = await self._check_preference_service()
    health["components"]["dynamic_scheduler"] = await self._check_dynamic_scheduler()
    health["components"]["lock_manager"] = await self._check_lock_manager()
    health["components"]["notification_service"] = await self._check_notification_service()

    return health
```

## Testing Integration

### Integration Tests

Comprehensive tests verify all components work together:

```python
class TestNotificationSystemIntegration:
    async def test_send_user_notification_integration(self):
        # Test full notification flow
        results = await integration_service.send_user_notification(user_id)
        assert len(results) > 0

    async def test_preference_change_event_handling(self):
        # Test event-driven synchronization
        await integration_service.update_user_preferences(user_id, updates)
        # Verify scheduler was updated automatically
```

## Benefits Achieved

### 1. Centralized Coordination

- Single integration service manages all component interactions
- Consistent error handling and logging across all operations
- Unified interface for all notification operations

### 2. Proper Dependency Injection

- Clear dependency hierarchy with no circular dependencies
- Services receive their dependencies through constructor injection
- Easy to mock dependencies for testing

### 3. Event-Driven Synchronization

- Automatic synchronization between interfaces
- No manual scheduler calls needed
- Extensible event system for future enhancements

### 4. Error Resilience

- Graceful degradation when components are unavailable
- Comprehensive error logging and monitoring
- System continues operating even with partial failures

### 5. Maintainability

- Clear separation of concerns between components
- Easy to add new components or modify existing ones
- Comprehensive testing coverage for all integration points

## Requirements Fulfilled

This implementation fulfills all integration requirements:

- ✅ **PreferenceService ↔ DynamicScheduler**: Connected via event system
- ✅ **DynamicScheduler ↔ NotificationService**: Connected via direct method calls
- ✅ **NotificationService ↔ LockManager**: Connected via atomic locking operations
- ✅ **Proper dependency injection**: All services receive dependencies through constructors
- ✅ **Error propagation**: Comprehensive error handling across service boundaries

The system now operates as a cohesive, integrated notification platform with proper component coordination and error handling.
