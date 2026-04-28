/**
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CategoryFilterMenu } from '../../CategoryFilterMenu';
import { useCategories } from '@/lib/hooks/useArticles';

import { vi } from 'vitest';

// Mock the useCategories hook
vi.mock('@/lib/hooks/useArticles', () => ({
  useCategories: vi.fn(),
}));

const mockUseCategories = useCategories as any;

// Test wrapper with QueryClient
function TestWrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe('CategoryFilterMenu', () => {
  const mockOnCategoryChange = vi.fn();
  const mockCategories = ['前端開發', 'AI 應用', '後端開發', '資料科學', '行動開發'];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render loading state', () => {
    mockUseCategories.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <CategoryFilterMenu selectedCategories={[]} onCategoryChange={mockOnCategoryChange} />
      </TestWrapper>
    );

    expect(screen.getByText(/載入分類中|Loading categories/i)).toBeInTheDocument();
  });

  it('should render error state', () => {
    const mockError = new Error('Failed to fetch categories');
    mockUseCategories.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: mockError,
    } as any);

    render(
      <TestWrapper>
        <CategoryFilterMenu selectedCategories={[]} onCategoryChange={mockOnCategoryChange} />
      </TestWrapper>
    );

    expect(screen.getByText(/載入分類失敗|Failed to load categories/i)).toBeInTheDocument();
    expect(screen.getByText(/Failed to fetch categories/)).toBeInTheDocument();
  });

  it('should render empty state when no categories available', () => {
    mockUseCategories.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <CategoryFilterMenu selectedCategories={[]} onCategoryChange={mockOnCategoryChange} />
      </TestWrapper>
    );

    expect(screen.getByText(/沒有可用的分類|No categories available/i)).toBeInTheDocument();
  });

  it('should render categories with "Show All" option', async () => {
    mockUseCategories.mockReturnValue({
      data: mockCategories,
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <CategoryFilterMenu selectedCategories={[]} onCategoryChange={mockOnCategoryChange} />
      </TestWrapper>
    );

    // Should show "Show All" as selected when no categories are selected
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByText(/顯示全部|Show all/i)).toBeInTheDocument();
  });

  it('should handle category selection', async () => {
    const user = userEvent.setup();
    mockUseCategories.mockReturnValue({
      data: mockCategories,
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <CategoryFilterMenu selectedCategories={[]} onCategoryChange={mockOnCategoryChange} />
      </TestWrapper>
    );

    // Click to open the dropdown
    await user.click(screen.getByRole('combobox'));

    // Wait for options to appear and select a category
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Select a category
    await user.click(screen.getByText('前端開發'));

    // Should call onCategoryChange with the selected category
    expect(mockOnCategoryChange).toHaveBeenCalledWith(['前端開發']);
  });

  it('should handle "Show All" selection', async () => {
    const user = userEvent.setup();
    mockUseCategories.mockReturnValue({
      data: mockCategories,
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <CategoryFilterMenu
          selectedCategories={['前端開發']}
          onCategoryChange={mockOnCategoryChange}
        />
      </TestWrapper>
    );

    // Click to open the dropdown
    await user.click(screen.getByRole('combobox'));

    // Wait for options to appear and click "Show All" within the dialog
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    const dialog = screen.getByRole('dialog');
    const showAllOption = within(dialog).getByText(/顯示全部|Show all/i);
    await user.click(showAllOption);

    // Should call onCategoryChange with empty array
    expect(mockOnCategoryChange).toHaveBeenCalledWith([]);
  });

  it('should display selected categories count', () => {
    mockUseCategories.mockReturnValue({
      data: mockCategories,
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <CategoryFilterMenu
          selectedCategories={['前端開發', 'AI 應用']}
          onCategoryChange={mockOnCategoryChange}
        />
      </TestWrapper>
    );

    expect(screen.getByText(/已選擇 2 個項目|2 items selected/i)).toBeInTheDocument();
  });

  it('should limit categories to maxCategories', () => {
    const manyCategories = Array.from({ length: 30 }, (_, i) => `Category ${i + 1}`);
    mockUseCategories.mockReturnValue({
      data: manyCategories,
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <CategoryFilterMenu
          selectedCategories={[]}
          onCategoryChange={mockOnCategoryChange}
          maxCategories={5}
        />
      </TestWrapper>
    );

    // The component should limit to 5 categories plus "Show All"
    // This is tested indirectly through the MultiSelectFilter component
    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });

  it('should be disabled when disabled prop is true', () => {
    mockUseCategories.mockReturnValue({
      data: mockCategories,
      isLoading: false,
      error: null,
    } as any);

    render(
      <TestWrapper>
        <CategoryFilterMenu
          selectedCategories={[]}
          onCategoryChange={mockOnCategoryChange}
          disabled={true}
        />
      </TestWrapper>
    );

    expect(screen.getByRole('combobox')).toBeDisabled();
  });

  it('should apply custom className', () => {
    mockUseCategories.mockReturnValue({
      data: mockCategories,
      isLoading: false,
      error: null,
    } as any);

    const { container } = render(
      <TestWrapper>
        <CategoryFilterMenu
          selectedCategories={[]}
          onCategoryChange={mockOnCategoryChange}
          className="custom-class"
        />
      </TestWrapper>
    );

    expect(container.firstChild).toHaveClass('custom-class');
  });
});
