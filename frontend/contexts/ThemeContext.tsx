'use client';

/**
 * Theme Context
 *
 * This module provides a React Context for managing theme preferences.
 * It handles theme state (light/dark mode) and persists preferences to localStorage.
 *
 * Responsibilities:
 * - Theme state (light, dark, system)
 * - Theme switching
 * - Persisting theme preference to localStorage
 * - Applying theme to document root
 *
 * Does NOT handle:
 * - Authentication status (see AuthContext)
 * - User profile data (see UserContext)
 *
 * Usage:
 * ```tsx
 * // In app/layout.tsx
 * <ThemeProvider>
 *   {children}
 * </ThemeProvider>
 *
 * // In any component
 * const { theme, setTheme } = useTheme();
 * ```
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

/**
 * Theme type
 *
 * - 'light': Light mode
 * - 'dark': Dark mode
 * - 'system': Follow system preference
 */
export type Theme = 'light' | 'dark' | 'system';

/**
 * Theme Context Type
 *
 * Defines the shape of the theme context.
 * Only includes theme-related state and methods.
 */
export interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: 'light' | 'dark';
}

/**
 * Theme Context
 *
 * Provides theme state and methods to all child components.
 * Should not be used directly - use the useTheme hook instead.
 */
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_STORAGE_KEY = 'theme-preference';

/**
 * ThemeProvider Component
 *
 * Wraps the application and provides theme state to all child components.
 * Automatically loads theme preference from localStorage and applies it to the document.
 *
 * @param children - Child components to wrap
 * @param defaultTheme - Default theme to use if no preference is stored (default: 'system')
 */
export function ThemeProvider({
  children,
  defaultTheme = 'system',
}: {
  children: React.ReactNode;
  defaultTheme?: Theme;
}) {
  const [theme, setThemeState] = useState<Theme>(defaultTheme);
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light');

  /**
   * Get system theme preference
   *
   * Checks the user's system preference for dark mode.
   */
  const getSystemTheme = useCallback((): 'light' | 'dark' => {
    if (typeof window === 'undefined') return 'light';
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }, []);

  /**
   * Resolve theme to actual light/dark value
   *
   * If theme is 'system', returns the system preference.
   * Otherwise, returns the theme value directly.
   */
  const resolveTheme = useCallback(
    (themeValue: Theme): 'light' | 'dark' => {
      if (themeValue === 'system') {
        return getSystemTheme();
      }
      return themeValue;
    },
    [getSystemTheme]
  );

  /**
   * Apply theme to document
   *
   * Adds or removes the 'dark' class from the document root element.
   * This allows CSS to apply dark mode styles using the .dark selector.
   */
  const applyTheme = useCallback((resolvedThemeValue: 'light' | 'dark') => {
    if (typeof window === 'undefined') return;

    const root = document.documentElement;
    if (resolvedThemeValue === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, []);

  /**
   * Set theme
   *
   * Updates the theme state, persists it to localStorage, and applies it to the document.
   */
  const setTheme = useCallback(
    (newTheme: Theme) => {
      setThemeState(newTheme);
      const resolved = resolveTheme(newTheme);
      setResolvedTheme(resolved);
      applyTheme(resolved);

      // Persist to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem(THEME_STORAGE_KEY, newTheme);
      }
    },
    [resolveTheme, applyTheme]
  );

  /**
   * Load theme preference from localStorage on mount
   */
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const storedTheme = localStorage.getItem(THEME_STORAGE_KEY) as Theme | null;
    const initialTheme = storedTheme || defaultTheme;
    const resolved = resolveTheme(initialTheme);

    setThemeState(initialTheme);
    setResolvedTheme(resolved);
    applyTheme(resolved);
  }, [defaultTheme, resolveTheme, applyTheme]);

  /**
   * Listen for system theme changes
   *
   * When theme is set to 'system', update the resolved theme when the system preference changes.
   */
  useEffect(() => {
    if (typeof window === 'undefined' || theme !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      const newResolvedTheme = e.matches ? 'dark' : 'light';
      setResolvedTheme(newResolvedTheme);
      applyTheme(newResolvedTheme);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme, applyTheme]);

  const value: ThemeContextType = {
    theme,
    setTheme,
    resolvedTheme,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

/**
 * useTheme Hook
 *
 * Custom hook to access theme state and methods.
 * Must be used within a component wrapped by ThemeProvider.
 *
 * @returns ThemeContextType - Theme state and methods
 * @throws Error if used outside of ThemeProvider
 *
 * @example
 * ```tsx
 * function ThemeToggle() {
 *   const { theme, setTheme, resolvedTheme } = useTheme();
 *
 *   return (
 *     <div>
 *       <p>Current theme: {theme}</p>
 *       <p>Resolved theme: {resolvedTheme}</p>
 *       <button onClick={() => setTheme('light')}>Light</button>
 *       <button onClick={() => setTheme('dark')}>Dark</button>
 *       <button onClick={() => setTheme('system')}>System</button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}
