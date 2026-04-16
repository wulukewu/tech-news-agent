/**
 * Unit tests for RSS feed URL validation
 *
 * Validates: Requirements 4.4
 * - THE Feed_Management_Dashboard SHALL allow users to add custom RSS feeds with URL validation
 */

import { describe, it, expect } from 'vitest';

/**
 * URL validation function (extracted from AddCustomFeedDialog for testing)
 */
function validateUrl(url: string): boolean {
  try {
    const urlObj = new URL(url);
    return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
  } catch {
    return false;
  }
}

describe('RSS Feed URL Validation', () => {
  describe('Valid URLs', () => {
    it('should accept valid HTTP URLs', () => {
      expect(validateUrl('http://example.com/feed.xml')).toBe(true);
      expect(validateUrl('http://blog.example.com/rss')).toBe(true);
      expect(validateUrl('http://example.com:8080/feed')).toBe(true);
    });

    it('should accept valid HTTPS URLs', () => {
      expect(validateUrl('https://example.com/feed.xml')).toBe(true);
      expect(validateUrl('https://blog.example.com/rss')).toBe(true);
      expect(validateUrl('https://example.com:443/feed')).toBe(true);
    });

    it('should accept URLs with query parameters', () => {
      expect(validateUrl('https://example.com/feed?format=xml')).toBe(true);
      expect(validateUrl('https://example.com/feed?type=rss&limit=10')).toBe(true);
    });

    it('should accept URLs with fragments', () => {
      expect(validateUrl('https://example.com/feed#section')).toBe(true);
    });

    it('should accept URLs with paths', () => {
      expect(validateUrl('https://example.com/blog/feed.xml')).toBe(true);
      expect(validateUrl('https://example.com/category/tech/rss')).toBe(true);
    });

    it('should accept URLs with subdomains', () => {
      expect(validateUrl('https://blog.tech.example.com/feed')).toBe(true);
      expect(validateUrl('https://www.example.com/rss')).toBe(true);
    });
  });

  describe('Invalid URLs', () => {
    it('should reject empty strings', () => {
      expect(validateUrl('')).toBe(false);
    });

    it('should reject URLs without protocol', () => {
      expect(validateUrl('example.com/feed.xml')).toBe(false);
      expect(validateUrl('www.example.com/rss')).toBe(false);
    });

    it('should reject URLs with invalid protocols', () => {
      expect(validateUrl('ftp://example.com/feed.xml')).toBe(false);
      expect(validateUrl('file:///path/to/feed.xml')).toBe(false);
      expect(validateUrl('javascript:alert(1)')).toBe(false);
    });

    it('should reject malformed URLs', () => {
      expect(validateUrl('not a url')).toBe(false);
      expect(validateUrl('http://')).toBe(false);
      expect(validateUrl('https://')).toBe(false);
      // Note: 'http://.' is technically valid according to URL spec, so we skip this test
    });

    it('should reject URLs with spaces', () => {
      expect(validateUrl('http://example .com/feed')).toBe(false);
      expect(validateUrl('http://example.com /feed')).toBe(false);
    });

    it('should reject relative URLs', () => {
      expect(validateUrl('/feed.xml')).toBe(false);
      expect(validateUrl('../feed.xml')).toBe(false);
      expect(validateUrl('./feed.xml')).toBe(false);
    });
  });

  describe('Edge Cases', () => {
    it('should handle URLs with special characters', () => {
      expect(validateUrl('https://example.com/feed?title=Tech%20News')).toBe(true);
      expect(validateUrl('https://example.com/feed?q=AI%26ML')).toBe(true);
    });

    it('should handle URLs with authentication', () => {
      expect(validateUrl('https://user:pass@example.com/feed')).toBe(true);
    });

    it('should handle URLs with IP addresses', () => {
      expect(validateUrl('http://192.168.1.1/feed')).toBe(true);
      expect(validateUrl('https://127.0.0.1:8080/rss')).toBe(true);
    });

    it('should handle URLs with international domains', () => {
      expect(validateUrl('https://例え.jp/feed')).toBe(true);
      expect(validateUrl('https://münchen.de/rss')).toBe(true);
    });

    it('should handle very long URLs', () => {
      const longPath = 'a'.repeat(1000);
      expect(validateUrl(`https://example.com/${longPath}`)).toBe(true);
    });
  });

  describe('Common RSS Feed URL Patterns', () => {
    it('should accept common RSS feed URL patterns', () => {
      const commonPatterns = [
        'https://example.com/feed',
        'https://example.com/rss',
        'https://example.com/feed.xml',
        'https://example.com/rss.xml',
        'https://example.com/atom.xml',
        'https://example.com/index.xml',
        'https://example.com/blog/feed',
        'https://example.com/feeds/posts/default',
        'https://medium.com/feed/@username',
        'https://www.reddit.com/r/programming/.rss',
      ];

      commonPatterns.forEach((url) => {
        expect(validateUrl(url)).toBe(true);
      });
    });
  });
});
