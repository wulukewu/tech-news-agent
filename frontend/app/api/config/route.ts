import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET() {
  // Use non-NEXT_PUBLIC_ prefixed vars to avoid Next.js build-time inlining
  const apiBaseUrl =
    process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const appUrl = process.env.APP_URL || process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
  const appName = process.env.APP_NAME || process.env.NEXT_PUBLIC_APP_NAME || 'Tech News Agent';

  return NextResponse.json({
    apiBaseUrl,
    appUrl,
    appName,
    _debug: {
      API_BASE_URL: process.env.API_BASE_URL,
      NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
      node_env: process.env.NODE_ENV,
    },
  });
}
