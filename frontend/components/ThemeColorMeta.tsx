'use client';

import { useEffect } from 'react';
import { useTheme } from 'next-themes';

/**
 * ThemeColorMeta component
 * Dynamically updates the meta theme-color tag based on the current theme
 * Requirement 17.8: Update meta theme-color tag to match current theme
 */
export function ThemeColorMeta() {
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    // Define theme colors matching our design system
    const themeColors = {
      light: '#ffffff', // Light mode background
      dark: '#0f172a', // Dark mode background (slate-900)
    };

    // Get the appropriate color based on resolved theme
    const color = themeColors[resolvedTheme as keyof typeof themeColors] || themeColors.light;

    // Update or create the meta theme-color tag
    let metaThemeColor = document.querySelector('meta[name="theme-color"]');

    if (!metaThemeColor) {
      metaThemeColor = document.createElement('meta');
      metaThemeColor.setAttribute('name', 'theme-color');
      document.head.appendChild(metaThemeColor);
    }

    metaThemeColor.setAttribute('content', color);
  }, [resolvedTheme]);

  return null; // This component doesn't render anything
}
