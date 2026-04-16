import React from 'react';
import { render, screen } from '@testing-library/react';
import { SortingControls } from '../SortingControls';

describe('SortingControls', () => {
  const mockOnSortByChange = jest.fn();
  const mockOnSortOrderChange = jest.fn();

  beforeEach(() => {
    mockOnSortByChange.mockClear();
    mockOnSortOrderChange.mockClear();
  });

  it('renders correctly with default props', () => {
    render(
      <SortingControls
        onSortByChange={mockOnSortByChange}
        onSortOrderChange={mockOnSortOrderChange}
      />
    );

    expect(screen.getByText('排序方式')).toBeInTheDocument();
    expect(screen.getByText('排序依據')).toBeInTheDocument();
    expect(screen.getByText('排序順序')).toBeInTheDocument();
  });

  it('displays current sort summary', () => {
    render(
      <SortingControls
        sortBy="tinkering_index"
        sortOrder="asc"
        onSortByChange={mockOnSortByChange}
        onSortOrderChange={mockOnSortOrderChange}
      />
    );

    expect(screen.getByText('按 技術深度 升序')).toBeInTheDocument();
  });

  it('shows correct default values', () => {
    render(
      <SortingControls
        onSortByChange={mockOnSortByChange}
        onSortOrderChange={mockOnSortOrderChange}
      />
    );

    expect(screen.getByText('按 發布日期 降序')).toBeInTheDocument();
  });
});
