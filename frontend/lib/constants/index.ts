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

// Category color mapping (Req 24.1, 24.2, 24.5)
// Colors maintain WCAG AA contrast ratios in both light and dark modes
export const CATEGORY_COLORS = {
  // Primary categories with defined colors
  'tech-news': {
    light: '#3B82F6', // blue-500
    dark: '#60A5FA', // blue-400
    label: 'Tech News',
  },
  'ai-ml': {
    light: '#A855F7', // purple-500
    dark: '#C084FC', // purple-400
    label: 'AI/ML',
  },
  'web-dev': {
    light: '#10B981', // green-500
    dark: '#34D399', // green-400
    label: 'Web Dev',
  },
  devops: {
    light: '#F97316', // orange-500
    dark: '#FB923C', // orange-400
    label: 'DevOps',
  },
  security: {
    light: '#EF4444', // red-500
    dark: '#F87171', // red-400
    label: 'Security',
  },
  // Additional categories with semantic colors
  mobile: {
    light: '#8B5CF6', // violet-500
    dark: '#A78BFA', // violet-400
    label: 'Mobile',
  },
  database: {
    light: '#06B6D4', // cyan-500
    dark: '#22D3EE', // cyan-400
    label: 'Database',
  },
  cloud: {
    light: '#0EA5E9', // sky-500
    dark: '#38BDF8', // sky-400
    label: 'Cloud',
  },
  blockchain: {
    light: '#F59E0B', // amber-500
    dark: '#FCD34D', // amber-300
    label: 'Blockchain',
  },
  // Fallback for unknown categories (Req 24.7)
  default: {
    light: '#6B7280', // gray-500
    dark: '#9CA3AF', // gray-400
    label: 'Other',
  },
} as const;

// Category aliases for flexible matching (Req 24.6)
export const CATEGORY_ALIASES: Record<string, keyof typeof CATEGORY_COLORS> = {
  tech: 'tech-news',
  'tech-news': 'tech-news',
  ai: 'ai-ml',
  'ai-ml': 'ai-ml',
  'machine-learning': 'ai-ml',
  'data-science': 'ai-ml',
  web: 'web-dev',
  'web-dev': 'web-dev',
  frontend: 'web-dev',
  backend: 'web-dev',
  devops: 'devops',
  security: 'security',
  cybersecurity: 'security',
  mobile: 'mobile',
  database: 'database',
  cloud: 'cloud',
  blockchain: 'blockchain',
  iot: 'default',
  programming: 'default',
  'software-engineering': 'default',
  'open-source': 'default',
  startup: 'default',
  product: 'default',
} as const;

// Tinkering index levels
export const TINKERING_INDEX_LEVELS = [
  { value: 1, labelKey: 'tinkering-index.level-1', descriptionKey: 'tinkering-index.level-1-desc' },
  { value: 2, labelKey: 'tinkering-index.level-2', descriptionKey: 'tinkering-index.level-2-desc' },
  { value: 3, labelKey: 'tinkering-index.level-3', descriptionKey: 'tinkering-index.level-3-desc' },
  { value: 4, labelKey: 'tinkering-index.level-4', descriptionKey: 'tinkering-index.level-4-desc' },
  { value: 5, labelKey: 'tinkering-index.level-5', descriptionKey: 'tinkering-index.level-5-desc' },
] as const;

// Sort options
export const SORT_OPTIONS = [
  { value: 'date', labelKey: 'sort.date', order: 'desc' },
  { value: 'tinkering_index', labelKey: 'sort.tinkering-index', order: 'desc' },
  { value: 'category', labelKey: 'sort.category', order: 'asc' },
  { value: 'title', labelKey: 'sort.title', order: 'asc' },
] as const;

// Theme options
export const THEME_OPTIONS = [
  { value: 'light', labelKey: 'theme.light' },
  { value: 'dark', labelKey: 'theme.dark' },
  { value: 'system', labelKey: 'theme.system' },
] as const;

// Language options
export const LANGUAGE_OPTIONS = [
  { value: 'zh-TW', label: '繁體中文' },
  { value: 'en-US', label: 'English' },
] as const;

// Notification frequency options
export const NOTIFICATION_FREQUENCY_OPTIONS = [
  { value: 'immediate', labelKey: 'notification-frequency.immediate' },
  { value: 'daily', labelKey: 'notification-frequency.daily' },
  { value: 'weekly', labelKey: 'notification-frequency.weekly' },
  { value: 'disabled', labelKey: 'notification-frequency.disabled' },
] as const;

// Error messages (translation keys)
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'errors.network-error',
  ANALYSIS_TIMEOUT: 'errors.analysis-timeout',
  INSUFFICIENT_PERMISSIONS: 'errors.insufficient-permissions',
  RATE_LIMIT_EXCEEDED: 'errors.rate-limit-exceeded',
  INVALID_INPUT: 'errors.invalid-input',
  SERVER_ERROR: 'errors.server-error',
  NOT_FOUND: 'errors.not-found',
  UNAUTHORIZED: 'errors.unauthorized',
} as const;

// Success messages (translation keys)
export const SUCCESS_MESSAGES = {
  ARTICLE_SAVED: 'success.article-saved',
  ARTICLE_REMOVED: 'success.article-removed',
  SETTINGS_SAVED: 'success.settings-saved',
  ANALYSIS_COPIED: 'success.analysis-copied',
  SUBSCRIPTION_ADDED: 'success.subscription-added',
  SUBSCRIPTION_REMOVED: 'success.subscription-removed',
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
