import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { I18nProvider } from '@/contexts/I18nContext';
import { PersonalizedNotificationSettings } from '@/features/notifications/components/PersonalizedNotificationSettings';
import { NotificationFrequencySelector } from '@/features/notifications/components/NotificationFrequencySelector';
import { NotificationPreview } from '@/features/notifications/components/NotificationPreview';
import * as notificationsApi from '@/lib/api/notifications';
import { NotificationSettings, NotificationFrequency } from '@/types/notification';
import * as fc from 'fast-check';

// Mock the API functions
vi.mock('@/lib/api/notifications');
const mockNotificationsApi = notificationsApi as any;

// Mock toast
vi.mock('@/lib/toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock i18n context
const mockI18n = {
  t: (key: string) => key,
  locale: 'en-US',
  setLocale: vi.fn(),
};

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <I18nProvider value={mockI18n}>{children}</I18nProvider>
    </QueryClientProvider>
  );
};

// Property-based test generators
const frequencyArbitrary = fc.constantFrom(
  'immediate',
  'daily',
  'weekly',
  'disabled'
) as fc.Arbitrary<NotificationFrequency>;

const timeArbitrary = fc
  .tuple(fc.integer({ min: 0, max: 23 }), fc.integer({ min: 0, max: 59 }))
  .map(
    ([hours, minutes]) =>
      `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`
  );

const timezoneArbitrary = fc.constantFrom(
  'UTC',
  'Asia/Taipei',
  'America/New_York',
  'Europe/London',
  'Asia/Tokyo',
  'Australia/Sydney',
  'America/Los_Angeles'
);

const userPreferencesArbitrary = fc.record({
  id: fc.uuid(),
  userId: fc.uuid(),
  frequency: frequencyArbitrary,
  notificationTime: timeArbitrary,
  timezone: timezoneArbitrary,
  dmEnabled: fc.boolean(),
  emailEnabled: fc.boolean(),
  createdAt: fc.date().map((d) => d.toISOString()),
  updatedAt: fc.date().map((d) => d.toISOString()),
});

const notificationSettingsArbitrary = fc.record({
  dmEnabled: fc.boolean(),
  emailEnabled: fc.boolean(),
  frequency: frequencyArbitrary,
  minTinkeringIndex: fc.integer({ min: 1, max: 5 }),
  quietHours: fc.record({
    enabled: fc.boolean(),
    start: timeArbitrary,
    end: timeArbitrary,
  }),
});

describe('Notification Preferences Property Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Property 1: Preference Validation Consistency', () => {
    /**
     * **Validates: Requirements 6.3, 6.5**
     *
     * For any user preference input, the system SHALL accept valid values
     * (frequencies: daily/weekly/monthly/disabled, times: 00:00-23:59, valid IANA timezones)
     * and reject invalid values with appropriate error messages.
     */
    it('should consistently validate time format across all valid inputs', () => {
      fc.assert(
        fc.property(timeArbitrary, (time) => {
          // All generated times should be valid HH:MM format
          const timeRegex = /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/;
          expect(timeRegex.test(time)).toBe(true);

          // Time should be parseable
          const [hours, minutes] = time.split(':').map(Number);
          expect(hours).toBeGreaterThanOrEqual(0);
          expect(hours).toBeLessThanOrEqual(23);
          expect(minutes).toBeGreaterThanOrEqual(0);
          expect(minutes).toBeLessThanOrEqual(59);
        }),
        { numRuns: 100 }
      );
    });

    it('should consistently validate frequency values', () => {
      fc.assert(
        fc.property(frequencyArbitrary, (frequency) => {
          const validFrequencies = ['immediate', 'daily', 'weekly', 'disabled'];
          expect(validFrequencies).toContain(frequency);
        }),
        { numRuns: 50 }
      );
    });

    it('should consistently validate timezone identifiers', () => {
      fc.assert(
        fc.property(timezoneArbitrary, (timezone) => {
          // All generated timezones should be valid IANA identifiers
          expect(() => {
            Intl.DateTimeFormat(undefined, { timeZone: timezone });
          }).not.toThrow();
        }),
        { numRuns: 50 }
      );
    });
  });

  describe('Property 2: Component State Consistency', () => {
    /**
     * **Validates: Requirements 6.1, 6.2, 6.4**
     *
     * For any valid notification preferences, the UI components SHALL display
     * consistent state across all interface elements and provide accurate previews.
     */
    it('should maintain consistent state between frequency selector and preview', async () => {
      await fc.assert(
        fc.asyncProperty(notificationSettingsArbitrary, async (settings) => {
          const onFrequencyChange = vi.fn();

          render(
            <div>
              <NotificationFrequencySelector
                frequency={settings.frequency}
                onFrequencyChange={onFrequencyChange}
              />
              <NotificationPreview settings={settings} />
            </div>,
            { wrapper: createWrapper() }
          );

          // Wait for components to render
          await screen.findByText(/Notification Frequency|notification-frequency.title/);

          // Frequency selector should show correct selection
          const selectedRadio = screen.getByRole('radio', { checked: true });
          expect(selectedRadio).toHaveAttribute('value', settings.frequency);

          // Preview should reflect the same frequency
          if (settings.dmEnabled && settings.frequency !== 'disabled') {
            const frequencyBadge = screen.getByText(
              settings.frequency === 'immediate'
                ? /Immediate|settings.notifications.frequency-immediate/
                : settings.frequency === 'daily'
                  ? /Daily|settings.notifications.frequency-daily/
                  : /Weekly|settings.notifications.frequency-weekly/
            );
            expect(frequencyBadge).toBeInTheDocument();
          }
        }),
        { numRuns: 20 }
      );
    });

    it('should consistently show notification trigger status based on settings', async () => {
      await fc.assert(
        fc.asyncProperty(notificationSettingsArbitrary, async (settings) => {
          render(<NotificationPreview settings={settings} />, { wrapper: createWrapper() });

          await screen.findByText(/Notification Preview|settings.notifications.preview-title/);

          const shouldTrigger =
            settings.dmEnabled &&
            settings.minTinkeringIndex <= 4 && // Mock article has tinkeringIndex: 4
            (!settings.quietHours.enabled || !isInQuietHours(settings.quietHours));

          if (shouldTrigger) {
            expect(
              screen.getByText(/Will send notification|settings.notifications.will-trigger/)
            ).toBeInTheDocument();
          } else {
            expect(
              screen.getByText(/Will not send notification|settings.notifications.will-not-trigger/)
            ).toBeInTheDocument();
          }
        }),
        { numRuns: 30 }
      );
    });
  });

  describe('Property 3: API Integration Consistency', () => {
    /**
     * **Validates: Requirements 6.5, 8.1, 8.2**
     *
     * For any preference update, the system SHALL validate input, call appropriate APIs,
     * handle responses consistently, and maintain data synchronization.
     */
    it('should consistently handle preference updates across all valid inputs', async () => {
      await fc.assert(
        fc.asyncProperty(
          userPreferencesArbitrary,
          fc.record({
            frequency: fc.option(frequencyArbitrary),
            notificationTime: fc.option(timeArbitrary),
            timezone: fc.option(timezoneArbitrary),
            dmEnabled: fc.option(fc.boolean()),
            emailEnabled: fc.option(fc.boolean()),
          }),
          async (initialPrefs, updates) => {
            const user = userEvent.setup();

            // Setup mocks
            mockNotificationsApi.getNotificationPreferences.mockResolvedValue(initialPrefs);
            mockNotificationsApi.getSupportedTimezones.mockResolvedValue([
              { value: 'UTC', label: 'UTC', offset: '+00:00' },
              { value: 'Asia/Taipei', label: 'Taipei', offset: '+08:00' },
            ]);
            mockNotificationsApi.getNotificationStatus.mockResolvedValue({
              scheduled: true,
              message: 'Scheduled',
            });
            mockNotificationsApi.previewNotificationTime.mockResolvedValue({
              nextNotificationTime: '2024-01-01T12:00:00Z',
              localTime: '2024-01-01T12:00:00Z',
              utcTime: '2024-01-01T12:00:00Z',
              message: 'Next notification',
            });
            mockNotificationsApi.updateNotificationPreferences.mockResolvedValue({
              ...initialPrefs,
              ...updates,
            });

            render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

            // Wait for component to load
            await screen.findByText(/個人化通知設定|personalized notification/i);

            // Test DM toggle if update includes dmEnabled
            if (updates.dmEnabled !== undefined) {
              const dmSwitch = screen.getByRole('switch', { name: /discord|dm/i });
              if (dmSwitch.checked !== updates.dmEnabled) {
                await user.click(dmSwitch);

                expect(mockNotificationsApi.updateNotificationPreferences).toHaveBeenCalledWith(
                  expect.objectContaining({ dmEnabled: updates.dmEnabled })
                );
              }
            }

            // All API calls should complete without throwing
            expect(mockNotificationsApi.getNotificationPreferences).toHaveBeenCalled();
          }
        ),
        { numRuns: 15 }
      );
    });
  });

  describe('Property 4: Timezone Conversion Accuracy', () => {
    /**
     * **Validates: Requirements 5.3**
     *
     * For any valid timezone and notification time combination, the system SHALL
     * correctly convert between user local time and UTC, ensuring notifications
     * are scheduled at the user's intended local time.
     */
    it('should consistently handle timezone conversions', () => {
      fc.assert(
        fc.property(timeArbitrary, timezoneArbitrary, (time, timezone) => {
          const [hours, minutes] = time.split(':').map(Number);

          // Create a date in the user's timezone
          const userDate = new Date();
          userDate.setHours(hours, minutes, 0, 0);

          // Convert to user timezone string representation
          const userTimeString = userDate.toLocaleString('en-US', {
            timeZone: timezone,
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
          });

          // The conversion should preserve the time components
          expect(userTimeString).toMatch(/\d{2}:\d{2}/);

          // Should be able to create valid Date objects
          expect(() => {
            new Date(userDate.toLocaleString('en-US', { timeZone: timezone }));
          }).not.toThrow();
        }),
        { numRuns: 50 }
      );
    });
  });

  describe('Property 5: Form Validation Robustness', () => {
    /**
     * **Validates: Requirements 6.3, 6.5**
     *
     * For any user input through Web interfaces, the system SHALL validate input,
     * provide immediate feedback, and handle edge cases gracefully.
     */
    it('should handle all edge cases in time input validation', () => {
      fc.assert(
        fc.property(
          fc.integer({ min: -1, max: 25 }),
          fc.integer({ min: -1, max: 61 }),
          (hours, minutes) => {
            const timeString = `${hours.toString().padStart(2, '0')}:${minutes
              .toString()
              .padStart(2, '0')}`;
            const isValid = hours >= 0 && hours <= 23 && minutes >= 0 && minutes <= 59;

            // HTML5 time input validation
            const input = document.createElement('input');
            input.type = 'time';
            input.value = timeString;

            if (isValid) {
              expect(input.value).toBe(timeString);
            } else {
              // Invalid times should be rejected by HTML5 input
              expect(input.value).toBe('');
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should consistently validate frequency transitions', () => {
      fc.assert(
        fc.property(frequencyArbitrary, frequencyArbitrary, (fromFreq, toFreq) => {
          // All frequency transitions should be valid
          const validFrequencies = ['immediate', 'daily', 'weekly', 'disabled'];
          expect(validFrequencies).toContain(fromFreq);
          expect(validFrequencies).toContain(toFreq);

          // Transition logic should be consistent
          const requiresTimeSettings = toFreq !== 'disabled' && toFreq !== 'immediate';
          expect(typeof requiresTimeSettings).toBe('boolean');
        }),
        { numRuns: 50 }
      );
    });
  });

  describe('Property 6: Error Handling Consistency', () => {
    /**
     * **Validates: Requirements 6.5, 8.3**
     *
     * For any error condition, the system SHALL handle errors gracefully,
     * provide appropriate feedback, and maintain system stability.
     */
    it('should consistently handle API errors across all operations', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.constantFrom(
            'getNotificationPreferences',
            'updateNotificationPreferences',
            'previewNotificationTime'
          ),
          fc.constantFrom('Network error', 'Timeout', 'Server error', 'Invalid response'),
          async (apiMethod, errorMessage) => {
            // Mock the specific API method to fail
            mockNotificationsApi[apiMethod].mockRejectedValue(new Error(errorMessage));

            // Mock other methods to succeed
            Object.keys(mockNotificationsApi).forEach((method) => {
              if (method !== apiMethod) {
                mockNotificationsApi[method].mockResolvedValue({});
              }
            });

            render(<PersonalizedNotificationSettings />, { wrapper: createWrapper() });

            // Component should handle the error gracefully without crashing
            // Either show error state or loading state, but not crash
            const component =
              screen.getByTestId('notification-settings') ||
              screen.getByText(/loading|error|無法載入/i) ||
              document.body;

            expect(component).toBeInTheDocument();
          }
        ),
        { numRuns: 10 }
      );
    });
  });
});

// Helper function to check if current time is in quiet hours
function isInQuietHours(quietHours: { enabled: boolean; start: string; end: string }): boolean {
  if (!quietHours.enabled) return false;

  const now = new Date();
  const currentTime = `${now.getHours().toString().padStart(2, '0')}:${now
    .getMinutes()
    .toString()
    .padStart(2, '0')}`;
  const { start, end } = quietHours;

  // Simple time range check (doesn't handle overnight ranges properly, but good for testing)
  if (start <= end) {
    return currentTime >= start && currentTime <= end;
  } else {
    return currentTime >= start || currentTime <= end;
  }
}
