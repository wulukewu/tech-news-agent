import { describe, it, expect } from 'vitest';

describe('Basic Setup', () => {
  it('should have working test environment', () => {
    expect(true).toBe(true);
  });

  it('should have access to DOM environment', () => {
    expect(typeof document).toBe('object');
    expect(typeof window).toBe('object');
  });

  it('should support modern JavaScript features', () => {
    const testArray = [1, 2, 3];
    const doubled = testArray.map((x) => x * 2);
    expect(doubled).toEqual([2, 4, 6]);
  });
});
