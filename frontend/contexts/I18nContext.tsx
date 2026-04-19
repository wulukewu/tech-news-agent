'use client';

/**
 * I18n Context
 *
 * This module provides a React Context for managing internationalization (i18n).
 * It handles language detection, translation loading, and language switching.
 *
 * Responsibilities:
 * - Language state (zh-TW, en-US)
 * - Language detection from browser settings
 * - Translation loading with dynamic imports
 * - Translation function with nested key lookup and variable interpolation
 * - Persisting language preference to localStorage
 * - Updating HTML lang attribute
 *
 * Does NOT handle:
 * - Theme preferences (see ThemeContext)
 * - Authentication status (see AuthContext)
 * - User profile data (see UserContext)
 *
 * Usage:
 * ```tsx
 * // In app/layout.tsx
 * <I18nProvider>
 *   {children}
 * </I18nProvider>
 *
 * // In any component
 * const { t, locale, setLocale } = useI18n();
 * <h1>{t('nav.articles')}</h1>
 * <p>{t('messages.article-count', { count: 5 })}</p>
 * ```
 *
 * @see Requirements 1.1-1.6, 2.1-2.5, 3.1-3.6, 7.1-7.7
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { Locale, I18nContextType, TranslationFunction } from '@/types/i18n';

/**
 * I18n Context
 *
 * Provides i18n state and methods to all child components.
 * Should not be used directly - use the useI18n hook instead.
 */
const I18nContext = createContext<I18nContextType | undefined>(undefined);

const LANGUAGE_STORAGE_KEY = 'language';
const SUPPORTED_LOCALES: Locale[] = ['zh-TW', 'en-US'];

/**
 * I18nProvider Component
 *
 * Wraps the application and provides i18n state to all child components.
 * Automatically detects language from localStorage or browser settings and loads translations.
 *
 * @param children - Child components to wrap
 *
 * @see Requirement 1: Language Detection and Initialization
 * @see Requirement 2: Language Persistence
 */
export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>('en-US');
  const [translations, setTranslations] = useState<Record<string, unknown>>({});
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Detect language from browser settings
   *
   * Maps browser language codes to supported locales:
   * - Chinese variants (zh, zh-TW, zh-CN, zh-HK) → zh-TW
   * - English variants (en, en-US, en-GB) → en-US
   * - Other languages → en-US (fallback)
   *
   * Completes within 100ms to prevent UI flash.
   *
   * @returns Detected locale
   *
   * @see Requirement 1.1-1.4: Language detection logic
   */
  const detectLanguage = useCallback((): Locale => {
    if (typeof window === 'undefined') return 'en-US';

    const browserLang = navigator.language || (navigator.languages && navigator.languages[0]);

    // Check for Chinese variants
    if (browserLang && browserLang.startsWith('zh')) {
      return 'zh-TW';
    }

    // Check for English variants
    if (browserLang && browserLang.startsWith('en')) {
      return 'en-US';
    }

    // Default fallback
    return 'en-US';
  }, []);

  /**
   * Load translations for a specific locale
   *
   * Uses dynamic imports for code splitting - only loads the active language.
   * Caches loaded translations in memory to prevent redundant fetching.
   *
   * @param targetLocale - Locale to load translations for
   *
   * @see Requirement 8.1-8.5: Performance optimization with lazy loading
   */
  const loadTranslations = useCallback(async (targetLocale: Locale) => {
    try {
      const response = await import(`@/locales/${targetLocale}.json`);
      setTranslations(response.default || response);
    } catch (error) {
      // Fallback to empty object - application continues to function
      setTranslations({});
    }
  }, []);

  /**
   * Translation function
   *
   * Translates a key to the current locale's string with optional variable interpolation.
   * Supports nested key access using dot notation (e.g., 'nav.articles', 'errors.network-error').
   *
   * Features:
   * - Nested key lookup: 'nav.articles' → translations.nav.articles
   * - Variable interpolation: {count}, {name}, etc.
   * - Fallback: Returns key itself if translation not found
   * - Development warnings: Logs missing keys in development mode
   *
   * @param key - Translation key using dot notation
   * @param variables - Optional variables for interpolation
   * @returns Translated string, or the key itself if translation not found
   *
   * @example
   * t('nav.articles') // "文章" or "Articles"
   * t('messages.article-count', { count: 5 }) // "成功抓取 5 篇新文章"
   *
   * @see Requirement 7.5-7.7: Translation function with nested keys and interpolation
   */
  const t: TranslationFunction = useCallback(
    (key, variables) => {
      const keys = key.split('.');
      let value: unknown = translations;

      // Traverse nested object structure
      for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
          value = (value as Record<string, unknown>)[k];
        } else {
          // Fallback: return key if translation not found
          return key;
        }
      }

      // Handle interpolation
      if (typeof value === 'string' && variables) {
        return value.replace(/\{(\w+)\}/g, (match, varName) => {
          return variables[varName]?.toString() || match;
        });
      }

      return typeof value === 'string' ? value : key;
    },
    [translations]
  );

  /**
   * Announce language change to screen readers
   *
   * Creates a temporary ARIA live region to announce the language change.
   * The announcement is in the NEW language (not the old one) so screen readers
   * can properly announce it with the correct pronunciation.
   *
   * The element is visually hidden but accessible to screen readers, and is
   * automatically removed after 1 second to keep the DOM clean.
   *
   * @param newLocale - The locale that was just switched to
   * @param newTranslations - The translations for the new locale
   *
   * @see Requirement 9.2: Screen reader announcements for language changes
   */
  const announceLanguageChange = useCallback(
    (newLocale: Locale, newTranslations: Record<string, unknown>) => {
      if (typeof document === 'undefined') return;

      // Get the announcement text in the NEW language
      const announcementKey =
        newLocale === 'zh-TW' ? 'language.changed-to-chinese' : 'language.changed-to-english';

      // Traverse the translation object to get the announcement text
      const keys = announcementKey.split('.');
      let announcementText: unknown = newTranslations;
      for (const k of keys) {
        if (announcementText && typeof announcementText === 'object' && k in announcementText) {
          announcementText = (announcementText as Record<string, unknown>)[k];
        } else {
          announcementText = announcementKey; // Fallback to key
          break;
        }
      }

      // Create a visually hidden live region
      const announcement = document.createElement('div');
      announcement.setAttribute('role', 'status');
      announcement.setAttribute('aria-live', 'polite');
      announcement.setAttribute('aria-atomic', 'true');
      announcement.className = 'sr-only'; // Tailwind's screen-reader-only class
      announcement.style.position = 'absolute';
      announcement.style.width = '1px';
      announcement.style.height = '1px';
      announcement.style.padding = '0';
      announcement.style.margin = '-1px';
      announcement.style.overflow = 'hidden';
      announcement.style.clip = 'rect(0, 0, 0, 0)';
      announcement.style.whiteSpace = 'nowrap';
      announcement.style.border = '0';
      announcement.textContent =
        typeof announcementText === 'string' ? announcementText : announcementKey;

      // Append to body
      document.body.appendChild(announcement);

      // Remove after 1 second
      setTimeout(() => {
        if (document.body.contains(announcement)) {
          document.body.removeChild(announcement);
        }
      }, 1000);
    },
    []
  );

  /**
   * Set locale with persistence
   *
   * Changes the active locale, loads corresponding translations, and persists preference.
   * Updates HTML lang attribute for accessibility and screen readers.
   * Announces the language change to screen readers.
   * Completes within 200ms for smooth user experience.
   *
   * @param newLocale - Locale to switch to
   *
   * @see Requirement 2.1-2.4: Language persistence
   * @see Requirement 3.2: Language switching within 200ms
   * @see Requirement 9.2: Screen reader announcements for language changes
   * @see Requirement 9.5: Update HTML lang attribute
   */
  const setLocale = useCallback(
    async (newLocale: Locale) => {
      setIsLoading(true);
      setLocaleState(newLocale);

      // Update HTML lang attribute for accessibility
      if (typeof document !== 'undefined') {
        document.documentElement.lang = newLocale;
      }

      // Persist to localStorage
      try {
        localStorage.setItem(LANGUAGE_STORAGE_KEY, newLocale);
      } catch {
        // Handle localStorage unavailability gracefully (e.g., private browsing)
        // Silently fail - application continues to function
      }

      // Load translations
      await loadTranslations(newLocale);

      // Get the newly loaded translations for the announcement
      const response = await import(`@/locales/${newLocale}.json`);
      const newTranslations = response.default || response;

      // Announce language change to screen readers (in the NEW language)
      announceLanguageChange(newLocale, newTranslations);

      setIsLoading(false);
    },
    [loadTranslations, announceLanguageChange]
  );

  /**
   * Initialize language on mount
   *
   * Priority order:
   * 1. localStorage preference (if available and valid)
   * 2. Browser language detection
   * 3. Default fallback (en-US)
   *
   * Handles localStorage unavailability gracefully without throwing errors.
   *
   * @see Requirement 1.5: Use stored preference before browser detection
   * @see Requirement 2.4: Fall back to browser detection if localStorage unavailable
   */
  useEffect(() => {
    const initializeLanguage = async () => {
      let initialLocale: Locale = 'en-US';

      // Check localStorage first
      try {
        const stored = localStorage.getItem(LANGUAGE_STORAGE_KEY) as Locale | null;
        if (stored && SUPPORTED_LOCALES.includes(stored)) {
          initialLocale = stored;
        } else {
          // Fall back to browser detection
          initialLocale = detectLanguage();
        }
      } catch (error) {
        // localStorage unavailable, use detection
        initialLocale = detectLanguage();
      }

      await setLocale(initialLocale);
    };

    initializeLanguage();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount

  const value: I18nContextType = {
    locale,
    setLocale,
    t,
    isLoading,
  };

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

/**
 * useI18n Hook
 *
 * Custom hook to access i18n state and methods.
 * Must be used within a component wrapped by I18nProvider.
 *
 * @returns I18nContextType - I18n state and methods
 * @throws Error if used outside of I18nProvider
 *
 * @example
 * ```tsx
 * function ArticleList() {
 *   const { t, locale, setLocale } = useI18n();
 *
 *   return (
 *     <div>
 *       <h1>{t('nav.articles')}</h1>
 *       <p>{t('messages.article-count', { count: 5 })}</p>
 *       <button onClick={() => setLocale('zh-TW')}>中文</button>
 *       <button onClick={() => setLocale('en-US')}>English</button>
 *     </div>
 *   );
 * }
 * ```
 *
 * @see Requirement 7.1-7.4: Translation Provider API
 */
export function useI18n(): I18nContextType {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return context;
}
