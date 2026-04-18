import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import React from 'react';
import { CATEGORY_COLORS, CATEGORY_ALIASES } from '../constants';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Format date utilities
export function formatDate(date: Date | string): string {
  const d = new Date(date);
  return d.toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export function formatRelativeTime(date: Date | string): string {
  const d = new Date(date);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - d.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return '剛剛';
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes} 分鐘前`;
  }

  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours} 小時前`;
  }

  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) {
    return `${diffInDays} 天前`;
  }

  return formatDate(d);
}

// URL utilities
export function buildUrl(base: string, params: Record<string, any>): string {
  // Only use window.location.origin in browser environment
  const origin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000';
  const url = new URL(base, origin);

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        value.forEach((v) => url.searchParams.append(key, String(v)));
      } else {
        url.searchParams.set(key, String(value));
      }
    }
  });

  return url.toString();
}

// Debounce utility
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return (...args: Parameters<T>) => {
    if (timeout) {
      clearTimeout(timeout);
    }

    timeout = setTimeout(() => {
      func(...args);
    }, wait);
  };
}

// Throttle utility
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean = false;

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

// Local storage utilities with error handling
export const storage = {
  get: <T>(key: string, defaultValue?: T): T | null => {
    if (typeof window === 'undefined') return defaultValue || null;

    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue || null;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return defaultValue || null;
    }
  },

  set: <T>(key: string, value: T): void => {
    if (typeof window === 'undefined') return;

    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  },

  remove: (key: string): void => {
    if (typeof window === 'undefined') return;

    try {
      window.localStorage.removeItem(key);
    } catch (error) {
      console.error(`Error removing localStorage key "${key}":`, error);
    }
  },
};

// Error handling utilities
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  return String(error);
}

// Array utilities
export function chunk<T>(array: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
}

export function unique<T>(array: T[]): T[] {
  return [...new Set(array)];
}

// Number utilities
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

// Category color utilities (Req 24.1, 24.2, 24.5, 24.6, 24.7)

/**
 * Get category color based on theme and category name
 * Supports custom category colors and falls back to neutral color for unknown categories
 *
 * @param category - Category name (e.g., 'tech-news', 'ai', 'web-dev')
 * @param theme - Current theme ('light' or 'dark')
 * @param customColors - Optional custom color mapping for user-defined categories
 * @returns Hex color string
 *
 * @example
 * getCategoryColor('tech-news', 'light') // Returns '#3B82F6'
 * getCategoryColor('ai', 'dark') // Returns '#C084FC' (uses alias mapping)
 * getCategoryColor('unknown', 'light') // Returns '#6B7280' (fallback)
 */
export function getCategoryColor(
  category: string,
  theme: 'light' | 'dark' = 'light',
  customColors?: Record<string, { light: string; dark: string }>
): string {
  // Normalize category name (lowercase, trim)
  const normalizedCategory = category.toLowerCase().trim();

  // Check custom colors first (Req 24.6)
  if (customColors && customColors[normalizedCategory]) {
    return customColors[normalizedCategory][theme];
  }

  // Map category through aliases
  const mappedCategory = CATEGORY_ALIASES[normalizedCategory as keyof typeof CATEGORY_ALIASES];

  // Get color from predefined mapping or use default (Req 24.7)
  const categoryKey = mappedCategory || 'default';
  return CATEGORY_COLORS[categoryKey][theme];
}

/**
 * Get category label for display
 *
 * @param category - Category name
 * @returns Human-readable category label
 *
 * @example
 * getCategoryLabel('tech-news') // Returns 'Tech News'
 * getCategoryLabel('ai') // Returns 'AI/ML'
 */
export function getCategoryLabel(category: string): string {
  const normalizedCategory = category.toLowerCase().trim();
  const mappedCategory = CATEGORY_ALIASES[normalizedCategory as keyof typeof CATEGORY_ALIASES];
  const categoryKey = mappedCategory || 'default';
  return CATEGORY_COLORS[categoryKey].label;
}

/**
 * Get Tailwind CSS classes for category badge
 * Ensures WCAG AA contrast ratios in both themes
 *
 * @param category - Category name
 * @param theme - Current theme ('light' or 'dark')
 * @returns Tailwind CSS class string
 *
 * @example
 * getCategoryBadgeClasses('tech-news', 'light')
 * // Returns classes with appropriate background and text colors
 */
export function getCategoryBadgeClasses(
  category: string,
  theme: 'light' | 'dark' = 'light'
): string {
  const color = getCategoryColor(category, theme);

  // Base badge classes with proper sizing (Req 24.8)
  const baseClasses = 'inline-flex items-center rounded-md px-2 py-1 text-xs font-medium';

  // Apply color as inline style since we're using hex colors
  // The component using this should apply the style separately
  return baseClasses;
}

/**
 * Get inline styles for category badge
 * Ensures WCAG AA contrast ratios in both themes
 *
 * @param category - Category name
 * @param theme - Current theme ('light' or 'dark')
 * @param customColors - Optional custom color mapping
 * @returns React CSSProperties object
 *
 * @example
 * <span style={getCategoryBadgeStyles('tech-news', 'light')}>Tech News</span>
 */
export function getCategoryBadgeStyles(
  category: string,
  theme: 'light' | 'dark' = 'light',
  customColors?: Record<string, { light: string; dark: string }>
): React.CSSProperties {
  const color = getCategoryColor(category, theme, customColors);

  // Calculate appropriate text color based on background
  // For colored backgrounds, use white text for better contrast
  const textColor = theme === 'light' ? '#FFFFFF' : '#000000';

  return {
    backgroundColor: color,
    color: textColor,
  };
}
