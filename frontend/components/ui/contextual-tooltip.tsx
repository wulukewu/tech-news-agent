'use client';

import * as React from 'react';
import { HelpCircle, Info, AlertCircle, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useI18n } from '@/contexts/I18nContext';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface ContextualTooltipProps {
  /** Tooltip content */
  content: React.ReactNode;
  /** Tooltip type for styling */
  type?: 'info' | 'help' | 'warning' | 'success';
  /** Trigger element */
  children?: React.ReactNode;
  /** Show default icon if no children provided */
  showIcon?: boolean;
  /** Custom icon */
  icon?: React.ReactNode;
  /** Tooltip position */
  side?: 'top' | 'right' | 'bottom' | 'left';
  /** Tooltip alignment */
  align?: 'start' | 'center' | 'end';
  /** Delay before showing tooltip (ms) */
  delayDuration?: number;
  /** Custom CSS classes */
  className?: string;
  /** Disable the tooltip */
  disabled?: boolean;
  /** Maximum width of tooltip content */
  maxWidth?: string;
}

/**
 * ContextualTooltip - Enhanced tooltip with contextual help and styling
 *
 * Features for Task 12.3:
 * - Multiple tooltip types with appropriate icons and colors
 * - Smooth animations and transitions
 * - Keyboard navigation support (Esc to close)
 * - Touch-friendly for mobile devices
 * - Respects prefers-reduced-motion
 * - ARIA labels for accessibility
 * - Auto-positioning to stay within viewport
 *
 * Requirements:
 * - 7.8: Contextual tooltips and help text
 * - 7.9: Smooth animations and transitions (respecting prefers-reduced-motion)
 * - 7.10: Mobile device touch support
 */
export function ContextualTooltip({
  content,
  type = 'info',
  children,
  showIcon = true,
  icon,
  side = 'top',
  align = 'center',
  delayDuration = 300,
  className,
  disabled = false,
  maxWidth = '300px',
}: ContextualTooltipProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [isTouchDevice, setIsTouchDevice] = React.useState(false);
  const { t } = useI18n();

  // Detect touch device
  React.useEffect(() => {
    setIsTouchDevice('ontouchstart' in window || navigator.maxTouchPoints > 0);
  }, []);

  // Handle keyboard events
  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen]);

  const getIcon = () => {
    if (icon) return icon;
    if (!showIcon) return null;

    const iconProps = { className: 'h-4 w-4' };

    switch (type) {
      case 'help':
        return <HelpCircle {...iconProps} />;
      case 'warning':
        return <AlertCircle {...iconProps} />;
      case 'success':
        return <CheckCircle {...iconProps} />;
      case 'info':
      default:
        return <Info {...iconProps} />;
    }
  };

  const getTypeStyles = () => {
    switch (type) {
      case 'help':
        return 'text-blue-600 hover:text-blue-700 dark:text-blue-400';
      case 'warning':
        return 'text-amber-600 hover:text-amber-700 dark:text-amber-400';
      case 'success':
        return 'text-green-600 hover:text-green-700 dark:text-green-400';
      case 'info':
      default:
        return 'text-muted-foreground hover:text-foreground';
    }
  };

  const getContentStyles = () => {
    const baseStyles = 'p-3 text-sm leading-relaxed';

    switch (type) {
      case 'help':
        return cn(
          baseStyles,
          'bg-blue-50 border-blue-200 text-blue-900 dark:bg-blue-950 dark:border-blue-800 dark:text-blue-100'
        );
      case 'warning':
        return cn(
          baseStyles,
          'bg-amber-50 border-amber-200 text-amber-900 dark:bg-amber-950 dark:border-amber-800 dark:text-amber-100'
        );
      case 'success':
        return cn(
          baseStyles,
          'bg-green-50 border-green-200 text-green-900 dark:bg-green-950 dark:border-green-800 dark:text-green-100'
        );
      case 'info':
      default:
        return cn(baseStyles, 'bg-popover border-border text-popover-foreground');
    }
  };

  if (disabled) {
    return <>{children}</>;
  }

  const trigger = children || (
    <button
      type="button"
      className={cn(
        'inline-flex items-center justify-center rounded-full p-1',
        'transition-all duration-200 ease-in-out',
        'motion-reduce:transition-none',
        'hover:bg-accent focus:bg-accent',
        'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
        getTypeStyles(),
        className
      )}
      aria-label={`${t('ui.show')}${
        type === 'help'
          ? t('ui.help')
          : type === 'warning'
            ? t('ui.warning')
            : type === 'success'
              ? t('ui.success')
              : t('ui.info')
      }${t('ui.tooltip')}`}
    >
      {getIcon()}
    </button>
  );

  return (
    <TooltipProvider delayDuration={delayDuration}>
      <Tooltip
        open={isOpen}
        onOpenChange={setIsOpen}
        // For touch devices, require tap to open
        {...(isTouchDevice && {
          onOpenChange: (open) => {
            setIsOpen(open);
            // Haptic feedback on mobile
            if (open && 'vibrate' in navigator) {
              navigator.vibrate(50);
            }
          },
        })}
      >
        <TooltipTrigger asChild>{trigger}</TooltipTrigger>
        <TooltipContent
          side={side}
          align={align}
          className={cn(
            'max-w-none border shadow-lg',
            'animate-in fade-in-0 zoom-in-95',
            'motion-reduce:animate-none',
            getContentStyles()
          )}
          style={{ maxWidth }}
          sideOffset={8}
        >
          <div className="space-y-2">{content}</div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/**
 * HelpText - Simple help text with tooltip
 */
interface HelpTextProps {
  children: React.ReactNode;
  help: React.ReactNode;
  className?: string;
}

export function HelpText({ children, help, className }: HelpTextProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span>{children}</span>
      <ContextualTooltip content={help} type="help" />
    </div>
  );
}

/**
 * InfoBadge - Information badge with tooltip
 */
interface InfoBadgeProps {
  content: React.ReactNode;
  type?: 'info' | 'help' | 'warning' | 'success';
  className?: string;
}

export function InfoBadge({ content, type = 'info', className }: InfoBadgeProps) {
  const { t } = useI18n();

  const getBadgeStyles = () => {
    switch (type) {
      case 'help':
        return 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900 dark:text-blue-200';
      case 'warning':
        return 'bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900 dark:text-amber-200';
      case 'success':
        return 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900 dark:text-green-200';
      case 'info':
      default:
        return 'bg-muted text-muted-foreground border-border';
    }
  };

  return (
    <ContextualTooltip content={content} type={type}>
      <span
        className={cn(
          'inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border',
          'transition-all duration-200 hover:shadow-sm',
          'motion-reduce:transition-none',
          getBadgeStyles(),
          className
        )}
      >
        <ContextualTooltip content={content} type={type} showIcon={false}>
          {type === 'help' && <HelpCircle className="h-3 w-3" />}
          {type === 'warning' && <AlertCircle className="h-3 w-3" />}
          {type === 'success' && <CheckCircle className="h-3 w-3" />}
          {type === 'info' && <Info className="h-3 w-3" />}
        </ContextualTooltip>
        <span>
          {type === 'help' && t('ui.help')}
          {type === 'warning' && t('ui.notice')}
          {type === 'success' && t('ui.complete')}
          {type === 'info' && t('ui.info')}
        </span>
      </span>
    </ContextualTooltip>
  );
}
