/**
 * Integration Tests: I18n Context Integration
 *
 * Tests the I18nContext integration with React components:
 * - Using translations in components
 * - Language switching updates all components
 * - Multiple components using translations simultaneously
 * - Translation updates propagate correctly
 *
 * **Validates: Requirements 3.4, 7.1-7.4, 8.6**
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
  },
};

vi.mock('@/locales/zh-TW.json', () => ({
  default: mockZhTWTranslations,
}));

vi.mock('@/locales/en-US.json', () => ({
  default: mockEnUSTranslations,
}));

// Test component that uses translations
function TestComponent() {
  const { t, locale, setLocale } = useI18n();

  return (
    <div>
      <h1 data-testid="title">{t('nav.articles')}</h1>
      <p data-testid="message">{t('messages.article-count', { count: 5 })}</p>
      <button data-testid="save-btn">{t('buttons.save')}</button>
      <div data-testid="locale">{locale}</div>
      <button data-testid="switch-zh" onClick={() => setLocale('zh-TW')}>
        中文
      </button>
      <button data-testid="switch-en" onClick={() => setLocale('en-US')}>
        English
      </button>
    </div>
  );
}

// Multiple components using translations
function ComponentA() {
  const { t } = useI18n();
  return <div data-testid="component-a">{t('nav.articles')}</div>;
}

function ComponentB() {
  const { t } = useI18n();
  return <div data-testid="component-b">{t('buttons.save')}</div>;
}

function MultiComponentTest() {
  const { setLocale } = useI18n();
  return (
    <div>
      <ComponentA />
      <ComponentB />
      <button data-testid="switch-lang" onClick={() => setLocale('zh-TW')}>
        Switch
      </button>
    </div>
  );
}

describe('I18n Context Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    document.documentElement.lang = '';
    Object.defineProperty(window.navigator, 'language', {
      writable: true,
      configurable: true,
      value: 'en-US',
    });
  });

  it('should render component with translations', async () => {
    // Requirement 7.1-7.4: Translation Provider API
    render(
      <I18nProvider>
        <TestComponent />
      </I18nProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('title')).toHaveTextContent('Articles');
    });

    expect(screen.getByTestId('message')).toHaveTextContent('Successfully fetched 5 new articles');
    expect(screen.getByTestId('save-btn')).toHaveTextContent('Save');
  });

  it('should update all translations when language switches', async () => {
    // Requirement 3.4: Update all UI text immediately without page reload
    const user = userEvent.setup();

    render(
      <I18nProvider>
        <TestComponent />
      </I18nProvider>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByTestId('title')).toHaveTextContent('Articles');
    });

    // Switch to Chinese
    await user.click(screen.getByTestId('switch-zh'));

    // Wait for translations to update
    await waitFor(() => {
      expect(screen.getByTestId('title')).toHaveTextContent('文章');
    });

    expect(screen.getByTestId('message')).toHaveTextContent('成功抓取 5 篇新文章');
    expect(screen.getByTestId('save-btn')).toHaveTextContent('儲存');
    expect(screen.getByTestId('locale')).toHaveTextContent('zh-TW');
  });

  it('should update multiple components simultaneously', async () => {
    // Requirement 8.6: Prevent unnecessary re-renders
    const user = userEvent.setup();

    render(
      <I18nProvider>
        <MultiComponentTest />
      </I18nProvider>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByTestId('component-a')).toHaveTextContent('Articles');
    });

    expect(screen.getByTestId('component-b')).toHaveTextContent('Save');

    // Switch language
    await user.click(screen.getByTestId('switch-lang'));

    // Both components should update
    await waitFor(() => {
      expect(screen.getByTestId('component-a')).toHaveTextContent('文章');
    });

    expect(screen.getByTestId('component-b')).toHaveTextContent('儲存');
  });

  it('should handle rapid language switching', async () => {
    // Test that rapid switching doesn't cause issues
    const user = userEvent.setup();

    render(
      <I18nProvider>
        <TestComponent />
      </I18nProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('title')).toHaveTextContent('Articles');
    });

    // Rapid switching
    await user.click(screen.getByTestId('switch-zh'));
    await user.click(screen.getByTestId('switch-en'));
    await user.click(screen.getByTestId('switch-zh'));

    // Should end up in Chinese
    await waitFor(() => {
      expect(screen.getByTestId('title')).toHaveTextContent('文章');
    });
  });

  it('should persist language preference across remounts', async () => {
    // Requirement 2.1-2.3: Language persistence
    const user = userEvent.setup();

    const { unmount } = render(
      <I18nProvider>
        <TestComponent />
      </I18nProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('title')).toHaveTextContent('Articles');
    });

    // Switch to Chinese
    await user.click(screen.getByTestId('switch-zh'));

    await waitFor(() => {
      expect(screen.getByTestId('title')).toHaveTextContent('文章');
    });

    // Unmount and remount
    unmount();

    render(
      <I18nProvider>
        <TestComponent />
      </I18nProvider>
    );

    // Should remember Chinese preference
    await waitFor(() => {
      expect(screen.getByTestId('title')).toHaveTextContent('文章');
    });
  });
});
