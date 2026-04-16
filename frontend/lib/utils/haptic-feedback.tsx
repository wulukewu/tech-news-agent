/**
 * Haptic Feedback Utilities for Mobile Devices
 *
 * Features for Task 12.3:
 * - Cross-platform haptic feedback support
 * - Different vibration patterns for different actions
 * - Graceful degradation for unsupported devices
 * - User preference respect (can be disabled)
 * - Performance optimized with debouncing
 *
 * Requirements:
 * - 7.10: Mobile device haptic feedback support
 */

export type HapticPattern =
  | 'light'
  | 'medium'
  | 'heavy'
  | 'success'
  | 'warning'
  | 'error'
  | 'selection';

interface HapticConfig {
  enabled: boolean;
  patterns: Record<HapticPattern, number | number[]>;
}

class HapticFeedbackManager {
  private config: HapticConfig = {
    enabled: true,
    patterns: {
      light: 50,
      medium: 100,
      heavy: 200,
      success: [50, 50, 100],
      warning: [100, 50, 100],
      error: [200, 100, 200],
      selection: 25,
    },
  };

  private lastVibration = 0;
  private debounceTime = 50; // Minimum time between vibrations

  constructor() {
    // Check if haptic feedback is supported
    this.config.enabled = this.isSupported();

    // Load user preferences
    this.loadPreferences();
  }

  /**
   * Check if haptic feedback is supported on this device
   */
  private isSupported(): boolean {
    return (
      typeof navigator !== 'undefined' &&
      'vibrate' in navigator &&
      typeof navigator.vibrate === 'function'
    );
  }

  /**
   * Load user preferences from localStorage
   */
  private loadPreferences(): void {
    try {
      const stored = localStorage.getItem('haptic-feedback-enabled');
      if (stored !== null) {
        this.config.enabled = JSON.parse(stored) && this.isSupported();
      }
    } catch (error) {
      console.warn('Failed to load haptic feedback preferences:', error);
    }
  }

  /**
   * Save user preferences to localStorage
   */
  private savePreferences(): void {
    try {
      localStorage.setItem('haptic-feedback-enabled', JSON.stringify(this.config.enabled));
    } catch (error) {
      console.warn('Failed to save haptic feedback preferences:', error);
    }
  }

  /**
   * Enable or disable haptic feedback
   */
  setEnabled(enabled: boolean): void {
    this.config.enabled = enabled && this.isSupported();
    this.savePreferences();
  }

  /**
   * Check if haptic feedback is currently enabled
   */
  isEnabled(): boolean {
    return this.config.enabled;
  }

  /**
   * Trigger haptic feedback with debouncing
   */
  private vibrate(pattern: number | number[]): void {
    if (!this.config.enabled || !this.isSupported()) {
      return;
    }

    const now = Date.now();
    if (now - this.lastVibration < this.debounceTime) {
      return;
    }

    try {
      navigator.vibrate(pattern);
      this.lastVibration = now;
    } catch (error) {
      console.warn('Haptic feedback failed:', error);
    }
  }

  /**
   * Trigger light haptic feedback (for subtle interactions)
   */
  light(): void {
    this.vibrate(this.config.patterns.light);
  }

  /**
   * Trigger medium haptic feedback (for standard interactions)
   */
  medium(): void {
    this.vibrate(this.config.patterns.medium);
  }

  /**
   * Trigger heavy haptic feedback (for important interactions)
   */
  heavy(): void {
    this.vibrate(this.config.patterns.heavy);
  }

  /**
   * Trigger success haptic feedback (for successful actions)
   */
  success(): void {
    this.vibrate(this.config.patterns.success);
  }

  /**
   * Trigger warning haptic feedback (for warning actions)
   */
  warning(): void {
    this.vibrate(this.config.patterns.warning);
  }

  /**
   * Trigger error haptic feedback (for error states)
   */
  error(): void {
    this.vibrate(this.config.patterns.error);
  }

  /**
   * Trigger selection haptic feedback (for item selection)
   */
  selection(): void {
    this.vibrate(this.config.patterns.selection);
  }

  /**
   * Trigger haptic feedback by pattern name
   */
  trigger(pattern: HapticPattern): void {
    switch (pattern) {
      case 'light':
        this.light();
        break;
      case 'medium':
        this.medium();
        break;
      case 'heavy':
        this.heavy();
        break;
      case 'success':
        this.success();
        break;
      case 'warning':
        this.warning();
        break;
      case 'error':
        this.error();
        break;
      case 'selection':
        this.selection();
        break;
    }
  }

  /**
   * Custom vibration pattern
   */
  custom(pattern: number | number[]): void {
    this.vibrate(pattern);
  }

  /**
   * Stop any ongoing vibration
   */
  stop(): void {
    if (this.isSupported()) {
      try {
        navigator.vibrate(0);
      } catch (error) {
        console.warn('Failed to stop haptic feedback:', error);
      }
    }
  }
}

// Create singleton instance
export const hapticFeedback = new HapticFeedbackManager();

/**
 * React hook for haptic feedback
 */
export function useHapticFeedback() {
  return {
    trigger: hapticFeedback.trigger.bind(hapticFeedback),
    light: hapticFeedback.light.bind(hapticFeedback),
    medium: hapticFeedback.medium.bind(hapticFeedback),
    heavy: hapticFeedback.heavy.bind(hapticFeedback),
    success: hapticFeedback.success.bind(hapticFeedback),
    warning: hapticFeedback.warning.bind(hapticFeedback),
    error: hapticFeedback.error.bind(hapticFeedback),
    selection: hapticFeedback.selection.bind(hapticFeedback),
    custom: hapticFeedback.custom.bind(hapticFeedback),
    stop: hapticFeedback.stop.bind(hapticFeedback),
    isEnabled: hapticFeedback.isEnabled.bind(hapticFeedback),
    setEnabled: hapticFeedback.setEnabled.bind(hapticFeedback),
  };
}

/**
 * Higher-order component to add haptic feedback to any component
 */
export function withHapticFeedback<T extends object>(
  Component: React.ComponentType<T>,
  pattern: HapticPattern = 'light'
) {
  return function HapticComponent(props: T & { onHapticTrigger?: () => void }) {
    const { onHapticTrigger, ...restProps } = props;

    const handleInteraction = () => {
      hapticFeedback.trigger(pattern);
      onHapticTrigger?.();
    };

    return (
      <div onClick={handleInteraction} onTouchStart={handleInteraction}>
        <Component {...(restProps as T)} />
      </div>
    );
  };
}

/**
 * Utility functions for common haptic feedback scenarios
 */
export const hapticUtils = {
  /**
   * Button press feedback
   */
  buttonPress: () => hapticFeedback.light(),

  /**
   * Toggle switch feedback
   */
  toggleSwitch: () => hapticFeedback.medium(),

  /**
   * Item selection feedback
   */
  itemSelect: () => hapticFeedback.selection(),

  /**
   * Drag start feedback
   */
  dragStart: () => hapticFeedback.medium(),

  /**
   * Drag end feedback
   */
  dragEnd: () => hapticFeedback.light(),

  /**
   * Form submission success
   */
  formSuccess: () => hapticFeedback.success(),

  /**
   * Form validation error
   */
  formError: () => hapticFeedback.error(),

  /**
   * Navigation feedback
   */
  navigate: () => hapticFeedback.light(),

  /**
   * Refresh action feedback
   */
  refresh: () => hapticFeedback.medium(),

  /**
   * Delete action feedback
   */
  delete: () => hapticFeedback.warning(),

  /**
   * Long press feedback
   */
  longPress: () => hapticFeedback.heavy(),
};

export default hapticFeedback;
