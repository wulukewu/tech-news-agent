# Frontend Test Organization Guide

## Quick Start

This guide helps you understand where to place new tests and how to organize them.

## Decision Tree: Where Should My Test Go?

```
┌─────────────────────────────────────────────────────────────┐
│  What are you testing?                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┬─────────────┐
                │             │             │             │
        ┌───────▼──────┐ ┌───▼────┐ ┌─────▼─────┐ ┌────▼─────┐
        │ Single Unit  │ │Multiple│ │ Full User │ │Universal │
        │ (Function,   │ │ Units  │ │ Workflow  │ │ Property │
        │  Component,  │ │Working │ │ (Browser) │ │ (All     │
        │  Hook)       │ │Together│ │           │ │  Inputs) │
        └───────┬──────┘ └───┬────┘ └─────┬─────┘ └────┬─────┘
                │            │            │            │
        ┌───────▼──────┐ ┌──▼─────┐ ┌───▼──────┐ ┌───▼──────┐
        │ unit/        │ │integra-│ │ e2e/     │ │property/ │
        │              │ │tion/   │ │          │ │          │
        └──────────────┘ └────────┘ └──────────┘ └──────────┘
```

## Test Type Selection Guide

### Use `unit/` when:

- ✅ Testing a single component in isolation
- ✅ Testing a single function or utility
- ✅ Testing a single hook
- ✅ All dependencies are mocked
- ✅ Test runs in < 100ms
- ✅ No external services needed

**Example:** Testing if `ArticleCard` renders title correctly

### Use `integration/` when:

- ✅ Testing multiple components together
- ✅ Testing data flow between modules
- ✅ Testing state management with components
- ✅ Testing API client with React Query
- ✅ Some real implementations (not all mocked)
- ✅ Test runs in 1-5 seconds

**Example:** Testing article list fetching and displaying with React Query

### Use `e2e/` when:

- ✅ Testing complete user workflows
- ✅ Testing across multiple pages
- ✅ Testing critical business paths
- ✅ Need real browser environment
- ✅ Testing authentication flows
- ✅ Test runs in 10+ seconds

**Example:** User logs in, browses articles, adds to reading list, marks as read

### Use `property/` when:

- ✅ Testing universal properties
- ✅ Need to test with many random inputs
- ✅ Testing mathematical properties
- ✅ Testing invariants
- ✅ Exploring bug conditions
- ✅ Verifying bug fixes don't break other cases

**Example:** API client always returns same instance (singleton property)

## Directory Structure by Feature

### API Tests

```
__tests__/
├── unit/api/
│   ├── client.test.ts           # API client unit tests
│   ├── errors.test.ts           # Error handling tests
│   └── retry.test.ts            # Retry logic tests
├── integration/api/
│   └── client-with-query.test.tsx  # API + React Query integration
└── property/api/
    ├── client.property.test.ts     # Singleton property
    └── logger.property.test.ts     # Log batching property
```

### Component Tests

```
__tests__/
├── unit/components/
│   ├── ArticleCard.test.tsx     # ArticleCard unit tests
│   ├── FeedCard.test.tsx        # FeedCard unit tests
│   └── Navigation.test.tsx      # Navigation unit tests
├── integration/features/
│   └── article-list.test.tsx    # Article list with data fetching
└── e2e/articles/
    └── browsing.spec.ts         # Full article browsing workflow
```

### State Management Tests

```
__tests__/
├── unit/contexts/
│   ├── AuthContext.test.tsx     # Auth context unit tests
│   └── UserContext.test.tsx     # User context unit tests
├── integration/state/
│   └── auth-flow.test.tsx       # Auth context + components
└── property/state/
    └── context-isolation.property.test.tsx  # Context isolation property
```

### Hook Tests

```
__tests__/
├── unit/hooks/
│   ├── useArticles.test.tsx     # useArticles hook tests
│   └── useAuth.test.tsx         # useAuth hook tests
└── integration/workflows/
    └── article-workflow.test.tsx  # Hooks + components together
```

## File Naming Patterns

### Unit Tests

```
{ComponentName}.test.tsx
{functionName}.test.ts
{hookName}.test.tsx
```

Examples:

- `ArticleCard.test.tsx`
- `formatDate.test.ts`
- `useArticles.test.tsx`

### Integration Tests

```
{feature-name}.integration.test.tsx
{workflow-name}.test.tsx
```

Examples:

- `article-list.integration.test.tsx`
- `auth-flow.test.tsx`

### E2E Tests

```
{workflow-name}.spec.ts
{user-journey}.spec.ts
```

Examples:

- `article-browsing.spec.ts`
- `user-registration.spec.ts`

### Property Tests

```
{property-name}.property.test.ts
{module}-{property}.property.test.ts
```

Examples:

- `api-client-singleton.property.test.ts`
- `context-isolation.property.test.tsx`

## Common Scenarios

### Scenario 1: New React Component

**Question:** I created a new `ArticleCard` component. Where do I put tests?

**Answer:**

1. **Unit test** in `unit/components/ArticleCard.test.tsx`
   - Test rendering with different props
   - Test user interactions (clicks, hovers)
   - Test edge cases (null data, missing fields)

2. **Integration test** (optional) in `integration/features/article-display.test.tsx`
   - Test ArticleCard with real data fetching
   - Test ArticleCard with reading list actions

3. **E2E test** (optional) in `e2e/articles/article-interaction.spec.ts`
   - Test complete user flow involving ArticleCard

### Scenario 2: New API Endpoint

**Question:** I added a new API endpoint for fetching articles. Where do I test it?

**Answer:**

1. **Unit test** in `unit/api/articles.test.ts`
   - Test request formatting
   - Test response parsing
   - Test error handling

2. **Integration test** in `integration/api/articles-with-cache.test.tsx`
   - Test API + React Query caching
   - Test API + component integration

3. **Property test** (optional) in `property/api/articles-response.property.test.ts`
   - Test response structure consistency
   - Test pagination properties

### Scenario 3: New Custom Hook

**Question:** I created a `useArticleFilters` hook. Where do I test it?

**Answer:**

1. **Unit test** in `unit/hooks/useArticleFilters.test.tsx`
   - Test hook logic in isolation
   - Test state updates
   - Test return values

2. **Integration test** in `integration/features/article-filtering.test.tsx`
   - Test hook with components
   - Test hook with API calls

### Scenario 4: Bug Fix

**Question:** I fixed a bug where undefined article IDs crashed the app. How do I test it?

**Answer:**

1. **Property test** in `property/bugfix/undefined-article-id.property.test.ts`
   - Exploration test: Verify bug exists in unfixed code
   - Preservation test: Verify fix works and doesn't break valid cases

2. **Unit test** in `unit/components/ArticleCard.test.tsx`
   - Add specific test case for undefined ID

### Scenario 5: User Workflow

**Question:** I need to test the complete "add article to reading list" workflow. Where?

**Answer:**

1. **E2E test** in `e2e/reading-list/add-article.spec.ts`
   - Test complete user journey
   - Navigate, click, verify

2. **Integration test** (optional) in `integration/workflows/reading-list.test.tsx`
   - Test workflow without browser
   - Faster feedback

## Test Organization Checklist

When adding a new test, ask yourself:

- [ ] Is this testing a single unit? → `unit/`
- [ ] Is this testing multiple units together? → `integration/`
- [ ] Is this testing a complete user workflow? → `e2e/`
- [ ] Is this testing a universal property? → `property/`
- [ ] Does the file name follow conventions?
- [ ] Is the test in the correct feature subdirectory?
- [ ] Am I using shared utilities from `@/__tests__/utils`?
- [ ] Does the test have clear describe blocks?
- [ ] Does the test have descriptive test names?

## Anti-Patterns to Avoid

### ❌ Don't: Mix test types in one file

```typescript
// Bad: mixing unit and integration tests
describe('ArticleCard', () => {
  it('renders title', () => {
    /* unit test */
  });
  it('fetches and displays data', () => {
    /* integration test */
  });
});
```

### ✅ Do: Separate by test type

```typescript
// unit/components/ArticleCard.test.tsx
describe('ArticleCard', () => {
  it('renders title', () => {
    /* unit test */
  });
});

// integration/features/article-display.test.tsx
describe('Article Display', () => {
  it('fetches and displays data', () => {
    /* integration test */
  });
});
```

### ❌ Don't: Create tests next to source files

```
components/
├── ArticleCard.tsx
└── ArticleCard.test.tsx  ❌ Wrong location
```

### ✅ Do: Use centralized test directory

```
__tests__/
└── unit/
    └── components/
        └── ArticleCard.test.tsx  ✅ Correct location
```

### ❌ Don't: Import from multiple utility files

```typescript
import { render } from '@testing-library/react';
import { mockArticle } from '../mocks';
import { createTestQueryClient } from '../utils/query';
```

### ✅ Do: Import from centralized utils

```typescript
import { render, mockArticle, createTestQueryClient } from '@/__tests__/utils';
```

## Quick Commands

```bash
# Create new unit test
touch __tests__/unit/{module}/{name}.test.ts

# Create new integration test
touch __tests__/integration/{feature}/{name}.test.tsx

# Create new E2E test
touch __tests__/e2e/{feature}/{workflow}.spec.ts

# Create new property test
touch __tests__/property/{module}/{property}.property.test.ts

# Run tests for specific module
npm test -- __tests__/unit/api/
npm test -- __tests__/integration/features/
npx playwright test __tests__/e2e/articles/
```

## Summary

| Test Type       | Location       | Speed     | Scope          | When to Use                                     |
| --------------- | -------------- | --------- | -------------- | ----------------------------------------------- |
| **Unit**        | `unit/`        | ⚡ Fast   | Single unit    | Testing isolated components, functions, hooks   |
| **Integration** | `integration/` | ⏱️ Medium | Multiple units | Testing component interactions, data flow       |
| **E2E**         | `e2e/`         | 🐌 Slow   | Full workflow  | Testing critical user paths, complete journeys  |
| **Property**    | `property/`    | ⚡ Fast   | Universal      | Testing properties, invariants, bug exploration |

## Need Help?

- See [README.md](./README.md) for comprehensive test guide
- See [TEST_STRUCTURE.md](./TEST_STRUCTURE.md) for detailed structure visualization
- Check existing tests in each directory for examples
- Ask team members for guidance on test placement
