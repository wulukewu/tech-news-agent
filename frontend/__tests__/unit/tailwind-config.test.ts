import { describe, it, expect } from 'vitest';
import config from '../../tailwind.config';

describe('Tailwind Configuration - Design System Foundation', () => {
  describe('Custom Breakpoints (Req 1.1, 1.2)', () => {
    it('should define xs breakpoint at 375px for mobile', () => {
      expect(config.theme?.extend?.screens).toHaveProperty('xs', '375px');
    });

    it('should define md breakpoint at 768px for tablet', () => {
      expect(config.theme?.extend?.screens).toHaveProperty('md', '768px');
    });

    it('should define lg breakpoint at 1024px for desktop', () => {
      expect(config.theme?.extend?.screens).toHaveProperty('lg', '1024px');
    });

    it('should define xl breakpoint at 1440px for wide desktop', () => {
      expect(config.theme?.extend?.screens).toHaveProperty('xl', '1440px');
    });
  });

  describe('Custom Spacing Scale (Req 1.7, 2.1)', () => {
    it('should define 44px spacing for touch targets', () => {
      expect(config.theme?.extend?.spacing).toHaveProperty('44', '44px');
    });

    it('should define 56px spacing for mobile nav items', () => {
      expect(config.theme?.extend?.spacing).toHaveProperty('56', '56px');
    });
  });

  describe('Semantic Color Tokens (Req 4.1, 4.2)', () => {
    it('should define primary color token', () => {
      expect(config.theme?.extend?.colors).toHaveProperty('primary');
    });

    it('should define secondary color token', () => {
      expect(config.theme?.extend?.colors).toHaveProperty('secondary');
    });

    it('should define accent color token', () => {
      expect(config.theme?.extend?.colors).toHaveProperty('accent');
    });

    it('should define destructive color token', () => {
      expect(config.theme?.extend?.colors).toHaveProperty('destructive');
    });

    it('should define muted color token', () => {
      expect(config.theme?.extend?.colors).toHaveProperty('muted');
    });
  });

  describe('Typography Scale (Req 4.3)', () => {
    it('should define xs font size at 12px', () => {
      expect(config.theme?.extend?.fontSize).toHaveProperty('xs');
      const xs = config.theme?.extend?.fontSize?.xs as [string, { lineHeight: string }];
      expect(xs[0]).toBe('12px');
    });

    it('should define base font size at 16px', () => {
      expect(config.theme?.extend?.fontSize).toHaveProperty('base');
      const base = config.theme?.extend?.fontSize?.base as [string, { lineHeight: string }];
      expect(base[0]).toBe('16px');
    });

    it('should define 5xl font size at 48px', () => {
      expect(config.theme?.extend?.fontSize).toHaveProperty('5xl');
      const fiveXl = config.theme?.extend?.fontSize?.['5xl'] as [string, { lineHeight: string }];
      expect(fiveXl[0]).toBe('48px');
    });
  });

  describe('Border Radius Values (Req 4.4)', () => {
    it('should define sm border radius at 2px', () => {
      expect(config.theme?.extend?.borderRadius).toHaveProperty('sm', '2px');
    });

    it('should define md border radius at 4px', () => {
      expect(config.theme?.extend?.borderRadius).toHaveProperty('md', '4px');
    });

    it('should define lg border radius at 6px', () => {
      expect(config.theme?.extend?.borderRadius).toHaveProperty('lg', '6px');
    });

    it('should define 3xl border radius at 16px', () => {
      expect(config.theme?.extend?.borderRadius).toHaveProperty('3xl', '16px');
    });
  });

  describe('Shadow System (Req 4.5)', () => {
    it('should define sm shadow', () => {
      expect(config.theme?.extend?.boxShadow).toHaveProperty('sm');
    });

    it('should define md shadow', () => {
      expect(config.theme?.extend?.boxShadow).toHaveProperty('md');
    });

    it('should define lg shadow', () => {
      expect(config.theme?.extend?.boxShadow).toHaveProperty('lg');
    });

    it('should define xl shadow', () => {
      expect(config.theme?.extend?.boxShadow).toHaveProperty('xl');
    });
  });

  describe('Animation Timing Functions and Durations (Req 4.7, 21.1)', () => {
    it('should define 150ms duration for micro-interactions', () => {
      expect(config.theme?.extend?.transitionDuration).toHaveProperty('150', '150ms');
    });

    it('should define 200ms duration for standard transitions', () => {
      expect(config.theme?.extend?.transitionDuration).toHaveProperty('200', '200ms');
    });

    it('should define 300ms duration for standard transitions', () => {
      expect(config.theme?.extend?.transitionDuration).toHaveProperty('300', '300ms');
    });

    it('should define 500ms duration for complex animations', () => {
      expect(config.theme?.extend?.transitionDuration).toHaveProperty('500', '500ms');
    });

    it('should define ease-out timing function', () => {
      expect(config.theme?.extend?.transitionTimingFunction).toHaveProperty('ease-out');
    });

    it('should define ease-in timing function', () => {
      expect(config.theme?.extend?.transitionTimingFunction).toHaveProperty('ease-in');
    });
  });

  describe('Touch Target Utilities (Req 2.1, 2.3)', () => {
    it('should define min-h-44 for touch targets', () => {
      expect(config.theme?.extend?.minHeight).toHaveProperty('44', '44px');
    });

    it('should define min-w-44 for touch targets', () => {
      expect(config.theme?.extend?.minWidth).toHaveProperty('44', '44px');
    });

    it('should define min-h-48 for form controls on mobile', () => {
      expect(config.theme?.extend?.minHeight).toHaveProperty('48', '48px');
    });

    it('should define min-h-56 for mobile nav items', () => {
      expect(config.theme?.extend?.minHeight).toHaveProperty('56', '56px');
    });
  });

  describe('Keyframe Animations (Req 21.2, 21.3)', () => {
    it('should define slide-in-from-left keyframe', () => {
      expect(config.theme?.extend?.keyframes).toHaveProperty('slide-in-from-left');
    });

    it('should define slide-up keyframe', () => {
      expect(config.theme?.extend?.keyframes).toHaveProperty('slide-up');
    });

    it('should define scale-up keyframe', () => {
      expect(config.theme?.extend?.keyframes).toHaveProperty('scale-up');
    });

    it('should define shimmer keyframe for loading states', () => {
      expect(config.theme?.extend?.keyframes).toHaveProperty('shimmer');
    });
  });

  describe('Animation Utilities', () => {
    it('should define slide-in-from-left animation', () => {
      expect(config.theme?.extend?.animation).toHaveProperty('slide-in-from-left');
    });

    it('should define slide-up animation', () => {
      expect(config.theme?.extend?.animation).toHaveProperty('slide-up');
    });

    it('should define scale-up animation', () => {
      expect(config.theme?.extend?.animation).toHaveProperty('scale-up');
    });

    it('should define shimmer animation', () => {
      expect(config.theme?.extend?.animation).toHaveProperty('shimmer');
    });
  });

  describe('Custom Utilities Plugin', () => {
    it('should include tailwindcss-animate plugin', () => {
      expect(config.plugins).toBeDefined();
      expect(config.plugins?.length).toBeGreaterThan(0);
    });

    it('should include custom utilities function for touch-target and safe-area', () => {
      expect(config.plugins).toBeDefined();
      expect(config.plugins?.length).toBe(2);
      expect(typeof config.plugins?.[1]).toBe('function');
    });
  });
});
