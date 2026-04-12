# Frontend Test Organization

This directory contains all frontend tests organized by test type and feature/module.

## Directory Structure

```
__tests__/
├── unit/              # Unit tests for individual components, hooks, and utilities
│   ├── api/          # API client and related utilities
│   ├── components/   # React components
│   ├── contexts/     # React contexts
│   ├── hooks/        # Custom React hooks
│   └── lib/          # Utility functions and helpers
├── integration/       # Integration tests for feature workflows
│   ├── api/          # API integration tests
│   ├── features/     # Feature-level integration tests
│   ├── state/        # State management integration tests
│   └── workflows/    # User workflow integration tests
├── e2e/              # End-to-end tests using Playwright
│   ├── articles/     # Article-related E2E tests
│   ├── auth/         # Authentication E2E tests
│   ├── feeds/        # Feed management E2E tests
│   └── reading-list/ # Reading list E2E tests
├── property/         # Property-based tests using fast-check
│   ├── api/          # API property tests
│   ├── bugfix/       # Bug condition exploration tests
│   └── state/        # State management property tests
└── utils/            # Shared test utilities and helpers
    ├── index.ts           # Main export file
    ├── test-utils.tsx     # Base testing utilities
    ├── render.tsx         # Custom render functions
    ├── mocks.ts           # Mock data factories
    ├── api-mocks.ts       # API mocking utilities
    ├── assertions.ts      # Custom assertions
    └── wait-for.ts        # Async wait utilities
```

## Test Types

### Unit Tests (`unit/`)

Unit tests focus on testing individual components, hooks, or functions in isolation.

**Characteristics:**

- Fast execution
- No external dependencies (mocked)
- Test single responsibility
- High code coverage

**Example:**

```typescript
import { render, screen } from '@/__tests__/utils';
import { ArticleCard } from '@/components/ArticleCard';
import { mockArticle } from '@/__tests__/utils';

describe('ArticleCard', () => {
  it('renders article title and summary', () => {
    const article = mockArticle({ title: 'Test Article' });
    render(<ArticleCard article={article} />);

    expect(screen.getByText('Test Article')).toBeInTheDocument();
  });
});
```

### Integration Tests (`integration/`)

Integration tests verify that multiple components or modules work together correctly.

**Characteristics:**

- Test component interactions
- Test data flow between modules
- May use real implementations with mocked external services
- Focus on feature workflows

**Example:**

```typescript
import { renderWithQueryClient, screen, waitFor } from '@/__tests__/utils';
import { ArticleList } from '@/components/ArticleList';
import { setupMockServer } from '@/__tests__/utils';

describe('ArticleList Integration', () => {
  const server = setupMockServer();

  it('fetches and displays articles', async () => {
    renderWithQueryClient(<ArticleList />);

    await waitFor(() => {
      expect(screen.getByText('Test Article')).toBeInTheDocument();
    });
  });
});
```

### E2E Tests (`e2e/`)

End-to-end tests simulate real user interactions using Playwright.

**Characteristics:**

- Test complete user workflows
- Run in real browser environment
- Slowest but most comprehensive
- Test critical user paths

**Example:**

```typescript
import { test, expect } from '@playwright/test';

test('user can add article to reading list', async ({ page }) => {
  await page.goto('/articles');
  await page.click('[data-testid="article-card-1"]');
  await page.click('[data-testid="add-to-reading-list"]');

  await expect(page.locator('[data-testid="success-toast"]')).toBeVisible();
});
```

### Property Tests (`property/`)

Property-based tests verify universal properties using fast-check.

**Characteristics:**

- Generate random test inputs
- Verify properties hold for all inputs
- Catch edge cases
- Complement example-based tests

**Example:**

```typescript
import fc from 'fast-check';
import { apiClient } from '@/lib/api/client';

describe('API Client Properties', () => {
  it('always returns same instance (singleton)', () => {
    fc.assert(
      fc.property(fc.nat(), () => {
        const instance1 = apiClient;
        const instance2 = apiClient;
        return instance1 === instance2;
      })
    );
  });
});
```

## Shared Test Utilities

### Render Utilities (`utils/render.tsx`)

Custom render functions with different provider configurations:

```typescript
import { renderWithQueryClient, renderWithAllProviders } from '@/__tests__/utils';

// Render with React Query only
const { queryClient } = renderWithQueryClient(<MyComponent />);

// Render with all providers (Query, Auth, Theme, etc.)
renderWithAllProviders(<MyComponent />);
```

### Mock Data Factories (`utils/mocks.ts`)

Factory functions for creating consistent test data:

```typescript
import { mockArticle, mockArticles, mockUser } from '@/__tests__/utils';

// Create single mock article
const article = mockArticle({ title: 'Custom Title' });

// Create multiple mock articles
const articles = mockArticles(5);

// Create mock user
const user = mockUser({ username: 'testuser' });
```

### API Mocking (`utils/api-mocks.ts`)

MSW-based API mocking utilities:

```typescript
import { setupMockServer, mockApiResponse } from '@/__tests__/utils';

// Setup MSW server for all tests
const server = setupMockServer();

// Create custom mock response
const response = mockApiResponse({ id: '1', title: 'Article' });
```

### Custom Assertions (`utils/assertions.ts`)

Domain-specific assertions for common scenarios:

```typescript
import { assertLoadingState, assertErrorMessage, assertArticleCard } from '@/__tests__/utils';

// Assert loading state is shown
assertLoadingState();

// Assert error message is displayed
assertErrorMessage('Failed to load articles');

// Assert article card displays correct info
assertArticleCard(card, { title: 'Test', author: 'John' });
```

### Wait Utilities (`utils/wait-for.ts`)

Specialized wait functions for async testing:

```typescript
import { waitForLoadingToFinish, waitForQuerySuccess } from '@/__tests__/utils';

// Wait for loading to finish
await waitForLoadingToFinish();

// Wait for React Query to succeed
await waitForQuerySuccess(['articles'], queryClient);
```

## Naming Conventions

For comprehensive test naming conventions and guidelines, see:

- **[TEST_NAMING_CONVENTIONS.md](./TEST_NAMING_CONVENTIONS.md)** - Detailed naming conventions for all test types
- **[TEST_WRITING_GUIDELINES.md](../TEST_WRITING_GUIDELINES.md)** - Best practices for writing effective tests

### Quick Reference

#### Test Files

- Unit tests: `ComponentName.test.tsx` or `functionName.test.ts`
- Integration tests: `feature-name.integration.test.tsx`
- E2E tests: `workflow-name.spec.ts`
- Property tests: `property-name.property.test.ts`

#### Test Suites

```typescript
describe('ComponentName', () => {
  describe('when condition', () => {
    it('should do something', () => {
      // Test implementation
    });
  });
});
```

#### Test Cases

- Use descriptive names that explain the expected behavior
- Start with action verbs (renders, displays, calls, etc.)
- Focus on behavior, not implementation

**Good:**

```typescript
it('displays error message when API call fails', () => {});
it('renders loading state while fetching data', () => {});
it('calls onSave when save button is clicked', () => {});
```

**Bad:**

```typescript
it('test 1', () => {});
it('calls useState hook', () => {});
it('works correctly', () => {});
```

## Running Tests

### All Tests

```bash
npm test
```

### Unit Tests Only

```bash
npm test -- __tests__/unit
```

### Integration Tests Only

```bash
npm test -- __tests__/integration
```

### E2E Tests

```bash
npm run test:e2e
```

### Property Tests

```bash
npm test -- __tests__/property
```

### Watch Mode

```bash
npm test -- --watch
```

### Coverage Report

```bash
npm test -- --coverage
```

## Best Practices

### 1. Test Behavior, Not Implementation

**Good:**

```typescript
it('displays article title', () => {
  render(<ArticleCard article={mockArticle()} />);
  expect(screen.getByText('Test Article')).toBeInTheDocument();
});
```

**Bad:**

```typescript
it('calls useState with initial value', () => {
  const spy = jest.spyOn(React, 'useState');
  render(<ArticleCard article={mockArticle()} />);
  expect(spy).toHaveBeenCalledWith(null);
});
```

### 2. Use Shared Utilities

Always import from `@/__tests__/utils` for consistency:

```typescript
import { render, screen, mockArticle, assertLoadingState } from '@/__tests__/utils';
```

### 3. Clean Up After Tests

```typescript
afterEach(() => {
  jest.clearAllMocks();
  cleanup();
});
```

### 4. Use Data Test IDs Sparingly

Prefer semantic queries (role, label, text) over test IDs:

**Good:**

```typescript
screen.getByRole('button', { name: 'Add to Reading List' });
screen.getByLabelText('Article Title');
screen.getByText('Test Article');
```

**Acceptable (when semantic queries don't work):**

```typescript
screen.getByTestId('article-card-1');
```

### 5. Test Accessibility

Include accessibility checks in component tests:

```typescript
import { axe } from 'jest-axe';

it('has no accessibility violations', async () => {
  const { container } = render(<ArticleCard article={mockArticle()} />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### 6. Mock External Dependencies

Always mock external services and APIs:

```typescript
import { setupMockServer } from '@/__tests__/utils';

const server = setupMockServer();
```

### 7. Keep Tests Focused

Each test should verify one behavior:

**Good:**

```typescript
it('displays article title', () => {
  /* ... */
});
it('displays article author', () => {
  /* ... */
});
it('displays article date', () => {
  /* ... */
});
```

**Bad:**

```typescript
it('displays article information', () => {
  // Tests title, author, date, summary, etc.
});
```

## Coverage Goals

- **Critical paths**: 80%+ coverage
- **UI components**: 70%+ coverage
- **Utility functions**: 90%+ coverage
- **API clients**: 80%+ coverage

## Troubleshooting

### Tests Timing Out

Increase timeout for slow tests:

```typescript
it('slow operation', async () => {
  // Test implementation
}, 10000); // 10 second timeout
```

### Act Warnings

Wrap state updates in `act()`:

```typescript
import { act } from '@testing-library/react';

await act(async () => {
  await userEvent.click(button);
});
```

### Query Client Errors

Always use `createTestQueryClient()` for isolated tests:

```typescript
const queryClient = createTestQueryClient();
```

## Resources

- [Testing Library Documentation](https://testing-library.com/docs/react-testing-library/intro/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Playwright Documentation](https://playwright.dev/docs/intro)
- [fast-check Documentation](https://fast-check.dev/)
- [MSW Documentation](https://mswjs.io/docs/)
