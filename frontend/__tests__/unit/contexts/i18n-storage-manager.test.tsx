/**
 * Unit Tests: I18n Storage Manager
 *
 * Tests the localStorage persistence functionality within the I18nContext.
 * Ensures robust handling of storage operations and edge cases.
 *
 * Task 1.6: Write unit tests for storage manager
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 11.6
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { I18nProvider, useI18n } from '@/contexts/I18nContext';
import type { Locale } from '@/types/i18n';

// Test component to interact with I18n context
function TestStorageComponent() {
  const { locale, setLocale, isLoading } = useI18n();

  if (isLoading) {
    return <div data-testid="loading">Loading...</div>;
  }

  return (
    <div>
      <div data-testid="current-locale">{locale}</div>
      <button data-testid="set-zh-tw" onClick={() => setLocale('zh-TW')}>
        Set Chinese
      </button>
      <button data-testid="set-en-us" onClick={() => setLocale('en-US')}>
        Set English
      </button>
    </div>
  );
}

describe('I18n Storage Manager', () => {
  let mockLocalStorage: { [key: string]: string };
  let localStorageGetItem: ReturnType<typeof vi.fn>;
  let localStorageSetItem: ReturnType<typeof vi.fn>;
  let localStorageRemoveItem: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    // Reset mock localStorage
    mockLocalStorage = {};

    localStorageGetItem = vi.fn((key: string) => mockLocalStorage[key] || null);
    localStorageSetItem = vi.fn((key: string, value: string) => {
      mockLocalStorage[key] = value;
    });
    localStorageRemoveItem = vi.fn((key: string) => {
      delete mockLocalStorage[key];
    });

    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: localStorageGetItem,
        setItem: localStorageSetItem,
        removeItem: localStorageRemoveItem,
        clear: vi.fn(() => {
          mockLocalStorage = {};
        }),
      },
      writable: true,
    });

    // Reset HTML lang attribute
    document.documentElement.lang = 'en-US';

    // Mock navigator.language for consistent testing
    Object.defineProperty(navigator, 'language', {
      value: 'en-US',
      writable: true,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Saving valid locale to localStorage', () => {
    it('should save zh-TW locale to localStorage when setLocale is called', async () => {
      const user = userEvent.setup();

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Click to set Chinese locale
      await user.click(screen.getByTestId('set-zh-tw'));

      // Wait for locale change
      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('zh-TW');
      });

      // Verify localStorage was called with correct values
      expect(localStorageSetItem).toHaveBeenCalledWith('language', 'zh-TW');
      expect(mockLocalStorage['language']).toBe('zh-TW');
    });

    it('should save en-US locale to localStorage when setLocale is called', async () => {
      const user = userEvent.setup();

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Click to set English locale
      await user.click(screen.getByTestId('set-en-us'));

      // Wait for locale change
      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
      });

      // Verify localStorage was called with correct values
      expect(localStorageSetItem).toHaveBeenCalledWith('language', 'en-US');
      expect(mockLocalStorage['language']).toBe('en-US');
    });

    it('should use correct storage key "language"', async () => {
      const user = userEvent.setup();

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Change locale
      await user.click(screen.getByTestId('set-zh-tw'));

      // Wait for locale change
      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('zh-TW');
      });

      // Verify the exact storage key is used
      expect(localStorageSetItem).toHaveBeenCalledWith('language', 'zh-TW');
      expect(localStorageSetItem).not.toHaveBeenCalledWith('locale', expect.anything());
      expect(localStorageSetItem).not.toHaveBeenCalledWith('i18n', expect.anything());
    });
  });

  describe('Retrieving stored locale on initialization', () => {
    it('should retrieve and use stored zh-TW locale on initialization', async () => {
      // Pre-populate localStorage with Chinese locale
      mockLocalStorage['language'] = 'zh-TW';

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Verify localStorage was checked
      expect(localStorageGetItem).toHaveBeenCalledWith('language');

      // Verify the stored locale is used
      expect(screen.getByTestId('current-locale')).toHaveTextContent('zh-TW');
    });

    it('should retrieve and use stored en-US locale on initialization', async () => {
      // Pre-populate localStorage with English locale
      mockLocalStorage['language'] = 'en-US';

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Verify localStorage was checked
      expect(localStorageGetItem).toHaveBeenCalledWith('language');

      // Verify the stored locale is used
      expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
    });

    it('should prioritize stored locale over browser detection', async () => {
      // Set browser language to Chinese
      Object.defineProperty(navigator, 'language', {
        value: 'zh-CN',
        writable: true,
      });

      // But store English in localStorage
      mockLocalStorage['language'] = 'en-US';

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Should use stored locale (en-US) not browser detected (zh-TW)
      expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
    });
  });

  describe('Validation rejects invalid locale values', () => {
    it('should reject invalid locale and fall back to browser detection', async () => {
      // Store invalid locale
      mockLocalStorage['language'] = 'invalid-locale';

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Should fall back to browser detection (en-US in our mock)
      expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
    });

    it('should reject empty string locale', async () => {
      // Store empty string
      mockLocalStorage['language'] = '';

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Should fall back to browser detection
      expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
    });

    it('should reject null value and fall back to browser detection', async () => {
      // localStorage returns null for non-existent keys
      mockLocalStorage = {}; // Empty storage

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Should fall back to browser detection
      expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
    });

    it('should reject unsupported locale codes', async () => {
      const invalidLocales = ['fr-FR', 'de-DE', 'ja-JP', 'es-ES', 'zh-CN'];

      for (const invalidLocale of invalidLocales) {
        // Store invalid locale
        mockLocalStorage['language'] = invalidLocale;

        render(
          <I18nProvider>
            <TestStorageComponent />
          </I18nProvider>
        );

        // Wait for initialization
        await waitFor(() => {
          expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
        });

        // Should fall back to browser detection (en-US)
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');

        // Clean up for next iteration
        screen.unmount?.();
      }
    });
  });

  describe('Graceful handling when localStorage is unavailable', () => {
    it('should handle localStorage.getItem throwing error (private browsing)', async () => {
      // Mock localStorage.getItem to throw error
      localStorageGetItem.mockImplementation(() => {
        throw new Error('localStorage is not available');
      });

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Should fall back to browser detection without crashing
      expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
    });

    it('should handle localStorage.setItem throwing error (private browsing)', async () => {
      const user = userEvent.setup();

      // Mock localStorage.setItem to throw error
      localStorageSetItem.mockImplementation(() => {
        throw new Error('localStorage is not available');
      });

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Try to change locale - should not crash
      await user.click(screen.getByTestId('set-zh-tw'));

      // Wait for locale change
      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('zh-TW');
      });

      // Locale should still change even if storage fails
      expect(screen.getByTestId('current-locale')).toHaveTextContent('zh-TW');
    });

    it('should handle localStorage being undefined', async () => {
      // Mock localStorage as undefined (some environments)
      Object.defineProperty(window, 'localStorage', {
        value: undefined,
        writable: true,
      });

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Should fall back to browser detection without crashing
      expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
    });

    it('should handle localStorage quota exceeded error', async () => {
      const user = userEvent.setup();

      // Mock localStorage.setItem to throw quota exceeded error
      localStorageSetItem.mockImplementation(() => {
        const error = new Error('QuotaExceededError');
        error.name = 'QuotaExceededError';
        throw error;
      });

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Try to change locale - should not crash
      await user.click(screen.getByTestId('set-zh-tw'));

      // Wait for locale change
      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('zh-TW');
      });

      // Locale should still change even if storage fails
      expect(screen.getByTestId('current-locale')).toHaveTextContent('zh-TW');
    });
  });

  describe('Handling of corrupted stored data', () => {
    it('should handle non-string values in localStorage', async () => {
      // Mock localStorage to return a non-string value
      localStorageGetItem.mockReturnValue(123 as any);

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Should fall back to browser detection
      expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
    });

    it('should handle malformed JSON-like strings', async () => {
      const malformedValues = [
        '{"locale": "zh-TW"}', // JSON object instead of string
        '[zh-TW]', // Array format
        'zh-TW,en-US', // Comma-separated
        'locale:zh-TW', // Key-value format
        '\\u0000zh-TW', // With null characters
      ];

      for (const malformedValue of malformedValues) {
        mockLocalStorage['language'] = malformedValue;

        render(
          <I18nProvider>
            <TestStorageComponent />
          </I18nProvider>
        );

        // Wait for initialization
        await waitFor(() => {
          expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
        });

        // Should fall back to browser detection for malformed data
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');

        // Clean up for next iteration
        screen.unmount?.();
      }
    });

    it('should handle extremely long strings', async () => {
      // Create a very long string
      const longString = 'a'.repeat(10000);
      mockLocalStorage['language'] = longString;

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Should fall back to browser detection
      expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
    });

    it('should handle special characters and unicode', async () => {
      const specialValues = [
        'zh-TW\x00', // Null terminator
        'zh-TW\n', // Newline
        'zh-TW\t', // Tab
        '🇹🇼zh-TW', // Emoji
        'zh-TW™', // Special symbols
      ];

      for (const specialValue of specialValues) {
        mockLocalStorage['language'] = specialValue;

        render(
          <I18nProvider>
            <TestStorageComponent />
          </I18nProvider>
        );

        // Wait for initialization
        await waitFor(() => {
          expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
        });

        // Should fall back to browser detection for invalid data
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');

        // Clean up for next iteration
        screen.unmount?.();
      }
    });
  });

  describe('Storage manager integration', () => {
    it('should maintain locale consistency between storage and state', async () => {
      const user = userEvent.setup();

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Change to Chinese
      await user.click(screen.getByTestId('set-zh-tw'));

      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('zh-TW');
      });

      // Verify storage matches state
      expect(mockLocalStorage['language']).toBe('zh-TW');

      // Change to English
      await user.click(screen.getByTestId('set-en-us'));

      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('en-US');
      });

      // Verify storage matches state
      expect(mockLocalStorage['language']).toBe('en-US');
    });

    it('should handle rapid locale changes correctly', async () => {
      const user = userEvent.setup();

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Rapidly change locales
      await user.click(screen.getByTestId('set-zh-tw'));
      await user.click(screen.getByTestId('set-en-us'));
      await user.click(screen.getByTestId('set-zh-tw'));

      // Wait for final state
      await waitFor(() => {
        expect(screen.getByTestId('current-locale')).toHaveTextContent('zh-TW');
      });

      // Final storage should match final state
      expect(mockLocalStorage['language']).toBe('zh-TW');
    });

    it('should not call localStorage unnecessarily', async () => {
      // Clear call counts
      vi.clearAllMocks();

      render(
        <I18nProvider>
          <TestStorageComponent />
        </I18nProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
      });

      // Should only call getItem once during initialization
      expect(localStorageGetItem).toHaveBeenCalledTimes(1);
      expect(localStorageGetItem).toHaveBeenCalledWith('language');
    });
  });
});
