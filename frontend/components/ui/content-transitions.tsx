/**
 * Smooth Content Transitions
 *
 * Provides smooth fade-in transitions when content loads,
 * with respect for prefers-reduced-motion preference.
 *
 * Requirements: 12.7, 12.8, 21.5
 */

'use client';

import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';

interface ContentTransitionProps {
  children: React.ReactNode;
  isLoading: boolean;
  duration?: number;
  className?: string;
  fallback?: React.ReactNode;
}

/**
 * Fade In Content Transition
 * Fades in content when loaded with 200ms duration
 * Respects prefers-reduced-motion preference
 * Requirements: 12.7, 12.8
 */
export function FadeInContent({
  children,
  isLoading,
  duration = 200,
  className,
  fallback,
}: ContentTransitionProps) {
  const [shouldShow, setShouldShow] = useState(!isLoading);
  const [isVisible, setIsVisible] = useState(!isLoading);

  useEffect(() => {
    if (!isLoading && !shouldShow) {
      // Content has finished loading, start showing it
      setShouldShow(true);
      // Small delay to ensure smooth transition
      const timer = setTimeout(() => {
        setIsVisible(true);
      }, 10);
      return () => clearTimeout(timer);
    } else if (isLoading) {
      // Content is loading, hide it
      setIsVisible(false);
      setShouldShow(false);
    }
  }, [isLoading, shouldShow]);

  if (isLoading) {
    return <>{fallback}</>;
  }

  return (
    <div
      className={cn(
        'transition-opacity ease-out',
        isVisible ? 'opacity-100' : 'opacity-0',
        // Respect prefers-reduced-motion
        'motion-reduce:transition-none motion-reduce:opacity-100',
        className
      )}
      style={{
        transitionDuration: `${duration}ms`,
      }}
    >
      {shouldShow && children}
    </div>
  );
}

/**
 * Slide Up Content Transition
 * Slides content up from bottom when loaded
 * Requirements: 12.7, 12.8
 */
export function SlideUpContent({
  children,
  isLoading,
  duration = 300,
  className,
  fallback,
}: ContentTransitionProps) {
  const [shouldShow, setShouldShow] = useState(!isLoading);
  const [isVisible, setIsVisible] = useState(!isLoading);

  useEffect(() => {
    if (!isLoading && !shouldShow) {
      setShouldShow(true);
      const timer = setTimeout(() => {
        setIsVisible(true);
      }, 10);
      return () => clearTimeout(timer);
    } else if (isLoading) {
      setIsVisible(false);
      setShouldShow(false);
    }
  }, [isLoading, shouldShow]);

  if (isLoading) {
    return <>{fallback}</>;
  }

  return (
    <div
      className={cn(
        'transition-all ease-out',
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4',
        // Respect prefers-reduced-motion
        'motion-reduce:transition-none motion-reduce:opacity-100 motion-reduce:translate-y-0',
        className
      )}
      style={{
        transitionDuration: `${duration}ms`,
      }}
    >
      {shouldShow && children}
    </div>
  );
}

/**
 * Scale In Content Transition
 * Scales content in when loaded
 * Requirements: 12.7, 12.8
 */
export function ScaleInContent({
  children,
  isLoading,
  duration = 200,
  className,
  fallback,
}: ContentTransitionProps) {
  const [shouldShow, setShouldShow] = useState(!isLoading);
  const [isVisible, setIsVisible] = useState(!isLoading);

  useEffect(() => {
    if (!isLoading && !shouldShow) {
      setShouldShow(true);
      const timer = setTimeout(() => {
        setIsVisible(true);
      }, 10);
      return () => clearTimeout(timer);
    } else if (isLoading) {
      setIsVisible(false);
      setShouldShow(false);
    }
  }, [isLoading, shouldShow]);

  if (isLoading) {
    return <>{fallback}</>;
  }

  return (
    <div
      className={cn(
        'transition-all ease-out',
        isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-95',
        // Respect prefers-reduced-motion
        'motion-reduce:transition-none motion-reduce:opacity-100 motion-reduce:scale-100',
        className
      )}
      style={{
        transitionDuration: `${duration}ms`,
      }}
    >
      {shouldShow && children}
    </div>
  );
}

/**
 * Staggered List Transition
 * Animates list items with staggered delays
 * Requirements: 12.7, 12.8
 */
export function StaggeredListTransition({
  children,
  isLoading,
  staggerDelay = 50,
  className,
  fallback,
}: ContentTransitionProps & {
  staggerDelay?: number;
}) {
  const [shouldShow, setShouldShow] = useState(!isLoading);

  useEffect(() => {
    if (!isLoading) {
      setShouldShow(true);
    } else {
      setShouldShow(false);
    }
  }, [isLoading]);

  if (isLoading) {
    return <>{fallback}</>;
  }

  return (
    <div className={className}>
      {shouldShow && Array.isArray(children)
        ? children.map((child, index) => (
            <div
              key={index}
              className={cn(
                'transition-all duration-300 ease-out',
                shouldShow ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4',
                // Respect prefers-reduced-motion
                'motion-reduce:transition-none motion-reduce:opacity-100 motion-reduce:translate-y-0'
              )}
              style={{
                transitionDelay: `${index * staggerDelay}ms`,
              }}
            >
              {child}
            </div>
          ))
        : children}
    </div>
  );
}

/**
 * Content Transition Wrapper
 * Generic wrapper that applies the appropriate transition
 * Requirements: 12.7, 12.8
 */
export function ContentTransition({
  children,
  isLoading,
  type = 'fade',
  duration = 200,
  className,
  fallback,
}: ContentTransitionProps & {
  type?: 'fade' | 'slide-up' | 'scale' | 'staggered';
}) {
  const commonProps = {
    children,
    isLoading,
    duration,
    className,
    fallback,
  };

  switch (type) {
    case 'slide-up':
      return <SlideUpContent {...commonProps} />;
    case 'scale':
      return <ScaleInContent {...commonProps} />;
    case 'staggered':
      return <StaggeredListTransition {...commonProps} />;
    case 'fade':
    default:
      return <FadeInContent {...commonProps} />;
  }
}

/**
 * Article Grid Transition
 * Specialized transition for article grids
 * Requirements: 12.7, 12.8
 */
export function ArticleGridTransition({
  children,
  isLoading,
  fallback,
  className,
}: {
  children: React.ReactNode;
  isLoading: boolean;
  fallback?: React.ReactNode;
  className?: string;
}) {
  return (
    <ContentTransition
      type="staggered"
      isLoading={isLoading}
      duration={200}
      fallback={fallback}
      className={className}
    >
      {children}
    </ContentTransition>
  );
}

/**
 * Page Content Transition
 * Specialized transition for page-level content
 * Requirements: 12.7, 12.8
 */
export function PageContentTransition({
  children,
  isLoading,
  fallback,
  className,
}: {
  children: React.ReactNode;
  isLoading: boolean;
  fallback?: React.ReactNode;
  className?: string;
}) {
  return (
    <ContentTransition
      type="fade"
      isLoading={isLoading}
      duration={200}
      fallback={fallback}
      className={className}
    >
      {children}
    </ContentTransition>
  );
}

/**
 * Card Content Transition
 * Specialized transition for individual cards
 * Requirements: 12.7, 12.8
 */
export function CardContentTransition({
  children,
  isLoading,
  fallback,
  className,
}: {
  children: React.ReactNode;
  isLoading: boolean;
  fallback?: React.ReactNode;
  className?: string;
}) {
  return (
    <ContentTransition
      type="scale"
      isLoading={isLoading}
      duration={150}
      fallback={fallback}
      className={className}
    >
      {children}
    </ContentTransition>
  );
}
