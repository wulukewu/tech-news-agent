/**
 * Unit tests for OPML utilities
 *
 * Validates: Requirements 4.9
 * - THE Feed_Management_Dashboard SHALL support importing/exporting OPML files for feed management
 */

import { describe, it, expect } from 'vitest';
import {
  exportToOPML,
  parseOPML,
  validateOPML,
  type OPMLOutline,
} from '@/features/subscriptions/utils/opml';
import type { Feed } from '@/types/feed';

describe('OPML Utilities', () => {
  const mockFeeds: Feed[] = [
    {
      id: '1',
      name: 'Tech Blog',
      url: 'https://example.com/feed.xml',
      category: 'Technology',
      is_subscribed: true,
    },
    {
      id: '2',
      name: 'AI News',
      url: 'https://ai-news.com/rss',
      category: 'AI',
      is_subscribed: true,
    },
  ];

  describe('exportToOPML', () => {
    it('should export feeds to valid OPML format', () => {
      const opml = exportToOPML(mockFeeds);

      expect(opml).toContain('<?xml version="1.0" encoding="UTF-8"?>');
      expect(opml).toContain('<opml version="2.0">');
      expect(opml).toContain('<head>');
      expect(opml).toContain('<body>');
      expect(opml).toContain('</opml>');
    });

    it('should include all feed information in OPML', () => {
      const opml = exportToOPML(mockFeeds);

      mockFeeds.forEach((feed) => {
        expect(opml).toContain(feed.name);
        expect(opml).toContain(feed.url);
        expect(opml).toContain(feed.category);
      });
    });

    it('should escape XML special characters', () => {
      const feedsWithSpecialChars: Feed[] = [
        {
          id: '1',
          name: 'Tech & AI <Blog>',
          url: 'https://example.com/feed.xml',
          category: 'Tech & AI',
          is_subscribed: true,
        },
      ];

      const opml = exportToOPML(feedsWithSpecialChars);

      expect(opml).toContain('&amp;');
      expect(opml).toContain('&lt;');
      expect(opml).toContain('&gt;');
    });

    it('should include custom title in OPML', () => {
      const customTitle = 'My Custom Subscriptions';
      const opml = exportToOPML(mockFeeds, customTitle);

      expect(opml).toContain(`<title>${customTitle}</title>`);
    });

    it('should handle empty feed list', () => {
      const opml = exportToOPML([]);

      expect(opml).toContain('<opml version="2.0">');
      expect(opml).toContain('<body>');
      expect(opml).toContain('</body>');
    });
  });

  describe('parseOPML', () => {
    it('should parse valid OPML content', () => {
      const opmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>Test Subscriptions</title>
  </head>
  <body>
    <outline text="Tech Blog" title="Tech Blog" type="rss" xmlUrl="https://example.com/feed.xml" category="Technology" />
    <outline text="AI News" title="AI News" type="rss" xmlUrl="https://ai-news.com/rss" category="AI" />
  </body>
</opml>`;

      const feeds = parseOPML(opmlContent);

      expect(feeds).toHaveLength(2);
      expect(feeds[0].text).toBe('Tech Blog');
      expect(feeds[0].xmlUrl).toBe('https://example.com/feed.xml');
      expect(feeds[0].category).toBe('Technology');
      expect(feeds[1].text).toBe('AI News');
      expect(feeds[1].xmlUrl).toBe('https://ai-news.com/rss');
    });

    it('should handle OPML with missing optional attributes', () => {
      const opmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <body>
    <outline text="Simple Feed" xmlUrl="https://example.com/feed.xml" />
  </body>
</opml>`;

      const feeds = parseOPML(opmlContent);

      expect(feeds).toHaveLength(1);
      expect(feeds[0].text).toBe('Simple Feed');
      expect(feeds[0].xmlUrl).toBe('https://example.com/feed.xml');
      expect(feeds[0].category).toBeUndefined();
    });

    it('should ignore outlines without xmlUrl', () => {
      const opmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <body>
    <outline text="Category" />
    <outline text="Valid Feed" xmlUrl="https://example.com/feed.xml" />
  </body>
</opml>`;

      const feeds = parseOPML(opmlContent);

      expect(feeds).toHaveLength(1);
      expect(feeds[0].text).toBe('Valid Feed');
    });

    it('should throw error for invalid XML', () => {
      const invalidXML = 'This is not valid XML';

      expect(() => parseOPML(invalidXML)).toThrow('Invalid OPML file format');
    });

    it('should use title attribute if text is missing', () => {
      const opmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <body>
    <outline title="Feed Title" xmlUrl="https://example.com/feed.xml" />
  </body>
</opml>`;

      const feeds = parseOPML(opmlContent);

      expect(feeds).toHaveLength(1);
      expect(feeds[0].text).toBe('Feed Title');
    });
  });

  describe('validateOPML', () => {
    it('should validate correct OPML', () => {
      const validOPML = `<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <body>
    <outline text="Feed" xmlUrl="https://example.com/feed.xml" />
  </body>
</opml>`;

      const result = validateOPML(validOPML);

      expect(result.valid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it('should reject invalid XML', () => {
      const invalidXML = 'Not XML';

      const result = validateOPML(invalidXML);

      expect(result.valid).toBe(false);
      expect(result.error).toBeDefined();
    });

    it('should reject OPML without root element', () => {
      const noRoot = `<?xml version="1.0" encoding="UTF-8"?>
<body>
  <outline text="Feed" xmlUrl="https://example.com/feed.xml" />
</body>`;

      const result = validateOPML(noRoot);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('OPML root element');
    });

    it('should reject OPML without body element', () => {
      const noBody = `<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head><title>Test</title></head>
</opml>`;

      const result = validateOPML(noBody);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('body element');
    });

    it('should reject OPML without any feeds', () => {
      const noFeeds = `<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <body>
    <outline text="Category" />
  </body>
</opml>`;

      const result = validateOPML(noFeeds);

      expect(result.valid).toBe(false);
      expect(result.error).toContain('No feeds found');
    });
  });

  describe('Round-trip conversion', () => {
    it('should maintain feed data through export and import', () => {
      // Export feeds to OPML
      const opml = exportToOPML(mockFeeds);

      // Parse the OPML back
      const parsedFeeds = parseOPML(opml);

      // Verify all feeds are present
      expect(parsedFeeds).toHaveLength(mockFeeds.length);

      // Verify feed data matches
      mockFeeds.forEach((originalFeed, index) => {
        const parsedFeed = parsedFeeds.find((f) => f.xmlUrl === originalFeed.url);
        expect(parsedFeed).toBeDefined();
        expect(parsedFeed?.text).toBe(originalFeed.name);
        expect(parsedFeed?.category).toBe(originalFeed.category);
      });
    });
  });
});
