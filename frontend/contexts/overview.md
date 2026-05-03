# Context Architecture Documentation

This directory contains the split context architecture for the Tech News Agent frontend. The contexts are designed to prevent unnecessary re-renders by separating concerns into focused, independent contexts.

## Architecture Overview

The application uses three separate contexts, each with a single, well-defined responsibility:

```
┌─────────────────────────────────────────────────────────────┐
│                      Application Root                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    AuthProvider                        │  │
│  │  (Authentication state: isAuthenticated, loading)     │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │              UserProvider                        │  │  │
│  │  │  (User profile: id, username, avatar)           │  │  │
│  │  │  ┌───────────────────────────────────────────┐  │  │  │
│  │  │  │          ThemeProvider                     │  │  │  │
│  │  │  │  (Theme: light, dark, system)             │  │  │  │
│  │  │  │  ┌─────────────────────────────────────┐  │  │  │  │
│  │  │  │  │        Application Content          │  │  │  │  │
│  │  │  │  └─────────────────────────────────────┘  │  │  │  │
│  │  │  └───────────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Context Responsibilities

### 1. AuthContext

**File:** `AuthContext.tsx`

**Responsibility:** Manages authentication state only.

**State:**

- `isAuthenticated: boolean` - Whether the user is authenticated
- `loading: boolean` - Whether authentication check is in progress

**Methods:**

- `login()` - Initiates Discord OAuth2 login flow
- `logout()` - Logs out the user and clears authentication state
- `checkAuth()` - Verifies JWT token validity

**When to use:**

- Checking if user is logged in
- Implementing login/logout buttons
- Protecting routes that require authentication
- Showing loading state during authentication check

**Example:**

```tsx
import { useAuth } from '@/contexts/AuthContext';

function LoginButton() {
  const { isAuthenticated, loading, login, logout } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (isAuthenticated) {
    return <button onClick={logout}>Logout</button>;
  }

  return <button onClick={login}>Login with Discord</button>;
}
```

### 2. UserContext

**File:** `UserContext.tsx`

**Responsibility:** Manages user profile data.

**State:**

- `user: User | null` - User profile information (id, discordId, username, avatar)
- `loading: boolean` - Whether user data is being fetched

**Methods:**

- `refreshUser()` - Manually refresh user data from the backend

**When to use:**

- Displaying user profile information (username, avatar)
- Accessing user ID for API calls
- Showing user-specific content
- Refreshing user data after profile updates

**Example:**

```tsx
import { useUser } from '@/contexts/UserContext';

function UserProfile() {
  const { user, loading, refreshUser } = useUser();

  if (loading) {
    return <div>Loading user data...</div>;
  }

  if (!user) {
    return <div>No user data available</div>;
  }

  return (
    <div>
      <img src={user.avatar} alt={user.username} />
      <h2>{user.username}</h2>
      <button onClick={refreshUser}>Refresh Profile</button>
    </div>
  );
}
```

### 3. ThemeContext

**File:** `ThemeContext.tsx`

**Responsibility:** Manages theme preferences (light/dark mode).

**State:**

- `theme: 'light' | 'dark' | 'system'` - Current theme preference
- `resolvedTheme: 'light' | 'dark'` - Actual theme being applied (resolves 'system' to light/dark)

**Methods:**

- `setTheme(theme)` - Changes the theme and persists to localStorage

**When to use:**

- Implementing theme toggle buttons
- Applying theme-specific styles
- Checking current theme for conditional rendering
- Respecting user's theme preference

**Example:**

```tsx
import { useTheme } from '@/contexts/ThemeContext';

function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme();

  return (
    <div>
      <p>Current theme: {theme}</p>
      <p>Applied theme: {resolvedTheme}</p>
      <button onClick={() => setTheme('light')}>Light</button>
      <button onClick={() => setTheme('dark')}>Dark</button>
      <button onClick={() => setTheme('system')}>System</button>
    </div>
  );
}
```

## Setup Instructions

### 1. Wrap your application with providers

In your root layout file (`app/layout.tsx`), wrap your application with all three providers in the correct order:

```tsx
import { AuthProvider } from '@/contexts/AuthContext';
import { UserProvider } from '@/contexts/UserContext';
import { ThemeProvider } from '@/contexts/ThemeProvider';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <UserProvider>
            <ThemeProvider>{children}</ThemeProvider>
          </UserProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
```

**Important:** The order matters!

- `AuthProvider` must be outermost because `UserProvider` depends on authentication state
- `UserProvider` should be inside `AuthProvider` to access `isAuthenticated`
- `ThemeProvider` is independent and can be placed anywhere, but conventionally goes innermost

### 2. Use hooks in components

Import and use the appropriate hook based on what data you need:

```tsx
// Only need authentication status
import { useAuth } from '@/contexts/AuthContext';
const { isAuthenticated } = useAuth();

// Only need user profile data
import { useUser } from '@/contexts/UserContext';
const { user } = useUser();

// Only need theme
import { useTheme } from '@/contexts/ThemeContext';
const { theme, setTheme } = useTheme();

// Need multiple contexts
import { useAuth } from '@/contexts/AuthContext';
import { useUser } from '@/contexts/UserContext';
const { isAuthenticated } = useAuth();
const { user } = useUser();
```

## Performance Benefits

### Problem: Single Monolithic Context

Before splitting, a single `AuthContext` contained all state:

```tsx
// Old approach - single context
const AuthContext = {
  isAuthenticated: boolean,
  user: User | null,
  theme: 'light' | 'dark',
  // ... other state
};
```

**Issue:** When ANY value changes (e.g., theme), ALL components using `useAuth()` re-render, even if they only care about `isAuthenticated`.

### Solution: Split Contexts

With split contexts, components only re-render when their specific context changes:

```tsx
// Component A: Only uses authentication
function ProtectedRoute() {
  const { isAuthenticated } = useAuth();
  // ✅ Only re-renders when isAuthenticated changes
  // ✅ Does NOT re-render when user data or theme changes
}

// Component B: Only uses user data
function UserProfile() {
  const { user } = useUser();
  // ✅ Only re-renders when user data changes
  // ✅ Does NOT re-render when auth status or theme changes
}

// Component C: Only uses theme
function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  // ✅ Only re-renders when theme changes
  // ✅ Does NOT re-render when auth status or user data changes
}
```

### Re-render Scope Comparison

| Scenario          | Old (Single Context)     | New (Split Contexts)                         |
| ----------------- | ------------------------ | -------------------------------------------- |
| User logs in      | All components re-render | Only components using `useAuth()` re-render  |
| User data updates | All components re-render | Only components using `useUser()` re-render  |
| Theme changes     | All components re-render | Only components using `useTheme()` re-render |

## Migration Guide

### From Old AuthContext

If you're migrating from the old monolithic `AuthContext`, follow these steps:

1. **Update imports:**

   ```tsx
   // Old
   import { useAuth } from '@/contexts/AuthContext';
   const { isAuthenticated, user, theme } = useAuth();

   // New
   import { useAuth } from '@/contexts/AuthContext';
   import { useUser } from '@/contexts/UserContext';
   import { useTheme } from '@/contexts/ThemeContext';
   const { isAuthenticated } = useAuth();
   const { user } = useUser();
   const { theme } = useTheme();
   ```

2. **Update provider setup:**

   ```tsx
   // Old
   <AuthProvider>
     {children}
   </AuthProvider>

   // New
   <AuthProvider>
     <UserProvider>
       <ThemeProvider>
         {children}
       </ThemeProvider>
     </UserProvider>
   </AuthProvider>
   ```

3. **Update type imports:**

   ```tsx
   // Old
   import { User, AuthContextType } from '@/types/auth';

   // New
   import { AuthContextType } from '@/contexts/AuthContext';
   import { User, UserContextType } from '@/contexts/UserContext';
   import { ThemeContextType } from '@/contexts/ThemeContext';
   ```

## Best Practices

### 1. Use the Minimal Context

Only import and use the context you actually need:

```tsx
// ❌ Bad: Using AuthContext just to get user data
function UserAvatar() {
  const { user } = useAuth(); // This will cause re-renders on auth changes
  return <img src={user?.avatar} />;
}

// ✅ Good: Using UserContext directly
function UserAvatar() {
  const { user } = useUser(); // Only re-renders on user data changes
  return <img src={user?.avatar} />;
}
```

### 2. Combine Contexts When Necessary

If a component truly needs multiple contexts, use them together:

```tsx
function UserDashboard() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { user, loading: userLoading } = useUser();
  const { theme } = useTheme();

  if (authLoading || userLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated || !user) {
    return <div>Please log in</div>;
  }

  return (
    <div className={theme === 'dark' ? 'dark-mode' : 'light-mode'}>
      <h1>Welcome, {user.username}!</h1>
    </div>
  );
}
```

### 3. Avoid Prop Drilling

Use contexts to avoid passing props through multiple levels:

```tsx
// ❌ Bad: Prop drilling
function App() {
  const { user } = useUser();
  return (
    <Layout user={user}>
      <Page user={user}>
        <Component user={user} />
      </Page>
    </Layout>
  );
}

// ✅ Good: Use context directly where needed
function App() {
  return (
    <Layout>
      <Page>
        <Component />
      </Page>
    </Layout>
  );
}

function Component() {
  const { user } = useUser(); // Access directly
  return <div>{user?.username}</div>;
}
```

### 4. Handle Loading States

Each context has its own loading state. Handle them appropriately:

```tsx
function MyComponent() {
  const { loading: authLoading, isAuthenticated } = useAuth();
  const { loading: userLoading, user } = useUser();

  // Show loading state while checking authentication
  if (authLoading) {
    return <div>Checking authentication...</div>;
  }

  // Show login prompt if not authenticated
  if (!isAuthenticated) {
    return <div>Please log in</div>;
  }

  // Show loading state while fetching user data
  if (userLoading) {
    return <div>Loading user data...</div>;
  }

  // Render component with user data
  return <div>Welcome, {user?.username}!</div>;
}
```

## Testing

### Testing Components with Contexts

When testing components that use these contexts, wrap them with the appropriate providers:

```tsx
import { render } from '@testing-library/react';
import { AuthProvider } from '@/contexts/AuthContext';
import { UserProvider } from '@/contexts/UserContext';
import { ThemeProvider } from '@/contexts/ThemeContext';

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <AuthProvider>
      <UserProvider>
        <ThemeProvider>{ui}</ThemeProvider>
      </UserProvider>
    </AuthProvider>
  );
}

test('renders user profile', () => {
  renderWithProviders(<UserProfile />);
  // ... test assertions
});
```

### Mocking Context Values

For unit tests, you can mock context values:

```tsx
import { useUser } from '@/contexts/UserContext';

jest.mock('@/contexts/UserContext', () => ({
  useUser: jest.fn(),
}));

test('displays username', () => {
  (useUser as jest.Mock).mockReturnValue({
    user: { id: '1', username: 'testuser', discordId: '123', avatar: 'avatar.png' },
    loading: false,
    refreshUser: jest.fn(),
  });

  render(<UserProfile />);
  expect(screen.getByText('testuser')).toBeInTheDocument();
});
```

## Troubleshooting

### Error: "useAuth must be used within AuthProvider"

**Cause:** You're trying to use `useAuth()` in a component that's not wrapped by `<AuthProvider>`.

**Solution:** Ensure your root layout wraps the application with `<AuthProvider>`:

```tsx
// app/layout.tsx
<AuthProvider>{children}</AuthProvider>
```

### Error: "useUser must be used within UserProvider"

**Cause:** You're trying to use `useUser()` in a component that's not wrapped by `<UserProvider>`.

**Solution:** Ensure `<UserProvider>` is in your provider hierarchy:

```tsx
// app/layout.tsx
<AuthProvider>
  <UserProvider>{children}</UserProvider>
</AuthProvider>
```

### User data is null even when authenticated

**Cause:** `UserProvider` depends on `AuthProvider` to know when to fetch user data.

**Solution:** Ensure `UserProvider` is nested inside `AuthProvider`:

```tsx
// ✅ Correct order
<AuthProvider>
  <UserProvider>
    {children}
  </UserProvider>
</AuthProvider>

// ❌ Wrong order
<UserProvider>
  <AuthProvider>
    {children}
  </AuthProvider>
</UserProvider>
```

### Theme not persisting across page refreshes

**Cause:** Theme is stored in localStorage, which may be blocked or cleared.

**Solution:** Check browser settings and ensure localStorage is enabled. The theme will default to 'system' if localStorage is unavailable.

## Additional Resources

- [React Context API Documentation](https://react.dev/reference/react/useContext)
- [React Performance Optimization](https://react.dev/learn/render-and-commit)
- [Next.js App Router](https://nextjs.org/docs/app)
