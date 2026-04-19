/**
 * Unit tests for i18n type definitions
 * Validates that the TypeScript types are correctly defined and usable
 */

import { vi } from 'vitest';
import type {
  Locale,
  TranslationKey,
  TranslationVariables,
  TranslationFunction,
  I18nContextType,
  TranslationFile,
} from '@/types/i18n';

describe('i18n Types', () => {
  describe('Locale', () => {
    it('should accept valid locale values', () => {
      const zhTW: Locale = 'zh-TW';
      const enUS: Locale = 'en-US';

      expect(zhTW).toBe('zh-TW');
      expect(enUS).toBe('en-US');
    });
  });

  describe('TranslationKey', () => {
    it('should accept string values', () => {
      const key: TranslationKey = 'nav.articles';
      expect(key).toBe('nav.articles');
    });

    it('should accept nested key paths', () => {
      const key: TranslationKey = 'errors.network-error';
      expect(key).toBe('errors.network-error');
    });
  });

  describe('TranslationVariables', () => {
    it('should accept string and number values', () => {
      const variables: TranslationVariables = {
        count: 5,
        name: 'Test',
        value: 100,
      };

      expect(variables.count).toBe(5);
      expect(variables.name).toBe('Test');
      expect(variables.value).toBe(100);
    });
  });

  describe('TranslationFunction', () => {
    it('should accept key and return string', () => {
      const mockT: TranslationFunction = (key) => `translated-${key}`;
      const result = mockT('nav.articles');

      expect(result).toBe('translated-nav.articles');
    });

    it('should accept key with variables', () => {
      const mockT: TranslationFunction = (key, variables) => {
        if (variables?.count) {
          return `${key}-${variables.count}`;
        }
        return key;
      };

      const result = mockT('messages.article-count', { count: 5 });
      expect(result).toBe('messages.article-count-5');
    });
  });

  describe('I18nContextType', () => {
    it('should have all required properties', () => {
      const mockContext: I18nContextType = {
        locale: 'en-US',
        setLocale: vi.fn(),
        t: vi.fn((key) => key),
        isLoading: false,
      };

      expect(mockContext.locale).toBe('en-US');
      expect(mockContext.isLoading).toBe(false);
      expect(typeof mockContext.setLocale).toBe('function');
      expect(typeof mockContext.t).toBe('function');
    });

    it('should allow locale changes', () => {
      const setLocaleMock = vi.fn();
      const mockContext: I18nContextType = {
        locale: 'en-US',
        setLocale: setLocaleMock,
        t: vi.fn((key) => key),
        isLoading: false,
      };

      mockContext.setLocale('zh-TW');
      expect(setLocaleMock).toHaveBeenCalledWith('zh-TW');
    });
  });

  describe('TranslationFile', () => {
    it('should match expected structure', () => {
      const mockTranslations: TranslationFile = {
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
          submit: 'Submit',
          reset: 'Reset',
          back: 'Back',
          next: 'Next',
          finish: 'Finish',
          retry: 'Retry',
          refresh: 'Refresh',
        },
        messages: {
          loading: 'Loading...',
          'article-count': 'Successfully fetched {count} articles',
          'no-articles': 'No articles found',
          'fetching-articles': 'Fetching articles...',
          'scheduler-running': 'Scheduler is running',
          processing: 'Processing...',
          success: 'Success',
          error: 'Error',
        },
        errors: {
          'network-error': 'Network error',
          'analysis-timeout': 'Analysis timeout',
          'insufficient-permissions': 'Insufficient permissions',
          'rate-limit-exceeded': 'Rate limit exceeded',
          'invalid-input': 'Invalid input',
          'server-error': 'Server error',
          'not-found': 'Not found',
          unauthorized: 'Unauthorized',
          'unknown-error': 'Unknown error',
        },
        success: {
          'article-saved': 'Article saved',
          'article-removed': 'Article removed',
          'settings-saved': 'Settings saved',
          'analysis-copied': 'Analysis copied',
          'subscription-added': 'Subscription added',
          'subscription-removed': 'Subscription removed',
        },
        'tinkering-index': {
          'level-1': 'Beginner',
          'level-1-desc': 'Suitable for beginners',
          'level-2': 'Basic',
          'level-2-desc': 'Requires basic knowledge',
          'level-3': 'Intermediate',
          'level-3-desc': 'Requires some experience',
          'level-4': 'Advanced',
          'level-4-desc': 'Requires deep understanding',
          'level-5': 'Expert',
          'level-5-desc': 'Requires professional knowledge',
        },
        sort: {
          date: 'Date',
          'tinkering-index': 'Technical Depth',
          category: 'Category',
          title: 'Title',
        },
        theme: {
          light: 'Light',
          dark: 'Dark',
          system: 'System',
        },
        'notification-frequency': {
          immediate: 'Immediate',
          daily: 'Daily',
          weekly: 'Weekly',
          disabled: 'Disabled',
        },
      };

      expect(mockTranslations.nav.articles).toBe('Articles');
      expect(mockTranslations.buttons.save).toBe('Save');
      expect(mockTranslations.messages.loading).toBe('Loading...');
      expect(mockTranslations.errors['network-error']).toBe('Network error');
      expect(mockTranslations.success['article-saved']).toBe('Article saved');
      expect(mockTranslations['tinkering-index']['level-1']).toBe('Beginner');
      expect(mockTranslations.sort.date).toBe('Date');
      expect(mockTranslations.theme.light).toBe('Light');
      expect(mockTranslations['notification-frequency'].immediate).toBe('Immediate');
    });
  });
});
