/**
 * Type definitions for the i18n (internationalization) system
 *
 * This file contains all TypeScript types for the bilingual UI system,
 * supporting Traditional Chinese (zh-TW) and English (en-US).
 *
 * @see Requirements 5.1, 5.2, 5.3, 7.1, 7.2, 7.3
 */

/**
 * Supported locales in the application
 * - zh-TW: Traditional Chinese (Taiwan)
 * - en-US: English (United States)
 */
export type Locale = 'zh-TW' | 'en-US';

/**
 * Translation key paths for accessing translations
 * Uses dot notation for nested keys (e.g., 'nav.articles', 'errors.network-error')
 */
export type TranslationKey = string;

/**
 * Variables for interpolation in translation strings
 * Used to replace placeholders like {count}, {name}, etc.
 *
 * @example
 * t('messages.article-count', { count: 5 })
 * // "成功抓取 5 篇新文章" or "Successfully fetched 5 new articles"
 */
export type TranslationVariables = Record<string, string | number>;

/**
 * Translation function type
 * Translates a key to the current locale's string, with optional variable interpolation
 *
 * @param key - Translation key using dot notation
 * @param variables - Optional variables for interpolation
 * @returns Translated string, or the key itself if translation not found
 *
 * @example
 * t('nav.articles') // "文章" or "Articles"
 * t('messages.article-count', { count: 5 }) // "成功抓取 5 篇新文章"
 */
export type TranslationFunction = (key: TranslationKey, variables?: TranslationVariables) => string;

/**
 * I18n Context type
 * Provides the current locale, translation function, and locale setter
 *
 * @property locale - Current active locale
 * @property setLocale - Function to change the active locale
 * @property t - Translation function
 * @property isLoading - Whether translations are currently being loaded
 */
export interface I18nContextType {
  /** Current active locale */
  locale: Locale;

  /** Change the active locale and load corresponding translations */
  setLocale: (locale: Locale) => void;

  /** Translation function for converting keys to localized strings */
  t: TranslationFunction;

  /** Whether translations are currently being loaded */
  isLoading: boolean;
}

/**
 * Translation file structure
 * Defines the schema for translation JSON files (zh-TW.json, en-US.json)
 *
 * Organized into logical sections:
 * - nav: Navigation labels
 * - buttons: Button labels
 * - messages: User-facing messages
 * - errors: Error messages
 * - success: Success messages
 * - tinkering-index: Technical depth level labels
 * - sort: Sort option labels
 * - theme: Theme option labels
 * - notification-frequency: Notification frequency labels
 */
export interface TranslationFile {
  /** Navigation menu labels */
  nav: {
    articles: string;
    'reading-list': string;
    subscriptions: string;
    analytics: string;
    settings: string;
    'system-status': string;
  };

  /** Common button labels */
  buttons: {
    save: string;
    cancel: string;
    delete: string;
    edit: string;
    add: string;
    remove: string;
    confirm: string;
    close: string;
    submit: string;
    reset: string;
    back: string;
    next: string;
    finish: string;
    retry: string;
    refresh: string;
  };

  /** User-facing messages */
  messages: {
    loading: string;
    'article-count': string; // Supports {count} interpolation
    'no-articles': string;
    'fetching-articles': string;
    'scheduler-running': string;
    processing: string;
    success: string;
    error: string;
  };

  /** Error messages */
  errors: {
    'network-error': string;
    'analysis-timeout': string;
    'insufficient-permissions': string;
    'rate-limit-exceeded': string;
    'invalid-input': string;
    'server-error': string;
    'not-found': string;
    unauthorized: string;
    'unknown-error': string;
  };

  /** Success messages */
  success: {
    'article-saved': string;
    'article-removed': string;
    'settings-saved': string;
    'analysis-copied': string;
    'subscription-added': string;
    'subscription-removed': string;
  };

  /** Tinkering index (technical depth) levels */
  'tinkering-index': {
    'level-1': string;
    'level-1-desc': string;
    'level-2': string;
    'level-2-desc': string;
    'level-3': string;
    'level-3-desc': string;
    'level-4': string;
    'level-4-desc': string;
    'level-5': string;
    'level-5-desc': string;
  };

  /** Sort option labels */
  sort: {
    date: string;
    'tinkering-index': string;
    category: string;
    title: string;
  };

  /** Theme option labels */
  theme: {
    light: string;
    dark: string;
    system: string;
  };

  /** Notification frequency option labels */
  'notification-frequency': {
    immediate: string;
    daily: string;
    weekly: string;
    disabled: string;
  };
}
