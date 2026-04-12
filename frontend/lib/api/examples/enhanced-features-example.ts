/**
 * Enhanced Features Examples - Task 11.2
 *
 * This file demonstrates how to use the new API client enhancements:
 * - New API modules (Analytics, Recommendations, Onboarding)
 * - Feature flags for A/B testing
 * - Performance monitoring
 * - Error recovery strategies
 */

import {
  // Core client
  apiClient,

  // New API modules
  logAnalyticsEvent,
  getRecommendedFeeds,
  getOnboardingStatus,
  updateOnboardingProgress,
  batchSubscribe,

  // Feature flags
  isFeatureEnabled,
  API_FEATURE_FLAGS,
  logFeatureFlags,

  // Performance monitoring
  performanceMonitor,

  // Error recovery
  withRecovery,
  batchWithRecovery,
  withTimeout,
  debounceApiCall,
  throttleApiCall,
  responseCache,
} from '@/lib/api';

// ============================================================================
// Example 1: Using New API Modules
// ============================================================================

/**
 * Example: Log analytics events
 */
export async function trackUserAction() {
  await logAnalyticsEvent({
    event_type: 'button_click',
    event_name: 'subscribe_feed',
    properties: {
      feed_id: '123',
      category: 'tech',
    },
  });
}

/**
 * Example: Get personalized recommendations
 */
export async function showRecommendations() {
  const { recommendations } = await getRecommendedFeeds();

  console.log('Recommended feeds:');
  recommendations.forEach((feed) => {
    console.log(`- ${feed.title} (${feed.reason})`);
  });

  return recommendations;
}

/**
 * Example: Manage onboarding flow
 */
export async function handleOnboarding() {
  // Check current status
  const status = await getOnboardingStatus();

  if (status.is_completed) {
    console.log('Onboarding already completed');
    return;
  }

  // Update progress
  await updateOnboardingProgress('feed_selection', true, {
    selected_feeds: ['feed1', 'feed2'],
  });

  console.log('Onboarding progress updated');
}

/**
 * Example: Batch subscribe to feeds
 */
export async function subscribeToMultipleFeeds(feedIds: string[]) {
  const result = await batchSubscribe(feedIds);

  console.log(`Subscribed to ${result.subscribed_count} feeds`);
  if (result.failed_count > 0) {
    console.warn(`Failed to subscribe to ${result.failed_count} feeds`);
  }

  return result;
}

// ============================================================================
// Example 2: Using Feature Flags
// ============================================================================

/**
 * Example: A/B test new articles API
 */
export async function fetchArticlesWithABTest() {
  if (isFeatureEnabled('USE_NEW_ARTICLES_API')) {
    // Use new implementation with enhanced caching
    console.log('Using new articles API');
    return fetchArticlesV2();
  } else {
    // Use old implementation
    console.log('Using old articles API');
    return fetchArticlesV1();
  }
}

async function fetchArticlesV1() {
  return apiClient.get('/api/articles/me');
}

async function fetchArticlesV2() {
  // New implementation with caching
  const cacheKey = 'articles-v2';
  const cached = responseCache.get(cacheKey);
  if (cached) return cached;

  const data = await apiClient.get('/api/articles/me');
  responseCache.set(cacheKey, data);
  return data;
}

/**
 * Example: Check feature flags on app startup
 */
export function initializeApp() {
  // Log all feature flags in development
  if (process.env.NODE_ENV === 'development') {
    logFeatureFlags();
  }

  // Configure based on flags
  if (API_FEATURE_FLAGS.ENABLE_API_MONITORING) {
    console.log('📊 Performance monitoring enabled');
  }

  if (API_FEATURE_FLAGS.ENABLE_API_CACHING) {
    console.log('💾 API caching enabled');
  }
}

// ============================================================================
// Example 3: Performance Monitoring
// ============================================================================

/**
 * Example: Monitor API performance
 */
export async function monitorApiPerformance() {
  // Make some API calls
  await apiClient.get('/api/articles/me');
  await apiClient.get('/api/reading-list');
  await apiClient.get('/api/feeds');

  // Get performance statistics
  const stats = performanceMonitor.getStats();

  console.log('Performance Statistics:');
  console.log(`- Total requests: ${stats.totalRequests}`);
  console.log(
    `- Success rate: ${((stats.successfulRequests / stats.totalRequests) * 100).toFixed(1)}%`
  );
  console.log(`- Average response time: ${stats.averageResponseTime.toFixed(0)}ms`);
  console.log(`- Slow requests: ${stats.slowRequestsCount}`);

  // Log detailed stats
  performanceMonitor.logStats();

  // Export metrics for analysis
  const metricsJson = performanceMonitor.exportMetrics();
  console.log('Metrics exported:', metricsJson);
}

/**
 * Example: Track specific endpoint performance
 */
export async function trackEndpointPerformance(endpoint: string) {
  const startTime = performance.now();

  try {
    await apiClient.get(endpoint);
    const duration = performance.now() - startTime;

    console.log(`${endpoint} took ${duration.toFixed(0)}ms`);

    if (duration > 1000) {
      console.warn(`⚠️ Slow request detected: ${endpoint}`);
    }
  } catch (error) {
    console.error(`Error fetching ${endpoint}:`, error);
  }
}

// ============================================================================
// Example 4: Error Recovery Strategies
// ============================================================================

/**
 * Example: Use fallback data on error
 */
export async function fetchArticlesWithFallback() {
  const result = await withRecovery(() => apiClient.get('/api/articles/me'), {
    fallback: () => ({
      data: [],
      pagination: {
        page: 1,
        page_size: 20,
        total_count: 0,
        has_next: false,
        has_previous: false,
      },
    }),
    cacheKey: 'articles',
  });

  if (result.success) {
    console.log(`Articles loaded via ${result.strategy}`);
    return result.data;
  } else {
    console.error('Failed to load articles:', result.error);
    throw result.error;
  }
}

/**
 * Example: Use cached data on error
 */
export async function fetchCategoriesWithCache() {
  const result = await withRecovery(() => apiClient.get('/api/articles/categories'), {
    cacheKey: 'categories',
    useCache: true,
  });

  if (result.success) {
    if (result.strategy === 'cache') {
      console.log('Using cached categories');
    }
    return result.data;
  }

  return { categories: [] };
}

/**
 * Example: Batch requests with recovery
 */
export async function loadDashboardData() {
  const results = await batchWithRecovery(
    [
      () => apiClient.get('/api/articles/me'),
      () => apiClient.get('/api/reading-list'),
      () => apiClient.get('/api/feeds'),
    ],
    {
      fallback: () => [],
      skipOnError: true,
    }
  );

  const [articles, readingList, feeds] = results;

  return {
    articles: articles.success ? articles.data : [],
    readingList: readingList.success ? readingList.data : [],
    feeds: feeds.success ? feeds.data : [],
  };
}

/**
 * Example: Timeout protection for slow endpoints
 */
export async function fetchWithTimeout() {
  try {
    const data = await withTimeout(
      () => apiClient.get('/api/slow-endpoint'),
      5000 // 5 second timeout
    );
    return data;
  } catch (error) {
    console.error('Request timed out after 5 seconds');
    throw error;
  }
}

/**
 * Example: Debounced search
 */
export const debouncedSearch = debounceApiCall(
  (query: string) => apiClient.get(`/api/search?q=${encodeURIComponent(query)}`),
  300 // 300ms delay
);

export async function handleSearchInput(query: string) {
  // Only the last call within 300ms will execute
  const results = await debouncedSearch(query);
  return results;
}

/**
 * Example: Throttled refresh
 */
export const throttledRefresh = throttleApiCall(
  () => apiClient.get('/api/articles/me'),
  2000 // Minimum 2 seconds between calls
);

export async function handleRefreshClick() {
  // Subsequent clicks within 2 seconds will wait
  const data = await throttledRefresh();
  console.log('Data refreshed');
  return data;
}

// ============================================================================
// Example 5: Complete Dashboard Component Pattern
// ============================================================================

/**
 * Example: Complete dashboard data loading with all features
 */
export async function loadDashboard() {
  // Log page view
  await logAnalyticsEvent({
    event_type: 'page_view',
    event_name: 'dashboard',
  });

  // Load data with recovery strategies
  const result = await withRecovery(
    async () => {
      // Use feature flag to determine implementation
      if (isFeatureEnabled('USE_BATCH_REQUESTS')) {
        // Load all data in parallel
        const [articles, readingList, feeds, recommendations] = await Promise.all([
          apiClient.get('/api/articles/me'),
          apiClient.get('/api/reading-list'),
          apiClient.get('/api/feeds'),
          getRecommendedFeeds(),
        ]);

        return { articles, readingList, feeds, recommendations };
      } else {
        // Load sequentially
        const articles = await apiClient.get('/api/articles/me');
        const readingList = await apiClient.get('/api/reading-list');
        const feeds = await apiClient.get('/api/feeds');
        const recommendations = await getRecommendedFeeds();

        return { articles, readingList, feeds, recommendations };
      }
    },
    {
      maxRetries: 3,
      cacheKey: 'dashboard-data',
      useCache: true,
      fallback: () => ({
        articles: { data: [], pagination: {} },
        readingList: { data: [], pagination: {} },
        feeds: [],
        recommendations: { recommendations: [], total_count: 0 },
      }),
      onError: (error) => {
        // Log error for monitoring
        console.error('Dashboard load error:', error);

        // Track error event
        logAnalyticsEvent({
          event_type: 'error',
          event_name: 'dashboard_load_failed',
          properties: {
            error_code: error.errorCode,
            error_message: error.message,
          },
        });
      },
    }
  );

  // Log performance stats in development
  if (process.env.NODE_ENV === 'development') {
    performanceMonitor.logStats();
  }

  return result.data;
}

// ============================================================================
// Example 6: React Component Integration
// ============================================================================

/**
 * Example: React hook with enhanced features
 */
export function useDashboardData() {
  // This would be a React hook in a real component
  // Showing the pattern here

  const loadData = async () => {
    try {
      const data = await loadDashboard();
      return data;
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      throw error;
    }
  };

  return { loadData };
}

/**
 * Example: Error boundary with analytics
 */
export async function handleComponentError(error: Error, componentName: string) {
  // Log error event
  await logAnalyticsEvent({
    event_type: 'error',
    event_name: 'component_error',
    properties: {
      component: componentName,
      error_message: error.message,
      stack: error.stack,
    },
  });

  console.error(`Error in ${componentName}:`, error);
}
