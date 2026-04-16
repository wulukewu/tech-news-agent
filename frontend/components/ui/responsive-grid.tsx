'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { useResponsiveColumns, type ScreenSize } from '@/hooks/useResponsiveLayout';

interface ResponsiveGridProps {
  children: React.ReactNode;
  columns?: Partial<Record<ScreenSize, number>>;
  gap?: string;
  className?: string;
}

/**
 * Responsive grid component that adapts column count based on screen size
 * Supports different column counts for each breakpoint
 */
export function ResponsiveGrid({
  children,
  columns = {
    xs: 1,
    sm: 1,
    md: 2,
    lg: 3,
    xl: 4,
    '2xl': 5,
  },
  gap = '1rem',
  className,
}: ResponsiveGridProps) {
  const columnCount = useResponsiveColumns(columns);

  return (
    <div
      className={cn('grid w-full', className)}
      style={{
        gridTemplateColumns: `repeat(${columnCount}, minmax(0, 1fr))`,
        gap,
      }}
    >
      {children}
    </div>
  );
}

interface ResponsiveGridItemProps {
  children: React.ReactNode;
  span?: Partial<Record<ScreenSize, number>>;
  className?: string;
}

/**
 * Responsive grid item that can span multiple columns based on screen size
 */
export function ResponsiveGridItem({ children, span = {}, className }: ResponsiveGridItemProps) {
  const spanCount = useResponsiveColumns(span);

  return (
    <div
      className={cn('w-full', className)}
      style={{
        gridColumn: spanCount > 1 ? `span ${spanCount}` : undefined,
      }}
    >
      {children}
    </div>
  );
}

/**
 * Masonry-style responsive grid for items with varying heights
 */
export function ResponsiveMasonryGrid({
  children,
  columns = {
    xs: 1,
    sm: 2,
    md: 3,
    lg: 4,
    xl: 5,
  },
  gap = '1rem',
  className,
}: ResponsiveGridProps) {
  const columnCount = useResponsiveColumns(columns);

  // Convert children to array and distribute across columns
  const childrenArray = React.Children.toArray(children);
  const columnArrays: React.ReactNode[][] = Array.from({ length: columnCount }, () => []);

  childrenArray.forEach((child, index) => {
    const columnIndex = index % columnCount;
    columnArrays[columnIndex].push(child);
  });

  return (
    <div className={cn('flex w-full', className)} style={{ gap }}>
      {columnArrays.map((columnChildren, columnIndex) => (
        <div key={columnIndex} className="flex-1 flex flex-col" style={{ gap }}>
          {columnChildren}
        </div>
      ))}
    </div>
  );
}
