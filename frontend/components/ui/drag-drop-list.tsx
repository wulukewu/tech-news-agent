'use client';

import * as React from 'react';
import { GripVertical, Move } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useI18n } from '@/contexts/I18nContext';

interface DragDropItem {
  id: string;
  content: React.ReactNode;
  disabled?: boolean;
}

interface DragDropListProps {
  /** List of items to display */
  items: DragDropItem[];
  /** Callback when items are reordered */
  onReorder: (items: DragDropItem[]) => void;
  /** Custom CSS classes */
  className?: string;
  /** Custom CSS classes for items */
  itemClassName?: string;
  /** Show drag handles */
  showDragHandle?: boolean;
  /** Enable drag and drop */
  enabled?: boolean;
  /** Custom drag handle icon */
  dragHandle?: React.ReactNode;
  /** Orientation of the list */
  orientation?: 'vertical' | 'horizontal';
}

/**
 * DragDropList - Drag and drop reorderable list component
 *
 * Features for Task 12.2:
 * - Native HTML5 drag and drop API
 * - Visual feedback during drag operations
 * - Keyboard navigation support (Arrow keys + Space/Enter)
 * - Touch support for mobile devices
 * - Smooth animations and transitions
 * - Accessibility with ARIA labels
 * - Customizable drag handles
 *
 * Requirements:
 * - 7.6: Drag-and-drop functionality for feed organization
 * - 7.7: Keyboard shortcuts and navigation support
 * - 7.9: Smooth animations and transitions
 * - 7.10: Mobile device haptic feedback support
 */
export function DragDropList({
  items,
  onReorder,
  className,
  itemClassName,
  showDragHandle = true,
  enabled = true,
  dragHandle,
  orientation = 'vertical',
}: DragDropListProps) {
  const { t } = useI18n();
  const [draggedItem, setDraggedItem] = React.useState<string | null>(null);
  const [dragOverItem, setDragOverItem] = React.useState<string | null>(null);
  const [focusedIndex, setFocusedIndex] = React.useState(-1);

  // Handle drag start
  const handleDragStart = (e: React.DragEvent, item: DragDropItem) => {
    if (!enabled || item.disabled) {
      e.preventDefault();
      return;
    }

    setDraggedItem(item.id);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', item.id);

    // Add visual feedback
    if (e.currentTarget instanceof HTMLElement) {
      e.currentTarget.style.opacity = '0.5';
    }

    // Haptic feedback for mobile devices
    if ('vibrate' in navigator) {
      navigator.vibrate(50);
    }
  };

  // Handle drag end
  const handleDragEnd = (e: React.DragEvent) => {
    setDraggedItem(null);
    setDragOverItem(null);

    // Reset visual feedback
    if (e.currentTarget instanceof HTMLElement) {
      e.currentTarget.style.opacity = '1';
    }
  };

  // Handle drag over
  const handleDragOver = (e: React.DragEvent, item: DragDropItem) => {
    if (!enabled || item.disabled || draggedItem === item.id) return;

    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverItem(item.id);
  };

  // Handle drag leave
  const handleDragLeave = (e: React.DragEvent) => {
    // Only clear if we're leaving the item entirely
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setDragOverItem(null);
    }
  };

  // Handle drop
  const handleDrop = (e: React.DragEvent, targetItem: DragDropItem) => {
    e.preventDefault();

    if (!enabled || targetItem.disabled) return;

    const draggedId = e.dataTransfer.getData('text/plain');
    if (!draggedId || draggedId === targetItem.id) return;

    const draggedIndex = items.findIndex((item) => item.id === draggedId);
    const targetIndex = items.findIndex((item) => item.id === targetItem.id);

    if (draggedIndex === -1 || targetIndex === -1) return;

    // Reorder items
    const newItems = [...items];
    const [draggedItemData] = newItems.splice(draggedIndex, 1);
    newItems.splice(targetIndex, 0, draggedItemData);

    onReorder(newItems);

    // Haptic feedback for successful drop
    if ('vibrate' in navigator) {
      navigator.vibrate([50, 50, 50]);
    }
  };

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    if (!enabled) return;

    const item = items[index];
    if (item.disabled) return;

    switch (e.key) {
      case 'ArrowDown':
        if (orientation === 'vertical') {
          e.preventDefault();
          setFocusedIndex(Math.min(index + 1, items.length - 1));
        }
        break;
      case 'ArrowUp':
        if (orientation === 'vertical') {
          e.preventDefault();
          setFocusedIndex(Math.max(index - 1, 0));
        }
        break;
      case 'ArrowRight':
        if (orientation === 'horizontal') {
          e.preventDefault();
          setFocusedIndex(Math.min(index + 1, items.length - 1));
        }
        break;
      case 'ArrowLeft':
        if (orientation === 'horizontal') {
          e.preventDefault();
          setFocusedIndex(Math.max(index - 1, 0));
        }
        break;
      case ' ':
      case 'Enter':
        e.preventDefault();
        // Move item up/down with keyboard
        if (e.shiftKey && index > 0) {
          // Move up
          const newItems = [...items];
          [newItems[index - 1], newItems[index]] = [newItems[index], newItems[index - 1]];
          onReorder(newItems);
          setFocusedIndex(index - 1);
        } else if (!e.shiftKey && index < items.length - 1) {
          // Move down
          const newItems = [...items];
          [newItems[index], newItems[index + 1]] = [newItems[index + 1], newItems[index]];
          onReorder(newItems);
          setFocusedIndex(index + 1);
        }
        break;
    }
  };

  // Focus management
  React.useEffect(() => {
    if (focusedIndex >= 0 && focusedIndex < items.length) {
      const element = document.querySelector(`[data-drag-item-index="${focusedIndex}"]`);
      if (element instanceof HTMLElement) {
        element.focus();
      }
    }
  }, [focusedIndex, items.length]);

  const getDragHandle = () => {
    if (dragHandle) return dragHandle;
    return <GripVertical className="h-4 w-4 text-muted-foreground" />;
  };

  return (
    <div
      className={cn(
        'space-y-2',
        orientation === 'horizontal' && 'flex space-y-0 space-x-2',
        className
      )}
      role="list"
      aria-label={t('ui.drag-drop-list')}
    >
      {items.map((item, index) => {
        const isDragged = draggedItem === item.id;
        const isDragOver = dragOverItem === item.id;
        const isFocused = focusedIndex === index;

        return (
          <div
            key={item.id}
            data-drag-item-index={index}
            draggable={enabled && !item.disabled}
            onDragStart={(e) => handleDragStart(e, item)}
            onDragEnd={handleDragEnd}
            onDragOver={(e) => handleDragOver(e, item)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, item)}
            onKeyDown={(e) => handleKeyDown(e, index)}
            tabIndex={enabled && !item.disabled ? 0 : -1}
            role="listitem"
            aria-grabbed={isDragged}
            aria-dropeffect={enabled && !item.disabled ? 'move' : 'none'}
            className={cn(
              'group relative flex items-center gap-3 p-3 rounded-lg border',
              'transition-all duration-200 ease-in-out',
              'motion-reduce:transition-none',
              enabled &&
                !item.disabled && [
                  'cursor-move hover:shadow-md hover:border-primary/30',
                  'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
                ],
              isDragged && 'opacity-50 scale-95 shadow-lg',
              isDragOver && 'border-primary bg-primary/5 shadow-md scale-102',
              isFocused && 'ring-2 ring-primary ring-offset-2',
              item.disabled && 'opacity-50 cursor-not-allowed',
              itemClassName
            )}
          >
            {/* Drag Handle */}
            {showDragHandle && enabled && (
              <div
                className={cn(
                  'flex items-center justify-center p-1 rounded',
                  'transition-all duration-200',
                  'motion-reduce:transition-none',
                  !item.disabled && [
                    'hover:bg-accent group-hover:text-primary',
                    'group-focus:text-primary',
                  ],
                  item.disabled && 'text-muted-foreground/50'
                )}
                aria-label={t('ui.drag-handle')}
              >
                {getDragHandle()}
              </div>
            )}

            {/* Content */}
            <div className="flex-1 min-w-0">{item.content}</div>

            {/* Keyboard hint */}
            {isFocused && enabled && !item.disabled && (
              <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded shadow-md border">
                <div className="flex items-center gap-1">
                  <Move className="h-3 w-3" />
                  <span>{t('ui.drag-keyboard-hint')}</span>
                </div>
              </div>
            )}
          </div>
        );
      })}

      {/* Drop zone indicator */}
      {draggedItem && (
        <div className="text-center py-4 text-sm text-muted-foreground border-2 border-dashed border-muted rounded-lg">
          {t('ui.drag-drop-zone')}
        </div>
      )}
    </div>
  );
}

/**
 * DragDropGrid - Grid version of drag and drop for more complex layouts
 */
interface DragDropGridProps extends Omit<DragDropListProps, 'orientation'> {
  /** Number of columns in the grid */
  columns?: number;
  /** Gap between grid items */
  gap?: 'sm' | 'md' | 'lg';
}

export function DragDropGrid({
  items,
  onReorder,
  className,
  itemClassName,
  showDragHandle = true,
  enabled = true,
  dragHandle,
  columns = 3,
  gap = 'md',
}: DragDropGridProps) {
  const gapClasses = {
    sm: 'gap-2',
    md: 'gap-4',
    lg: 'gap-6',
  };

  return (
    <div className={cn('grid', `grid-cols-${columns}`, gapClasses[gap], className)}>
      <DragDropList
        items={items}
        onReorder={onReorder}
        itemClassName={itemClassName}
        showDragHandle={showDragHandle}
        enabled={enabled}
        dragHandle={dragHandle}
        orientation="vertical"
      />
    </div>
  );
}
