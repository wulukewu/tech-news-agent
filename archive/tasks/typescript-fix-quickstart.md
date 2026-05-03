# TypeScript Errors Fix - Quick Start Guide

## Quick Reference

This is a condensed guide for quickly fixing TypeScript errors. For detailed explanations, see [typescript-errors-fix-plan.md](./typescript-errors-fix-plan.md).

## Before You Start

1. **Check current errors**:

```bash
./scripts/check-typescript-errors.sh
```

2. **Or run full type check**:

```bash
cd frontend && npm run type-check
```

## Priority Order

Fix in this order for fastest deployment:

1. ✅ **P0**: Production code (already mostly fixed)
2. 🔄 **P1**: Common components (start here)
3. ⏳ **P2**: Utilities
4. 📝 **P3**: Examples (can skip for now)

---

## Quick Fixes

### 1. Create Type Declaration Files

Create these files to fix external API types:

**`frontend/types/gtag.d.ts`**:

```typescript
interface Window {
  gtag?: (
    command: 'event' | 'config' | 'set',
    targetId: string,
    config?: Record<string, any>
  ) => void;
}
```

**`frontend/types/background-sync.d.ts`**:

```typescript
interface SyncManager {
  register(tag: string): Promise<void>;
  getTags(): Promise<string[]>;
}

interface ServiceWorkerRegistration {
  readonly sync?: SyncManager;
}
```

### 2. Add Missing Type Export

**`frontend/components/ui/drag-drop-list.tsx`** - Add at top:

```typescript
export interface DragDropItem {
  id: string;
  content: React.ReactNode;
  disabled?: boolean;
}
```

**`frontend/components/ui/index.ts`** - Add to exports:

```typescript
export type { DragDropItem } from './drag-drop-list';
```

### 3. Create Mock Response Helper

**`frontend/lib/api/test-helpers.ts`** - New file:

```typescript
import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios';

export function createMockAxiosResponse<T>(data: T): AxiosResponse<T> {
  return {
    data,
    status: 200,
    statusText: 'OK',
    headers: {},
    config: {
      headers: {} as any,
    } as InternalAxiosRequestConfig,
  };
}
```

### 4. Update Example Files

Replace `as any` casts in example files with proper helper:

**`frontend/lib/api/examples/enhanced-features-example.ts`**:

```typescript
import { createMockAxiosResponse } from '../test-helpers';

// Replace fallbacks like this:
fallback: () => createMockAxiosResponse({
  data: [],
  pagination: {
    page: 1,
    page_size: 20,
    total_count: 0,
    has_next: false,
    has_previous: false,
  },
}),
```

### 5. Remove `as any` Casts

**Find all `as any` casts**:

```bash
cd frontend
grep -r "as any" --include="*.ts" --include="*.tsx" | grep -v node_modules | grep -v ".next"
```

**Replace with proper types** using the helpers above.

---

## Testing After Each Fix

```bash
# 1. Type check specific file
cd frontend
npx tsc --noEmit path/to/file.tsx

# 2. Type check all
npm run type-check

# 3. Build test
npm run build

# 4. If all pass, commit
git add .
git commit -m "fix: resolve TypeScript errors in [component/file name]"
```

---

## Re-enable Type Checking

Once all P0-P1 errors are fixed, update `frontend/next.config.js`:

```javascript
const nextConfig = {
  // Remove or set to false
  typescript: {
    ignoreBuildErrors: false, // ✅ Re-enable
  },
  eslint: {
    ignoreDuringBuilds: false, // ✅ Re-enable
  },
  // ... rest of config
};
```

---

## Common Patterns

### Pattern 1: Window API Types

```typescript
// ❌ Bad
if (window.gtag) { ... }

// ✅ Good (after adding type declaration)
if (typeof window !== 'undefined' && window.gtag) { ... }
```

### Pattern 2: Error Message Props

```typescript
// ❌ Bad
<ErrorMessage error={error} />

// ✅ Good
<ErrorMessage message={error.message || 'An error occurred'} />
```

### Pattern 3: Generic Component Types

```typescript
// ❌ Bad
<List itemData={data} />

// ✅ Good
<List<MyDataType> itemData={data} />
```

### Pattern 4: API Response Types

```typescript
// ❌ Bad
async function fetchData(): Promise<void> {
  return apiClient.get('/data'); // Returns AxiosResponse
}

// ✅ Good
async function fetchData(): Promise<void> {
  await apiClient.get('/data');
}
```

---

## Verification Checklist

Before considering the task complete:

- [ ] Run `./scripts/check-typescript-errors.sh` - no errors
- [ ] Run `npm run type-check` - passes
- [ ] Run `npm run build` - succeeds
- [ ] Run `npm run lint` - passes
- [ ] Test in browser - no runtime errors
- [ ] Check bundle size - no significant increase
- [ ] Update `next.config.js` - remove `ignoreBuildErrors`
- [ ] Final build test - succeeds without ignoring errors

---

## Time Estimates

| Task                     | Time    |
| ------------------------ | ------- |
| Create type declarations | 10 min  |
| Add missing exports      | 10 min  |
| Create helper functions  | 15 min  |
| Fix P0-P1 errors         | 1 hour  |
| Fix P2 errors            | 1 hour  |
| Fix P3 errors (optional) | 2 hours |
| Testing & verification   | 30 min  |

**Minimum viable fix**: ~1.5 hours (P0-P1 only)
**Complete fix**: ~4 hours (all priorities)

---

## Need Help?

- **Detailed plan**: See [typescript-errors-fix-plan.md](./typescript-errors-fix-plan.md)
- **Check errors**: Run `./scripts/check-typescript-errors.sh`
- **TypeScript docs**: https://www.typescriptlang.org/docs/
- **Next.js TypeScript**: https://nextjs.org/docs/basic-features/typescript

---

## Example Commit Messages

```bash
# For type declarations
git commit -m "fix: add type declarations for window.gtag and background sync API"

# For component fixes
git commit -m "fix: resolve ErrorMessage prop type mismatches"

# For utility fixes
git commit -m "fix: add proper types to VirtualizedList component"

# For re-enabling checks
git commit -m "chore: re-enable TypeScript and ESLint build checks"
```
