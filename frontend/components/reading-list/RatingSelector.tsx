'use client';

import { Star } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';

interface RatingSelectorProps {
  rating: number | null;
  onChange: (rating: number | null) => void;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Interactive star rating component for article ratings
 * Validates Requirements 6.1, 6.2, 6.3, 10.4, 10.5, 11.3
 */
export function RatingSelector({
  rating,
  onChange,
  disabled = false,
  size = 'md',
}: RatingSelectorProps) {
  const [hoverRating, setHoverRating] = useState<number | null>(null);
  const [focusedIndex, setFocusedIndex] = useState<number | null>(null);

  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6',
  };

  const handleClick = (index: number) => {
    if (disabled) return;
    // If clicking the current rating, clear it
    if (rating === index) {
      onChange(null);
    } else {
      onChange(index);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    if (disabled) return;

    switch (e.key) {
      case 'ArrowRight':
      case 'ArrowUp':
        e.preventDefault();
        if (index < 5) {
          setFocusedIndex(index + 1);
          onChange(index + 1);
        }
        break;
      case 'ArrowLeft':
      case 'ArrowDown':
        e.preventDefault();
        if (index > 1) {
          setFocusedIndex(index - 1);
          onChange(index - 1);
        }
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        handleClick(index);
        break;
      case 'Escape':
        e.preventDefault();
        onChange(null);
        break;
    }
  };

  const displayRating = hoverRating ?? rating ?? 0;
  const ratingText = rating
    ? `Rated ${rating} out of 5 stars`
    : 'Not rated. Click to rate';

  return (
    <div
      className="flex items-center gap-1"
      role="group"
      aria-label={ratingText}
      onMouseLeave={() => setHoverRating(null)}
    >
      {[1, 2, 3, 4, 5].map((index) => {
        const isFilled = index <= displayRating;
        const isHovering = hoverRating !== null && index <= hoverRating;

        return (
          <button
            key={index}
            type="button"
            onClick={() => handleClick(index)}
            onMouseEnter={() => !disabled && setHoverRating(index)}
            onKeyDown={(e) => handleKeyDown(e, index)}
            onFocus={() => setFocusedIndex(index)}
            onBlur={() => setFocusedIndex(null)}
            disabled={disabled}
            aria-label={`Rate ${index} out of 5 stars`}
            className={cn(
              'transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded',
              disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer',
              'motion-reduce:transition-none',
            )}
          >
            <Star
              className={cn(
                sizeClasses[size],
                'transition-colors duration-150',
                isFilled && !isHovering && 'fill-yellow-400 text-yellow-400',
                isHovering && 'fill-yellow-300 text-yellow-300',
                !isFilled && !isHovering && 'text-gray-300 dark:text-gray-600',
                'motion-reduce:transition-none',
              )}
            />
          </button>
        );
      })}
    </div>
  );
}
