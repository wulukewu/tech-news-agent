'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { Check, ChevronDown, Search, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { useCategories } from '@/lib/hooks/useArticles';
import { cn } from '@/lib/utils';
import { useI18n } from '@/contexts/I18nContext';

interface CategoryFilterMenuProps {
  /** Currently selected categories */
  selectedCategories: string[];
  /** Callback when selection changes */
  onCategoryChange: (categories: string[]) => void;
  /** Maximum categories to show initially (default: 24) */
  maxCategories?: number;
  /** Custom CSS classes */
  className?: string;
  /** Disabled state */
  disabled?: boolean;
}

/**
 * CategoryFilterMenu - Multi-select category filter with search
 *
 * Features:
 * - Shows top 24 most common categories by default
 * - "Show All" option to clear all filters
 * - Real-time search functionality
 * - Multi-select with visual feedback
 * - Integrates with useCategories hook for data fetching
 *
 * Requirements:
 * - 1.2: Category filtering with multi-select support
 * - 1.5: Real-time filtering without page refresh
 */
export function CategoryFilterMenu({
  selectedCategories,
  onCategoryChange,
  maxCategories = 24,
  className,
  disabled = false,
}: CategoryFilterMenuProps) {
  const [open, setOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAll, setShowAll] = useState(false);
  const { t } = useI18n();

  // Fetch categories using the hook
  const { data: categories, isLoading, error } = useCategories();

  // Filter and limit categories - MOVED BEFORE EARLY RETURNS
  const filteredCategories = useMemo(() => {
    if (!categories) return [];

    let filtered = categories;

    // Apply search filter
    if (searchQuery) {
      filtered = categories.filter((category) =>
        category.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply limit unless showing all or searching
    if (!showAll && !searchQuery) {
      filtered = filtered.slice(0, maxCategories);
    }

    return filtered;
  }, [categories, searchQuery, showAll, maxCategories]);

  // Handle category selection
  const handleSelect = useCallback(
    (categoryValue: string) => {
      const newSelection = selectedCategories.includes(categoryValue)
        ? selectedCategories.filter((c) => c !== categoryValue)
        : [...selectedCategories, categoryValue];

      onCategoryChange(newSelection);
    },
    [selectedCategories, onCategoryChange]
  );

  // Handle "Show All" selection (clear all filters)
  const handleShowAll = useCallback(() => {
    onCategoryChange([]);
    setOpen(false);
  }, [onCategoryChange]);

  // Clear all selections
  const handleClearAll = useCallback(() => {
    onCategoryChange([]);
  }, [onCategoryChange]);

  // Toggle show all categories
  const handleToggleShowAll = useCallback(() => {
    setShowAll(!showAll);
  }, [showAll]);

  // Get display text for trigger button
  const getDisplayText = () => {
    if (selectedCategories.length === 0) {
      return t('forms.messages.show-all');
    }
    if (selectedCategories.length === 1) {
      return selectedCategories[0];
    }
    return t('forms.messages.selected-count', { count: selectedCategories.length });
  };

  // Handle loading state
  if (isLoading) {
    return (
      <div className={cn('relative', className)}>
        <Button
          variant="outline"
          disabled={true}
          className="w-full justify-between text-muted-foreground"
        >
          {t('forms.messages.loading-categories')}
          <ChevronDown className="h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </div>
    );
  }

  // Handle error state
  if (error) {
    return (
      <div className={cn('relative', className)}>
        <Button
          variant="outline"
          disabled={true}
          className="w-full justify-between text-destructive"
        >
          {t('forms.messages.loading-failed')}
          <ChevronDown className="h-4 w-4 shrink-0 opacity-50" />
        </Button>
        <div className="text-xs text-destructive mt-1">{error.message}</div>
      </div>
    );
  }

  // Handle empty state
  if (!categories || categories.length === 0) {
    return (
      <div className={cn('relative', className)}>
        <Button
          variant="outline"
          disabled={true}
          className="w-full justify-between text-muted-foreground"
        >
          {t('forms.messages.no-categories')}
          <ChevronDown className="h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </div>
    );
  }

  return (
    <div className={cn('relative', className)}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className={cn(
              'w-full justify-between',
              selectedCategories.length === 0 && 'text-muted-foreground'
            )}
            disabled={disabled}
          >
            <span className="truncate">{getDisplayText()}</span>
            <div className="flex items-center gap-2">
              {selectedCategories.length > 0 && (
                <Badge variant="secondary" className="text-xs">
                  {selectedCategories.length}
                </Badge>
              )}
              <ChevronDown className="h-4 w-4 shrink-0 opacity-50" />
            </div>
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[400px] p-0" align="start">
          <div className="flex flex-col max-h-[400px]">
            {/* Search Input */}
            <div className="flex items-center border-b px-3 py-2">
              <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
              <Input
                placeholder={t('forms.placeholders.search-categories')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0"
              />
            </div>

            {/* Header with clear all button */}
            {selectedCategories.length > 0 && (
              <div className="flex items-center justify-between p-3 border-b bg-muted/50">
                <span className="text-sm text-muted-foreground">
                  {t('forms.messages.selected-categories', { count: selectedCategories.length })}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearAll}
                  className="h-6 px-2 text-xs"
                >
                  <X className="h-3 w-3 mr-1" />
                  {t('forms.messages.clear-filters')}
                </Button>
              </div>
            )}

            {/* Categories List */}
            <div className="flex-1 overflow-y-auto p-1">
              {filteredCategories.length === 0 ? (
                <div className="py-6 text-center text-sm text-muted-foreground">
                  {t('forms.messages.no-results')}
                </div>
              ) : (
                <>
                  {/* Show All option */}
                  <div
                    role="option"
                    aria-selected={selectedCategories.length === 0}
                    className={cn(
                      'flex items-center justify-between cursor-pointer rounded-sm px-2 py-2 text-sm hover:bg-accent hover:text-accent-foreground',
                      selectedCategories.length === 0 && 'bg-accent text-accent-foreground'
                    )}
                    onClick={handleShowAll}
                  >
                    <div className="flex items-center">
                      <div
                        className={cn(
                          'mr-2 flex h-4 w-4 items-center justify-center rounded-sm border border-primary',
                          selectedCategories.length === 0
                            ? 'bg-primary text-primary-foreground'
                            : 'opacity-50 [&_svg]:invisible'
                        )}
                      >
                        <Check className="h-3 w-3" />
                      </div>
                      <span className="truncate">{t('forms.messages.show-all')}</span>
                    </div>
                  </div>

                  {/* Category options */}
                  {filteredCategories.map((category) => {
                    const isSelected = selectedCategories.includes(category);
                    return (
                      <div
                        key={category}
                        role="option"
                        aria-selected={isSelected}
                        className={cn(
                          'flex items-center justify-between cursor-pointer rounded-sm px-2 py-2 text-sm hover:bg-accent hover:text-accent-foreground',
                          isSelected && 'bg-accent text-accent-foreground'
                        )}
                        onClick={() => handleSelect(category)}
                      >
                        <div className="flex items-center">
                          <div
                            className={cn(
                              'mr-2 flex h-4 w-4 items-center justify-center rounded-sm border border-primary',
                              isSelected
                                ? 'bg-primary text-primary-foreground'
                                : 'opacity-50 [&_svg]:invisible'
                            )}
                          >
                            <Check className="h-3 w-3" />
                          </div>
                          <span className="truncate">{category}</span>
                        </div>
                      </div>
                    );
                  })}

                  {/* Show All / Show Less toggle */}
                  {!searchQuery && categories.length > maxCategories && (
                    <div className="border-t mt-1 pt-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleToggleShowAll}
                        className="w-full text-xs"
                      >
                        {showAll
                          ? t('forms.messages.show-less')
                          : `${t('forms.messages.show-all')} (${categories.length})`}
                      </Button>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </PopoverContent>
      </Popover>

      {/* Selected categories display */}
      {selectedCategories.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {selectedCategories.map((categoryValue) => (
            <Badge
              key={categoryValue}
              variant="secondary"
              className="text-xs cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
              onClick={() => handleSelect(categoryValue)}
            >
              {categoryValue}
              <X className="h-3 w-3 ml-1" />
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

// Export types for external use
export type { CategoryFilterMenuProps };
