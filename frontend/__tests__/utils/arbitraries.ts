/**
 * Fast-check arbitraries for property-based testing
 * Provides reusable data generators for consistent testing
 */

import React from 'react';
import fc from 'fast-check';
import type { NavigationItem, BreadcrumbItem } from '@/components/layout';

// Basic primitives
export const nonEmptyString = fc.string({ minLength: 1, maxLength: 100 });
export const shortString = fc.string({ minLength: 1, maxLength: 50 });
export const longString = fc.string({ minLength: 1, maxLength: 500 });
export const className = fc.string({ maxLength: 100 });
export const url = fc.webUrl();
export const webPath = fc.webPath();

// UI-specific arbitraries
export const badgeArbitrary = fc.oneof(
  fc.string({ maxLength: 10 }),
  fc.integer({ min: 0, max: 999 })
);

export const navigationItemArbitrary: fc.Arbitrary<NavigationItem> = fc.record({
  href: webPath,
  label: shortString,
  icon: fc.constant(({ className }: { className?: string }) =>
    React.createElement('div', { 'data-testid': 'mock-icon', className })
  ),
  badge: fc.option(badgeArbitrary),
  disabled: fc.boolean(),
  shortcut: fc.option(fc.string({ minLength: 1, maxLength: 1 })),
});

export const breadcrumbItemArbitrary: fc.Arbitrary<BreadcrumbItem> = fc.record({
  label: shortString,
  href: fc.option(webPath),
  current: fc.boolean(),
});

// Layout-specific arbitraries
export const layoutPropsArbitrary = fc.record({
  className: fc.option(className),
  sidebarCollapsed: fc.boolean(),
});

export const dashboardLayoutPropsArbitrary = fc.record({
  title: nonEmptyString,
  description: fc.option(longString),
  className: fc.option(className),
});

export const headerPropsArbitrary = fc.record({
  showSearch: fc.boolean(),
  showNotifications: fc.boolean(),
  showUserMenu: fc.boolean(),
  searchPlaceholder: fc.option(shortString),
});

// Viewport and responsive arbitraries
export const viewportArbitrary = fc.record({
  width: fc.integer({ min: 320, max: 2560 }),
  height: fc.integer({ min: 568, max: 1440 }),
});

export const responsiveBreakpoints = fc.oneof(
  fc.constant(320), // Mobile
  fc.constant(768), // Tablet
  fc.constant(1024), // Desktop
  fc.constant(1440), // Large desktop
  fc.constant(2560) // Ultra-wide
);

// Theme arbitraries
export const themeArbitrary = fc.oneof(
  fc.constant('light'),
  fc.constant('dark'),
  fc.constant('system')
);

// Article-related arbitraries (for future use)
export const articleArbitrary = fc.record({
  id: fc.uuid(),
  title: nonEmptyString,
  url: url,
  summary: longString,
  category: fc.constantFrom('tech', 'ai', 'web', 'mobile', 'devops'),
  tinkeringIndex: fc.integer({ min: 1, max: 5 }),
  publishedAt: fc.date({ min: new Date('2020-01-01'), max: new Date() }),
  source: fc.record({
    id: fc.uuid(),
    name: shortString,
    url: url,
    category: fc.constantFrom('blog', 'news', 'documentation'),
  }),
  userRating: fc.option(fc.integer({ min: 1, max: 5 })),
  isInReadingList: fc.boolean(),
  viewCount: fc.integer({ min: 0, max: 10000 }),
  shareCount: fc.integer({ min: 0, max: 1000 }),
});

// Filter arbitraries
export const articleFiltersArbitrary = fc.record({
  categories: fc.array(fc.constantFrom('tech', 'ai', 'web', 'mobile'), { maxLength: 5 }),
  tinkeringIndex: fc
    .tuple(fc.integer(1, 5), fc.integer(1, 5))
    .map(([min, max]) => [Math.min(min, max), Math.max(min, max)] as [number, number]),
  dateRange: fc.option(
    fc
      .tuple(
        fc.date({ min: new Date('2020-01-01'), max: new Date() }),
        fc.date({ min: new Date('2020-01-01'), max: new Date() })
      )
      .map(
        ([start, end]) =>
          [
            new Date(Math.min(start.getTime(), end.getTime())),
            new Date(Math.max(start.getTime(), end.getTime())),
          ] as [Date, Date]
      )
  ),
  sources: fc.array(fc.uuid(), { maxLength: 3 }),
  sortBy: fc.constantFrom('date', 'tinkering_index', 'category', 'title'),
  sortOrder: fc.constantFrom('asc', 'desc'),
});

// User arbitraries
export const userArbitrary = fc.record({
  id: fc.uuid(),
  username: shortString,
  email: fc.emailAddress(),
  avatar: fc.option(url),
  createdAt: fc.date({ min: new Date('2020-01-01'), max: new Date() }),
});

// Recommendation arbitraries
export const recommendationArbitrary = fc.record({
  id: fc.uuid(),
  article: articleArbitrary,
  reason: longString,
  confidence: fc.float({ min: 0, max: 1 }),
  generatedAt: fc.date({ min: new Date('2020-01-01'), max: new Date() }),
  dismissed: fc.boolean(),
});

// System status arbitraries
export const systemStatusArbitrary = fc.record({
  scheduler: fc.record({
    isRunning: fc.boolean(),
    lastExecution: fc.date(),
    nextExecution: fc.date(),
  }),
  database: fc.record({
    connected: fc.boolean(),
    responseTime: fc.integer({ min: 1, max: 1000 }),
  }),
  api: fc.record({
    healthy: fc.boolean(),
    responseTime: fc.integer({ min: 10, max: 5000 }),
    errorRate: fc.float({ min: 0, max: 1 }),
  }),
});

// Error arbitraries
export const apiErrorArbitrary = fc.record({
  code: fc.constantFrom('NETWORK_ERROR', 'VALIDATION_ERROR', 'SERVER_ERROR', 'NOT_FOUND'),
  message: nonEmptyString,
  timestamp: fc.date().map((d) => d.toISOString()),
  requestId: fc.option(fc.uuid()),
});

// AI Analysis arbitraries
export const analysisResultArbitrary = fc.record({
  coreConcepts: fc.array(nonEmptyString, { minLength: 1, maxLength: 5 }),
  applicationScenarios: fc.array(nonEmptyString, { minLength: 1, maxLength: 5 }),
  potentialRisks: fc.array(nonEmptyString, { minLength: 1, maxLength: 5 }),
  recommendedSteps: fc.array(nonEmptyString, { minLength: 1, maxLength: 5 }),
  generatedAt: fc.date({ min: new Date('2020-01-01'), max: new Date() }),
  model: fc.constantFrom('llama-3.1-8b', 'llama-3.3-70b'),
  rawText: longString,
});

export const analysisModalPropsArbitrary = fc.record({
  articleId: fc.uuid(),
  articleTitle: nonEmptyString,
  articleSource: shortString,
  articlePublishedAt: fc.option(fc.date().map((d) => d.toISOString())),
});

export const articleMetadataArbitrary = fc.record({
  id: fc.uuid(),
  title: nonEmptyString,
  source: shortString,
  publishedAt: fc.option(fc.date().map((d) => d.toISOString())),
});

export const analysisApiResponseArbitrary = fc.record({
  success: fc.constant(true),
  data: fc.record({
    core_concepts: fc.array(nonEmptyString, { minLength: 1, maxLength: 5 }),
    application_scenarios: fc.array(nonEmptyString, { minLength: 1, maxLength: 5 }),
    potential_risks: fc.array(nonEmptyString, { minLength: 1, maxLength: 5 }),
    recommended_steps: fc.array(nonEmptyString, { minLength: 1, maxLength: 5 }),
    generated_at: fc.date().map((d) => d.toISOString()),
    model: fc.constant('llama-3.3-70b'),
    raw_text: longString,
  }),
});

export const articleIdArbitrary = fc.uuid();

// Utility functions for test data
export function createMockNavigationItems(count: number = 5): NavigationItem[] {
  return fc.sample(navigationItemArbitrary, count);
}

export function createMockBreadcrumbItems(count: number = 3): BreadcrumbItem[] {
  return fc.sample(breadcrumbItemArbitrary, count);
}

export function createMockArticles(count: number = 10) {
  return fc.sample(articleArbitrary, count);
}
