import { hapticFeedback, useHapticFeedback, hapticUtils } from '../haptic-feedback';
import { renderHook, act } from '@testing-library/react';

// Mock navigator.vibrate
const mockVibrate = jest.fn();
Object.defineProperty(navigator, 'vibrate', {
  value: mockVibrate,
  writable: true,
});

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
});

describe('HapticFeedback', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockVibrate.mockClear();
    mockLocalStorage.getItem.mockClear();
    mockLocalStorage.setItem.mockClear();

    // Reset haptic feedback to enabled state
    hapticFeedback.setEnabled(true);
  });

  describe('Initialization', () => {
    it('detects vibration support correctly', () => {
      expect(hapticFeedback.isEnabled()).toBe(true);
    });

    it('loads preferences from localStorage', () => {
      mockLocalStorage.getItem.mockReturnValue('false');

      // Create new instance to test initialization
      const { hapticFeedback: newInstance } = require('../haptic-feedback');

      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('haptic-feedback-enabled');
    });

    it('handles localStorage errors gracefully', () => {
      mockLocalStorage.getItem.mockImplementation(() => {
        throw new Error('localStorage error');
      });

      // Should not throw error
      expect(() => {
        const { hapticFeedback: newInstance } = require('../haptic-feedback');
      }).not.toThrow();
    });
  });

  describe('Enable/Disable Functionality', () => {
    it('enables haptic feedback', () => {
      hapticFeedback.setEnabled(true);

      expect(hapticFeedback.isEnabled()).toBe(true);
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('haptic-feedback-enabled', 'true');
    });

    it('disables haptic feedback', () => {
      hapticFeedback.setEnabled(false);

      expect(hapticFeedback.isEnabled()).toBe(false);
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('haptic-feedback-enabled', 'false');
    });

    it('saves preferences to localStorage', () => {
      hapticFeedback.setEnabled(true);

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('haptic-feedback-enabled', 'true');
    });

    it('handles localStorage save errors gracefully', () => {
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error('localStorage error');
      });

      expect(() => {
        hapticFeedback.setEnabled(true);
      }).not.toThrow();
    });
  });

  describe('Vibration Patterns', () => {
    it('triggers light vibration', () => {
      hapticFeedback.light();

      expect(mockVibrate).toHaveBeenCalledWith(50);
    });

    it('triggers medium vibration', () => {
      hapticFeedback.medium();

      expect(mockVibrate).toHaveBeenCalledWith(100);
    });

    it('triggers heavy vibration', () => {
      hapticFeedback.heavy();

      expect(mockVibrate).toHaveBeenCalledWith(200);
    });

    it('triggers success vibration pattern', () => {
      hapticFeedback.success();

      expect(mockVibrate).toHaveBeenCalledWith([50, 50, 100]);
    });

    it('triggers warning vibration pattern', () => {
      hapticFeedback.warning();

      expect(mockVibrate).toHaveBeenCalledWith([100, 50, 100]);
    });

    it('triggers error vibration pattern', () => {
      hapticFeedback.error();

      expect(mockVibrate).toHaveBeenCalledWith([200, 100, 200]);
    });

    it('triggers selection vibration', () => {
      hapticFeedback.selection();

      expect(mockVibrate).toHaveBeenCalledWith(25);
    });

    it('triggers custom vibration pattern', () => {
      const customPattern = [100, 200, 100];
      hapticFeedback.custom(customPattern);

      expect(mockVibrate).toHaveBeenCalledWith(customPattern);
    });
  });

  describe('Pattern Trigger Method', () => {
    it('triggers correct pattern by name', () => {
      hapticFeedback.trigger('light');
      expect(mockVibrate).toHaveBeenCalledWith(50);

      hapticFeedback.trigger('medium');
      expect(mockVibrate).toHaveBeenCalledWith(100);

      hapticFeedback.trigger('heavy');
      expect(mockVibrate).toHaveBeenCalledWith(200);

      hapticFeedback.trigger('success');
      expect(mockVibrate).toHaveBeenCalledWith([50, 50, 100]);

      hapticFeedback.trigger('warning');
      expect(mockVibrate).toHaveBeenCalledWith([100, 50, 100]);

      hapticFeedback.trigger('error');
      expect(mockVibrate).toHaveBeenCalledWith([200, 100, 200]);

      hapticFeedback.trigger('selection');
      expect(mockVibrate).toHaveBeenCalledWith(25);
    });
  });

  describe('Debouncing', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('debounces rapid vibration calls', () => {
      hapticFeedback.light();
      hapticFeedback.light();
      hapticFeedback.light();

      // Only first call should trigger vibration
      expect(mockVibrate).toHaveBeenCalledTimes(1);
    });

    it('allows vibration after debounce period', () => {
      hapticFeedback.light();
      expect(mockVibrate).toHaveBeenCalledTimes(1);

      // Advance time past debounce period
      jest.advanceTimersByTime(100);

      hapticFeedback.light();
      expect(mockVibrate).toHaveBeenCalledTimes(2);
    });
  });

  describe('Disabled State', () => {
    it('does not vibrate when disabled', () => {
      hapticFeedback.setEnabled(false);
      hapticFeedback.light();

      expect(mockVibrate).not.toHaveBeenCalled();
    });

    it('does not vibrate any pattern when disabled', () => {
      hapticFeedback.setEnabled(false);

      hapticFeedback.light();
      hapticFeedback.medium();
      hapticFeedback.heavy();
      hapticFeedback.success();
      hapticFeedback.warning();
      hapticFeedback.error();
      hapticFeedback.selection();

      expect(mockVibrate).not.toHaveBeenCalled();
    });
  });

  describe('Stop Functionality', () => {
    it('stops ongoing vibration', () => {
      hapticFeedback.stop();

      expect(mockVibrate).toHaveBeenCalledWith(0);
    });

    it('handles stop errors gracefully', () => {
      mockVibrate.mockImplementation(() => {
        throw new Error('Vibration error');
      });

      expect(() => {
        hapticFeedback.stop();
      }).not.toThrow();
    });
  });

  describe('Error Handling', () => {
    it('handles vibration errors gracefully', () => {
      mockVibrate.mockImplementation(() => {
        throw new Error('Vibration error');
      });

      expect(() => {
        hapticFeedback.light();
      }).not.toThrow();
    });

    it('continues working after vibration error', () => {
      mockVibrate
        .mockImplementationOnce(() => {
          throw new Error('Vibration error');
        })
        .mockImplementationOnce(() => {});

      hapticFeedback.light(); // Should handle error

      jest.advanceTimersByTime(100);
      hapticFeedback.medium(); // Should work normally

      expect(mockVibrate).toHaveBeenCalledTimes(2);
    });
  });

  describe('Unsupported Device Handling', () => {
    beforeEach(() => {
      // Mock unsupported device
      Object.defineProperty(navigator, 'vibrate', {
        value: undefined,
        writable: true,
      });
    });

    afterEach(() => {
      // Restore vibrate support
      Object.defineProperty(navigator, 'vibrate', {
        value: mockVibrate,
        writable: true,
      });
    });

    it('detects unsupported devices', () => {
      const { hapticFeedback: newInstance } = require('../haptic-feedback');
      expect(newInstance.isEnabled()).toBe(false);
    });

    it('does not attempt vibration on unsupported devices', () => {
      const { hapticFeedback: newInstance } = require('../haptic-feedback');
      newInstance.light();

      // Should not call vibrate (since it's undefined)
      expect(mockVibrate).not.toHaveBeenCalled();
    });
  });
});

describe('useHapticFeedback Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockVibrate.mockClear();
  });

  it('provides all haptic feedback methods', () => {
    const { result } = renderHook(() => useHapticFeedback());

    expect(typeof result.current.trigger).toBe('function');
    expect(typeof result.current.light).toBe('function');
    expect(typeof result.current.medium).toBe('function');
    expect(typeof result.current.heavy).toBe('function');
    expect(typeof result.current.success).toBe('function');
    expect(typeof result.current.warning).toBe('function');
    expect(typeof result.current.error).toBe('function');
    expect(typeof result.current.selection).toBe('function');
    expect(typeof result.current.custom).toBe('function');
    expect(typeof result.current.stop).toBe('function');
    expect(typeof result.current.isEnabled).toBe('function');
    expect(typeof result.current.setEnabled).toBe('function');
  });

  it('calls haptic feedback methods correctly', () => {
    const { result } = renderHook(() => useHapticFeedback());

    act(() => {
      result.current.light();
    });

    expect(mockVibrate).toHaveBeenCalledWith(50);
  });

  it('manages enabled state correctly', () => {
    const { result } = renderHook(() => useHapticFeedback());

    act(() => {
      result.current.setEnabled(false);
    });

    expect(result.current.isEnabled()).toBe(false);

    act(() => {
      result.current.light();
    });

    expect(mockVibrate).not.toHaveBeenCalled();
  });
});

describe('hapticUtils', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockVibrate.mockClear();
    hapticFeedback.setEnabled(true);
  });

  it('provides button press feedback', () => {
    hapticUtils.buttonPress();
    expect(mockVibrate).toHaveBeenCalledWith(50);
  });

  it('provides toggle switch feedback', () => {
    hapticUtils.toggleSwitch();
    expect(mockVibrate).toHaveBeenCalledWith(100);
  });

  it('provides item selection feedback', () => {
    hapticUtils.itemSelect();
    expect(mockVibrate).toHaveBeenCalledWith(25);
  });

  it('provides drag start feedback', () => {
    hapticUtils.dragStart();
    expect(mockVibrate).toHaveBeenCalledWith(100);
  });

  it('provides drag end feedback', () => {
    hapticUtils.dragEnd();
    expect(mockVibrate).toHaveBeenCalledWith(50);
  });

  it('provides form success feedback', () => {
    hapticUtils.formSuccess();
    expect(mockVibrate).toHaveBeenCalledWith([50, 50, 100]);
  });

  it('provides form error feedback', () => {
    hapticUtils.formError();
    expect(mockVibrate).toHaveBeenCalledWith([200, 100, 200]);
  });

  it('provides navigation feedback', () => {
    hapticUtils.navigate();
    expect(mockVibrate).toHaveBeenCalledWith(50);
  });

  it('provides refresh feedback', () => {
    hapticUtils.refresh();
    expect(mockVibrate).toHaveBeenCalledWith(100);
  });

  it('provides delete feedback', () => {
    hapticUtils.delete();
    expect(mockVibrate).toHaveBeenCalledWith([100, 50, 100]);
  });

  it('provides long press feedback', () => {
    hapticUtils.longPress();
    expect(mockVibrate).toHaveBeenCalledWith(200);
  });
});
