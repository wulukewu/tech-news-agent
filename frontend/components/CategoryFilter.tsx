'use client';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useI18n } from '@/contexts/I18nContext';

interface CategoryFilterProps {
  categories: string[];
  selectedCategories: string[];
  onToggleCategory: (category: string) => void;
  onSelectAll: () => void;
  onClearAll: () => void;
  loading?: boolean;
}

export function CategoryFilter({
  categories,
  selectedCategories,
  onToggleCategory,
  onSelectAll,
  onClearAll,
  loading = false,
}: CategoryFilterProps) {
  const { t } = useI18n();

  if (loading) {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{t('buttons.filter-by-category')}</span>
          <div className="h-7 w-20 animate-pulse rounded bg-muted" />
          <div className="h-7 w-20 animate-pulse rounded bg-muted" />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-6 w-20 animate-pulse rounded-full bg-muted" />
          ))}
        </div>
      </div>
    );
  }

  if (categories.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">{t('buttons.filter-by-category')}</span>
        <Button
          variant="ghost"
          size="sm"
          onClick={onSelectAll}
          className="h-7 text-xs"
          disabled={selectedCategories.length === categories.length}
        >
          {t('buttons.select-all')}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearAll}
          className="h-7 text-xs"
          disabled={selectedCategories.length === 0}
        >
          {t('buttons.clear-all')}
        </Button>
      </div>

      {/* Horizontal scroll container for mobile */}
      <div
        className={cn(
          'flex gap-2 overflow-x-auto pb-2',
          // Hide scrollbar but keep functionality
          'scrollbar-hide',
          // Smooth scrolling
          'scroll-smooth',
          // Snap to items on mobile for better UX
          'snap-x snap-mandatory md:snap-none',
          // Add padding for better mobile scroll experience
          'px-1 -mx-1'
        )}
        role="group"
        aria-label="Category filters"
      >
        {categories.map((category) => {
          const isSelected = selectedCategories.includes(category);
          return (
            <Badge
              key={category}
              variant={isSelected ? 'default' : 'outline'}
              className={cn(
                'cursor-pointer transition-colors duration-150',
                'snap-start',
                'h-7 px-3 py-1',
                'whitespace-nowrap flex-shrink-0',
                'hover:shadow-sm',
                'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary',
                isSelected && 'shadow-sm'
              )}
              onClick={() => onToggleCategory(category)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onToggleCategory(category);
                }
              }}
              tabIndex={0}
              role="checkbox"
              aria-checked={isSelected}
              aria-label={`Filter by ${category}`}
            >
              {category}
            </Badge>
          );
        })}
      </div>
    </div>
  );
}
