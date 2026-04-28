import '@testing-library/jest-dom';
import { beforeAll, afterEach, afterAll, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import { server } from './mocks/server';
import enUS from './locales/en-US.json';

// Mock I18n globally with en-US (most tests expect English)
vi.mock('./contexts/I18nContext', async () => {
  const actual = await vi.importActual('./contexts/I18nContext');
  return {
    ...actual,
    useI18n: () => ({
      locale: 'en-US' as const,
      setLocale: vi.fn(),
      t: (key: string, params?: Record<string, any>) => {
        const keys = key.split('.');
        let value: any = enUS;
        for (const k of keys) {
          value = value?.[k];
        }
        if (typeof value === 'string' && params) {
          return value.replace(/\{(\w+)\}/g, (_, k) => params[k] ?? `{${k}}`);
        }
        return value || key;
      },
      isLoading: false,
    }),
  };
});

// Start server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));

// Clean up after each test case (e.g. clearing jsdom)
afterEach(() => {
  cleanup();
  server.resetHandlers();
});

// Close server after all tests
afterAll(() => server.close());

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  }),
});

// Mock pointer capture functions for Radix UI Slider compatibility
Object.defineProperty(Element.prototype, 'hasPointerCapture', {
  writable: true,
  value: () => false,
});

Object.defineProperty(Element.prototype, 'setPointerCapture', {
  writable: true,
  value: () => {},
});

Object.defineProperty(Element.prototype, 'releasePointerCapture', {
  writable: true,
  value: () => {},
});
