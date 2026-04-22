# Test Organization Quick Start

Quick reference for working with the new hierarchical test structure.

## Directory Structure at a Glance

```
tests/
├── fixtures/          # Shared test fixtures
├── unit/             # Fast, isolated tests
├── integration/      # Multi-component tests
├── e2e/              # Full workflow tests
└── property/         # Property-based tests
```

## Where Does My Test Go?

| Test Type       | Location                 | When to Use                                  |
| --------------- | ------------------------ | -------------------------------------------- |
| **Unit**        | `unit/<feature>/`        | Testing single function/class with mocks     |
| **Integration** | `integration/<feature>/` | Testing multiple components together         |
| **E2E**         | `e2e/<feature>/`         | Testing complete user workflows              |
| **Property**    | `property/<feature>/`    | Testing universal properties with Hypothesis |

## Quick Commands

```bash
# Run all tests
pytest

# Run specific test type
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest tests/e2e/               # E2E tests only
pytest tests/property/          # Property tests only

# Run tests for specific feature
pytest tests/unit/services/     # All service unit tests
pytest tests/integration/api/   # All API integration tests

# Run with coverage
pytest --cov=app --cov-report=html

# Run fast tests only (skip slow integration/e2e)
pytest -m "not slow"

# Run property tests with more examples
pytest tests/property/ --hypothesis-show-statistics
```

## Writing a New Test

### 1. Unit Test Example

```python
# tests/unit/services/test_rss_service.py
from tests.fixtures.database import mock_supabase_client
from app.services.rss_service import RSSService

def test_parse_feed_entry_with_valid_data(mock_supabase_client):
    """Test RSS feed entry parsing with valid data."""
    # Arrange
    service = RSSService(mock_supabase_client)
    entry = {"title": "Test", "link": "https://example.com"}

    # Act
    result = service.parse_feed_entry(entry)

    # Assert
    assert result["title"] == "Test"
    assert result["url"] == "https://example.com"
```

### 2. Integration Test Example

```python
# tests/integration/services/test_article_workflow.py
from tests.fixtures.database import test_supabase_client, test_feed
from app.repositories.article import ArticleRepository
from app.services.article_service import ArticleService

def test_create_and_retrieve_article(test_supabase_client, test_feed):
    """Test article creation and retrieval workflow."""
    # Arrange
    repo = ArticleRepository(test_supabase_client)
    service = ArticleService(repo)
    article_data = {
        "title": "Test Article",
        "url": "https://example.com/article",
        "feed_id": test_feed["id"]
    }

    # Act
    created = service.create_article(article_data)
    retrieved = service.get_article(created.id)

    # Assert
    assert retrieved.id == created.id
    assert retrieved.title == "Test Article"
```

### 3. E2E Test Example

```python
# tests/e2e/auth/test_discord_login_flow.py
from tests.fixtures.api import test_client

def test_complete_discord_oauth_flow(test_client):
    """Test complete Discord OAuth login flow."""
    # Step 1: Get OAuth URL
    response = test_client.get("/api/auth/discord/login")
    assert response.status_code == 200
    assert "url" in response.json()

    # Step 2: Simulate OAuth callback
    response = test_client.get(
        "/api/auth/discord/callback",
        params={"code": "test_code"}
    )
    assert response.status_code == 200

    # Step 3: Verify user session
    assert "access_token" in response.cookies
```

### 4. Property Test Example

```python
# tests/property/core/test_config_property.py
from hypothesis import given, strategies as st
from app.core.config import ConfigManager

@given(st.text(min_size=1))
def test_config_validation_rejects_invalid_values(invalid_value):
    """Property: Config validation rejects all invalid values."""
    config = ConfigManager()

    # Assume invalid_value doesn't match expected format
    with pytest.raises(ValidationError):
        config.validate_database_url(invalid_value)
```

## Using Shared Fixtures

Import fixtures from the fixtures directory:

```python
# Import database fixtures
from tests.fixtures.database import (
    mock_supabase_client,
    sample_user_data,
    sample_article_data,
    sample_feed_data
)

# Import auth fixtures
from tests.fixtures.auth import (
    mock_jwt_token,
    mock_jwt_payload,
    authenticated_headers
)

# Import API fixtures
from tests.fixtures.api import (
    test_client,
    mock_request_context
)

# Import bot fixtures
from tests.fixtures.bot import (
    mock_discord_bot,
    mock_discord_context,
    mock_discord_interaction
)

# Use in test
def test_example(mock_supabase_client, sample_user_data):
    # Test implementation
    pass
```

## Test Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_unit_example():
    """Fast unit test."""
    pass

@pytest.mark.integration
def test_integration_example():
    """Integration test requiring database."""
    pass

@pytest.mark.e2e
def test_e2e_example():
    """End-to-end test."""
    pass

@pytest.mark.property
def test_property_example():
    """Property-based test."""
    pass

@pytest.mark.slow
def test_slow_example():
    """Slow test (skip with -m "not slow")."""
    pass
```

Run tests by marker:

```bash
pytest -m unit           # Run only unit tests
pytest -m integration    # Run only integration tests
pytest -m "not slow"     # Skip slow tests
```

## Common Patterns

### Mocking External Services

```python
from unittest.mock import MagicMock, patch

def test_with_mocked_service():
    """Test with mocked external service."""
    with patch('app.services.external_api.ExternalAPI') as mock_api:
        mock_api.return_value.fetch_data.return_value = {"data": "test"}

        # Test implementation
        result = my_function()

        assert result == {"data": "test"}
        mock_api.return_value.fetch_data.assert_called_once()
```

### Testing Async Functions

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await my_async_function()
    assert result is not None
```

### Testing Exceptions

```python
import pytest

def test_raises_exception():
    """Test that function raises expected exception."""
    with pytest.raises(ValueError, match="Invalid input"):
        my_function(invalid_input)
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
])
def test_uppercase(input, expected):
    """Test uppercase conversion with multiple inputs."""
    assert input.upper() == expected
```

## Debugging Tests

```bash
# Run with verbose output
pytest -v

# Run with print statements visible
pytest -s

# Run specific test
pytest tests/unit/services/test_rss_service.py::test_parse_feed_entry -v

# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l

# Run last failed tests
pytest --lf

# Run tests that failed, then all
pytest --ff
```

## Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Show missing lines in terminal
pytest --cov=app --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=app --cov-fail-under=80
```

## Best Practices Checklist

- [ ] Test is in correct directory (unit/integration/e2e/property)
- [ ] Test name clearly describes what is being tested
- [ ] Test uses shared fixtures where applicable
- [ ] Test follows AAA pattern (Arrange, Act, Assert)
- [ ] Test is independent (doesn't depend on other tests)
- [ ] Test cleans up after itself (or uses fixtures that do)
- [ ] Test has appropriate markers (@pytest.mark.unit, etc.)
- [ ] Test is fast (unit tests < 1s, integration < 10s)
- [ ] Test covers both happy path and error cases
- [ ] Test has clear assertion messages

## Getting Help

- **README.md**: Comprehensive test organization guide
- **MIGRATION_GUIDE.md**: Guide for migrating existing tests
- **fixtures/**: Check fixture implementations for examples
- **Existing tests**: Look at already-organized tests as examples

## Quick Reference Card

| Need                  | Command                             |
| --------------------- | ----------------------------------- |
| Run all tests         | `pytest`                            |
| Run unit tests        | `pytest tests/unit/`                |
| Run fast tests        | `pytest -m "not slow"`              |
| Run with coverage     | `pytest --cov=app`                  |
| Run specific test     | `pytest path/to/test.py::test_name` |
| Debug test            | `pytest --pdb`                      |
| Show print output     | `pytest -s`                         |
| Verbose output        | `pytest -v`                         |
| Last failed           | `pytest --lf`                       |
| Stop on first failure | `pytest -x`                         |

## Example Test File Template

```python
"""
Tests for <module_name>.

This module contains <unit/integration/e2e/property> tests for <feature>.
"""
import pytest
from tests.fixtures.database import mock_supabase_client
from app.<module> import <Class>


class Test<ClassName>:
    """Test suite for <ClassName>."""

    def test_<method_name>_with_valid_input(self, mock_supabase_client):
        """Test <method_name> with valid input."""
        # Arrange
        instance = <Class>(mock_supabase_client)
        valid_input = "test"

        # Act
        result = instance.<method_name>(valid_input)

        # Assert
        assert result is not None
        assert result == expected_value

    def test_<method_name>_with_invalid_input(self, mock_supabase_client):
        """Test <method_name> with invalid input."""
        # Arrange
        instance = <Class>(mock_supabase_client)
        invalid_input = None

        # Act & Assert
        with pytest.raises(ValueError):
            instance.<method_name>(invalid_input)
```
