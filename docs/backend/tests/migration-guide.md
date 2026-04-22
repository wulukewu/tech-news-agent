# Test Migration Guide

This guide helps migrate existing tests from the flat structure to the new hierarchical organization.

## Migration Strategy

The migration follows a gradual approach:

1. New hierarchical structure is created alongside existing tests
2. Tests are moved incrementally by feature/module
3. Old test files are removed after successful migration
4. All tests continue to work during migration

## Test Classification

### How to Classify Your Test

Ask these questions to determine where a test belongs:

1. **Does it test a single function/class in isolation?**
   - YES → `unit/<feature>/`
   - Uses mocks for all dependencies
   - Fast execution (< 1 second)

2. **Does it test multiple components working together?**
   - YES → `integration/<feature>/`
   - May use real database or services
   - Moderate execution (1-10 seconds)

3. **Does it test a complete user workflow end-to-end?**
   - YES → `e2e/<feature>/`
   - Uses real or near-real system
   - Slower execution (10+ seconds)

4. **Does it test universal properties with generated inputs?**
   - YES → `property/<feature>/`
   - Uses Hypothesis
   - Tests invariants and mathematical properties

## Migration Mapping

### Current Flat Structure → New Hierarchical Structure

| Current Location                                  | Test Type   | New Location                                             |
| ------------------------------------------------- | ----------- | -------------------------------------------------------- |
| `test_config.py`                                  | Unit        | `unit/core/test_config.py`                               |
| `test_config_property.py`                         | Property    | `property/core/test_config_property.py`                  |
| `test_logger.py`                                  | Unit        | `unit/core/test_logger.py`                               |
| `test_logger_property.py`                         | Property    | `property/core/test_logger_property.py`                  |
| `test_core_errors.py`                             | Unit        | `unit/core/test_errors.py`                               |
| `test_error_handling_properties.py`               | Property    | `property/core/test_error_handling_properties.py`        |
| `test_validators.py`                              | Unit        | `unit/core/test_validators.py`                           |
| `test_article_schema_*.py`                        | Unit        | `unit/schemas/test_article_schema.py`                    |
| `test_feed_schema_*.py`                           | Unit        | `unit/schemas/test_feed_schema.py`                       |
| `test_reading_list_schema.py`                     | Unit        | `unit/schemas/test_reading_list_schema.py`               |
| `test_supabase_service_*.py`                      | Unit        | `unit/services/test_supabase_service.py`                 |
| `test_rss_service.py`                             | Unit        | `unit/services/test_rss_service.py`                      |
| `test_rss_service_*_property.py`                  | Property    | `property/services/test_rss_service_property.py`         |
| `test_llm_service.py`                             | Unit        | `unit/services/test_llm_service.py`                      |
| `test_llm_service_*_property.py`                  | Property    | `property/services/test_llm_service_property.py`         |
| `test_notion_service.py`                          | Unit        | `unit/services/test_notion_service.py`                   |
| `test_analytics_service.py`                       | Unit        | `unit/services/test_analytics_service.py`                |
| `test_recommendation_service.py`                  | Unit        | `unit/services/test_recommendation_service.py`           |
| `test_onboarding_service.py`                      | Unit        | `unit/services/test_onboarding_service.py`               |
| `test_add_feed_command.py`                        | Unit        | `unit/bot/test_add_feed_command.py`                      |
| `test_list_feeds_command.py`                      | Unit        | `unit/bot/test_list_feeds_command.py`                    |
| `test_news_now_command.py`                        | Unit        | `unit/bot/test_news_now_command.py`                      |
| `test_admin_commands.py`                          | Unit        | `unit/bot/test_admin_commands.py`                        |
| `test_auth_jwt_utils.py`                          | Unit        | `unit/api/test_auth_jwt_utils.py`                        |
| `test_auth_discord_login_endpoint.py`             | Unit        | `unit/api/test_auth_endpoints.py`                        |
| `test_health_endpoint.py`                         | Unit        | `unit/api/test_health_endpoint.py`                       |
| `test_auth_integration.py`                        | Integration | `integration/api/test_auth_integration.py`               |
| `test_service_layer_integration.py`               | Integration | `integration/services/test_service_layer_integration.py` |
| `test_bot_cogs_integration.py`                    | Integration | `integration/bot/test_bot_cogs_integration.py`           |
| `test_complete_workflow_integration.py`           | Integration | `integration/workflows/test_complete_workflow.py`        |
| `test_onboarding_service_integration.py`          | Integration | `integration/workflows/test_onboarding_workflow.py`      |
| `test_discord_multi_tenant_e2e.py`                | E2E         | `e2e/auth/test_discord_multi_tenant.py`                  |
| `test_dm_notification_integration.py`             | E2E         | `e2e/notifications/test_dm_notification.py`              |
| `test_weekly_news_job_integration.py`             | E2E         | `e2e/notifications/test_weekly_news_job.py`              |
| `test_api_response_standardization_properties.py` | Property    | `property/api/test_response_standardization.py`          |
| `test_audit_and_integrity_properties.py`          | Property    | `property/core/test_audit_and_integrity.py`              |

## Step-by-Step Migration Process

### 1. Identify Test Type and Feature

```bash
# Example: Migrating test_rss_service.py
# 1. Read the test file
# 2. Identify: Unit test for RSS service
# 3. Target location: unit/services/test_rss_service.py
```

### 2. Move Test File

```bash
# Option A: Git move (preserves history)
git mv backend/tests/test_rss_service.py backend/tests/unit/services/test_rss_service.py

# Option B: Regular move
mv backend/tests/test_rss_service.py backend/tests/unit/services/test_rss_service.py
```

### 3. Update Imports

```python
# Before (in flat structure)
from app.services.rss_service import RSSService
from conftest import mock_supabase_client

# After (in hierarchical structure)
from app.services.rss_service import RSSService
from tests.fixtures.database import mock_supabase_client
```

### 4. Use Shared Fixtures

Replace local fixtures with shared ones:

```python
# Before: Local fixture in test file
@pytest.fixture
def mock_supabase_client():
    client = MagicMock()
    # ... setup code
    return client

# After: Import from shared fixtures
from tests.fixtures.database import mock_supabase_client
```

### 5. Run Tests

```bash
# Run the migrated test
pytest backend/tests/unit/services/test_rss_service.py -v

# Run all tests to ensure nothing broke
pytest backend/tests/ -v
```

### 6. Update CI Configuration (if needed)

If CI runs specific test paths, update `.github/workflows/test.yml`:

```yaml
# Before
- name: Run tests
  run: pytest backend/tests/test_*.py

# After
- name: Run unit tests
  run: pytest backend/tests/unit/
- name: Run integration tests
  run: pytest backend/tests/integration/
```

## Consolidation Opportunities

Some tests can be consolidated during migration:

### Example: Multiple Property Tests → Single File

```python
# Before: Separate files
# test_rss_service_deduplication_property.py
# test_rss_service_time_filtering_property.py

# After: Consolidated in property/services/test_rss_service_property.py
"""Property-based tests for RSS service."""

def test_deduplication_property():
    """Property: RSS service deduplicates articles by URL."""
    pass

def test_time_filtering_property():
    """Property: RSS service filters articles by time window."""
    pass
```

### Example: Multiple Unit Tests → Single File

```python
# Before: Separate files
# test_auth_jwt_utils.py
# test_auth_jwt_round_trip_property.py
# test_auth_jwt_token_structure_property.py

# After: Organized in unit/api/test_auth.py and property/api/test_auth_property.py
```

## Common Issues and Solutions

### Issue 1: Import Errors After Migration

**Problem:**

```python
ModuleNotFoundError: No module named 'conftest'
```

**Solution:**

```python
# Update imports to use absolute paths from tests/
from tests.fixtures.database import mock_supabase_client
```

### Issue 2: Fixture Not Found

**Problem:**

```
fixture 'mock_supabase_client' not found
```

**Solution:**

```python
# Import fixture explicitly or add to conftest.py
from tests.fixtures.database import mock_supabase_client
```

### Issue 3: Relative Imports Break

**Problem:**

```python
# This breaks after moving
from ..app.services import RSSService
```

**Solution:**

```python
# Use absolute imports
from app.services.rss_service import RSSService
```

### Issue 4: Test Discovery Issues

**Problem:**

```
pytest can't find tests in new location
```

**Solution:**

```bash
# Ensure __init__.py exists in all directories
touch backend/tests/unit/services/__init__.py

# Or run pytest with explicit path
pytest backend/tests/unit/services/
```

## Verification Checklist

After migrating a test file:

- [ ] Test file is in correct directory based on test type
- [ ] All imports are updated and working
- [ ] Test runs successfully: `pytest <path_to_test> -v`
- [ ] Test is using shared fixtures where applicable
- [ ] Old test file is removed (if fully migrated)
- [ ] CI pipeline still passes
- [ ] Test coverage is maintained or improved

## Batch Migration Script

For migrating multiple tests at once:

```bash
#!/bin/bash
# migrate_tests.sh

# Example: Migrate all RSS service tests
mkdir -p backend/tests/unit/services
mkdir -p backend/tests/property/services

# Move unit tests
git mv backend/tests/test_rss_service.py backend/tests/unit/services/
git mv backend/tests/test_rss_parsing_unit.py backend/tests/unit/services/

# Move property tests
git mv backend/tests/test_rss_service_deduplication_property.py backend/tests/property/services/
git mv backend/tests/test_rss_service_time_filtering_property.py backend/tests/property/services/

# Run tests to verify
pytest backend/tests/unit/services/ -v
pytest backend/tests/property/services/ -v
```

## Priority Migration Order

Migrate tests in this order for minimal disruption:

1. **Phase 1: Core Infrastructure** (Week 1)
   - Core tests (config, logger, errors, validators)
   - Shared fixtures setup
   - Update conftest.py

2. **Phase 2: Repository & Service Layers** (Week 2)
   - Repository unit tests
   - Service unit tests
   - Service property tests

3. **Phase 3: API & Bot** (Week 3)
   - API unit tests
   - Bot unit tests
   - Schema validation tests

4. **Phase 4: Integration Tests** (Week 4)
   - Service integration tests
   - API integration tests
   - Bot integration tests
   - Workflow integration tests

5. **Phase 5: E2E Tests** (Week 5)
   - Auth E2E tests
   - Onboarding E2E tests
   - Notification E2E tests
   - Article management E2E tests

## Rollback Plan

If migration causes issues:

1. **Keep old tests until migration is verified**

   ```bash
   # Don't delete old tests immediately
   # Keep them until new structure is proven
   ```

2. **Use git to revert if needed**

   ```bash
   git checkout HEAD -- backend/tests/test_*.py
   ```

3. **Run both old and new tests in parallel**
   ```bash
   # In CI, run both until confident
   pytest backend/tests/test_*.py  # Old tests
   pytest backend/tests/unit/      # New tests
   ```

## Questions?

If you encounter issues during migration:

1. Check this guide for common issues
2. Review the README.md for test organization principles
3. Look at already-migrated tests as examples
4. Ask the team for help

## Progress Tracking

Track migration progress:

```markdown
## Migration Status

### Core (5/5) ✅

- [x] config
- [x] logger
- [x] errors
- [x] validators
- [x] fixtures

### Services (0/8)

- [ ] rss_service
- [ ] llm_service
- [ ] notion_service
- [ ] analytics_service
- [ ] recommendation_service
- [ ] onboarding_service
- [ ] supabase_service
- [ ] subscription_service

### API (0/6)

- [ ] auth
- [ ] articles
- [ ] feeds
- [ ] reading_list
- [ ] recommendations
- [ ] scheduler

### Bot (0/4)

- [ ] feed_commands
- [ ] admin_commands
- [ ] news_commands
- [ ] interactions

### Integration (0/4)

- [ ] service_layer
- [ ] api
- [ ] bot
- [ ] workflows

### E2E (0/4)

- [ ] auth
- [ ] onboarding
- [ ] notifications
- [ ] articles
```
