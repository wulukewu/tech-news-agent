'use client';

import { useState, useEffect } from 'react';

interface UseResponsiveNavigationOptions {
  defaultCollapsed?: boolean;
  breakpoint?: number;
}

/**
 * Hook for managing responsive navigation state
 * Handles sidebar collapse/expand and mobile navigation
 */
export function useResponsiveNavigation({
  defaultCollapsed = false,
  breakpoint = 1024, // lg breakpoint
}: UseResponsiveNavigationOptions = {}) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  const [isMobile, setIsMobile] = useState(false);

  // Check if we're on mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < breakpoint);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, [breakpoint]);

  // Auto-collapse on mobile
  useEffect(() => {
    if (isMobile) {
      setIsCollapsed(true);
    }
  }, [isMobile]);

  const toggleCollapsed = () => {
    setIsCollapsed(!isCollapsed);
  };

  const collapse = () => {
    setIsCollapsed(true);
  };

  const expand = () => {
    setIsCollapsed(false);
  };

  return {
    isCollapsed,
    isMobile,
    toggleCollapsed,
    collapse,
    expand,
  };
}
