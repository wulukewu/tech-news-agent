/**
 * Lazy Route Configuration
 * Requirements: 12.4
 *
 * This module provides lazy-loaded route components for optimal bundle splitting.
 * Each route is loaded on-demand to reduce initial bundle size.
 */

'use client';

import { createLazyRoute } from './code-splitting';

/**
 * Articles Page - Main article browsing interface
 */
export const LazyArticlesPage = createLazyRoute(
  () => import('@/app/dashboard/articles/page'),
  'Articles'
);

/**
 * Recommendations Page - AI-powered recommendations
 */
export const LazyRecommendationsPage = createLazyRoute(
  () => import('@/app/dashboard/recommendations/page'),
  'Recommendations'
);

/**
 * Analytics Page - User analytics dashboard
 */
export const LazyAnalyticsPage = createLazyRoute(
  () => import('@/app/dashboard/analytics/page'),
  'Analytics'
);

/**
 * Subscriptions Page - Feed management
 */
export const LazySubscriptionsPage = createLazyRoute(
  () => import('@/app/dashboard/subscriptions/page'),
  'Subscriptions'
);

/**
 * System Status Page - System monitoring
 */
export const LazySystemStatusPage = createLazyRoute(
  () => import('@/app/dashboard/system-status/page'),
  'System Status'
);

/**
 * Settings Page - User settings
 */
export const LazySettingsPage = createLazyRoute(
  () => import('@/app/dashboard/settings/page'),
  'Settings'
);

/**
 * Reading List - Saved articles
 */
export const LazyReadingListPage = createLazyRoute(
  () => import('@/app/dashboard/reading-list/page'),
  'Reading List'
);

/**
 * Search Page - Advanced search interface (commented out - route doesn't exist)
 */
// export const LazySearchPage = createLazyRoute(
//   () => import('@/app/(dashboard)/search/page'),
//   'Search'
// );
