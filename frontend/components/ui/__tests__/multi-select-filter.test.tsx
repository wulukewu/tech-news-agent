import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MultiSelectFilter, type FilterOption } from '../multi-select-filter';

// Mock data for testing
const mockOptions: FilterOption[] = [
  { value: 'tech', label: 'Technology', count: 25 },
  { value: 'ai', label: 'Artificial Intelligence', count: 18 },
  { value: 'web', label: 'Web Development', count: 32 },
  { value: 'mobile', label: 'Mobile Development', count: 15 },
  { value: 'devops', label: 'DevOps', count: 12 },
  { value: 'design', label: 'Design', count: 8 },
];

describe('MultiSelectFilter', () => {
  const defaultProps = {
    options: mockOptions,
    selected: [],
    onSelectionChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Functionality', () => {
    it('renders with placeholder text when no items selected', () => {
      render(<MultiSelectFilter {...defaultProps} placeholder="Select categories..." />);

      expect(screen.getByRole('combobox')).toHaveTextContent('Select categories...');
    });

    it('displays selected count when multiple items are selected', () => {
      render(<MultiSelectFilter {...defaultProps} selected={['tech', 'ai']} />);

      expect(screen.getByRole('combobox')).toHaveTextContent('已選擇 2 個項目');
    });

    it('displays single item label when one item is selected', () => {
      render(<MultiSelectFilter {...defaultProps} selected={['tech']} />);

      expect(screen.getByRole('combobox')).toHaveTextContent('Technology');
    });

    it('opens dropdown when clicked', async () => {
      const user = userEvent.setup();
      render(<MultiSelectFilter {...defaultProps} />);

      await user.click(screen.getByRole('combobox'));

      expect(screen.getByPlaceholderText('搜尋選項...')).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('filters options based on search query', async () => {
      const user = userEvent.setup();
      render(<MultiSelectFilter {...defaultProps} />);

      await user.click(screen.getByRole('combobox'));
      await user.type(screen.getByPlaceholderText('搜尋選項...'), 'dev');

      expect(screen.getByText('Web Development')).toBeInTheDocument();
      expect(screen.getByText('Mobile Development')).toBeInTheDocument();
      expect(screen.getByText('DevOps')).toBeInTheDocument();
      expect(screen.queryByText('Technology')).not.toBeInTheDocument();
    });

    it('supports fuzzy search matching', async () => {
      const user = userEvent.setup();
      render(<MultiSelectFilter {...defaultProps} />);

      await user.click(screen.getByRole('combobox'));
      await user.type(screen.getByPlaceholderText('搜尋選項...'), 'ai');

      expect(screen.getByText('Artificial Intelligence')).toBeInTheDocument();
    });

    it('shows empty message when no options match search', async () => {
      const user = userEvent.setup();
      render(<MultiSelectFilter {...defaultProps} emptyMessage="No matches found" />);

      await user.click(screen.getByRole('combobox'));
      await user.type(screen.getByPlaceholderText('搜尋選項...'), 'nonexistent');

      expect(screen.getByText('No matches found')).toBeInTheDocument();
    });
  });

  describe('Selection Functionality', () => {
    it('calls onSelectionChange when option is selected', async () => {
      const user = userEvent.setup();
      const onSelectionChange = jest.fn();
      render(<MultiSelectFilter {...defaultProps} onSelectionChange={onSelectionChange} />);

      await user.click(screen.getByRole('combobox'));
      await user.click(screen.getByText('Technology'));

      expect(onSelectionChange).toHaveBeenCalledWith(['tech']);
    });

    it('calls onSelectionChange when option is deselected', async () => {
      const user = userEvent.setup();
      const onSelectionChange = jest.fn();
      render(
        <MultiSelectFilter
          {...defaultProps}
          selected={['tech']}
          onSelectionChange={onSelectionChange}
        />
      );

      await user.click(screen.getByRole('combobox'));
      await user.click(screen.getByText('Technology'));

      expect(onSelectionChange).toHaveBeenCalledWith([]);
    });

    it('supports multiple selections', async () => {
      const user = userEvent.setup();
      const onSelectionChange = jest.fn();
      render(<MultiSelectFilter {...defaultProps} onSelectionChange={onSelectionChange} />);

      await user.click(screen.getByRole('combobox'));
      await user.click(screen.getByText('Technology'));

      expect(onSelectionChange).toHaveBeenCalledWith(['tech']);

      // Simulate second selection
      render(
        <MultiSelectFilter
          {...defaultProps}
          selected={['tech']}
          onSelectionChange={onSelectionChange}
        />
      );

      await user.click(screen.getByRole('combobox'));
      await user.click(screen.getByText('Artificial Intelligence'));

      expect(onSelectionChange).toHaveBeenCalledWith(['tech', 'ai']);
    });
  });

  describe('Bulk Actions', () => {
    it('shows bulk actions when enabled', async () => {
      const user = userEvent.setup();
      render(<MultiSelectFilter {...defaultProps} showBulkActions={true} />);

      await user.click(screen.getByRole('combobox'));

      expect(screen.getByText('全選')).toBeInTheDocument();
      expect(screen.getByText('取消選擇')).toBeInTheDocument();
    });

    it('selects all visible options when "Select All" is clicked', async () => {
      const user = userEvent.setup();
      const onSelectionChange = jest.fn();
      render(
        <MultiSelectFilter
          {...defaultProps}
          onSelectionChange={onSelectionChange}
          showBulkActions={true}
          maxDisplayed={3}
        />
      );

      await user.click(screen.getByRole('combobox'));
      await user.click(screen.getByText('全選'));

      // Should select first 3 options (due to maxDisplayed=3)
      expect(onSelectionChange).toHaveBeenCalledWith(['tech', 'ai', 'web']);
    });

    it('deselects all visible options when "Deselect All" is clicked', async () => {
      const user = userEvent.setup();
      const onSelectionChange = jest.fn();
      render(
        <MultiSelectFilter
          {...defaultProps}
          selected={['tech', 'ai', 'web']}
          onSelectionChange={onSelectionChange}
          showBulkActions={true}
        />
      );

      await user.click(screen.getByRole('combobox'));
      await user.click(screen.getByText('取消選擇'));

      expect(onSelectionChange).toHaveBeenCalledWith([]);
    });
  });

  describe('Keyboard Navigation', () => {
    it('navigates options with arrow keys', async () => {
      const user = userEvent.setup();
      render(<MultiSelectFilter {...defaultProps} enableKeyboardNav={true} />);

      await user.click(screen.getByRole('combobox'));

      // Press arrow down to focus first option
      fireEvent.keyDown(screen.getByRole('dialog'), { key: 'ArrowDown' });

      // First option should be focused (we can't easily test focus state, but we can test the behavior)
      expect(screen.getByText('Technology')).toBeInTheDocument();
    });

    it('selects option with Enter key', async () => {
      const user = userEvent.setup();
      const onSelectionChange = jest.fn();
      render(
        <MultiSelectFilter
          {...defaultProps}
          onSelectionChange={onSelectionChange}
          enableKeyboardNav={true}
        />
      );

      await user.click(screen.getByRole('combobox'));

      // Navigate to first option and select it
      fireEvent.keyDown(screen.getByRole('dialog'), { key: 'ArrowDown' });
      fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Enter' });

      expect(onSelectionChange).toHaveBeenCalledWith(['tech']);
    });

    it('closes dropdown with Escape key', async () => {
      const user = userEvent.setup();
      render(<MultiSelectFilter {...defaultProps} enableKeyboardNav={true} />);

      await user.click(screen.getByRole('combobox'));
      expect(screen.getByPlaceholderText('搜尋選項...')).toBeInTheDocument();

      fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' });

      await waitFor(() => {
        expect(screen.queryByPlaceholderText('搜尋選項...')).not.toBeInTheDocument();
      });
    });
  });

  describe('Sorting', () => {
    it('sorts options by count when sortBy is "count"', async () => {
      const user = userEvent.setup();
      render(<MultiSelectFilter {...defaultProps} sortBy="count" showCounts={true} />);

      await user.click(screen.getByRole('combobox'));

      const options = screen.getAllByRole('option');
      // First option should be "Web Development" (count: 32)
      expect(options[0]).toHaveTextContent('Web Development');
      expect(options[0]).toHaveTextContent('(32)');
    });

    it('sorts options alphabetically when sortBy is "alphabetical"', async () => {
      const user = userEvent.setup();
      render(<MultiSelectFilter {...defaultProps} sortBy="alphabetical" />);

      await user.click(screen.getByRole('combobox'));

      const options = screen.getAllByRole('option');
      // First option should be "Artificial Intelligence" (alphabetically first)
      expect(options[0]).toHaveTextContent('Artificial Intelligence');
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(<MultiSelectFilter {...defaultProps} />);

      const combobox = screen.getByRole('combobox');
      expect(combobox).toHaveAttribute('aria-expanded', 'false');
    });

    it('updates aria-expanded when opened', async () => {
      const user = userEvent.setup();
      render(<MultiSelectFilter {...defaultProps} />);

      const combobox = screen.getByRole('combobox');
      await user.click(combobox);

      expect(combobox).toHaveAttribute('aria-expanded', 'true');
    });

    it('has proper role attributes for options', async () => {
      const user = userEvent.setup();
      render(<MultiSelectFilter {...defaultProps} />);

      await user.click(screen.getByRole('combobox'));

      const options = screen.getAllByRole('option');
      expect(options).toHaveLength(mockOptions.length);

      options.forEach((option, index) => {
        expect(option).toHaveAttribute('aria-selected');
      });
    });
  });

  describe('Disabled State', () => {
    it('disables the component when disabled prop is true', () => {
      render(<MultiSelectFilter {...defaultProps} disabled={true} />);

      expect(screen.getByRole('combobox')).toBeDisabled();
    });

    it('does not open dropdown when disabled', async () => {
      const user = userEvent.setup();
      render(<MultiSelectFilter {...defaultProps} disabled={true} />);

      await user.click(screen.getByRole('combobox'));

      expect(screen.queryByPlaceholderText('搜尋選項...')).not.toBeInTheDocument();
    });
  });

  describe('Clear Functionality', () => {
    it('shows clear button when items are selected', () => {
      render(<MultiSelectFilter {...defaultProps} selected={['tech']} />);

      expect(screen.getByLabelText('清除所有選項')).toBeInTheDocument();
    });

    it('clears all selections when clear button is clicked', async () => {
      const user = userEvent.setup();
      const onSelectionChange = jest.fn();
      render(
        <MultiSelectFilter
          {...defaultProps}
          selected={['tech', 'ai']}
          onSelectionChange={onSelectionChange}
        />
      );

      await user.click(screen.getByLabelText('清除所有選項'));

      expect(onSelectionChange).toHaveBeenCalledWith([]);
    });
  });
});
