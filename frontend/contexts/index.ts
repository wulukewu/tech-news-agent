/**
 * Context Exports
 *
 * This file provides a centralized export point for all context providers and hooks.
 * Import contexts from this file for cleaner imports.
 *
 * @example
 * ```tsx
 * // Instead of:
 * import { useAuth } from '@/contexts/AuthContext';
 * import { useUser } from '@/contexts/UserContext';
 * import { useTheme } from '@/contexts/ThemeContext';
 *
 * // You can use:
 * import { useAuth, useUser, useTheme } from '@/contexts';
 * ```
 */

// AuthContext exports
export { AuthProvider, useAuth, type AuthContextType } from './AuthContext';

// UserContext exports
export { UserProvider, useUser, type User, type UserContextType } from './UserContext';

// ThemeContext exports
export { ThemeProvider, useTheme, type Theme, type ThemeContextType } from './ThemeContext';

// NotFoundContext exports
export { NotFoundProvider, useNotFound } from './NotFoundContext';

// I18nContext exports
export { I18nProvider, useI18n } from './I18nContext';
