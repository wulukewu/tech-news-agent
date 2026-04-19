/**
 * Unit tests for LanguageSwitcher component
 * Task 2.1: Create LanguageSwitcher component with accessibility
 * Requirements: 3.1, 3.2, 3.3, 3.5, 3.6, 9.1, 9.2, 9.3, 9.4, 9.6
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { I18nProvider } from '@/contexts/I18nContext';
import { vi } from 'vitest';

// Mock the translation files
vi.mock('@/locales/zh-TW.json', () => ({
  default: {
    nav: { articles: '文章' },
  },
}));

vi.mock('@/locales/en-US.json', () => ({
  default: {
    nav: { articles: 'Articles' },
  },
}));

/**
 * Helper function to render LanguageSwitcher with I18nProvider
 */
function renderLanguageSwitcher() {
  return render(
    <I18nProvider>
      <LanguageSwitcher />
    </I18nProvider>
  );
}

describe('LanguageSwitcher Component', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Reset document.documentElement.lang
    document.documentElement.lang = 'en-US';
  });

  describe('Rendering', () => {
    it('should render both language options', async () => {
      renderLanguageSwitcher();

      await waitFor(() => {
        expect(screen.getByText('繁體中文')).toBeInTheDocument();
        expect(screen.getByText('English')).toBeInTheDocument();
      });
    });

    it('should render with role="group" and aria-label', async () => {
      renderLanguageSwitcher();

      await waitFor(() => {
        const group = screen.getByRole('group', { name: 'Language selector' });
        expect(group).toBeInTheDocument();
      });
    });

    it('should render buttons with proper aria-labels', async () => {
      renderLanguageSwitcher();

      await waitFor(() => {
        expect(screen.getByLabelText('Switch to Traditional Chinese')).toBeInTheDocument();
        expect(screen.getByLabelText('Switch to English')).toBeInTheDocument();
      });
    });
  });

  describe('Visual Feedback', () => {
    it('should highlight the active language with aria-pressed="true"', async () => {
      renderLanguageSwitcher();

      await waitFor(() => {
        const englishButton = screen.getByLabelText('Switch to English');
        expect(englishButton).toHaveAttribute('aria-pressed', 'true');
      });
    });

    it('should not highlight inactive language', async () => {
      renderLanguageSwitcher();

      await waitFor(() => {
        const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
        expect(chineseButton).toHaveAttribute('aria-pressed', 'false');
      });
    });

    it('should apply active styles to the current language', async () => {
      renderLanguageSwitcher();

      await waitFor(() => {
        const englishButton = screen.getByLabelText('Switch to English');
        expect(englishButton.className).toContain('bg-white');
        expect(englishButton.className).toContain('shadow-sm');
      });
    });

    it('should apply inactive styles to non-current language', async () => {
      renderLanguageSwitcher();

      await waitFor(() => {
        const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
        expect(chineseButton.className).toContain('text-gray-600');
      });
    });
  });

  describe('Language Switching', () => {
    it('should switch language when clicking a language button', async () => {
      const user = userEvent.setup();
      renderLanguageSwitcher();

      await waitFor(() => {
        expect(screen.getByLabelText('Switch to Traditional Chinese')).toBeInTheDocument();
      });

      const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
      await user.click(chineseButton);

      await waitFor(() => {
        expect(chineseButton).toHaveAttribute('aria-pressed', 'true');
      });
    });

    it('should update HTML lang attribute when switching language', async () => {
      const user = userEvent.setup();
      renderLanguageSwitcher();

      await waitFor(() => {
        expect(screen.getByLabelText('Switch to Traditional Chinese')).toBeInTheDocument();
      });

      const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
      await user.click(chineseButton);

      await waitFor(() => {
        expect(document.documentElement.lang).toBe('zh-TW');
      });
    });

    it('should persist language preference to localStorage', async () => {
      const user = userEvent.setup();
      renderLanguageSwitcher();

      await waitFor(() => {
        expect(screen.getByLabelText('Switch to Traditional Chinese')).toBeInTheDocument();
      });

      const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
      await user.click(chineseButton);

      await waitFor(() => {
        expect(localStorage.getItem('language')).toBe('zh-TW');
      });
    });
  });

  describe('Keyboard Navigation', () => {
    it('should be keyboard navigable with Tab key', async () => {
      const user = userEvent.setup();
      renderLanguageSwitcher();

      await waitFor(() => {
        expect(screen.getByLabelText('Switch to Traditional Chinese')).toBeInTheDocument();
      });

      // Tab to first button
      await user.tab();
      const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
      expect(chineseButton).toHaveFocus();

      // Tab to second button
      await user.tab();
      const englishButton = screen.getByLabelText('Switch to English');
      expect(englishButton).toHaveFocus();
    });

    it('should activate language with Enter key', async () => {
      const user = userEvent.setup();
      renderLanguageSwitcher();

      await waitFor(() => {
        expect(screen.getByLabelText('Switch to Traditional Chinese')).toBeInTheDocument();
      });

      const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
      chineseButton.focus();

      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(chineseButton).toHaveAttribute('aria-pressed', 'true');
      });
    });

    it('should activate language with Space key', async () => {
      const user = userEvent.setup();
      renderLanguageSwitcher();

      await waitFor(() => {
        expect(screen.getByLabelText('Switch to Traditional Chinese')).toBeInTheDocument();
      });

      const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
      chineseButton.focus();

      await user.keyboard(' ');

      await waitFor(() => {
        expect(chineseButton).toHaveAttribute('aria-pressed', 'true');
      });
    });
  });

  describe('Accessibility', () => {
    it('should have minimum touch target size (44x44px)', async () => {
      renderLanguageSwitcher();

      await waitFor(() => {
        const buttons = screen.getAllByRole('button');
        buttons.forEach((button) => {
          expect(button.className).toContain('min-w-[44px]');
          expect(button.className).toContain('min-h-[44px]');
        });
      });
    });

    it('should have focus indicators', async () => {
      renderLanguageSwitcher();

      await waitFor(() => {
        const buttons = screen.getAllByRole('button');
        buttons.forEach((button) => {
          expect(button.className).toContain('focus:ring-2');
          expect(button.className).toContain('focus:ring-blue-500');
        });
      });
    });

    it('should have smooth transitions', async () => {
      renderLanguageSwitcher();

      await waitFor(() => {
        const buttons = screen.getAllByRole('button');
        buttons.forEach((button) => {
          expect(button.className).toContain('transition-colors');
          expect(button.className).toContain('duration-200');
        });
      });
    });

    it('should have proper ARIA attributes for screen readers', async () => {
      renderLanguageSwitcher();

      await waitFor(() => {
        const group = screen.getByRole('group');
        expect(group).toHaveAttribute('aria-label', 'Language selector');

        const buttons = screen.getAllByRole('button');
        buttons.forEach((button) => {
          expect(button).toHaveAttribute('aria-label');
          expect(button).toHaveAttribute('aria-pressed');
        });
      });
    });
  });

  describe('Dark Mode Support', () => {
    it('should have dark mode styles', async () => {
      renderLanguageSwitcher();

      await waitFor(() => {
        const group = screen.getByRole('group');
        expect(group.className).toContain('dark:bg-gray-800');

        const buttons = screen.getAllByRole('button');
        buttons.forEach((button) => {
          expect(button.className).toMatch(/dark:/);
        });
      });
    });
  });

  describe('Integration with I18nContext', () => {
    it('should use locale from I18nContext', async () => {
      renderLanguageSwitcher();

      await waitFor(() => {
        // Default locale should be en-US
        const englishButton = screen.getByLabelText('Switch to English');
        expect(englishButton).toHaveAttribute('aria-pressed', 'true');
      });
    });

    it('should call setLocale from I18nContext when switching', async () => {
      const user = userEvent.setup();
      renderLanguageSwitcher();

      await waitFor(() => {
        expect(screen.getByLabelText('Switch to Traditional Chinese')).toBeInTheDocument();
      });

      const chineseButton = screen.getByLabelText('Switch to Traditional Chinese');
      await user.click(chineseButton);

      await waitFor(() => {
        expect(chineseButton).toHaveAttribute('aria-pressed', 'true');
        expect(document.documentElement.lang).toBe('zh-TW');
      });
    });
  });
});
