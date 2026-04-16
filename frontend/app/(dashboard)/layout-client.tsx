'use client';

import { Sidebar } from '@/components/layout';

interface DashboardLayoutClientProps {
  children: React.ReactNode;
}

export function DashboardLayoutClient({ children }: DashboardLayoutClientProps) {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <div className="hidden lg:flex lg:w-64 lg:flex-col lg:fixed lg:inset-y-0 lg:z-40 lg:pt-16">
        <Sidebar />
      </div>

      {/* Main content */}
      <div className="flex-1 lg:pl-64">
        <div className="container mx-auto px-4 py-6 max-w-7xl">
          <div className="space-y-6">{children}</div>
        </div>
      </div>

      {/* Mobile sidebar handled by Sidebar component */}
    </div>
  );
}
