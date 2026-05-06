# Bot Cogs Integration Tests

## Overview

This document describes the integration tests for Discord bot cogs, validating Requirements 7.2 and 7.4 (Bot cogs use Service_Layer for business logic).

## Test File

- **Location**: `backend/tests/integration/test_bot_cogs_integration.py`
- **Test Count**: 17 integration tests
- **Status**: ✅ All tests passing

## Test Coverage

### 1. NewsCommands Integration Tests (3 tests)

Tests for the `/news_now` command:

- **test_news_now_with_service_layer**: Verifies that the command correctly integrates with SupabaseService to fetch user subscriptions and articles
- **test_news_now_error_handling**: Validates graceful error handling when service layer operations fail
- **test_news_now_logging**: Confirms that operations are properly logged with structured context

### 2. SubscriptionCommands Integration Tests (5 tests)

Tests for subscription management commands:

- **test_add_feed_with_service_layer**: Verifies `/add_feed` command integrates with service layer for feed creation and subscription
- **test_list_feeds_with_service_layer**: Validates `/list_feeds` command retrieves subscriptions through service layer
- **test_unsubscribe_feed_with_service_layer**: Tests `/unsubscribe_feed` command uses service layer for unsubscription
- **test_subscription_error_handling**: Confirms error handling for database failures
- **test_subscription_logging**: Validates logging of subscription operations

### 3. ReadingListCog Integration Tests (5 tests)

Tests for reading list management:

- **test_reading_list_view_with_service_layer**: Verifies `/reading_list view` command integrates with SupabaseService
- **test_reading_list_recommend_with_service_layer**: Tests integration with both SupabaseService and LLMService for recommendations
- **test_reading_list_error_handling**: Validates error handling for database failures
- **test_reading_list_llm_error_handling**: Tests error handling for LLM service failures
- **test_reading_list_logging**: Confirms proper logging of reading list operations

### 4. Interactive Components Integration Tests (4 tests)

Tests for Discord UI components (buttons, selects):

- **test_mark_as_read_button_with_service_layer**: Verifies MarkAsReadButton integrates with service layer to update article status
- **test_rating_select_with_service_layer**: Tests RatingSelect integrates with service layer to update article ratings
- **test_interactive_component_error_handling**: Validates error handling in interactive components
- **test_interactive_component_logging**: Confirms logging of interactive component operations

## Key Testing Patterns

### 1. Service Layer Mocking

All tests use mocked service instances to isolate bot cog logic:

```python
@pytest.fixture
def mock_supabase_service():
    """Create a mock SupabaseService."""
    service = MagicMock(spec=SupabaseService)
    service.get_or_create_user = AsyncMock()
    service.get_user_subscriptions = AsyncMock()
    # ... other methods
    return service
```

### 2. Discord Interaction Mocking

Discord interactions are mocked to test command behavior without a real Discord client:

```python
@pytest.fixture
def mock_interaction():
    """Create a mock Discord interaction."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user.id = 123456789
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction
```

### 3. Command Callback Testing

Commands are tested by calling their callback methods directly:

```python
await cog.news_now.callback(cog, mock_interaction)
```

### 4. Decorator Mocking

The `ensure_user_registered` decorator is mocked to avoid database dependencies:

```python
with patch('app.bot.cogs.news_commands.ensure_user_registered', return_value=user_uuid):
    await cog.news_now.callback(cog, mock_interaction)
```

### 5. Discord UI Component Testing

Discord UI components (buttons, selects) have read-only properties that require special handling:

```python
button = MarkAsReadButton(item, row=1, supabase_service=mock_supabase_service)
# Use object.__setattr__ to bypass read-only property
object.__setattr__(button, '_view', MagicMock())
```

## Validation

### Requirements Validated

- **Requirement 7.2**: Bot cogs use Service_Layer for business logic
  - All cogs inject service dependencies through constructors
  - No direct database access in cog code
  - Service layer methods are called for all data operations

- **Requirement 7.4**: Bot cogs use Service_Layer for business logic (duplicate of 7.2)
  - Same validation as 7.2

### Test Assertions

Each test validates:

1. **Service Layer Integration**: Service methods are called with correct parameters
2. **Error Handling**: Errors from service layer are caught and user-friendly messages are sent
3. **Logging**: Operations are logged with structured context (user_id, command, etc.)
4. **Response Format**: Discord responses follow expected format (ephemeral, content structure)

## Running the Tests

```bash
# Run all bot cogs integration tests
python3 -m pytest tests/integration/test_bot_cogs_integration.py -v

# Run specific test class
python3 -m pytest tests/integration/test_bot_cogs_integration.py::TestNewsCommandsIntegration -v

# Run with coverage
python3 -m pytest tests/integration/test_bot_cogs_integration.py --cov=app.bot.cogs --cov-report=term-missing
```

## Test Results

```
===================================== test session starts =====================================
collected 17 items

tests/integration/test_bot_cogs_integration.py::TestNewsCommandsIntegration::test_news_now_with_service_layer PASSED [  5%]
tests/integration/test_bot_cogs_integration.py::TestNewsCommandsIntegration::test_news_now_error_handling PASSED [ 11%]
tests/integration/test_bot_cogs_integration.py::TestNewsCommandsIntegration::test_news_now_logging PASSED [ 17%]
tests/integration/test_bot_cogs_integration.py::TestSubscriptionCommandsIntegration::test_add_feed_with_service_layer PASSED [ 23%]
tests/integration/test_bot_cogs_integration.py::TestSubscriptionCommandsIntegration::test_list_feeds_with_service_layer PASSED [ 29%]
tests/integration/test_bot_cogs_integration.py::TestSubscriptionCommandsIntegration::test_unsubscribe_feed_with_service_layer PASSED [ 35%]
tests/integration/test_bot_cogs_integration.py::TestSubscriptionCommandsIntegration::test_subscription_error_handling PASSED [ 41%]
tests/integration/test_bot_cogs_integration.py::TestSubscriptionCommandsIntegration::test_subscription_logging PASSED [ 47%]
tests/integration/test_bot_cogs_integration.py::TestReadingListCogIntegration::test_reading_list_view_with_service_layer PASSED [ 52%]
tests/integration/test_bot_cogs_integration.py::TestReadingListCogIntegration::test_reading_list_recommend_with_service_layer PASSED [ 58%]
tests/integration/test_bot_cogs_integration.py::TestReadingListCogIntegration::test_reading_list_error_handling PASSED [ 64%]
tests/integration/test_bot_cogs_integration.py::TestReadingListCogIntegration::test_reading_list_llm_error_handling PASSED [ 70%]
tests/integration/test_bot_cogs_integration.py::TestReadingListCogIntegration::test_reading_list_logging PASSED [ 76%]
tests/integration/test_bot_cogs_integration.py::TestInteractiveComponentsIntegration::test_mark_as_read_button_with_service_layer PASSED [ 82%]
tests/integration/test_bot_cogs_integration.py::TestInteractiveComponentsIntegration::test_rating_select_with_service_layer PASSED [ 88%]
tests/integration/test_bot_cogs_integration.py::TestInteractiveComponentsIntegration::test_interactive_component_error_handling PASSED [ 94%]
tests/integration/test_bot_cogs_integration.py::TestInteractiveComponentsIntegration::test_interactive_component_logging PASSED [100%]

======================== 17 passed, 5 warnings in 0.45s ========================
```

## Notes

- Tests use mocked services to avoid database dependencies
- All tests are isolated and can run in any order
- Tests validate both happy path and error scenarios
- Logging is verified to ensure observability
- Interactive components (buttons, selects) are tested for service layer integration
