# Homepage and Routing Fixes

## Issues Fixed

### 1. Duplicate Navbar on Homepage ✅

**Problem:** The landing page had two navbars - one from the root layout and one from the LandingNav component.

**Root Cause:** The root layout (`app/layout.tsx`) was rendering `<Navigation />` for ALL pages, including the landing page.

**Solution:**

- Removed `<AppLayout header={<Navigation />}>` from root layout
- Created `ConditionalLayout` component that only renders Navigation + AppLayout for dashboard routes
- Landing page (`/`), login page (`/login`), and auth callback (`/auth/callback`) now render without the app navigation

**Files Changed:**

- `frontend/app/layout.tsx` - Removed AppLayout wrapper, added ConditionalLayout
- `frontend/components/ConditionalLayout.tsx` - New component for conditional layout rendering
- `frontend/app/page.tsx` - Simplified to remove AuthGuard wrapper

### 2. Large Padding Gap on Homepage ✅

**Problem:** The landing page had excessive padding/spacing.

**Root Cause:** The `AppLayout` component was adding container padding (`p-4 lg:p-6`) to all pages, including the landing page.

**Solution:**

- Landing page now renders without AppLayout wrapper
- Each landing page section controls its own spacing
- Removed unnecessary AuthGuard wrapper that was adding extra structure

**Files Changed:**

- `frontend/app/page.tsx` - Removed AuthGuard, simplified structure
- `frontend/components/ConditionalLayout.tsx` - Ensures landing page bypasses AppLayout

### 3. Infinite Reload on `/dashboard/articles` ✅

**Problem:** The articles page was reloading infinitely.

**Root Cause:** Double authentication check - both the dashboard layout AND the ProtectedRoute component were checking authentication and redirecting, creating a loop.

**Solution:**

- Removed `ProtectedRoute` wrapper from `dashboard/articles/page.tsx`
- The dashboard layout (`app/dashboard/layout.tsx`) already has authentication protection via `AuthGuard`
- No need for double protection

**Files Changed:**

- `frontend/app/dashboard/articles/page.tsx` - Removed ProtectedRoute wrapper and import

## Implementation Details

### ConditionalLayout Component

```typescript
'use client';

import { usePathname } from 'next/navigation';
import { Navigation } from '@/components/Navigation';
import { AppLayout } from '@/components/layout';

export function ConditionalLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // Routes that should NOT have navigation/layout
  const publicRoutes = ['/', '/login', '/auth/callback'];
  const isPublicRoute = publicRoutes.includes(pathname);

  // If it's a public route, render children without layout
  if (isPublicRoute) {
    return <>{children}</>;
  }

  // For all other routes (dashboard, etc.), render with navigation and layout
  return <AppLayout header={<Navigation />}>{children}</AppLayout>;
}
```

### Route Structure

**Public Routes (No Navigation/Layout):**

- `/` - Landing page with LandingNav
- `/login` - Login page with simple header
- `/auth/callback` - OAuth callback (minimal UI)

**Protected Routes (With Navigation/Layout):**

- `/dashboard/*` - All dashboard routes
- `/articles` - Articles page
- `/recommendations` - Recommendations page
- `/settings/*` - Settings pages

## Testing

### Manual Testing Checklist

- [x] Landing page renders without duplicate navbar
- [x] Landing page has proper spacing (no excessive padding)
- [x] Login page renders correctly
- [x] Dashboard routes have Navigation component
- [x] `/dashboard/articles` loads without infinite reload
- [x] Authentication flow works correctly
- [x] Build succeeds with no errors

### Build Results

```
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Collecting page data
✓ Generating static pages (18/18)
✓ Collecting build traces
✓ Finalizing page optimization

Exit Code: 0
```

## Files Modified

1. `frontend/app/layout.tsx` - Removed AppLayout, added ConditionalLayout
2. `frontend/app/page.tsx` - Simplified landing page structure
3. `frontend/app/dashboard/layout.tsx` - Removed redundant container padding
4. `frontend/app/dashboard/articles/page.tsx` - Removed ProtectedRoute wrapper
5. `frontend/components/ConditionalLayout.tsx` - New component (created)

## Notes

- The dashboard layout still has authentication protection via AuthGuard
- No need for ProtectedRoute on individual dashboard pages
- Landing page components (LandingNav, HeroSection, etc.) are self-contained
- ConditionalLayout provides clean separation between public and protected routes

## Next Steps

The routing infrastructure is now clean and working correctly. Ready to proceed with:

- Task 7: Implement login page (already done)
- Task 8: Checkpoint - Verify landing and login pages
- Phase 3: Navigation components
