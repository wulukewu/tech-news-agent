/**
 * Code Splitting Utilities Unit Tests
 * Requirements: 12.4
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  LoadingFallback,
  SkeletonFallback,
  preloadComponent,
  prefetchRoute,
} from '@/lib/performance/code-splitting';

describe('Code Splitting Utilities', () => {
  describe('LoadingFallback', () => {
    it('should render loading message', () => {
      render(<LoadingFallback message="Loading test..." />);
      expect(screen.getByText('Loading test...')).toBeInTheDocument();
    });

    it('should render default loading message', () => {
      render(<LoadingFallback />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('should render loading spinner', () => {
      const { container } = render(<LoadingFallback />);
      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });
  });

  describe('SkeletonFallback', () => {
    it('should render skeleton elements', () => {
      const { container } = render(<SkeletonFallback />);
      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  describe('preloadComponent', () => {
    it('should trigger component import', async () => {
      const mockImport = vi.fn().mockResolvedValue({ default: () => null });
      preloadComponent(mockImport);

      // Wait for next tick
      await new Promise((resolve) => setTimeout(resolve, 0));

      expect(mockImport).toHaveBeenCalled();
    });

    it('should handle import errors gracefully', async () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const mockImport = vi.fn().mockRejectedValue(new Error('Import failed'));

      preloadComponent(mockImport);

      // Wait for next tick
      await new Promise((resolve) => setTimeout(resolve, 0));

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'Failed to preload component:',
        expect.any(Error)
      );

      consoleWarnSpy.mockRestore();
    });
  });

  describe('prefetchRoute', () => {
    it('should create prefetch link element', () => {
      // Mock document.head.appendChild
      const appendChildSpy = vi.spyOn(document.head, 'appendChild');

      prefetchRoute('/test-route');

      expect(appendChildSpy).toHaveBeenCalled();
      const link = appendChildSpy.mock.calls[0][0] as HTMLLinkElement;
      expect(link.rel).toBe('prefetch');
      expect(link.href).toContain('/test-route');

      appendChildSpy.mockRestore();
    });
  });
});
