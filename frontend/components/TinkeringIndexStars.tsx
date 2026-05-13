'use client';

/**
 * TinkeringIndexStars — displays a 1-5 star rating with color coding and tooltip.
 *
 * Requirements:
 * - 25.1: Display tinkering index using 1-5 star icons with color coding
 * - 25.2: Use gray for 1-2 stars, yellow for 3 stars, orange for 4-5 stars
 * - 25.3: Display filled stars for rating value, outlined for remaining
 * - 25.6: Ensure 24px minimum size on mobile viewport
 * - 25.7: Include tooltip showing numeric value and description
 * - 25.8: Use consistent star icon sizing (20px standard view)
 */

import { Star } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { useI18n } from '@/contexts/I18nContext';

export function TinkeringIndexStars({ index }: { index: number }) {
  const { t } = useI18n();
  const clampedIndex = Math.max(1, Math.min(5, index || 1));

  const getDescription = (idx: number): string => {
    if (idx <= 2) return 'Beginner';
    if (idx === 3) return 'Intermediate';
    return 'Advanced';
  };

  const getStarColor = (starIndex: number) => {
    if (starIndex >= clampedIndex) return 'text-gray-300 dark:text-gray-600';
    if (clampedIndex <= 2) return 'fill-gray-400 text-gray-400';
    if (clampedIndex === 3) return 'fill-yellow-400 text-yellow-400';
    return 'fill-orange-400 text-orange-400';
  };

  const description = getDescription(clampedIndex);

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className="flex items-center gap-1 cursor-help group/stars"
            aria-label={t('article-card.tinkering-aria', { index: clampedIndex, description })}
            role="img"
          >
            {Array.from({ length: 5 }).map((_, i) => (
              <Star
                key={i}
                className={cn(
                  'h-5 w-5 min-h-[20px] min-w-[20px]',
                  'md:h-5 md:w-5',
                  'transition-all duration-300 hover:scale-[1.05]',
                  'group-hover/stars:animate-pulse',
                  getStarColor(i)
                )}
                style={{ animationDelay: `${i * 50}ms` }}
                aria-hidden="true"
              />
            ))}
          </div>
        </TooltipTrigger>
        <TooltipContent side="top" align="center">
          <p className="text-sm font-medium">{`${clampedIndex} - ${description}`}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
