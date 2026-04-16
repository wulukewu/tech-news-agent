'use client';

import * as React from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface CollapsibleSectionProps {
  /** Section title */
  title: React.ReactNode;
  /** Section content */
  children: React.ReactNode;
  /** Initially expanded state */
  defaultExpanded?: boolean;
  /** Controlled expanded state */
  expanded?: boolean;
  /** Callback when expanded state changes */
  onExpandedChange?: (expanded: boolean) => void;
  /** Custom CSS classes */
  className?: string;
  /** Custom CSS classes for header */
  headerClassName?: string;
  /** Custom CSS classes for content */
  contentClassName?: string;
  /** Disable the collapsible functionality */
  disabled?: boolean;
  /** Show expand/collapse animation */
  animated?: boolean;
  /** Icon position */
  iconPosition?: 'left' | 'right';
  /** Custom expand/collapse icons */
  expandIcon?: React.ReactNode;
  collapseIcon?: React.ReactNode;
}

/**
 * CollapsibleSection - Expandable/collapsible content section
 *
 * Features for Task 12.2:
 * - Smooth expand/collapse animations
 * - Keyboard navigation support (Enter/Space to toggle)
 * - Customizable icons and styling
 * - Controlled and uncontrolled modes
 * - ARIA attributes for accessibility
 * - Respects prefers-reduced-motion
 *
 * Requirements:
 * - 7.5: Expandable/collapsible information sections
 * - 7.7: Keyboard shortcuts and navigation support
 * - 7.9: Smooth animations and transitions (respecting prefers-reduced-motion)
 */
export function CollapsibleSection({
  title,
  children,
  defaultExpanded = false,
  expanded: controlledExpanded,
  onExpandedChange,
  className,
  headerClassName,
  contentClassName,
  disabled = false,
  animated = true,
  iconPosition = 'left',
  expandIcon,
  collapseIcon,
}: CollapsibleSectionProps) {
  const [internalExpanded, setInternalExpanded] = React.useState(defaultExpanded);
  const contentRef = React.useRef<HTMLDivElement>(null);
  const [contentHeight, setContentHeight] = React.useState<number | undefined>(undefined);

  // Use controlled or uncontrolled state
  const isExpanded = controlledExpanded !== undefined ? controlledExpanded : internalExpanded;

  const handleToggle = () => {
    if (disabled) return;

    const newExpanded = !isExpanded;

    if (controlledExpanded === undefined) {
      setInternalExpanded(newExpanded);
    }

    onExpandedChange?.(newExpanded);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleToggle();
    }
  };

  // Measure content height for smooth animations
  React.useEffect(() => {
    if (!animated || !contentRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContentHeight(entry.contentRect.height);
      }
    });

    resizeObserver.observe(contentRef.current);

    return () => {
      resizeObserver.disconnect();
    };
  }, [animated]);

  const getIcon = () => {
    if (expandIcon && collapseIcon) {
      return isExpanded ? collapseIcon : expandIcon;
    }

    return isExpanded ? (
      <ChevronDown className="h-4 w-4 transition-transform duration-200 motion-reduce:transition-none" />
    ) : (
      <ChevronRight className="h-4 w-4 transition-transform duration-200 motion-reduce:transition-none" />
    );
  };

  return (
    <div className={cn('border border-border rounded-lg overflow-hidden', className)}>
      {/* Header */}
      <Button
        variant="ghost"
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        className={cn(
          'w-full h-auto p-4 justify-between text-left font-medium',
          'hover:bg-accent/50 focus:bg-accent',
          'transition-all duration-200 ease-in-out',
          'motion-reduce:transition-none',
          'rounded-none border-0',
          disabled && 'opacity-50 cursor-not-allowed',
          headerClassName
        )}
        aria-expanded={isExpanded}
        aria-controls="collapsible-content"
      >
        <div
          className={cn(
            'flex items-center gap-3 w-full',
            iconPosition === 'right' && 'flex-row-reverse'
          )}
        >
          {iconPosition === 'left' && (
            <div
              className={cn(
                'transition-transform duration-200 ease-in-out',
                'motion-reduce:transition-none',
                isExpanded && 'rotate-0',
                !isExpanded && 'rotate-0'
              )}
            >
              {getIcon()}
            </div>
          )}

          <div className="flex-1 min-w-0">{title}</div>

          {iconPosition === 'right' && (
            <div
              className={cn(
                'transition-transform duration-200 ease-in-out',
                'motion-reduce:transition-none'
              )}
            >
              {getIcon()}
            </div>
          )}
        </div>
      </Button>

      {/* Content */}
      <div
        id="collapsible-content"
        className={cn(
          'overflow-hidden transition-all duration-300 ease-in-out',
          'motion-reduce:transition-none',
          !animated && 'transition-none'
        )}
        style={{
          height: animated ? (isExpanded ? contentHeight : 0) : isExpanded ? 'auto' : 0,
        }}
      >
        <div
          ref={contentRef}
          className={cn('p-4 pt-0 border-t border-border/50', contentClassName)}
        >
          {children}
        </div>
      </div>
    </div>
  );
}

/**
 * CollapsibleGroup - Container for multiple collapsible sections
 * Supports accordion-style behavior (only one open at a time)
 */
interface CollapsibleGroupProps {
  children: React.ReactNode;
  /** Allow multiple sections to be open simultaneously */
  allowMultiple?: boolean;
  /** Default expanded section index (for accordion mode) */
  defaultExpanded?: number;
  /** Custom CSS classes */
  className?: string;
  /** Spacing between sections */
  spacing?: 'none' | 'sm' | 'md' | 'lg';
}

export function CollapsibleGroup({
  children,
  allowMultiple = true,
  defaultExpanded,
  className,
  spacing = 'md',
}: CollapsibleGroupProps) {
  const [expandedIndex, setExpandedIndex] = React.useState<number | null>(
    defaultExpanded !== undefined ? defaultExpanded : null
  );

  const spacingClasses = {
    none: 'space-y-0',
    sm: 'space-y-2',
    md: 'space-y-4',
    lg: 'space-y-6',
  };

  const handleSectionToggle = (index: number, expanded: boolean) => {
    if (allowMultiple) return; // Let individual sections handle their own state

    if (expanded) {
      setExpandedIndex(index);
    } else if (expandedIndex === index) {
      setExpandedIndex(null);
    }
  };

  return (
    <div className={cn(spacingClasses[spacing], className)}>
      {React.Children.map(children, (child, index) => {
        if (!React.isValidElement(child)) return child;

        if (!allowMultiple) {
          return React.cloneElement(child, {
            expanded: expandedIndex === index,
            onExpandedChange: (expanded: boolean) => {
              handleSectionToggle(index, expanded);
              child.props.onExpandedChange?.(expanded);
            },
          });
        }

        return child;
      })}
    </div>
  );
}
