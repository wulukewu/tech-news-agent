import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  // 重定向 /app/settings 到 /app/settings/notifications
  if (pathname === '/app/settings') {
    return NextResponse.redirect(new URL('/app/settings/notifications', request.url));
  }

  // 重定向 /app/setting (單數) 到 /app/settings/notifications
  if (pathname === '/app/setting') {
    return NextResponse.redirect(new URL('/app/settings/notifications', request.url));
  }

  // 重定向舊的 /dashboard/* 路徑到 /app/*
  if (pathname.startsWith('/dashboard')) {
    const newPath = pathname.replace('/dashboard', '/app');
    return NextResponse.redirect(new URL(newPath, request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/app/settings', '/app/setting', '/dashboard/:path*'],
};
