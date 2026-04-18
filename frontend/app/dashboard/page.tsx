'use client';

/**
 * App Home Page
 *
 * Redirects to /dashboard/articles as the default app landing page.
 *
 * Requirement 3.2: /dashboard redirects to /dashboard/articles
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function AppHomePage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to articles page
    router.replace('/dashboard/articles');
  }, [router]);

  // Show loading while redirecting
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        <p className="mt-4 text-muted-foreground">Redirecting...</p>
      </div>
    </div>
  );
}
