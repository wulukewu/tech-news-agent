/**
 * Test file demonstrating the migration of SORT_OPTIONS to use translation keys
 *
 * This test verifies that:
 * 1. SORT_OPTIONS uses labelKey instead of hardcoded labels
 * 2. The translation keys match the expected format
 * 3. Components can map SORT_OPTIONS to translated labels
 */

import { SORT_OPTIONS } from '@/lib/constants';

describe('SORT_OPTIONS Migration', () => {
  it('should have labelKey instead of label property', () => {
    SORT_OPTIONS.forEach((option) => {
      expect(option).toHaveProperty('labelKey');
      expect(option).not.toHaveProperty('label');
    });
  });

  it('should have correct translation key format', () => {
    const expectedKeys = ['sort.date', 'sort.tinkering-index', 'sort.category', 'sort.title'];

    const actualKeys = SORT_OPTIONS.map((option) => option.labelKey);
    expect(actualKeys).toEqual(expectedKeys);
  });

  it('should maintain value and order properties', () => {
    expect(SORT_OPTIONS[0]).toEqual({
      value: 'date',
      labelKey: 'sort.date',
      order: 'desc',
    });

    expect(SORT_OPTIONS[1]).toEqual({
      value: 'tinkering_index',
      labelKey: 'sort.tinkering-index',
      order: 'desc',
    });

    expect(SORT_OPTIONS[2]).toEqual({
      value: 'category',
      labelKey: 'sort.category',
      order: 'asc',
    });

    expect(SORT_OPTIONS[3]).toEqual({
      value: 'title',
      labelKey: 'sort.title',
      order: 'asc',
    });
  });

  it('should be usable with translation function', () => {
    // Mock translation function
    const mockTranslations = {
      'sort.date': '發布日期',
      'sort.tinkering-index': '技術深度',
      'sort.category': '分類',
      'sort.title': '標題',
    };

    const t = (key: string) => mockTranslations[key as keyof typeof mockTranslations] || key;

    // Simulate component usage
    const translatedOptions = SORT_OPTIONS.map((option) => ({
      ...option,
      label: t(option.labelKey),
    }));

    expect(translatedOptions[0].label).toBe('發布日期');
    expect(translatedOptions[1].label).toBe('技術深度');
    expect(translatedOptions[2].label).toBe('分類');
    expect(translatedOptions[3].label).toBe('標題');
  });
});
