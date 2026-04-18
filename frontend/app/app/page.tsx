import { redirect } from 'next/navigation';

/**
 * App Root Page
 *
 * Redirects to /app/articles as the default app view.
 * This ensures /app always has a valid destination.
 */
export default function AppPage() {
  redirect('/app/articles');
}
