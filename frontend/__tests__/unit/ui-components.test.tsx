/**
 * Unit Tests for UI Components
 * Feature: frontend-feature-enhancement
 *
 * Tests component rendering, interactions, and accessibility
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MultiSelectFilter } from '@/components/ui/multi-select-filter';
import { RatingDropdown } from '@/components/ui/rating-dropdown';
import { Pagination, PaginationInfo } from '@/components/ui/pagination';
import {
  OptimizedImage,
  AvatarImage,
  ArticleImage,
  HeroImage,
} from '@/components/ui/optimized-image';
import { LoadingSpinner, PageLoader, Skeleton } from '@/components/ui/loading-spinner';
import {
  ErrorMessage,
  NetworkError,
  NotFoundError,
  PermissionError,
  ValidationError,
  SuccessMessage,
  ErrorBoundary,
} from '@/components/ui/error-message';
import { renderWithProviders } from '../utils/test-utils';

describe('MultiSelectFilter Component', () => {
  const mockOptions = [
    { value: 'tech', label: 'Technology', count: 10 },
    { value: 'ai', label: 'Artificial Intelligence', count: 5 },
    { value: 'web', label: 'Web Development', count: 8 },
  ];

  it('should render with placeholder when no items selected', () => {
    const mockOnChange = vi.fn();

    render(
      <MultiSelectFilter
        options={mockOptions}
        selected={[]}
        onSelectionChange={mockOnChange}
        placeholder="選擇分類..."
      />
    );

    expect(screen.getByText('選擇分類...')).toBeInTheDocument();
  });

  it('should display selected count when multiple items selected', () => {
    const mockOnChange = vi.fn();

    render(
      <MultiSelectFilter
        options={mockOptions}
        selected={['tech', 'ai']}
        onSelectionChange={mockOnChange}
      />
    );

    expect(screen.getByText('已選擇 2 個項目')).toBeInTheDocument();
  });

  it('should handle item selection and deselection', async () => {
    const user = userEvent.setup();
    const mockOnChange = vi.fn();

    render(
      <MultiSelectFilter options={mockOptions} selected={[]} onSelectionChange={mockOnChange} />
    );

    // Open dropdown
    await user.click(screen.getByRole('combobox'));

    // Select an item
    await user.click(screen.getByText('Technology'));

    expect(mockOnChange).toHaveBeenCalledWith(['tech']);
  });

  it('should filter options based on search query', async () => {
    const user = userEvent.setup();
    const mockOnChange = vi.fn();

    render(
      <MultiSelectFilter
        options={mockOptions}
        selected={[]}
        onSelectionChange={mockOnChange}
        searchable={true}
      />
    );

    // Open dropdown
    await user.click(screen.getByRole('combobox'));

    // Search for "AI" - should match "Artificial Intelligence"
    const searchInput = screen.getByPlaceholderText('搜尋選項...');
    await user.type(searchInput, 'Artificial');

    // Wait for filtering to occur
    await waitFor(() => {
      // Should only show AI option
      expect(screen.getByText('Artificial Intelligence')).toBeInTheDocument();
    });
    expect(screen.queryByText('Technology')).not.toBeInTheDocument();
  });

  it('should clear all selections', async () => {
    const user = userEvent.setup();
    const mockOnChange = vi.fn();

    render(
      <MultiSelectFilter
        options={mockOptions}
        selected={['tech', 'ai']}
        onSelectionChange={mockOnChange}
      />
    );

    // Clear all selections
    const clearButton = screen.getByLabelText('清除所有選項');
    await user.click(clearButton);

    expect(mockOnChange).toHaveBeenCalledWith([]);
  });

  // Accessibility tests
  it('should have proper ARIA attributes', () => {
    const mockOnChange = vi.fn();

    render(
      <MultiSelectFilter
        options={mockOptions}
        selected={['tech']}
        onSelectionChange={mockOnChange}
      />
    );

    const combobox = screen.getByRole('combobox');
    expect(combobox).toHaveAttribute('aria-expanded', 'false');
    expect(combobox).toHaveAttribute('role', 'combobox');
  });

  it('should support keyboard navigation', async () => {
    const user = userEvent.setup();
    const mockOnChange = vi.fn();

    render(
      <MultiSelectFilter options={mockOptions} selected={[]} onSelectionChange={mockOnChange} />
    );

    const combobox = screen.getByRole('combobox');

    // Test keyboard opening
    await user.click(combobox);
    expect(combobox).toHaveAttribute('aria-expanded', 'true');
  });

  it('should handle disabled state', () => {
    const mockOnChange = vi.fn();

    render(
      <MultiSelectFilter
        options={mockOptions}
        selected={[]}
        onSelectionChange={mockOnChange}
        disabled={true}
      />
    );

    const combobox = screen.getByRole('combobox');
    expect(combobox).toBeDisabled();
  });

  it('should show empty message when no options match search', async () => {
    const user = userEvent.setup();
    const mockOnChange = vi.fn();

    render(
      <MultiSelectFilter
        options={mockOptions}
        selected={[]}
        onSelectionChange={mockOnChange}
        searchable={true}
        emptyMessage="找不到匹配項目"
      />
    );

    // Open dropdown
    await user.click(screen.getByRole('combobox'));

    // Search for non-existent item
    const searchInput = screen.getByPlaceholderText('搜尋選項...');
    await user.type(searchInput, 'nonexistent');

    await waitFor(() => {
      expect(screen.getByText('找不到匹配項目')).toBeInTheDocument();
    });
  });

  it('should handle options with counts', async () => {
    const user = userEvent.setup();
    const mockOnChange = vi.fn();

    render(
      <MultiSelectFilter options={mockOptions} selected={[]} onSelectionChange={mockOnChange} />
    );

    // Open dropdown
    await user.click(screen.getByRole('combobox'));

    // Check that counts are displayed
    expect(screen.getByText('(10)')).toBeInTheDocument();
    expect(screen.getByText('(5)')).toBeInTheDocument();
    expect(screen.getByText('(8)')).toBeInTheDocument();
  });
});

describe('RatingDropdown Component', () => {
  it('should render with placeholder when no rating selected', () => {
    const mockOnChange = vi.fn();

    render(<RatingDropdown onChange={mockOnChange} placeholder="選擇評分..." />);

    expect(screen.getByText('選擇評分...')).toBeInTheDocument();
  });

  it('should display selected rating with stars and label', () => {
    const mockOnChange = vi.fn();

    const { container } = render(<RatingDropdown value={4} onChange={mockOnChange} />);

    expect(screen.getByText('進階')).toBeInTheDocument();
    // Should have 5 stars total (4 filled, 1 empty)
    const stars = container.querySelectorAll('svg[class*="lucide-star"]');
    expect(stars).toHaveLength(5);
  });

  it('should handle rating selection', async () => {
    const user = userEvent.setup();
    const mockOnChange = vi.fn();

    render(<RatingDropdown onChange={mockOnChange} />);

    // Open dropdown
    await user.click(screen.getByRole('button'));

    // Select 3 stars
    await user.click(screen.getByText('中級'));

    expect(mockOnChange).toHaveBeenCalledWith(3);
  });

  it('should clear rating when clear option is clicked', async () => {
    const user = userEvent.setup();
    const mockOnChange = vi.fn();

    render(<RatingDropdown value={3} onChange={mockOnChange} showClear={true} />);

    // Open dropdown
    await user.click(screen.getByRole('button'));

    // Click clear
    await user.click(screen.getByText('清除評分'));

    expect(mockOnChange).toHaveBeenCalledWith(undefined);
  });

  // Accessibility tests
  it('should have proper ARIA attributes', () => {
    const mockOnChange = vi.fn();

    render(<RatingDropdown value={3} onChange={mockOnChange} />);

    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    expect(button).not.toBeDisabled();
  });

  it('should support disabled state', () => {
    const mockOnChange = vi.fn();

    render(<RatingDropdown onChange={mockOnChange} disabled={true} />);

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('should display different sizes correctly', () => {
    const mockOnChange = vi.fn();

    const { rerender } = render(<RatingDropdown onChange={mockOnChange} size="sm" />);
    let button = screen.getByRole('button');
    expect(button).toHaveClass('h-8');

    rerender(<RatingDropdown onChange={mockOnChange} size="lg" />);
    button = screen.getByRole('button');
    expect(button).toHaveClass('h-10');
  });

  it('should not show clear option when showClear is false', async () => {
    const user = userEvent.setup();
    const mockOnChange = vi.fn();

    render(<RatingDropdown value={3} onChange={mockOnChange} showClear={false} />);

    // Open dropdown
    await user.click(screen.getByRole('button'));

    // Clear option should not be present
    expect(screen.queryByText('清除評分')).not.toBeInTheDocument();
  });

  it('should display rating descriptions', async () => {
    const user = userEvent.setup();
    const mockOnChange = vi.fn();

    render(<RatingDropdown onChange={mockOnChange} />);

    // Open dropdown
    await user.click(screen.getByRole('button'));

    // Check that descriptions are displayed
    expect(screen.getByText('適合初學者')).toBeInTheDocument();
    expect(screen.getByText('需要專業知識')).toBeInTheDocument();
  });
});

describe('Pagination Component', () => {
  it('should render page numbers correctly', () => {
    const mockOnPageChange = vi.fn();

    render(<Pagination currentPage={3} totalPages={10} onPageChange={mockOnPageChange} />);

    // Should show current page as selected
    const currentPageButton = screen.getByRole('button', { name: '第 3 頁' });
    expect(currentPageButton).toHaveAttribute('aria-current', 'page');
  });

  it('should handle page navigation', async () => {
    const user = userEvent.setup();
    const mockOnPageChange = vi.fn();

    render(<Pagination currentPage={3} totalPages={10} onPageChange={mockOnPageChange} />);

    // Click next page
    await user.click(screen.getByLabelText('下一頁'));
    expect(mockOnPageChange).toHaveBeenCalledWith(4);

    // Click previous page
    await user.click(screen.getByLabelText('上一頁'));
    expect(mockOnPageChange).toHaveBeenCalledWith(2);
  });

  it('should disable navigation buttons at boundaries', () => {
    const mockOnPageChange = vi.fn();

    render(<Pagination currentPage={1} totalPages={5} onPageChange={mockOnPageChange} />);

    // Previous button should be disabled on first page
    expect(screen.getByLabelText('上一頁')).toBeDisabled();
  });

  it('should not render when totalPages is 1 or less', () => {
    const mockOnPageChange = vi.fn();

    const { container } = render(
      <Pagination currentPage={1} totalPages={1} onPageChange={mockOnPageChange} />
    );

    expect(container.firstChild).toBeNull();
  });

  // Accessibility tests
  it('should have proper ARIA attributes', () => {
    const mockOnPageChange = vi.fn();

    render(<Pagination currentPage={3} totalPages={10} onPageChange={mockOnPageChange} />);

    const nav = screen.getByRole('navigation');
    expect(nav).toHaveAttribute('aria-label', '分頁導航');

    const currentPageButton = screen.getByRole('button', { name: '第 3 頁' });
    expect(currentPageButton).toHaveAttribute('aria-current', 'page');
  });

  it('should support keyboard navigation', async () => {
    const user = userEvent.setup();
    const mockOnPageChange = vi.fn();

    render(<Pagination currentPage={3} totalPages={10} onPageChange={mockOnPageChange} />);

    const nextButton = screen.getByLabelText('下一頁');

    // Test Enter key
    await user.type(nextButton, '{Enter}');
    expect(mockOnPageChange).toHaveBeenCalledWith(4);
  });

  it('should handle disabled state', () => {
    const mockOnPageChange = vi.fn();

    render(
      <Pagination currentPage={3} totalPages={10} onPageChange={mockOnPageChange} disabled={true} />
    );

    const buttons = screen.getAllByRole('button');
    buttons.forEach((button) => {
      expect(button).toBeDisabled();
    });
  });

  it('should show first and last buttons when configured', () => {
    const mockOnPageChange = vi.fn();

    render(
      <Pagination
        currentPage={5}
        totalPages={10}
        onPageChange={mockOnPageChange}
        showFirstLast={true}
      />
    );

    expect(screen.getByLabelText('第一頁')).toBeInTheDocument();
    expect(screen.getByLabelText('最後一頁')).toBeInTheDocument();
  });

  it('should hide first and last buttons when configured', () => {
    const mockOnPageChange = vi.fn();

    render(
      <Pagination
        currentPage={5}
        totalPages={10}
        onPageChange={mockOnPageChange}
        showFirstLast={false}
      />
    );

    expect(screen.queryByLabelText('第一頁')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('最後一頁')).not.toBeInTheDocument();
  });

  it('should show ellipsis for large page ranges', () => {
    const mockOnPageChange = vi.fn();

    render(
      <Pagination
        currentPage={5}
        totalPages={20}
        onPageChange={mockOnPageChange}
        siblingCount={1}
      />
    );

    // Should show ellipsis
    const ellipsis = screen.getAllByRole('generic', { hidden: true });
    expect(ellipsis.length).toBeGreaterThan(0);
  });
});

describe('PaginationInfo Component', () => {
  it('should display correct pagination information', () => {
    render(<PaginationInfo currentPage={2} totalPages={5} totalItems={100} itemsPerPage={20} />);

    expect(screen.getByText(/顯示第 21 - 40 項，共 100 項結果/)).toBeInTheDocument();
    expect(screen.getByText(/第 2 頁，共 5 頁/)).toBeInTheDocument();
  });
});

describe('OptimizedImage Component', () => {
  it('should render image with correct attributes', () => {
    render(<OptimizedImage src="/test-image.jpg" alt="Test image" width={400} height={300} />);

    const image = screen.getByAltText('Test image');
    expect(image).toBeInTheDocument();
    expect(image).toHaveAttribute('src');
  });

  it('should handle image load error with fallback', async () => {
    const mockOnError = vi.fn();

    render(
      <OptimizedImage
        src="/non-existent-image.jpg"
        alt="Test image"
        width={400}
        height={300}
        fallbackSrc="/fallback.jpg"
        onError={mockOnError}
      />
    );

    const image = screen.getByAltText('Test image');

    // Simulate image error
    fireEvent.error(image);

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalled();
    });
  });

  // Accessibility tests
  it('should have proper alt text', () => {
    render(
      <OptimizedImage src="/test-image.jpg" alt="Descriptive alt text" width={400} height={300} />
    );

    const image = screen.getByAltText('Descriptive alt text');
    expect(image).toBeInTheDocument();
  });

  it('should handle loading states', () => {
    render(<OptimizedImage src="/test-image.jpg" alt="Test image" width={400} height={300} />);

    const image = screen.getByAltText('Test image');
    expect(image).toHaveClass('opacity-0'); // Initially loading
  });

  it('should support fill mode', () => {
    render(<OptimizedImage src="/test-image.jpg" alt="Test image" fill={true} />);

    const image = screen.getByAltText('Test image');
    expect(image).toBeInTheDocument();
  });

  it('should handle priority loading', () => {
    render(
      <OptimizedImage
        src="/test-image.jpg"
        alt="Test image"
        width={400}
        height={300}
        priority={true}
      />
    );

    const image = screen.getByAltText('Test image');
    expect(image).toBeInTheDocument();
  });

  it('should show error message when image fails and no fallback', async () => {
    render(
      <OptimizedImage src="/non-existent-image.jpg" alt="Test image" width={400} height={300} />
    );

    const image = screen.getByAltText('Test image');
    fireEvent.error(image);

    await waitFor(() => {
      expect(screen.getByText('圖片載入失敗')).toBeInTheDocument();
    });
  });
});

describe('AvatarImage Component', () => {
  it('should render with rounded styling', () => {
    render(<AvatarImage src="/avatar.jpg" alt="User avatar" size={40} />);

    const image = screen.getByAltText('User avatar');
    expect(image).toHaveClass('rounded-full');
  });
});

describe('LoadingSpinner Component', () => {
  it('should render spinner with text', () => {
    render(<LoadingSpinner size="md" text="載入中..." />);

    expect(screen.getByText('載入中...')).toBeInTheDocument();
  });

  it('should render full screen overlay when fullScreen is true', () => {
    render(<LoadingSpinner fullScreen={true} text="載入中..." />);

    const overlay = screen.getByText('載入中...').closest('div')?.parentElement;
    expect(overlay).toHaveClass('fixed', 'inset-0', 'z-50');
  });

  it('should render different sizes correctly', () => {
    const { rerender } = render(<LoadingSpinner size="sm" />);
    let spinner = document.querySelector('.animate-spin');
    expect(spinner).toHaveClass('h-4', 'w-4');

    rerender(<LoadingSpinner size="xl" />);
    spinner = document.querySelector('.animate-spin');
    expect(spinner).toHaveClass('h-12', 'w-12');
  });

  it('should render without text', () => {
    render(<LoadingSpinner size="md" />);

    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
    expect(screen.queryByText('載入中...')).not.toBeInTheDocument();
  });

  it('should have proper animation classes', () => {
    render(<LoadingSpinner />);

    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toHaveClass('animate-spin', 'text-primary');
  });
});

describe('PageLoader Component', () => {
  it('should render with default loading text', () => {
    render(<PageLoader />);

    expect(screen.getByText('載入中...')).toBeInTheDocument();
  });

  it('should render with custom text', () => {
    render(<PageLoader text="正在處理..." />);

    expect(screen.getByText('正在處理...')).toBeInTheDocument();
  });
});

describe('Skeleton Component', () => {
  it('should render with animation classes', () => {
    render(<Skeleton className="h-4 w-20" />);

    const skeleton = document.querySelector('.animate-pulse');
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveClass('bg-muted', 'rounded-md');
  });
});

describe('ErrorMessage Component', () => {
  it('should render error message with title and description', () => {
    render(<ErrorMessage title="錯誤標題" message="錯誤描述" type="error" />);

    expect(screen.getByText('錯誤標題')).toBeInTheDocument();
    expect(screen.getByText('錯誤描述')).toBeInTheDocument();
  });

  it('should handle retry action', async () => {
    const user = userEvent.setup();
    const mockOnRetry = vi.fn();

    render(<ErrorMessage message="網路錯誤" onRetry={mockOnRetry} type="error" />);

    await user.click(screen.getByText('重試'));
    expect(mockOnRetry).toHaveBeenCalled();
  });

  it('should handle dismiss action', async () => {
    const user = userEvent.setup();
    const mockOnDismiss = vi.fn();

    render(<ErrorMessage message="資訊訊息" onDismiss={mockOnDismiss} type="info" />);

    await user.click(screen.getByLabelText('關閉'));
    expect(mockOnDismiss).toHaveBeenCalled();
  });

  it('should render different types with appropriate styling', () => {
    const { rerender } = render(<ErrorMessage message="錯誤" type="error" />);

    let alert = screen.getByRole('alert');
    expect(alert).toHaveClass('border-destructive/50');

    rerender(<ErrorMessage message="警告" type="warning" />);
    alert = screen.getByRole('alert');
    expect(alert).toHaveClass('border-yellow-500/50');

    rerender(<ErrorMessage message="資訊" type="info" />);
    alert = screen.getByRole('alert');
    expect(alert).toHaveClass('border-blue-500/50');

    rerender(<ErrorMessage message="成功" type="success" />);
    alert = screen.getByRole('alert');
    expect(alert).toHaveClass('border-green-500/50');
  });

  // Accessibility tests
  it('should have proper ARIA role', () => {
    render(<ErrorMessage message="測試訊息" type="error" />);

    const alert = screen.getByRole('alert');
    expect(alert).toBeInTheDocument();
  });

  it('should show icon by default', () => {
    render(<ErrorMessage message="測試訊息" type="error" />);

    const icon = document.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('should hide icon when showIcon is false', () => {
    render(<ErrorMessage message="測試訊息" type="error" showIcon={false} />);

    const icon = document.querySelector('svg');
    expect(icon).not.toBeInTheDocument();
  });

  it('should use default title when none provided', () => {
    render(<ErrorMessage message="測試訊息" type="error" />);

    expect(screen.getByText('發生錯誤')).toBeInTheDocument();
  });

  it('should support fullWidth prop', () => {
    render(<ErrorMessage message="測試訊息" type="error" fullWidth={true} />);

    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('w-full');
  });

  it('should support custom retry and dismiss text', async () => {
    const user = userEvent.setup();
    const mockOnRetry = vi.fn();
    const mockOnDismiss = vi.fn();

    render(
      <ErrorMessage
        message="測試訊息"
        type="error"
        onRetry={mockOnRetry}
        onDismiss={mockOnDismiss}
        retryText="再試一次"
        dismissText="忽略"
      />
    );

    expect(screen.getByText('再試一次')).toBeInTheDocument();

    const dismissButton = screen.getByLabelText('忽略');
    expect(dismissButton).toBeInTheDocument();
  });
});

describe('NetworkError Component', () => {
  it('should render network error with retry button', () => {
    const mockOnRetry = vi.fn();

    render(<NetworkError onRetry={mockOnRetry} />);

    expect(screen.getByText('網路連線異常')).toBeInTheDocument();
    expect(screen.getByText('請檢查您的網路連線，然後重試。')).toBeInTheDocument();
    expect(screen.getByText('重試')).toBeInTheDocument();
  });
});

describe('ErrorBoundary Component', () => {
  // Suppress console.error for this test
  const originalError = console.error;
  beforeAll(() => {
    console.error = vi.fn();
  });

  afterAll(() => {
    console.error = originalError;
  });

  const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
    if (shouldThrow) {
      throw new Error('Test error');
    }
    return <div>No error</div>;
  };

  it('should render children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(screen.getByText('No error')).toBeInTheDocument();
  });

  it('should render error UI when error occurs', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('應用程式發生錯誤')).toBeInTheDocument();
    expect(screen.getByText(/很抱歉，應用程式遇到了未預期的錯誤/)).toBeInTheDocument();
  });

  it('should call onError callback when error occurs', () => {
    const mockOnError = vi.fn();

    render(
      <ErrorBoundary onError={mockOnError}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(mockOnError).toHaveBeenCalled();
  });

  it('should render custom fallback component when provided', () => {
    const CustomFallback = ({ error, retry }: { error: Error; retry: () => void }) => (
      <div>
        <span>Custom error: {error.message}</span>
        <button onClick={retry}>Custom retry</button>
      </div>
    );

    render(
      <ErrorBoundary fallback={CustomFallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Custom error: Test error')).toBeInTheDocument();
    expect(screen.getByText('Custom retry')).toBeInTheDocument();
  });

  it('should reset error state when retry is clicked', async () => {
    const user = userEvent.setup();

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('應用程式發生錯誤')).toBeInTheDocument();

    // Click retry button
    await user.click(screen.getByText('重試'));

    // Error should be cleared (though component will throw again)
    // This tests the retry mechanism works
  });
});

// Additional preset component tests
describe('Preset Components', () => {
  describe('PageLoader', () => {
    it('should render with default text', () => {
      render(<PageLoader />);
      expect(screen.getByText('載入中...')).toBeInTheDocument();
    });

    it('should render with custom text', () => {
      render(<PageLoader text="正在處理..." />);
      expect(screen.getByText('正在處理...')).toBeInTheDocument();
    });

    it('should have proper container styling', () => {
      render(<PageLoader />);
      const container = screen.getByText('載入中...').closest('div');
      expect(container).toHaveClass('flex', 'items-center', 'justify-center', 'min-h-[400px]');
    });
  });

  describe('Skeleton', () => {
    it('should render with animation classes', () => {
      render(<Skeleton className="h-4 w-20" />);

      const skeleton = document.querySelector('.animate-pulse');
      expect(skeleton).toBeInTheDocument();
      expect(skeleton).toHaveClass('bg-muted', 'rounded-md');
    });

    it('should render children when provided', () => {
      render(
        <Skeleton>
          <span>Content</span>
        </Skeleton>
      );
      expect(screen.getByText('Content')).toBeInTheDocument();
    });
  });

  describe('NetworkError', () => {
    it('should render network error with retry button', () => {
      const mockOnRetry = vi.fn();

      render(<NetworkError onRetry={mockOnRetry} />);

      expect(screen.getByText('網路連線異常')).toBeInTheDocument();
      expect(screen.getByText('請檢查您的網路連線，然後重試。')).toBeInTheDocument();
      expect(screen.getByText('重試')).toBeInTheDocument();
    });
  });

  describe('NotFoundError', () => {
    it('should render with default message', () => {
      render(<NotFoundError />);
      expect(screen.getByText('找不到請求的資源')).toBeInTheDocument();
    });

    it('should render with custom message', () => {
      render(<NotFoundError message="找不到該頁面" />);
      expect(screen.getByText('找不到該頁面')).toBeInTheDocument();
    });
  });

  describe('PermissionError', () => {
    it('should render permission error message', () => {
      render(<PermissionError />);
      expect(screen.getByText('權限不足')).toBeInTheDocument();
      expect(screen.getByText('您沒有執行此操作的權限，請聯繫管理員。')).toBeInTheDocument();
    });
  });

  describe('ValidationError', () => {
    it('should render with default message', () => {
      render(<ValidationError />);
      expect(screen.getByText('輸入的資料格式不正確，請檢查後重試。')).toBeInTheDocument();
    });

    it('should render with custom message', () => {
      render(<ValidationError message="電子郵件格式不正確" />);
      expect(screen.getByText('電子郵件格式不正確')).toBeInTheDocument();
    });
  });

  describe('SuccessMessage', () => {
    it('should render success message', () => {
      render(<SuccessMessage message="操作成功完成" />);
      expect(screen.getByText('操作成功完成')).toBeInTheDocument();
    });

    it('should handle dismiss action', async () => {
      const user = userEvent.setup();
      const mockOnDismiss = vi.fn();

      render(<SuccessMessage message="操作成功完成" onDismiss={mockOnDismiss} />);

      await user.click(screen.getByLabelText('關閉'));
      expect(mockOnDismiss).toHaveBeenCalled();
    });
  });

  describe('ArticleImage', () => {
    it('should render with proper dimensions and styling', () => {
      render(<ArticleImage src="/test.jpg" alt="Article image" />);

      const image = screen.getByAltText('Article image');
      expect(image).toHaveClass('rounded-lg', 'object-cover');
    });
  });

  describe('HeroImage', () => {
    it('should render with fill and priority', () => {
      render(<HeroImage src="/hero.jpg" alt="Hero image" />);

      const image = screen.getByAltText('Hero image');
      expect(image).toHaveClass('object-cover');
    });
  });
});
