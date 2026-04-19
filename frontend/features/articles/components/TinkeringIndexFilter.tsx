'use client';

import React from 'react';
import { RatingDropdown } from '@/components/ui/rating-dropdown';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import { useI18n } from '@/contexts/I18nContext';

interface TinkeringIndexFilterProps {
  /** Minimum tinkering index (1-5) */
  minValue?: number;
  /** Maximum tinkering index (1-5) */
  maxValue?: number;
  /** Callback when minimum value changes */
  onMinChange: (value: number | undefined) => void;
  /** Callback when maximum value changes */
  onMaxChange: (value: number | undefined) => void;
  /** Whether the filter is disabled */
  disabled?: boolean;
  /** Custom CSS classes */
  className?: string;
}

/**
 * TinkeringIndexFilter - Filter component for technical depth (1-5 stars)
 *
 * Features:
 * - Dual range filtering with min/max values
 * - Star-based visual representation
 * - Clear individual or both filters
 * - Validation to ensure min <= max
 *
 * Requirements:
 * - 1.3: Tinkering_Index_Filter with options for different technical depth levels (1-5 stars)
 * - 7.2: Rating_Dropdown components with star visualization and hover effects
 */
export function TinkeringIndexFilter({
  minValue,
  maxValue,
  onMinChange,
  onMaxChange,
  disabled = false,
  className,
}: TinkeringIndexFilterProps) {
  const { t } = useI18n();

  // Handle minimum value change with validation
  const handleMinChange = (value: number | undefined) => {
    if (value && maxValue && value > maxValue) {
      // If min > max, adjust max to match min
      onMaxChange(value);
    }
    onMinChange(value);
  };

  // Handle maximum value change with validation
  const handleMaxChange = (value: number | undefined) => {
    if (value && minValue && value < minValue) {
      // If max < min, adjust min to match max
      onMinChange(value);
    }
    onMaxChange(value);
  };

  // Clear all filters
  const handleClearAll = () => {
    onMinChange(undefined);
    onMaxChange(undefined);
  };

  const hasFilters = minValue !== undefined || maxValue !== undefined;

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium">{t('forms.labels.tinkering-filter')}</Label>
        {hasFilters && (
          <button
            onClick={handleClearAll}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            disabled={disabled}
          >
            {t('forms.messages.clear-filters')}
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label htmlFor="min-tinkering" className="text-xs text-muted-foreground">
            {t('forms.labels.min-depth')}
          </Label>
          <RatingDropdown
            value={minValue}
            onChange={handleMinChange}
            placeholder={t('forms.placeholders.select-min')}
            disabled={disabled}
            size="sm"
            showClear={true}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="max-tinkering" className="text-xs text-muted-foreground">
            {t('forms.labels.max-depth')}
          </Label>
          <RatingDropdown
            value={maxValue}
            onChange={handleMaxChange}
            placeholder={t('forms.placeholders.select-max')}
            disabled={disabled}
            size="sm"
            showClear={true}
          />
        </div>
      </div>

      {/* Filter summary */}
      {hasFilters && (
        <div className="text-xs text-muted-foreground">
          {minValue && maxValue && minValue === maxValue ? (
            <span>{t('forms.messages.filter-summary-equal', { level: minValue })}</span>
          ) : (
            <span>
              {t('forms.messages.filter-summary-range', {
                min: minValue ? t('forms.messages.filter-summary-min', { level: minValue }) : '',
                max: maxValue ? t('forms.messages.filter-summary-max', { level: maxValue }) : '',
              })}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
