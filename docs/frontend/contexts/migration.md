# Migration Guide: Split Context Architecture

This guide helps you migrate from the old monolithic `AuthContext` to the new split context architecture.

## Overview of Changes

The old `AuthContext` has been split into three focused contexts:

| Old Context   | New Contexts   | Responsibility                                                      |
| ------------- | -------------- | ------------------------------------------------------------------- |
| `AuthContext` | `AuthContext`  | Authentication state only (isAuthenticated, loading, login, logout) |
|               | `UserContext`  | User profile data (user object with id, username, avatar)           |
|               | `ThemeContext` | Theme preferences (light/dark mode)                                 |

## Why Split Contexts?

**Performance:** Components only re-render when their specific context changes.

**Example:**

- Before: Changing theme → ALL components using `useAuth()` re-render
- After: Changing theme → ONLY components using `useTheme()` re-render

## Step-by-Step Migration

### Step 1: Update Provider Setup

**Before:**

```tsx
// app/layout.tsx
import { AuthProvider } from '@/contexts/AuthContext';

<AuthProvider>{children}</AuthProvider>;
```

**After:**

```tsx
// app/layout.tsx
import { AuthProvider, UserProvider } from '@/contexts';
// ThemeProvider already exists from next-themes

<AuthProvider>
  <UserProvider>{children}</UserProvider>
</AuthProvider>;
```

**Note:** `UserProvider` must be nested inside `AuthProvider` because it depends on authentication state.

### Step 2: Update Component Imports

**Before:**

```tsx
import { useAuth } from '@/contexts/AuthContext';

function MyComponent() {
  const { isAuthenticated, user, logout } = useAuth();
  // ...
}
```

**After:**

```tsx
import { useAuth } from '@/contexts/AuthContext';
import { useUser } from '@/contexts/UserContext';

function MyComponent() {
  const { isAuthenticated, logout } = useAuth();
  const { user } = useUser();
  // ...
}
```

**Or use the centralized export:**

```tsx
import { useAuth, useUser } from '@/contexts';

function MyComponent() {
  const { isAuthenticated, logout } = useAuth();
  const { user } = useUser();
  // ...
}
```

### Step 3: Update Type Imports

**Before:**

```tsx
import { User, AuthContextType } from '@/types/auth';
```

**After:**

```tsx
import { AuthContextType } from '@/contexts/AuthContext';
import { User, UserContextType } from '@/contexts/UserContext';
```

**Or use the centralized export:**

```tsx
import { AuthContextType, User, UserContextType } from '@/contexts';
```

### Step 4: Update Test Mocks

**Before:**

```tsx
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    isAuthenticated: true,
    user: mockUser,
    logout: jest.fn(),
  })),
}));
```

**After:**

```tsx
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    isAuthenticated: true,
    logout: jest.fn(),
  })),
}));

jest.mock('@/contexts/UserContext', () => ({
  useUser: jest.fn(() => ({
    user: mockUser,
    loading: false,
    refreshUser: jest.fn(),
  })),
}));
```

## Common Migration Patterns

### Pattern 1: Authentication Check Only

If you only check authentication status:

**Before:**

```tsx
function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuth();
  // ...
}
```

**After:**

```tsx
// No changes needed! ✅
function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuth();
  // ...
}
```

### Pattern 2: Display User Profile

If you display user information:

**Before:**

```tsx
function UserProfile() {
  const { user } = useAuth();
  return <div>{user?.username}</div>;
}
```

**After:**

```tsx
import { useUser } from '@/contexts/UserContext';

function UserProfile() {
  const { user } = useUser();
  return <div>{user?.username}</div>;
}
```

### Pattern 3: Authentication + User Data

If you need both authentication and user data:

**Before:**

```tsx
function Dashboard() {
  const { isAuthenticated, user, logout } = useAuth();
  // ...
}
```

**After:**

```tsx
import { useAuth } from '@/contexts/AuthContext';
import { useUser } from '@/contexts/UserContext';

function Dashboard() {
  const { isAuthenticated, logout } = useAuth();
  const { user } = useUser();
  // ...
}
```

### Pattern 4: Refresh User Data

If you need to refresh user data after updates:

**Before:**

```tsx
function ProfileEditor() {
  const { checkAuth } = useAuth();

  const handleSave = async () => {
    await updateProfile();
    await checkAuth(); // Refresh user data
  };
}
```

**After:**

```tsx
import { useUser } from '@/contexts/UserContext';

function ProfileEditor() {
  const { refreshUser } = useUser();

  const handleSave = async () => {
    await updateProfile();
    await refreshUser(); // Refresh user data
  };
}
```

## API Reference

### AuthContext

```tsx
interface AuthContextType {
  isAuthenticated: boolean;
  loading: boolean;
  login: () => void;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}
```

**Usage:**

```tsx
const { isAuthenticated, loading, login, logout, checkAuth } = useAuth();
```

### UserContext

```tsx
interface UserContextType {
  user: User | null;
  loading: boolean;
  refreshUser: () => Promise<void>;
}

interface User {
  id: string;
  discordId: string;
  username?: string;
  avatar?: string;
}
```

**Usage:**

```tsx
const { user, loading, refreshUser } = useUser();
```

### ThemeContext

```tsx
interface ThemeContextType {
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: Theme) => void;
  resolvedTheme: 'light' | 'dark';
}
```

**Usage:**

```tsx
const { theme, setTheme, resolvedTheme } = useTheme();
```

## Checklist

Use this checklist to ensure complete migration:

- [ ] Updated provider setup in `app/layout.tsx`
- [ ] Updated all component imports
- [ ] Updated all type imports
- [ ] Updated all test mocks
- [ ] Verified no TypeScript errors
- [ ] Ran all tests and verified they pass
- [ ] Tested authentication flow manually
- [ ] Tested user profile display
- [ ] Tested logout functionality
- [ ] Verified no unnecessary re-renders (use React DevTools Profiler)

## Troubleshooting

### Error: "useUser must be used within UserProvider"

**Cause:** Component is trying to use `useUser()` but `UserProvider` is not in the component tree.

**Solution:** Ensure `UserProvider` is added to your layout:

```tsx
<AuthProvider>
  <UserProvider>{children}</UserProvider>
</AuthProvider>
```

### User data is null even when authenticated

**Cause:** `UserProvider` is not nested inside `AuthProvider`.

**Solution:** Ensure correct nesting order:

```tsx
// ✅ Correct
<AuthProvider>
  <UserProvider>
    {children}
  </UserProvider>
</AuthProvider>

// ❌ Wrong
<UserProvider>
  <AuthProvider>
    {children}
  </AuthProvider>
</UserProvider>
```

### Components re-rendering unnecessarily

**Cause:** Component is using `useAuth()` when it only needs user data.

**Solution:** Use the minimal context:

```tsx
// ❌ Bad: Will re-render on auth changes
function UserAvatar() {
  const { user } = useAuth();
  return <img src={user?.avatar} />;
}

// ✅ Good: Only re-renders on user data changes
function UserAvatar() {
  const { user } = useUser();
  return <img src={user?.avatar} />;
}
```

### TypeScript errors after migration

**Cause:** Old type imports are still being used.

**Solution:** Update type imports:

```tsx
// ❌ Old
import { User, AuthContextType } from '@/types/auth';

// ✅ New
import { AuthContextType } from '@/contexts/AuthContext';
import { User, UserContextType } from '@/contexts/UserContext';

// ✅ Or use centralized export
import { AuthContextType, User, UserContextType } from '@/contexts';
```

## Performance Verification

After migration, verify performance improvements:

1. **Open React DevTools Profiler**
2. **Start recording**
3. **Perform actions:**
   - Change theme
   - Update user profile
   - Login/logout
4. **Check which components re-rendered**

**Expected results:**

- Theme change → Only components using `useTheme()` re-render
- User data update → Only components using `useUser()` re-render
- Auth status change → Only components using `useAuth()` re-render

## Rollback Plan

If you need to rollback:

1. **Revert provider setup** in `app/layout.tsx`
2. **Revert component imports** to use old `useAuth()`
3. **Restore old `AuthContext.tsx`** from git history
4. **Run tests** to verify everything works

```bash
# Restore old AuthContext
git checkout HEAD~1 -- frontend/contexts/AuthContext.tsx

# Revert layout changes
git checkout HEAD~1 -- frontend/app/layout.tsx
```

## Questions?

If you encounter issues not covered in this guide:

1. Check the [README.md](./README.md) for detailed context documentation
2. Review the [test files](./tests/) for usage examples
3. Ask the team for help

## Summary

The split context architecture provides:

✅ **Better performance** - Fewer unnecessary re-renders
✅ **Clearer responsibilities** - Each context has a single purpose
✅ **Easier testing** - Mock only what you need
✅ **Better developer experience** - Clearer API surface

The migration is straightforward and can be done incrementally, one component at a time.
