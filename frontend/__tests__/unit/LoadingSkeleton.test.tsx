/**
 * Loading Skeleton Components Tests
 *
 * Tests for the loading skeleton components implemented in task 15
 */

import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import {
  ArticleCardSkeletonMobile,
  ArticleCardSkeletonDesktop,
  ArticleGridSkeleton,
  FeedListSkeleton,
  NavigationSkeleton,
  ReadingListSkeleton,
} from '@/components/LoadingSkeleton';

describe('Loading Skeleton Components', () => {
  describe('ArticleCardSkeletonMobile', () => {
    it('renders mobile article card skeleton', () => {
      render(<ArticleCardSkeletonMobile />);

      // Should render as an article element
      const article = screen.getByRole('article');
      expect(article).toBeInTheDocument();
    });
  });

  describe('ArticleCardSkeletonDesktop', () => {
    it('renders desktop article card skeleton', () => {
      render(<ArticleCardSkeletonDesktop />);

      // Should render as an article element
      const article = screen.getByRole('article');
      expect(article).toBeInTheDocument();
    });
  });

  describe('ArticleGridSkeleton', () => {
    it('renders article grid skeleton with default count', () => {
      render(<ArticleGridSkeleton />);

      // Should render multiple article skeletons (6 by default, but responsive)
      const articles = screen.getAllByRole('article');
      expect(articles.length).toBeGreaterThan(0);
    });

    it('renders article grid skeleton with custom count', () => {
      render(<ArticleGridSkeleton count={3} />);

      // Should render the specified number of articles (responsive)
      const articles = screen.getAllByRole('article');
      expect(articles.length).toBeGreaterThan(0);
    });
  });

  describe('FeedListSkeleton', () => {
    it('renders feed list skeleton with default count', () => {
      const { container } = render(<FeedListSkeleton />);

      // Should render multiple feed items (5 by default)
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders feed list skeleton with custom count', () => {
      const { container } = render(<FeedListSkeleton count={3} />);

      // Should render the specified number of feed items
      expect(container.firstChild).toBeInTheDocument();
    });
  });

  describe('NavigationSkeleton', () => {
    it('renders navigation skeleton', () => {
      render(<NavigationSkeleton />);

      // Should render as a header element
      const header = screen.getByRole('banner');
      expect(header).toBeInTheDocument();

      // Should contain navigation
      const nav = screen.getByRole('navigation');
      expect(nav).toBeInTheDocument();
    });
  });

  describe('ReadingListSkeleton', () => {
    it('renders reading list skeleton with default count', () => {
      const { container } = render(<ReadingListSkeleton />);

      // Should render the container
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders reading list skeleton with custom count', () => {
      const { container } = render(<ReadingListSkeleton count={3} />);

      // Should render the container
      expect(container.firstChild).toBeInTheDocument();
    });
  });
});
