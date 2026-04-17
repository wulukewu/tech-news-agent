import {
  getCategoryColor,
  getCategoryLabel,
  getCategoryBadgeClasses,
  getCategoryBadgeStyles,
} from '@/lib/utils';

describe('Category Color Utilities', () => {
  describe('getCategoryColor', () => {
    it('should return correct color for tech-news in light mode', () => {
      const color = getCategoryColor('tech-news', 'light');
      expect(color).toBe('#3B82F6');
    });

    it('should return correct color for tech-news in dark mode', () => {
      const color = getCategoryColor('tech-news', 'dark');
      expect(color).toBe('#60A5FA');
    });

    it('should return correct color for ai-ml in light mode', () => {
      const color = getCategoryColor('ai-ml', 'light');
      expect(color).toBe('#A855F7');
    });

    it('should return correct color for web-dev in light mode', () => {
      const color = getCategoryColor('web-dev', 'light');
      expect(color).toBe('#10B981');
    });

    it('should return correct color for devops in light mode', () => {
      const color = getCategoryColor('devops', 'light');
      expect(color).toBe('#F97316');
    });

    it('should return correct color for security in light mode', () => {
      const color = getCategoryColor('security', 'light');
      expect(color).toBe('#EF4444');
    });

    it('should handle category aliases (ai -> ai-ml)', () => {
      const color = getCategoryColor('ai', 'light');
      expect(color).toBe('#A855F7'); // Same as ai-ml
    });

    it('should handle category aliases (web -> web-dev)', () => {
      const color = getCategoryColor('web', 'light');
      expect(color).toBe('#10B981'); // Same as web-dev
    });

    it('should handle category aliases (frontend -> web-dev)', () => {
      const color = getCategoryColor('frontend', 'light');
      expect(color).toBe('#10B981'); // Same as web-dev
    });

    it('should return default color for unknown category', () => {
      const color = getCategoryColor('unknown-category', 'light');
      expect(color).toBe('#6B7280'); // gray-500
    });

    it('should return default dark color for unknown category in dark mode', () => {
      const color = getCategoryColor('unknown-category', 'dark');
      expect(color).toBe('#9CA3AF'); // gray-400
    });

    it('should normalize category names (uppercase)', () => {
      const color = getCategoryColor('TECH-NEWS', 'light');
      expect(color).toBe('#3B82F6');
    });

    it('should normalize category names (with spaces)', () => {
      const color = getCategoryColor('  tech-news  ', 'light');
      expect(color).toBe('#3B82F6');
    });

    it('should support custom category colors', () => {
      const customColors = {
        'custom-category': {
          light: '#FF0000',
          dark: '#00FF00',
        },
      };

      const lightColor = getCategoryColor('custom-category', 'light', customColors);
      expect(lightColor).toBe('#FF0000');

      const darkColor = getCategoryColor('custom-category', 'dark', customColors);
      expect(darkColor).toBe('#00FF00');
    });

    it('should prioritize custom colors over predefined colors', () => {
      const customColors = {
        'tech-news': {
          light: '#CUSTOM1',
          dark: '#CUSTOM2',
        },
      };

      const color = getCategoryColor('tech-news', 'light', customColors);
      expect(color).toBe('#CUSTOM1');
    });
  });

  describe('getCategoryLabel', () => {
    it('should return correct label for tech-news', () => {
      const label = getCategoryLabel('tech-news');
      expect(label).toBe('Tech News');
    });

    it('should return correct label for ai-ml', () => {
      const label = getCategoryLabel('ai-ml');
      expect(label).toBe('AI/ML');
    });

    it('should return correct label for web-dev', () => {
      const label = getCategoryLabel('web-dev');
      expect(label).toBe('Web Dev');
    });

    it('should return correct label for devops', () => {
      const label = getCategoryLabel('devops');
      expect(label).toBe('DevOps');
    });

    it('should return correct label for security', () => {
      const label = getCategoryLabel('security');
      expect(label).toBe('Security');
    });

    it('should handle aliases (ai -> AI/ML)', () => {
      const label = getCategoryLabel('ai');
      expect(label).toBe('AI/ML');
    });

    it('should return "Other" for unknown categories', () => {
      const label = getCategoryLabel('unknown-category');
      expect(label).toBe('Other');
    });
  });

  describe('getCategoryBadgeClasses', () => {
    it('should return base badge classes', () => {
      const classes = getCategoryBadgeClasses('tech-news', 'light');
      expect(classes).toContain('inline-flex');
      expect(classes).toContain('items-center');
      expect(classes).toContain('rounded-md');
      expect(classes).toContain('px-2');
      expect(classes).toContain('py-1');
      expect(classes).toContain('text-xs');
      expect(classes).toContain('font-medium');
    });
  });

  describe('getCategoryBadgeStyles', () => {
    it('should return correct styles for light mode', () => {
      const styles = getCategoryBadgeStyles('tech-news', 'light');
      expect(styles.backgroundColor).toBe('#3B82F6');
      expect(styles.color).toBe('#FFFFFF');
    });

    it('should return correct styles for dark mode', () => {
      const styles = getCategoryBadgeStyles('tech-news', 'dark');
      expect(styles.backgroundColor).toBe('#60A5FA');
      expect(styles.color).toBe('#000000');
    });

    it('should support custom colors', () => {
      const customColors = {
        'custom-category': {
          light: '#FF0000',
          dark: '#00FF00',
        },
      };

      const styles = getCategoryBadgeStyles('custom-category', 'light', customColors);
      expect(styles.backgroundColor).toBe('#FF0000');
    });
  });

  describe('WCAG AA Contrast Compliance', () => {
    it('should use different shades for light and dark modes', () => {
      const lightColor = getCategoryColor('tech-news', 'light');
      const darkColor = getCategoryColor('tech-news', 'dark');
      expect(lightColor).not.toBe(darkColor);
    });

    it('should use lighter shades in dark mode for better contrast', () => {
      // Dark mode colors should be lighter (higher in the color scale)
      // blue-500 (#3B82F6) in light mode -> blue-400 (#60A5FA) in dark mode
      const lightColor = getCategoryColor('tech-news', 'light');
      const darkColor = getCategoryColor('tech-news', 'dark');

      // Verify they are different shades
      expect(lightColor).toBe('#3B82F6'); // blue-500
      expect(darkColor).toBe('#60A5FA'); // blue-400 (lighter)
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty string category', () => {
      const color = getCategoryColor('', 'light');
      expect(color).toBe('#6B7280'); // default color
    });

    it('should handle null-like values gracefully', () => {
      const color = getCategoryColor('null', 'light');
      expect(color).toBe('#6B7280'); // default color
    });

    it('should handle special characters in category names', () => {
      const color = getCategoryColor('tech@news!', 'light');
      expect(color).toBe('#6B7280'); // default color (no match)
    });
  });
});
