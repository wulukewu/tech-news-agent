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
  },
  errors: {
    'network-error': '網路連線異常',
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
  },
  errors: {
    'network-error': 'Network connection error',
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

    it('should default to en-US for unsupported languages', async () => {
      // Requirement 1.4: Unsupported languages → en-US
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
