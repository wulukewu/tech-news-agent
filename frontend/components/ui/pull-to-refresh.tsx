'use client';
import { logger } from '@/lib/utils/logger';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PullToRefreshProps {
  children: React.ReactNode;
  onRefresh: () => Promise<void> | void;
  threshold?: number;
  disabled?: boolean;
  className?: string;
}

/**
 * Pull-to-refresh component for mobile devices
 * Provides native-like pull-to-refresh functionality
 */
export function PullToRefresh({
  children,
  onRefresh,
  threshold = 80,
  disabled = false,
  className,
}: PullToRefreshProps) {
  const [pullDistance, setPullDistance] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [canPull, setCanPull] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const startY = useRef<number>(0);
  const currentY = useRef<number>(0);

  const handleTouchStart = useCallback(
    (e: TouchEvent) => {
      if (disabled || isRefreshing) return;

      const container = containerRef.current;
      if (!container) return;

      // Only allow pull-to-refresh when at the top of the container
      const isAtTop = container.scrollTop === 0;
      setCanPull(isAtTop);

      if (isAtTop) {
        startY.current = e.touches[0].clientY;
        currentY.current = startY.current;
      }
    },
    [disabled, isRefreshing]
  );

  const handleTouchMove = useCallback(
    (e: TouchEvent) => {
      if (disabled || isRefreshing || !canPull) return;

      currentY.current = e.touches[0].clientY;
      const distance = currentY.current - startY.current;

      if (distance > 0) {
        // Apply resistance to the pull distance
        const resistance = Math.min(distance / 2.5, threshold * 1.5);
        setPullDistance(resistance);

        // Prevent default scrolling when pulling
        if (distance > 10) {
          e.preventDefault();
        }
      }
    },
    [disabled, isRefreshing, canPull, threshold]
  );

  const handleTouchEnd = useCallback(async () => {
    if (disabled || isRefreshing || !canPull) return;

    if (pullDistance >= threshold) {
      setIsRefreshing(true);
      try {
        await onRefresh();
      } catch (error) {
        console.error('Refresh failed:', error);
      } finally {
        setIsRefreshing(false);
      }
    }

    setPullDistance(0);
    setCanPull(false);
    startY.current = 0;
    currentY.current = 0;
  }, [disabled, isRefreshing, canPull, pullDistance, threshold, onRefresh]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener('touchstart', handleTouchStart, { passive: false });
    container.addEventListener('touchmove', handleTouchMove, { passive: false });
    container.addEventListener('touchend', handleTouchEnd, { passive: true });

    return () => {
      container.removeEventListener('touchstart', handleTouchStart);
      container.removeEventListener('touchmove', handleTouchMove);
      container.removeEventListener('touchend', handleTouchEnd);
    };
  }, [handleTouchStart, handleTouchMove, handleTouchEnd]);

  const refreshIndicatorOpacity = Math.min(pullDistance / threshold, 1);
  const refreshIndicatorScale = Math.min(pullDistance / threshold, 1);
  const shouldShowRefreshing = isRefreshing || pullDistance >= threshold;

  return (
    <div
      ref={containerRef}
      className={cn('relative overflow-auto', className)}
      style={{
        transform: `translateY(${Math.min(pullDistance * 0.5, 40)}px)`,
        transition: pullDistance === 0 ? 'transform 0.3s ease-out' : 'none',
      }}
    >
      {/* Refresh indicator */}
      <div
        className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-full flex items-center justify-center w-12 h-12 bg-background border rounded-full shadow-lg z-10"
        style={{
          opacity: refreshIndicatorOpacity,
          transform: `translateX(-50%) translateY(-100%) scale(${refreshIndicatorScale})`,
          transition: pullDistance === 0 ? 'all 0.3s ease-out' : 'none',
        }}
      >
        <RefreshCw
          className={cn(
            'h-5 w-5 text-muted-foreground',
            shouldShowRefreshing && 'animate-spin text-primary'
          )}
        />
      </div>

      {/* Content */}
      {children}
    </div>
  );
}
