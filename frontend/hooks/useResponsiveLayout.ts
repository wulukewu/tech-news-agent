'use client';

import { useState, useEffect } from 'react';

export type ScreenSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
export type DeviceType = 'mobile' | 'tablet' | 'desktop';

interface ResponsiveLayoutState {
  screenSize: ScreenSize;
  deviceType: DeviceType;
  width: number;
  height: number;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isPortrait: boolean;
  isLandscape: boolean;
  isTouchDevice: boolean;
}

const breakpoints = {
  xs: 475,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
} as const;

/**
 * Hook for responsive layout management
 * Provides screen size detection, device type, and orientation information
 */
export function useResponsiveLayout(): ResponsiveLayoutState {
  const [state, setState] = useState<ResponsiveLayoutState>(() => {
    // Default values for SSR
    return {
      screenSize: 'lg' as ScreenSize,
      deviceType: 'desktop' as DeviceType,
      width: 1024,
      height: 768,
      isMobile: false,
      isTablet: false,
      isDesktop: true,
      isPortrait: false,
      isLandscape: true,
      isTouchDevice: false,
    };
  });

  useEffect(() => {
    const updateLayout = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      const isPortrait = height > width;
      const isLandscape = width > height;

      // Determine screen size
      let screenSize: ScreenSize = 'xs';
      if (width >= breakpoints['2xl']) screenSize = '2xl';
      else if (width >= breakpoints.xl) screenSize = 'xl';
      else if (width >= breakpoints.lg) screenSize = 'lg';
      else if (width >= breakpoints.md) screenSize = 'md';
      else if (width >= breakpoints.sm) screenSize = 'sm';
      else if (width >= breakpoints.xs) screenSize = 'xs';

      // Determine device type
      let deviceType: DeviceType = 'mobile';
      if (width >= breakpoints.lg) deviceType = 'desktop';
      else if (width >= breakpoints.md) deviceType = 'tablet';

      // Check for touch device
      const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

      setState({
        screenSize,
        deviceType,
        width,
        height,
        isMobile: deviceType === 'mobile',
        isTablet: deviceType === 'tablet',
        isDesktop: deviceType === 'desktop',
        isPortrait,
        isLandscape,
        isTouchDevice,
      });
    };

    // Initial update
    updateLayout();

    // Listen for resize events
    window.addEventListener('resize', updateLayout);
    window.addEventListener('orientationchange', updateLayout);

    return () => {
      window.removeEventListener('resize', updateLayout);
      window.removeEventListener('orientationchange', updateLayout);
    };
  }, []);

  return state;
}

/**
 * Hook for checking if current screen size matches given breakpoint
 */
export function useBreakpoint(breakpoint: ScreenSize): boolean {
  const { width } = useResponsiveLayout();
  return width >= breakpoints[breakpoint];
}

/**
 * Hook for getting responsive values based on screen size
 */
export function useResponsiveValue<T>(values: Partial<Record<ScreenSize, T>>, defaultValue: T): T {
  const { screenSize } = useResponsiveLayout();

  // Find the best matching value
  const sizes: ScreenSize[] = ['2xl', 'xl', 'lg', 'md', 'sm', 'xs'];
  const currentIndex = sizes.indexOf(screenSize);

  for (let i = currentIndex; i < sizes.length; i++) {
    const size = sizes[i];
    if (values[size] !== undefined) {
      return values[size]!;
    }
  }

  return defaultValue;
}

/**
 * Hook for responsive grid columns
 */
export function useResponsiveColumns(columns: Partial<Record<ScreenSize, number>> = {}): number {
  return useResponsiveValue(columns, 1);
}

/**
 * Hook for responsive spacing
 */
export function useResponsiveSpacing(spacing: Partial<Record<ScreenSize, string>> = {}): string {
  return useResponsiveValue(spacing, '1rem');
}
