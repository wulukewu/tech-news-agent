'use client';

import React, { useMemo } from 'react';
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
import { useI18n } from '@/contexts/I18nContext';

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
  const { t } = useI18n();

  // Memoize translated sort options to prevent re-translation on every render
  // Requirements: 8.6 - Performance optimization with useMemo
  const translatedSortOptions = useMemo(
    () =>
      SORT_OPTIONS.map((option) => {
        // Map value to translation key (tinkering_index -> tinkering-index)
        const translationKey = option.value.replace('_', '-');
        return {
          ...option,
          translatedLabel: t(`forms.sort-options.${translationKey}`),
        };
      }),
    [t]
  );

  // Memoize translated order options
  const translatedOrderOptions = useMemo(
    () =>
      ORDER_OPTIONS.map((option) => ({
        ...option,
        translatedLabel: t(`forms.order-options.${option.value}`),
      })),
    [t]
  );

  const currentSortOption = translatedSortOptions.find((option) => option.value === sortBy);
  const currentOrderOption = translatedOrderOptions.find((option) => option.value === sortOrder);

  const handleSortByChange = (value: string) => {
    onSortByChange(value as SortField);
  };

  const handleSortOrderChange = (value: string) => {
    onSortOrderChange(value as SortOrder);
  };

  return (
    <div className={cn('space-y-3', className)}>
      <Label className="text-sm font-medium">{t('forms.labels.sort-by')}</Label>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Sort Field Selection */}
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">{t('forms.labels.sort-field')}</Label>
          <Select value={sortBy} onValueChange={handleSortByChange} disabled={disabled}>
            <SelectTrigger className="h-9">
              <SelectValue placeholder={t('forms.placeholders.select-sort-by')} />
            </SelectTrigger>
            <SelectContent>
              {translatedSortOptions.map((option) => {
                const Icon = option.icon;
                return (
                  <SelectItem key={option.value} value={option.value}>
                    <div className="flex items-center gap-2">
                      <Icon className="h-4 w-4" />
                      <span>{option.translatedLabel}</span>
                    </div>
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>
        </div>

        {/* Sort Order Selection */}
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">{t('forms.labels.sort-order')}</Label>
          <Select value={sortOrder} onValueChange={handleSortOrderChange} disabled={disabled}>
            <SelectTrigger className="h-9">
              <SelectValue placeholder={t('forms.placeholders.select-order')} />
            </SelectTrigger>
            <SelectContent>
              {translatedOrderOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  <div className="flex items-center gap-2">
                    <ArrowUpDown className="h-4 w-4" />
                    <span>{option.translatedLabel}</span>
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
          {t('forms.messages.sort-summary', {
            field: currentSortOption?.translatedLabel || '',
            order: currentOrderOption?.translatedLabel || '',
          })}
        </span>
      </div>
    </div>
  );
}
