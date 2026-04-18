'use client';

import React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const touchButtonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 touch-target select-none',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90 active:bg-primary/80',
        destructive:
          'bg-destructive text-destructive-foreground hover:bg-destructive/90 active:bg-destructive/80',
        outline:
          'border border-input bg-background hover:bg-accent hover:text-accent-foreground active:bg-accent/80',
        secondary:
          'bg-secondary text-secondary-foreground hover:bg-secondary/80 active:bg-secondary/70',
        ghost: 'hover:bg-accent hover:text-accent-foreground active:bg-accent/80',
        link: 'text-primary underline-offset-4 hover:underline active:text-primary/80',
      },
      size: {
        default: 'h-12 px-6 py-3', // Increased from h-10 for better touch targets
        sm: 'h-10 rounded-md px-4 text-xs', // Minimum 40px height
        lg: 'h-14 rounded-md px-8 text-base', // Larger for primary actions
        icon: 'h-12 w-12', // Square touch target
        'icon-sm': 'h-10 w-10', // Smaller icon button
        'icon-lg': 'h-14 w-14', // Larger icon button
      },
      touchFeedback: {
        none: '',
        subtle: 'active:scale-[0.98] transition-transform',
        strong: 'active:scale-95 transition-transform',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
      touchFeedback: 'subtle',
    },
  }
);

export interface TouchButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof touchButtonVariants> {
  asChild?: boolean;
  hapticFeedback?: boolean;
}

/**
 * Touch-optimized button component with proper touch targets and feedback
 * Ensures minimum 44px touch targets and provides haptic feedback on supported devices
 */
const TouchButton = React.forwardRef<HTMLButtonElement, TouchButtonProps>(
  (
    {
      className,
      variant,
      size,
      touchFeedback,
      asChild = false,
      hapticFeedback = true,
      onClick,
      ...props
    },
    ref
  ) => {
    const Comp = asChild ? Slot : 'button';

    const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
      // Provide haptic feedback on supported devices
      if (hapticFeedback && 'vibrate' in navigator) {
        navigator.vibrate(10); // Short vibration
      }

      onClick?.(event);
    };

    return (
      <Comp
        className={cn(touchButtonVariants({ variant, size, touchFeedback, className }))}
        ref={ref}
        onClick={handleClick}
        {...props}
      />
    );
  }
);
TouchButton.displayName = 'TouchButton';

export { TouchButton, touchButtonVariants };
