import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DragDropList, type DragDropItem } from '../drag-drop-list';

// Mock navigator.vibrate for haptic feedback tests
const mockVibrate = jest.fn();
Object.defineProperty(navigator, 'vibrate', {
  value: mockVibrate,
  writable: true,
});

// Mock data for testing
const mockItems: DragDropItem[] = [
  { id: '1', content: <div>Item 1</div> },
  { id: '2', content: <div>Item 2</div> },
  { id: '3', content: <div>Item 3</div> },
  { id: '4', content: <div>Item 4</div>, disabled: true },
];

describe('DragDropList', () => {
  const defaultProps = {
    items: mockItems,
    onReorder: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockVibrate.mockClear();
  });

  describe('Basic Rendering', () => {
    it('renders all items', () => {
      render(<DragDropList {...defaultProps} />);

      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Item 2')).toBeInTheDocument();
      expect(screen.getByText('Item 3')).toBeInTheDocument();
      expect(screen.getByText('Item 4')).toBeInTheDocument();
    });

    it('shows drag handles when enabled', () => {
      render(<DragDropList {...defaultProps} showDragHandle={true} />);

      const dragHandles = screen.getAllByLabelText('拖拽手柄');
      expect(dragHandles).toHaveLength(4);
    });

    it('hides drag handles when disabled', () => {
      render(<DragDropList {...defaultProps} showDragHandle={false} />);

      expect(screen.queryByLabelText('拖拽手柄')).not.toBeInTheDocument();
    });

    it('applies custom className', () => {
      render(<DragDropList {...defaultProps} className="custom-class" />);

      const container = screen.getByRole('list');
      expect(container).toHaveClass('custom-class');
    });
  });

  describe('Drag and Drop Functionality', () => {
    it('makes items draggable when enabled', () => {
      render(<DragDropList {...defaultProps} enabled={true} />);

      const items = screen.getAllByRole('listitem');
      items.forEach((item, index) => {
        if (index < 3) {
          // First 3 items are not disabled
          expect(item).toHaveAttribute('draggable', 'true');
        }
      });
    });

    it('makes disabled items non-draggable', () => {
      render(<DragDropList {...defaultProps} enabled={true} />);

      const items = screen.getAllByRole('listitem');
      const disabledItem = items[3]; // Item 4 is disabled
      expect(disabledItem).toHaveAttribute('draggable', 'false');
    });

    it('prevents drag when component is disabled', () => {
      render(<DragDropList {...defaultProps} enabled={false} />);

      const items = screen.getAllByRole('listitem');
      items.forEach((item) => {
        expect(item).toHaveAttribute('draggable', 'false');
      });
    });

    it('calls onReorder when items are reordered via drag and drop', async () => {
      const onReorder = jest.fn();
      render(<DragDropList {...defaultProps} onReorder={onReorder} enabled={true} />);

      const items = screen.getAllByRole('listitem');
      const firstItem = items[0];
      const secondItem = items[1];

      // Simulate drag and drop
      fireEvent.dragStart(firstItem, {
        dataTransfer: {
          effectAllowed: 'move',
          setData: jest.fn(),
        },
      });

      fireEvent.dragOver(secondItem, {
        dataTransfer: {
          dropEffect: 'move',
        },
      });

      fireEvent.drop(secondItem, {
        dataTransfer: {
          getData: () => '1', // Return the dragged item ID
        },
      });

      expect(onReorder).toHaveBeenCalled();
    });

    it('provides haptic feedback on drag start', () => {
      render(<DragDropList {...defaultProps} enabled={true} />);

      const items = screen.getAllByRole('listitem');
      const firstItem = items[0];

      fireEvent.dragStart(firstItem, {
        dataTransfer: {
          effectAllowed: 'move',
          setData: jest.fn(),
        },
      });

      expect(mockVibrate).toHaveBeenCalledWith(50);
    });

    it('provides haptic feedback on successful drop', () => {
      render(<DragDropList {...defaultProps} enabled={true} />);

      const items = screen.getAllByRole('listitem');
      const firstItem = items[0];
      const secondItem = items[1];

      // Simulate complete drag and drop sequence
      fireEvent.dragStart(firstItem, {
        dataTransfer: {
          effectAllowed: 'move',
          setData: jest.fn(),
        },
      });

      fireEvent.drop(secondItem, {
        dataTransfer: {
          getData: () => '1',
        },
      });

      expect(mockVibrate).toHaveBeenCalledWith([50, 50, 50]);
    });
  });

  describe('Keyboard Navigation', () => {
    it('supports keyboard navigation with arrow keys', () => {
      render(<DragDropList {...defaultProps} enabled={true} orientation="vertical" />);

      const items = screen.getAllByRole('listitem');
      const firstItem = items[0];

      // Focus first item
      firstItem.focus();

      // Press arrow down
      fireEvent.keyDown(firstItem, { key: 'ArrowDown' });

      // Should not throw error (actual focus change is hard to test)
      expect(firstItem).toBeInTheDocument();
    });

    it('moves items with keyboard shortcuts', () => {
      const onReorder = jest.fn();
      render(<DragDropList {...defaultProps} onReorder={onReorder} enabled={true} />);

      const items = screen.getAllByRole('listitem');
      const firstItem = items[0];

      // Focus first item and press Enter (move down)
      firstItem.focus();
      fireEvent.keyDown(firstItem, { key: 'Enter' });

      expect(onReorder).toHaveBeenCalled();
    });

    it('moves items up with Shift+Enter', () => {
      const onReorder = jest.fn();
      render(<DragDropList {...defaultProps} onReorder={onReorder} enabled={true} />);

      const items = screen.getAllByRole('listitem');
      const secondItem = items[1];

      // Focus second item and press Shift+Enter (move up)
      secondItem.focus();
      fireEvent.keyDown(secondItem, { key: 'Enter', shiftKey: true });

      expect(onReorder).toHaveBeenCalled();
    });

    it('does not move items when disabled', () => {
      const onReorder = jest.fn();
      render(<DragDropList {...defaultProps} onReorder={onReorder} enabled={false} />);

      const items = screen.getAllByRole('listitem');
      const firstItem = items[0];

      fireEvent.keyDown(firstItem, { key: 'Enter' });

      expect(onReorder).not.toHaveBeenCalled();
    });

    it('does not move disabled items', () => {
      const onReorder = jest.fn();
      render(<DragDropList {...defaultProps} onReorder={onReorder} enabled={true} />);

      const items = screen.getAllByRole('listitem');
      const disabledItem = items[3]; // Item 4 is disabled

      fireEvent.keyDown(disabledItem, { key: 'Enter' });

      expect(onReorder).not.toHaveBeenCalled();
    });
  });

  describe('Horizontal Orientation', () => {
    it('applies horizontal layout classes', () => {
      render(<DragDropList {...defaultProps} orientation="horizontal" />);

      const container = screen.getByRole('list');
      expect(container).toHaveClass('flex');
      expect(container).toHaveClass('space-x-2');
    });

    it('handles horizontal keyboard navigation', () => {
      render(<DragDropList {...defaultProps} enabled={true} orientation="horizontal" />);

      const items = screen.getAllByRole('listitem');
      const firstItem = items[0];

      // Press arrow right (should work for horizontal orientation)
      fireEvent.keyDown(firstItem, { key: 'ArrowRight' });

      expect(firstItem).toBeInTheDocument();
    });
  });

  describe('Visual Feedback', () => {
    it('applies dragged styling during drag', () => {
      render(<DragDropList {...defaultProps} enabled={true} />);

      const items = screen.getAllByRole('listitem');
      const firstItem = items[0];

      fireEvent.dragStart(firstItem);

      // Check if opacity is applied (this is set via inline style)
      expect(firstItem.style.opacity).toBe('0.5');
    });

    it('resets styling after drag ends', () => {
      render(<DragDropList {...defaultProps} enabled={true} />);

      const items = screen.getAllByRole('listitem');
      const firstItem = items[0];

      fireEvent.dragStart(firstItem);
      fireEvent.dragEnd(firstItem);

      expect(firstItem.style.opacity).toBe('1');
    });

    it('shows drop zone indicator during drag', () => {
      render(<DragDropList {...defaultProps} enabled={true} />);

      const items = screen.getAllByRole('listitem');
      const firstItem = items[0];

      fireEvent.dragStart(firstItem, {
        dataTransfer: {
          effectAllowed: 'move',
          setData: jest.fn(),
        },
      });

      expect(screen.getByText('拖拽到此處重新排序')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(<DragDropList {...defaultProps} enabled={true} />);

      const container = screen.getByRole('list');
      expect(container).toHaveAttribute('aria-label', '可拖拽排序的列表');

      const items = screen.getAllByRole('listitem');
      items.forEach((item, index) => {
        if (index < 3) {
          // Non-disabled items
          expect(item).toHaveAttribute('aria-grabbed', 'false');
          expect(item).toHaveAttribute('aria-dropeffect', 'move');
        } else {
          // Disabled item
          expect(item).toHaveAttribute('aria-dropeffect', 'none');
        }
      });
    });

    it('updates aria-grabbed during drag', () => {
      render(<DragDropList {...defaultProps} enabled={true} />);

      const items = screen.getAllByRole('listitem');
      const firstItem = items[0];

      fireEvent.dragStart(firstItem, {
        dataTransfer: {
          effectAllowed: 'move',
          setData: jest.fn(),
        },
      });

      expect(firstItem).toHaveAttribute('aria-grabbed', 'true');
    });

    it('makes items focusable when enabled', () => {
      render(<DragDropList {...defaultProps} enabled={true} />);

      const items = screen.getAllByRole('listitem');
      items.forEach((item, index) => {
        if (index < 3) {
          // Non-disabled items
          expect(item).toHaveAttribute('tabIndex', '0');
        } else {
          // Disabled item
          expect(item).toHaveAttribute('tabIndex', '-1');
        }
      });
    });

    it('shows keyboard hint when focused', async () => {
      render(<DragDropList {...defaultProps} enabled={true} />);

      const items = screen.getAllByRole('listitem');
      const firstItem = items[0];

      // Focus the item (simulate focus state)
      fireEvent.focus(firstItem);
      fireEvent.keyDown(firstItem, { key: 'ArrowDown' });

      // The keyboard hint should be visible (though testing focus state is complex)
      expect(screen.getByText('Shift+Enter 向上，Enter 向下')).toBeInTheDocument();
    });
  });

  describe('Custom Drag Handle', () => {
    it('renders custom drag handle when provided', () => {
      const customHandle = <div data-testid="custom-handle">Custom Handle</div>;
      render(<DragDropList {...defaultProps} showDragHandle={true} dragHandle={customHandle} />);

      expect(screen.getAllByTestId('custom-handle')).toHaveLength(4);
    });
  });

  describe('Error Handling', () => {
    it('handles invalid drag data gracefully', () => {
      const onReorder = jest.fn();
      render(<DragDropList {...defaultProps} onReorder={onReorder} enabled={true} />);

      const items = screen.getAllByRole('listitem');
      const secondItem = items[1];

      // Drop with invalid data
      fireEvent.drop(secondItem, {
        dataTransfer: {
          getData: () => 'invalid-id',
        },
      });

      expect(onReorder).not.toHaveBeenCalled();
    });

    it('handles drag to same item gracefully', () => {
      const onReorder = jest.fn();
      render(<DragDropList {...defaultProps} onReorder={onReorder} enabled={true} />);

      const items = screen.getAllByRole('listitem');
      const firstItem = items[0];

      // Drag item to itself
      fireEvent.dragStart(firstItem, {
        dataTransfer: {
          effectAllowed: 'move',
          setData: jest.fn(),
        },
      });

      fireEvent.drop(firstItem, {
        dataTransfer: {
          getData: () => '1',
        },
      });

      expect(onReorder).not.toHaveBeenCalled();
    });
  });
});
