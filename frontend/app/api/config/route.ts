import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET() {
  const allKeys = Object.keys(process.env).filter((k) => k.startsWith('NEXT_PUBLIC'));
  return NextResponse.json({
    apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
    appUrl: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
    appName: process.env.NEXT_PUBLIC_APP_NAME || 'Tech News Agent',
    _debug: {
      raw_api: process.env.NEXT_PUBLIC_API_BASE_URL,
      raw_api_len: process.env.NEXT_PUBLIC_API_BASE_URL?.length,
      node_env: process.env.NODE_ENV,
      next_public_keys: allKeys,
    },
  });
}
