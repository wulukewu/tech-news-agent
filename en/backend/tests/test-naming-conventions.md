# Test Naming Conventions and Guidelines

## Overview

This document establishes consistent naming conventions for tests across the Tech News Agent backend codebase. Following these conventions ensures tests are discoverable, maintainable, and clearly communicate their purpose.

**Validates: Requirement 9.4 - Consistent naming conventions for tests**

## Table of Contents

1. [File Naming Conventions](#file-naming-conventions)
2. [Test Function Naming](#test-function-naming)
3. [Test Class Naming](#test-class-naming)
4. [Describe/Context Patterns](#describecontext-patterns)
5. [Common Test Patterns](#common-test-patterns)
6. [Property-Based Test Naming](#property-based-test-naming)
7. [Examples by Test Type](#examples-by-test-type)

---

## File Naming Conventions

### General Rules

- All test files MUST start with `test_`
- Use snake_case for file names
- File name should reflect the module being tested
- Include test type suffix for clarity

### Unit Tests

**Pattern:** `test_{module_name}.py`

```
✅ Good:
tests/unit/services/test_rss_service.py
tests/unit/repositories/test_feed_repository.py
tests/unit/core/test_logger.py

❌ Bad:
tests/unit/services/rss_service_test.py
tests/unit/services/test_rss.py
tests/unit/services/RSSServiceTest.py
```

### Integration Tests

**Pattern:** `test_{feature}_integration.py`

```
✅ Good:
tests/integration/test_service_layer_integration.py
tests/integration/test_bot_cogs_integration.py
tests/integration/api/test_auth_integration.py

❌ Bad:
tests/integration/service_layer_test.py
tests/integration/test_service_layer.py
tests/integration/integration_test_service_layer.py
```

### End-to-End Tests

**Pattern:** `test_{workflow}_e2e.py`

```
✅ Good:
tests/e2e/test_discord_multi_tenant_e2e.py
tests/e2e/auth/test_oauth_flow_e2e.py
tests/e2e/onboarding/test_complete_onboarding_e2e.py

❌ Bad:
tests/e2e/discord_test.py
tests/e2e/test_discord.py
tests/e2e/e2e_discord_test.py
```

### Property-Based Tests

**Pattern:** `test_{feature}_property.py`

```
✅ Good:
tests/property/core/test_config_property.py
tests/property/api/test_api_response_standardization_properties.py
tests/test_error_handling_properties.py

❌ Bad:
tests/property/config_test.py
tests/property/test_config.py
tests/property/property_test_config.py
```

---

## Test Function Naming

### General Rules

- Use descriptive names that explain WHAT is being tested and WHAT the expected outcome is
- Start with `test_`
- Use snake_case
- Include context about the scenario being tested
- Avoid generic names like `test_1`, `test_basic`, `test_function`

### Pattern: `test_{what}_{scenario}_{expected_result}`

### Unit Test Functions

**Pattern:** `test_{function_name}_{scenario}_{expected_result}`

```python
✅ Good:
def test_parse_feed_entry_with_valid_data_returns_article():
    """Test that parse_feed_entry returns article when given valid data."""
    pass

def test_parse_feed_entry_with_missing_title_raises_validation_error():
    """Test that parse_feed_entry raises ValidationError when title is missing."""
    pass

def test_calculate_reading_time_with_empty_content_returns_zero():
    """Test that calculate_reading_time returns 0 for empty content."""
    pass

❌ Bad:
def test_parse_feed_entry():
    pass

def test_parse_feed_entry_1():
    pass

def test_basic_parsing():
    pass
```

### Integration Test Functions

**Pattern:** `test_{feature}_{workflow}_{expected_result}`

```python
✅ Good:
def test_batch_subscribe_with_valid_feeds_creates_subscriptions():
    """Test that batch_subscribe creates subscriptions for valid feeds."""
    pass

def test_batch_subscribe_with_partial_failures_returns_error_details():
    """Test that batch_subscribe returns detailed errors for failed subscriptions."""
    pass

def test_onboarding_service_with_new_user_creates_default_preferences():
    """Test that onboarding service creates default preferences for new users."""
    pass

❌ Bad:
def test_batch_subscribe():
    pass

def test_subscription_works():
    pass

def test_integration_1():
    pass
```

### End-to-End Test Functions

**Pattern:** `test_{user_action}_{expected_outcome}`

```python
✅ Good:
def test_user_can_complete_discord_oauth_flow_and_receive_token():
    """Test complete Discord OAuth flow from login to token receipt."""
    pass

def test_user_can_subscribe_to_feed_and_receive_articles():
    """Test user can subscribe to feed and articles appear in their list."""
    pass

def test_admin_can_trigger_manual_fetch_and_see_new_articles():
    """Test admin can manually trigger article fetch and see results."""
    pass

❌ Bad:
def test_oauth():
    pass

def test_user_flow():
    pass

def test_e2e_1():
    pass
```

### Property-Based Test Functions

**Pattern:** `test_property_{number}_{property_name}`

```python
✅ Good:
def test_property_5_missing_required_config_fails_fast():
    """
    **Property 5: Configuration Validation**

    For any required configuration value that is missing or invalid at startup,
    the Config Manager SHALL fail immediately with a clear error message.

    **Validates: Requirements 6.3, 6.4**
    """
    pass

def test_property_6_valid_config_loads_successfully():
    """
    **Property 6: Configuration Loading**

    For any environment variable set in the system, the Config Manager SHALL
    correctly load and provide type-safe access to that configuration value.

    **Validates: Requirements 6.1**
    """
    pass

❌ Bad:
def test_config_property():
    pass

def test_property_test_1():
    pass

def test_hypothesis_config():
    pass
```

---

## Test Class Naming

### General Rules

- Use PascalCase for class names
- Start with `Test`
- Group related tests in classes
- Class name should describe the feature or component being tested

### Pattern: `Test{FeatureName}{TestType}`

```python
✅ Good:
class TestSubscriptionServiceIntegration:
    """Integration tests for SubscriptionService with real repositories."""
    pass

class TestOnboardingServiceIntegration:
    """Integration tests for OnboardingService with real repositories."""
    pass

class TestServiceLayerTransactionBoundaries:
    """Tests for transaction boundaries and cross-repository operations."""
    pass

class TestConfigurationValidation:
    """Tests for configuration validation rules."""
    pass

❌ Bad:
class SubscriptionTests:
    pass

class TestService:
    pass

class Test1:
    pass
```

---

## Describe/Context Patterns

While pytest doesn't have built-in `describe`/`context` blocks like Jest, we use test classes and docstrings to achieve similar organization.

### Using Test Classes as Describe Blocks

```python
class TestArticleRepository:
    """Unit tests for ArticleRepository."""

    class TestCreate:
        """Tests for create method."""

        def test_create_with_valid_data_returns_article(self):
            """Test that create returns article when given valid data."""
            pass

        def test_create_with_duplicate_url_raises_conflict_error(self):
            """Test that create raises ConflictError for duplicate URLs."""
            pass

    class TestUpdate:
        """Tests for update method."""

        def test_update_with_valid_id_updates_article(self):
            """Test that update modifies article when given valid ID."""
            pass

        def test_update_with_invalid_id_raises_not_found_error(self):
            """Test that update raises NotFoundError for invalid ID."""
            pass
```

### Using Docstrings for Context

```python
def test_batch_subscribe_with_valid_feeds_creates_subscriptions(
    subscription_service,
    test_user,
    test_feed
):
    """
    Test successful batch subscription with real repositories.

    Context: User has valid account and feeds exist in database
    Action: Call batch_subscribe with valid feed IDs
    Expected: Subscriptions are created and count is correct

    Validates: Requirements 3.3 (service calls repository methods)
    """
    # Arrange
    user_id = UUID(test_user['id'])
    feed_ids = [UUID(test_feed['id'])]

    # Act
    result = await subscription_service.batch_subscribe(user_id, feed_ids)

    # Assert
    assert result.subscribed_count == 1
```

---

## Common Test Patterns

### AAA Pattern (Arrange-Act-Assert)

Always structure tests with clear AAA sections:

```python
def test_create_article_with_valid_data_returns_article(article_repo, sample_article_data):
    """Test that create_article returns article when given valid data."""
    # Arrange
    article_data = sample_article_data.copy()
    article_data['title'] = 'Test Article'

    # Act
    result = article_repo.create(article_data)

    # Assert
    assert result.id is not None
    assert result.title == 'Test Article'
    assert result.created_at is not None
```

### Error Testing Pattern

```python
def test_create_article_with_missing_title_raises_validation_error(article_repo):
    """Test that create_article raises ValidationError when title is missing."""
    # Arrange
    invalid_data = {'url': 'https://example.com', 'content': 'Test'}

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        article_repo.create(invalid_data)

    # Assert error details
    assert 'title' in str(exc_info.value).lower()
    assert exc_info.value.error_code == 'VALIDATION_FAILED'
```

### Async Test Pattern

```python
@pytest.mark.asyncio
async def test_fetch_articles_with_valid_feed_returns_articles(rss_service, test_feed):
    """Test that fetch_articles returns articles for valid feed."""
    # Arrange
    feed_url = test_feed['url']

    # Act
    articles = await rss_service.fetch_articles(feed_url)

    # Assert
    assert len(articles) > 0
    assert all(article.feed_id == test_feed['id'] for article in articles)
```

### Parametrized Test Pattern

```python
@pytest.mark.parametrize('invalid_url,expected_error', [
    ('', 'URL cannot be empty'),
    ('not-a-url', 'Invalid URL format'),
    ('http://invalid', 'URL must use HTTPS'),
])
def test_validate_feed_url_with_invalid_urls_raises_error(invalid_url, expected_error):
    """Test that validate_feed_url raises appropriate errors for invalid URLs."""
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        validate_feed_url(invalid_url)

    assert expected_error in str(exc_info.value)
```

---

## Property-Based Test Naming

### Property Test Structure

Property-based tests should include:

1. Property number (from design document)
2. Property name
3. Detailed docstring with property statement
4. Requirements validation

```python
@given(config_env=valid_config_env_strategy())
@settings(max_examples=50, deadline=None)
def test_property_6_valid_config_loads_successfully(config_env, monkeypatch):
    """
    **Property 6: Configuration Loading**

    For any environment variable set in the system, the Config Manager SHALL
    correctly load and provide type-safe access to that configuration value.

    **Validates: Requirements 6.1**
    """
    # Import Settings here to avoid module-level config loading
    from app.core.config import Settings

    # Set all environment variables
    for key, value in config_env.items():
        monkeypatch.setenv(key, value)

    # Load settings
    settings = Settings()

    # Verify all values are loaded correctly
    assert settings.supabase_url == config_env["SUPABASE_URL"]
    assert settings.supabase_key == config_env["SUPABASE_KEY"]
```

### Property Test Naming Convention

**Pattern:** `test_property_{number}_{descriptive_name}`

```python
✅ Good:
test_property_5_missing_required_config_fails_fast
test_property_6_valid_config_loads_successfully
test_property_7_audit_trail_completeness
test_property_10_api_response_structure_consistency

❌ Bad:
test_config_property
test_property_1
test_hypothesis_test
```

---

## Examples by Test Type

### Unit Test Example

```python
# tests/unit/services/test_rss_service.py

class TestRSSService:
    """Unit tests for RSSService."""

    def test_parse_feed_entry_with_valid_data_returns_article(self, mock_supabase_client):
        """Test that parse_feed_entry returns article when given valid data."""
        # Arrange
        service = RSSService(mock_supabase_client)
        entry = {
            'title': 'Test Article',
            'link': 'https://example.com/article',
            'published': '2024-01-01T00:00:00Z',
            'summary': 'Test summary'
        }

        # Act
        result = service.parse_feed_entry(entry)

        # Assert
        assert result['title'] == 'Test Article'
        assert result['url'] == 'https://example.com/article'
        assert result['summary'] == 'Test summary'

    def test_parse_feed_entry_with_missing_title_raises_validation_error(self, mock_supabase_client):
        """Test that parse_feed_entry raises ValidationError when title is missing."""
        # Arrange
        service = RSSService(mock_supabase_client)
        entry = {
            'link': 'https://example.com/article',
            'published': '2024-01-01T00:00:00Z'
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            service.parse_feed_entry(entry)

        assert 'title' in str(exc_info.value).lower()
```

### Integration Test Example

```python
# tests/integration/test_service_layer_integration.py

class TestSubscriptionServiceIntegration:
    """
    Integration tests for SubscriptionService with real repositories.

    Tests service methods with actual database operations to verify:
    - Correct repository usage
    - Error handling
    - Logging integration
    - Business logic execution
    """

    @pytest.fixture
    def subscription_service(self, test_supabase_client: Client):
        """Create SubscriptionService with real repositories."""
        feed_repo = FeedRepository(test_supabase_client)
        user_subscription_repo = UserSubscriptionRepository(test_supabase_client)
        return SubscriptionService(feed_repo, user_subscription_repo)

    @pytest.mark.asyncio
    async def test_batch_subscribe_with_valid_feeds_creates_subscriptions(
        self,
        subscription_service,
        test_supabase_client,
        test_user,
        test_feed
    ):
        """
        Test successful batch subscription with real repositories.

        Validates: Requirements 3.3 (service calls repository methods)
        """
        # Arrange
        user_id = UUID(test_user['id'])
        feed_ids = [UUID(test_feed['id'])]

        # Act
        result = await subscription_service.batch_subscribe(user_id, feed_ids)

        # Assert
        assert result.subscribed_count == 1
        assert result.failed_count == 0

        # Verify subscription was created in database
        response = test_supabase_client.table('user_subscriptions') \
            .select('*') \
            .eq('user_id', str(user_id)) \
            .execute()

        assert len(response.data) == 1
```

### E2E Test Example

```python
# tests/e2e/auth/test_discord_oauth_e2e.py

class TestDiscordOAuthFlowE2E:
    """End-to-end tests for Discord OAuth authentication flow."""

    @pytest.mark.asyncio
    async def test_user_can_complete_oauth_flow_and_receive_token(
        self,
        test_client,
        mock_discord_api
    ):
        """
        Test complete Discord OAuth flow from login to token receipt.

        User Story: As a user, I want to log in with Discord so that
        I can access the application.

        Steps:
        1. User clicks "Login with Discord"
        2. User is redirected to Discord OAuth page
        3. User authorizes the application
        4. User is redirected back with auth code
        5. Application exchanges code for token
        6. User receives access token cookie
        """
        # Arrange
        mock_discord_api.setup_oauth_flow()

        # Act - Step 1: Get OAuth URL
        response = test_client.get('/api/auth/discord/login')
        assert response.status_code == 200
        oauth_url = response.json()['url']
        assert 'discord.com/oauth2/authorize' in oauth_url

        # Act - Step 2-4: Simulate OAuth callback
        response = test_client.get(
            '/api/auth/discord/callback',
            params={'code': 'test_auth_code'}
        )

        # Assert - Step 5-6: Verify token received
        assert response.status_code == 200
        assert 'access_token' in response.cookies
        assert response.json()['user']['id'] is not None
```

### Property Test Example

```python
# tests/property/core/test_config_property.py

@given(config_env=valid_config_env_strategy())
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None
)
def test_property_6_valid_config_loads_successfully(config_env, monkeypatch):
    """
    **Property 6: Configuration Loading**

    For any environment variable set in the system, the Config Manager SHALL
    correctly load and provide type-safe access to that configuration value.

    **Validates: Requirements 6.1**
    """
    # Import Settings here to avoid module-level config loading
    from app.core.config import Settings

    # Set all environment variables
    for key, value in config_env.items():
        monkeypatch.setenv(key, value)

    # Load settings
    settings = Settings()

    # Verify all values are loaded correctly
    assert settings.supabase_url == config_env["SUPABASE_URL"]
    assert settings.supabase_key == config_env["SUPABASE_KEY"]
    assert settings.discord_token == config_env["DISCORD_TOKEN"]
```

---

## Quick Reference

### File Naming

| Test Type   | Pattern                         | Example                             |
| ----------- | ------------------------------- | ----------------------------------- |
| Unit        | `test_{module}.py`              | `test_rss_service.py`               |
| Integration | `test_{feature}_integration.py` | `test_service_layer_integration.py` |
| E2E         | `test_{workflow}_e2e.py`        | `test_discord_oauth_e2e.py`         |
| Property    | `test_{feature}_property.py`    | `test_config_property.py`           |

### Function Naming

| Test Type   | Pattern                               | Example                                              |
| ----------- | ------------------------------------- | ---------------------------------------------------- |
| Unit        | `test_{function}_{scenario}_{result}` | `test_parse_feed_with_valid_data_returns_article`    |
| Integration | `test_{feature}_{workflow}_{result}`  | `test_batch_subscribe_with_valid_feeds_creates_subs` |
| E2E         | `test_{user_action}_{outcome}`        | `test_user_can_complete_oauth_and_receive_token`     |
| Property    | `test_property_{number}_{name}`       | `test_property_6_valid_config_loads_successfully`    |

### Class Naming

| Pattern               | Example                              |
| --------------------- | ------------------------------------ |
| `Test{Feature}`       | `TestRSSService`                     |
| `Test{Feature}{Type}` | `TestSubscriptionServiceIntegration` |
| `Test{Feature}E2E`    | `TestDiscordOAuthFlowE2E`            |

---

## Checklist for Writing Tests

When writing a new test, ensure:

- [ ] File name starts with `test_` and uses snake_case
- [ ] File name includes test type suffix (for integration/e2e/property tests)
- [ ] Test function name starts with `test_`
- [ ] Test function name describes what is being tested and expected outcome
- [ ] Test has clear docstring explaining purpose
- [ ] Test follows AAA pattern (Arrange-Act-Assert)
- [ ] Test class name starts with `Test` and uses PascalCase
- [ ] Property tests include property number and validation statement
- [ ] Test is in correct directory (unit/integration/e2e/property)
- [ ] Test uses appropriate fixtures from `conftest.py` or `fixtures/`

---

## Additional Resources

- [Backend Test README](./README.md) - Comprehensive test organization guide
- [Pytest Documentation](https://docs.pytest.org/) - Official pytest docs
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/) - Property-based testing
- [Design Document](../../.kiro/specs/project-architecture-refactoring/design.md) - Correctness properties

---

**Last Updated:** 2024-01-XX
**Maintained By:** Tech News Agent Team
**Related:** Requirements 9.4, Tasks 14.3
