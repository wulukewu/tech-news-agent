'use client';

import * as React from 'react';
import * as CheckboxPrimitive from '@radix-ui/react-checkbox';
import { Check, Minus } from 'lucide-react';

import { cn } from '@/lib/utils';

/**
 * Checkbox component with WCAG AA accessibility compliance
 *
 * Features:
 * - 44x44px minimum touch target (Req 2.1)
 * - Visible 2px focus ring with primary color (Req 15.3)
 * - Keyboard navigation support (Space to toggle) (Req 15.2)
 * - Checked, unchecked, and indeterminate states
 * - Disabled state with 50% opacity
 * - Smooth transitions (200ms)
 *
 * @example
 * ```tsx
 * <Checkbox id="terms" />
 * <label htmlFor="terms">Accept terms and conditions</label>
 * ```
 */
const Checkbox = React.forwardRef<
  React.ElementRef<typeof CheckboxPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof CheckboxPrimitive.Root>
>(({ className, ...props }, ref) => (
  <CheckboxPrimitive.Root
    ref={ref}
    className={cn(
      // Base styles - actual checkbox is 20x20px but touch target is 44x44px
      'peer h-5 w-5 shrink-0 rounded-sm border-2 border-primary',
      // Touch target - minimum 44x44px clickable area
      'min-h-44 min-w-44 inline-flex items-center justify-center',
      // Focus indicator - 2px ring with primary color (Req 15.3)
      'ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
      // States
      'data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground data-[state=checked]:border-primary',
      'data-[state=indeterminate]:bg-primary data-[state=indeterminate]:text-primary-foreground data-[state=indeterminate]:border-primary',
      // Disabled state - 50% opacity
      'disabled:cursor-not-allowed disabled:opacity-50',
      // Transitions - smooth 200ms
      'transition-colors duration-200',
      // Cursor
      'cursor-pointer',
      className
    )}
    {...props}
  >
    <CheckboxPrimitive.Indicator className={cn('flex items-center justify-center text-current')}>
      {props.checked === 'indeterminate' ? (
        <Minus className="h-4 w-4" />
      ) : (
        <Check className="h-4 w-4" />
      )}
    </CheckboxPrimitive.Indicator>
  </CheckboxPrimitive.Root>
));
Checkbox.displayName = CheckboxPrimitive.Root.displayName;

export { Checkbox };
