# Frontend Test Structure Visualization

## Directory Tree

```
frontend/__tests__/
│
├── 📄 README.md                          # Comprehensive test guide
├── 📄 MIGRATION_SUMMARY.md              # Migration documentation
├── 📄 TEST_STRUCTURE.md                 # This file
│
├── 🛠️  utils/                            # Shared Test Utilities
│   ├── index.ts                         # Central export point
│   ├── test-utils.tsx                   # React Testing Library setup
│   ├── render.tsx                       # Custom render functions
│   └── mocks.ts                         # Mock data factories
│
├── 🧪 unit/                              # Unit Tests (Isolated, Fast)
│   │
│   ├── api/                             # API Client Tests
│   │   ├── api-client.test.ts          # ✅ Singleton pattern tests
│   │   ├── api-client-advanced.test.ts # ✅ Advanced client features
│   │   └── api-validation.test.ts      # ✅ Request/response validation
│   │
│   ├── hooks/                           # React Hooks Tests
│   │   └── react-query-hooks.test.tsx  # ✅ React Query hooks
│   │
│   ├── contexts/                        # Context Provider Tests
│   │   └── (ready for context tests)
│   │
│   ├── components/                      # Component Unit Tests
│   │   └── (ready for component tests)
│   │
│   └── lib/                             # Utility Function Tests
│       └── (ready for utility tests)
│
├── 🔗 integration/                       # Integration Tests (Multiple Components)
│   │
│   ├── api/                             # API Integration Tests
│   │   └── (ready for API integration)
│   │
│   ├── state/                           # State Management Integration
│   │   └── (ready for state tests)
│   │
│   ├── features/                        # Feature Integration Tests
│   │   └── (ready for feature tests)
│   │
│   └── workflows/                       # Multi-Step Workflow Tests
│       └── (ready for workflow tests)
│
├── 🌐 e2e/                               # End-to-End Tests (Full User Flows)
│   │
│   ├── basic.spec.ts                    # ✅ Basic smoke tests
│   │
│   ├── auth/                            # Authentication Flows
│   │   └── (ready for auth flows)
│   │
│   ├── articles/                        # Article Browsing Flows
│   │   └── (ready for article flows)
│   │
│   ├── reading-list/                    # Reading List Management
│   │   └── (ready for reading list flows)
│   │
│   └── feeds/                           # Feed Subscription Flows
│       └── (ready for feed flows)
│
└── 🎲 property/                          # Property-Based Tests (Universal Properties)
    │
    ├── api/                             # API Property Tests
    │   ├── api-client.property.test.ts # ✅ Singleton & interceptor properties
    │   ├── logger.property.test.ts     # ✅ Log batching properties
    │   └── migration-backward-compatibility.property.test.ts # ✅ Migration properties
    │
    ├── state/                           # State Management Properties
    │   └── (ready for state properties)
    │
    └── bugfix/                          # Bug Exploration & Preservation
        ├── bugfix-exploration-undefined-article-id.test.ts # ✅ Undefined ID bug
        ├── bugfix-exploration.test.ts                      # ✅ General bug exploration
        ├── bugfix-preservation-valid-article-id.test.ts    # ✅ Valid ID preservation
        └── bugfix-preservation.test.tsx                    # ✅ Component bug preservation
```

## Test Type Distribution

### 🧪 Unit Tests (4 files, ~40 tests)

**Purpose**: Test individual functions, components, or hooks in isolation

**Characteristics**:

- ⚡ Fast execution (< 1 second)
- 🎯 Focused on single units
- 🔒 Mocked dependencies
- 📊 High edge case coverage

**Current Tests**:

- API Client singleton pattern
- API Client advanced features
- API request/response validation
- React Query hooks

### 🔗 Integration Tests (0 files, ready for expansion)

**Purpose**: Test multiple components working together

**Characteristics**:

- ⏱️ Moderate execution (1-5 seconds)
- 🔄 Real component interactions
- 💾 May use real caches/contexts
- 🌊 Focus on data flow

**Ready For**:

- API + State integration
- Context + Component integration
- Multi-hook workflows
- Cache invalidation flows

### 🌐 E2E Tests (1 file, 2 tests)

**Purpose**: Test complete user workflows from start to finish

**Characteristics**:

- 🐌 Slower execution (10+ seconds)
- 🌍 Full browser automation
- 👤 User-centric scenarios
- 🎯 Critical path focus

**Current Tests**:

- Login page loading
- Responsive navigation

**Ready For**:

- Complete authentication flows
- Article browsing and filtering
- Reading list management
- Feed subscription workflows

### 🎲 Property-Based Tests (7 files, ~79 tests)

**Purpose**: Test universal properties that should hold for all inputs

**Characteristics**:

- 🎰 Generated test cases
- 🔍 Exhaustive input coverage
- 📐 Mathematical properties
- 🐛 Bug exploration/preservation

**Current Tests**:

- API Client singleton property
- Request interceptor execution
- Frontend log batching
- Migration backward compatibility
- Bugfix exploration and preservation

## Test Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     npm test                                 │
│                                                              │
│  Runs: Unit + Integration + Property Tests                  │
│  Time: ~1.8 seconds                                          │
│  Tests: 121 passing                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ├─────────────────────────────────┐
                              │                                 │
                    ┌─────────▼─────────┐          ┌──────────▼──────────┐
                    │   Unit Tests      │          │  Property Tests     │
                    │   (Fast)          │          │  (Comprehensive)    │
                    │                   │          │                     │
                    │   • API Client    │          │   • Singleton       │
                    │   • Hooks         │          │   • Interceptors    │
                    │   • Validation    │          │   • Log Batching    │
                    │                   │          │   • Migration       │
                    │   ~40 tests       │          │   • Bugfix          │
                    │   < 1 second      │          │                     │
                    └───────────────────┘          │   ~79 tests         │
                                                   │   ~1 second         │
                                                   └─────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  npx playwright test                         │
│                                                              │
│  Runs: E2E Tests Only                                        │
│  Time: ~10-30 seconds                                        │
│  Tests: 2 passing                                            │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   E2E Tests       │
                    │   (Slow)          │
                    │                   │
                    │   • Login page    │
                    │   • Navigation    │
                    │                   │
                    │   2 tests         │
                    │   10-30 seconds   │
                    └───────────────────┘
```

## Shared Utilities Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    utils/index.ts                            │
│                  (Central Export Point)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
    ┌───────────▼──────────┐ │ ┌──────────▼──────────┐
    │   test-utils.tsx     │ │ │    render.tsx       │
    │                      │ │ │                     │
    │   • AllTheProviders  │ │ │   • createTestQC    │
    │   • customRender     │ │ │   • renderWithQC    │
    │   • QueryClient      │ │ │   • createWrapper   │
    │     setup            │ │ │   • waitForLoading  │
    └──────────────────────┘ │ └─────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   mocks.ts      │
                    │                 │
                    │   • mockArticle │
                    │   • mockUser    │
                    │   • mockFeed    │
                    │   • mockError   │
                    │   • factories   │
                    └─────────────────┘
```

## Import Patterns

### ✅ Recommended

```typescript
// Import from central utils
import { render, screen, waitFor } from '@/__tests__/utils';
import { mockArticle, mockUser } from '@/__tests__/utils';
import { renderWithQueryClient } from '@/__tests__/utils';

// Use in tests
describe('MyComponent', () => {
  it('should render article', () => {
    render(<ArticleCard article={mockArticle()} />);
    expect(screen.getByText('Test Article')).toBeInTheDocument();
  });
});
```

### ❌ Avoid

```typescript
// Don't import from individual files
import { render } from '@testing-library/react';
import { mockArticle } from '@/__tests__/utils/mocks';

// Don't create local test utilities
const createTestQueryClient = () => {
  /* ... */
};
```

## Coverage Goals

```
┌─────────────────────────────────────────────────────────────┐
│                    Coverage Targets                          │
├─────────────────────────────────────────────────────────────┤
│  Critical Paths:        ████████████████████░  80%+          │
│  Core Functionality:    ██████████████░░░░░░  70%+          │
│  Overall Codebase:      ████████████░░░░░░░░  60%+          │
└─────────────────────────────────────────────────────────────┘

Current Coverage:
  Branches:   70%
  Functions:  70%
  Lines:      70%
  Statements: 70%
```

## Test Naming Conventions

### File Names

```
unit/api/api-client.test.ts              # Unit test
integration/state/reading-list.test.tsx  # Integration test
e2e/auth/login-flow.spec.ts              # E2E test (Playwright)
property/api/client.property.test.ts     # Property test
```

### Test Suites

```typescript
// Unit test
describe('ApiClient', () => { ... });

// Integration test
describe('Reading List State Integration', () => { ... });

// E2E test
test('user can login and view articles', async ({ page }) => { ... });

// Property test
describe('Property: API Client Singleton', () => { ... });
```

## Quick Reference

### Run Specific Tests

```bash
# All tests
npm test

# Unit tests only
npm test -- __tests__/unit/

# Integration tests only
npm test -- __tests__/integration/

# Property tests only
npm test -- __tests__/property/

# E2E tests only
npx playwright test

# Specific feature
npm test -- __tests__/unit/api/
npm test -- __tests__/property/bugfix/

# With coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

### Add New Tests

```bash
# Unit test for new component
touch __tests__/unit/components/MyComponent.test.tsx

# Integration test for feature
touch __tests__/integration/features/my-feature.test.tsx

# E2E test for workflow
touch __tests__/e2e/articles/article-workflow.spec.ts

# Property test
touch __tests__/property/state/my-property.property.test.ts
```

## Benefits Summary

✅ **Clear Organization**: Tests organized by type and feature
✅ **Easy Navigation**: Find tests quickly by feature or type
✅ **Reusable Utilities**: Shared test helpers reduce duplication
✅ **Scalable Structure**: Easy to add new tests in appropriate locations
✅ **Consistent Patterns**: Same structure as backend tests
✅ **Fast Feedback**: Unit tests run in < 2 seconds
✅ **Comprehensive Coverage**: 121 tests covering critical paths

## Next Steps

1. **Add Component Tests**: Create unit tests for React components
2. **Add Integration Tests**: Test component + state interactions
3. **Expand E2E Tests**: Add critical user workflow tests
4. **Add Context Tests**: Test context providers and consumers
5. **Improve Coverage**: Target 80%+ coverage for critical paths
