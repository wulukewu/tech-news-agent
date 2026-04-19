'use client';

import { useI18n } from '@/contexts/I18nContext';

/**
 * Skip to Main Content Link
 *
 * Provides a keyboard-accessible skip link for screen readers and keyboard navigation.
 * The link is visually hidden but becomes visible when focused.
 */
export function SkipToMainContent() {
  const { t } = useI18n();

  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
    >
      {t('aria-labels.skip-to-main')}
    </a>
  );
}
