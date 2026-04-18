import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // 重定向 /app/settings 到 /app/settings/notifications
  if (request.nextUrl.pathname === '/app/settings') {
    return NextResponse.redirect(new URL('/app/settings/notifications', request.url));
  }
}

export const config = {
  matcher: '/app/settings',
};
