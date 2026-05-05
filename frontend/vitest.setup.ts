import '@testing-library/jest-dom';
import React from 'react';
import { beforeAll, afterEach, afterAll, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import { server } from './mocks/server';
import fc from 'fast-check';

// Configure fast-check: use fewer runs in CI to keep tests fast
// Default: 100 runs; CI: 20 runs
fc.configureGlobal({
  numRuns: process.env.CI === 'true' ? 20 : 100,
  endOnFailure: true,
});

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = String(value);
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    get length() {
      return Object.keys(store).length;
    },
    key: (index: number) => Object.keys(store)[index] ?? null,
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock, writable: true });

// Mock I18n globally — tries en-US first, falls back to zh-TW key lookup
vi.mock('./contexts/I18nContext', async () => {
  const actual = await vi.importActual('./contexts/I18nContext');
  const enUS = (await import('./locales/en-US.json')).default;
  const zhTW = (await import('./locales/zh-TW.json')).default;

  const lookupKey = (obj: any, key: string, params?: Record<string, any>): string | null => {
    const keys = key.split('.');
    let value: any = obj;
    for (const k of keys) {
      value = value?.[k];
    }
    if (typeof value !== 'string') return null;
    if (params) {
      return value.replace(/\{(\w+)\}/g, (_, k) => params[k] ?? `{${k}}`);
    }
    return value;
  };

  return {
    ...actual,
    useI18n: () => ({
      locale: 'en-US' as const,
      setLocale: vi.fn(),
      t: (key: string, params?: Record<string, any>) => {
        return lookupKey(enUS, key, params) ?? lookupKey(zhTW, key, params) ?? key;
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
  localStorageMock.clear();
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

// Mock HTMLCanvasElement.getContext (not available in jsdom)
HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
  fillRect: vi.fn(),
  clearRect: vi.fn(),
  getImageData: vi.fn(() => ({ data: new Array(4) })),
  putImageData: vi.fn(),
  createImageData: vi.fn(() => []),
  setTransform: vi.fn(),
  drawImage: vi.fn(),
  save: vi.fn(),
  fillText: vi.fn(),
  restore: vi.fn(),
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  closePath: vi.fn(),
  stroke: vi.fn(),
  translate: vi.fn(),
  scale: vi.fn(),
  rotate: vi.fn(),
  arc: vi.fn(),
  fill: vi.fn(),
  measureText: vi.fn(() => ({ width: 0 })),
  transform: vi.fn(),
  rect: vi.fn(),
  clip: vi.fn(),
  createLinearGradient: vi.fn(() => ({
    addColorStop: vi.fn(),
  })),
  createRadialGradient: vi.fn(() => ({
    addColorStop: vi.fn(),
  })),
}) as any;
