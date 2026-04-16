/**
 * Lazy-loaded Component Exports
 * Requirements: 12.4
 *
 * This module provides lazy-loaded versions of heavy components
 * to improve initial page load performance through code splitting.
 */

'use client';

import { createLazyComponent, SkeletonFallback } from '@/lib/performance/code-splitting';

/**
 * AI Analysis Modal - Heavy component with AI processing
 * Only loaded when user requests analysis
 */
export const LazyAnalysisModal = createLazyComponent(
  () => import('@/features/ai-analysis/components/AnalysisModal'),
  {
    fallback: <SkeletonFallback />,
    ssr: false,
  }
);

/**
 * Chart Components - Heavy visualization libraries
 * Only loaded when user views analytics
 */
export const LazyChartComponents = createLazyComponent(() => import('@/components/charts'), {
  fallback: <SkeletonFallback />,
  ssr: false,
});

/**
 * Rich Text Editor - Heavy component for article editing
 * Only loaded when user needs to edit content
 */
export const LazyRichTextEditor = createLazyComponent(
  () => import('@/components/forms/RichTextEditor'),
  {
    fallback: <SkeletonFallback />,
    ssr: false,
  }
);

/**
 * Advanced Filter Panel - Complex filtering UI
 * Only loaded when user opens advanced filters
 */
export const LazyAdvancedFilterPanel = createLazyComponent(
  () => import('@/features/articles/components/AdvancedFilterPanel'),
  {
    fallback: <SkeletonFallback />,
    ssr: false,
  }
);

/**
 * Recommendation Engine UI - Complex recommendation display
 * Only loaded on recommendations page
 */
export const LazyRecommendationEngine = createLazyComponent(
  () => import('@/features/recommendations/components/RecommendationEngine'),
  {
    fallback: <SkeletonFallback />,
    ssr: false,
  }
);

/**
 * System Monitor Dashboard - Real-time monitoring UI
 * Only loaded on system status page
 */
export const LazySystemMonitor = createLazyComponent(
  () => import('@/features/system-monitor/components/SystemMonitor'),
  {
    fallback: <SkeletonFallback />,
    ssr: false,
  }
);

/**
 * Analytics Dashboard - Heavy data visualization
 * Only loaded on analytics page
 */
export const LazyAnalyticsDashboard = createLazyComponent(
  () => import('@/features/analytics/components/AnalyticsDashboard'),
  {
    fallback: <SkeletonFallback />,
    ssr: false,
  }
);

/**
 * Notification Center - Complex notification UI
 * Only loaded when user opens notifications
 */
export const LazyNotificationCenter = createLazyComponent(
  () => import('@/features/notifications/components/NotificationCenter'),
  {
    fallback: <SkeletonFallback />,
    ssr: false,
  }
);

/**
 * Feed Management Dashboard - Complex subscription management
 * Only loaded on subscriptions page
 */
export const LazyFeedManagement = createLazyComponent(
  () => import('@/features/subscriptions/components/FeedManagement'),
  {
    fallback: <SkeletonFallback />,
    ssr: false,
  }
);

/**
 * Settings Panel - Complex settings UI
 * Only loaded on settings page
 */
export const LazySettingsPanel = createLazyComponent(
  () => import('@/components/settings/SettingsPanel'),
  {
    fallback: <SkeletonFallback />,
    ssr: false,
  }
);
