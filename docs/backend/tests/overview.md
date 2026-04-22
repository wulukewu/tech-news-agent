# Backend Test Organization

This directory contains all backend tests organized hierarchically by feature/module and test type.

## Directory Structure

```
backend/tests/
├── fixtures/              # Shared test fixtures and utilities
│   ├── __init__.py
│   ├── database.py       # Database-related fixtures
│   ├── auth.py           # Authentication fixtures
│   ├── api.py            # API testing fixtures
│   └── bot.py            # Discord bot fixtures
│
├── unit/                  # Unit tests (isolated, fast)
│   ├── core/             # Core functionality tests
│   ├── repositories/     # Repository layer tests
│   ├── services/         # Service layer tests
│   ├── api/              # API route handler tests
│   ├── bot/              # Bot cog tests
│   └── schemas/          # Schema validation tests
│
├── integration/           # Integration tests (multiple components)
│   ├── api/              # API integration tests
│   ├── services/         # Service integration tests
│   ├── bot/              # Bot integration tests
│   └── workflows/        # End-to-end workflow tests
│
├── e2e/                   # End-to-end tests (full system)
│   ├── auth/             # Authentication flows
│   ├── onboarding/       # User onboarding flows
│   ├── articles/         # Article management flows
│   └── notifications/    # Notification flows
│
├── property/              # Property-based tests
│   ├── core/             # Core property tests
│   ├── api/              # API property tests
│   └── services/         # Service property tests
│
├── conftest.py           # Pytest configuration and global fixtures
└── README.md             # This file
```

## Test Types

### Unit Tests (`unit/`)

- Test individual functions, classes, or modules in isolation
- Use mocks for external dependencies
- Fast execution (< 1 second per test)
- High coverage of edge cases and error conditions

**Example:**

```python
# tests/unit/services/test_rss_service.py
def test_parse_feed_entry(mock_supabase_client):
    service = RSSService(mock_supabase_client)
    entry = {"title": "Test", "link": "https://example.com"}
    result = service.parse_feed_entry(entry)
    assert result["title"] == "Test"
```

### Integration Tests (`integration/`)

- Test multiple components working together
- May use real database connections or external services
- Moderate execution time (1-10 seconds per test)
- Focus on component interactions and data flow

**Example:**

```python
# tests/integration/services/test_service_layer_integration.py
def test_article_creation_workflow(test_db):
    article_repo = ArticleRepository(test_db)
    article_service = ArticleService(article_repo)
    result = article_service.create_article(article_data)
    assert result.id is not None
```

### End-to-End Tests (`e2e/`)

- Test complete user workflows from start to finish
- Use real or near-real system configuration
- Slower execution (10+ seconds per test)
- Focus on critical user paths and business scenarios

**Example:**

```python
# tests/e2e/auth/test_discord_oauth_flow.py
def test_complete_discord_login_flow(test_client):
    # 1. Get OAuth URL
    response = test_client.get("/api/auth/discord/login")
    # 2. Simulate OAuth callback
    response = test_client.get("/api/auth/discord/callback?code=test")
    # 3. Verify user session
    assert response.cookies.get("access_token") is not None
```

### Property-Based Tests (`property/`)

- Test universal properties that should hold for all inputs
- Use Hypothesis for generating test cases
- Validate correctness properties from design document
- Focus on invariants and mathematical properties

**Example:**

```python
# tests/property/core/test_config_property.py
from hypothesis import given, strategies as st

@given(st.text())
def test_config_validation_property(config_value):
    # Property: All valid configs should load without error
    # Property: Invalid configs should fail with clear message
    ...
```

## Shared Fixtures

Shared fixtures are located in `fixtures/` and can be imported in any test:

```python
# Import specific fixtures
from tests.fixtures.database import mock_supabase_client, sample_user_data
from tests.fixtures.auth import mock_jwt_token, authenticated_headers
from tests.fixtures.api import test_client
from tests.fixtures.bot import mock_discord_bot, mock_discord_context

# Use in tests
def test_example(mock_supabase_client, sample_user_data):
    # Test implementation
    pass
```

## Running Tests

### Run all tests

```bash
pytest
```

### Run specific test type

```bash
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest tests/e2e/               # E2E tests only
pytest tests/property/          # Property-based tests only
```

### Run tests for specific feature

```bash
pytest tests/unit/services/     # All service unit tests
pytest tests/integration/api/   # All API integration tests
pytest tests/e2e/auth/          # All auth E2E tests
```

### Run with coverage

```bash
pytest --cov=app --cov-report=html
```

### Run property-based tests with more examples

```bash
pytest tests/property/ --hypothesis-show-statistics
```

## Test Naming Conventions

For comprehensive test naming conventions and guidelines, see:

- **[TEST_NAMING_CONVENTIONS.md](./TEST_NAMING_CONVENTIONS.md)** - Detailed naming conventions for all test types
- **[TEST_WRITING_GUIDELINES.md](../../TEST_WRITING_GUIDELINES.md)** - Best practices for writing effective tests

### Quick Reference

#### File Names

- Unit tests: `test_<module_name>.py`
- Integration tests: `test_<feature>_integration.py`
- E2E tests: `test_<workflow>_e2e.py`
- Property tests: `test_<feature>_property.py`

#### Test Function Names

- Unit tests: `test_<function_name>_<scenario>_<expected_result>()`
- Integration tests: `test_<feature>_<workflow>_<expected_result>()`
- E2E tests: `test_<user_action>_<expected_outcome>()`
- Property tests: `test_property_<number>_<property_name>()`

**Examples:**

```python
# Unit test
def test_parse_feed_entry_with_missing_title_raises_validation_error():
    pass

# Integration test
def test_batch_subscribe_with_valid_feeds_creates_subscriptions():
    pass

# E2E test
def test_user_can_complete_oauth_flow_and_receive_token():
    pass

# Property test
def test_property_6_valid_config_loads_successfully():
    pass
```

## Migration Guide

When moving tests to the new structure:

1. **Identify test type**: Determine if the test is unit, integration, e2e, or property-based
2. **Identify feature/module**: Determine which feature the test belongs to
3. **Move to appropriate directory**: Place in `tests/<type>/<feature>/`
4. **Update imports**: Adjust import paths if needed
5. **Use shared fixtures**: Replace local fixtures with shared ones where applicable
6. **Run tests**: Verify tests still pass after migration

## Best Practices

1. **Keep tests focused**: Each test should verify one specific behavior
2. **Use descriptive names**: Test names should clearly describe what is being tested
3. **Minimize test dependencies**: Tests should be independent and runnable in any order
4. **Use appropriate fixtures**: Leverage shared fixtures to reduce duplication
5. **Mock external dependencies**: Use mocks for databases, APIs, and external services in unit tests
6. **Test error cases**: Don't just test happy paths, test error handling too
7. **Keep tests fast**: Unit tests should run in milliseconds, not seconds
8. **Document complex tests**: Add comments explaining non-obvious test logic
9. **Follow AAA pattern**: Arrange, Act, Assert structure for clarity
10. **Clean up after tests**: Use fixtures and teardown to ensure clean state

## Coverage Goals

- **Critical paths**: 80%+ coverage
- **Core functionality**: 70%+ coverage
- **Overall codebase**: 60%+ coverage

## Continuous Integration

Tests are automatically run on:

- Every pull request
- Every push to main branch
- Nightly builds (full test suite including property-based tests)

CI configuration is in `.github/workflows/test.yml`

## Troubleshooting

### Tests fail locally but pass in CI

- Check Python version matches CI
- Ensure all dependencies are installed
- Clear pytest cache: `pytest --cache-clear`

### Property-based tests are slow

- Reduce max_examples in Hypothesis settings
- Use `@settings(max_examples=10)` for faster feedback during development
- Run full property tests only in CI

### Import errors after migration

- Update `sys.path` if needed
- Check `__init__.py` files exist in all directories
- Verify import paths are correct

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Discord.py Testing](https://discordpy.readthedocs.io/en/stable/ext/test/index.html)
