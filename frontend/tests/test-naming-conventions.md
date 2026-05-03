# Test Naming Conventions and Guidelines

## Overview

This document establishes consistent naming conventions for tests across the Tech News Agent frontend codebase. Following these conventions ensures tests are discoverable, maintainable, and clearly communicate their purpose.

**Validates: Requirement 9.4 - Consistent naming conventions for tests**

## Table of Contents

1. [File Naming Conventions](#file-naming-conventions)
2. [Test Suite Naming (describe blocks)](#test-suite-naming-describe-blocks)
3. [Test Case Naming (it/test blocks)](#test-case-naming-ittest-blocks)
4. [Common Test Patterns](#common-test-patterns)
5. [Property-Based Test Naming](#property-based-test-naming)
6. [Examples by Test Type](#examples-by-test-type)

---

## File Naming Conventions

### General Rules

- Use PascalCase for component test files
- Use kebab-case for utility/function test files
- Include `.test.ts` or `.test.tsx` suffix for unit/integration tests
- Include `.spec.ts` suffix for E2E tests
- Include `.property.test.ts` suffix for property-based tests

### Unit Tests

**Pattern:** `{ComponentName}.test.tsx` or `{moduleName}.test.ts`

```
✅ Good:
__tests__/unit/components/ArticleCard.test.tsx
__tests__/unit/hooks/useArticles.test.tsx
__tests__/unit/lib/format-date.test.ts
__tests__/unit/api/api-client.test.ts

❌ Bad:
__tests__/unit/components/article-card.test.tsx
__tests__/unit/components/ArticleCardTest.tsx
__tests__/unit/components/test-article-card.tsx
__tests__/unit/components/ArticleCard.spec.tsx
```

### Integration Tests

**Pattern:** `{feature-name}.integration.test.tsx` or `{feature-name}.test.tsx`

```
✅ Good:
__tests__/integration/api/api-client-integration.test.ts
__tests__/integration/features/article-list.test.tsx
__tests__/integration/state/auth-flow.test.tsx
__tests__/integration/workflows/reading-list.test.tsx

❌ Bad:
__tests__/integration/api/apiClient.test.ts
__tests__/integration/features/ArticleList.test.tsx
__tests__/integration/state/authFlow.integration.test.tsx
```

### End-to-End Tests

**Pattern:** `{workflow-name}.spec.ts`

```
✅ Good:
__tests__/e2e/articles/article-browsing.spec.ts
__tests__/e2e/auth/discord-login.spec.ts
__tests__/e2e/reading-list/add-article.spec.ts
__tests__/e2e/feeds/feed-subscription.spec.ts

❌ Bad:
__tests__/e2e/articles/ArticleBrowsing.spec.ts
__tests__/e2e/auth/discord-login.test.ts
__tests__/e2e/reading-list/test-add-article.spec.ts
```

### Property-Based Tests

**Pattern:** `{feature-name}.property.test.ts`

```
✅ Good:
__tests__/property/api/api-client-singleton.property.test.ts
__tests__/property/state/context-isolation.property.test.tsx
__tests__/property/bugfix/undefined-article-id.property.test.ts

❌ Bad:
__tests__/property/api/apiClient.test.ts
__tests__/property/state/ContextIsolation.property.test.tsx
__tests__/property/bugfix/test-undefined-article.ts
```

---

## Test Suite Naming (describe blocks)

### General Rules

- Use `describe()` for grouping related tests
- First `describe` should match the component/module name
- Nested `describe` blocks should describe specific scenarios or methods
- Use plain language that describes behavior
- Avoid technical jargon in describe blocks

### Pattern: `describe('{ComponentName}', () => { ... })`

### Component Test Suites

```typescript
✅ Good:
describe('ArticleCard', () => {
  describe('when article has all fields', () => {
    it('renders title, author, and date', () => {});
  });

  describe('when article is missing author', () => {
    it('renders title and date only', () => {});
  });

  describe('when user clicks save button', () => {
    it('calls onSave with article ID', () => {});
  });
});

❌ Bad:
describe('ArticleCard component', () => {
  describe('test rendering', () => {
    it('test 1', () => {});
  });
});
```

### Hook Test Suites

```typescript
✅ Good:
describe('useArticles', () => {
  describe('when fetching articles', () => {
    it('returns loading state initially', () => {});
    it('returns articles on success', () => {});
    it('returns error on failure', () => {});
  });

  describe('when filtering by category', () => {
    it('refetches with category parameter', () => {});
  });
});

❌ Bad:
describe('useArticles hook', () => {
  describe('fetching', () => {
    it('works', () => {});
  });
});
```

### Utility Function Test Suites

```typescript
✅ Good:
describe('formatDate', () => {
  describe('when given valid date', () => {
    it('returns formatted string', () => {});
  });

  describe('when given invalid date', () => {
    it('returns fallback string', () => {});
  });

  describe('when given null', () => {
    it('returns empty string', () => {});
  });
});

❌ Bad:
describe('formatDate function', () => {
  it('test date formatting', () => {});
});
```

### API Client Test Suites

```typescript
✅ Good:
describe('ApiClient', () => {
  describe('Singleton Pattern', () => {
    it('returns same instance on multiple calls', () => {});
  });

  describe('Interceptor Support', () => {
    it('allows adding request interceptors', () => {});
    it('allows removing request interceptors', () => {});
  });

  describe('HTTP Methods', () => {
    it('performs GET request and returns data', () => {});
    it('performs POST request and returns data', () => {});
  });
});

❌ Bad:
describe('API Client', () => {
  it('test singleton', () => {});
  it('test interceptors', () => {});
  it('test methods', () => {});
});
```

---

## Test Case Naming (it/test blocks)

### General Rules

- Use `it()` or `test()` (prefer `it()` for consistency)
- Start with a verb (renders, displays, calls, returns, throws, etc.)
- Describe the expected behavior, not the implementation
- Use plain language that non-developers can understand
- Include context about the scenario being tested

### Pattern: `it('{action} {expected result}', () => { ... })`

### Component Rendering Tests

```typescript
✅ Good:
it('renders article title and summary', () => {});
it('displays loading spinner while fetching', () => {});
it('shows error message when fetch fails', () => {});
it('hides save button when article is already saved', () => {});

❌ Bad:
it('renders correctly', () => {});
it('test rendering', () => {});
it('should work', () => {});
it('ArticleCard test 1', () => {});
```

### User Interaction Tests

```typescript
✅ Good:
it('calls onSave when save button is clicked', () => {});
it('opens modal when edit button is clicked', () => {});
it('updates input value when user types', () => {});
it('submits form when enter key is pressed', () => {});

❌ Bad:
it('handles click', () => {});
it('test button click', () => {});
it('onClick works', () => {});
```

### State Management Tests

```typescript
✅ Good:
it('updates articles when refetch is called', () => {});
it('caches articles for 5 minutes', () => {});
it('invalidates cache when article is deleted', () => {});
it('preserves scroll position when navigating back', () => {});

❌ Bad:
it('state updates', () => {});
it('test cache', () => {});
it('works correctly', () => {});
```

### Error Handling Tests

```typescript
✅ Good:
it('displays error toast when API call fails', () => {});
it('retries request up to 3 times on network error', () => {});
it('falls back to cached data when offline', () => {});
it('logs error to console when validation fails', () => {});

❌ Bad:
it('handles errors', () => {});
it('test error case', () => {});
it('error handling works', () => {});
```

### Async Operation Tests

```typescript
✅ Good:
it('fetches articles on mount', async () => {});
it('waits for loading to finish before displaying content', async () => {});
it('debounces search input for 300ms', async () => {});
it('cancels pending request when component unmounts', async () => {});

❌ Bad:
it('async test', async () => {});
it('test loading', async () => {});
it('fetching works', async () => {});
```

---

## Common Test Patterns

### AAA Pattern (Arrange-Act-Assert)

Always structure tests with clear AAA sections:

```typescript
it('displays article title', () => {
  // Arrange
  const article = mockArticle({ title: 'Test Article' });

  // Act
  render(<ArticleCard article={article} />);

  // Assert
  expect(screen.getByText('Test Article')).toBeInTheDocument();
});
```

### User Event Pattern

```typescript
it('calls onSave when save button is clicked', async () => {
  // Arrange
  const onSave = jest.fn();
  const article = mockArticle();
  render(<ArticleCard article={article} onSave={onSave} />);

  // Act
  await userEvent.click(screen.getByRole('button', { name: /save/i }));

  // Assert
  expect(onSave).toHaveBeenCalledWith(article.id);
});
```

### Async Wait Pattern

```typescript
it('displays articles after loading', async () => {
  // Arrange
  setupMockServer();

  // Act
  renderWithQueryClient(<ArticleList />);

  // Assert
  await waitFor(() => {
    expect(screen.getByText('Test Article')).toBeInTheDocument();
  });
});
```

### Error Testing Pattern

```typescript
it('displays error message when fetch fails', async () => {
  // Arrange
  server.use(
    rest.get('/api/articles', (req, res, ctx) => {
      return res(ctx.status(500), ctx.json({ error: 'Server error' }));
    })
  );

  // Act
  renderWithQueryClient(<ArticleList />);

  // Assert
  await waitFor(() => {
    expect(screen.getByText(/failed to load articles/i)).toBeInTheDocument();
  });
});
```

### Hook Testing Pattern

```typescript
it('returns articles on successful fetch', async () => {
  // Arrange
  const { result } = renderHook(() => useArticles(), {
    wrapper: createQueryWrapper(),
  });

  // Act
  await waitFor(() => expect(result.current.isSuccess).toBe(true));

  // Assert
  expect(result.current.data).toHaveLength(3);
  expect(result.current.data[0].title).toBe('Test Article');
});
```

---

## Property-Based Test Naming

### Property Test Structure

Property-based tests should include:

1. Property number (from design document)
2. Property name
3. Detailed description of the property
4. Requirements validation

```typescript
describe('API Client Properties', () => {
  describe('Property 1: API Client Singleton', () => {
    it('always returns same instance across all calls', () => {
      /**
       * **Property 1: API Client Singleton**
       *
       * For any sequence of API client instantiation calls,
       * all instances SHALL reference the same underlying HTTP client object.
       *
       * **Validates: Requirements 1.1**
       */
      fc.assert(
        fc.property(fc.nat(100), () => {
          const instance1 = ApiClient.getInstance();
          const instance2 = ApiClient.getInstance();
          return instance1 === instance2;
        })
      );
    });
  });

  describe('Property 15: Request Interceptor Execution', () => {
    it('executes all interceptors in order before request', () => {
      /**
       * **Property 15: Request Interceptor Execution**
       *
       * For any API request made through the unified client,
       * all registered request interceptors SHALL execute in order
       * before the request is sent.
       *
       * **Validates: Requirements 1.3**
       */
      // Test implementation
    });
  });
});
```

### Property Test Naming Convention

**Pattern:** `describe('Property {number}: {name}', () => { ... })`

```typescript
✅ Good:
describe('Property 1: API Client Singleton', () => {
  it('always returns same instance across all calls', () => {});
});

describe('Property 3: Context Isolation', () => {
  it('only re-renders components consuming changed context', () => {});
});

describe('Property 14: Frontend Log Batching', () => {
  it('batches logs and sends in groups', () => {});
});

❌ Bad:
describe('Singleton test', () => {
  it('works', () => {});
});

describe('Property test 1', () => {
  it('test property', () => {});
});
```

---

## Examples by Test Type

### Unit Test Example

```typescript
// __tests__/unit/components/ArticleCard.test.tsx

import { render, screen } from '@/__tests__/utils';
import { ArticleCard } from '@/components/ArticleCard';
import { mockArticle } from '@/__tests__/utils';

describe('ArticleCard', () => {
  describe('when article has all fields', () => {
    it('renders title, author, and publication date', () => {
      // Arrange
      const article = mockArticle({
        title: 'Test Article',
        author: 'John Doe',
        published_at: '2024-01-01T00:00:00Z',
      });

      // Act
      render(<ArticleCard article={article} />);

      // Assert
      expect(screen.getByText('Test Article')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText(/Jan 1, 2024/i)).toBeInTheDocument();
    });

    it('renders article summary', () => {
      // Arrange
      const article = mockArticle({
        summary: 'This is a test summary',
      });

      // Act
      render(<ArticleCard article={article} />);

      // Assert
      expect(screen.getByText('This is a test summary')).toBeInTheDocument();
    });
  });

  describe('when article is missing optional fields', () => {
    it('renders title without author when author is null', () => {
      // Arrange
      const article = mockArticle({
        title: 'Test Article',
        author: null,
      });

      // Act
      render(<ArticleCard article={article} />);

      // Assert
      expect(screen.getByText('Test Article')).toBeInTheDocument();
      expect(screen.queryByText(/by/i)).not.toBeInTheDocument();
    });
  });

  describe('when user interacts with card', () => {
    it('calls onSave when save button is clicked', async () => {
      // Arrange
      const onSave = jest.fn();
      const article = mockArticle();
      render(<ArticleCard article={article} onSave={onSave} />);

      // Act
      await userEvent.click(screen.getByRole('button', { name: /save/i }));

      // Assert
      expect(onSave).toHaveBeenCalledWith(article.id);
      expect(onSave).toHaveBeenCalledTimes(1);
    });

    it('navigates to article detail when card is clicked', async () => {
      // Arrange
      const mockPush = jest.fn();
      jest.mock('next/navigation', () => ({
        useRouter: () => ({ push: mockPush }),
      }));
      const article = mockArticle({ id: '123' });
      render(<ArticleCard article={article} />);

      // Act
      await userEvent.click(screen.getByTestId('article-card'));

      // Assert
      expect(mockPush).toHaveBeenCalledWith('/articles/123');
    });
  });
});
```

### Integration Test Example

```typescript
// __tests__/integration/features/article-list.test.tsx

import { renderWithQueryClient, screen, waitFor } from '@/__tests__/utils';
import { ArticleList } from '@/components/ArticleList';
import { setupMockServer, mockArticles } from '@/__tests__/utils';
import { rest } from 'msw';

describe('ArticleList Integration', () => {
  const server = setupMockServer();

  describe('when fetching articles successfully', () => {
    it('displays loading state then articles', async () => {
      // Arrange
      const articles = mockArticles(3);
      server.use(
        rest.get('/api/articles', (req, res, ctx) => {
          return res(ctx.json({ data: articles }));
        })
      );

      // Act
      renderWithQueryClient(<ArticleList />);

      // Assert - Loading state
      expect(screen.getByText(/loading/i)).toBeInTheDocument();

      // Assert - Articles displayed
      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
        expect(screen.getByText(articles[0].title)).toBeInTheDocument();
        expect(screen.getByText(articles[1].title)).toBeInTheDocument();
        expect(screen.getByText(articles[2].title)).toBeInTheDocument();
      });
    });

    it('caches articles and does not refetch on remount', async () => {
      // Arrange
      const articles = mockArticles(2);
      let fetchCount = 0;
      server.use(
        rest.get('/api/articles', (req, res, ctx) => {
          fetchCount++;
          return res(ctx.json({ data: articles }));
        })
      );

      // Act - First render
      const { unmount } = renderWithQueryClient(<ArticleList />);
      await waitFor(() => {
        expect(screen.getByText(articles[0].title)).toBeInTheDocument();
      });
      expect(fetchCount).toBe(1);

      // Act - Unmount and remount
      unmount();
      renderWithQueryClient(<ArticleList />);

      // Assert - Should use cached data, no new fetch
      await waitFor(() => {
        expect(screen.getByText(articles[0].title)).toBeInTheDocument();
      });
      expect(fetchCount).toBe(1); // Still 1, no refetch
    });
  });

  describe('when fetch fails', () => {
    it('displays error message with retry button', async () => {
      // Arrange
      server.use(
        rest.get('/api/articles', (req, res, ctx) => {
          return res(ctx.status(500), ctx.json({ error: 'Server error' }));
        })
      );

      // Act
      renderWithQueryClient(<ArticleList />);

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/failed to load articles/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });

    it('refetches articles when retry button is clicked', async () => {
      // Arrange
      let attemptCount = 0;
      const articles = mockArticles(2);
      server.use(
        rest.get('/api/articles', (req, res, ctx) => {
          attemptCount++;
          if (attemptCount === 1) {
            return res(ctx.status(500), ctx.json({ error: 'Server error' }));
          }
          return res(ctx.json({ data: articles }));
        })
      );

      // Act - Initial render (fails)
      renderWithQueryClient(<ArticleList />);
      await waitFor(() => {
        expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
      });

      // Act - Click retry
      await userEvent.click(screen.getByRole('button', { name: /retry/i }));

      // Assert - Articles displayed after retry
      await waitFor(() => {
        expect(screen.getByText(articles[0].title)).toBeInTheDocument();
      });
    });
  });
});
```

### E2E Test Example

```typescript
// __tests__/e2e/reading-list/add-article.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Add Article to Reading List', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/articles');
  });

  test('user can add article to reading list from article card', async ({ page }) => {
    // Arrange - Navigate to articles page
    await page.goto('/articles');
    await page.waitForSelector('[data-testid="article-card"]');

    // Act - Click save button on first article
    const firstArticle = page.locator('[data-testid="article-card"]').first();
    const articleTitle = await firstArticle.locator('h3').textContent();
    await firstArticle.locator('[data-testid="save-button"]').click();

    // Assert - Success toast appears
    await expect(page.locator('[data-testid="success-toast"]')).toBeVisible();
    await expect(page.locator('[data-testid="success-toast"]')).toContainText(
      'Added to reading list'
    );

    // Assert - Article appears in reading list
    await page.goto('/reading-list');
    await expect(page.locator('h3', { hasText: articleTitle })).toBeVisible();
  });

  test('user can remove article from reading list', async ({ page }) => {
    // Arrange - Add article first
    await page.goto('/articles');
    const firstArticle = page.locator('[data-testid="article-card"]').first();
    const articleTitle = await firstArticle.locator('h3').textContent();
    await firstArticle.locator('[data-testid="save-button"]').click();
    await expect(page.locator('[data-testid="success-toast"]')).toBeVisible();

    // Act - Navigate to reading list and remove article
    await page.goto('/reading-list');
    const savedArticle = page.locator('h3', { hasText: articleTitle }).locator('..');
    await savedArticle.locator('[data-testid="remove-button"]').click();

    // Assert - Article removed
    await expect(page.locator('[data-testid="success-toast"]')).toContainText(
      'Removed from reading list'
    );
    await expect(page.locator('h3', { hasText: articleTitle })).not.toBeVisible();
  });

  test('user cannot add same article twice', async ({ page }) => {
    // Arrange - Add article first time
    await page.goto('/articles');
    const firstArticle = page.locator('[data-testid="article-card"]').first();
    await firstArticle.locator('[data-testid="save-button"]').click();
    await expect(page.locator('[data-testid="success-toast"]')).toBeVisible();

    // Act - Try to add same article again
    await firstArticle.locator('[data-testid="save-button"]').click();

    // Assert - Info message appears
    await expect(page.locator('[data-testid="info-toast"]')).toBeVisible();
    await expect(page.locator('[data-testid="info-toast"]')).toContainText(
      'Already in reading list'
    );
  });
});
```

### Property Test Example

```typescript
// __tests__/property/api/api-client-singleton.property.test.ts

import fc from 'fast-check';
import ApiClient from '@/lib/api/client';

describe('API Client Properties', () => {
  describe('Property 1: API Client Singleton', () => {
    it('always returns same instance across all calls', () => {
      /**
       * **Property 1: API Client Singleton**
       *
       * For any sequence of API client instantiation calls,
       * all instances SHALL reference the same underlying HTTP client object.
       *
       * **Validates: Requirements 1.1**
       */
      fc.assert(
        fc.property(fc.nat(100), (callCount) => {
          // Generate multiple getInstance calls
          const instances = Array.from({ length: callCount + 1 }, () => ApiClient.getInstance());

          // All instances should be the same object
          const firstInstance = instances[0];
          return instances.every((instance) => instance === firstInstance);
        }),
        { numRuns: 100 }
      );
    });

    it('returns same axios instance across all calls', () => {
      /**
       * Verify that the underlying axios instance is also shared.
       */
      fc.assert(
        fc.property(fc.nat(50), () => {
          const client1 = ApiClient.getInstance();
          const client2 = ApiClient.getInstance();
          const axios1 = client1.getAxiosInstance();
          const axios2 = client2.getAxiosInstance();

          return axios1 === axios2;
        }),
        { numRuns: 50 }
      );
    });
  });

  describe('Property 15: Request Interceptor Execution', () => {
    it('executes all interceptors in registration order', () => {
      /**
       * **Property 15: Request Interceptor Execution**
       *
       * For any API request made through the unified client,
       * all registered request interceptors SHALL execute in order
       * before the request is sent.
       *
       * **Validates: Requirements 1.3**
       */
      fc.assert(
        fc.property(fc.array(fc.string(), { minLength: 1, maxLength: 5 }), (interceptorNames) => {
          const client = ApiClient.getInstance();
          const executionOrder: string[] = [];

          // Register interceptors
          interceptorNames.forEach((name) => {
            client.addRequestInterceptor({
              onFulfilled: (config) => {
                executionOrder.push(name);
                return config;
              },
            });
          });

          // Make a request (mocked)
          // Verify execution order matches registration order
          return executionOrder.every((name, index) => name === interceptorNames[index]);
        }),
        { numRuns: 50 }
      );
    });
  });
});
```

---

## Quick Reference

### File Naming

| Test Type   | Pattern                      | Example                                 |
| ----------- | ---------------------------- | --------------------------------------- |
| Unit        | `{ComponentName}.test.tsx`   | `ArticleCard.test.tsx`                  |
| Unit        | `{moduleName}.test.ts`       | `format-date.test.ts`                   |
| Integration | `{feature-name}.test.tsx`    | `article-list.test.tsx`                 |
| E2E         | `{workflow-name}.spec.ts`    | `add-article.spec.ts`                   |
| Property    | `{feature}.property.test.ts` | `api-client-singleton.property.test.ts` |

### Describe Block Naming

| Pattern                                 | Example                                    |
| --------------------------------------- | ------------------------------------------ |
| `describe('{Component}', ...)`          | `describe('ArticleCard', ...)`             |
| `describe('when {condition}', ...)`     | `describe('when article is loading', ...)` |
| `describe('Property {N}: {name}', ...)` | `describe('Property 1: Singleton', ...)`   |

### Test Case Naming

| Pattern                                | Example                                      |
| -------------------------------------- | -------------------------------------------- |
| `it('{action} {result}', ...)`         | `it('renders article title', ...)`           |
| `it('{action} when {condition}', ...)` | `it('displays error when fetch fails', ...)` |
| `it('always {property}', ...)`         | `it('always returns same instance', ...)`    |

---

## Checklist for Writing Tests

When writing a new test, ensure:

- [ ] File name follows conventions (PascalCase for components, kebab-case for utilities)
- [ ] File has correct suffix (`.test.tsx`, `.test.ts`, `.spec.ts`, `.property.test.ts`)
- [ ] Top-level `describe` matches component/module name
- [ ] Nested `describe` blocks use "when {condition}" pattern
- [ ] Test cases start with action verbs (renders, displays, calls, etc.)
- [ ] Test cases describe expected behavior, not implementation
- [ ] Tests follow AAA pattern (Arrange-Act-Assert)
- [ ] Property tests include property number and validation statement
- [ ] Tests use shared utilities from `@/__tests__/utils`
- [ ] Tests are in correct directory (unit/integration/e2e/property)

---

## Additional Resources

- [Frontend Test README](./README.md) - Comprehensive test organization guide
- [Organization Guide](./ORGANIZATION_GUIDE.md) - Where to place tests
- [Testing Library Documentation](https://testing-library.com/docs/react-testing-library/intro/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Playwright Documentation](https://playwright.dev/docs/intro)
- [fast-check Documentation](https://fast-check.dev/)

---

**Last Updated:** 2024-01-XX
**Maintained By:** Tech News Agent Team
**Related:** Requirements 9.4, Tasks 14.3
