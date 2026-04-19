/**
 * Unit Tests: Constant Migrations
 *
 * Tests that constants return correct translations in both languages and handle
 * variable interpolation correctly for dynamic content.
 *
 * **Validates: Requirements 6.4, 10.1, 10.4, 11.3**
 *
 * Task 8.6: Write unit tests for constant migrations
 * - Test constants return correct translations in both languages
 * - Test constants with variables (e.g., article-count) interpolate correctly
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { I18nProvider, useI18n } from '@/contexts/I18nContext';

// Import the migrated constants
import {
  TINKERING_INDEX_LEVELS,
  SORT_OPTIONS,
  THEME_OPTIONS,
  NOTIFICATION_FREQUENCY_OPTIONS,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
} from '@/lib/constants';

// Mock translation files with constant-related translations
const mockZhTWTranslations = {
  'tinkering-index': {
    'level-1': '入門',
    'level-1-desc': '適合初學者的基礎內容',
    'level-2': '基礎',
    'level-2-desc': '需要基本程式設計知識',
    'level-3': '中級',
    'level-3-desc': '需要一定的開發經驗',
    'level-4': '進階',
    'level-4-desc': '需要深度的技術理解',
    'level-5': '專家',
    'level-5-desc': '需要專業領域知識',
  },
  sort: {
    date: '發布日期',
    'tinkering-index': '技術深度',
    category: '分類',
    title: '標題',
    relevance: '相關性',
  },
  theme: {
    light: '淺色模式',
    dark: '深色模式',
    system: '跟隨系統',
    auto: '自動',
  },
  'notification-frequency': {
    immediate: '即時通知',
    daily: '每日摘要',
    weekly: '每週摘要',
    disabled: '關閉通知',
    monthly: '每月摘要',
  },
  errors: {
    'network-error': '網路連線異常，請檢查您的網路設定',
    'analysis-timeout': 'AI 分析處理時間過長，請稍後再試',
    'insufficient-permissions': '您沒有執行此操作的權限',
    'rate-limit-exceeded': '請求過於頻繁，請稍後再試',
    'invalid-input': '輸入資料格式不正確',
    'server-error': '伺服器發生錯誤，請稍後再試',
    'not-found': '找不到請求的資源',
    unauthorized: '請先登入後再進行此操作',
    'validation-failed': '資料驗證失敗',
    'file-too-large': '檔案大小超過限制',
  },
  success: {
    'article-saved': '文章已加入閱讀清單',
    'article-removed': '文章已從閱讀清單移除',
    'settings-saved': '設定已儲存',
    'analysis-copied': '分析內容已複製到剪貼簿',
    'subscription-added': '訂閱已新增',
    'subscription-removed': '訂閱已移除',
    'profile-updated': '個人資料已更新',
    'password-changed': '密碼已變更',
    'email-verified': '電子郵件已驗證',
    'backup-created': '備份已建立',
  },
  messages: {
    'article-count': '成功抓取 {count} 篇新文章',
    'user-count': '目前有 {count} 位使用者在線',
    'processing-time': '處理時間：{time} 秒',
    'file-size': '檔案大小：{size} MB',
    progress: '進度：{current}/{total} ({percentage}%)',
  },
};

const mockEnUSTranslations = {
  'tinkering-index': {
    'level-1': 'Beginner',
    'level-1-desc': 'Basic content suitable for beginners',
    'level-2': 'Basic',
    'level-2-desc': 'Requires basic programming knowledge',
    'level-3': 'Intermediate',
    'level-3-desc': 'Requires some development experience',
    'level-4': 'Advanced',
    'level-4-desc': 'Requires deep technical understanding',
    'level-5': 'Expert',
    'level-5-desc': 'Requires specialized domain knowledge',
  },
  sort: {
    date: 'Publication Date',
    'tinkering-index': 'Technical Depth',
    category: 'Category',
    title: 'Title',
    relevance: 'Relevance',
  },
  theme: {
    light: 'Light Mode',
    dark: 'Dark Mode',
    system: 'Follow System',
    auto: 'Auto',
  },
  'notification-frequency': {
    immediate: 'Immediate',
    daily: 'Daily Digest',
    weekly: 'Weekly Digest',
    disabled: 'Disabled',
    monthly: 'Monthly Digest',
  },
  errors: {
    'network-error': 'Network connection error. Please check your internet connection',
    'analysis-timeout': 'AI analysis took too long. Please try again later',
    'insufficient-permissions': 'You do not have permission to perform this action',
    'rate-limit-exceeded': 'Too many requests. Please try again later',
    'invalid-input': 'Invalid input data format',
    'server-error': 'Server error occurred. Please try again later',
    'not-found': 'Requested resource not found',
    unauthorized: 'Please log in to perform this action',
    'validation-failed': 'Data validation failed',
    'file-too-large': 'File size exceeds limit',
  },
  success: {
    'article-saved': 'Article added to reading list',
    'article-removed': 'Article removed from reading list',
    'settings-saved': 'Settings saved successfully',
    'analysis-copied': 'Analysis content copied to clipboard',
    'subscription-added': 'Subscription added successfully',
    'subscription-removed': 'Subscription removed successfully',
    'profile-updated': 'Profile updated successfully',
    'password-changed': 'Password changed successfully',
    'email-verified': 'Email verified successfully',
    'backup-created': 'Backup created successfully',
  },
  messages: {
    'article-count': 'Successfully fetched {count} new articles',
    'user-count': 'Currently {count} users online',
    'processing-time': 'Processing time: {time} seconds',
    'file-size': 'File size: {size} MB',
    progress: 'Progress: {current}/{total} ({percentage}%)',
  },
};

vi.mock('@/locales/zh-TW.json', () => ({
  default: mockZhTWTranslations,
}));

vi.mock('@/locales/en-US.json', () => ({
  default: mockEnUSTranslations,
}));

describe('Constant Migrations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    document.documentElement.lang = '';

    // Set browser language to English for consistent initial state
    Object.defineProperty(window.navigator, 'language', {
      writable: true,
      configurable: true,
      value: 'en-US',
    });
  });

  describe('TINKERING_INDEX_LEVELS constant', () => {
    it('should return correct English translations for all levels', async () => {
      // Requirement 10.1: Constants should use translation system
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const { t } = result.current;

      // Test all tinkering index levels
      TINKERING_INDEX_LEVELS.forEach((level) => {
        const label = t(level.labelKey);
        const description = t(level.descriptionKey);

        expect(label).not.toBe(level.labelKey); // Should not return the key itself
        expect(description).not.toBe(level.descriptionKey);

        // Verify specific translations
        switch (level.value) {
          case 1:
            expect(label).toBe('Beginner');
            expect(description).toBe('Basic content suitable for beginners');
            break;
          case 2:
            expect(label).toBe('Basic');
            expect(description).toBe('Requires basic programming knowledge');
            break;
          case 3:
            expect(label).toBe('Intermediate');
            expect(description).toBe('Requires some development experience');
            break;
          case 4:
            expect(label).toBe('Advanced');
            expect(description).toBe('Requires deep technical understanding');
            break;
          case 5:
            expect(label).toBe('Expert');
            expect(description).toBe('Requires specialized domain knowledge');
            break;
        }
      });
    });

    it('should return correct Chinese translations for all levels', async () => {
      // Test Chinese translations
      localStorage.setItem('language', 'zh-TW');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const { t } = result.current;

      // Test all tinkering index levels in Chinese
      TINKERING_INDEX_LEVELS.forEach((level) => {
        const label = t(level.labelKey);
        const description = t(level.descriptionKey);

        expect(label).not.toBe(level.labelKey);
        expect(description).not.toBe(level.descriptionKey);

        // Verify specific Chinese translations
        switch (level.value) {
          case 1:
            expect(label).toBe('入門');
            expect(description).toBe('適合初學者的基礎內容');
            break;
          case 2:
            expect(label).toBe('基礎');
            expect(description).toBe('需要基本程式設計知識');
            break;
          case 3:
            expect(label).toBe('中級');
            expect(description).toBe('需要一定的開發經驗');
            break;
          case 4:
            expect(label).toBe('進階');
            expect(description).toBe('需要深度的技術理解');
            break;
          case 5:
            expect(label).toBe('專家');
            expect(description).toBe('需要專業領域知識');
            break;
        }
      });
    });

    it('should maintain correct structure after migration', () => {
      // Verify constant structure is correct
      expect(Array.isArray(TINKERING_INDEX_LEVELS)).toBe(true);
      expect(TINKERING_INDEX_LEVELS).toHaveLength(5);

      TINKERING_INDEX_LEVELS.forEach((level, index) => {
        expect(level).toHaveProperty('value');
        expect(level).toHaveProperty('labelKey');
        expect(level).toHaveProperty('descriptionKey');
        expect(level.value).toBe(index + 1);
        expect(typeof level.labelKey).toBe('string');
        expect(typeof level.descriptionKey).toBe('string');
        expect(level.labelKey).toMatch(/^tinkering-index\.level-\d+$/);
        expect(level.descriptionKey).toMatch(/^tinkering-index\.level-\d+-desc$/);
      });
    });
  });

  describe('SORT_OPTIONS constant', () => {
    it('should return correct English translations for all sort options', async () => {
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const { t } = result.current;

      // Test all sort options
      SORT_OPTIONS.forEach((option) => {
        const label = t(option.labelKey);
        expect(label).not.toBe(option.labelKey);

        // Verify specific translations
        switch (option.value) {
          case 'date':
            expect(label).toBe('Publication Date');
            break;
          case 'tinkering-index':
            expect(label).toBe('Technical Depth');
            break;
          case 'category':
            expect(label).toBe('Category');
            break;
          case 'title':
            expect(label).toBe('Title');
            break;
        }
      });
    });

    it('should return correct Chinese translations for all sort options', async () => {
      localStorage.setItem('language', 'zh-TW');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const { t } = result.current;

      // Test all sort options in Chinese
      SORT_OPTIONS.forEach((option) => {
        const label = t(option.labelKey);
        expect(label).not.toBe(option.labelKey);

        // Verify specific Chinese translations
        switch (option.value) {
          case 'date':
            expect(label).toBe('發布日期');
            break;
          case 'tinkering-index':
            expect(label).toBe('技術深度');
            break;
          case 'category':
            expect(label).toBe('分類');
            break;
          case 'title':
            expect(label).toBe('標題');
            break;
        }
      });
    });
  });

  describe('THEME_OPTIONS constant', () => {
    it('should return correct English translations for all theme options', async () => {
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const { t } = result.current;

      // Test all theme options
      THEME_OPTIONS.forEach((option) => {
        const label = t(option.labelKey);
        expect(label).not.toBe(option.labelKey);

        // Verify specific translations
        switch (option.value) {
          case 'light':
            expect(label).toBe('Light Mode');
            break;
          case 'dark':
            expect(label).toBe('Dark Mode');
            break;
          case 'system':
            expect(label).toBe('Follow System');
            break;
        }
      });
    });

    it('should return correct Chinese translations for all theme options', async () => {
      localStorage.setItem('language', 'zh-TW');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const { t } = result.current;

      // Test all theme options in Chinese
      THEME_OPTIONS.forEach((option) => {
        const label = t(option.labelKey);
        expect(label).not.toBe(option.labelKey);

        // Verify specific Chinese translations
        switch (option.value) {
          case 'light':
            expect(label).toBe('淺色模式');
            break;
          case 'dark':
            expect(label).toBe('深色模式');
            break;
          case 'system':
            expect(label).toBe('跟隨系統');
            break;
        }
      });
    });
  });

  describe('NOTIFICATION_FREQUENCY_OPTIONS constant', () => {
    it('should return correct English translations for all notification frequency options', async () => {
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const { t } = result.current;

      // Test all notification frequency options
      NOTIFICATION_FREQUENCY_OPTIONS.forEach((option) => {
        const label = t(option.labelKey);
        expect(label).not.toBe(option.labelKey);

        // Verify specific translations
        switch (option.value) {
          case 'immediate':
            expect(label).toBe('Immediate');
            break;
          case 'daily':
            expect(label).toBe('Daily Digest');
            break;
          case 'weekly':
            expect(label).toBe('Weekly Digest');
            break;
          case 'disabled':
            expect(label).toBe('Disabled');
            break;
        }
      });
    });

    it('should return correct Chinese translations for all notification frequency options', async () => {
      localStorage.setItem('language', 'zh-TW');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const { t } = result.current;

      // Test all notification frequency options in Chinese
      NOTIFICATION_FREQUENCY_OPTIONS.forEach((option) => {
        const label = t(option.labelKey);
        expect(label).not.toBe(option.labelKey);

        // Verify specific Chinese translations
        switch (option.value) {
          case 'immediate':
            expect(label).toBe('即時通知');
            break;
          case 'daily':
            expect(label).toBe('每日摘要');
            break;
          case 'weekly':
            expect(label).toBe('每週摘要');
            break;
          case 'disabled':
            expect(label).toBe('關閉通知');
            break;
        }
      });
    });
  });

  describe('ERROR_MESSAGES constant', () => {
    it('should return correct English translations for all error messages', async () => {
      // Requirement 10.4: Error messages should use translation system
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const { t } = result.current;

      // Test all error messages
      Object.entries(ERROR_MESSAGES).forEach(([key, translationKey]) => {
        const message = t(translationKey);
        expect(message).not.toBe(translationKey);

        // Verify specific error message translations
        switch (key) {
          case 'NETWORK_ERROR':
            expect(message).toBe('Network connection error. Please check your internet connection');
            break;
          case 'ANALYSIS_TIMEOUT':
            expect(message).toBe('AI analysis took too long. Please try again later');
            break;
          case 'INSUFFICIENT_PERMISSIONS':
            expect(message).toBe('You do not have permission to perform this action');
            break;
          case 'UNAUTHORIZED':
            expect(message).toBe('Please log in to perform this action');
            break;
        }
      });
    });

    it('should return correct Chinese translations for all error messages', async () => {
      localStorage.setItem('language', 'zh-TW');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const { t } = result.current;

      // Test all error messages in Chinese
      Object.entries(ERROR_MESSAGES).forEach(([key, translationKey]) => {
        const message = t(translationKey);
        expect(message).not.toBe(translationKey);

        // Verify specific Chinese error message translations
        switch (key) {
          case 'NETWORK_ERROR':
            expect(message).toBe('網路連線異常，請檢查您的網路設定');
            break;
          case 'ANALYSIS_TIMEOUT':
            expect(message).toBe('AI 分析處理時間過長，請稍後再試');
            break;
          case 'INSUFFICIENT_PERMISSIONS':
            expect(message).toBe('您沒有執行此操作的權限');
            break;
          case 'UNAUTHORIZED':
            expect(message).toBe('請先登入後再進行此操作');
            break;
        }
      });
    });
  });

  describe('SUCCESS_MESSAGES constant', () => {
    it('should return correct English translations for all success messages', async () => {
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const { t } = result.current;

      // Test all success messages
      Object.entries(SUCCESS_MESSAGES).forEach(([key, translationKey]) => {
        const message = t(translationKey);
        expect(message).not.toBe(translationKey);

        // Verify specific success message translations
        switch (key) {
          case 'ARTICLE_SAVED':
            expect(message).toBe('Article added to reading list');
            break;
          case 'SETTINGS_SAVED':
            expect(message).toBe('Settings saved successfully');
            break;
          case 'SUBSCRIPTION_ADDED':
            expect(message).toBe('Subscription added successfully');
            break;
        }
      });
    });

    it('should return correct Chinese translations for all success messages', async () => {
      localStorage.setItem('language', 'zh-TW');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const { t } = result.current;

      // Test all success messages in Chinese
      Object.entries(SUCCESS_MESSAGES).forEach(([key, translationKey]) => {
        const message = t(translationKey);
        expect(message).not.toBe(translationKey);

        // Verify specific Chinese success message translations
        switch (key) {
          case 'ARTICLE_SAVED':
            expect(message).toBe('文章已加入閱讀清單');
            break;
          case 'SETTINGS_SAVED':
            expect(message).toBe('設定已儲存');
            break;
          case 'SUBSCRIPTION_ADDED':
            expect(message).toBe('訂閱已新增');
            break;
        }
      });
    });
  });

  describe('Variable Interpolation in Constants', () => {
    it('should handle variable interpolation correctly in English', async () => {
      // Requirement 6.4: Test interpolation with variables
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const { t } = result.current;

      // Test article count interpolation
      const articleCountMessage = t('messages.article-count', { count: 5 });
      expect(articleCountMessage).toBe('Successfully fetched 5 new articles');

      // Test user count interpolation
      const userCountMessage = t('messages.user-count', { count: 42 });
      expect(userCountMessage).toBe('Currently 42 users online');

      // Test processing time interpolation
      const processingTimeMessage = t('messages.processing-time', { time: 2.5 });
      expect(processingTimeMessage).toBe('Processing time: 2.5 seconds');

      // Test file size interpolation
      const fileSizeMessage = t('messages.file-size', { size: 15.7 });
      expect(fileSizeMessage).toBe('File size: 15.7 MB');

      // Test progress interpolation with multiple variables
      const progressMessage = t('messages.progress', { current: 7, total: 10, percentage: 70 });
      expect(progressMessage).toBe('Progress: 7/10 (70%)');
    });

    it('should handle variable interpolation correctly in Chinese', async () => {
      localStorage.setItem('language', 'zh-TW');

      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const { t } = result.current;

      // Test article count interpolation in Chinese
      const articleCountMessage = t('messages.article-count', { count: 5 });
      expect(articleCountMessage).toBe('成功抓取 5 篇新文章');

      // Test user count interpolation in Chinese
      const userCountMessage = t('messages.user-count', { count: 42 });
      expect(userCountMessage).toBe('目前有 42 位使用者在線');

      // Test processing time interpolation in Chinese
      const processingTimeMessage = t('messages.processing-time', { time: 2.5 });
      expect(processingTimeMessage).toBe('處理時間：2.5 秒');

      // Test file size interpolation in Chinese
      const fileSizeMessage = t('messages.file-size', { size: 15.7 });
      expect(fileSizeMessage).toBe('檔案大小：15.7 MB');

      // Test progress interpolation with multiple variables in Chinese
      const progressMessage = t('messages.progress', { current: 7, total: 10, percentage: 70 });
      expect(progressMessage).toBe('進度：7/10 (70%)');
    });

    it('should handle edge cases in variable interpolation', async () => {
      // Requirement 11.3: Test edge cases in interpolation
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const { t } = result.current;

      // Test with zero count
      const zeroCountMessage = t('messages.article-count', { count: 0 });
      expect(zeroCountMessage).toBe('Successfully fetched 0 new articles');

      // Test with large numbers
      const largeCountMessage = t('messages.user-count', { count: 1000000 });
      expect(largeCountMessage).toBe('Currently 1000000 users online');

      // Test with decimal numbers
      const decimalMessage = t('messages.processing-time', { time: 0.123 });
      expect(decimalMessage).toBe('Processing time: 0.123 seconds');

      // Test with negative numbers
      const negativeMessage = t('messages.processing-time', { time: -1 });
      expect(negativeMessage).toBe('Processing time: -1 seconds');
    });

    it('should handle missing variables gracefully', async () => {
      const { result } = renderHook(() => useI18n(), {
        wrapper: I18nProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const { t } = result.current;

      // Test with missing variable - should leave placeholder unchanged
      const missingVariableMessage = t('messages.article-count', {});
      expect(missingVariableMessage).toBe('Successfully fetched {count} new articles');

      // Test with partial variables
      const partialVariableMessage = t('messages.progress', { current: 5, total: 10 });
      expect(partialVariableMessage).toBe('Progress: 5/10 ({percentage}%)');
    });
  });

  describe('Constant Structure Validation', () => {
    it('should maintain proper constant structure after migration', () => {
      // Verify all constants have the expected structure
      expect(Array.isArray(TINKERING_INDEX_LEVELS)).toBe(true);
      expect(Array.isArray(SORT_OPTIONS)).toBe(true);
      expect(Array.isArray(THEME_OPTIONS)).toBe(true);
      expect(Array.isArray(NOTIFICATION_FREQUENCY_OPTIONS)).toBe(true);
      expect(typeof ERROR_MESSAGES).toBe('object');
      expect(typeof SUCCESS_MESSAGES).toBe('object');

      // Verify constants are not empty
      expect(TINKERING_INDEX_LEVELS.length).toBeGreaterThan(0);
      expect(SORT_OPTIONS.length).toBeGreaterThan(0);
      expect(THEME_OPTIONS.length).toBeGreaterThan(0);
      expect(NOTIFICATION_FREQUENCY_OPTIONS.length).toBeGreaterThan(0);
      expect(Object.keys(ERROR_MESSAGES).length).toBeGreaterThan(0);
      expect(Object.keys(SUCCESS_MESSAGES).length).toBeGreaterThan(0);
    });

    it('should use translation keys instead of hardcoded text', () => {
      // Verify that constants use translation keys, not hardcoded text
      TINKERING_INDEX_LEVELS.forEach((level) => {
        expect(level.labelKey).toMatch(/^tinkering-index\./);
        expect(level.descriptionKey).toMatch(/^tinkering-index\./);
        // Should not contain hardcoded Chinese or English text
        expect(level.labelKey).not.toMatch(/[一-龯]/); // Chinese characters
        expect(level.labelKey).not.toMatch(/^[A-Z][a-z]/); // English words
      });

      SORT_OPTIONS.forEach((option) => {
        expect(option.labelKey).toMatch(/^sort\./);
        expect(option.labelKey).not.toMatch(/[一-龯]/);
        expect(option.labelKey).not.toMatch(/^[A-Z][a-z]/);
      });

      Object.values(ERROR_MESSAGES).forEach((translationKey) => {
        expect(translationKey).toMatch(/^errors\./);
        expect(translationKey).not.toMatch(/[一-龯]/);
      });

      Object.values(SUCCESS_MESSAGES).forEach((translationKey) => {
        expect(translationKey).toMatch(/^success\./);
        expect(translationKey).not.toMatch(/[一-龯]/);
      });
    });
  });
});
