/**
 * ProtectedRoute Component - Usage Examples
 *
 * This file demonstrates how to use the ProtectedRoute component
 * to protect pages that require authentication.
 */

import { ProtectedRoute } from './ProtectedRoute';

/**
 * Example 1: Basic Usage in a Dashboard Page
 *
 * Wrap your page content with ProtectedRoute to ensure
 * only authenticated users can access it.
 */
export function DashboardPageExample() {
  return (
    <ProtectedRoute>
      <div className="container mx-auto py-8">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p>This content is only visible to authenticated users.</p>
      </div>
    </ProtectedRoute>
  );
}

/**
 * Example 2: Subscriptions Page
 *
 * The ProtectedRoute component automatically:
 * 1. Shows a loading screen while checking authentication
 * 2. Saves the current URL to sessionStorage
 * 3. Redirects to login if not authenticated
 * 4. Renders the content if authenticated
 */
export function SubscriptionsPageExample() {
  return (
    <ProtectedRoute>
      <div className="container mx-auto py-8">
        <h1 className="text-3xl font-bold">Manage Subscriptions</h1>
        {/* Your subscriptions content here */}
      </div>
    </ProtectedRoute>
  );
}

/**
 * Example 3: Articles Page
 *
 * The saved URL in sessionStorage can be used after login
 * to redirect users back to where they wanted to go.
 */
export function ArticlesPageExample() {
  return (
    <ProtectedRoute>
      <div className="container mx-auto py-8">
        <h1 className="text-3xl font-bold">Your Articles</h1>
        {/* Your articles content here */}
      </div>
    </ProtectedRoute>
  );
}

/**
 * Example 4: Reading List Page
 *
 * All protected routes should use the same pattern
 * for consistent authentication behavior.
 */
export function ReadingListPageExample() {
  return (
    <ProtectedRoute>
      <div className="container mx-auto py-8">
        <h1 className="text-3xl font-bold">Reading List</h1>
        {/* Your reading list content here */}
      </div>
    </ProtectedRoute>
  );
}

/**
 * Example 5: Using ProtectedRoute in Next.js App Router
 *
 * In Next.js 14+ with App Router, you would typically use
 * ProtectedRoute in your page.tsx files like this:
 */

// app/dashboard/page.tsx
/*
'use client';

import { ProtectedRoute } from '@/components/ProtectedRoute';

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <div className="container mx-auto py-8">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p>Protected content</p>
      </div>
    </ProtectedRoute>
  );
}
*/

/**
 * Example 6: Accessing Saved Redirect URL After Login
 *
 * After successful login, you can retrieve the saved URL
 * and redirect the user back to their intended destination:
 */

// In your callback page or after login success:
/*
const redirectUrl = sessionStorage.getItem('redirectAfterLogin');
if (redirectUrl) {
  sessionStorage.removeItem('redirectAfterLogin');
  router.push(redirectUrl);
} else {
  router.push('/dashboard'); // Default redirect
}
*/

/**
 * Protected Routes in the Application:
 *
 * According to Requirement 6.6, the following routes should be protected:
 * - /dashboard
 * - /subscriptions
 * - /articles
 * - /reading-list
 *
 * The following routes should NOT be protected (Requirement 6.7):
 * - / (login page)
 * - /auth/callback (OAuth callback page)
 */
