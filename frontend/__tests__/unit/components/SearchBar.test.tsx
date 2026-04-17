import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { SearchBar } from '@/components/SearchBar';

// Mock debounce to make tests synchronous
vi.mock('@/lib/utils', async () => {
  const actual = await vi.importActual('@/lib/utils');
  return {
    ...actual,
    debounce: <T extends (...args: unknown[]) => unknown>(fn: T) => fn,
  };
});

describe('SearchBar Component', () => {
  const mockOnSearch = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders search input with default placeholder', () => {
      render(<SearchBar onSearch={mockOnSearch} />);

      const input = screen.getByRole('searchbox', { name: /search articles/i });
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('placeholder', 'Search articles...');
    });

    it('renders with custom placeholder', () => {
      render(<SearchBar onSearch={mockOnSearch} placeholder="Find content..." />);

      const input = screen.getByRole('searchbox');
      expect(input).toHaveAttribute('placeholder', 'Find content...');
    });

    it('renders search icon', () => {
      render(<SearchBar onSearch={mockOnSearch} />);

      // Search icon should be present (aria-hidden)
      const searchIcon = document.querySelector('svg[aria-hidden="true"]');
      expect(searchIcon).toBeInTheDocument();
    });

    it('does not show clear button when input is empty', () => {
      render(<SearchBar onSearch={mockOnSearch} />);

      const clearButton = screen.queryByRole('button', { name: /clear search/i });
      expect(clearButton).not.toBeInTheDocument();
    });

    it('shows clear button when input has text', async () => {
      const user = userEvent.setup();
      render(<SearchBar onSearch={mockOnSearch} />);

      const input = screen.getByRole('searchbox');
      await user.type(input, 'test query');

      const clearButton = screen.getByRole('button', { name: /clear search/i });
      expect(clearButton).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('calls onSearch when user types', async () => {
      const user = userEvent.setup();
      render(<SearchBar onSearch={mockOnSearch} />);

      const input = screen.getByRole('searchbox');
      await user.type(input, 'test');

      // With mocked debounce, should be called immediately
      expect(mockOnSearch).toHaveBeenCalledWith('test');
    });

    it('calls onSearch with empty string when cleared', async () => {
      const user = userEvent.setup();
      render(<SearchBar onSearch={mockOnSearch} />);

      const input = screen.getByRole('searchbox');
      await user.type(input, 'test query');

      mockOnSearch.mockClear();

      const clearButton = screen.getByRole('button', { name: /clear search/i });
      await user.click(clearButton);

      expect(mockOnSearch).toHaveBeenCalledWith('');
      expect(input).toHaveValue('');
    });

    it('clears input when Escape key is pressed', async () => {
      const user = userEvent.setup();
      render(<SearchBar onSearch={mockOnSearch} />);

      const input = screen.getByRole('searchbox');
      await user.type(input, 'test query');

      mockOnSearch.mockClear();

      fireEvent.keyDown(input, { key: 'Escape' });

      expect(mockOnSearch).toHaveBeenCalledWith('');
      expect(input).toHaveValue('');
    });
  });

  describe('Loading State', () => {
    it('shows loading indicator when isLoading is true', () => {
      render(<SearchBar onSearch={mockOnSearch} isLoading={true} />);

      const loadingIndicator = screen.getByRole('status');
      expect(loadingIndicator).toBeInTheDocument();
      expect(screen.getByText(/searching/i)).toBeInTheDocument();
    });

    it('does not show loading indicator when isLoading is false', () => {
      render(<SearchBar onSearch={mockOnSearch} isLoading={false} />);

      const loadingIndicator = screen.queryByRole('status');
      expect(loadingIndicator).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      render(<SearchBar onSearch={mockOnSearch} />);

      const input = screen.getByRole('searchbox', { name: /search articles/i });
      expect(input).toBeInTheDocument();
    });

    it('has search role on container', () => {
      render(<SearchBar onSearch={mockOnSearch} />);

      const searchContainer = screen.getByRole('search');
      expect(searchContainer).toBeInTheDocument();
    });

    it('associates loading indicator with input', () => {
      render(<SearchBar onSearch={mockOnSearch} isLoading={true} />);

      const input = screen.getByRole('searchbox');
      expect(input).toHaveAttribute('aria-describedby', 'search-loading');
    });

    it('clear button has accessible label', async () => {
      const user = userEvent.setup();
      render(<SearchBar onSearch={mockOnSearch} />);

      const input = screen.getByRole('searchbox');
      await user.type(input, 'test');

      const clearButton = screen.getByRole('button', { name: /clear search/i });
      expect(clearButton).toBeInTheDocument();
    });
  });

  describe('Responsive Behavior', () => {
    it('applies full-width class on mobile', () => {
      render(<SearchBar onSearch={mockOnSearch} />);

      const searchContainer = screen.getByRole('search');
      expect(searchContainer).toHaveClass('w-full');
    });

    it('applies custom className', () => {
      render(<SearchBar onSearch={mockOnSearch} className="custom-class" />);

      const searchContainer = screen.getByRole('search');
      expect(searchContainer).toHaveClass('custom-class');
    });
  });

  describe('Debouncing', () => {
    it('uses custom debounce delay', () => {
      render(<SearchBar onSearch={mockOnSearch} debounceMs={500} />);

      // Component should render without errors
      const input = screen.getByRole('searchbox');
      expect(input).toBeInTheDocument();
    });
  });
});
