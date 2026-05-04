import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CategoryFilter } from '@/components/CategoryFilter';

describe('CategoryFilter', () => {
  const mockCategories = ['Tech News', 'AI/ML', 'Web Dev', 'DevOps', 'Security'];
  const mockOnToggleCategory = vi.fn();
  const mockOnClearAll = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render all categories as badges', () => {
    render(
      <CategoryFilter
        categories={mockCategories}
        selectedCategories={[]}
        onToggleCategory={mockOnToggleCategory}
        onClearAll={mockOnClearAll}
      />
    );
    mockCategories.forEach((category) => {
      expect(screen.getByText(category)).toBeInTheDocument();
    });
  });

  it('should render "All" badge', () => {
    render(
      <CategoryFilter
        categories={mockCategories}
        selectedCategories={[]}
        onToggleCategory={mockOnToggleCategory}
        onClearAll={mockOnClearAll}
      />
    );
    expect(screen.getByText('All')).toBeInTheDocument();
  });

  it('should not render when categories array is empty', () => {
    const { container } = render(
      <CategoryFilter
        categories={[]}
        selectedCategories={[]}
        onToggleCategory={mockOnToggleCategory}
        onClearAll={mockOnClearAll}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('should render loading skeleton when loading is true', () => {
    const { container } = render(
      <CategoryFilter
        categories={mockCategories}
        selectedCategories={[]}
        onToggleCategory={mockOnToggleCategory}
        onClearAll={mockOnClearAll}
        loading={true}
      />
    );
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('should show selected categories with aria-checked true', () => {
    render(
      <CategoryFilter
        categories={mockCategories}
        selectedCategories={['Tech News', 'AI/ML']}
        onToggleCategory={mockOnToggleCategory}
        onClearAll={mockOnClearAll}
      />
    );
    expect(screen.getByText('Tech News').closest('[role="checkbox"]')).toHaveAttribute(
      'aria-checked',
      'true'
    );
    expect(screen.getByText('Web Dev').closest('[role="checkbox"]')).toHaveAttribute(
      'aria-checked',
      'false'
    );
  });

  it('should call onToggleCategory when a badge is clicked', () => {
    render(
      <CategoryFilter
        categories={mockCategories}
        selectedCategories={['Tech News']}
        onToggleCategory={mockOnToggleCategory}
        onClearAll={mockOnClearAll}
      />
    );
    fireEvent.click(screen.getByText('AI/ML'));
    expect(mockOnToggleCategory).toHaveBeenCalledWith('AI/ML');
  });

  it('should call onClearAll when All badge is clicked', () => {
    render(
      <CategoryFilter
        categories={mockCategories}
        selectedCategories={['Tech News']}
        onToggleCategory={mockOnToggleCategory}
        onClearAll={mockOnClearAll}
      />
    );
    fireEvent.click(screen.getByText('All'));
    expect(mockOnClearAll).toHaveBeenCalledTimes(1);
  });

  it('should call onToggleCategory when Enter key is pressed on a badge', () => {
    render(
      <CategoryFilter
        categories={mockCategories}
        selectedCategories={[]}
        onToggleCategory={mockOnToggleCategory}
        onClearAll={mockOnClearAll}
      />
    );
    fireEvent.keyDown(screen.getByText('Tech News'), { key: 'Enter' });
    expect(mockOnToggleCategory).toHaveBeenCalledWith('Tech News');
  });

  it('should have proper ARIA attributes on container', () => {
    render(
      <CategoryFilter
        categories={mockCategories}
        selectedCategories={[]}
        onToggleCategory={mockOnToggleCategory}
        onClearAll={mockOnClearAll}
      />
    );
    expect(screen.getByRole('group')).toBeInTheDocument();
  });

  it('should have horizontal scroll container', () => {
    render(
      <CategoryFilter
        categories={mockCategories}
        selectedCategories={[]}
        onToggleCategory={mockOnToggleCategory}
        onClearAll={mockOnClearAll}
      />
    );
    const container = screen.getByRole('group');
    expect(container.className).toContain('overflow-x-auto');
  });
});
