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

const typeConfig = {
  error: {
    icon: AlertCircle,
    title: '發生錯誤',
    className: 'border-destructive/50 text-destructive dark:border-destructive',
  },
  warning: {
    icon: AlertTriangle,
    title: '警告',
    className: 'border-yellow-500/50 text-yellow-600 dark:border-yellow-500',
  },
  info: {
    icon: Info,
    title: '資訊',
    className: 'border-blue-500/50 text-blue-600 dark:border-blue-500',
  },
  success: {
    icon: CheckCircle,
    title: '成功',
    className: 'border-green-500/50 text-green-600 dark:border-green-500',
  },
};

export function ErrorMessage({
  title,
  message,
  type = 'error',
  onRetry,
  onDismiss,
  retryText = '重試',
  dismissText = '關閉',
  showIcon = true,
  fullWidth = false,
  className,
}: ErrorMessageProps) {
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
            aria-label={dismissText}
            className="h-6 w-6 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>
      {onRetry && (
        <div className="mt-3">
          <Button variant="outline" size="sm" onClick={onRetry}>
            {retryText}
          </Button>
        </div>
      )}
    </Alert>
  );
}

// Preset error components
export function NetworkError({ onRetry }: { onRetry?: () => void }) {
  return (
    <ErrorMessage
      title="網路連線異常"
      message="請檢查您的網路連線，然後重試。"
      type="error"
      onRetry={onRetry}
    />
  );
}

export function NotFoundError({ message }: { message?: string }) {
  return <ErrorMessage title="找不到資源" message={message || '找不到請求的資源'} type="error" />;
}

export function PermissionError() {
  return (
    <ErrorMessage title="權限不足" message="您沒有執行此操作的權限，請聯繫管理員。" type="error" />
  );
}

export function ValidationError({ message }: { message?: string }) {
  return (
    <ErrorMessage
      title="驗證錯誤"
      message={message || '輸入的資料格式不正確，請檢查後重試。'}
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
          <ErrorMessage
            title="應用程式發生錯誤"
            message={`很抱歉，應用程式遇到了未預期的錯誤。錯誤訊息：${this.state.error.message}`}
            type="error"
            onRetry={this.retry}
          />
        </div>
      );
    }

    return this.props.children;
  }
}
