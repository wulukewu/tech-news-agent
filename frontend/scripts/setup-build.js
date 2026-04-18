/**
 * Build Setup Script
 *
 * Adds polyfills needed for SSR compatibility before the build starts.
 * This file is loaded via NODE_OPTIONS=--require to ensure it runs in all Node.js processes.
 */

// Polyfill 'self' for server-side rendering
if (typeof global !== 'undefined' && typeof global.self === 'undefined') {
  global.self = global;
}
