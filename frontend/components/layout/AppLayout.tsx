'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';

interface AppLayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
  sidebarCollapsed?: boolean;
  onSidebarToggle?: (collapsed: boolean) => void;
}

/**
 * AppLayout - Main application layout component
 * Provides the overall structure for the application with optional sidebar, header, and footer
 * Supports responsive design with collapsible sidebar and mobile-optimized navigation
 */
export function AppLayout({
  children,
  sidebar,
  header,
  footer,
  className,
  sidebarCollapsed = false,
  onSidebarToggle,
}: AppLayoutProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(false);

  const collapsed = sidebarCollapsed ?? internalCollapsed;
  const handleToggle = (newCollapsed: boolean) => {
    if (onSidebarToggle) {
      onSidebarToggle(newCollapsed);
    } else {
      setInternalCollapsed(newCollapsed);
    }
  };

  return (
    <div className={cn('min-h-screen flex flex-col bg-background', className)}>
      {/* Header */}
      {header && (
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container mx-auto">{header}</div>
        </header>
      )}

      {/* Main content area */}
      <div className="flex flex-1 relative">
        {/* Sidebar - Fixed with 64px collapsed / 256px expanded width (Req 3.1) */}
        {sidebar && (
          <aside
            className={cn(
              'hidden lg:flex lg:flex-col lg:fixed lg:inset-y-0 lg:z-40 transition-all duration-300 ease-in-out',
              header && 'lg:pt-16',
              collapsed ? 'lg:w-16' : 'lg:w-64'
            )}
            style={{
              width: collapsed ? '64px' : '256px',
            }}
            aria-label="側邊導航"
          >
            <div className="flex flex-col flex-1 min-h-0 border-r bg-background/95 backdrop-blur">
              {React.cloneElement(sidebar as React.ReactElement, {
                collapsed,
                onToggle: () => handleToggle(!collapsed),
              })}
            </div>
          </aside>
        )}

        {/* Main content */}
        <main
          className={cn(
            'flex-1 flex flex-col min-w-0 transition-all duration-300 ease-in-out',
            'pb-16 lg:pb-0' // Add bottom padding for mobile bottom nav
          )}
          style={{
            marginLeft: sidebar ? (collapsed ? '64px' : '256px') : '0',
          }}
          id="main-content"
          tabIndex={-1}
        >
          <div className="flex-1 p-4 lg:p-6">{children}</div>
        </main>
      </div>

      {/* Footer */}
      {footer && (
        <footer className="border-t bg-background/95 backdrop-blur hidden lg:block">
          <div className="container mx-auto">{footer}</div>
        </footer>
      )}
    </div>
  );
}
