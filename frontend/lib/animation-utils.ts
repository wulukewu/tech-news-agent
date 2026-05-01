/**
 * Animation Utilities
 *
 * Centralized animation classes and utilities for consistent UX.
 * Follows design principles: subtle, purposeful, performant.
 */

/**
 * Spin Animation Speeds
 * - spin-slow: 3s per rotation (refresh buttons, non-urgent loading)
 * - spin-normal: 1.5s per rotation (standard loading indicators)
 * - spin-fast: 1s per rotation (only for very small spinners)
 */

/* Add to global CSS or use with arbitrary values */
export const SPIN_SPEEDS = {
  slow: 'animate-[spin_3s_linear_infinite]',
  normal: 'animate-[spin_1.5s_linear_infinite]',
  fast: 'animate-spin', // Default Tailwind (1s)
} as const;

/**
 * Pulse Animation Speeds
 * - pulse-slow: 3s cycle (subtle attention)
 * - pulse-normal: 2s cycle (default)
 */
export const PULSE_SPEEDS = {
  slow: 'animate-[pulse_3s_ease-in-out_infinite]',
  normal: 'animate-pulse', // Default Tailwind (2s)
} as const;

/**
 * Scale Hover Effects
 * - Buttons/CTAs: scale-[1.02] (2% growth)
 * - Cards: scale-[1.01] (1% growth)
 * - Icons: Use color transition instead
 */
export const HOVER_SCALES = {
  button: 'hover:scale-[1.02]',
  card: 'hover:scale-[1.01]',
  none: '', // For icons - use color instead
} as const;

/**
 * Transition Durations
 * - Fast: 150ms (color changes, opacity)
 * - Normal: 200ms (most interactions)
 * - Slow: 300ms (complex animations)
 */
export const TRANSITION_DURATIONS = {
  fast: 'duration-150',
  normal: 'duration-200',
  slow: 'duration-300',
} as const;

/**
 * Active (pressed) state
 * - Subtle press: scale-[0.98] (2% shrink)
 */
export const ACTIVE_SCALE = 'active:scale-[0.98]';

/**
 * Recommended combinations
 */
export const ANIMATION_PRESETS = {
  // Refresh button (not loading)
  refreshButton: 'transition-transform duration-200 hover:rotate-180',

  // Refresh button (loading)
  refreshButtonLoading: 'animate-[spin_3s_linear_infinite]',

  // Standard loading spinner
  loadingSpinner: 'animate-[spin_1.5s_linear_infinite]',

  // Button hover
  buttonHover: 'transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]',

  // Card hover
  cardHover: 'transition-all duration-200 hover:scale-[1.01] hover:shadow-md',

  // Icon color transition (no scale)
  iconHover: 'transition-colors duration-150',

  // Subtle pulse for status indicators
  statusPulse: 'animate-[pulse_3s_ease-in-out_infinite]',
} as const;
