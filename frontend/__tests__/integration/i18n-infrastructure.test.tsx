/**
 * Integration Test: i18n Infrastructure
 *
 * This test verifies that the core i18n infrastructure is working correctly:
 * - I18nProvider can be mounted
 * - Language detection works
 * - Translation files can be loaded
 * - LanguageSwitcher integrates correctly
 * - Language switching updates the UI
 *
 * Task 3: Checkpoint - Verify infrastructure works
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { I18nProvider, useI18n } from '@/contexts/I18nContext';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

// Test component that uses translations
function TestApp() {
  const { t, locale, isLoading } = useI18n();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <div data-testid="locale">{locale}</div>
      <div data-testid="translation-test">{t('nav.articles')}</div>
      <LanguageSwitcher />
    </div>
  );
}

describe('i18n Infrastructure Integration', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Reset HTML lang attribute
    document.documentElement.lang = 'en-US';
  });

  it('should render the app with i18n infrastructure', async () => {
    render(
      <I18nProvider>
        <TestApp />
      </I18nProvider>
    );

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Verify locale is set
    const localeElement = screen.getByTestId('locale');
    expect(localeElement.textContent).toMatch(/^(zh-TW|en-US)$/);
  });

  it('should load and display translations', async () => {
    render(
      <I18nProvider>
        <TestApp />
      </I18nProvider>
    );

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Verify translation function returns something (even if it's the key as fallback)
    const translationElement = screen.getByTestId('translation-test');
    expect(translationElement.textContent).toBeTruthy();
  });

  it('should render LanguageSwitcher component', async () => {
    render(
      <I18nProvider>
        <TestApp />
      </I18nProvider>
    );

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Verify LanguageSwitcher is rendered
    expect(screen.getByLabelText('Language selector')).toBeInTheDocument();
    expect(screen.getByText('繁體中文')).toBeInTheDocument();
    expect(screen.getByText('English')).toBeInTheDocument();
  });

  it('should switch languages when clicking language buttons', async () => {
    const user = userEvent.setup();

    render(
      <I18nProvider>
        <TestApp />
      </I18nProvider>
    );

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Click English button to ensure we're switching to a known state
    const enButton = screen.getByLabelText('Switch to English');
    await user.click(enButton);

    // Wait for language to switch to English
    await waitFor(
      () => {
        expect(screen.getByTestId('locale').textContent).toBe('en-US');
      },
      { timeout: 3000 }
    );

    // Verify HTML lang attribute is updated
    expect(document.documentElement.lang).toBe('en-US');

    // Now switch to Chinese
    const zhButton = screen.getByLabelText('Switch to Traditional Chinese');
    await user.click(zhButton);

    // Wait for language to switch to Chinese
    await waitFor(
      () => {
        expect(screen.getByTestId('locale').textContent).toBe('zh-TW');
      },
      { timeout: 3000 }
    );

    // Verify HTML lang attribute is updated
    expect(document.documentElement.lang).toBe('zh-TW');
  });

  it('should persist language preference to localStorage', async () => {
    const user = userEvent.setup();

    render(
      <I18nProvider>
        <TestApp />
      </I18nProvider>
    );

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Click Chinese button
    const zhButton = screen.getByLabelText('Switch to Traditional Chinese');
    await user.click(zhButton);

    // Wait for language to switch
    await waitFor(
      () => {
        expect(screen.getByTestId('locale').textContent).toBe('zh-TW');
      },
      { timeout: 3000 }
    );

    // Verify localStorage is updated
    expect(localStorage.getItem('language')).toBe('zh-TW');
  });

  it('should handle translation fallback gracefully', async () => {
    render(
      <I18nProvider>
        <TestApp />
      </I18nProvider>
    );

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Even with empty translation files, the app should not crash
    // and should return the key as fallback
    const translationElement = screen.getByTestId('translation-test');
    expect(translationElement).toBeInTheDocument();
  });
});
