'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Input } from './input';
import { Label } from './label';
import { CharacterCount } from './character-count';

export interface FormInputProps extends React.ComponentProps<'input'> {
  /**
   * Label text displayed above the input
   */
  label?: string;
  /**
   * Helper text displayed below the input
   */
  helperText?: string;
  /**
   * Error message displayed below the input with destructive color
   */
  error?: string;
  /**
   * Whether the input is in an error state
   */
  hasError?: boolean;
  /**
   * ID for the input element (required for accessibility)
   */
  id: string;
  /**
   * Container className for the wrapper div
   */
  containerClassName?: string;
  /**
   * Whether to show character count (requires maxLength prop)
   */
  showCharacterCount?: boolean;
}

/**
 * Enhanced Input component with label, helper text, error state, and character count support
 *
 * Requirements Coverage:
 * - 11.1: Label with 8px spacing above input
 * - 11.2: Placeholder with muted color
 * - 11.3: Error state with destructive color
 * - 11.4: Character count for text inputs with maximum length constraints
 * - 11.5: Full-width on mobile, auto-width on desktop
 * - 11.6: 48px minimum height on mobile
 * - 11.7: Visible focus ring (2px, primary color)
 * - 11.8: Disabled state (50% opacity, not-allowed cursor)
 */
// eslint-disable-next-line complexity
const FormInput = React.forwardRef<HTMLInputElement, FormInputProps>(
  (
    {
      label,
      helperText,
      error,
      hasError,
      id,
      className,
      containerClassName,
      disabled,
      showCharacterCount = false,
      maxLength,
      value,
      defaultValue,
      ...props
    },
    ref
  ) => {
    const showError = hasError || !!error;
    const messageText = error || helperText;
    const messageId = error ? `${id}-error` : `${id}-helper`;
    const messageRole = error ? 'alert' : undefined;
    const messageClassName = error ? 'text-destructive' : 'text-muted-foreground';

    // Track character count for controlled and uncontrolled inputs
    const [internalValue, setInternalValue] = React.useState<string>(
      (value as string) || (defaultValue as string) || ''
    );

    // Use controlled value if provided, otherwise use internal state
    const currentValue = value !== undefined ? (value as string) : internalValue;
    const currentLength = currentValue?.length || 0;

    // Show character count only if explicitly enabled and maxLength is set
    const shouldShowCharacterCount = showCharacterCount && maxLength !== undefined;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      // Update internal state for uncontrolled inputs
      if (value === undefined) {
        setInternalValue(e.target.value);
      }
      // Call parent onChange if provided
      props.onChange?.(e);
    };

    return (
      <div className={cn('w-full md:w-auto', containerClassName)}>
        {/* Label with 8px spacing (Req 11.1) */}
        {label && (
          <Label
            htmlFor={id}
            className={cn(
              'mb-2', // 8px spacing
              showError && 'text-destructive',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
          >
            {label}
          </Label>
        )}

        {/* Input with enhanced styling (Req 11.2, 11.5, 11.6, 11.7, 11.8) */}
        <Input
          id={id}
          ref={ref}
          disabled={disabled}
          maxLength={maxLength}
          value={value}
          defaultValue={defaultValue}
          className={cn(
            // Full-width on mobile, auto-width on desktop (Req 11.5)
            'w-full md:w-auto',
            // Minimum 48px height on mobile (Req 11.6)
            'min-h-12 md:min-h-10',
            // Visible focus ring - 2px with primary color (Req 11.7)
            'focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
            // Error state with destructive color (Req 11.3)
            showError && 'border-destructive focus-visible:ring-destructive',
            // Disabled state - 50% opacity, not-allowed cursor (Req 11.8)
            disabled && 'opacity-50 cursor-not-allowed',
            // Placeholder with muted color (Req 11.2) - handled by base Input component
            className
          )}
          aria-invalid={showError}
          aria-describedby={messageText || shouldShowCharacterCount ? messageId : undefined}
          onChange={handleChange}
          {...props}
        />

        {/* Character count and helper text/error message container */}
        <div className="mt-2 flex items-center justify-between gap-2">
          {/* Helper text or error message below input (Req 11.3, 11.7) */}
          {messageText && (
            <p
              id={messageId}
              className={cn('text-sm', messageClassName, disabled && 'opacity-50')}
              role={messageRole}
            >
              {messageText}
            </p>
          )}

          {/* Character count (Req 11.4) */}
          {shouldShowCharacterCount && (
            <CharacterCount
              current={currentLength}
              max={maxLength}
              showLabel={false}
              className={cn('ml-auto', disabled && 'opacity-50')}
            />
          )}
        </div>
      </div>
    );
  }
);

FormInput.displayName = 'FormInput';

export { FormInput };
