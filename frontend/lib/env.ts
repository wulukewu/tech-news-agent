function validateEnv() {
  const requiredEnvVars = ['NEXT_PUBLIC_API_BASE_URL', 'NEXT_PUBLIC_APP_URL'];

  const missingVars = requiredEnvVars.filter(
    (varName) => !process.env[varName],
  );

  if (missingVars.length > 0) {
    throw new Error(
      `Missing required environment variables: ${missingVars.join(', ')}`,
    );
  }
}

// Validate on application startup (server-side only)
if (typeof window === 'undefined') {
  validateEnv();
}

export const env = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL!,
  appUrl: process.env.NEXT_PUBLIC_APP_URL!,
  enablePWA: process.env.NEXT_PUBLIC_ENABLE_PWA === 'true',
  enableAnalytics: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true',
};
