'use client';

import * as Tabs from '@radix-ui/react-tabs';
import { cn } from '@/lib/utils';
import type { ReadingListStatus } from '@/types/readingList';

interface StatusFilterTabsProps {
  selectedStatus: ReadingListStatus | null;
  onStatusChange: (status: ReadingListStatus | null) => void;
  counts?: {
    all: number;
    unread: number;
    read: number;
    archived: number;
  };
}

/**
 * Tab navigation for filtering reading list by status
 * Validates Requirements 2.1, 2.2, 2.3, 2.4, 10.3, 10.5, 11.1, 11.5
 */
export function StatusFilterTabs({
  selectedStatus,
  onStatusChange,
  counts,
}: StatusFilterTabsProps) {
  const tabs = [
    { value: 'all', label: 'All', count: counts?.all },
    { value: 'Unread', label: 'Unread', count: counts?.unread },
    { value: 'Read', label: 'Read', count: counts?.read },
    { value: 'Archived', label: 'Archived', count: counts?.archived },
  ];

  const currentValue = selectedStatus || 'all';

  return (
    <nav aria-label="Reading list status filter">
      <Tabs.Root
        value={currentValue}
        onValueChange={(value) => {
          onStatusChange(value === 'all' ? null : (value as ReadingListStatus));
        }}
      >
        <Tabs.List
          className={cn(
            'flex gap-4 border-b border-border',
            'overflow-x-auto scrollbar-hide',
            'md:overflow-x-visible',
            // Mobile horizontal scroll styling
            'pb-px', // Prevent border from being cut off during scroll
            'snap-x snap-mandatory' // Smooth snapping on mobile
          )}
        >
          {tabs.map((tab) => (
            <Tabs.Trigger
              key={tab.value}
              value={tab.value}
              className={cn(
                'relative px-4 py-3 text-sm font-medium transition-colors',
                'whitespace-nowrap flex-shrink-0', // Prevent text wrapping and shrinking
                'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded-t',
                'hover:text-foreground',
                'data-[state=active]:text-primary',
                'data-[state=inactive]:text-muted-foreground',
                'after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5',
                'after:transition-colors after:duration-200',
                'data-[state=active]:after:bg-primary',
                'motion-reduce:transition-none',
                // Mobile touch targets
                'min-h-[44px] min-w-[44px]', // Ensure minimum touch target size
                'snap-start' // Snap alignment for horizontal scroll
              )}
              aria-selected={currentValue === tab.value}
            >
              <span className="flex items-center gap-2">
                {tab.label}
                {tab.count !== undefined && (
                  <span
                    className={cn(
                      'inline-flex items-center justify-center',
                      'min-w-[1.5rem] h-5 px-1.5 rounded-full',
                      'text-xs font-medium',
                      currentValue === tab.value
                        ? 'bg-primary/10 text-primary'
                        : 'bg-muted text-muted-foreground'
                    )}
                  >
                    {tab.count}
                  </span>
                )}
              </span>
            </Tabs.Trigger>
          ))}
        </Tabs.List>
      </Tabs.Root>
    </nav>
  );
}
