/**
 * Next.js Instrumentation
 *
 * This file runs once when the server starts up.
 * Used to add polyfills for SSR compatibility.
 */

export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    // Polyfill 'self' to prevent "self is not defined" errors during SSR
    // Some libraries expect 'self' to be available (browser global)
    if (typeof global.self === 'undefined') {
      (global as any).self = global;
    }
  }
}
