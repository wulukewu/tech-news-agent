'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

interface AnimatedContainerProps {
  /** Animation type */
  animation?: 'fade' | 'slide' | 'scale' | 'bounce' | 'spin';
  /** Animation direction for slide animations */
  direction?: 'up' | 'down' | 'left' | 'right';
  /** Animation duration in milliseconds */
  duration?: number;
  /** Animation delay in milliseconds */
  delay?: number;
  /** Animation easing function */
  easing?: 'ease' | 'ease-in' | 'ease-out' | 'ease-in-out' | 'linear';
  /** Whether animation is currently active */
  isActive?: boolean;
  /** Children to animate */
  children: React.ReactNode;
  /** Custom CSS classes */
  className?: string;
  /** Callback when animation completes */
  onAnimationComplete?: () => void;
}

/**
 * AnimatedContainer - Smooth animations with prefers-reduced-motion support
 *
 * Features for Task 12.3:
 * - Multiple animation types (fade, slide, scale, bounce, spin)
 * - Respects prefers-reduced-motion user preference
 * - Customizable duration, delay, and easing
 * - Smooth transitions with CSS transforms
 * - Callback support for animation completion
 * - Optimized for performance with transform and opacity
 *
 * Requirements:
 * - 7.9: Smooth animations and transitions (respecting prefers-reduced-motion)
 */
export function AnimatedContainer({
  animation = 'fade',
  direction = 'up',
  duration = 300,
  delay = 0,
  easing = 'ease-out',
  isActive = true,
  children,
  className,
  onAnimationComplete,
}: AnimatedContainerProps) {
  const [hasAnimated, setHasAnimated] = React.useState(false);

  // Handle animation completion
  const handleAnimationEnd = React.useCallback(() => {
    setHasAnimated(true);
    onAnimationComplete?.();
  }, [onAnimationComplete]);

  // Get animation classes based on type and state
  const getAnimationClasses = () => {
    const baseClasses = [
      'transition-all',
      'motion-reduce:transition-none',
      'motion-reduce:transform-none',
    ];

    // Duration and easing
    const timingClasses = [
      `duration-[${duration}ms]`,
      `delay-[${delay}ms]`,
      easing === 'ease' && 'ease',
      easing === 'ease-in' && 'ease-in',
      easing === 'ease-out' && 'ease-out',
      easing === 'ease-in-out' && 'ease-in-out',
      easing === 'linear' && 'linear',
    ].filter(Boolean);

    // Animation-specific classes
    let animationClasses: string[] = [];

    switch (animation) {
      case 'fade':
        animationClasses = [isActive ? 'opacity-100' : 'opacity-0'];
        break;

      case 'slide': {
        const slideTransforms = {
          up: isActive ? 'translate-y-0' : 'translate-y-4',
          down: isActive ? 'translate-y-0' : '-translate-y-4',
          left: isActive ? 'translate-x-0' : 'translate-x-4',
          right: isActive ? 'translate-x-0' : '-translate-x-4',
        };
        animationClasses = [isActive ? 'opacity-100' : 'opacity-0', slideTransforms[direction]];
        break;
      }

      case 'scale':
        animationClasses = [isActive ? 'opacity-100 scale-100' : 'opacity-0 scale-95'];
        break;

      case 'bounce':
        animationClasses = [
          isActive ? 'opacity-100 scale-100' : 'opacity-0 scale-110',
          isActive && hasAnimated ? 'animate-bounce motion-reduce:animate-none' : '',
        ].filter(Boolean);
        break;

      case 'spin':
        animationClasses = [isActive ? 'opacity-100 rotate-0' : 'opacity-0 rotate-180'];
        break;
    }

    return cn(...baseClasses, ...timingClasses, ...animationClasses);
  };

  return (
    <div
      className={cn(getAnimationClasses(), className)}
      onTransitionEnd={handleAnimationEnd}
      style={{
        transitionDuration: `${duration}ms`,
        transitionDelay: `${delay}ms`,
        transitionTimingFunction: easing,
      }}
    >
      {children}
    </div>
  );
}

/**
 * FadeIn - Simple fade-in animation component
 */
interface FadeInProps {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  className?: string;
}

export function FadeIn({ children, delay = 0, duration = 300, className }: FadeInProps) {
  const [isVisible, setIsVisible] = React.useState(false);

  React.useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <AnimatedContainer
      animation="fade"
      duration={duration}
      isActive={isVisible}
      className={className}
    >
      {children}
    </AnimatedContainer>
  );
}

/**
 * SlideIn - Slide-in animation component
 */
interface SlideInProps {
  children: React.ReactNode;
  direction?: 'up' | 'down' | 'left' | 'right';
  delay?: number;
  duration?: number;
  className?: string;
}

export function SlideIn({
  children,
  direction = 'up',
  delay = 0,
  duration = 300,
  className,
}: SlideInProps) {
  const [isVisible, setIsVisible] = React.useState(false);

  React.useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <AnimatedContainer
      animation="slide"
      direction={direction}
      duration={duration}
      isActive={isVisible}
      className={className}
    >
      {children}
    </AnimatedContainer>
  );
}

/**
 * ScaleIn - Scale-in animation component
 */
interface ScaleInProps {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  className?: string;
}

export function ScaleIn({ children, delay = 0, duration = 300, className }: ScaleInProps) {
  const [isVisible, setIsVisible] = React.useState(false);

  React.useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <AnimatedContainer
      animation="scale"
      duration={duration}
      isActive={isVisible}
      className={className}
    >
      {children}
    </AnimatedContainer>
  );
}

/**
 * StaggeredList - Animate list items with staggered delays
 */
interface StaggeredListProps {
  children: React.ReactNode;
  staggerDelay?: number;
  animation?: 'fade' | 'slide' | 'scale';
  direction?: 'up' | 'down' | 'left' | 'right';
  className?: string;
}

export function StaggeredList({
  children,
  staggerDelay = 100,
  animation = 'slide',
  direction = 'up',
  className,
}: StaggeredListProps) {
  return (
    <div className={className}>
      {React.Children.map(children, (child, index) => (
        <AnimatedContainer
          key={index}
          animation={animation}
          direction={direction}
          delay={index * staggerDelay}
          isActive={true}
        >
          {child}
        </AnimatedContainer>
      ))}
    </div>
  );
}

/**
 * PulseLoader - Pulsing loading animation
 */
interface PulseLoaderProps {
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'secondary' | 'muted';
  className?: string;
}

export function PulseLoader({ size = 'md', color = 'primary', className }: PulseLoaderProps) {
  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4',
  };

  const colorClasses = {
    primary: 'bg-primary',
    secondary: 'bg-secondary',
    muted: 'bg-muted-foreground',
  };

  return (
    <div className={cn('flex items-center gap-1', className)}>
      {[0, 1, 2].map((index) => (
        <div
          key={index}
          className={cn(
            'rounded-full animate-pulse motion-reduce:animate-none',
            sizeClasses[size],
            colorClasses[color]
          )}
          style={{
            animationDelay: `${index * 200}ms`,
            animationDuration: '1s',
          }}
        />
      ))}
    </div>
  );
}

/**
 * ProgressiveBlur - Progressive blur effect for loading states
 */
interface ProgressiveBlurProps {
  children: React.ReactNode;
  isLoading?: boolean;
  className?: string;
}

export function ProgressiveBlur({ children, isLoading = false, className }: ProgressiveBlurProps) {
  return (
    <div
      className={cn(
        'transition-all duration-500 ease-in-out',
        'motion-reduce:transition-none motion-reduce:filter-none',
        isLoading ? 'blur-sm opacity-60' : 'blur-none opacity-100',
        className
      )}
    >
      {children}
    </div>
  );
}
