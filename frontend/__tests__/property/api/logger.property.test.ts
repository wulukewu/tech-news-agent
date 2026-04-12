/**
 * Property-Based Tests for Frontend Logger
 * Task 9.2: Write property test for frontend log batching
 *
 * **Validates: Requirement 5.4**
 *
 * Property 14: Frontend Log Batching
 */

import * as fc from 'fast-check';
import FrontendLogger, { LogLevel, LogEntry } from '@/lib/logger';

// Mock fetch globally
global.fetch = jest.fn();

describe('Property-Based Tests: Frontend Logger', () => {
  let logger: FrontendLogger;

  beforeEach(() => {
    jest.clearAllMocks();
    FrontendLogger.resetInstance();
    logger = FrontendLogger.getInstance({
      enabled: true,
      batchSize: 10,
      flushInterval: 60000, // Long interval to prevent auto-flush during tests
      endpoint: '/api/logs',
    });
  });

  afterEach(() => {
    FrontendLogger.resetInstance();
  });

  describe('Property 14: Frontend Log Batching', () => {
    /**
     * **Validates: Requirement 5.4**
     *
     * Property: For any sequence of frontend log calls, the logger SHALL batch logs
     * and send them to the backend in groups rather than sending each log individually.
     *
     * This property ensures that:
     * 1. Logs are accumulated in a buffer
     * 2. Logs are sent in batches when buffer reaches batch size
     * 3. Multiple logs result in fewer network requests than individual logs
     */

    it('should batch logs and not send until batch size is reached', () => {
      fc.assert(
        fc.property(
          // Generate arbitrary number of logs less than batch size
          fc.integer({ min: 1, max: 9 }),
          fc.array(fc.string({ minLength: 1, maxLength: 50 }), { minLength: 1, maxLength: 9 }),
          (numLogs, messages) => {
            // Clear buffer
            logger.clearBuffer();
            (global.fetch as jest.Mock).mockClear();

            // Log messages (less than batch size)
            for (let i = 0; i < Math.min(numLogs, messages.length); i++) {
              logger.info(messages[i]);
            }

            // Verify logs are in buffer
            const bufferSize = logger.getBufferSize();
            expect(bufferSize).toBe(Math.min(numLogs, messages.length));

            // Verify no network requests made yet
            expect(global.fetch).not.toHaveBeenCalled();
          }
        ),
        { numRuns: 50 }
      );
    });

    it('should automatically flush when batch size is reached', async () => {
      // Simple test: log exactly batch size messages and verify flush
      FrontendLogger.resetInstance();
      const testLogger = FrontendLogger.getInstance({
        enabled: true,
        batchSize: 5,
        flushInterval: 60000,
        endpoint: '/api/logs',
        minLevel: LogLevel.DEBUG,
      });

      (global.fetch as jest.Mock).mockClear();
      (global.fetch as jest.Mock).mockResolvedValue({ ok: true, status: 200 });

      // Log exactly batch size messages
      for (let i = 0; i < 5; i++) {
        testLogger.info(`Message ${i}`);
      }

      // Wait for flush
      await new Promise((resolve) => setTimeout(resolve, 200));

      // Should have flushed once
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(testLogger.getBufferSize()).toBe(0);

      FrontendLogger.resetInstance();
    });

    it('should batch logs from different log levels together', () => {
      fc.assert(
        fc.property(
          // Generate mixed log levels (excluding DEBUG since minLevel is INFO by default)
          fc.array(
            fc.record({
              level: fc.constantFrom(LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR),
              message: fc.string({ minLength: 1, maxLength: 50 }),
            }),
            { minLength: 1, maxLength: 9 }
          ),
          (logs) => {
            logger.clearBuffer();
            (global.fetch as jest.Mock).mockClear();

            // Log messages with different levels
            for (const log of logs) {
              switch (log.level) {
                case LogLevel.INFO:
                  logger.info(log.message);
                  break;
                case LogLevel.WARN:
                  logger.warn(log.message);
                  break;
                case LogLevel.ERROR:
                  logger.error(log.message);
                  break;
              }
            }

            // Verify all logs are in buffer
            expect(logger.getBufferSize()).toBe(logs.length);

            // Verify no network requests made yet (less than batch size)
            expect(global.fetch).not.toHaveBeenCalled();
          }
        ),
        { numRuns: 50 }
      );
    });

    it('should preserve log order in batches', () => {
      fc.assert(
        fc.property(
          // Generate sequence of log messages
          fc.array(fc.string({ minLength: 1, maxLength: 30 }), { minLength: 5, maxLength: 9 }), // Less than batch size
          (messages) => {
            logger.clearBuffer();

            // Log messages in order
            for (const message of messages) {
              logger.info(message);
            }

            // Get buffer
            const buffer = logger.getBuffer();

            // Verify order is preserved
            expect(buffer.length).toBe(messages.length);
            for (let i = 0; i < messages.length; i++) {
              expect(buffer[i].message).toBe(messages[i]);
            }
          }
        ),
        { numRuns: 50 }
      );
    });

    it('should handle rapid logging without losing messages', () => {
      fc.assert(
        fc.property(
          // Generate number of logs less than batch size
          fc.integer({ min: 1, max: 9 }),
          (numLogs) => {
            logger.clearBuffer();
            (global.fetch as jest.Mock).mockClear();

            // Rapidly log messages
            for (let i = 0; i < numLogs; i++) {
              logger.info(`Rapid log ${i}`);
            }

            // Get buffer size (no flushes should have happened for < 10 logs)
            const bufferSize = logger.getBufferSize();

            // Verify all logs are in buffer
            expect(bufferSize).toBe(numLogs);

            // Verify no flush happened
            expect(global.fetch).not.toHaveBeenCalled();
          }
        ),
        { numRuns: 30 }
      );
    });

    it('should include timestamp in all log entries', () => {
      fc.assert(
        fc.property(
          fc.array(fc.string({ minLength: 1, maxLength: 50 }), { minLength: 1, maxLength: 10 }),
          (messages) => {
            logger.clearBuffer();

            // Log messages
            for (const message of messages) {
              logger.info(message);
            }

            // Get buffer
            const buffer = logger.getBuffer();

            // Verify all entries have timestamps
            for (const entry of buffer) {
              expect(entry.timestamp).toBeDefined();
              expect(typeof entry.timestamp).toBe('string');
              // Verify timestamp is valid ISO 8601
              expect(new Date(entry.timestamp).toISOString()).toBe(entry.timestamp);
            }
          }
        ),
        { numRuns: 50 }
      );
    });

    it('should sanitize sensitive data in context', () => {
      fc.assert(
        fc.property(
          fc.record({
            password: fc.string({ minLength: 1 }), // Non-empty strings
            token: fc.string({ minLength: 1 }),
            apiKey: fc.string({ minLength: 1 }),
            normalData: fc.string(),
          }),
          (context) => {
            logger.clearBuffer();

            // Log with sensitive context
            logger.info('Test message', context);

            // Get buffer
            const buffer = logger.getBuffer();
            const entry = buffer[0];

            // Verify sensitive data is redacted
            expect(entry.context?.password).toBe('[REDACTED]');
            expect(entry.context?.token).toBe('[REDACTED]');
            expect(entry.context?.apiKey).toBe('[REDACTED]');

            // Verify normal data is preserved
            expect(entry.context?.normalData).toBe(context.normalData);
          }
        ),
        { numRuns: 50 }
      );
    });

    it('should respect minimum log level configuration', () => {
      fc.assert(
        fc.property(
          fc.constantFrom(LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR),
          (minLevel) => {
            // Create logger with specific min level
            FrontendLogger.resetInstance();
            const testLogger = FrontendLogger.getInstance({
              enabled: true,
              minLevel,
              batchSize: 10,
              flushInterval: 60000,
            });

            testLogger.clearBuffer();

            // Log at all levels
            testLogger.debug('Debug message');
            testLogger.info('Info message');
            testLogger.warn('Warn message');
            testLogger.error('Error message');

            // Get buffer
            const buffer = testLogger.getBuffer();

            // Verify only logs at or above min level are in buffer
            const levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR];
            const minLevelIndex = levels.indexOf(minLevel);

            for (const entry of buffer) {
              const entryLevelIndex = levels.indexOf(entry.level);
              expect(entryLevelIndex).toBeGreaterThanOrEqual(minLevelIndex);
            }

            FrontendLogger.resetInstance();
          }
        ),
        { numRuns: 50 }
      );
    });
  });

  describe('Flush Behavior', () => {
    it('should send batched logs to correct endpoint', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({ ok: true });

      // Log enough messages to trigger flush
      for (let i = 0; i < 10; i++) {
        logger.info(`Message ${i}`);
      }

      // Wait for flush
      await new Promise((resolve) => setTimeout(resolve, 100));

      // Verify fetch was called with correct endpoint
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/logs',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );

      // Verify logs were sent
      const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
      const body = JSON.parse(fetchCall[1].body);
      expect(body.logs).toHaveLength(10);
    });

    it('should retry failed flushes by keeping logs in buffer', async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

      // Log enough messages to trigger flush
      for (let i = 0; i < 10; i++) {
        logger.info(`Message ${i}`);
      }

      // Wait for flush attempt
      await new Promise((resolve) => setTimeout(resolve, 100));

      // Verify logs are back in buffer
      expect(logger.getBufferSize()).toBe(10);
    });
  });

  describe('Configuration', () => {
    it('should allow updating configuration', () => {
      logger.configure({
        batchSize: 20,
        flushInterval: 10000,
      });

      const config = logger.getConfig();
      expect(config.batchSize).toBe(20);
      expect(config.flushInterval).toBe(10000);
    });

    it('should respect enabled flag', () => {
      FrontendLogger.resetInstance();
      const disabledLogger = FrontendLogger.getInstance({
        enabled: false,
        batchSize: 10,
      });

      disabledLogger.info('Test message');

      expect(disabledLogger.getBufferSize()).toBe(0);
    });
  });
});
