# Testing Guide

This project uses separate test suites for backend and frontend.

## Project Structure

```
tech-news-agent/
├── backend/
│   ├── tests/              # Backend Python tests
│   ├── pytest.ini          # Backend pytest configuration
│   ├── requirements.txt    # Backend dependencies
│   └── requirements-dev.txt
│
├── frontend/
│   ├── __tests__/          # Frontend unit tests (Jest)
│   ├── e2e/                # Frontend E2E tests (Playwright)
│   ├── jest.config.js
│   └── playwright.config.ts
│
└── .github/workflows/
    └── ci.yml              # Separate CI jobs for backend & frontend
```

## Backend Tests (Python)

### Setup

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Run Tests

```bash
# Run all tests
pytest

# Run fast tests (skip property-based and integration tests)
pytest --ignore-glob="*property*.py" --ignore=tests/integration/

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth_integration.py

# Run with parallel execution
pytest -n auto
```

### Test Categories

- **Unit Tests**: `test_*.py` (non-property, non-integration)
- **Property-Based Tests**: `test_*_property.py` (uses Hypothesis)
- **Integration Tests**: `tests/integration/`

## Frontend Tests (TypeScript/JavaScript)

### Setup

```bash
cd frontend
npm install
```

### Run Tests

```bash
# Run unit tests (Jest)
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run E2E tests (Playwright)
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui

# Type checking
npm run type-check

# Linting
npm run lint
```

## CI/CD

GitHub Actions runs both test suites in parallel:

- **Backend Job**: Python tests with pytest
- **Frontend Job**: TypeScript checks, linting, unit tests, and build

### CI Configuration

See `.github/workflows/ci.yml` for the complete CI pipeline.

### Fast Tests (All Branches)

```bash
# Backend
pytest --ignore-glob="*property*.py" --ignore=tests/integration/

# Frontend
npm test -- --passWithNoTests
```

### Full Tests (Main/PR Only)

```bash
# Backend
pytest  # Includes property-based and integration tests

# Frontend
npm test && npm run build
```

## Environment Variables for Tests

Backend tests use dummy values (see `.github/workflows/ci.yml`):

```bash
SUPABASE_URL=https://dummy.supabase.co
SUPABASE_KEY=dummy_supabase_key
DISCORD_TOKEN=dummy_discord_token
DISCORD_CHANNEL_ID=123456789012345678
GROQ_API_KEY=dummy_groq_api_key
TIMEZONE=Asia/Taipei
```

All external calls are mocked, so real credentials are never needed.

## Writing Tests

### Backend (pytest)

```python
# tests/test_example.py
import pytest
from app.services.example import example_function

def test_example():
    result = example_function("input")
    assert result == "expected"

@pytest.mark.asyncio
async def test_async_example():
    result = await async_function()
    assert result is not None
```

### Frontend (Jest)

```typescript
// __tests__/example.test.tsx
import { render, screen } from '@testing-library/react'
import Component from '@/components/Component'

describe('Component', () => {
  it('renders correctly', () => {
    render(<Component />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

## Troubleshooting

### Backend

**Issue**: `ModuleNotFoundError: No module named 'app'`

- **Solution**: Run tests from `backend/` directory

**Issue**: `ImportPathMismatchError`

- **Solution**: Ensure you're in the correct directory (backend/)

### Frontend

**Issue**: `Cannot find module '@/...'`

- **Solution**: Check `tsconfig.json` paths configuration

**Issue**: Tests timeout

- **Solution**: Increase timeout in `jest.config.js` or `playwright.config.ts`

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [Jest documentation](https://jestjs.io/)
- [Playwright documentation](https://playwright.dev/)
- [Hypothesis (property-based testing)](https://hypothesis.readthedocs.io/)
