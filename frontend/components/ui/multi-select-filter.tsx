'use client';

import * as React from 'react';
import { Check, ChevronDown, Search, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Badge } from '@/components/ui/badge';

export interface FilterOption<T = string> {
  value: T;
  label: string;
  count?: number;
  disabled?: boolean;
}

interface MultiSelectFilterProps<T = string> {
  options: FilterOption<T>[];
  selected: T[];
  onSelectionChange: (selected: T[]) => void;
  placeholder?: string;
  searchable?: boolean;
  maxDisplayed?: number;
  className?: string;
  disabled?: boolean;
  emptyMessage?: string;
  /** Enable bulk select/deselect actions */
  showBulkActions?: boolean;
  /** Sort options by count (desc) or alphabetically */
  sortBy?: 'count' | 'alphabetical' | 'none';
  /** Enable keyboard navigation within dropdown */
  enableKeyboardNav?: boolean;
  /** Show option counts */
  showCounts?: boolean;
}

/**
 * MultiSelectFilter - Advanced multi-select dropdown with search functionality
 *
 * Enhanced Features for Task 12.1:
 * - Advanced search with fuzzy matching
 * - Keyboard navigation within dropdown
 * - Bulk select/deselect actions
 * - Visual feedback and hover effects
 * - Improved accessibility with ARIA labels
 * - Sortable options by count or alphabetically
 *
 * Requirements:
 * - 7.1: Multi-select category filter menu with search functionality
 * - 7.7: Keyboard shortcuts and navigation support
 * - 7.9: Smooth animations and transitions
 */
export function MultiSelectFilter<T = string>({
  options,
  selected,
  onSelectionChange,
  placeholder = '選擇選項...',
  searchable = true,
  maxDisplayed = 24,
  className,
  disabled = false,
  emptyMessage = '沒有找到選項',
  showBulkActions = true,
  sortBy = 'count',
  enableKeyboardNav = true,
  showCounts = true,
}: MultiSelectFilterProps<T>) {
  const [open, setOpen] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState('');
  const [focusedIndex, setFocusedIndex] = React.useState(-1);

  // Sort and filter options based on search query and sort preference
  const filteredOptions = React.useMemo(() => {
    let filtered = options;

    // Apply search filter with fuzzy matching
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = options.filter((option) => {
        const label = option.label.toLowerCase();
        // Simple fuzzy matching - check if all characters in query exist in order
        let queryIndex = 0;
        for (let i = 0; i < label.length && queryIndex < query.length; i++) {
          if (label[i] === query[queryIndex]) {
            queryIndex++;
          }
        }
        return queryIndex === query.length || label.includes(query);
      });
    }

    // Apply sorting
    if (sortBy === 'count' && showCounts) {
      filtered = [...filtered].sort((a, b) => (b.count || 0) - (a.count || 0));
    } else if (sortBy === 'alphabetical') {
      filtered = [...filtered].sort((a, b) => a.label.localeCompare(b.label));
    }

    // Apply limit
    return filtered.slice(0, maxDisplayed);
  }, [options, searchQuery, maxDisplayed, sortBy, showCounts]);

  // Get selected option labels for display
  const selectedLabels = React.useMemo(() => {
    return selected
      .map((value) => options.find((option) => option.value === value)?.label)
      .filter(Boolean) as string[];
  }, [selected, options]);

  const handleSelect = (value: T) => {
    const newSelected = selected.includes(value)
      ? selected.filter((item) => item !== value)
      : [...selected, value];

    onSelectionChange(newSelected);
  };

  const handleClear = () => {
    onSelectionChange([]);
  };

  const handleRemoveItem = (value: T) => {
    onSelectionChange(selected.filter((item) => item !== value));
  };

  // Bulk actions
  const handleSelectAll = () => {
    const allValues = filteredOptions.map((option) => option.value);
    const newSelected = [...new Set([...selected, ...allValues])];
    onSelectionChange(newSelected);
  };

  const handleDeselectAll = () => {
    const filteredValues = new Set(filteredOptions.map((option) => option.value));
    const newSelected = selected.filter((item) => !filteredValues.has(item));
    onSelectionChange(newSelected);
  };

  // Keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (!enableKeyboardNav || !open) return;

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        setFocusedIndex((prev) => (prev < filteredOptions.length - 1 ? prev + 1 : 0));
        break;
      case 'ArrowUp':
        event.preventDefault();
        setFocusedIndex((prev) => (prev > 0 ? prev - 1 : filteredOptions.length - 1));
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        if (focusedIndex >= 0 && focusedIndex < filteredOptions.length) {
          handleSelect(filteredOptions[focusedIndex].value);
        }
        break;
      case 'Escape':
        event.preventDefault();
        setOpen(false);
        setFocusedIndex(-1);
        break;
    }
  };

  // Reset focused index when options change
  React.useEffect(() => {
    setFocusedIndex(-1);
  }, [filteredOptions]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn(
            'w-full justify-between text-left font-normal',
            !selected.length && 'text-muted-foreground',
            className
          )}
          disabled={disabled}
        >
          <div className="flex flex-wrap gap-1 flex-1 min-w-0">
            {selected.length === 0 ? (
              <span className="truncate">{placeholder}</span>
            ) : selected.length === 1 ? (
              <span className="truncate">{selectedLabels[0]}</span>
            ) : (
              <span className="truncate">已選擇 {selected.length} 個項目</span>
            )}
          </div>
          <div className="flex items-center gap-1 ml-2">
            {selected.length > 0 && (
              <Button
                variant="ghost"
                size="icon"
                className="h-4 w-4 p-0 hover:bg-transparent"
                onClick={(e) => {
                  e.stopPropagation();
                  handleClear();
                }}
                aria-label="清除所有選項"
              >
                <X className="h-3 w-3" />
              </Button>
            )}
            <ChevronDown className="h-4 w-4 opacity-50" />
          </div>
        </Button>
      </PopoverTrigger>

      <PopoverContent
        className="w-[--radix-popover-trigger-width] p-0"
        align="start"
        onKeyDown={handleKeyDown}
      >
        <div className="flex flex-col">
          {/* Search input */}
          {searchable && (
            <div className="flex items-center border-b px-3 py-2">
              <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
              <Input
                placeholder="搜尋選項..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="border-0 p-0 focus-visible:ring-0 focus-visible:ring-offset-0"
                onKeyDown={(e) => {
                  if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    setFocusedIndex(0);
                  }
                }}
              />
            </div>
          )}

          {/* Bulk actions */}
          {showBulkActions && filteredOptions.length > 0 && (
            <div className="flex items-center justify-between p-2 border-b bg-muted/30">
              <span className="text-xs text-muted-foreground">{filteredOptions.length} 個選項</span>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleSelectAll}
                  className="h-6 px-2 text-xs hover:bg-accent"
                >
                  全選
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleDeselectAll}
                  className="h-6 px-2 text-xs hover:bg-accent"
                >
                  取消選擇
                </Button>
              </div>
            </div>
          )}

          {/* Selected items display */}
          {selected.length > 0 && (
            <div className="border-b p-3">
              <div className="text-xs font-medium text-muted-foreground mb-2">
                已選擇 ({selected.length})
              </div>
              <div className="flex flex-wrap gap-1">
                {selectedLabels.map((label, index) => (
                  <Badge key={`selected-${index}`} variant="secondary" className="text-xs">
                    {label}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-3 w-3 p-0 ml-1 hover:bg-transparent"
                      onClick={() => handleRemoveItem(selected[index])}
                      aria-label={`移除 ${label}`}
                    >
                      <X className="h-2 w-2" />
                    </Button>
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Options list */}
          <div className="max-h-60 overflow-y-auto">
            {filteredOptions.length === 0 ? (
              <div className="py-6 text-center text-sm text-muted-foreground">{emptyMessage}</div>
            ) : (
              <div className="p-1">
                {filteredOptions.map((option, index) => {
                  const isSelected = selected.includes(option.value);
                  const isFocused = focusedIndex === index;

                  return (
                    <div
                      key={String(option.value)}
                      className={cn(
                        'relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-all duration-150',
                        'hover:bg-accent hover:text-accent-foreground',
                        'focus:bg-accent focus:text-accent-foreground',
                        isFocused && 'bg-accent text-accent-foreground ring-1 ring-primary/20',
                        option.disabled && 'pointer-events-none opacity-50'
                      )}
                      onClick={() => !option.disabled && handleSelect(option.value)}
                      onMouseEnter={() => setFocusedIndex(index)}
                      role="option"
                      aria-selected={isSelected}
                      data-focused={isFocused}
                    >
                      <div className="flex items-center justify-center w-4 h-4 mr-2">
                        <div
                          className={cn(
                            'w-3 h-3 border rounded-sm transition-all duration-150',
                            isSelected
                              ? 'bg-primary border-primary'
                              : 'border-muted-foreground/30 hover:border-primary/50'
                          )}
                        >
                          {isSelected && <Check className="h-2 w-2 text-primary-foreground" />}
                        </div>
                      </div>

                      <span className="flex-1 truncate">{option.label}</span>

                      {showCounts && option.count !== undefined && (
                        <span
                          className={cn(
                            'ml-2 text-xs transition-colors duration-150',
                            isFocused ? 'text-accent-foreground/70' : 'text-muted-foreground'
                          )}
                        >
                          ({option.count})
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Footer with actions */}
          {selected.length > 0 && (
            <div className="border-t p-2 flex justify-between">
              <Button variant="ghost" size="sm" onClick={handleClear} className="text-xs">
                清除全部
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setOpen(false)} className="text-xs">
                完成
              </Button>
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
