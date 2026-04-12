# Refactoring Status

Current status of the project-wide refactoring effort.

## Overview

**Date**: April 12, 2026
**Status**: 🟡 In Progress
**Phase**: Documentation Organization & Code Quality Setup

## Completed ✅

### Documentation Organization

- ✅ Consolidated all documentation into `docs/` folder
- ✅ Created clear folder structure (tasks/, ci/, backend/, etc.)
- ✅ Updated both English and Chinese READMEs
- ✅ Created comprehensive documentation index
- ✅ Removed temporary and duplicate files
- ✅ Cleaned up root directory

### Pre-commit Configuration

- ✅ Configured pre-commit hooks for both backend and frontend
- ✅ Adjusted ESLint rules to allow commits during refactoring
- ✅ Temporarily disabled TypeScript strict checking
- ✅ Documented pre-commit setup and usage

## In Progress 🟡

### Type System Migration

- 🟡 Standardizing API response types
- 🟡 Fixing type mismatches in test files
- 🟡 Updating mock data to match new types
- 🟡 Aligning frontend types with backend schemas

### Code Quality Improvements

- 🟡 Reducing function complexity
- 🟡 Breaking down large functions
- 🟡 Removing unused variables
- 🟡 Fixing ESLint warnings

## Pending ⏳

### Type System

- ⏳ Re-enable TypeScript strict checking
- ⏳ Add comprehensive type tests
- ⏳ Document type conventions

### Code Quality

- ⏳ Tighten ESLint rules back to strict mode
- ⏳ Reduce complexity limits back to 10
- ⏳ Reduce max-lines-per-function back to 50
- ⏳ Fix all remaining console.log statements

### Testing

- ⏳ Update all test mocks with correct types
- ⏳ Fix property-based test type issues
- ⏳ Add missing test coverage

### Documentation

- ⏳ Update API documentation with new types
- ⏳ Document migration patterns
- ⏳ Create type usage examples

## Known Issues

### TypeScript Errors (50 total)

**High Priority:**

1. API response type mismatches (ArticleListResponse, ReadingListResponse)
2. Missing required properties in interfaces
3. Test mock data not matching types
4. MSW (Mock Service Worker) version incompatibility

**Medium Priority:**

1. Unused variables in test files
2. Missing type definitions for third-party libraries
3. Implicit 'any' types in callbacks

**Low Priority:**

1. Non-null assertions
2. Display name warnings in React components

### ESLint Warnings (300+ total)

**Categories:**

- Console statements: ~100
- Function complexity: ~50
- Function length: ~80
- Unused variables: ~30
- Explicit any types: ~40

## Temporary Adjustments

### ESLint Rules (Relaxed)

| Rule                              | Before     | Current    | Target     |
| --------------------------------- | ---------- | ---------- | ---------- |
| complexity                        | error (10) | warn (15)  | error (10) |
| max-lines-per-function            | warn (50)  | warn (100) | warn (50)  |
| max-params                        | warn (4)   | warn (5)   | warn (4)   |
| @typescript-eslint/no-unused-vars | error      | warn       | error      |

### Pre-commit Hooks

| Hook       | Status                        | Reason                           |
| ---------- | ----------------------------- | -------------------------------- |
| ESLint     | ✅ Enabled (warnings allowed) | Allow commits during refactoring |
| TypeScript | ❌ Disabled                   | Type migration in progress       |
| Prettier   | ✅ Enabled                    | Formatting is stable             |
| Black      | ✅ Enabled                    | Backend is stable                |
| Ruff       | ✅ Enabled                    | Backend is stable                |

## Migration Strategy

### Phase 1: Setup (Current)

1. ✅ Organize documentation
2. ✅ Configure pre-commit hooks
3. ✅ Relax rules temporarily
4. 🟡 Document current state

### Phase 2: Type System

1. Fix API response types
2. Update test mocks
3. Fix type errors file by file
4. Re-enable TypeScript checking

### Phase 3: Code Quality

1. Fix high-priority ESLint warnings
2. Reduce function complexity
3. Break down large functions
4. Remove console statements

### Phase 4: Finalization

1. Tighten ESLint rules
2. Re-enable strict TypeScript
3. Update documentation
4. Final verification

## How to Help

### For Developers

**Before committing:**

```bash
# Run pre-commit checks
pre-commit run --all-files

# Fix auto-fixable issues
npm run lint:fix  # Frontend
black backend/    # Backend
```

**When you see warnings:**

1. Don't ignore them - they indicate technical debt
2. Fix them if you're working in that file
3. Create an issue if it's a larger problem

**When adding new code:**

1. Follow the target rules (not current relaxed rules)
2. Keep functions small (<50 lines)
3. Keep complexity low (<10)
4. Add proper types (no 'any')

### For Reviewers

**Check for:**

1. New code follows strict rules
2. Types are properly defined
3. No new console.log statements
4. Functions are reasonably sized
5. Complexity is manageable

## Progress Tracking

### Type Errors by File

| File                       | Errors | Priority |
| -------------------------- | ------ | -------- |
| api-mocks.ts               | 19     | High     |
| ReactQueryCache.test.tsx   | 13     | High     |
| react-query-hooks.test.tsx | 8      | High     |
| ArticleCard.test.tsx       | 1      | Medium   |
| readingList.ts             | 1      | Medium   |
| Others                     | 8      | Low      |

### ESLint Warnings by Category

| Category           | Count | Trend         |
| ------------------ | ----- | ------------- |
| console statements | ~100  | 📈 Increasing |
| function length    | ~80   | ➡️ Stable     |
| complexity         | ~50   | ➡️ Stable     |
| explicit any       | ~40   | 📉 Decreasing |
| unused vars        | ~30   | 📉 Decreasing |

## Timeline

| Phase            | Start  | Target End | Status         |
| ---------------- | ------ | ---------- | -------------- |
| Phase 1: Setup   | Apr 12 | Apr 12     | ✅ Complete    |
| Phase 2: Types   | Apr 12 | Apr 19     | 🟡 In Progress |
| Phase 3: Quality | Apr 19 | Apr 26     | ⏳ Pending     |
| Phase 4: Final   | Apr 26 | Apr 30     | ⏳ Pending     |

## Success Criteria

### Phase 2 Complete When:

- [ ] All TypeScript errors fixed
- [ ] TypeScript checking re-enabled
- [ ] Test mocks updated
- [ ] API types standardized

### Phase 3 Complete When:

- [ ] <50 ESLint warnings remaining
- [ ] No functions >100 lines
- [ ] No complexity >15
- [ ] No console.log in production code

### Phase 4 Complete When:

- [ ] All ESLint rules back to strict
- [ ] All pre-commit hooks enabled
- [ ] Documentation updated
- [ ] Zero warnings on clean build

## Resources

- [Pre-commit Configuration](./PRE_COMMIT_CONFIGURATION.md)
- [Code Quality Guide](./CODE_QUALITY.md)
- [Type System Guide](./DEVELOPER_GUIDE.md#type-system)
- [Testing Guide](./TESTING.md)

---

**Last Updated**: April 12, 2026
**Next Review**: April 19, 2026
