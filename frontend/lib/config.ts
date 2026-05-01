interface RuntimeConfig {
  apiBaseUrl: string;
  appUrl: string;
  appName: string;
}

let cached: RuntimeConfig | null = null;

export async function getRuntimeConfig(): Promise<RuntimeConfig> {
  if (cached) return cached;

  try {
    const res = await fetch('/api/config');
    cached = await res.json();
    return cached!;
  } catch {
    cached = {
      apiBaseUrl: 'http://localhost:8000',
      appUrl: 'http://localhost:3000',
      appName: 'Tech News Agent',
    };
    return cached;
  }
}
