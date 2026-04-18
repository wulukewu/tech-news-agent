import { redirect } from 'next/navigation';

/**
 * Dashboard Root Page
 *
 * Redirects to /dashboard/articles as the default dashboard view.
 * This ensures /dashboard always has a valid destination.
 */
export default function DashboardPage() {
  redirect('/dashboard/articles');
}
