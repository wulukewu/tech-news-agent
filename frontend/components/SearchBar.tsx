'use client';
import { logger } from '@/lib/utils/logger';

import { useState, useEffect, useCallback } from 'react';
import { Search, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { debounce } from '@/lib/utils';

interface SearchBarProps {
  /** Callback when search query changes (debounced) */
  onSearch: (query: string) => void;
  /** Placeholder text */
  placeholder?: string;
  /** Debounce delay in milliseconds */
  debounceMs?: number;
  /** Additional CSS classes */
  className?: string;
  /** Show loading indicator */
  isLoading?: boolean;
}

/**
 * SearchBar Component
 *
 * A search input with debounced filtering and clear functionality.
 *
 * Requirements Coverage:
 * - 18.1: Full-width search input on mobile (< 768px)
 * - 18.2: 300ms debounce for search queries
 * - 18.3: Clear search button when active
 * - 16.6: Minimum 48px height on mobile
 *
 * Features:
 * - Debounced search (default 300ms)
 * - Clear button appears when text is entered
 * - Search icon on the left
 * - Loading indicator during search
 * - Accessible with ARIA labels
 * - Keyboard navigation support
 *
 * @example
 * ```tsx
 * <SearchBar
 *   onSearch={(query) => logger.debug('Search:', query)}
 *   placeholder="Search articles..."
 *   isLoading={isSearching}
 * />
 * ```
 */
export function SearchBar({
  onSearch,
  placeholder = 'Search articles...',
  debounceMs = 300,
  className,
  isLoading = false,
}: SearchBarProps) {
  const [query, setQuery] = useState('');

  // Create debounced search function
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const debouncedSearch = useCallback(
    debounce((searchQuery: string) => {
      onSearch(searchQuery);
    }, debounceMs),
    [onSearch, debounceMs]
  );

  // Trigger debounced search when query changes
  useEffect(() => {
    debouncedSearch(query);
  }, [query, debouncedSearch]);

  const handleClear = () => {
    setQuery('');
    onSearch('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    // Clear on Escape key
    if (e.key === 'Escape') {
      handleClear();
    }
  };

  return (
    <div
      className={cn('relative flex items-center w-full md:w-auto md:min-w-[320px]', className)}
      role="search"
    >
      {/* Search Icon */}
      <Search
        className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none"
        aria-hidden="true"
      />

      {/* Search Input */}
      <Input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className={cn(
          'pl-9 pr-9',
          query && 'pr-16' // Extra padding when clear button is visible
        )}
        aria-label="Search articles"
        aria-describedby={isLoading ? 'search-loading' : undefined}
      />

      {/* Clear Button */}
      {query && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={handleClear}
          className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 hover:bg-transparent"
          aria-label="Clear search"
        >
          <X className="h-4 w-4" />
        </Button>
      )}

      {/* Loading Indicator */}
      {isLoading && (
        <div
          className="absolute right-3 top-1/2 -translate-y-1/2"
          role="status"
          aria-live="polite"
          id="search-loading"
        >
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <span className="sr-only">Searching...</span>
        </div>
      )}
    </div>
  );
}
