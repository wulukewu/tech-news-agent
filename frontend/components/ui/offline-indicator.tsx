'use client';

import React from 'react';
import { WifiOff, Wifi, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { usePWA } from '@/hooks/usePWA';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface OfflineIndicatorProps {
  className?: string;
  showWhenOnline?: boolean;
  variant?: 'banner' | 'badge' | 'toast';
}

/**
 * Offline indicator component
 * Shows connection status and provides offline functionality information
 */
export function OfflineIndicator({
  className,
  showWhenOnline = false,
  variant = 'banner',
}: OfflineIndicatorProps) {
  const { isOffline } = usePWA();

  // Don't show when online unless explicitly requested
  if (!isOffline && !showWhenOnline) {
    return null;
  }

  const content = {
    icon: isOffline ? WifiOff : Wifi,
    title: isOffline ? "You're offline" : 'Back online',
    description: isOffline
      ? 'Some features may be limited. Previously viewed content is still available.'
      : 'All features are now available.',
    className: isOffline
      ? 'bg-destructive/10 border-destructive/20 text-destructive-foreground'
      : 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-800 dark:text-green-300',
  };

  const Icon = content.icon;

  if (variant === 'badge') {
    return (
      <div
        className={cn(
          'inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium',
          content.className,
          className
        )}
      >
        <Icon className="h-3 w-3" />
        <span>{isOffline ? 'Offline' : 'Online'}</span>
      </div>
    );
  }

  if (variant === 'toast') {
    return (
      <div
        className={cn(
          'fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg backdrop-blur-sm',
          content.className,
          'animate-in slide-in-from-top-2 duration-300',
          className
        )}
      >
        <Icon className="h-4 w-4" />
        <div>
          <p className="font-medium text-sm">{content.title}</p>
          <p className="text-xs opacity-90">{content.description}</p>
        </div>
      </div>
    );
  }

  // Banner variant (default)
  return (
    <Alert className={cn(content.className, className)}>
      <Icon className="h-4 w-4" />
      <AlertDescription className="flex items-center justify-between">
        <div>
          <span className="font-medium">{content.title}</span>
          <span className="ml-2">{content.description}</span>
        </div>
        {isOffline && (
          <button
            onClick={() => window.location.reload()}
            className="text-xs underline hover:no-underline ml-4 whitespace-nowrap"
          >
            Try again
          </button>
        )}
      </AlertDescription>
    </Alert>
  );
}

/**
 * Connection status indicator for the navigation bar
 */
export function ConnectionStatus({ className }: { className?: string }) {
  const { isOffline } = usePWA();

  return (
    <div className={cn('flex items-center gap-2 text-sm', className)}>
      {isOffline ? (
        <>
          <WifiOff className="h-4 w-4 text-destructive" />
          <span className="text-muted-foreground">Offline</span>
        </>
      ) : (
        <>
          <Wifi className="h-4 w-4 text-green-500" />
          <span className="text-muted-foreground hidden sm:inline">Online</span>
        </>
      )}
    </div>
  );
}

/**
 * Offline fallback component for failed content
 */
export function OfflineFallback({
  title = 'Content unavailable offline',
  description = 'This content is not available while offline. Please check your connection and try again.',
  onRetry,
  className,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div className={cn('flex flex-col items-center justify-center p-8 text-center', className)}>
      <div className="mb-4 p-3 bg-muted rounded-full">
        <AlertCircle className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-muted-foreground mb-4 max-w-md">{description}</p>
      {onRetry && (
        <button onClick={onRetry} className="text-primary hover:underline font-medium">
          Try again
        </button>
      )}
    </div>
  );
}
