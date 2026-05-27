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

import { Star, BookOpen, Terminal, Layers, Zap } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { useI18n } from '@/contexts/I18nContext';

export function TinkeringIndexStars({ index }: { index: number }) {
  const { t } = useI18n();
  const clampedIndex = Math.max(1, Math.min(5, index || 1));

  const getDescription = (idx: number): string => {
    if (idx <= 2) return 'Beginner';
    if (idx === 3) return 'Intermediate';
    if (idx === 4) return 'Advanced';
    return 'Expert';
  };

  const description = getDescription(clampedIndex);

  // Difficulty-progressive icons to unify with Settings page
  const getStarsIcon = (idx: number) => {
    if (idx <= 2) return BookOpen;
    if (idx === 3) return Terminal;
    if (idx === 4) return Layers;
    return Zap;
  };

  // Badge theme classes matching the Settings page HSL colors
  const getBadgeClasses = (idx: number) => {
    if (idx === 5) {
      // Expert -> Fuchsia
      return 'bg-fuchsia-50 text-fuchsia-700 border border-fuchsia-200/60 dark:bg-fuchsia-950/20 dark:text-fuchsia-300 dark:border-fuchsia-900/40';
    }
    if (idx === 4) {
      // Advanced -> Purple
      return 'bg-purple-50 text-purple-700 border border-purple-200/60 dark:bg-purple-950/20 dark:text-purple-300 dark:border-purple-900/40';
    }
    if (idx === 3) {
      // Intermediate -> Blue
      return 'bg-blue-50 text-blue-700 border border-blue-200/60 dark:bg-blue-950/20 dark:text-blue-300 dark:border-blue-900/40';
    }
    // Basic -> Green
    return 'bg-green-50 text-green-700 border border-green-200/60 dark:bg-green-950/20 dark:text-green-300 dark:border-green-900/40';
  };

  const Icon = getStarsIcon(clampedIndex);

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className="flex items-center gap-2 cursor-help group/stars"
            aria-label={t('article-card.tinkering-aria', { index: clampedIndex, description })}
            role="img"
          >
            {/* Unified Level Badge */}
            <span
              className={cn(
                'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider transition-all duration-300',
                getBadgeClasses(clampedIndex)
              )}
            >
              <Icon className="h-3 w-3 flex-shrink-0 animate-pulse" />
              <span>{t(`tinkering-index.level-${clampedIndex}` as any)}</span>
            </span>

            {/* Delicate monochrome star rail */}
            <div className="flex items-center gap-0.5">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star
                  key={i}
                  className={cn(
                    'h-3.5 w-3.5 min-h-[14px] min-w-[14px]',
                    'transition-all duration-300 group-hover/stars:scale-[1.05]',
                    i < clampedIndex
                      ? 'fill-yellow-400 text-yellow-400'
                      : 'text-muted-foreground/20 dark:text-muted-foreground/15'
                  )}
                  style={{ animationDelay: `${i * 50}ms` }}
                  aria-hidden="true"
                />
              ))}
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent side="top" align="center">
          <p className="text-sm font-medium">{`${clampedIndex} - ${description}`}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
