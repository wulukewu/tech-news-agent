// Build-time only flags (these are fine as build-time since they don't vary per environment)
export const env = {
  enablePWA: process.env.NEXT_PUBLIC_ENABLE_PWA === 'true',
  enableAnalytics: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true',
};
