'use client';

import React from 'react';
import { RatingDropdown } from '@/components/ui/rating-dropdown';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

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
        <Label className="text-sm font-medium">技術深度篩選</Label>
        {hasFilters && (
          <button
            onClick={handleClearAll}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            disabled={disabled}
          >
            清除全部
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label htmlFor="min-tinkering" className="text-xs text-muted-foreground">
            最低深度
          </Label>
          <RatingDropdown
            value={minValue}
            onChange={handleMinChange}
            placeholder="選擇最低..."
            disabled={disabled}
            size="sm"
            showClear={true}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="max-tinkering" className="text-xs text-muted-foreground">
            最高深度
          </Label>
          <RatingDropdown
            value={maxValue}
            onChange={handleMaxChange}
            placeholder="選擇最高..."
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
            <span>顯示深度等級 {minValue} 星的文章</span>
          ) : (
            <span>
              顯示深度等級
              {minValue && ` ${minValue} 星以上`}
              {minValue && maxValue && '，'}
              {maxValue && ` ${maxValue} 星以下`}
              的文章
            </span>
          )}
        </div>
      )}
    </div>
  );
}
