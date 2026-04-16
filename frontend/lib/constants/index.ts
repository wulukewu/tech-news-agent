// API endpoints
export const API_ENDPOINTS = {
  ARTICLES: '/api/articles',
  ANALYSIS: '/api/analysis',
  RECOMMENDATIONS: '/api/recommendations',
  SUBSCRIPTIONS: '/api/subscriptions',
  USER: '/api/user',
  SYSTEM: '/api/system',
} as const;

// Application routes
export const ROUTES = {
  HOME: '/',
  ARTICLES: '/articles',
  RECOMMENDATIONS: '/recommendations',
  SUBSCRIPTIONS: '/subscriptions',
  ANALYTICS: '/analytics',
  SETTINGS: '/settings',
  SYSTEM_STATUS: '/system-status',
  AUTH: {
    LOGIN: '/',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
  },
} as const;

// UI constants
export const UI_CONSTANTS = {
  // Pagination
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,

  // Article browser
  MAX_ANALYSIS_BUTTONS_PER_PAGE: 5,
  MAX_READING_LIST_BUTTONS_PER_PAGE: 10,
  MAX_CATEGORY_FILTERS: 24,

  // Virtualization
  VIRTUAL_LIST_ITEM_HEIGHT: 200,
  VIRTUAL_LIST_OVERSCAN: 5,

  // Timeouts
  API_TIMEOUT: 30000, // 30 seconds
  ANALYSIS_TIMEOUT: 60000, // 60 seconds for AI analysis

  // Cache durations (in milliseconds)
  CACHE_DURATION: {
    SHORT: 5 * 60 * 1000, // 5 minutes
    MEDIUM: 15 * 60 * 1000, // 15 minutes
    LONG: 60 * 60 * 1000, // 1 hour
    VERY_LONG: 24 * 60 * 60 * 1000, // 24 hours
  },

  // Animation durations
  ANIMATION_DURATION: {
    FAST: 150,
    NORMAL: 200,
    SLOW: 300,
  },
} as const;

// Article categories
export const ARTICLE_CATEGORIES = [
  'tech',
  'ai',
  'web',
  'mobile',
  'devops',
  'security',
  'database',
  'frontend',
  'backend',
  'cloud',
  'blockchain',
  'iot',
  'data-science',
  'machine-learning',
  'cybersecurity',
  'programming',
  'software-engineering',
  'open-source',
  'startup',
  'product',
] as const;

// Tinkering index levels
export const TINKERING_INDEX_LEVELS = [
  { value: 1, label: '入門', description: '適合初學者' },
  { value: 2, label: '基礎', description: '需要基本知識' },
  { value: 3, label: '中級', description: '需要一定經驗' },
  { value: 4, label: '進階', description: '需要深度理解' },
  { value: 5, label: '專家', description: '需要專業知識' },
] as const;

// Sort options
export const SORT_OPTIONS = [
  { value: 'date', label: '發布日期', order: 'desc' },
  { value: 'tinkering_index', label: '技術深度', order: 'desc' },
  { value: 'category', label: '分類', order: 'asc' },
  { value: 'title', label: '標題', order: 'asc' },
] as const;

// Theme options
export const THEME_OPTIONS = [
  { value: 'light', label: '淺色模式' },
  { value: 'dark', label: '深色模式' },
  { value: 'system', label: '跟隨系統' },
] as const;

// Language options
export const LANGUAGE_OPTIONS = [
  { value: 'zh-TW', label: '繁體中文' },
  { value: 'en-US', label: 'English' },
] as const;

// Notification frequency options
export const NOTIFICATION_FREQUENCY_OPTIONS = [
  { value: 'immediate', label: '即時通知' },
  { value: 'daily', label: '每日摘要' },
  { value: 'weekly', label: '每週摘要' },
  { value: 'disabled', label: '關閉通知' },
] as const;

// Error messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: '網路連線異常，請檢查您的網路設定',
  ANALYSIS_TIMEOUT: 'AI 分析處理時間過長，請稍後再試',
  INSUFFICIENT_PERMISSIONS: '您沒有執行此操作的權限',
  RATE_LIMIT_EXCEEDED: '請求過於頻繁，請稍後再試',
  INVALID_INPUT: '輸入資料格式不正確',
  SERVER_ERROR: '伺服器發生錯誤，請稍後再試',
  NOT_FOUND: '找不到請求的資源',
  UNAUTHORIZED: '請先登入後再進行此操作',
} as const;

// Success messages
export const SUCCESS_MESSAGES = {
  ARTICLE_SAVED: '文章已加入閱讀清單',
  ARTICLE_REMOVED: '文章已從閱讀清單移除',
  SETTINGS_SAVED: '設定已儲存',
  ANALYSIS_COPIED: '分析內容已複製到剪貼簿',
  SUBSCRIPTION_ADDED: '訂閱已新增',
  SUBSCRIPTION_REMOVED: '訂閱已移除',
} as const;

// Local storage keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  USER_PREFERENCES: 'user_preferences',
  THEME: 'theme',
  LANGUAGE: 'language',
  RECENT_SEARCHES: 'recent_searches',
  READING_PROGRESS: 'reading_progress',
} as const;
