'use client';

import * as React from 'react';
import { Star, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import { useI18n } from '@/contexts/I18nContext';
import { TINKERING_INDEX_LEVELS } from '@/lib/constants';

interface RatingDropdownProps {
  value?: number;
  onChange: (rating: number | undefined) => void;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
  placeholder?: string;
  showClear?: boolean;
  className?: string;
}

/**
 * RatingDropdown - Enhanced star rating dropdown with hover effects
 *
 * Enhanced Features for Task 12.1:
 * - Smooth hover animations and transitions
 * - Visual feedback with star fill animations
 * - Improved accessibility with better ARIA labels
 * - Keyboard navigation support
 * - Enhanced visual design with better spacing
 *
 * Requirements:
 * - 7.2: Star rating dropdown with hover effects
 * - 7.9: Smooth animations and transitions (respecting prefers-reduced-motion)
 * - 7.7: Keyboard shortcuts and navigation support
 */
export function RatingDropdown({
  value,
  onChange,
  disabled = false,
  size = 'md',
  placeholder = '選擇評分...',
  showClear = true,
  className,
}: RatingDropdownProps) {
  const { t } = useI18n();
  const [hoveredRating, setHoveredRating] = React.useState<number | null>(null);

  // Memoize translated rating levels to prevent re-translation on every render
  // Requirements: 8.6 - Performance optimization with useMemo
  const translatedLevels = React.useMemo(
    () =>
      TINKERING_INDEX_LEVELS.map((level) => ({
        value: level.value,
        label: t(level.labelKey),
        description: t(level.descriptionKey),
      })),
    [t]
  );

  // Get label and description for a rating value
  const getRatingLabel = (rating: number) => {
    const level = translatedLevels.find((l) => l.value === rating);
    return level ? level.label : '';
  };

  const getRatingDescription = (rating: number) => {
    const level = translatedLevels.find((l) => l.value === rating);
    return level ? level.description : '';
  };

  const sizeClasses = {
    sm: 'h-8 text-sm',
    md: 'h-9 text-sm',
    lg: 'h-10 text-base',
  };

  const starSizeClasses = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  };

  const renderStars = (
    rating: number,
    interactive: boolean = false,
    isHovered: boolean = false
  ) => {
    return Array.from({ length: 5 }, (_, index) => {
      const starNumber = index + 1;
      const isFilled = starNumber <= rating;
      const shouldHighlight = interactive && hoveredRating !== null && starNumber <= hoveredRating;

      return (
        <Star
          key={starNumber}
          className={cn(
            starSizeClasses[size],
            'transition-all duration-200 ease-in-out',
            // Respect prefers-reduced-motion
            'motion-reduce:transition-none',
            isFilled || shouldHighlight
              ? 'fill-yellow-400 text-yellow-400 scale-110 motion-reduce:scale-100'
              : 'text-muted-foreground hover:text-yellow-300',
            // Add subtle glow effect on hover
            (shouldHighlight || (isFilled && isHovered)) && 'drop-shadow-sm'
          )}
          style={{
            // Stagger animation for visual appeal
            transitionDelay: interactive ? `${index * 50}ms` : '0ms',
          }}
        />
      );
    });
  };

  const handleRatingSelect = (rating: number) => {
    onChange(rating);
  };

  const handleClear = () => {
    onChange(undefined);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            'justify-between font-normal transition-all duration-200',
            'hover:border-yellow-300 hover:shadow-sm',
            'focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20',
            sizeClasses[size],
            !value && 'text-muted-foreground',
            className
          )}
          disabled={disabled}
          onMouseEnter={() => value && setHoveredRating(value)}
          onMouseLeave={() => setHoveredRating(null)}
        >
          <div className="flex items-center gap-2">
            {value ? (
              <>
                <div className="flex items-center gap-1">
                  {renderStars(value, false, hoveredRating === value)}
                </div>
                <span className="transition-colors duration-200">{getRatingLabel(value)}</span>
              </>
            ) : (
              <span>{placeholder}</span>
            )}
          </div>
          <ChevronDown className="h-4 w-4 opacity-50 transition-transform duration-200 group-data-[state=open]:rotate-180" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="start" className="w-64 p-1">
        <DropdownMenuLabel className="px-2 py-1.5 text-sm font-medium">
          {t('forms.labels.tinkering-filter')}
        </DropdownMenuLabel>

        {[1, 2, 3, 4, 5].map((rating) => (
          <DropdownMenuItem
            key={rating}
            onClick={() => handleRatingSelect(rating)}
            onMouseEnter={() => setHoveredRating(rating)}
            onMouseLeave={() => setHoveredRating(null)}
            className={cn(
              'flex items-center gap-3 cursor-pointer p-3 rounded-md',
              'transition-all duration-200 ease-in-out',
              'hover:bg-accent/80 hover:shadow-sm',
              'focus:bg-accent focus:shadow-sm',
              value === rating && 'bg-accent/60 border border-accent-foreground/10'
            )}
          >
            <div className="flex items-center gap-1 min-w-[120px]">{renderStars(rating, true)}</div>
            <div className="flex flex-col flex-1">
              <span className="font-medium text-sm">{getRatingLabel(rating)}</span>
              <span className="text-xs text-muted-foreground leading-tight">
                {getRatingDescription(rating)}
              </span>
            </div>
            {value === rating && (
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse motion-reduce:animate-none" />
            )}
          </DropdownMenuItem>
        ))}

        {showClear && value && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleClear} className="text-muted-foreground">
              {t('forms.messages.clear-filters')}
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
