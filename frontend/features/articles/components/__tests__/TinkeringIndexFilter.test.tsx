import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { TinkeringIndexFilter } from '../TinkeringIndexFilter';

describe('TinkeringIndexFilter', () => {
  const mockOnMinChange = jest.fn();
  const mockOnMaxChange = jest.fn();

  beforeEach(() => {
    mockOnMinChange.mockClear();
    mockOnMaxChange.mockClear();
  });

  it('renders correctly with default props', () => {
    render(<TinkeringIndexFilter onMinChange={mockOnMinChange} onMaxChange={mockOnMaxChange} />);

    expect(screen.getByText('技術深度篩選')).toBeInTheDocument();
    expect(screen.getByText('最低深度')).toBeInTheDocument();
    expect(screen.getByText('最高深度')).toBeInTheDocument();
  });

  it('displays filter summary when values are set', () => {
    render(
      <TinkeringIndexFilter
        minValue={2}
        maxValue={4}
        onMinChange={mockOnMinChange}
        onMaxChange={mockOnMaxChange}
      />
    );

    expect(screen.getByText('顯示深度等級 2 星以上， 4 星以下的文章')).toBeInTheDocument();
  });

  it('displays single value summary when min equals max', () => {
    render(
      <TinkeringIndexFilter
        minValue={3}
        maxValue={3}
        onMinChange={mockOnMinChange}
        onMaxChange={mockOnMaxChange}
      />
    );

    expect(screen.getByText('顯示深度等級 3 星的文章')).toBeInTheDocument();
  });

  it('shows clear all button when filters are active', () => {
    render(
      <TinkeringIndexFilter
        minValue={2}
        onMinChange={mockOnMinChange}
        onMaxChange={mockOnMaxChange}
      />
    );

    expect(screen.getByText('清除全部')).toBeInTheDocument();
  });

  it('calls clear functions when clear all is clicked', () => {
    render(
      <TinkeringIndexFilter
        minValue={2}
        maxValue={4}
        onMinChange={mockOnMinChange}
        onMaxChange={mockOnMaxChange}
      />
    );

    fireEvent.click(screen.getByText('清除全部'));

    expect(mockOnMinChange).toHaveBeenCalledWith(undefined);
    expect(mockOnMaxChange).toHaveBeenCalledWith(undefined);
  });
});
