'use client';

/**
 * LanguageSwitcher Component
 *
 * A button group component that allows users to manually switch between
 * Traditional Chinese (zh-TW) and English (en-US) languages.
 *
 * Features:
 * - Visual feedback for active language (highlighted background)
 * - Full keyboard navigation support (Tab, Enter, Space)
 * - WCAG AA compliant accessibility (ARIA attributes, focus indicators)
 * - Minimum touch target size (44x44px)
 * - Smooth transitions for state changes
 *
 * Accessibility:
 * - role="group" for semantic grouping
 * - aria-label="Language selector" for screen readers
 * - aria-pressed for active state indication
 * - Keyboard navigation: Tab (focus), Enter/Space (activate)
 * - Focus indicators: 2px ring with blue-500 color
 *
 * Usage:
 * ```tsx
 * import { LanguageSwitcher } from '@/components/LanguageSwitcher';
 *
 * function Navigation() {
 *   return (
 *     <nav>
 *       <LanguageSwitcher />
 *     </nav>
 *   );
 * }
 * ```
 *
 * @see Requirements 3.1, 3.2, 3.3, 3.5, 3.6, 9.1, 9.2, 9.3, 9.4, 9.6
 */

import React from 'react';
import { useI18n } from '@/contexts/I18nContext';
import type { Locale } from '@/types/i18n';

/**
 * Language option configuration
 * Defines the available languages with their labels and metadata
 */
const LANGUAGE_OPTIONS: Array<{
  value: Locale;
  label: string;
  nativeLabel: string;
}> = [
  {
    value: 'zh-TW',
    label: 'Traditional Chinese',
    nativeLabel: '繁體中文',
  },
  {
    value: 'en-US',
    label: 'English',
    nativeLabel: 'English',
  },
];

/**
 * LanguageSwitcher Component
 *
 * Renders a button group for language selection with full accessibility support.
 * Integrates with I18nContext to manage language state.
 *
 * @returns Language switcher button group
 *
 * @see Requirement 3.1: Display both language options
 * @see Requirement 3.2: Change language within 200ms
 * @see Requirement 3.3: Visual feedback for active language
 * @see Requirement 3.6: Keyboard navigation support
 * @see Requirement 9.1-9.4: Accessibility compliance
 */
export function LanguageSwitcher() {
  const { locale, setLocale } = useI18n();

  /**
   * Handle language change
   *
   * Calls setLocale from I18nContext to switch the active language.
   * The context handles translation loading and persistence.
   *
   * @param newLocale - The locale to switch to
   *
   * @see Requirement 3.2: Language change within 200ms
   */
  const handleLanguageChange = (newLocale: Locale) => {
    setLocale(newLocale);
  };

  /**
   * Handle keyboard events
   *
   * Supports Enter and Space keys for activation, matching native button behavior.
   *
   * @param event - Keyboard event
   * @param targetLocale - The locale to switch to
   *
   * @see Requirement 3.6: Keyboard navigation (Tab, Enter, Space)
   */
  const handleKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>, targetLocale: Locale) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleLanguageChange(targetLocale);
    }
  };

  return (
    <div
      role="group"
      aria-label="Language selector"
      className="flex items-center gap-2 rounded-lg bg-gray-100 dark:bg-gray-800 p-1"
    >
      {LANGUAGE_OPTIONS.map((option) => {
        const isActive = locale === option.value;

        return (
          <button
            key={option.value}
            onClick={() => handleLanguageChange(option.value)}
            onKeyDown={(e) => handleKeyDown(e, option.value)}
            aria-label={`Switch to ${option.label}`}
            aria-pressed={isActive}
            className={`
              px-3 py-1.5 rounded-md text-sm font-medium
              transition-colors duration-200
              min-w-[44px] min-h-[44px]
              flex items-center justify-center
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
              ${
                isActive
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }
            `}
          >
            {option.nativeLabel}
          </button>
        );
      })}
    </div>
  );
}
