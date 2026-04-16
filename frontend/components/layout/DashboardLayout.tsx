'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface DashboardLayoutProps {
  children: React.ReactNode;
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
  breadcrumbs?: React.ReactNode;
}

/**
 * DashboardLayout - Layout component for dashboard pages
 * Provides consistent header structure with title, description, breadcrumbs, and action buttons
 * Optimized for responsive design and accessibility
 */
export function DashboardLayout({
  children,
  title,
  description,
  actions,
  className,
  breadcrumbs,
}: DashboardLayoutProps) {
  return (
    <div className={cn('flex flex-col min-h-full', className)}>
      {/* Dashboard header */}
      <div className="border-b bg-background/95 backdrop-blur px-4 py-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Breadcrumbs */}
          {breadcrumbs && (
            <nav className="mb-4" aria-label="麵包屑導航">
              {breadcrumbs}
            </nav>
          )}

          {/* Header content */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0 flex-1">
              <h1 className="text-2xl font-bold leading-7 text-foreground sm:truncate sm:text-3xl lg:text-4xl">
                {title}
              </h1>
              {description && (
                <p className="mt-2 text-sm text-muted-foreground sm:text-base lg:text-lg max-w-3xl">
                  {description}
                </p>
              )}
            </div>

            {/* Actions */}
            {actions && (
              <div className="flex flex-shrink-0 flex-wrap gap-2 sm:flex-nowrap">{actions}</div>
            )}
          </div>
        </div>
      </div>

      {/* Dashboard content */}
      <div className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">{children}</div>
      </div>
    </div>
  );
}
