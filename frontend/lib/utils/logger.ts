/**
 * Production-safe logger utility
 *
 * Replaces console.log with environment-aware logging
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LoggerConfig {
  enabled: boolean;
  level: LogLevel;
  prefix?: string;
}

class Logger {
  private config: LoggerConfig;

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = {
      enabled: process.env.NODE_ENV === 'development',
      level: 'debug',
      ...config,
    };
  }

  private shouldLog(level: LogLevel): boolean {
    if (!this.config.enabled) return false;

    const levels: LogLevel[] = ['debug', 'info', 'warn', 'error'];
    const currentLevelIndex = levels.indexOf(this.config.level);
    const messageLevelIndex = levels.indexOf(level);

    return messageLevelIndex >= currentLevelIndex;
  }

  private formatMessage(level: LogLevel, ...args: any[]): any[] {
    const prefix = this.config.prefix ? `[${this.config.prefix}]` : '';
    const timestamp = new Date().toISOString();
    return [`[${timestamp}] ${prefix} [${level.toUpperCase()}]`, ...args];
  }

  debug(...args: any[]): void {
    if (this.shouldLog('debug')) {
      console.log(...this.formatMessage('debug', ...args));
    }
  }

  info(...args: any[]): void {
    if (this.shouldLog('info')) {
      console.info(...this.formatMessage('info', ...args));
    }
  }

  warn(...args: any[]): void {
    if (this.shouldLog('warn')) {
      console.warn(...this.formatMessage('warn', ...args));
    }
  }

  error(...args: any[]): void {
    // Always log errors, even in production
    console.error(...this.formatMessage('error', ...args));
  }

  // Create a child logger with a specific prefix
  child(prefix: string): Logger {
    return new Logger({
      ...this.config,
      prefix: this.config.prefix ? `${this.config.prefix}:${prefix}` : prefix,
    });
  }
}

// Default logger instance
export const logger = new Logger();

// Create domain-specific loggers
export const apiLogger = logger.child('API');
export const uiLogger = logger.child('UI');
export const cacheLogger = logger.child('Cache');

export default logger;
