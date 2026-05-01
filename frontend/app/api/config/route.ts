import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET() {
  return NextResponse.json({
    apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8000',
    appUrl: process.env.APP_URL || 'http://localhost:3000',
    appName: process.env.APP_NAME || 'Tech News Agent',
  });
}
