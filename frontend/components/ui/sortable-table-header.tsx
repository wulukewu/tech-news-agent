'use client';

import * as React from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

export type SortDirection = 'asc' | 'desc' | null;

interface SortableTableHeaderProps {
  /** Column identifier */
  column: string;
  /** Display label for the column */
  children: React.ReactNode;
  /** Current sort column */
  sortColumn?: string;
  /** Current sort direction */
  sortDirection?: SortDirection;
  /** Callback when sort changes */
  onSort?: (column: string, direction: SortDirection) => void;
  /** Whether this column is sortable */
  sortable?: boolean;
  /** Custom CSS classes */
  className?: string;
  /** Alignment of content */
  align?: 'left' | 'center' | 'right';
  /** Width of the column */
  width?: string | number;
}

/**
 * SortableTableHeader - Interactive table header with sorting functionality
 *
 * Features for Task 12.1:
 * - Click to sort with visual feedback
 * - Three-state sorting: none -> asc -> desc -> none
 * - Smooth animations and hover effects
 * - Keyboard navigation support
 * - ARIA labels for accessibility
 * - Visual indicators for current sort state
 *
 * Requirements:
 * - 7.4: Sortable table headers for article lists
 * - 7.7: Keyboard shortcuts and navigation support
 * - 7.9: Smooth animations and transitions
 */
export function SortableTableHeader({
  column,
  children,
  sortColumn,
  sortDirection,
  onSort,
  sortable = true,
  className,
  align = 'left',
  width,
}: SortableTableHeaderProps) {
  const isActive = sortColumn === column;
  const currentDirection = isActive ? sortDirection : null;

  const handleSort = () => {
    if (!sortable || !onSort) return;

    let newDirection: SortDirection;

    if (!isActive || currentDirection === null) {
      newDirection = 'asc';
    } else if (currentDirection === 'asc') {
      newDirection = 'desc';
    } else {
      newDirection = null;
    }

    onSort(column, newDirection);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleSort();
    }
  };

  const getSortIcon = () => {
    if (!sortable) return null;

    if (!isActive || currentDirection === null) {
      return <ArrowUpDown className="h-4 w-4 opacity-50" />;
    }

    return currentDirection === 'asc' ? (
      <ArrowUp className="h-4 w-4 text-primary" />
    ) : (
      <ArrowDown className="h-4 w-4 text-primary" />
    );
  };

  const getSortLabel = () => {
    if (!isActive || currentDirection === null) {
      return '點擊排序';
    }
    return currentDirection === 'asc' ? '升序排列' : '降序排列';
  };

  if (!sortable) {
    return (
      <div
        className={cn(
          'flex items-center px-3 py-2 text-sm font-medium text-muted-foreground',
          align === 'center' && 'justify-center',
          align === 'right' && 'justify-end',
          className
        )}
        style={{ width }}
      >
        {children}
      </div>
    );
  }

  return (
    <Button
      variant="ghost"
      onClick={handleSort}
      onKeyDown={handleKeyDown}
      className={cn(
        'flex items-center gap-2 px-3 py-2 h-auto text-sm font-medium',
        'hover:bg-accent/50 hover:text-accent-foreground',
        'focus:bg-accent focus:text-accent-foreground',
        'transition-all duration-200 ease-in-out',
        'motion-reduce:transition-none',
        isActive && 'text-primary bg-accent/30',
        align === 'center' && 'justify-center',
        align === 'right' && 'justify-end',
        className
      )}
      style={{ width }}
      aria-label={`${children} - ${getSortLabel()}`}
      aria-sort={
        !isActive || currentDirection === null
          ? 'none'
          : currentDirection === 'asc'
            ? 'ascending'
            : 'descending'
      }
    >
      <span className="truncate">{children}</span>
      <div
        className={cn(
          'transition-all duration-200 ease-in-out',
          'motion-reduce:transition-none',
          isActive ? 'scale-100 opacity-100' : 'scale-90 opacity-50 group-hover:opacity-75'
        )}
      >
        {getSortIcon()}
      </div>
    </Button>
  );
}

/**
 * SortableTable - Container component for sortable table
 */
interface SortableTableProps {
  children: React.ReactNode;
  className?: string;
}

export function SortableTable({ children, className }: SortableTableProps) {
  return (
    <div className={cn('overflow-x-auto', className)}>
      <table className="w-full border-collapse">{children}</table>
    </div>
  );
}

/**
 * SortableTableHead - Table head wrapper
 */
interface SortableTableHeadProps {
  children: React.ReactNode;
  className?: string;
}

export function SortableTableHead({ children, className }: SortableTableHeadProps) {
  return (
    <thead className={cn('border-b border-border', className)}>
      <tr className="hover:bg-muted/50 transition-colors duration-200">{children}</tr>
    </thead>
  );
}

/**
 * SortableTableBody - Table body wrapper
 */
interface SortableTableBodyProps {
  children: React.ReactNode;
  className?: string;
}

export function SortableTableBody({ children, className }: SortableTableBodyProps) {
  return <tbody className={className}>{children}</tbody>;
}

/**
 * SortableTableRow - Table row wrapper with hover effects
 */
interface SortableTableRowProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  selected?: boolean;
}

export function SortableTableRow({
  children,
  className,
  onClick,
  selected = false,
}: SortableTableRowProps) {
  return (
    <tr
      className={cn(
        'border-b border-border/50 transition-all duration-200',
        'hover:bg-muted/30 hover:shadow-sm',
        'motion-reduce:transition-none',
        onClick && 'cursor-pointer',
        selected && 'bg-accent/20 border-accent',
        className
      )}
      onClick={onClick}
    >
      {children}
    </tr>
  );
}

/**
 * SortableTableCell - Table cell wrapper
 */
interface SortableTableCellProps {
  children: React.ReactNode;
  className?: string;
  align?: 'left' | 'center' | 'right';
}

export function SortableTableCell({ children, className, align = 'left' }: SortableTableCellProps) {
  return (
    <td
      className={cn(
        'px-3 py-2 text-sm',
        align === 'center' && 'text-center',
        align === 'right' && 'text-right',
        className
      )}
    >
      {children}
    </td>
  );
}
