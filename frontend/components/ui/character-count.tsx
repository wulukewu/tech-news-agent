'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

export interface CharacterCountProps {
  /**
   * Current character count
   */
  current: number;
  /**
   * Maximum character limit
   */
  max: number;
  /**
   * Additional className for styling
   */
  className?: string;
  /**
   * Warning threshold percentage (default: 80%)
   * When current/max >= this value, warning color is shown
   */
  warningThreshold?: number;
  /**
   * Whether to show the count as "X / Y" or just "X / Y characters"
   */
  showLabel?: boolean;
}

/**
 * Character count component that displays current/max character count
 * with color coding based on usage percentage
 *
 * Requirements Coverage:
 * - 11.4: Display character count for text inputs with maximum length constraints
 *   - Display format: "X / Y characters" or "X / Y"
 *   - Color coding:
 *     - Default: muted color (text-muted-foreground)
 *     - Warning (80-99% of limit): yellow/warning color
 *     - Error (at or over limit): destructive color (text-destructive)
 *   - Real-time updates as user types
 */
const CharacterCount = React.forwardRef<HTMLParagraphElement, CharacterCountProps>(
  ({ current, max, className, warningThreshold = 0.8, showLabel = true }, ref) => {
    // Calculate usage percentage
    const percentage = max > 0 ? current / max : 0;

    // Determine color based on percentage
    const getColorClass = () => {
      if (percentage >= 1) {
        // At or over limit - destructive color
        return 'text-destructive';
      } else if (percentage >= warningThreshold) {
        // Warning threshold (80-99%) - yellow/warning color
        return 'text-yellow-600 dark:text-yellow-500';
      } else {
        // Default - muted color
        return 'text-muted-foreground';
      }
    };

    // Format the display text
    const displayText = showLabel ? `${current} / ${max} characters` : `${current} / ${max}`;

    return (
      <p
        ref={ref}
        className={cn('text-sm transition-colors duration-200', getColorClass(), className)}
        aria-live="polite"
        aria-atomic="true"
      >
        {displayText}
      </p>
    );
  }
);

CharacterCount.displayName = 'CharacterCount';

export { CharacterCount };
