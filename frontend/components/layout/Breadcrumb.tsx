'use client';

import React from 'react';
import Link from 'next/link';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface BreadcrumbItem {
  label: string;
  href?: string;
  current?: boolean;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
  showHome?: boolean;
}

/**
 * Breadcrumb - Navigation breadcrumb component
 * Provides hierarchical navigation with accessibility support
 */
export function Breadcrumb({ items, className, showHome = true }: BreadcrumbProps) {
  const allItems = showHome
    ? [{ label: 'Dashboard', href: '/dashboard/articles' }, ...items]
    : items;

  return (
    <nav
      className={cn('flex items-center space-x-1 text-sm text-muted-foreground', className)}
      aria-label="麵包屑導航"
    >
      <ol className="flex items-center space-x-1">
        {allItems.map((item, index) => {
          const isLast = index === allItems.length - 1;
          const isCurrent = item.current || isLast;

          return (
            <li key={index} className="flex items-center">
              {index > 0 && (
                <ChevronRight
                  className="h-4 w-4 mx-1 text-muted-foreground/50"
                  aria-hidden="true"
                />
              )}

              {item.href && !isCurrent ? (
                <Link
                  href={item.href}
                  className="hover:text-foreground transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded-sm px-1 py-0.5"
                  aria-current={isCurrent ? 'page' : undefined}
                >
                  {index === 0 && showHome ? (
                    <div className="flex items-center gap-1">
                      <Home className="h-4 w-4" aria-hidden="true" />
                      <span className="sr-only sm:not-sr-only">{item.label}</span>
                    </div>
                  ) : (
                    item.label
                  )}
                </Link>
              ) : (
                <span
                  className={cn('px-1 py-0.5', isCurrent && 'text-foreground font-medium')}
                  aria-current={isCurrent ? 'page' : undefined}
                >
                  {index === 0 && showHome ? (
                    <div className="flex items-center gap-1">
                      <Home className="h-4 w-4" aria-hidden="true" />
                      <span className="sr-only sm:not-sr-only">{item.label}</span>
                    </div>
                  ) : (
                    item.label
                  )}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
