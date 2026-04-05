// Learn more: https://github.com/testing-library/jest-dom
require('@testing-library/jest-dom');
require('whatwg-fetch');

// Polyfill for TextEncoder/TextDecoder
const { TextEncoder, TextDecoder } = require('util');
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      pathname: '/',
      query: {},
      asPath: '/',
    };
  },
  usePathname() {
    return '/';
  },
  useSearchParams() {
    return new URLSearchParams();
  },
  useParams() {
    return {};
  },
}));

// Mock environment variables
process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000';
process.env.NEXT_PUBLIC_APP_URL = 'http://localhost:3000';
