# Implementation Plan: Personalized Notification Frequency

## Overview

This implementation plan transforms the notification system from a rigid system-wide CRON approach to a flexible, user-centric dynamic scheduling system. The implementation follows a phased approach: database schema setup, core services development, interface implementation, and integration testing.

## Tasks

- [x] 1. Database schema setup and migrations
  - [x] 1.1 Create database migration for user_notification_preferences table
    - Create migration file with table schema including user_id, frequency, notification_time, timezone, dm_enabled, email_enabled fields
    - Add foreign key constraint to users table with CASCADE delete
    - Add check constraints for frequency enum values
    - Add indexes for user_id and frequency columns
    - _Requirements: 4.1, 4.2, 4.3, 4.6, 4.7_

  - [x] 1.2 Create database migration for notification_locks table
    - Create migration file with table schema including user_id, notification_type, scheduled_time, status, instance_id, created_at, expires_at fields
    - Add foreign key constraint to users table with CASCADE delete
    - Add unique constraint on (user_id, notification_type, scheduled_time)
    - Add indexes for (user_id, scheduled_time) and (status, expires_at)
    - _Requirements: 4.4, 4.5, 4.7_

  - [x] 1.3 Write property test for database schema integrity
    - **Property 1: Default Preference Creation**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

- [x] 2. Core service implementations
  - [x] 2.1 Implement PreferenceService class
    - Create TypeScript class with getUserPreferences, updatePreferences, createDefaultPreferences, validatePreferences methods
    - Implement database CRUD operations with proper error handling
    - Add input validation for frequency, time format, and timezone
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 2.1, 2.2, 2.3, 2.4_

  - [x] 2.2 Write property test for preference validation
    - **Property 2: Preference Validation Consistency**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

  - [x] 2.3 Implement TimezoneConverter utility class
    - Create static methods for convertToUserTime, convertToUTC, getNextNotificationTime
    - Handle timezone conversion using Intl.DateTimeFormat
    - Support all frequency types (daily, weekly, monthly) with proper date calculations
    - _Requirements: 5.3_

  - [x] 2.4 Write property test for timezone conversion accuracy
    - **Property 4: Timezone Conversion Accuracy**
    - **Validates: Requirements 5.3**

- [x] 3. Dynamic scheduling system
  - [x] 3.1 Implement DynamicScheduler class
    - Create methods for scheduleUserNotification, cancelUserNotification, rescheduleUserNotification
    - Integrate with job scheduling library (node-cron or similar)
    - Handle job lifecycle management and cleanup
    - _Requirements: 5.1, 5.2, 5.4, 5.5_

  - [x] 3.2 Write property test for dynamic scheduling correctness
    - **Property 3: Dynamic Scheduling Correctness**
    - **Validates: Requirements 5.1, 5.2, 5.4, 5.5**

  - [x] 3.3 Implement LockManager for atomic notification locking
    - Create methods for acquireNotificationLock, releaseLock, cleanupExpiredLocks
    - Use database transactions for atomic lock operations
    - Implement lock expiration and cleanup mechanisms
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 3.4 Write property test for atomic notification locking
    - **Property 6: Atomic Notification Locking**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

- [x] 4. Checkpoint - Core services validation
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Notification service implementation
  - [x] 5.1 Implement NotificationService class
    - Create methods for sendNotification, sendDiscordDM, sendEmail
    - Integrate with Discord API for DM sending
    - Implement email service integration with HTML and text formats
    - Add retry logic and error handling for failed deliveries
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 10.6_

  - [x] 5.2 Write property test for multi-channel notification delivery
    - **Property 7: Multi-Channel Notification Delivery**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 10.6**

  - [x] 5.3 Remove system-level DM_NOTIFICATION_CRON dependency
    - Remove DM_NOTIFICATION_CRON environment variable usage from codebase
    - Update system startup to not initialize CRON-based scheduling
    - Ensure no legacy CRON jobs remain active
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 6. Web interface implementation
  - [x] 6.1 Create notification preferences API endpoints
    - Implement GET /api/user/notification-preferences endpoint
    - Implement PUT /api/user/notification-preferences endpoint
    - Implement GET /api/user/notification-preview endpoint
    - Add request/response validation and error handling
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 6.2 Create notification preferences UI components
    - Build React components for preference settings form
    - Add form validation and real-time preview functionality
    - Implement timezone selector with search/filter capability
    - Add confirmation messages and error display
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [x] 6.3 Write unit tests for web interface components
    - Test form validation, user interactions, and API integration
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 7. Discord interface implementation
  - [x] 7.1 Implement Discord slash commands
    - Create /notification-settings command for viewing current preferences
    - Create /set-notification-frequency command with frequency options
    - Create /set-notification-time command with time validation
    - Create /set-timezone command with timezone validation
    - Create /toggle-notifications command for enabling/disabling
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 7.2 Implement Discord command handlers
    - Add command validation and error handling
    - Integrate with PreferenceService for database operations
    - Provide user-friendly response messages
    - _Requirements: 7.6_

  - [x] 7.3 Write unit tests for Discord commands
    - Test command parsing, validation, and database integration
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 8. Cross-interface synchronization
  - [x] 8.1 Implement preference synchronization mechanism
    - Add event system for preference changes
    - Ensure immediate synchronization between web and Discord interfaces
    - Trigger scheduler updates on preference changes
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 8.2 Write property test for cross-interface synchronization
    - **Property 5: Cross-Interface Synchronization**
    - **Validates: Requirements 6.2, 6.6, 7.1, 7.6, 8.1, 8.2, 8.3, 8.4, 11.1, 11.2, 11.3**

  - [x] 8.3 Fix notification status display issues
    - Correct DM notification status reading in web interface
    - Correct DM notification status reading in Discord interface
    - Ensure immediate status updates when toggling notifications
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [x] 9. Integration and system wiring
  - [x] 9.1 Wire all components together
    - Connect PreferenceService with DynamicScheduler
    - Connect DynamicScheduler with NotificationService
    - Connect NotificationService with LockManager
    - Ensure proper dependency injection and error propagation
    - _Requirements: All requirements integration_

  - [x] 9.2 Implement system initialization
    - Add startup routine to initialize dynamic scheduling for existing users
    - Migrate existing users to default notification preferences
    - Start background cleanup processes for expired locks
    - _Requirements: 2.4, 10.5_

  - [x] 9.3 Write integration tests
    - Test end-to-end notification flow from preference setting to delivery
    - Test multi-instance coordination and lock management
    - _Requirements: All requirements validation_

- [x] 10. Final validation and cleanup
  - [x] 10.1 Add comprehensive logging and monitoring
    - Implement structured logging for all preference changes
    - Add metrics collection for notification delivery rates
    - Add alerting for system health monitoring
    - _Requirements: 10.6_

  - [x] 10.2 Write property test for interface input validation
    - **Property 8: Interface Input Validation and Feedback**
    - **Validates: Requirements 6.3, 6.4, 6.5, 7.2, 7.3, 7.4, 7.5**

  - [x] 10.3 Final checkpoint - Ensure all tests pass
    - Ensure all tests pass, ask the user if questions arise.

## Phase 1: Advanced Notification Features

- [x] 11. Quiet Hours Implementation
  - [x] 11.1 Create database migration for user_quiet_hours table
    - Create migration file with table schema including user_id, start_time, end_time, timezone, weekdays, enabled fields
    - Add foreign key constraint to users table with CASCADE delete
    - Add indexes for user_id and enabled columns
    - Support time ranges that span midnight (e.g., 22:00-08:00)

  - [x] 11.2 Implement QuietHoursService class
    - Create methods for getQuietHours, updateQuietHours, isInQuietHours
    - Handle timezone conversion for quiet hours checking
    - Support weekday-specific quiet hours (work days vs weekends)
    - Integrate with notification scheduling to respect quiet hours

  - [x] 11.3 Create quiet hours API endpoints
    - Implement GET /api/user/quiet-hours endpoint
    - Implement PUT /api/user/quiet-hours endpoint
    - Add request/response validation and error handling
    - Include timezone-aware quiet hours checking

  - [x] 11.4 Create QuietHoursSettings UI component
    - Build React component for quiet hours configuration
    - Add time range picker with timezone support
    - Include weekday selection (work days, weekends, custom)
    - Add real-time preview of when notifications will be blocked

  - [x] 11.5 Implement Discord quiet hours commands
    - Create /quiet-hours command for viewing current settings
    - Create /set-quiet-hours command with time range validation
    - Add weekday selection support in Discord interface
    - Provide clear feedback on quiet hours status

  - [x] 11.6 Write unit tests for quiet hours functionality
    - Test quiet hours validation and timezone handling
    - Test integration with notification scheduling
    - Test cross-platform synchronization

- [x] 12. Technical Depth Threshold Implementation
  - [x] 12.1 Create database migration for technical depth settings
    - Add tech_depth_threshold column to user_notification_preferences table
    - Add tech_depth_enabled boolean column with default false
    - Create indexes for efficient filtering
    - Support four levels: basic, intermediate, advanced, expert

  - [x] 12.2 Implement TechnicalDepthService class
    - Create methods for getTechDepthSettings, updateTechDepthSettings
    - Implement article filtering based on technical depth
    - Add depth level validation and conversion utilities
    - Integrate with notification filtering pipeline

  - [x] 12.3 Create technical depth API endpoints
    - Implement GET /api/user/tech-depth-threshold endpoint
    - Implement PUT /api/user/tech-depth-threshold endpoint
    - Add validation for depth levels and settings
    - Include preview of how many articles would be filtered

  - [x] 12.4 Create TechnicalDepthThreshold UI component
    - Build React component for depth threshold selection
    - Add visual indicators for each depth level
    - Include description and examples for each level
    - Show real-time preview of filtering effects

  - [x] 12.5 Implement Discord technical depth commands
    - Create /tech-depth command for viewing current threshold
    - Create /set-tech-depth command with level validation
    - Provide clear descriptions of each depth level
    - Show examples of content at each level

  - [x] 12.6 Write unit tests for technical depth functionality
    - Test depth level validation and filtering
    - Test integration with article recommendation system
    - Test cross-platform synchronization

- [x] 13. Notification History Implementation
  - [x] 13.1 Create database migration for notification_history table
    - Create migration file with table schema including id, user_id, sent_at, channel, status, content, feed_source fields
    - Add foreign key constraint to users table with CASCADE delete
    - Add indexes for (user_id, sent_at) and (user_id, status)
    - Support pagination and efficient querying

  - [x] 13.2 Implement NotificationHistoryService class
    - Create methods for recordNotification, getNotificationHistory, getNotificationStats
    - Add filtering by date range, channel, and status
    - Implement pagination for large history sets
    - Add cleanup for old notification records

  - [x] 13.3 Create notification history API endpoints
    - Implement GET /api/user/notification-history endpoint with pagination
    - Implement GET /api/user/notification-stats endpoint
    - Add filtering parameters (date range, channel, status)
    - Include search functionality for notification content

  - [x] 13.4 Create NotificationHistoryPanel UI component
    - Build React component for notification history display
    - Add filtering and search functionality
    - Include status indicators and retry options for failed notifications
    - Implement infinite scroll or pagination for large datasets

  - [x] 13.5 Implement Discord notification history commands
    - Create /notification-history command with pagination
    - Add filtering options for recent notifications
    - Show notification status and retry options
    - Provide summary statistics

  - [x] 13.6 Write unit tests for notification history functionality
    - Test history recording and retrieval
    - Test filtering and pagination
    - Test cleanup and data retention policies

- [x] 14. Integration and Testing
  - [x] 14.1 Update notification scheduling to respect quiet hours
    - Modify DynamicScheduler to check quiet hours before sending
    - Implement notification queuing during quiet hours
    - Add logic to send queued notifications after quiet hours end
    - Ensure timezone-aware quiet hours checking

  - [x] 14.2 Update notification filtering for technical depth
    - Modify article processing to include technical depth scoring
    - Update notification pipeline to filter based on user threshold
    - Add depth level to notification content and history
    - Ensure consistent depth scoring across all content sources

  - [x] 14.3 Integrate notification history recording
    - Update NotificationService to record all notification attempts
    - Add history recording to both Discord and email channels
    - Include detailed status tracking (sent, failed, queued, cancelled)
    - Ensure history is recorded even for failed notifications

  - [x] 14.4 Write integration tests for advanced features
    - Test end-to-end flow with quiet hours, depth filtering, and history
    - Test cross-platform synchronization of all new settings
    - Test notification queuing and delayed delivery
    - Validate data consistency across all new features

  - [x] 14.5 Update existing UI to integrate new features
    - Enhance PersonalizedNotificationSettings component
    - Add new settings sections with proper organization
    - Ensure responsive design and accessibility
    - Update navigation and help text

- [x] 15. Final Phase 1 Validation
  - [x] 15.1 Comprehensive testing of all Phase 1 features
    - Run all unit tests and integration tests
    - Test cross-platform functionality (Web ↔ Discord)
    - Validate database migrations and data integrity
    - Ensure backward compatibility with existing users

  - [x] 15.2 Performance optimization and monitoring
    - Add performance monitoring for new database queries
    - Optimize notification history queries with proper indexing
    - Add caching for frequently accessed settings
    - Monitor memory usage and cleanup processes

  - [x] 15.3 Documentation and user guidance
    - Update API documentation for new endpoints
    - Create user guides for new features
    - Add help text and tooltips in UI components
    - Document Discord command usage and examples

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation uses TypeScript throughout for type safety
- Database migrations ensure backward compatibility with existing data
- Multi-instance coordination prevents duplicate notifications through atomic locking
- Cross-interface synchronization ensures consistent user experience

## Phase 2: Notification Frequency Enhancement

- [x] 16. Add Day-of-Week and Day-of-Month Fields
  - [x] 16.1 Create database migration for new fields
    - Create migration 009 to add notification_day_of_week (0-6) and notification_day_of_month (1-31) columns
    - Add CHECK constraints for valid ranges
    - Set default values: notification_day_of_week = 5 (Friday), notification_day_of_month = 1
    - Update existing records with default values

  - [x] 16.2 Update backend schemas and services
    - Update UserNotificationPreferences schema to include new fields
    - Update UpdateUserNotificationPreferencesRequest schema with validation
    - Update PreferenceService.update_preferences to handle new fields ⚠️ **Fixed**
    - Update TimezoneConverter to use day fields in scheduling logic
    - Update DynamicScheduler to respect day-of-week and day-of-month settings

  - [x] 16.3 Update frontend components
    - Update UserNotificationPreferences interface in API types
    - Add day-of-week selector for weekly frequency
    - Add day-of-month selector for monthly frequency
    - Implement conditional rendering based on frequency selection
    - Update preview functionality to include day fields

  - [x] 16.4 Testing and validation
    - Test database migration execution
    - Test backend API updates with new fields
    - Test scheduling logic with different day configurations
    - Test edge cases (Sunday=0, Saturday=6, day 31 in short months)
    - Verify frontend UI displays and updates correctly

  - [x] 16.5 Bug fix: PreferenceService not handling new fields
    - **Issue**: API returned "No fields to update" when updating day fields
    - **Root cause**: PreferenceService.update_preferences missing handlers for notification_day_of_week and notification_day_of_month
    - **Fix**: Added field handlers in update_preferences method
    - **Validation**: Backend tests pass, API correctly updates database
    - **Status**: ✅ Fixed and verified

## Implementation Notes

### Phase 2 Completion Status

All Phase 2 tasks are complete. The notification frequency enhancement now supports:

- **Weekly notifications**: Users can select specific day of week (Sunday-Saturday)
- **Monthly notifications**: Users can select specific day of month (1-31)
- **Automatic adjustment**: System handles months with fewer than 31 days
- **Default values**: Friday for weekly, 1st for monthly
- **Full integration**: Works across web and Discord interfaces

### Known Issues and Resolutions

1. ✅ **PreferenceService field handling** - Fixed in backend/app/services/preference_service.py
2. ✅ **Database migration** - Successfully applied to production
3. ✅ **Frontend UI** - Day selectors display and function correctly
4. ✅ **API integration** - All endpoints handle new fields properly

### Testing Summary

- ✅ Database migration: Passed
- ✅ Backend unit tests: Passed (daily, weekly, monthly, edge cases)
- ✅ API endpoint tests: Passed
- ✅ Frontend UI tests: Passed
- ✅ Integration tests: Passed

**Last Updated**: 2026-04-21
**Status**: ✅ Phase 2 Complete
