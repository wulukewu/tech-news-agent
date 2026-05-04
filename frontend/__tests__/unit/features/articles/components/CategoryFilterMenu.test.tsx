import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/__tests__/utils/test-utils';
import { CategoryFilterMenu } from '@/features/articles/components/CategoryFilterMenu';

import * as useArticlesModule from '@/lib/hooks/useArticles';

vi.mock('@/lib/hooks/useArticles', () => ({
  useArticles: vi.fn(),
  useCategories: vi.fn(),
}));

describe('CategoryFilterMenu', () => {
  const mockOnSelectionChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useArticlesModule.useCategories).mockReturnValue({
      data: ['Technology', 'Artificial Intelligence', 'Web Development', 'Mobile Development'],
      isLoading: false,
      error: null,
    });
  });

  it('should render with show-all text when no categories selected', () => {
    renderWithProviders(
      <CategoryFilterMenu selectedCategories={[]} onSelectionChange={mockOnSelectionChange} />
    );
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByText('Show All')).toBeInTheDocument();
  });

  it('should display selected count when multiple categories selected', () => {
    renderWithProviders(
      <CategoryFilterMenu
        selectedCategories={['Technology', 'Artificial Intelligence']}
        onSelectionChange={mockOnSelectionChange}
      />
    );
    expect(screen.getByText('2 items selected')).toBeInTheDocument();
  });

  it('should display single category name when one selected', () => {
    renderWithProviders(
      <CategoryFilterMenu
        selectedCategories={['Technology']}
        onSelectionChange={mockOnSelectionChange}
      />
    );
    expect(screen.getAllByText('Technology').length).toBeGreaterThan(0);
  });

  it('should open dropdown when trigger is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <CategoryFilterMenu selectedCategories={[]} onSelectionChange={mockOnSelectionChange} />
    );
    await user.click(screen.getByRole('combobox'));
    await waitFor(() => {
      expect(screen.getAllByText('Technology').length).toBeGreaterThan(0);
    });
  });

  it('should show loading state', () => {
    vi.mocked(useArticlesModule.useCategories).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });
    renderWithProviders(
      <CategoryFilterMenu selectedCategories={[]} onSelectionChange={mockOnSelectionChange} />
    );
    expect(screen.getByText('Loading categories...')).toBeInTheDocument();
  });

  it('should show no categories message when empty', () => {
    vi.mocked(useArticlesModule.useCategories).mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });
    renderWithProviders(
      <CategoryFilterMenu selectedCategories={[]} onSelectionChange={mockOnSelectionChange} />
    );
    expect(screen.getByText('No categories available')).toBeInTheDocument();
  });

  it('should be disabled when disabled prop is true', () => {
    renderWithProviders(
      <CategoryFilterMenu
        selectedCategories={[]}
        onSelectionChange={mockOnSelectionChange}
        disabled={true}
      />
    );
    expect(screen.getByRole('combobox')).toBeDisabled();
  });
});
