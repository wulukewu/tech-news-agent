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
      <div className="flex items-center gap-2 animate-in fade-in-50 slide-in-from-left-2 duration-500">
        <span className="text-sm font-medium">{t('buttons.filter-by-category')}</span>
        <Button
          variant="ghost"
          size="sm"
          onClick={onSelectAll}
          className="h-7 text-xs transition-all duration-200 hover:scale-105 hover:shadow-sm"
          disabled={selectedCategories.length === categories.length}
        >
          {t('buttons.select-all')}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearAll}
          className="h-7 text-xs transition-all duration-200 hover:scale-105 hover:shadow-sm"
          disabled={selectedCategories.length === 0}
        >
          {t('buttons.clear-all')}
        </Button>
      </div>

      {/* Horizontal scroll container with fade edges */}
      <div className="relative animate-in fade-in-50 slide-in-from-bottom-2 duration-500 delay-200">
        <div className="pointer-events-none absolute left-0 top-0 bottom-2 w-8 bg-gradient-to-r from-background to-transparent z-10" />
        <div className="pointer-events-none absolute right-0 top-0 bottom-2 w-8 bg-gradient-to-l from-background to-transparent z-10" />
        <div
          className={cn(
            'flex gap-2 overflow-x-auto pb-2 px-6',
            'scrollbar-hide scroll-smooth',
            'snap-x snap-mandatory md:snap-none'
          )}
          role="group"
          aria-label="Category filters"
        >
          {categories.map((category, index) => {
            const isSelected = selectedCategories.includes(category);
            return (
              <Badge
                key={category}
                variant={isSelected ? 'default' : 'outline'}
                className={cn(
                  'cursor-pointer transition-all duration-200',
                  'snap-start',
                  'h-7 px-3 py-1',
                  'whitespace-nowrap flex-shrink-0',
                  'hover:shadow-sm hover:scale-105 active:scale-95',
                  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary',
                  'animate-in zoom-in-50',
                  isSelected && 'shadow-sm scale-105'
                )}
                style={{ animationDelay: `${300 + index * 50}ms` }}
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
    </div>
  );
}
