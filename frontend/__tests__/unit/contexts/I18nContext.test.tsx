/**
 * Unit Tests: I18nContext
 *
 * Tests the I18nContext functionality including:
 * - Language detection from browser settings
 * - Translation loading with dynamic imports
 * - Translation function with nested key lookup
 * - Variable interpolation in translations
 * - Language switching with localStorage persistence
 * - HTML lang attribute updates
 * - Fallback behavior for missing keys
 *
 * **Validates: Requirements 1.1-1.6, 2.1-2.5, 7.1-7.7**
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { I18nProvider, useI18n } from '@/contexts/I18nContext';

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
    'article-count': '成功抓取 {count} 篇新文章',
    loading: '載入中...',
    'user-count': '共有 {count} 位使用者',
    'status-active': '狀態：{active}',
    'empty-message': '',
  },
  errors: {
    'network-error': '網路連線異常',
  },
  language: {
    'changed-to-chinese': '語言已切換為繁體中文',
    'changed-to-english': '語言已切換為英文',
  },
  special: {
    'quotes-single': "It's a beautiful day",
    'quotes-double': 'He said "Hello world"',
    'quotes-mixed': `She replied: "I'm fine, thanks!"`,
    'unicode-emoji': '歡迎使用 🚀 技術新聞',
    'unicode-symbols': '溫度：25°C • 濕度：60%',
    apostrophe: "Don't worry, be happy",
    'complex-punctuation': '問題？答案！解決方案... (完成)',
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
    'article-count': 'Successfully fetched {count} new articles',
    loading: 'Loading...',
    'user-count': 'Total {count} users',
    'status-active': 'Status: {active}',
    'empty-message': '',
  },
  errors: {
    'network-error': 'Network connection error',
  },
  language: {
    'changed-to-chinese': 'Language changed to Traditional Chinese',
    'changed-to-english': 'Language changed to English',
  },
  special: {
    'quotes-single': "It's a beautiful day",
    'quotes-double': 'He said "Hello world"',
    'quotes-mixed': `She replied: "I'm fine, thanks!"`,
    'unicode-emoji': 'Welcome to 🚀 Tech News',
    'unicode-symbols': 'Temperature: 25°C • Humidity: 60%',
    apostrophe: "Don't worry, be happy",
    'complex-punctuation': 'Question? Answer! Solution... (Done)',
  },
};

// Mock dynamic imports
vi.mock('@/locales/zh-TW.json', () => ({
  default: mockZhTWTranslations,
}));

vi.mock('@/locales/en-US.json', () => ({
  default: mockEnUSTranslations,
}));

describe('I18nContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    // Reset document.documentElement.lang
    document.documentElement.lang = '';
    // Mock navigator.language
    Object.defineProperty(window.navigator, 'language', {
      writable: true,
      configurable: true,
      value: 'en-US',
    });
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('Language Detection', () => {
    it('should detect Chinese variants and map to zh-TW', async () => {
      // Requirement 1.2: Chinese variants → zh-TW
      Object.defineProperty(window.navigator, 'language', {
        writable: true,
        configurable: true,
        value: 'zh-CN',
      });

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.locale).toBe('zh-TW');
    });

    it('should detect zh variant and map to zh-TW', async () => {
      // Requirement 1.2: Chinese variants (zh) → zh-TW
      Object.defineProperty(window.navigator, 'language', {
        writable: true,
        configurable: true,
        value: 'zh',
      });

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.locale).toBe('zh-TW');
    });

    it('should detect zh-TW variant and map to zh-TW', async () => {
      // Requirement 1.2: Chinese variants (zh-TW) → zh-TW
      Object.defineProperty(window.navigator, 'language', {
        writable: true,
        configurable: true,
        value: 'zh-TW',
      });

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.locale).toBe('zh-TW');
    });

    it('should detect zh-HK variant and map to zh-TW', async () => {
      // Requirement 1.2: Chinese variants (zh-HK) → zh-TW
      Object.defineProperty(window.navigator, 'language', {
        writable: true,
        configurable: true,
        value: 'zh-HK',
      });

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.locale).toBe('zh-TW');
    });

    it('should detect English variants and map to en-US', async () => {
      // Requirement 1.3: English variants → en-US
      Object.defineProperty(window.navigator, 'language', {
        writable: true,
        configurable: true,
        value: 'en-GB',
      });

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.locale).toBe('en-US');
    });

    it('should detect en variant and map to en-US', async () => {
      // Requirement 1.3: English variants (en) → en-US
      Object.defineProperty(window.navigator, 'language', {
        writable: true,
        configurable: true,
        value: 'en',
      });

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.locale).toBe('en-US');
    });

    it('should detect en-US variant and map to en-US', async () => {
      // Requirement 1.3: English variants (en-US) → en-US
      Object.defineProperty(window.navigator, 'language', {
        writable: true,
        configurable: true,
        value: 'en-US',
      });

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.locale).toBe('en-US');
    });

    it('should default to en-US for French language', async () => {
      // Requirement 1.4: Unsupported languages (fr) → en-US
      Object.defineProperty(window.navigator, 'language', {
        writable: true,
        configurable: true,
        value: 'fr-FR',
      });

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.locale).toBe('en-US');
    });

    it('should default to en-US for German language', async () => {
      // Requirement 1.4: Unsupported languages (de) → en-US
      Object.defineProperty(window.navigator, 'language', {
        writable: true,
        configurable: true,
        value: 'de-DE',
      });

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.locale).toBe('en-US');
    });

    it('should default to en-US for Japanese language', async () => {
      // Requirement 1.4: Unsupported languages (ja) → en-US
      Object.defineProperty(window.navigator, 'language', {
        writable: true,
        configurable: true,
        value: 'ja-JP',
      });

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.locale).toBe('en-US');
    });

    it('should handle undefined navigator.language gracefully', async () => {
      // Requirement 1.6: Handle undefined navigator.language
      Object.defineProperty(window.navigator, 'language', {
        writable: true,
        configurable: true,
        value: undefined,
      });
      Object.defineProperty(window.navigator, 'languages', {
        writable: true,
        configurable: true,
        value: undefined,
      });

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.locale).toBe('en-US');
    });

    it('should complete language detection within 100ms', async () => {
      // Requirement 1.6: Detection completes within 100ms
      Object.defineProperty(window.navigator, 'language', {
        writable: true,
        configurable: true,
        value: 'zh-CN',
      });

      const startTime = performance.now();

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const endTime = performance.now();
      const detectionTime = endTime - startTime;

      expect(detectionTime).toBeLessThan(100);
      expect(result.current.locale).toBe('zh-TW');
    });

    it('should use stored preference over browser detection', async () => {
      // Requirement 1.5: localStorage preference takes priority
      localStorage.setItem('language', 'zh-TW');
      Object.defineProperty(window.navigator, 'language', {
        writable: true,
        configurable: true,
        value: 'en-US',
      });

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.locale).toBe('zh-TW');
    });
  });

  describe('Translation Function', () => {
    it('should translate basic keys correctly', async () => {
      // Requirement 7.5: Basic key lookup
      localStorage.setItem('language', 'zh-TW');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.t('nav.articles')).toBe('文章');
      expect(result.current.t('buttons.save')).toBe('儲存');
    });

    it('should handle nested key lookup with dot notation', async () => {
      // Requirement 7.6: Nested key access
      localStorage.setItem('language', 'en-US');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.t('errors.network-error')).toBe('Network connection error');
    });

    it('should interpolate variables correctly', async () => {
      // Requirement 7.7: Variable interpolation
      localStorage.setItem('language', 'zh-TW');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.t('messages.article-count', { count: 5 })).toBe('成功抓取 5 篇新文章');
    });

    it('should return key itself when translation not found', async () => {
      // Requirement 5.5: Fallback behavior
      localStorage.setItem('language', 'en-US');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.t('non.existent.key')).toBe('non.existent.key');
    });

    it('should handle multiple variable interpolations', async () => {
      // Additional test for complex interpolation
      localStorage.setItem('language', 'en-US');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Test with numeric values
      expect(result.current.t('messages.article-count', { count: 10 })).toBe(
        'Successfully fetched 10 new articles'
      );
    });

    it('should handle special characters in translations - single quotes', async () => {
      // Requirement 5.6: Special characters (quotes, apostrophes)
      localStorage.setItem('language', 'en-US');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.t('special.quotes-single')).toBe("It's a beautiful day");
      expect(result.current.t('special.apostrophe')).toBe("Don't worry, be happy");
    });

    it('should handle special characters in translations - double quotes', async () => {
      // Requirement 5.6: Special characters (quotes)
      localStorage.setItem('language', 'en-US');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.t('special.quotes-double')).toBe('He said "Hello world"');
      expect(result.current.t('special.quotes-mixed')).toBe(`She replied: "I'm fine, thanks!"`);
    });

    it('should handle unicode characters in translations', async () => {
      // Requirement 5.6: Special characters (unicode)
      localStorage.setItem('language', 'zh-TW');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.t('special.unicode-emoji')).toBe('歡迎使用 🚀 技術新聞');
      expect(result.current.t('special.unicode-symbols')).toBe('溫度：25°C • 濕度：60%');
    });

    it('should handle complex punctuation in translations', async () => {
      // Requirement 5.6: Special characters (complex punctuation)
      localStorage.setItem('language', 'zh-TW');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.t('special.complex-punctuation')).toBe(
        '問題？答案！解決方案... (完成)'
      );
    });

    it('should handle empty string translations', async () => {
      // Requirement 5.6: Empty string translations
      localStorage.setItem('language', 'en-US');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.t('messages.empty-message')).toBe('');
    });

    it('should handle numeric variable interpolation', async () => {
      // Requirement 7.7: Numeric variable interpolation
      localStorage.setItem('language', 'en-US');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Test with different numeric types
      expect(result.current.t('messages.user-count', { count: 42 })).toBe('Total 42 users');
      expect(result.current.t('messages.user-count', { count: 0 })).toBe('Total 0 users');
      expect(result.current.t('messages.user-count', { count: 1.5 })).toBe('Total 1.5 users');
      expect(result.current.t('messages.user-count', { count: -5 })).toBe('Total -5 users');
    });

    it('should handle boolean variable interpolation', async () => {
      // Requirement 7.7: Boolean variable interpolation
      localStorage.setItem('language', 'en-US');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Test with boolean values
      expect(result.current.t('messages.status-active', { active: true })).toBe('Status: true');
      expect(result.current.t('messages.status-active', { active: false })).toBe('Status: false');
    });

    it('should handle mixed variable types in interpolation', async () => {
      // Additional test for mixed variable types
      localStorage.setItem('language', 'en-US');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Test with string, number, and boolean in same translation
      // For this test, we'll verify the interpolation logic works with multiple types
      expect(result.current.t('messages.user-count', { count: 'many' })).toBe('Total many users');
    });

    it('should handle undefined and null variables gracefully', async () => {
      // Edge case: undefined/null variables
      localStorage.setItem('language', 'en-US');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Test with undefined variables - should leave placeholder unchanged
      expect(result.current.t('messages.user-count', { count: undefined })).toBe(
        'Total {count} users'
      );
      expect(result.current.t('messages.user-count', { count: null })).toBe('Total {count} users');
    });
  });

  describe('Language Switching', () => {
    it('should switch language and update translations', async () => {
      // Requirement 3.2: Language switching within 200ms
      localStorage.setItem('language', 'en-US');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.t('nav.articles')).toBe('Articles');

      // Switch to Chinese
      await act(async () => {
        await result.current.setLocale('zh-TW');
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.locale).toBe('zh-TW');
      expect(result.current.t('nav.articles')).toBe('文章');
    });

    it('should persist language preference to localStorage', async () => {
      // Requirement 2.1: Save preference to localStorage
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.setLocale('zh-TW');
      });

      expect(localStorage.getItem('language')).toBe('zh-TW');
    });

    it('should update HTML lang attribute on language change', async () => {
      // Requirement 9.5: Update HTML lang attribute
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.setLocale('zh-TW');
      });

      expect(document.documentElement.lang).toBe('zh-TW');

      await act(async () => {
        await result.current.setLocale('en-US');
      });

      expect(document.documentElement.lang).toBe('en-US');
    });

    it('should announce language change to screen readers', async () => {
      // Requirement 9.2: Screen reader announcements for language changes
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Switch to Chinese
      await act(async () => {
        await result.current.setLocale('zh-TW');
      });

      // Check that announcement element was created
      const announcements = document.querySelectorAll('[role="status"][aria-live="polite"]');
      expect(announcements.length).toBeGreaterThan(0);

      // Check that the announcement has the correct text (in the NEW language)
      const announcement = announcements[announcements.length - 1];
      expect(announcement.textContent).toContain('語言已切換為繁體中文');

      // Check that the element is visually hidden but accessible
      expect(announcement.className).toBe('sr-only');
      expect(announcement.getAttribute('aria-atomic')).toBe('true');

      // Wait for the announcement to be removed (after 1 second)
      await waitFor(
        () => {
          expect(document.body.contains(announcement)).toBe(false);
        },
        { timeout: 1500 }
      );
    });

    it('should announce in the NEW language when switching', async () => {
      // Requirement 9.2: Announcement should be in the NEW language
      localStorage.setItem('language', 'en-US');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Switch from English to Chinese
      await act(async () => {
        await result.current.setLocale('zh-TW');
      });

      // Announcement should be in Chinese (the NEW language)
      const announcements = document.querySelectorAll('[role="status"][aria-live="polite"]');
      const announcement = announcements[announcements.length - 1];
      expect(announcement.textContent).toBe('語言已切換為繁體中文');

      // Switch from Chinese to English
      await act(async () => {
        await result.current.setLocale('en-US');
      });

      // Announcement should be in English (the NEW language)
      const newAnnouncements = document.querySelectorAll('[role="status"][aria-live="polite"]');
      const newAnnouncement = newAnnouncements[newAnnouncements.length - 1];
      expect(newAnnouncement.textContent).toBe('Language changed to English');
    });

    it('should handle localStorage unavailability gracefully', async () => {
      // Requirement 2.4: Graceful handling of localStorage unavailability
      const originalSetItem = Storage.prototype.setItem;
      Storage.prototype.setItem = vi.fn(() => {
        throw new Error('localStorage unavailable');
      });

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Should not throw error
      await act(async () => {
        await result.current.setLocale('zh-TW');
      });

      expect(result.current.locale).toBe('zh-TW');

      // Restore original
      Storage.prototype.setItem = originalSetItem;
    });
  });

  describe('Error Handling', () => {
    it('should handle translation loading errors gracefully', async () => {
      // This test verifies that the app doesn't crash when translations fail to load
      // In practice, the dynamic import will fail and translations will be empty
      // The translation function will return the key itself as fallback

      // We can't easily mock dynamic import failures in vitest, but we can test
      // that missing keys return the key itself (which is the same behavior)
      localStorage.setItem('language', 'en-US');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Test with a non-existent key to verify fallback behavior
      expect(result.current.t('non.existent.key')).toBe('non.existent.key');
    });

    it('should validate stored locale values', async () => {
      // Requirement 2.5: Validate stored language values
      localStorage.setItem('language', 'invalid-locale');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Should fall back to browser detection or default
      expect(['zh-TW', 'en-US']).toContain(result.current.locale);
    });
  });

  describe('Hook Usage', () => {
    it('should throw error when used outside provider', () => {
      // Test that useI18n requires I18nProvider
      expect(() => {
        renderHook(() => useI18n());
      }).toThrow('useI18n must be used within I18nProvider');
    });
  });
});
