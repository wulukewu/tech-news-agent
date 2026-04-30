'use client';

import * as React from 'react';
import { ChevronLeft, ChevronRight, MoreHorizontal } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useI18n } from '@/contexts/I18nContext';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  showFirstLast?: boolean;
  showPrevNext?: boolean;
  siblingCount?: number;
  className?: string;
  disabled?: boolean;
}

/**
 * Pagination - Accessible pagination component with keyboard navigation
 * Supports first/last, prev/next, and page number navigation
 */
export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  showFirstLast = true,
  showPrevNext = true,
  siblingCount = 1,
  className,
  disabled = false,
}: PaginationProps) {
  const { t } = useI18n();
  // Generate page numbers to display
  const getPageNumbers = () => {
    const delta = siblingCount;
    const range = [];
    const rangeWithDots = [];

    // Calculate range around current page
    const left = Math.max(2, currentPage - delta);
    const right = Math.min(totalPages - 1, currentPage + delta);

    // Always show first page
    range.push(1);

    // Add pages around current page
    for (let i = left; i <= right; i++) {
      range.push(i);
    }

    // Always show last page if more than 1 page
    if (totalPages > 1) {
      range.push(totalPages);
    }

    // Remove duplicates and sort
    const uniqueRange = [...new Set(range)].sort((a, b) => a - b);

    // Add dots where there are gaps
    for (let i = 0; i < uniqueRange.length; i++) {
      const current = uniqueRange[i];
      const next = uniqueRange[i + 1];

      rangeWithDots.push(current);

      if (next && next - current > 1) {
        rangeWithDots.push('...');
      }
    }

    return rangeWithDots;
  };

  const pageNumbers = getPageNumbers();

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages && page !== currentPage && !disabled) {
      onPageChange(page);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent, page: number) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handlePageChange(page);
    }
  };

  if (totalPages <= 1) {
    return null;
  }

  return (
    <nav
      role="navigation"
      aria-label={t('ui.pagination-navigation')}
      className={cn(
        'flex items-center justify-center gap-1 animate-in fade-in slide-in-from-bottom-2 duration-500',
        className
      )}
    >
      {/* First page button */}
      {showFirstLast && currentPage > 1 && (
        <Button
          variant="outline"
          size="icon"
          onClick={() => handlePageChange(1)}
          disabled={disabled}
          aria-label={t('ui.pagination-first')}
          className="h-9 w-9 transition-all duration-200 hover:scale-105 animate-in slide-in-from-left-2 duration-300"
        >
          <span className="text-xs">{t('ui.pagination-first-short')}</span>
        </Button>
      )}

      {/* Previous page button */}
      {showPrevNext && (
        <Button
          variant="outline"
          size="icon"
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage <= 1 || disabled}
          aria-label={t('ui.pagination-previous')}
          className="h-9 w-9 transition-all duration-200 hover:scale-105 animate-in slide-in-from-left-2 duration-300 delay-100"
        >
          <ChevronLeft className="h-4 w-4 transition-transform duration-200 hover:-translate-x-0.5" />
        </Button>
      )}

      {/* Page numbers */}
      <div className="flex items-center gap-1">
        {pageNumbers.map((pageNumber, index) => {
          if (pageNumber === '...') {
            return (
              <div
                key={`dots-${index}`}
                className="flex h-9 w-9 items-center justify-center animate-in zoom-in-50 duration-300"
                style={{ animationDelay: `${200 + index * 50}ms` }}
                aria-hidden="true"
              >
                <MoreHorizontal className="h-4 w-4 text-muted-foreground animate-pulse" />
              </div>
            );
          }

          const page = pageNumber as number;
          const isCurrentPage = page === currentPage;

          return (
            <Button
              key={page}
              variant={isCurrentPage ? 'default' : 'outline'}
              size="icon"
              onClick={() => handlePageChange(page)}
              onKeyDown={(e) => handleKeyDown(e, page)}
              disabled={disabled}
              aria-label={t('ui.pagination-page', { page })}
              aria-current={isCurrentPage ? 'page' : undefined}
              className={cn(
                'h-9 w-9 transition-all duration-200 hover:scale-105 animate-in zoom-in-50 duration-300',
                isCurrentPage && 'pointer-events-none scale-110 shadow-md'
              )}
              style={{ animationDelay: `${200 + index * 50}ms` }}
            >
              {page}
            </Button>
          );
        })}
      </div>

      {/* Next page button */}
      {showPrevNext && (
        <Button
          variant="outline"
          size="icon"
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage >= totalPages || disabled}
          aria-label={t('ui.pagination-next')}
          className="h-9 w-9 transition-all duration-200 hover:scale-105 animate-in slide-in-from-right-2 duration-300 delay-100"
        >
          <ChevronRight className="h-4 w-4 transition-transform duration-200 hover:translate-x-0.5" />
        </Button>
      )}

      {/* Last page button */}
      {showFirstLast && currentPage < totalPages && (
        <Button
          variant="outline"
          size="icon"
          onClick={() => handlePageChange(totalPages)}
          disabled={disabled}
          aria-label={t('ui.pagination-last')}
          className="h-9 w-9 transition-all duration-200 hover:scale-105 animate-in slide-in-from-right-2 duration-300"
        >
          <span className="text-xs">{t('ui.pagination-last-short')}</span>
        </Button>
      )}
    </nav>
  );
}

// Additional pagination info component
interface PaginationInfoProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  className?: string;
}

export function PaginationInfo({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  className,
}: PaginationInfoProps) {
  const { t } = useI18n();
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  return (
    <div
      className={cn(
        'text-sm text-muted-foreground animate-in fade-in slide-in-from-bottom-2 duration-500 delay-200',
        className
      )}
    >
      <span className="animate-in slide-in-from-left-2 duration-300">
        {t('ui.pagination-showing', { start: startItem, end: endItem, total: totalItems })}
      </span>
      {totalPages > 1 && (
        <span className="ml-2 animate-in slide-in-from-right-2 duration-300 delay-100">
          {t('ui.pagination-page-info', { current: currentPage, total: totalPages })}
        </span>
      )}
    </div>
  );
}
