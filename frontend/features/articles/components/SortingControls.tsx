'use client';

import React from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { ArrowUpDown, Calendar, Star, Tag } from 'lucide-react';
import { cn } from '@/lib/utils';

export type SortField = 'date' | 'tinkering_index' | 'category';
export type SortOrder = 'asc' | 'desc';

interface SortingControlsProps {
  /** Current sort field */
  sortBy?: SortField;
  /** Current sort order */
  sortOrder?: SortOrder;
  /** Callback when sort field changes */
  onSortByChange: (field: SortField) => void;
  /** Callback when sort order changes */
  onSortOrderChange: (order: SortOrder) => void;
  /** Whether the controls are disabled */
  disabled?: boolean;
  /** Custom CSS classes */
  className?: string;
}

const SORT_OPTIONS = [
  {
    value: 'date' as const,
    label: '發布日期',
    icon: Calendar,
    description: '按文章發布時間排序',
  },
  {
    value: 'tinkering_index' as const,
    label: '技術深度',
    icon: Star,
    description: '按技術深度評分排序',
  },
  {
    value: 'category' as const,
    label: '分類',
    icon: Tag,
    description: '按文章分類排序',
  },
] as const;

const ORDER_OPTIONS = [
  {
    value: 'desc' as const,
    label: '降序',
    description: '從高到低 / 從新到舊',
  },
  {
    value: 'asc' as const,
    label: '升序',
    description: '從低到高 / 從舊到新',
  },
] as const;

/**
 * SortingControls - Component for sorting articles
 *
 * Features:
 * - Sort by date, technical depth, or category
 * - Ascending/descending order toggle
 * - Visual icons for each sort option
 * - Descriptive labels and tooltips
 *
 * Requirements:
 * - 1.4: Sorting options by published date, tinkering index, and category
 * - 7.4: Sortable table headers for article lists
 */
export function SortingControls({
  sortBy = 'date',
  sortOrder = 'desc',
  onSortByChange,
  onSortOrderChange,
  disabled = false,
  className,
}: SortingControlsProps) {
  const currentSortOption = SORT_OPTIONS.find((option) => option.value === sortBy);
  const currentOrderOption = ORDER_OPTIONS.find((option) => option.value === sortOrder);

  const handleSortByChange = (value: string) => {
    onSortByChange(value as SortField);
  };

  const handleSortOrderChange = (value: string) => {
    onSortOrderChange(value as SortOrder);
  };

  const toggleSortOrder = () => {
    onSortOrderChange(sortOrder === 'asc' ? 'desc' : 'asc');
  };

  return (
    <div className={cn('space-y-3', className)}>
      <Label className="text-sm font-medium">排序方式</Label>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Sort Field Selection */}
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">排序依據</Label>
          <Select value={sortBy} onValueChange={handleSortByChange} disabled={disabled}>
            <SelectTrigger className="h-9">
              <SelectValue placeholder="選擇排序方式..." />
            </SelectTrigger>
            <SelectContent>
              {SORT_OPTIONS.map((option) => {
                const Icon = option.icon;
                return (
                  <SelectItem key={option.value} value={option.value}>
                    <div className="flex items-center gap-2">
                      <Icon className="h-4 w-4" />
                      <div className="flex flex-col">
                        <span>{option.label}</span>
                        <span className="text-xs text-muted-foreground">{option.description}</span>
                      </div>
                    </div>
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>
        </div>

        {/* Sort Order Selection */}
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">排序順序</Label>
          <Select value={sortOrder} onValueChange={handleSortOrderChange} disabled={disabled}>
            <SelectTrigger className="h-9">
              <SelectValue placeholder="選擇順序..." />
            </SelectTrigger>
            <SelectContent>
              {ORDER_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  <div className="flex items-center gap-2">
                    <ArrowUpDown className="h-4 w-4" />
                    <div className="flex flex-col">
                      <span>{option.label}</span>
                      <span className="text-xs text-muted-foreground">{option.description}</span>
                    </div>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Current Sort Summary */}
      <div className="text-xs text-muted-foreground">
        <span>
          按 {currentSortOption?.label} {currentOrderOption?.label}
        </span>
      </div>
    </div>
  );
}
