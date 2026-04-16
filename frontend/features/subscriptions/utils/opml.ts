/**
 * OPML Import/Export Utilities
 *
 * Provides functionality for importing and exporting feed subscriptions in OPML format
 *
 * Validates: Requirements 4.9
 * - THE Feed_Management_Dashboard SHALL support importing/exporting OPML files for feed management
 */

import type { Feed } from '@/types/feed';

export interface OPMLOutline {
  text: string;
  title?: string;
  type?: string;
  xmlUrl?: string;
  htmlUrl?: string;
  category?: string;
}

/**
 * Export feeds to OPML format
 */
export function exportToOPML(
  feeds: Feed[],
  title: string = 'Tech News Agent Subscriptions'
): string {
  const date = new Date().toUTCString();

  const outlines = feeds
    .map((feed) => {
      const escapedName = escapeXml(feed.name);
      const escapedUrl = escapeXml(feed.url);
      const escapedCategory = feed.category ? escapeXml(feed.category) : '';

      return `    <outline text="${escapedName}" title="${escapedName}" type="rss" xmlUrl="${escapedUrl}" htmlUrl="${escapedUrl}" category="${escapedCategory}" />`;
    })
    .join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>${escapeXml(title)}</title>
    <dateCreated>${date}</dateCreated>
    <dateModified>${date}</dateModified>
  </head>
  <body>
${outlines}
  </body>
</opml>`;
}

/**
 * Parse OPML file content and extract feeds
 */
export function parseOPML(opmlContent: string): OPMLOutline[] {
  const parser = new DOMParser();
  const doc = parser.parseFromString(opmlContent, 'text/xml');

  // Check for parsing errors
  const parserError = doc.querySelector('parsererror');
  if (parserError) {
    throw new Error('Invalid OPML file format');
  }

  const outlines = doc.querySelectorAll('outline[xmlUrl]');
  const feeds: OPMLOutline[] = [];

  outlines.forEach((outline) => {
    const xmlUrl = outline.getAttribute('xmlUrl');
    if (!xmlUrl) return;

    feeds.push({
      text: outline.getAttribute('text') || outline.getAttribute('title') || 'Untitled Feed',
      title: outline.getAttribute('title') || outline.getAttribute('text') || undefined,
      type: outline.getAttribute('type') || 'rss',
      xmlUrl,
      htmlUrl: outline.getAttribute('htmlUrl') || undefined,
      category: outline.getAttribute('category') || undefined,
    });
  });

  return feeds;
}

/**
 * Download OPML file
 */
export function downloadOPML(opmlContent: string, filename: string = 'subscriptions.opml'): void {
  const blob = new Blob([opmlContent], { type: 'text/xml;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Read OPML file from File object
 */
export function readOPMLFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      const content = e.target?.result;
      if (typeof content === 'string') {
        resolve(content);
      } else {
        reject(new Error('Failed to read file content'));
      }
    };

    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };

    reader.readAsText(file);
  });
}

/**
 * Escape XML special characters
 */
function escapeXml(unsafe: string): string {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

/**
 * Validate OPML file
 */
export function validateOPML(opmlContent: string): { valid: boolean; error?: string } {
  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(opmlContent, 'text/xml');

    const parserError = doc.querySelector('parsererror');
    if (parserError) {
      return { valid: false, error: 'Invalid XML format' };
    }

    const opmlElement = doc.querySelector('opml');
    if (!opmlElement) {
      return { valid: false, error: 'Missing OPML root element' };
    }

    const body = doc.querySelector('body');
    if (!body) {
      return { valid: false, error: 'Missing OPML body element' };
    }

    const outlines = doc.querySelectorAll('outline[xmlUrl]');
    if (outlines.length === 0) {
      return { valid: false, error: 'No feeds found in OPML file' };
    }

    return { valid: true };
  } catch (error) {
    return { valid: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}
