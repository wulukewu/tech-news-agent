'use client';

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { useI18n } from '@/contexts/I18nContext';

interface CategoryFilterProps {
  categories: string[];
  selectedCategories: string[];
  onToggleCategory: (category: string) => void;
  onClearAll: () => void;
  loading?: boolean;
}

export function CategoryFilter({
  categories,
  selectedCategories,
  onToggleCategory,
  onClearAll,
  loading = false,
}: CategoryFilterProps) {
  const { t } = useI18n();
  const isAllSelected = selectedCategories.length === 0;

  if (loading) {
    return (
      <div className="flex gap-2 overflow-x-auto pb-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-7 w-20 animate-pulse rounded-full bg-muted flex-shrink-0" />
        ))}
      </div>
    );
  }

  if (categories.length === 0) return null;

  return (
    <div className="relative">
      {/* fade edges */}
      <div className="pointer-events-none absolute left-0 inset-y-0 w-8 bg-gradient-to-r from-background to-transparent z-10" />
      <div className="pointer-events-none absolute right-0 inset-y-0 w-8 bg-gradient-to-l from-background to-transparent z-10" />

      <div
        className="flex gap-2 overflow-x-auto py-1 pb-2 px-8 scrollbar-hide scroll-smooth"
        role="group"
        aria-label={t('buttons.filter-by-category')}
      >
        {/* All tag */}
        <Badge
          variant={isAllSelected ? 'default' : 'outline'}
          className={cn(
            'cursor-pointer transition-all duration-200 h-7 px-3 whitespace-nowrap flex-shrink-0',
            'hover:shadow-sm active:scale-95',
            isAllSelected && 'shadow-sm'
          )}
          onClick={onClearAll}
          role="radio"
          aria-checked={isAllSelected}
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onClearAll();
            }
          }}
        >
          {t('ui.all')}
        </Badge>

        {categories.map((category) => {
          const isSelected = selectedCategories.includes(category);
          return (
            <Badge
              key={category}
              variant={isSelected ? 'default' : 'outline'}
              className={cn(
                'cursor-pointer transition-all duration-200 h-7 px-3 whitespace-nowrap flex-shrink-0',
                'hover:shadow-sm active:scale-95',
                isSelected && 'shadow-sm'
              )}
              onClick={() => onToggleCategory(category)}
              role="checkbox"
              aria-checked={isSelected}
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onToggleCategory(category);
                }
              }}
            >
              {category}
            </Badge>
          );
        })}
      </div>
    </div>
  );
}
