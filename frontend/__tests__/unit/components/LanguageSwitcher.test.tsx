/**
 * LanguageSwitcher Component Tests
 *
 * Tests for the language switcher component covering:
 * - Rendering both variants (icon and compact)
 * - Language switching functionality
 * - Keyboard navigation
 * - Accessibility features
 * - Dropdown behavior
 *
 * Requirements: Bilingual UI System
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { I18nProvider } from '@/contexts/I18nContext';

// Mock the I18n context
const mockSetLocale = vi.fn();

vi.mock('@/contexts/I18nContext', () => ({
  ...vi.importActual('@/contexts/I18nContext'),
  useI18n: () => ({
    locale: 'en-US',
    setLocale: mockSetLocale,
    t: (key: string) => key,
    isLoading: false,
  }),
}));

describe('LanguageSwitcher', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Icon Variant', () => {
    it('renders globe icon button', () => {
      render(<LanguageSwitcher variant="icon" />);
      const button = screen.getByLabelText('Language selector');
      expect(button).toBeInTheDocument();
    });

    it('opens dropdown when clicking globe icon', async () => {
      render(<LanguageSwitcher variant="icon" />);
      const button = screen.getByLabelText('Language selector');

      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('繁體中文')).toBeInTheDocument();
        expect(screen.getByText('English')).toBeInTheDocument();
      });
    });

    it('closes dropdown when clicking outside', async () => {
      render(
        <div>
          <LanguageSwitcher variant="icon" />
          <div data-testid="outside">Outside</div>
        </div>
      );

      const button = screen.getByLabelText('Language selector');
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('繁體中文')).toBeInTheDocument();
      });

      const outside = screen.getByTestId('outside');
      fireEvent.mouseDown(outside);

      await waitFor(() => {
        expect(screen.queryByText('繁體中文')).not.toBeInTheDocument();
      });
    });

    it('closes dropdown on Escape key', async () => {
      render(<LanguageSwitcher variant="icon" />);
      const button = screen.getByLabelText('Language selector');

      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('繁體中文')).toBeInTheDocument();
      });

      fireEvent.keyDown(document, { key: 'Escape' });

      await waitFor(() => {
        expect(screen.queryByText('繁體中文')).not.toBeInTheDocument();
      });
    });

    it('calls setLocale when selecting a language', async () => {
      render(<LanguageSwitcher variant="icon" />);
      const button = screen.getByLabelText('Language selector');

      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('繁體中文')).toBeInTheDocument();
      });

      const zhOption = screen.getByLabelText('Switch to Traditional Chinese');
      fireEvent.click(zhOption);

      expect(mockSetLocale).toHaveBeenCalledWith('zh-TW');
    });

    it('has proper ARIA attributes', () => {
      render(<LanguageSwitcher variant="icon" />);
      const button = screen.getByLabelText('Language selector');

      expect(button).toHaveAttribute('aria-expanded', 'false');
      expect(button).toHaveAttribute('aria-haspopup', 'true');

      fireEvent.click(button);

      expect(button).toHaveAttribute('aria-expanded', 'true');
    });
  });

  describe('Compact Variant', () => {
    it('renders both language options', () => {
      render(<LanguageSwitcher variant="compact" />);

      expect(screen.getByText('繁')).toBeInTheDocument();
      expect(screen.getByText('EN')).toBeInTheDocument();
      expect(screen.getByText('/')).toBeInTheDocument();
    });

    it('calls setLocale when clicking a language', () => {
      render(<LanguageSwitcher variant="compact" />);

      const zhButton = screen.getByLabelText('Switch to Traditional Chinese');
      fireEvent.click(zhButton);

      expect(mockSetLocale).toHaveBeenCalledWith('zh-TW');
    });

    it('has proper ARIA attributes for buttons', () => {
      render(<LanguageSwitcher variant="compact" />);

      const zhButton = screen.getByLabelText('Switch to Traditional Chinese');
      const enButton = screen.getByLabelText('Switch to English');

      expect(zhButton).toHaveAttribute('aria-pressed');
      expect(enButton).toHaveAttribute('aria-pressed');
    });

    it('meets minimum touch target size', () => {
      render(<LanguageSwitcher variant="compact" />);

      const zhButton = screen.getByLabelText('Switch to Traditional Chinese');
      const enButton = screen.getByLabelText('Switch to English');

      // Check that buttons have min-w-[44px] and min-h-[44px] classes
      expect(zhButton).toHaveClass('min-w-[44px]', 'min-h-[44px]');
      expect(enButton).toHaveClass('min-w-[44px]', 'min-h-[44px]');
    });
  });

  describe('Keyboard Navigation', () => {
    it('supports keyboard navigation in icon variant', async () => {
      const user = userEvent.setup();
      render(<LanguageSwitcher variant="icon" />);

      const button = screen.getByLabelText('Language selector');

      // Tab to button
      await user.tab();
      expect(button).toHaveFocus();

      // Open with Enter
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText('繁體中文')).toBeInTheDocument();
      });
    });

    it('supports keyboard navigation in compact variant', async () => {
      const user = userEvent.setup();
      render(<LanguageSwitcher variant="compact" />);

      // Tab to first button
      await user.tab();
      const zhButton = screen.getByLabelText('Switch to Traditional Chinese');
      expect(zhButton).toHaveFocus();

      // Activate with Enter
      await user.keyboard('{Enter}');
      expect(mockSetLocale).toHaveBeenCalledWith('zh-TW');
    });
  });

  describe('Accessibility', () => {
    it('has focus indicators', () => {
      render(<LanguageSwitcher variant="icon" />);
      const button = screen.getByLabelText('Language selector');

      expect(button).toHaveClass('focus:outline-none', 'focus:ring-2');
    });

    it('provides descriptive labels', () => {
      render(<LanguageSwitcher variant="icon" />);

      fireEvent.click(screen.getByLabelText('Language selector'));

      expect(screen.getByLabelText('Switch to Traditional Chinese')).toBeInTheDocument();
      expect(screen.getByLabelText('Switch to English')).toBeInTheDocument();
    });

    it('shows checkmark for active language in icon variant', async () => {
      render(<LanguageSwitcher variant="icon" />);

      fireEvent.click(screen.getByLabelText('Language selector'));

      await waitFor(() => {
        // English is active (mocked as 'en-US')
        const enOption = screen.getByLabelText('Switch to English');
        expect(enOption).toHaveTextContent('✓');
      });
    });
  });

  describe('Visual Feedback', () => {
    it('applies active styles to current language in compact variant', () => {
      render(<LanguageSwitcher variant="compact" />);

      const enButton = screen.getByLabelText('Switch to English');

      // English is active (mocked as 'en-US')
      expect(enButton).toHaveClass('text-foreground');
    });

    it('applies hover styles', () => {
      render(<LanguageSwitcher variant="compact" />);

      const zhButton = screen.getByLabelText('Switch to Traditional Chinese');

      // Check for hover classes
      expect(zhButton).toHaveClass('hover:text-foreground');
    });
  });
});
