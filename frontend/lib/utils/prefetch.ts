/**
 * Intelligent Prefetching Mechanisms
 * Requirements: 12.5, 12.6
 *
 * This module provides intelligent prefetching for likely next actions
 * to improve perceived performance and user experience.
 */
import { logger } from '@/lib/utils/logger';

import { QueryClient } from '@tanstack/react-query';
import { cacheStrategies } from '../cache/strategies';

/**
 * User behavior patterns for predictive prefetching
 */
interface UserBehaviorPattern {
  pageViews: string[];
  timeSpent: Record<string, number>;
  clickPatterns: string[];
  lastActivity: number;
}

/**
 * Prefetch priority levels
 */
enum PrefetchPriority {
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
}

/**
 * Prefetch action definition
 */
interface PrefetchAction {
  key: string;
  priority: PrefetchPriority;
  condition: () => boolean;
  action: () => Promise<void>;
  cooldown?: number; // Minimum time between prefetches
}

/**
 * Intelligent Prefetch Manager
 */
export class IntelligentPrefetcher {
  private queryClient: QueryClient;
  private userBehavior: UserBehaviorPattern;
  private prefetchHistory: Map<string, number> = new Map();
  private isOnline: boolean = true;
  private connectionSpeed: 'slow' | 'fast' = 'fast';

  constructor(queryClient: QueryClient) {
    this.queryClient = queryClient;
    this.userBehavior = this.loadUserBehavior();
    this.setupNetworkMonitoring();
    this.setupBehaviorTracking();
  }

  /**
   * Setup network monitoring to adjust prefetch strategy
   */
  private setupNetworkMonitoring() {
    if (typeof window === 'undefined') return;

    // Monitor online/offline status
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.resumePrefetching();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
    });

    // Monitor connection speed
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;

      const updateConnectionSpeed = () => {
        const effectiveType = connection.effectiveType;
        this.connectionSpeed = ['slow-2g', '2g', '3g'].includes(effectiveType) ? 'slow' : 'fast';
      };

      connection.addEventListener('change', updateConnectionSpeed);
      updateConnectionSpeed();
    }
  }

  /**
   * Setup user behavior tracking
   */
  private setupBehaviorTracking() {
    if (typeof window === 'undefined') return;

    // Track page views
    const trackPageView = (path: string) => {
      this.userBehavior.pageViews.push(path);
      this.userBehavior.lastActivity = Date.now();

      // Keep only last 50 page views
      if (this.userBehavior.pageViews.length > 50) {
        this.userBehavior.pageViews.shift();
      }

      this.saveUserBehavior();
    };

    // Track time spent on pages
    let pageStartTime = Date.now();
    const trackTimeSpent = () => {
      const currentPath = window.location.pathname;
      const timeSpent = Date.now() - pageStartTime;

      this.userBehavior.timeSpent[currentPath] =
        (this.userBehavior.timeSpent[currentPath] || 0) + timeSpent;

      pageStartTime = Date.now();
      this.saveUserBehavior();
    };

    // Listen for navigation changes
    window.addEventListener('beforeunload', trackTimeSpent);
    window.addEventListener('popstate', () => {
      trackTimeSpent();
      trackPageView(window.location.pathname);
    });

    // Track initial page view
    trackPageView(window.location.pathname);
  }

  /**
   * Load user behavior from localStorage
   */
  private loadUserBehavior(): UserBehaviorPattern {
    if (typeof window === 'undefined') {
      return {
        pageViews: [],
        timeSpent: {},
        clickPatterns: [],
        lastActivity: Date.now(),
      };
    }

    try {
      const stored = localStorage.getItem('user-behavior');
      return stored
        ? JSON.parse(stored)
        : {
            pageViews: [],
            timeSpent: {},
            clickPatterns: [],
            lastActivity: Date.now(),
          };
    } catch {
      return {
        pageViews: [],
        timeSpent: {},
        clickPatterns: [],
        lastActivity: Date.now(),
      };
    }
  }

  /**
   * Save user behavior to localStorage
   */
  private saveUserBehavior() {
    if (typeof window === 'undefined') return;

    try {
      localStorage.setItem('user-behavior', JSON.stringify(this.userBehavior));
    } catch (error) {
      logger.warn('Failed to save user behavior:', error);
    }
  }

  /**
   * Predict likely next actions based on user behavior
   */
  private predictNextActions(): string[] {
    const { pageViews, timeSpent } = this.userBehavior;
    const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';

    // Analyze common navigation patterns
    const patterns: Record<string, string[]> = {
      '/articles': ['/recommendations', '/reading-list', '/subscriptions'],
      '/recommendations': ['/articles', '/reading-list'],
      '/reading-list': ['/articles', '/recommendations'],
      '/subscriptions': ['/articles', '/system-status'],
      '/analytics': ['/articles', '/subscriptions'],
      '/settings': ['/articles', '/subscriptions'],
    };

    // Get base predictions
    const basePredictions = patterns[currentPath] || [];

    // Enhance with user-specific patterns
    const userPatterns = this.analyzeUserPatterns();

    return [...new Set([...basePredictions, ...userPatterns])];
  }

  /**
   * Analyze user-specific navigation patterns
   */
  private analyzeUserPatterns(): string[] {
    const { pageViews, timeSpent } = this.userBehavior;

    // Find most visited pages
    const pageCounts = pageViews.reduce(
      (acc, page) => {
        acc[page] = (acc[page] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>
    );

    // Find pages where user spends most time
    const timeSpentSorted = Object.entries(timeSpent)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3)
      .map(([page]) => page);

    return timeSpentSorted;
  }

  /**
   * Define prefetch actions
   */
  private getPrefetchActions(): PrefetchAction[] {
    return [
      // High priority: Articles page data
      {
        key: 'articles-list',
        priority: PrefetchPriority.HIGH,
        condition: () => window.location.pathname === '/',
        action: async () => {
          await this.queryClient.prefetchQuery({
            queryKey: ['articles', 'list', { page: 1 }],
            queryFn: () => import('../api/articles').then((api) => api.fetchMyArticles(1, 20)),
            ...cacheStrategies.articleList,
          });
        },
        cooldown: 5 * 60 * 1000, // 5 minutes
      },

      // High priority: User's reading list
      {
        key: 'reading-list',
        priority: PrefetchPriority.HIGH,
        condition: () => ['/articles', '/'].includes(window.location.pathname),
        action: async () => {
          await this.queryClient.prefetchQuery({
            queryKey: ['reading-list'],
            queryFn: () => import('../api/readingList').then((api) => api.fetchReadingList()),
            ...cacheStrategies.readingList,
          });
        },
        cooldown: 2 * 60 * 1000, // 2 minutes
      },

      // Medium priority: Recommendations
      {
        key: 'recommendations',
        priority: PrefetchPriority.MEDIUM,
        condition: () => ['/articles', '/reading-list'].includes(window.location.pathname),
        action: async () => {
          await this.queryClient.prefetchQuery({
            queryKey: ['recommendations'],
            queryFn: () =>
              import('../api/recommendations').then((api) => api.getRecommendedFeeds()),
            ...cacheStrategies.recommendations,
          });
        },
        cooldown: 10 * 60 * 1000, // 10 minutes
      },

      // Medium priority: User subscriptions
      {
        key: 'subscriptions',
        priority: PrefetchPriority.MEDIUM,
        condition: () => ['/articles', '/recommendations'].includes(window.location.pathname),
        action: async () => {
          await this.queryClient.prefetchQuery({
            queryKey: ['subscriptions'],
            queryFn: () => import('../api/feeds').then((api) => api.fetchFeeds()),
            ...cacheStrategies.subscriptions,
          });
        },
        cooldown: 15 * 60 * 1000, // 15 minutes
      },

      // Low priority: System status
      {
        key: 'system-status',
        priority: PrefetchPriority.LOW,
        condition: () => this.userBehavior.pageViews.includes('/system-status'),
        action: async () => {
          await this.queryClient.prefetchQuery({
            queryKey: ['system', 'status'],
            queryFn: () => import('../api/scheduler').then((api) => api.getSchedulerStatus()),
            ...cacheStrategies.systemStatus,
          });
        },
        cooldown: 30 * 60 * 1000, // 30 minutes
      },

      // Low priority: Analytics data - commented out as function doesn't exist
      // {
      //   key: 'analytics',
      //   priority: PrefetchPriority.LOW,
      //   condition: () => this.userBehavior.timeSpent['/analytics'] > 30000, // 30 seconds
      //   action: async () => {
      //     await this.queryClient.prefetchQuery({
      //       queryKey: ['analytics', 'overview'],
      //       queryFn: () => import('../api/analytics').then((api) => api.getAnalyticsOverview()),
      //       ...cacheStrategies.analytics,
      //     });
      //   },
      //   cooldown: 60 * 60 * 1000, // 1 hour
      // },
    ];
  }

  /**
   * Execute prefetch actions based on priority and conditions
   */
  async executePrefetching() {
    if (!this.isOnline) return;

    const actions = this.getPrefetchActions();
    const now = Date.now();

    // Filter actions based on conditions and cooldown
    const eligibleActions = actions.filter((action) => {
      const lastPrefetch = this.prefetchHistory.get(action.key) || 0;
      const cooldownPassed = !action.cooldown || now - lastPrefetch > action.cooldown;

      return action.condition() && cooldownPassed;
    });

    // Sort by priority
    const priorityOrder = {
      [PrefetchPriority.HIGH]: 3,
      [PrefetchPriority.MEDIUM]: 2,
      [PrefetchPriority.LOW]: 1,
    };

    eligibleActions.sort((a, b) => priorityOrder[b.priority] - priorityOrder[a.priority]);

    // Limit concurrent prefetches based on connection speed
    const maxConcurrent = this.connectionSpeed === 'slow' ? 1 : 3;
    const actionsToExecute = eligibleActions.slice(0, maxConcurrent);

    // Execute prefetch actions
    const promises = actionsToExecute.map(async (action) => {
      try {
        await action.action();
        this.prefetchHistory.set(action.key, now);

        if (process.env.NODE_ENV === 'development') {
          logger.debug(`✅ Prefetched: ${action.key}`);
        }
      } catch (error) {
        logger.warn(`❌ Prefetch failed: ${action.key}`, error);
      }
    });

    await Promise.allSettled(promises);
  }

  /**
   * Resume prefetching when connection is restored
   */
  private resumePrefetching() {
    // Wait a bit for connection to stabilize
    setTimeout(() => {
      this.executePrefetching();
    }, 1000);
  }

  /**
   * Start intelligent prefetching
   */
  start() {
    if (typeof window === 'undefined') return;

    // Initial prefetch
    setTimeout(() => {
      this.executePrefetching();
    }, 2000); // Wait 2 seconds after page load

    // Setup periodic prefetching
    const interval = setInterval(() => {
      this.executePrefetching();
    }, 30 * 1000); // Every 30 seconds

    // Setup idle prefetching
    if ('requestIdleCallback' in window) {
      const idlePrefetch = () => {
        requestIdleCallback(() => {
          this.executePrefetching();
          // Schedule next idle prefetch
          setTimeout(idlePrefetch, 60 * 1000); // Every minute
        });
      };
      idlePrefetch();
    }

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
      clearInterval(interval);
    });
  }

  /**
   * Manual prefetch for specific data
   */
  async prefetch(key: string, queryFn: () => Promise<any>, options = {}) {
    if (!this.isOnline) return;

    try {
      await this.queryClient.prefetchQuery({
        queryKey: [key],
        queryFn,
        ...options,
      });

      if (process.env.NODE_ENV === 'development') {
        logger.debug(`✅ Manual prefetch: ${key}`);
      }
    } catch (error) {
      logger.warn(`❌ Manual prefetch failed: ${key}`, error);
    }
  }

  /**
   * Get prefetch statistics
   */
  getStats() {
    return {
      totalPrefetches: this.prefetchHistory.size,
      recentPrefetches: Array.from(this.prefetchHistory.entries()).filter(
        ([, time]) => Date.now() - time < 60 * 60 * 1000
      ).length, // Last hour
      connectionSpeed: this.connectionSpeed,
      isOnline: this.isOnline,
      userBehavior: {
        totalPageViews: this.userBehavior.pageViews.length,
        uniquePages: new Set(this.userBehavior.pageViews).size,
        averageTimePerPage:
          Object.values(this.userBehavior.timeSpent).reduce((a, b) => a + b, 0) /
            Object.keys(this.userBehavior.timeSpent).length || 0,
      },
    };
  }
}

/**
 * Create and initialize intelligent prefetcher
 */
export function createIntelligentPrefetcher(queryClient: QueryClient): IntelligentPrefetcher {
  const prefetcher = new IntelligentPrefetcher(queryClient);

  // Start prefetching when DOM is ready
  if (typeof window !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => prefetcher.start());
    } else {
      prefetcher.start();
    }
  }

  return prefetcher;
}
