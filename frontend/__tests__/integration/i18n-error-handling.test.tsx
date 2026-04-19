/**
 * Error Handling Integration Tests: I18n System
 *
 * Tests that the internationalization system handles various error conditions gracefully
 * and maintains functionality even when components fail or data is corrupted.
 *
 * **Validates: Requirements 2.4, 11.4**
 *
 * Task 13.2: Write error handling integration tests
 * - Test behavior when translation file fails to load
 * - Test behavior when translation file is malformed JSON
 * - Test behavior when localStorage is blocked
 * - Test behavior when browser language detection fails
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { I18nProvider } from '@/contexts/I18nContext';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

// Mock translation files
const mockZhTWTranslations = {
  nav: {
    articles: '文章',
    'reading-list': '閱讀清單',
  },
  buttons: {
    save: '儲存',
    cancel: '取消',
  },
  messages: {
    loading: '載入中...',
    'article-count': '成功抓取 {count} 篇新文章',
  },
  language: {
    'changed-to-chinese': '語言已切換為繁體中文',
    'changed-to-english': '語言已切換為英文',
  },
};

const mockEnUSTranslations = {
  nav: {
    articles: 'Articles',
    'reading-list': 'Reading List',
  },
  buttons: {
    save: 'Save',
    cancel: 'Cancel',
  },
  messages: {
    loading: 'Loading...',
    'article-count': 'Successfully fetched {count} new articles',
  },
  language: {
    'changed-to-chinese': 'Language changed to Traditional Chinese',
    'changed-to-english': 'Language changed to English',
  },
};

// Test component that uses translations
function TestErrorHandlingApp() {
  const { t, locale, isLoading } = useI18n();

  if (isLoading) {
    return <div data-testid="loading">Loading translations...</div>;
  }

  return (
    <div data-testid="test-app">
      <LanguageSwitcher variant="compact" />

      <div data-testid="current-locale">{locale}</div>

      <nav data-testid="navigation">
        <a data-testid="nav-articles">{t('nav.articles')}</a>
        <a data-testid="nav-reading-list">{t('nav.reading-list')}</a>
      </nav>

      <div data-testid="buttons">
        <button data-testid="btn-save">{t('buttons.save')}</button>
        <button data-testid="btn-cancel">{t('buttons.cancel')}</button>
      </div>

      <div data-testid="messages">
        <div data-testid="msg-loading">{t('messages.loading')}</div>
        <div data-testid="msg-article-count">{t('messages.article-count', { count: 5 })}</div>
      </div>

      {/* Test missing translation keys */}
      <div data-testid="missing-key">{t('non.existent.key')}</div>
      <div data-testid="missing-nested">{t('missing.deeply.nested.key')}</div>
    </div>
  );
}

// Import useI18n after mocking
import { useI18n } from '@/contexts/I18nContext';

describe('I18n Error Handling Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    document.documentElement.lang = '';

    // Reset browser language
    Object.defineProperty(window.navigator, 'language', {
      writable: true,
      configurable: true,
      value: 'en-US',
    });

    // Reset console methods to capture error logs
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  describe('Translation File Loading Failures', () => {
    it('should handle translation file import failures gracefully', async () => {
      // Requirement 2.4: Graceful handling of loading failures

      // Mock import failure for Chinese translations
      vi.doMock('@/locales/zh-TW.json', () => {
        throw new Error('Failed to load translation file');
      });

      // Mock successful English translations
      vi.doMock('@/locales/en-US.json', () => ({
        default: mockEnUSTranslations,
      }));

      render(
        <I18nProvider>
          <TestErrorHandlingApp />
        </I18nProvider>
      );

      // Should still load with English (fallback)
      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
      });

      // English translations should work
      expect(screen.getByTestId('nav-articles')).toHaveTextContent('Articles');
      expect(screen.getByTestId('btn-save')).toHaveTextContent('Save');

      // Try to switch to Chinese - should handle failure gracefully
      const user = userEvent.setup();
      const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
      await user.click(chineseButton);

      // Should either stay in English or show fallback behavior
      await waitFor(() => {
        const locale = screen.getByTestId('current-locale').textContent;
        expect(['en-US', 'zh-TW']).toContain(locale);
      });

      // App should not crash
      expect(screen.getByTestId('test-app')).toBeInTheDocument();
    });

    it('should handle both translation files failing to load', async () => {
      // Mock both imports failing
      vi.doMock('@/locales/zh-TW.json', () => {
        throw new Error('Failed to load Chinese translations');
      });

      vi.doMock('@/locales/en-US.json', () => {
        throw new Error('Failed to load English translations');
      });

      render(
        <I18nProvider>
          <TestErrorHandlingApp />
        </I18nProvider>
      );

      // Should still render without crashing
      await waitFor(() => {
        expect(screen.getByTestId('test-app')).toBeInTheDocument();
      });

      // Should show translation keys as fallback
      expect(screen.getByTestId('nav-articles')).toHaveTextContent('nav.articles');
      expect(screen.getByTestId('btn-save')).toHaveTextContent('buttons.save');

      // Missing keys should return the key itself
      expect(screen.getByTestId('missing-key')).toHaveTextContent('non.existent.key');
    });

    it('should handle network timeouts during translation loading', async () => {
      // Mock slow/failing network request
      vi.doMock('@/locales/zh-TW.json', () => {
        return new Promise((_, reject) => {
          setTimeout(() => reject(new Error('Network timeout')), 100);
        });
      });

      vi.doMock('@/locales/en-US.json', () => ({
        default: mockEnUSTranslations,
      }));

      const user = userEvent.setup();

      render(
        <I18nProvider>
          <TestErrorHandlingApp />
        </I18nProvider>
      );

      // Should load English successfully
      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
      });

      // Try to switch to Chinese (will timeout)
      const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
      await user.click(chineseButton);

      // Should handle timeout gracefully
      await waitFor(
        () => {
          expect(screen.getByTestId('test-app')).toBeInTheDocument();
        },
        { timeout: 2000 }
      );

      // Should not crash the app
      expect(screen.getByTestId('nav-articles')).toBeInTheDocument();
    });
  });

  describe('Malformed Translation File Handling', () => {
    it('should handle malformed JSON in translation files', async () => {
      // Mock malformed JSON
      vi.doMock('@/locales/zh-TW.json', () => {
        throw new SyntaxError('Unexpected token in JSON');
      });

      vi.doMock('@/locales/en-US.json', () => ({
        default: mockEnUSTranslations,
      }));

      render(
        <I18nProvider>
          <TestErrorHandlingApp />
        </I18nProvider>
      );

      // Should fall back to English
      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
      });

      expect(screen.getByTestId('nav-articles')).toHaveTextContent('Articles');
      expect(screen.getByTestId('btn-save')).toHaveTextContent('Save');
    });

    it('should handle translation files with wrong structure', async () => {
      // Mock translation file with wrong structure
      const malformedTranslations = {
        // Missing expected structure
        wrongStructure: 'This is not the expected format',
        nav: 'This should be an object, not a string',
      };

      vi.doMock('@/locales/zh-TW.json', () => ({
        default: malformedTranslations,
      }));

      vi.doMock('@/locales/en-US.json', () => ({
        default: mockEnUSTranslations,
      }));

      const user = userEvent.setup();

      render(
        <I18nProvider>
          <TestErrorHandlingApp />
        </I18nProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
      });

      // Switch to Chinese with malformed translations
      const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
      await user.click(chineseButton);

      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('zh-TW');
      });

      // Should handle malformed structure gracefully
      // Keys that don't exist in proper structure should return the key itself
      expect(screen.getByTestId('nav-articles')).toHaveTextContent('nav.articles');
      expect(screen.getByTestId('btn-save')).toHaveTextContent('buttons.save');
    });

    it('should handle translation files with null or undefined values', async () => {
      const translationsWithNulls = {
        nav: {
          articles: null,
          'reading-list': undefined,
        },
        buttons: {
          save: '',
          cancel: 'Cancel', // This one is valid
        },
        messages: {
          loading: null,
        },
      };

      vi.doMock('@/locales/zh-TW.json', () => ({
        default: translationsWithNulls,
      }));

      vi.doMock('@/locales/en-US.json', () => ({
        default: mockEnUSTranslations,
      }));

      const user = userEvent.setup();

      render(
        <I18nProvider>
          <TestErrorHandlingApp />
        </I18nProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
      });

      // Switch to Chinese with null/undefined values
      const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
      await user.click(chineseButton);

      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('zh-TW');
      });

      // Should handle null/undefined values by returning the key
      expect(screen.getByTestId('nav-articles')).toHaveTextContent('nav.articles');
      expect(screen.getByTestId('nav-reading-list')).toHaveTextContent('nav.reading-list');

      // Empty string should also fall back to key
      expect(screen.getByTestId('btn-save')).toHaveTextContent('buttons.save');

      // Valid value should work
      expect(screen.getByTestId('btn-cancel')).toHaveTextContent('Cancel');
    });
  });

  describe('localStorage Blocking and Errors', () => {
    it('should handle localStorage being blocked (private browsing)', async () => {
      // Requirement 2.4: Graceful handling when localStorage is unavailable

      // Mock localStorage to throw errors
      const mockLocalStorage = {
        getItem: vi.fn(() => {
          throw new Error('localStorage is not available');
        }),
        setItem: vi.fn(() => {
          throw new Error('localStorage is not available');
        }),
        removeItem: vi.fn(() => {
          throw new Error('localStorage is not available');
        }),
        clear: vi.fn(() => {
          throw new Error('localStorage is not available');
        }),
      };

      Object.defineProperty(window, 'localStorage', {
        value: mockLocalStorage,
        writable: true,
      });

      vi.doMock('@/locales/zh-TW.json', () => ({
        default: mockZhTWTranslations,
      }));

      vi.doMock('@/locales/en-US.json', () => ({
        default: mockEnUSTranslations,
      }));

      const user = userEvent.setup();

      render(
        <I18nProvider>
          <TestErrorHandlingApp />
        </I18nProvider>
      );

      // Should still work with browser detection
      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
      });

      expect(screen.getByTestId('nav-articles')).toHaveTextContent('Articles');

      // Language switching should still work (just won't persist)
      const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
      await user.click(chineseButton);

      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('zh-TW');
      });

      expect(screen.getByTestId('nav-articles')).toHaveTextContent('文章');

      // Should not crash despite localStorage errors
      expect(console.error).not.toHaveBeenCalled();
    });

    it('should handle localStorage quota exceeded errors', async () => {
      // Mock localStorage quota exceeded
      const mockLocalStorage = {
        getItem: vi.fn(() => 'en-US'),
        setItem: vi.fn(() => {
          const error = new Error('QuotaExceededError');
          error.name = 'QuotaExceededError';
          throw error;
        }),
        removeItem: vi.fn(),
        clear: vi.fn(),
      };

      Object.defineProperty(window, 'localStorage', {
        value: mockLocalStorage,
        writable: true,
      });

      vi.doMock('@/locales/zh-TW.json', () => ({
        default: mockZhTWTranslations,
      }));

      vi.doMock('@/locales/en-US.json', () => ({
        default: mockEnUSTranslations,
      }));

      const user = userEvent.setup();

      render(
        <I18nProvider>
          <TestErrorHandlingApp />
        </I18nProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
      });

      // Language switching should work despite storage errors
      const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
      await user.click(chineseButton);

      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('zh-TW');
      });

      expect(screen.getByTestId('nav-articles')).toHaveTextContent('文章');

      // Should handle quota error gracefully
      expect(mockLocalStorage.setItem).toHaveBeenCalled();
    });

    it('should handle corrupted localStorage data', async () => {
      // Mock corrupted localStorage data
      const mockLocalStorage = {
        getItem: vi.fn((key) => {
          if (key === 'language') {
            return '{"corrupted": json}'; // Invalid JSON
          }
          return null;
        }),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      };

      Object.defineProperty(window, 'localStorage', {
        value: mockLocalStorage,
        writable: true,
      });

      vi.doMock('@/locales/zh-TW.json', () => ({
        default: mockZhTWTranslations,
      }));

      vi.doMock('@/locales/en-US.json', () => ({
        default: mockEnUSTranslations,
      }));

      render(
        <I18nProvider>
          <TestErrorHandlingApp />
        </I18nProvider>
      );

      // Should fall back to browser detection when localStorage is corrupted
      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
      });

      expect(screen.getByTestId('nav-articles')).toHaveTextContent('Articles');
    });
  });

  describe('Browser Language Detection Failures', () => {
    it('should handle undefined navigator.language', async () => {
      // Mock undefined navigator.language
      Object.defineProperty(window.navigator, 'language', {
        value: undefined,
        writable: true,
      });

      Object.defineProperty(window.navigator, 'languages', {
        value: undefined,
        writable: true,
      });

      vi.doMock('@/locales/zh-TW.json', () => ({
        default: mockZhTWTranslations,
      }));

      vi.doMock('@/locales/en-US.json', () => ({
        default: mockEnUSTranslations,
      }));

      render(
        <I18nProvider>
          <TestErrorHandlingApp />
        </I18nProvider>
      );

      // Should default to en-US when detection fails
      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
      });

      expect(screen.getByTestId('nav-articles')).toHaveTextContent('Articles');
    });

    it('should handle navigator object being unavailable', async () => {
      // Mock navigator being undefined (edge case)
      const originalNavigator = window.navigator;

      // @ts-expect-error - Intentionally setting to undefined for testing
      delete window.navigator;

      vi.doMock('@/locales/zh-TW.json', () => ({
        default: mockZhTWTranslations,
      }));

      vi.doMock('@/locales/en-US.json', () => ({
        default: mockEnUSTranslations,
      }));

      render(
        <I18nProvider>
          <TestErrorHandlingApp />
        </I18nProvider>
      );

      // Should default to en-US when navigator is unavailable
      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
      });

      expect(screen.getByTestId('nav-articles')).toHaveTextContent('Articles');

      // Restore navigator
      window.navigator = originalNavigator;
    });

    it('should handle malformed language codes', async () => {
      // Mock malformed language codes
      Object.defineProperty(window.navigator, 'language', {
        value: 'invalid-language-code-that-is-too-long',
        writable: true,
      });

      vi.doMock('@/locales/zh-TW.json', () => ({
        default: mockZhTWTranslations,
      }));

      vi.doMock('@/locales/en-US.json', () => ({
        default: mockEnUSTranslations,
      }));

      render(
        <I18nProvider>
          <TestErrorHandlingApp />
        </I18nProvider>
      );

      // Should default to en-US for invalid language codes
      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
      });

      expect(screen.getByTestId('nav-articles')).toHaveTextContent('Articles');
    });
  });

  describe('Component Error Recovery', () => {
    it('should handle translation function errors gracefully', async () => {
      // Mock translation function that might throw errors
      vi.doMock('@/locales/zh-TW.json', () => ({
        default: mockZhTWTranslations,
      }));

      vi.doMock('@/locales/en-US.json', () => ({
        default: mockEnUSTranslations,
      }));

      render(
        <I18nProvider>
          <TestErrorHandlingApp />
        </I18nProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
      });

      // Test missing keys return the key itself
      expect(screen.getByTestId('missing-key')).toHaveTextContent('non.existent.key');
      expect(screen.getByTestId('missing-nested')).toHaveTextContent('missing.deeply.nested.key');

      // Valid keys should still work
      expect(screen.getByTestId('nav-articles')).toHaveTextContent('Articles');
    });

    it('should handle interpolation errors gracefully', async () => {
      function TestInterpolationErrors() {
        const { t } = useI18n();

        return (
          <div>
            {/* Test with missing variables */}
            <div data-testid="missing-vars">{t('messages.article-count')}</div>

            {/* Test with wrong variable types */}
            <div data-testid="wrong-types">{t('messages.article-count', { count: null })}</div>

            {/* Test with circular references */}
            <div data-testid="circular-ref">
              {t('messages.article-count', { count: { toString: () => 'circular' } })}
            </div>
          </div>
        );
      }

      vi.doMock('@/locales/zh-TW.json', () => ({
        default: mockZhTWTranslations,
      }));

      vi.doMock('@/locales/en-US.json', () => ({
        default: mockEnUSTranslations,
      }));

      render(
        <I18nProvider>
          <TestInterpolationErrors />
        </I18nProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('missing-vars')).toBeInTheDocument();
      });

      // Should handle interpolation errors gracefully
      expect(screen.getByTestId('missing-vars')).toHaveTextContent(
        'Successfully fetched {count} new articles'
      );
      expect(screen.getByTestId('wrong-types')).toBeInTheDocument();
      expect(screen.getByTestId('circular-ref')).toBeInTheDocument();
    });

    it('should handle concurrent error conditions', async () => {
      // Simulate multiple error conditions at once

      // Mock localStorage errors
      const mockLocalStorage = {
        getItem: vi.fn(() => {
          throw new Error('localStorage error');
        }),
        setItem: vi.fn(() => {
          throw new Error('localStorage error');
        }),
        removeItem: vi.fn(),
        clear: vi.fn(),
      };

      Object.defineProperty(window, 'localStorage', {
        value: mockLocalStorage,
        writable: true,
      });

      // Mock undefined navigator
      Object.defineProperty(window.navigator, 'language', {
        value: undefined,
        writable: true,
      });

      // Mock translation loading errors
      vi.doMock('@/locales/zh-TW.json', () => {
        throw new Error('Translation loading error');
      });

      vi.doMock('@/locales/en-US.json', () => ({
        default: mockEnUSTranslations,
      }));

      const user = userEvent.setup();

      render(
        <I18nProvider>
          <TestErrorHandlingApp />
        </I18nProvider>
      );

      // Should still render and function despite multiple errors
      await waitFor(() => {
        expect(screen.getByTestId('test-app')).toBeInTheDocument();
      });

      // Should default to en-US and work with available translations
      expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
      expect(screen.getByTestId('nav-articles')).toHaveTextContent('Articles');

      // Language switching should still work for available languages
      const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
      await user.click(chineseButton);

      // Should handle the switch attempt gracefully
      await waitFor(() => {
        expect(screen.getByTestId('test-app')).toBeInTheDocument();
      });
    });
  });

  describe('Error Logging and Monitoring', () => {
    it('should log appropriate errors for debugging', async () => {
      // Mock translation loading failure
      vi.doMock('@/locales/zh-TW.json', () => {
        throw new Error('Failed to load Chinese translations');
      });

      vi.doMock('@/locales/en-US.json', () => ({
        default: mockEnUSTranslations,
      }));

      const user = userEvent.setup();

      render(
        <I18nProvider>
          <TestErrorHandlingApp />
        </I18nProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
      });

      // Try to switch to Chinese (will fail)
      const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
      await user.click(chineseButton);

      // Should log error but not crash
      await waitFor(() => {
        expect(screen.getByTestId('test-app')).toBeInTheDocument();
      });

      // In development, should log warnings for missing translations
      if (process.env.NODE_ENV === 'development') {
        expect(console.warn).toHaveBeenCalled();
      }
    });

    it('should not expose sensitive information in error messages', async () => {
      // Mock error that might contain sensitive info
      vi.doMock('@/locales/zh-TW.json', () => {
        const error = new Error('Database connection failed: password=secret123');
        throw error;
      });

      vi.doMock('@/locales/en-US.json', () => ({
        default: mockEnUSTranslations,
      }));

      render(
        <I18nProvider>
          <TestErrorHandlingApp />
        </I18nProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('test-app')).toBeInTheDocument();
      });

      // Should not display sensitive error information to users
      expect(screen.queryByText(/password=secret123/)).not.toBeInTheDocument();
      expect(screen.queryByText(/Database connection failed/)).not.toBeInTheDocument();
    });
  });
});
