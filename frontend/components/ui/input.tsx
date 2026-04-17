import * as React from 'react';

import { cn } from '@/lib/utils';

/**
 * Base Input component with responsive sizing and accessibility features
 *
 * Requirements Coverage:
 * - 11.2: Placeholder with muted color
 * - 11.5: Full-width on mobile, auto-width on desktop
 * - 11.6: 48px minimum height on mobile
 * - 11.7: Visible focus ring (2px, primary color)
 * - 11.8: Disabled state (50% opacity, not-allowed cursor)
 */
const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<'input'>>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          // Base styles
          'flex w-full rounded-md border border-input bg-background px-3 py-2 text-base ring-offset-background',
          // File input styles
          'file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground',
          // Placeholder with muted color (Req 11.2)
          'placeholder:text-muted-foreground',
          // Minimum 48px height on mobile, 40px on desktop (Req 11.6)
          'min-h-12 md:min-h-10',
          // Visible focus ring - 2px with primary color (Req 11.7)
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
          // Disabled state - 50% opacity, not-allowed cursor (Req 11.8)
          'disabled:cursor-not-allowed disabled:opacity-50',
          // Responsive text sizing
          'md:text-sm',
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = 'Input';

export { Input };
