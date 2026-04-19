/**
 * Unit tests for the translation validation script
 *
 * Tests the core validation functions to ensure they correctly identify
 * translation issues like missing keys, empty values, and interpolation mismatches.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock fs module for testing
vi.mock('fs', () => ({
  existsSync: vi.fn(),
  readFileSync: vi.fn(),
}));

// Import the functions after mocking
import * as fs from 'fs';
import { validateTranslations } from '../../../scripts/validate-translations';

const mockFs = fs as any;

describe('Translation Validation Script', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('validateTranslations', () => {
    it('should pass validation when translations are complete and consistent', () => {
      // Mock file system calls
      mockFs.existsSync.mockReturnValue(true);

      const zhTWContent = JSON.stringify({
        nav: {
          articles: '文章',
          settings: '設定',
        },
        messages: {
          'article-count': '成功抓取 {count} 篇新文章',
          loading: '載入中...',
        },
      });

      const enUSContent = JSON.stringify({
        nav: {
          articles: 'Articles',
          settings: 'Settings',
        },
        messages: {
          'article-count': 'Successfully fetched {count} new articles',
          loading: 'Loading...',
        },
      });

      mockFs.readFileSync
        .mockReturnValueOnce(zhTWContent) // First call for zh-TW
        .mockReturnValueOnce(enUSContent); // Second call for en-US

      const result = validateTranslations();

      expect(result.issues).toHaveLength(0);
      expect(result.totalKeys.zhTW).toBe(4);
      expect(result.totalKeys.enUS).toBe(4);
      expect(result.summary.missingKeys).toBe(0);
      expect(result.summary.emptyValues).toBe(0);
      expect(result.summary.interpolationMismatches).toBe(0);
      expect(result.summary.duplicateKeys).toBe(0);
    });

    it('should detect missing keys', () => {
      mockFs.existsSync.mockReturnValue(true);

      const zhTWContent = JSON.stringify({
        nav: {
          articles: '文章',
          settings: '設定',
          'missing-in-en': '僅在中文',
        },
      });

      const enUSContent = JSON.stringify({
        nav: {
          articles: 'Articles',
          settings: 'Settings',
        },
      });

      mockFs.readFileSync.mockReturnValueOnce(zhTWContent).mockReturnValueOnce(enUSContent);

      const result = validateTranslations();

      expect(result.issues).toHaveLength(1);
      expect(result.issues[0]).toMatchObject({
        key: 'nav.missing-in-en',
        issue: 'missing',
        language: 'en-US',
      });
      expect(result.summary.missingKeys).toBe(1);
    });

    it('should detect empty values', () => {
      mockFs.existsSync.mockReturnValue(true);

      const zhTWContent = JSON.stringify({
        nav: {
          articles: '文章',
          empty: '',
        },
      });

      const enUSContent = JSON.stringify({
        nav: {
          articles: 'Articles',
          empty: 'Not Empty',
        },
      });

      mockFs.readFileSync.mockReturnValueOnce(zhTWContent).mockReturnValueOnce(enUSContent);

      const result = validateTranslations();

      expect(result.issues).toHaveLength(1);
      expect(result.issues[0]).toMatchObject({
        key: 'nav.empty',
        issue: 'empty',
        language: 'zh-TW',
      });
      expect(result.summary.emptyValues).toBe(1);
    });

    it('should detect interpolation variable mismatches', () => {
      mockFs.existsSync.mockReturnValue(true);

      const zhTWContent = JSON.stringify({
        messages: {
          'article-count': '成功抓取 {count} 篇新文章',
        },
      });

      const enUSContent = JSON.stringify({
        messages: {
          'article-count': 'Successfully fetched {number} new articles',
        },
      });

      mockFs.readFileSync.mockReturnValueOnce(zhTWContent).mockReturnValueOnce(enUSContent);

      const result = validateTranslations();

      expect(result.issues).toHaveLength(1);
      expect(result.issues[0]).toMatchObject({
        key: 'messages.article-count',
        issue: 'interpolation-mismatch',
        expected: ['count'],
        actual: ['number'],
      });
      expect(result.summary.interpolationMismatches).toBe(1);
    });

    it('should handle multiple interpolation variables', () => {
      mockFs.existsSync.mockReturnValue(true);

      const zhTWContent = JSON.stringify({
        messages: {
          'user-stats': '用戶 {name} 有 {count} 篇文章和 {likes} 個讚',
        },
      });

      const enUSContent = JSON.stringify({
        messages: {
          'user-stats': 'User {name} has {count} articles and {likes} likes',
        },
      });

      mockFs.readFileSync.mockReturnValueOnce(zhTWContent).mockReturnValueOnce(enUSContent);

      const result = validateTranslations();

      expect(result.issues).toHaveLength(0);
      expect(result.summary.interpolationMismatches).toBe(0);
    });

    it('should detect missing interpolation variables', () => {
      mockFs.existsSync.mockReturnValue(true);

      const zhTWContent = JSON.stringify({
        messages: {
          'user-stats': '用戶 {name} 有 {count} 篇文章',
        },
      });

      const enUSContent = JSON.stringify({
        messages: {
          'user-stats': 'User has articles', // Missing both variables
        },
      });

      mockFs.readFileSync.mockReturnValueOnce(zhTWContent).mockReturnValueOnce(enUSContent);

      const result = validateTranslations();

      expect(result.issues).toHaveLength(1);
      expect(result.issues[0]).toMatchObject({
        key: 'messages.user-stats',
        issue: 'interpolation-mismatch',
        expected: ['count', 'name'],
        actual: [],
      });
    });

    it('should handle nested object structures', () => {
      mockFs.existsSync.mockReturnValue(true);

      const zhTWContent = JSON.stringify({
        pages: {
          login: {
            title: '登入',
            form: {
              username: '使用者名稱',
              password: '密碼',
            },
          },
        },
      });

      const enUSContent = JSON.stringify({
        pages: {
          login: {
            title: 'Login',
            form: {
              username: 'Username',
              password: 'Password',
            },
          },
        },
      });

      mockFs.readFileSync.mockReturnValueOnce(zhTWContent).mockReturnValueOnce(enUSContent);

      const result = validateTranslations();

      expect(result.issues).toHaveLength(0);
      expect(result.totalKeys.zhTW).toBe(3);
      expect(result.totalKeys.enUS).toBe(3);
    });
  });
});
