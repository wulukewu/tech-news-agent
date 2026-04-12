/**
 * API Error Logging and Reporting
 * Requirements: 1.2, 4.3
 *
 * This module provides error logging and reporting for API errors.
 */

import { ApiError } from './errors';
import { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';

/**
 * Log levels
 */
export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
}

/**
 * Log entry structure
 */
export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: Record<string, any>;
}

/**
 * API Logger class
 */
export class ApiLogger {
  private static instance: ApiLogger | null = null;
  private logs: LogEntry[] = [];
  private maxLogs: number = 100;

  private constructor() {}

  /**
   * Get singleton instance
   */
  public static getInstance(): ApiLogger {
    if (!ApiLogger.instance) {
      ApiLogger.instance = new ApiLogger();
    }
    return ApiLogger.instance;
  }

  /**
   * Log a message
   */
  private log(level: LogLevel, message: string, context?: Record<string, any>): void {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context,
    };

    this.logs.push(entry);

    // Keep only last maxLogs entries
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    // Console output in development
    if (process.env.NODE_ENV === 'development') {
      const consoleMethod =
        level === LogLevel.ERROR ? 'error' : level === LogLevel.WARN ? 'warn' : 'log';
      console[consoleMethod](`[${level}] ${message}`, context || '');
    }
  }

  /**
   * Log debug message
   */
  public debug(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.DEBUG, message, context);
  }

  /**
   * Log info message
   */
  public info(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.INFO, message, context);
  }

  /**
   * Log warning message
   */
  public warn(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.WARN, message, context);
  }

  /**
   * Log error message
   */
  public error(message: string, context?: Record<string, any>): void {
    this.log(LogLevel.ERROR, message, context);
  }

  /**
   * Log API request
   */
  public logRequest(config: AxiosRequestConfig): void {
    this.debug('API Request', {
      method: config.method?.toUpperCase(),
      url: config.url,
      params: config.params,
      headers: this.sanitizeHeaders(config.headers),
    });
  }

  /**
   * Log API response
   */
  public logResponse(response: AxiosResponse): void {
    this.debug('API Response', {
      status: response.status,
      statusText: response.statusText,
      url: response.config.url,
      method: response.config.method?.toUpperCase(),
    });
  }

  /**
   * Log API error
   */
  public logApiError(error: ApiError, requestConfig?: AxiosRequestConfig): void {
    this.error('API Error', {
      statusCode: error.statusCode,
      errorCode: error.errorCode,
      message: error.message,
      userMessage: error.userMessage,
      details: error.details,
      url: requestConfig?.url,
      method: requestConfig?.method?.toUpperCase(),
    });
  }

  /**
   * Log retry attempt
   */
  public logRetry(
    attempt: number,
    error: ApiError,
    delay: number,
    requestConfig?: AxiosRequestConfig
  ): void {
    this.warn('API Retry', {
      attempt,
      delay,
      errorCode: error.errorCode,
      message: error.message,
      url: requestConfig?.url,
      method: requestConfig?.method?.toUpperCase(),
    });
  }

  /**
   * Get all logs
   */
  public getLogs(): LogEntry[] {
    return [...this.logs];
  }

  /**
   * Clear all logs
   */
  public clearLogs(): void {
    this.logs = [];
  }

  /**
   * Sanitize headers to remove sensitive information
   */
  private sanitizeHeaders(headers?: any): Record<string, string> {
    if (!headers) {
      return {};
    }

    const sanitized: Record<string, string> = {};
    const sensitiveKeys = ['authorization', 'cookie', 'x-api-key'];

    for (const [key, value] of Object.entries(headers)) {
      const lowerKey = key.toLowerCase();
      if (sensitiveKeys.includes(lowerKey)) {
        sanitized[key] = '[REDACTED]';
      } else {
        sanitized[key] = String(value);
      }
    }

    return sanitized;
  }
}

/**
 * Export singleton instance
 */
export const apiLogger = ApiLogger.getInstance();
