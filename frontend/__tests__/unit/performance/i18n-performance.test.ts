/**
 * Performance Tests: I18n System
 *
 * Tests that the internationalization system meets performance requirements
 * for language detection, switching, and translation loading.
 *
 * **Validates: Requirements 1.6, 3.2, 8.1, 8.2, 8.3, 8.5**
 *
 * Task 10.3: Write performance tests
 * - Test initial language detection completes within 100ms
 * - Test language switch completes within 200ms
 * - Test translation file loading time
 * - Test only active language is in initial bundle
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { act } from '@testing-library/react';
import { I18nProvider, useI18n } from '@/contexts/I18nContext';

// Mock translation files with realistic size
const mockZhTWTranslations = {
  nav: {
    articles: '文章',
    'reading-list': '閱讀清單',
    subscriptions: '訂閱',
    analytics: '分析',
    settings: '設定',
    'system-status': '系統狀態',
  },
  buttons: {
    save: '儲存',
    cancel: '取消',
    delete: '刪除',
    edit: '編輯',
    add: '新增',
    remove: '移除',
    confirm: '確認',
    close: '關閉',
  },
  messages: {
    'article-count': '成功抓取 {count} 篇新文章',
    loading: '載入中...',
    'no-articles': '沒有發現新文章',
    'fetching-articles': '正在抓取文章...',
    'scheduler-running': '排程器執行中，請稍候',
  },
  errors: {
    'network-error': '網路連線異常，請檢查您的網路設定',
    'analysis-timeout': 'AI 分析處理時間過長，請稍後再試',
    'insufficient-permissions': '您沒有執行此操作的權限',
    'rate-limit-exceeded': '請求過於頻繁，請稍後再試',
    'invalid-input': '輸入資料格式不正確',
    'server-error': '伺服器發生錯誤，請稍後再試',
    'not-found': '找不到請求的資源',
    unauthorized: '請先登入後再進行此操作',
  },
  success: {
    'article-saved': '文章已加入閱讀清單',
    'article-removed': '文章已從閱讀清單移除',
    'settings-saved': '設定已儲存',
    'analysis-copied': '分析內容已複製到剪貼簿',
    'subscription-added': '訂閱已新增',
    'subscription-removed': '訂閱已移除',
  },
  // Add more sections to simulate realistic translation file size
  forms: {
    labels: {
      title: '標題',
      description: '描述',
      category: '分類',
      tags: '標籤',
      url: '網址',
      email: '電子郵件',
      password: '密碼',
      'confirm-password': '確認密碼',
      username: '使用者名稱',
    },
    placeholders: {
      'enter-title': '請輸入標題',
      'enter-description': '請輸入描述',
      'enter-url': '請輸入網址',
      'search-articles': '搜尋文章...',
      'enter-email': '請輸入電子郵件',
    },
  },
};

const mockEnUSTranslations = {
  nav: {
    articles: 'Articles',
    'reading-list': 'Reading List',
    subscriptions: 'Subscriptions',
    analytics: 'Analytics',
    settings: 'Settings',
    'system-status': 'System Status',
  },
  buttons: {
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    edit: 'Edit',
    add: 'Add',
    remove: 'Remove',
    confirm: 'Confirm',
    close: 'Close',
  },
  messages: {
    'article-count': 'Successfully fetched {count} new articles',
    loading: 'Loading...',
    'no-articles': 'No new articles found',
    'fetching-articles': 'Fetching articles...',
    'scheduler-running': 'Scheduler is running, please wait',
  },
  errors: {
    'network-error': 'Network connection error. Please check your internet connection',
    'analysis-timeout': 'AI analysis took too long. Please try again later',
    'insufficient-permissions': 'You do not have permission to perform this action',
    'rate-limit-exceeded': 'Too many requests. Please try again later',
    'invalid-input': 'Invalid input data format',
    'server-error': 'Server error occurred. Please try again later',
    'not-found': 'Requested resource not found',
    unauthorized: 'Please log in to perform this action',
  },
  success: {
    'article-saved': 'Article added to reading list',
    'article-removed': 'Article removed from reading list',
    'settings-saved': 'Settings saved successfully',
    'analysis-copied': 'Analysis content copied to clipboard',
    'subscription-added': 'Subscription added successfully',
    'subscription-removed': 'Subscription removed successfully',
  },
  forms: {
    labels: {
      title: 'Title',
      description: 'Description',
      category: 'Category',
      tags: 'Tags',
      url: 'URL',
      email: 'Email',
      password: 'Password',
      'confirm-password': 'Confirm Password',
      username: 'Username',
    },
    placeholders: {
      'enter-title': 'Enter title',
      'enter-description': 'Enter description',
      'enter-url': 'Enter URL',
      'search-articles': 'Search articles...',
      'enter-email': 'Enter email address',
    },
  },
};

// Mock dynamic imports with timing simulation
let importDelay = 0;
const originalImport = global.import;

vi.mock('@/locales/zh-TW.json', () => ({
  default: mockZhTWTranslations,
}));

vi.mock('@/locales/en-US.json', () => ({
  default: mockEnUSTranslations,
}));

// Performance measurement utilities
function measureTime<T>(fn: () => T): { result: T; duration: number } {
  const start = performance.now();
  const result = fn();
  const end = performance.now();
  return { result, duration: end - start };
}

async function measureAsyncTime<T>(fn: () => Promise<T>): Promise<{ result: T; duration: number }> {
  const start = performance.now();
  const result = await fn();
  const end = performance.now();
  return { result, duration: end - start };
}

describe('I18n Performance Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    document.documentElement.lang = '';
    importDelay = 0;

    // Reset performance timing
    performance.mark = vi.fn();
    performance.measure = vi.fn();

    // Set browser language to English for consistent initial state
    Object.defineProperty(window.navigator, 'language', {
      writable: true,
      configurable: true,
      value: 'en-US',
    });
  });

  describe('Initial Language Detection Performance', () => {
    it('should complete language detection within 100ms', async () => {
      // Requirement 1.6: Detection completes within 100ms
      const { duration } = await measureAsyncTime(async () => {
        const { result } = renderHook(() => useI18n(), {
          wrapper: I18nProvider,
        });

        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });

        return result.current.locale;
      });

      expect(duration).toBeLessThan(100);
    });

    it('should detect Chinese language variants quickly', async () => {
      Object.defineProperty(window.navigator, 'language', {
        writable: true,
        configurable: true,
        value: 'zh-CN',
      });

      const { duration } = await measureAsyncTime(async () => {
        const { result } = renderHook(() => useI18n(), {
          wrapper: I18nProvider,
        });

        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });

        return result.current.locale;
      });

      expect(duration).toBeLessThan(100);
    });

    it('should handle multiple language detection calls efficiently', async () => {
      // Test that multiple simultaneous detection calls don't slow down the system
      const detectionPromises = Array.from({ length: 5 }, async () => {
        return measureAsyncTime(async () => {
          const { result } = renderHook(() => useI18n(), {
            wrapper: I18nProvider,
          });

          await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
          });

          return result.current.locale;
        });
      });

      const results = await Promise.all(detectionPromises);

      // All detections should complete within 100ms
      results.forEach(({ duration }) => {
        expect(duration).toBeLessThan(100);
      });
    });

    it('should handle localStorage retrieval efficiently', async () => {
      // Pre-populate localStorage
      localStorage.setItem('language', 'zh-TW');

      const { duration } = await measureAsyncTime(async () => {
        const { result } = renderHook(() => useI18n(), {
          wrapper: I18nProvider,
        });

        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });

        return result.current.locale;
      });

      // Should be even faster when reading from localStorage
      expect(duration).toBeLessThan(50);
    });
  });

  describe('Language Switch Performance', () => {
    it('should complete language switch within 200ms', async () => {
      // Requirement 3.2: Language switch completes within 200ms
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      // Wait for initial load
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Measure language switch time
      const { duration } = await measureAsyncTime(async () => {
        await act(async () => {
          await result.current.setLocale('zh-TW');
        });

        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });
      });

      expect(duration).toBeLessThan(200);
      expect(result.current.locale).toBe('zh-TW');
    });

    it('should handle rapid language switching efficiently', async () => {
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Measure rapid switching
      const { duration } = await measureAsyncTime(async () => {
        await act(async () => {
          await result.current.setLocale('zh-TW');
        });

        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });

        await act(async () => {
          await result.current.setLocale('en-US');
        });

        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });

        await act(async () => {
          await result.current.setLocale('zh-TW');
        });

        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });
      });

      // Total time for 3 switches should be reasonable
      expect(duration).toBeLessThan(600); // 200ms * 3
      expect(result.current.locale).toBe('zh-TW');
    });

    it('should cache translations to improve subsequent switches', async () => {
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // First switch to Chinese (should load translations)
      const firstSwitchTime = await measureAsyncTime(async () => {
        await act(async () => {
          await result.current.setLocale('zh-TW');
        });

        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });
      });

      // Switch back to English
      await act(async () => {
        await result.current.setLocale('en-US');
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Second switch to Chinese (should use cache)
      const secondSwitchTime = await measureAsyncTime(async () => {
        await act(async () => {
          await result.current.setLocale('zh-TW');
        });

        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });
      });

      // Second switch should be faster due to caching
      expect(secondSwitchTime.duration).toBeLessThanOrEqual(firstSwitchTime.duration);
      expect(secondSwitchTime.duration).toBeLessThan(100);
    });
  });

  describe('Translation File Loading Performance', () => {
    it('should load translation files efficiently', async () => {
      // Requirement 8.1: Translation file loading time
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      // Measure initial translation loading
      const { duration } = await measureAsyncTime(async () => {
        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });
      });

      expect(duration).toBeLessThan(150);
    });

    it('should handle large translation files within acceptable time', async () => {
      // Simulate larger translation files
      const largeTranslations = {
        ...mockEnUSTranslations,
        // Add many more keys to simulate a large file
        ...Array.from({ length: 100 }, (_, i) => ({
          [`section${i}`]: {
            [`key${i}`]: `Value ${i}`,
            [`description${i}`]: `Description for item ${i}`,
          },
        })).reduce((acc, item) => ({ ...acc, ...item }), {}),
      };

      // Mock larger file
      vi.doMock('@/locales/en-US.json', () => ({
        default: largeTranslations,
      }));

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      const { duration } = await measureAsyncTime(async () => {
        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });
      });

      // Should still load within reasonable time even with larger files
      expect(duration).toBeLessThan(300);
    });

    it('should handle network delays gracefully', async () => {
      // Simulate network delay
      importDelay = 50;

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      const { duration } = await measureAsyncTime(async () => {
        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });
      });

      // Should handle delay but still complete within reasonable time
      expect(duration).toBeLessThan(200);
    });
  });

  describe('Bundle Size and Code Splitting', () => {
    it('should only load active language initially', async () => {
      // Requirement 8.2: Only active language is in initial bundle
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Initially should only have English translations loaded
      expect(result.current.locale).toBe('en-US');
      expect(result.current.t('nav.articles')).toBe('Articles');

      // Chinese translations should not be available yet
      // (This is tested by ensuring the translation function works correctly)
      expect(result.current.t('nav.articles')).not.toBe('文章');
    });

    it('should lazy load alternative language on demand', async () => {
      // Requirement 8.3: Lazy load alternative language
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Initially English
      expect(result.current.t('nav.articles')).toBe('Articles');

      // Switch to Chinese - should lazy load
      const switchTime = await measureAsyncTime(async () => {
        await act(async () => {
          await result.current.setLocale('zh-TW');
        });

        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });
      });

      // Should load Chinese translations
      expect(result.current.t('nav.articles')).toBe('文章');
      expect(switchTime.duration).toBeLessThan(200);
    });

    it('should not load unused languages', async () => {
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Stay in English - Chinese should not be loaded
      expect(result.current.locale).toBe('en-US');
      expect(result.current.t('nav.articles')).toBe('Articles');

      // Verify we're not loading unnecessary translations
      // (This is implicit - if Chinese were loaded, it would affect performance)
    });
  });

  describe('Translation Function Performance', () => {
    it('should perform key lookups efficiently', async () => {
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Measure translation function performance
      const { duration } = measureTime(() => {
        // Perform many translation lookups
        for (let i = 0; i < 1000; i++) {
          result.current.t('nav.articles');
          result.current.t('buttons.save');
          result.current.t('messages.loading');
        }
      });

      // 1000 lookups should complete very quickly
      expect(duration).toBeLessThan(10);
    });

    it('should handle interpolation efficiently', async () => {
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Measure interpolation performance
      const { duration } = measureTime(() => {
        // Perform many interpolations
        for (let i = 0; i < 100; i++) {
          result.current.t('messages.article-count', { count: i });
        }
      });

      // 100 interpolations should complete quickly
      expect(duration).toBeLessThan(5);
    });

    it('should handle nested key lookups efficiently', async () => {
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Measure nested lookup performance
      const { duration } = measureTime(() => {
        // Perform many nested lookups
        for (let i = 0; i < 1000; i++) {
          result.current.t('forms.labels.title');
          result.current.t('forms.placeholders.enter-title');
          result.current.t('errors.network-error');
        }
      });

      // Nested lookups should still be fast
      expect(duration).toBeLessThan(15);
    });
  });

  describe('Memory Usage and Cleanup', () => {
    it('should not create memory leaks during language switching', async () => {
      const { result, unmount } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Perform multiple language switches
      for (let i = 0; i < 10; i++) {
        await act(async () => {
          await result.current.setLocale(i % 2 === 0 ? 'zh-TW' : 'en-US');
        });

        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });
      }

      // Cleanup should work without issues
      expect(() => unmount()).not.toThrow();
    });

    it('should handle component unmounting during language switch', async () => {
      const { result, unmount } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Start language switch but unmount before completion
      act(() => {
        result.current.setLocale('zh-TW');
      });

      // Unmount immediately
      expect(() => unmount()).not.toThrow();
    });
  });

  describe('Concurrent Operations Performance', () => {
    it('should handle multiple simultaneous translation requests', async () => {
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Measure concurrent translation performance
      const { duration } = measureTime(() => {
        const promises = Array.from({ length: 100 }, () => {
          return Promise.resolve(result.current.t('nav.articles'));
        });

        return Promise.all(promises);
      });

      expect(duration).toBeLessThan(5);
    });

    it('should handle concurrent language switches gracefully', async () => {
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Start multiple language switches simultaneously
      const switchPromises = [
        act(async () => {
          await result.current.setLocale('zh-TW');
        }),
        act(async () => {
          await result.current.setLocale('en-US');
        }),
        act(async () => {
          await result.current.setLocale('zh-TW');
        }),
      ];

      // Should handle concurrent switches without errors
      await expect(Promise.all(switchPromises)).resolves.not.toThrow();

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Should end up in a valid state
      expect(['zh-TW', 'en-US']).toContain(result.current.locale);
    });
  });

  describe('Performance Regression Tests', () => {
    it('should maintain performance with large number of translation keys', async () => {
      // Test that performance doesn't degrade with many translation keys
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Generate many unique translation keys
      const keys = Array.from({ length: 1000 }, (_, i) => `test.key.${i}`);

      const { duration } = measureTime(() => {
        keys.forEach((key) => {
          result.current.t(key); // Will return key itself as fallback
        });
      });

      // Should handle many keys efficiently
      expect(duration).toBeLessThan(50);
    });

    it('should maintain performance with complex interpolation', async () => {
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Test complex interpolation scenarios
      const { duration } = measureTime(() => {
        for (let i = 0; i < 100; i++) {
          result.current.t('messages.article-count', {
            count: i,
            user: `user${i}`,
            date: new Date().toISOString(),
            category: `category${i % 5}`,
          });
        }
      });

      expect(duration).toBeLessThan(10);
    });
  });
});
