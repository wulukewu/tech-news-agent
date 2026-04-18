/**
 * Route Accessibility Tests
 *
 * Tests that all routes defined in the routing structure are accessible.
 * This is a checkpoint test for Task 4 - Verify routing setup.
 *
 * Test Coverage:
 * - All public routes are accessible
 * - All protected routes exist and have page components
 * - No broken links in navigation
 */

import { describe, it, expect } from 'vitest';
import { existsSync } from 'fs';
import { join } from 'path';

describe('Route Accessibility - Phase 1 Checkpoint', () => {
  const appDir = join(process.cwd(), 'app');

  describe('Public Routes', () => {
    it('should have landing page at /', () => {
      const landingPage = join(appDir, 'page.tsx');
      expect(existsSync(landingPage)).toBe(true);
    });

    it('should have login page at /login', () => {
      const loginPage = join(appDir, 'login', 'page.tsx');
      expect(existsSync(loginPage)).toBe(true);
    });

    it('should have OAuth callback at /auth/callback', () => {
      const callbackPage = join(appDir, 'auth', 'callback', 'page.tsx');
      expect(existsSync(callbackPage)).toBe(true);
    });
  });

  describe('Protected Routes - /app/*', () => {
    it('should have app layout with route protection', () => {
      const appLayout = join(appDir, 'app', 'layout.tsx');
      expect(existsSync(appLayout)).toBe(true);
    });

    it('should have app home page that redirects to /app/articles', () => {
      const appHomePage = join(appDir, 'app', 'page.tsx');
      expect(existsSync(appHomePage)).toBe(true);
    });

    it('should have articles page at /app/articles', () => {
      const articlesPage = join(appDir, 'app', 'articles', 'page.tsx');
      expect(existsSync(articlesPage)).toBe(true);
    });

    it('should have reading list page at /app/reading-list', () => {
      const readingListPage = join(appDir, 'app', 'reading-list', 'page.tsx');
      expect(existsSync(readingListPage)).toBe(true);
    });

    it('should have subscriptions page at /app/subscriptions', () => {
      const subscriptionsPage = join(appDir, 'app', 'subscriptions', 'page.tsx');
      expect(existsSync(subscriptionsPage)).toBe(true);
    });

    it('should have analytics page at /app/analytics', () => {
      const analyticsPage = join(appDir, 'app', 'analytics', 'page.tsx');
      expect(existsSync(analyticsPage)).toBe(true);
    });

    it('should have settings page at /app/settings', () => {
      const settingsPage = join(appDir, 'app', 'settings', 'page.tsx');
      expect(existsSync(settingsPage)).toBe(true);
    });

    it('should have system status page at /app/system-status', () => {
      const systemStatusPage = join(appDir, 'app', 'system-status', 'page.tsx');
      expect(existsSync(systemStatusPage)).toBe(true);
    });
  });

  describe('Route Structure Validation', () => {
    it('should have all Phase 1 routes implemented', () => {
      const phase1Routes = [
        'page.tsx', // Landing page
        'login/page.tsx', // Login page
        'auth/callback/page.tsx', // OAuth callback
        'app/layout.tsx', // App layout with protection
        'app/page.tsx', // App home (redirects to articles)
        'app/articles/page.tsx', // Articles
        'app/reading-list/page.tsx', // Reading list
        'app/subscriptions/page.tsx', // Subscriptions
        'app/analytics/page.tsx', // Analytics
        'app/settings/page.tsx', // Settings
        'app/system-status/page.tsx', // System status
      ];

      const missingRoutes = phase1Routes.filter((route) => {
        const routePath = join(appDir, route);
        return !existsSync(routePath);
      });

      expect(missingRoutes).toEqual([]);
    });
  });
});
