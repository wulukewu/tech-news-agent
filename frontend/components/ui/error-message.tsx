/**
 * Error Message Component
 *
 * A reusable error message component for displaying errors.
 */

'use client';

import * as React from 'react';
import { AlertCircle, AlertTriangle, Info, CheckCircle, X } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useI18n } from '@/contexts/I18nContext';

type ErrorType = 'error' | 'warning' | 'info' | 'success';

interface ErrorMessageProps {
  title?: string;
  message: string;
  type?: ErrorType;
  onRetry?: () => void;
  onDismiss?: () => void;
  retryText?: string;
  dismissText?: string;
  showIcon?: boolean;
  fullWidth?: boolean;
  className?: string;
}

export function ErrorMessage({
  title,
  message,
  type = 'error',
  onRetry,
  onDismiss,
  retryText,
  dismissText,
  showIcon = true,
  fullWidth = false,
  className,
}: ErrorMessageProps) {
  const { t } = useI18n();

  const typeConfig = {
    error: {
      icon: AlertCircle,
      title: t('ui.error'),
      className: 'border-destructive/50 text-destructive dark:border-destructive',
    },
    warning: {
      icon: AlertTriangle,
      title: t('ui.warning'),
      className: 'border-yellow-500/50 text-yellow-600 dark:border-yellow-500',
    },
    info: {
      icon: Info,
      title: t('ui.info'),
      className: 'border-blue-500/50 text-blue-600 dark:border-blue-500',
    },
    success: {
      icon: CheckCircle,
      title: t('ui.success'),
      className: 'border-green-500/50 text-green-600 dark:border-green-500',
    },
  };

  const config = typeConfig[type];
  const Icon = config.icon;
  const displayTitle = title || config.title;

  return (
    <Alert role="alert" className={cn(config.className, fullWidth && 'w-full', className)}>
      <div className="flex items-start gap-3">
        {showIcon && <Icon className="h-5 w-5 mt-0.5" />}
        <div className="flex-1 space-y-1">
          <AlertTitle>{displayTitle}</AlertTitle>
          <AlertDescription>{message}</AlertDescription>
        </div>
        {onDismiss && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onDismiss}
            aria-label={dismissText || t('buttons.close')}
            className="h-6 w-6 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>
      {onRetry && (
        <div className="mt-3">
          <Button variant="outline" size="sm" onClick={onRetry}>
            {retryText || t('ui.retry')}
          </Button>
        </div>
      )}
    </Alert>
  );
}

// Preset error components
export function NetworkError({ onRetry }: { onRetry?: () => void }) {
  const { t } = useI18n();
  return (
    <ErrorMessage
      title={t('errors.network-connection')}
      message={t('errors.check-connection')}
      type="error"
      onRetry={onRetry}
    />
  );
}

export function NotFoundError({ message }: { message?: string }) {
  const { t } = useI18n();
  return (
    <ErrorMessage
      title={t('errors.resource-not-found')}
      message={message || t('errors.resource-not-found-desc')}
      type="error"
    />
  );
}

export function PermissionError() {
  const { t } = useI18n();
  return (
    <ErrorMessage
      title={t('errors.permission-denied')}
      message={t('errors.permission-denied-desc')}
      type="error"
    />
  );
}

export function ValidationError({ message }: { message?: string }) {
  const { t } = useI18n();
  return (
    <ErrorMessage
      title={t('errors.validation-error')}
      message={message || t('errors.validation-error-desc')}
      type="warning"
    />
  );
}

export function SuccessMessage({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss?: () => void;
}) {
  return <ErrorMessage message={message} type="success" onDismiss={onDismiss} />;
}

// Error Boundary Component
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; retry: () => void }>;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.props.onError?.(error, errorInfo);
  }

  retry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return <FallbackComponent error={this.state.error} retry={this.retry} />;
      }

      return (
        <div className="flex items-center justify-center min-h-[400px] p-4">
          <ErrorBoundaryErrorMessage error={this.state.error} onRetry={this.retry} />
        </div>
      );
    }

    return this.props.children;
  }
}

// Separate component to use hooks inside class component
function ErrorBoundaryErrorMessage({ error, onRetry }: { error: Error; onRetry: () => void }) {
  const { t } = useI18n();

  return (
    <ErrorMessage
      title={t('errors.app-error')}
      message={t('errors.app-error-desc', { message: error.message })}
      type="error"
      onRetry={onRetry}
    />
  );
}
