/**
 * Integration Tests: Component Translation Updates
 *
 * Tests that common UI components (buttons, forms, notifications) properly update their displayed text
 * when the user switches languages. Verifies that all components show the correct translations in both zh-TW and en-US.
 *
 * **Validates: Requirements 3.4, 4.2, 4.3, 4.4, 11.4**
 *
 * Task 6.4: Write integration tests for component translation updates
 * - Test buttons display correct translations in both languages
 * - Test form labels update when language switches
 * - Test notifications display correct translations
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { I18nProvider } from '@/contexts/I18nContext';

// Mock translation files with comprehensive component translations
const mockZhTWTranslations = {
  buttons: {
    save: '儲存',
    cancel: '取消',
    delete: '刪除',
    edit: '編輯',
    add: '新增',
    remove: '移除',
    confirm: '確認',
    close: '關閉',
    submit: '提交',
    reset: '重設',
    'add-to-list': '加入清單',
    'remove-from-list': '從清單移除',
    'copy-link': '複製連結',
    'share-article': '分享文章',
  },
  forms: {
    labels: {
      title: '標題',
      description: '描述',
      category: '分類',
      tags: '標籤',
      url: '網址',
      email: '電子郵件',
      password: '密碼',
      'confirm-password': '確認密碼',
      username: '使用者名稱',
      'notification-frequency': '通知頻率',
    },
    placeholders: {
      'enter-title': '請輸入標題',
      'enter-description': '請輸入描述',
      'enter-url': '請輸入網址',
      'search-articles': '搜尋文章...',
      'enter-email': '請輸入電子郵件',
      'enter-tags': '請輸入標籤，用逗號分隔',
    },
    validation: {
      required: '此欄位為必填',
      'invalid-email': '請輸入有效的電子郵件地址',
      'invalid-url': '請輸入有效的網址',
      'password-too-short': '密碼至少需要8個字元',
      'passwords-dont-match': '密碼不一致',
    },
  },
  notifications: {
    success: {
      'article-saved': '文章已加入閱讀清單',
      'article-removed': '文章已從閱讀清單移除',
      'settings-saved': '設定已儲存',
      'analysis-copied': '分析內容已複製到剪貼簿',
      'subscription-added': '訂閱已新增',
      'subscription-removed': '訂閱已移除',
      'profile-updated': '個人資料已更新',
      'password-changed': '密碼已變更',
    },
    error: {
      'network-error': '網路連線異常，請檢查您的網路設定',
      'analysis-timeout': 'AI 分析處理時間過長，請稍後再試',
      'insufficient-permissions': '您沒有執行此操作的權限',
      'rate-limit-exceeded': '請求過於頻繁，請稍後再試',
      'invalid-input': '輸入資料格式不正確',
      'server-error': '伺服器發生錯誤，請稍後再試',
      'not-found': '找不到請求的資源',
      unauthorized: '請先登入後再進行此操作',
    },
    info: {
      'loading-articles': '正在載入文章...',
      'analyzing-content': '正在分析內容...',
      'saving-changes': '正在儲存變更...',
      'processing-request': '正在處理請求...',
    },
    warning: {
      'unsaved-changes': '您有未儲存的變更',
      'delete-confirmation': '確定要刪除此項目嗎？',
      'logout-confirmation': '確定要登出嗎？',
    },
  },
  ui: {
    'loading-text': '載入中...',
    'no-results': '沒有找到結果',
    'try-again': '重試',
    'learn-more': '了解更多',
  },
};

const mockEnUSTranslations = {
  buttons: {
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    edit: 'Edit',
    add: 'Add',
    remove: 'Remove',
    confirm: 'Confirm',
    close: 'Close',
    submit: 'Submit',
    reset: 'Reset',
    'add-to-list': 'Add to List',
    'remove-from-list': 'Remove from List',
    'copy-link': 'Copy Link',
    'share-article': 'Share Article',
  },
  forms: {
    labels: {
      title: 'Title',
      description: 'Description',
      category: 'Category',
      tags: 'Tags',
      url: 'URL',
      email: 'Email',
      password: 'Password',
      'confirm-password': 'Confirm Password',
      username: 'Username',
      'notification-frequency': 'Notification Frequency',
    },
    placeholders: {
      'enter-title': 'Enter title',
      'enter-description': 'Enter description',
      'enter-url': 'Enter URL',
      'search-articles': 'Search articles...',
      'enter-email': 'Enter email address',
      'enter-tags': 'Enter tags, separated by commas',
    },
    validation: {
      required: 'This field is required',
      'invalid-email': 'Please enter a valid email address',
      'invalid-url': 'Please enter a valid URL',
      'password-too-short': 'Password must be at least 8 characters',
      'passwords-dont-match': 'Passwords do not match',
    },
  },
  notifications: {
    success: {
      'article-saved': 'Article added to reading list',
      'article-removed': 'Article removed from reading list',
      'settings-saved': 'Settings saved successfully',
      'analysis-copied': 'Analysis content copied to clipboard',
      'subscription-added': 'Subscription added successfully',
      'subscription-removed': 'Subscription removed successfully',
      'profile-updated': 'Profile updated successfully',
      'password-changed': 'Password changed successfully',
    },
    error: {
      'network-error': 'Network connection error. Please check your internet connection',
      'analysis-timeout': 'AI analysis took too long. Please try again later',
      'insufficient-permissions': 'You do not have permission to perform this action',
      'rate-limit-exceeded': 'Too many requests. Please try again later',
      'invalid-input': 'Invalid input data format',
      'server-error': 'Server error occurred. Please try again later',
      'not-found': 'Requested resource not found',
      unauthorized: 'Please log in to perform this action',
    },
    info: {
      'loading-articles': 'Loading articles...',
      'analyzing-content': 'Analyzing content...',
      'saving-changes': 'Saving changes...',
      'processing-request': 'Processing request...',
    },
    warning: {
      'unsaved-changes': 'You have unsaved changes',
      'delete-confirmation': 'Are you sure you want to delete this item?',
      'logout-confirmation': 'Are you sure you want to log out?',
    },
  },
  ui: {
    'loading-text': 'Loading...',
    'no-results': 'No results found',
    'try-again': 'Try Again',
    'learn-more': 'Learn More',
  },
};

vi.mock('@/locales/zh-TW.json', () => ({
  default: mockZhTWTranslations,
}));

vi.mock('@/locales/en-US.json', () => ({
  default: mockEnUSTranslations,
}));

// Test components that use translations
function TestButtonComponent() {
  const { t } = useI18n();

  return (
    <div>
      <button data-testid="save-button">{t('buttons.save')}</button>
      <button data-testid="cancel-button">{t('buttons.cancel')}</button>
      <button data-testid="delete-button">{t('buttons.delete')}</button>
      <button data-testid="add-button">{t('buttons.add')}</button>
      <button data-testid="edit-button">{t('buttons.edit')}</button>
      <button data-testid="confirm-button">{t('buttons.confirm')}</button>
      <button data-testid="add-to-list-button">{t('buttons.add-to-list')}</button>
      <button data-testid="copy-link-button">{t('buttons.copy-link')}</button>
    </div>
  );
}

function TestFormComponent() {
  const { t } = useI18n();

  return (
    <form>
      <div>
        <label htmlFor="title" data-testid="title-label">
          {t('forms.labels.title')}
        </label>
        <input
          id="title"
          type="text"
          placeholder={t('forms.placeholders.enter-title')}
          data-testid="title-input"
        />
      </div>
      <div>
        <label htmlFor="description" data-testid="description-label">
          {t('forms.labels.description')}
        </label>
        <textarea
          id="description"
          placeholder={t('forms.placeholders.enter-description')}
          data-testid="description-input"
        />
      </div>
      <div>
        <label htmlFor="email" data-testid="email-label">
          {t('forms.labels.email')}
        </label>
        <input
          id="email"
          type="email"
          placeholder={t('forms.placeholders.enter-email')}
          data-testid="email-input"
        />
      </div>
      <div>
        <label htmlFor="url" data-testid="url-label">
          {t('forms.labels.url')}
        </label>
        <input
          id="url"
          type="url"
          placeholder={t('forms.placeholders.enter-url')}
          data-testid="url-input"
        />
      </div>
      <div>
        <label htmlFor="tags" data-testid="tags-label">
          {t('forms.labels.tags')}
        </label>
        <input
          id="tags"
          type="text"
          placeholder={t('forms.placeholders.enter-tags')}
          data-testid="tags-input"
        />
      </div>
      <div data-testid="validation-required">{t('forms.validation.required')}</div>
      <div data-testid="validation-invalid-email">{t('forms.validation.invalid-email')}</div>
    </form>
  );
}

function TestNotificationComponent() {
  const { t } = useI18n();

  return (
    <div>
      {/* Success notifications */}
      <div data-testid="success-article-saved">{t('notifications.success.article-saved')}</div>
      <div data-testid="success-settings-saved">{t('notifications.success.settings-saved')}</div>
      <div data-testid="success-subscription-added">
        {t('notifications.success.subscription-added')}
      </div>

      {/* Error notifications */}
      <div data-testid="error-network-error">{t('notifications.error.network-error')}</div>
      <div data-testid="error-server-error">{t('notifications.error.server-error')}</div>
      <div data-testid="error-unauthorized">{t('notifications.error.unauthorized')}</div>

      {/* Info notifications */}
      <div data-testid="info-loading-articles">{t('notifications.info.loading-articles')}</div>
      <div data-testid="info-analyzing-content">{t('notifications.info.analyzing-content')}</div>

      {/* Warning notifications */}
      <div data-testid="warning-unsaved-changes">{t('notifications.warning.unsaved-changes')}</div>
      <div data-testid="warning-delete-confirmation">
        {t('notifications.warning.delete-confirmation')}
      </div>
    </div>
  );
}

// Import useI18n after mocking
import { useI18n } from '@/contexts/I18nContext';

describe('Component Translation Updates Integration', () => {
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

  describe('Button Component Translations', () => {
    it('should display all button labels in English initially', async () => {
      // Requirement 4.2: Button labels should be properly translated
      render(
        <I18nProvider>
          <TestButtonComponent />
        </I18nProvider>
      );

      // Wait for translations to load
      await waitFor(() => {
        expect(screen.getByTestId('save-button')).toHaveTextContent('Save');
      });

      // Check all button translations
      expect(screen.getByTestId('save-button')).toHaveTextContent('Save');
      expect(screen.getByTestId('cancel-button')).toHaveTextContent('Cancel');
      expect(screen.getByTestId('delete-button')).toHaveTextContent('Delete');
      expect(screen.getByTestId('add-button')).toHaveTextContent('Add');
      expect(screen.getByTestId('edit-button')).toHaveTextContent('Edit');
      expect(screen.getByTestId('confirm-button')).toHaveTextContent('Confirm');
      expect(screen.getByTestId('add-to-list-button')).toHaveTextContent('Add to List');
      expect(screen.getByTestId('copy-link-button')).toHaveTextContent('Copy Link');

      // Verify Chinese translations are not present
      expect(screen.queryByText('儲存')).not.toBeInTheDocument();
      expect(screen.queryByText('取消')).not.toBeInTheDocument();
      expect(screen.queryByText('刪除')).not.toBeInTheDocument();
    });

    it('should update all button labels when switching to Chinese', async () => {
      // Requirement 3.4: Update all UI text immediately without page reload
      const user = userEvent.setup();

      render(
        <I18nProvider>
          <TestButtonComponent />
        </I18nProvider>
      );

      // Wait for initial English translations
      await waitFor(() => {
        expect(screen.getByTestId('save-button')).toHaveTextContent('Save');
      });

      // Switch to Chinese by setting localStorage (simulating language switcher)
      localStorage.setItem('language', 'zh-TW');

      // Re-render to trigger language change
      const { rerender } = render(
        <I18nProvider>
          <TestButtonComponent />
        </I18nProvider>
      );

      // Wait for Chinese translations to load
      await waitFor(() => {
        expect(screen.getByTestId('save-button')).toHaveTextContent('儲存');
      });

      // Verify all button labels are translated to Chinese
      expect(screen.getByTestId('save-button')).toHaveTextContent('儲存');
      expect(screen.getByTestId('cancel-button')).toHaveTextContent('取消');
      expect(screen.getByTestId('delete-button')).toHaveTextContent('刪除');
      expect(screen.getByTestId('add-button')).toHaveTextContent('新增');
      expect(screen.getByTestId('edit-button')).toHaveTextContent('編輯');
      expect(screen.getByTestId('confirm-button')).toHaveTextContent('確認');
      expect(screen.getByTestId('add-to-list-button')).toHaveTextContent('加入清單');
      expect(screen.getByTestId('copy-link-button')).toHaveTextContent('複製連結');

      // Verify English translations are no longer present
      expect(screen.queryByText('Save')).not.toBeInTheDocument();
      expect(screen.queryByText('Cancel')).not.toBeInTheDocument();
      expect(screen.queryByText('Delete')).not.toBeInTheDocument();
    });

    it('should handle compound button labels correctly', async () => {
      // Test multi-word button labels
      render(
        <I18nProvider>
          <TestButtonComponent />
        </I18nProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('add-to-list-button')).toHaveTextContent('Add to List');
      });

      expect(screen.getByTestId('add-to-list-button')).toHaveTextContent('Add to List');
      expect(screen.getByTestId('copy-link-button')).toHaveTextContent('Copy Link');
    });
  });

  describe('Form Component Translations', () => {
    it('should display all form labels and placeholders in English initially', async () => {
      // Requirement 4.3: Form labels should be properly translated
      render(
        <I18nProvider>
          <TestFormComponent />
        </I18nProvider>
      );

      // Wait for translations to load
      await waitFor(() => {
        expect(screen.getByTestId('title-label')).toHaveTextContent('Title');
      });

      // Check form labels
      expect(screen.getByTestId('title-label')).toHaveTextContent('Title');
      expect(screen.getByTestId('description-label')).toHaveTextContent('Description');
      expect(screen.getByTestId('email-label')).toHaveTextContent('Email');
      expect(screen.getByTestId('url-label')).toHaveTextContent('URL');
      expect(screen.getByTestId('tags-label')).toHaveTextContent('Tags');

      // Check form placeholders
      expect(screen.getByTestId('title-input')).toHaveAttribute('placeholder', 'Enter title');
      expect(screen.getByTestId('description-input')).toHaveAttribute(
        'placeholder',
        'Enter description'
      );
      expect(screen.getByTestId('email-input')).toHaveAttribute(
        'placeholder',
        'Enter email address'
      );
      expect(screen.getByTestId('url-input')).toHaveAttribute('placeholder', 'Enter URL');
      expect(screen.getByTestId('tags-input')).toHaveAttribute(
        'placeholder',
        'Enter tags, separated by commas'
      );

      // Check validation messages
      expect(screen.getByTestId('validation-required')).toHaveTextContent('This field is required');
      expect(screen.getByTestId('validation-invalid-email')).toHaveTextContent(
        'Please enter a valid email address'
      );
    });

    it('should update all form labels and placeholders when switching to Chinese', async () => {
      // Test form translation updates
      localStorage.setItem('language', 'zh-TW');

      render(
        <I18nProvider>
          <TestFormComponent />
        </I18nProvider>
      );

      // Wait for Chinese translations to load
      await waitFor(() => {
        expect(screen.getByTestId('title-label')).toHaveTextContent('標題');
      });

      // Check form labels in Chinese
      expect(screen.getByTestId('title-label')).toHaveTextContent('標題');
      expect(screen.getByTestId('description-label')).toHaveTextContent('描述');
      expect(screen.getByTestId('email-label')).toHaveTextContent('電子郵件');
      expect(screen.getByTestId('url-label')).toHaveTextContent('網址');
      expect(screen.getByTestId('tags-label')).toHaveTextContent('標籤');

      // Check form placeholders in Chinese
      expect(screen.getByTestId('title-input')).toHaveAttribute('placeholder', '請輸入標題');
      expect(screen.getByTestId('description-input')).toHaveAttribute('placeholder', '請輸入描述');
      expect(screen.getByTestId('email-input')).toHaveAttribute('placeholder', '請輸入電子郵件');
      expect(screen.getByTestId('url-input')).toHaveAttribute('placeholder', '請輸入網址');
      expect(screen.getByTestId('tags-input')).toHaveAttribute(
        'placeholder',
        '請輸入標籤，用逗號分隔'
      );

      // Check validation messages in Chinese
      expect(screen.getByTestId('validation-required')).toHaveTextContent('此欄位為必填');
      expect(screen.getByTestId('validation-invalid-email')).toHaveTextContent(
        '請輸入有效的電子郵件地址'
      );
    });

    it('should handle complex form validation messages', async () => {
      // Test complex validation message translations
      render(
        <I18nProvider>
          <TestFormComponent />
        </I18nProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('validation-invalid-email')).toHaveTextContent(
          'Please enter a valid email address'
        );
      });

      // Verify complex validation messages
      expect(screen.getByTestId('validation-invalid-email')).toHaveTextContent(
        'Please enter a valid email address'
      );
    });
  });

  describe('Notification Component Translations', () => {
    it('should display all notification messages in English initially', async () => {
      // Requirement 4.4: Notification messages should be properly translated
      render(
        <I18nProvider>
          <TestNotificationComponent />
        </I18nProvider>
      );

      // Wait for translations to load
      await waitFor(() => {
        expect(screen.getByTestId('success-article-saved')).toHaveTextContent(
          'Article added to reading list'
        );
      });

      // Check success notifications
      expect(screen.getByTestId('success-article-saved')).toHaveTextContent(
        'Article added to reading list'
      );
      expect(screen.getByTestId('success-settings-saved')).toHaveTextContent(
        'Settings saved successfully'
      );
      expect(screen.getByTestId('success-subscription-added')).toHaveTextContent(
        'Subscription added successfully'
      );

      // Check error notifications
      expect(screen.getByTestId('error-network-error')).toHaveTextContent(
        'Network connection error. Please check your internet connection'
      );
      expect(screen.getByTestId('error-server-error')).toHaveTextContent(
        'Server error occurred. Please try again later'
      );
      expect(screen.getByTestId('error-unauthorized')).toHaveTextContent(
        'Please log in to perform this action'
      );

      // Check info notifications
      expect(screen.getByTestId('info-loading-articles')).toHaveTextContent('Loading articles...');
      expect(screen.getByTestId('info-analyzing-content')).toHaveTextContent(
        'Analyzing content...'
      );

      // Check warning notifications
      expect(screen.getByTestId('warning-unsaved-changes')).toHaveTextContent(
        'You have unsaved changes'
      );
      expect(screen.getByTestId('warning-delete-confirmation')).toHaveTextContent(
        'Are you sure you want to delete this item?'
      );
    });

    it('should update all notification messages when switching to Chinese', async () => {
      // Test notification translation updates
      localStorage.setItem('language', 'zh-TW');

      render(
        <I18nProvider>
          <TestNotificationComponent />
        </I18nProvider>
      );

      // Wait for Chinese translations to load
      await waitFor(() => {
        expect(screen.getByTestId('success-article-saved')).toHaveTextContent('文章已加入閱讀清單');
      });

      // Check success notifications in Chinese
      expect(screen.getByTestId('success-article-saved')).toHaveTextContent('文章已加入閱讀清單');
      expect(screen.getByTestId('success-settings-saved')).toHaveTextContent('設定已儲存');
      expect(screen.getByTestId('success-subscription-added')).toHaveTextContent('訂閱已新增');

      // Check error notifications in Chinese
      expect(screen.getByTestId('error-network-error')).toHaveTextContent(
        '網路連線異常，請檢查您的網路設定'
      );
      expect(screen.getByTestId('error-server-error')).toHaveTextContent(
        '伺服器發生錯誤，請稍後再試'
      );
      expect(screen.getByTestId('error-unauthorized')).toHaveTextContent('請先登入後再進行此操作');

      // Check info notifications in Chinese
      expect(screen.getByTestId('info-loading-articles')).toHaveTextContent('正在載入文章...');
      expect(screen.getByTestId('info-analyzing-content')).toHaveTextContent('正在分析內容...');

      // Check warning notifications in Chinese
      expect(screen.getByTestId('warning-unsaved-changes')).toHaveTextContent('您有未儲存的變更');
      expect(screen.getByTestId('warning-delete-confirmation')).toHaveTextContent(
        '確定要刪除此項目嗎？'
      );
    });

    it('should handle long notification messages correctly', async () => {
      // Test long notification messages
      render(
        <I18nProvider>
          <TestNotificationComponent />
        </I18nProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('error-network-error')).toHaveTextContent(
          'Network connection error. Please check your internet connection'
        );
      });

      // Verify long messages are displayed correctly
      expect(screen.getByTestId('error-network-error')).toHaveTextContent(
        'Network connection error. Please check your internet connection'
      );
    });
  });

  describe('Translation Completeness and Consistency', () => {
    it('should not display fallback keys for any component', async () => {
      // Requirement 11.4: Ensure no translation keys are displayed as fallback text
      render(
        <I18nProvider>
          <TestButtonComponent />
          <TestFormComponent />
          <TestNotificationComponent />
        </I18nProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('save-button')).toHaveTextContent('Save');
      });

      // Check that no translation keys are displayed as fallback text
      expect(screen.queryByText('buttons.save')).not.toBeInTheDocument();
      expect(screen.queryByText('forms.labels.title')).not.toBeInTheDocument();
      expect(screen.queryByText('notifications.success.article-saved')).not.toBeInTheDocument();
      expect(screen.queryByText('forms.placeholders.enter-title')).not.toBeInTheDocument();
      expect(screen.queryByText('notifications.error.network-error')).not.toBeInTheDocument();
    });

    it('should maintain translation consistency across component types', async () => {
      // Test that the same translation keys work across different component types
      localStorage.setItem('language', 'zh-TW');

      render(
        <I18nProvider>
          <TestButtonComponent />
          <TestFormComponent />
          <TestNotificationComponent />
        </I18nProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('save-button')).toHaveTextContent('儲存');
      });

      // Verify consistent translations across components
      expect(screen.getByTestId('save-button')).toHaveTextContent('儲存');
      expect(screen.getByTestId('title-label')).toHaveTextContent('標題');
      expect(screen.getByTestId('success-article-saved')).toHaveTextContent('文章已加入閱讀清單');
    });

    it('should handle special characters and punctuation in translations', async () => {
      // Test special characters in translations
      render(
        <I18nProvider>
          <TestNotificationComponent />
        </I18nProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('info-loading-articles')).toHaveTextContent(
          'Loading articles...'
        );
      });

      // Check that ellipsis and punctuation are preserved
      expect(screen.getByTestId('info-loading-articles')).toHaveTextContent('Loading articles...');
      expect(screen.getByTestId('warning-delete-confirmation')).toHaveTextContent(
        'Are you sure you want to delete this item?'
      );
    });
  });

  describe('Performance and Error Handling', () => {
    it('should handle rapid component re-renders during language switching', async () => {
      // Test performance during rapid re-renders
      const { rerender } = render(
        <I18nProvider>
          <TestButtonComponent />
        </I18nProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('save-button')).toHaveTextContent('Save');
      });

      // Simulate rapid re-renders
      for (let i = 0; i < 5; i++) {
        rerender(
          <I18nProvider>
            <TestButtonComponent />
          </I18nProvider>
        );
      }

      // Should still display correct translations
      expect(screen.getByTestId('save-button')).toHaveTextContent('Save');
      expect(screen.getByTestId('cancel-button')).toHaveTextContent('Cancel');
    });

    it('should handle missing translation gracefully', async () => {
      // Test graceful handling of missing translations
      function TestMissingTranslationComponent() {
        const { t } = useI18n();
        return <div data-testid="missing-key">{t('non.existent.key')}</div>;
      }

      render(
        <I18nProvider>
          <TestMissingTranslationComponent />
        </I18nProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('missing-key')).toBeInTheDocument();
      });

      // Should display the key itself as fallback
      expect(screen.getByTestId('missing-key')).toHaveTextContent('non.existent.key');
    });
  });
});
