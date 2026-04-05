import { NextResponse } from 'next/server';

/**
 * Health Check Endpoint
 *
 * Provides a simple health check endpoint for monitoring and deployment verification.
 * Returns 200 OK with basic application status information.
 *
 * Requirement 30.5: Implement health check endpoints
 */
export async function GET() {
  return NextResponse.json(
    {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      service: 'tech-news-agent-frontend',
      version: process.env.npm_package_version || '1.0.0',
    },
    { status: 200 },
  );
}
