import { logger } from '@/lib/utils/logger';
/**
 * Debug Utilities for Development
 * Requirements: 13.1, 13.4, 13.5
 */

import { apiLogger } from '@/lib/api/logger';

// Debug configuration
export const DEBUG_CONFIG = {
  enabled: process.env.NODE_ENV === 'development',
  logLevel: process.env.NEXT_PUBLIC_LOG_LEVEL || 'info',
  showPerformanceMetrics: true,
  showApiCalls: true,
  showStateChanges: true,
};

// Performance monitoring
class PerformanceMonitor {
  private marks: Map<string, number> = new Map();
  private measures: Map<string, number> = new Map();

  mark(name: string): void {
    if (!DEBUG_CONFIG.enabled || !DEBUG_CONFIG.showPerformanceMetrics) return;

    this.marks.set(name, performance.now());
    logger.debug(`🏁 Performance Mark: ${name} at ${this.marks.get(name)?.toFixed(2)}ms`);
  }

  measure(name: string, startMark: string, endMark?: string): number {
    if (!DEBUG_CONFIG.enabled || !DEBUG_CONFIG.showPerformanceMetrics) return 0;

    const startTime = this.marks.get(startMark);
    const endTime = endMark ? this.marks.get(endMark) : performance.now();

    if (!startTime) {
      logger.warn(`⚠️ Start mark "${startMark}" not found`);
      return 0;
    }

    const duration = (endTime || performance.now()) - startTime;
    this.measures.set(name, duration);

    logger.debug(`📊 Performance Measure: ${name} = ${duration.toFixed(2)}ms`);

    // Warn about slow operations
    if (duration > 1000) {
      logger.warn(`🐌 Slow operation detected: ${name} took ${duration.toFixed(2)}ms`);
    }

    return duration;
  }

  getMeasure(name: string): number | undefined {
    return this.measures.get(name);
  }

  getAllMeasures(): Record<string, number> {
    return Object.fromEntries(this.measures);
  }

  clear(): void {
    this.marks.clear();
    this.measures.clear();
  }
}

export const perfMonitor = new PerformanceMonitor();

// Enhanced console logging with context
export class DebugLogger {
  private context: string;

  constructor(context: string) {
    this.context = context;
  }

  private formatMessage(level: string, message: string, data?: any): void {
    if (!DEBUG_CONFIG.enabled) return;

    const timestamp = new Date().toISOString();
    const emoji = this.getLevelEmoji(level);

    console.group(`${emoji} [${timestamp}] ${this.context}: ${message}`);

    if (data) {
      logger.debug('Data:', data);
    }

    // Add stack trace for errors
    if (level === 'error') {
      console.trace('Stack trace:');
    }

    console.groupEnd();
  }

  private getLevelEmoji(level: string): string {
    const emojis: Record<string, string> = {
      debug: '🔍',
      info: 'ℹ️',
      warn: '⚠️',
      error: '❌',
      success: '✅',
    };
    return emojis[level] || 'ℹ️';
  }

  debug(message: string, data?: any): void {
    this.formatMessage('debug', message, data);
  }

  info(message: string, data?: any): void {
    this.formatMessage('info', message, data);
  }

  warn(message: string, data?: any): void {
    this.formatMessage('warn', message, data);
  }

  error(message: string, data?: any): void {
    this.formatMessage('error', message, data);

    // Send to API logger for persistence
    apiLogger.error(`[${this.context}] ${message}`, data);
  }

  success(message: string, data?: any): void {
    this.formatMessage('success', message, data);
  }
}

// API call debugging
export function debugApiCall(
  method: string,
  url: string,
  data?: any,
  response?: any,
  error?: any
): void {
  if (!DEBUG_CONFIG.enabled || !DEBUG_CONFIG.showApiCalls) return;

  const logger = new DebugLogger('API');

  if (error) {
    logger.error(`${method} ${url} failed`, {
      requestData: data,
      error: error.message,
      status: error.response?.status,
      responseData: error.response?.data,
    });
  } else {
    logger.info(`${method} ${url}`, {
      requestData: data,
      responseData: response,
      status: response?.status || 'success',
    });
  }
}

// State change debugging
export function debugStateChange(
  component: string,
  stateName: string,
  oldValue: any,
  newValue: any
): void {
  if (!DEBUG_CONFIG.enabled || !DEBUG_CONFIG.showStateChanges) return;

  const logger = new DebugLogger(`State:${component}`);

  logger.info(`${stateName} changed`, {
    from: oldValue,
    to: newValue,
    type: typeof newValue,
  });

  // Warn about potential issues
  if (oldValue === newValue) {
    logger.warn(`${stateName} set to same value`, { value: newValue });
  }

  if (newValue === null || newValue === undefined) {
    logger.warn(`${stateName} set to ${newValue}`);
  }
}

// Component lifecycle debugging
export function debugComponentLifecycle(
  componentName: string,
  lifecycle: 'mount' | 'update' | 'unmount',
  props?: any,
  state?: any
): void {
  if (!DEBUG_CONFIG.enabled) return;

  const logger = new DebugLogger(`Lifecycle:${componentName}`);

  switch (lifecycle) {
    case 'mount':
      logger.success('Component mounted', { props, state });
      break;
    case 'update':
      logger.info('Component updated', { props, state });
      break;
    case 'unmount':
      logger.info('Component unmounted');
      break;
  }
}

// Error context collection
export function collectErrorContext(): Record<string, any> {
  // Only collect browser-specific context in browser environment
  if (typeof window === 'undefined') {
    return {
      timestamp: new Date().toISOString(),
      environment: 'server',
    };
  }

  return {
    url: window.location.href,
    userAgent: navigator.userAgent,
    timestamp: new Date().toISOString(),
    viewport: {
      width: window.innerWidth,
      height: window.innerHeight,
    },
    performance: {
      memory: (performance as any).memory
        ? {
            used: (performance as any).memory.usedJSHeapSize,
            total: (performance as any).memory.totalJSHeapSize,
            limit: (performance as any).memory.jsHeapSizeLimit,
          }
        : null,
      timing: performance.timing
        ? {
            loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
            domReady:
              performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
          }
        : null,
    },
    localStorage: (() => {
      try {
        return {
          keys: Object.keys(localStorage),
          size: JSON.stringify(localStorage).length,
        };
      } catch {
        return { error: 'Cannot access localStorage' };
      }
    })(),
    sessionStorage: (() => {
      try {
        return {
          keys: Object.keys(sessionStorage),
          size: JSON.stringify(sessionStorage).length,
        };
      } catch {
        return { error: 'Cannot access sessionStorage' };
      }
    })(),
  };
}

// Common error patterns and solutions
export const ERROR_SOLUTIONS: Record<string, string[]> = {
  network_error: [
    'Check your internet connection',
    'Verify the API server is running',
    'Check for CORS issues in browser console',
    'Try refreshing the page',
  ],
  auth_error: [
    'Check if you are logged in',
    'Try logging out and logging back in',
    'Clear browser cookies and localStorage',
    "Verify your session hasn't expired",
  ],
  validation_error: [
    'Check that all required fields are filled',
    'Verify data formats (email, phone, etc.)',
    'Check for special characters in input',
    'Ensure data meets minimum/maximum requirements',
  ],
  not_found: [
    'Check the URL for typos',
    'Verify the resource exists',
    'Try navigating from the home page',
    'Contact support if the issue persists',
  ],
  server_error: [
    'Try again in a few moments',
    'Check if the service is under maintenance',
    'Clear browser cache and cookies',
    'Contact support with error details',
  ],
};

// Get error solutions based on error type or message
export function getErrorSolutions(error: Error | string): string[] {
  const errorMessage = typeof error === 'string' ? error : error.message;
  const lowerMessage = errorMessage.toLowerCase();

  // Check for specific error patterns
  for (const [pattern, solutions] of Object.entries(ERROR_SOLUTIONS)) {
    if (lowerMessage.includes(pattern.replace('_', ' ')) || lowerMessage.includes(pattern)) {
      return solutions;
    }
  }

  // Check for common error keywords
  if (lowerMessage.includes('network') || lowerMessage.includes('fetch')) {
    return ERROR_SOLUTIONS.network_error;
  }

  if (lowerMessage.includes('unauthorized') || lowerMessage.includes('forbidden')) {
    return ERROR_SOLUTIONS.auth_error;
  }

  if (lowerMessage.includes('validation') || lowerMessage.includes('invalid')) {
    return ERROR_SOLUTIONS.validation_error;
  }

  if (lowerMessage.includes('not found') || lowerMessage.includes('404')) {
    return ERROR_SOLUTIONS.not_found;
  }

  if (lowerMessage.includes('server') || lowerMessage.includes('500')) {
    return ERROR_SOLUTIONS.server_error;
  }

  // Default solutions
  return [
    'Try refreshing the page',
    'Check the browser console for more details',
    'Clear browser cache and cookies',
    'Contact support if the issue persists',
  ];
}

// Debug panel for development
export function createDebugPanel(): void {
  if (!DEBUG_CONFIG.enabled || typeof window === 'undefined') return;

  // Create debug panel element
  const panel = document.createElement('div');
  panel.id = 'debug-panel';
  panel.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    width: 300px;
    max-height: 400px;
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 10px;
    border-radius: 5px;
    font-family: monospace;
    font-size: 12px;
    z-index: 10000;
    overflow-y: auto;
    display: none;
  `;

  // Add toggle button
  const toggleButton = document.createElement('button');
  toggleButton.textContent = '🐛';
  toggleButton.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    width: 40px;
    height: 40px;
    background: #007acc;
    color: white;
    border: none;
    border-radius: 50%;
    font-size: 16px;
    cursor: pointer;
    z-index: 10001;
  `;

  toggleButton.onclick = () => {
    const isVisible = panel.style.display !== 'none';
    panel.style.display = isVisible ? 'none' : 'block';
    toggleButton.style.right = isVisible ? '10px' : '320px';
  };

  // Add content to panel
  const updatePanel = () => {
    const measures = perfMonitor.getAllMeasures();
    const context = collectErrorContext();

    panel.innerHTML = `
      <h3>🐛 Debug Panel</h3>
      <div><strong>Performance:</strong></div>
      ${Object.entries(measures)
        .map(([name, time]) => `<div>${name}: ${time.toFixed(2)}ms</div>`)
        .join('')}
      <div><strong>Memory:</strong></div>
      <div>Used: ${
        context.performance.memory?.used
          ? (context.performance.memory.used / 1024 / 1024).toFixed(2) + 'MB'
          : 'N/A'
      }</div>
      <div><strong>Viewport:</strong></div>
      <div>${context.viewport.width}x${context.viewport.height}</div>
      <button onclick="console.clear()" style="margin-top: 10px; padding: 5px;">Clear Console</button>
    `;
  };

  // Update panel every 5 seconds
  setInterval(updatePanel, 5000);
  updatePanel();

  // Add to DOM
  document.body.appendChild(panel);
  document.body.appendChild(toggleButton);
}

// Initialize debug utilities
export function initializeDebugUtils(): void {
  if (!DEBUG_CONFIG.enabled) return;

  logger.debug('🐛 Debug utilities initialized');
  logger.debug('Debug config:', DEBUG_CONFIG);

  // Create debug panel
  if (typeof window !== 'undefined') {
    window.addEventListener('load', createDebugPanel);
  }

  // Add global debug helpers
  if (typeof window !== 'undefined') {
    (window as any).debugUtils = {
      perfMonitor,
      DebugLogger,
      collectErrorContext,
      getErrorSolutions,
      config: DEBUG_CONFIG,
    };
  }
}

// Export commonly used debug logger instances
export const debugLogger = new DebugLogger('App');
export const apiDebugLogger = new DebugLogger('API');
export const stateDebugLogger = new DebugLogger('State');
