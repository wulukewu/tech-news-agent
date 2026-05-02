/**
 * Refresh Button Component
 *
 * A standardized refresh button with consistent animation behavior.
 */

import { RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface RefreshButtonProps {
  /** Whether the refresh is in progress */
  isLoading: boolean;
  /** Click handler */
  onClick: () => void;
  /** Button text */
  children?: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
  /** Button variant */
  variant?: 'default' | 'outline' | 'ghost' | 'secondary';
  /** Button size */
  size?: 'default' | 'sm' | 'lg' | 'icon';
  /** Whether the button is disabled */
  disabled?: boolean;
}

export function RefreshButton({
  isLoading,
  onClick,
  children,
  className,
  variant = 'outline',
  size = 'sm',
  disabled = false,
}: RefreshButtonProps) {
  return (
    <Button
      variant={variant}
      size={size}
      onClick={onClick}
      disabled={disabled || isLoading}
      className={cn(
        'transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]',
        className
      )}
      data-refresh-button="v2" // Version marker for debugging
    >
      <RefreshCw
        className={cn(
          'h-4 w-4',
          children && 'mr-2',
          'transition-transform duration-200',
          isLoading && '[animation:spin-slow_2s_linear_infinite]'
        )}
      />
      {children}
    </Button>
  );
}
