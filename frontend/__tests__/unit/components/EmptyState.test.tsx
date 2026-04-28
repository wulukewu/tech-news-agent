import { render, screen } from '@testing-library/react';
import { EmptyState } from '@/components/EmptyState';
import { Rss, FileText, BookMarked } from 'lucide-react';

describe('EmptyState Component', () => {
  describe('Basic Rendering', () => {
    it('should render title and description', () => {
      render(<EmptyState title="Test Title" description="Test Description" />);

      expect(screen.getByText('Test Title')).toBeInTheDocument();
      expect(screen.getByText('Test Description')).toBeInTheDocument();
    });

    it('should render custom icon when provided', () => {
      const { container } = render(
        <EmptyState
          title="Test"
          description="Test"
          icon={<div data-testid="custom-icon">Custom Icon</div>}
        />
      );

      expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
    });
  });

  describe('Variant Support', () => {
    it('should render no-subscriptions variant with Rss icon', () => {
      const { container } = render(
        <EmptyState
          type="no-subscriptions"
          title="No Subscriptions"
          description="Subscribe to some feeds"
        />
      );

      // Check that an SVG icon is rendered (Lucide icons render as SVG)
      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should render no-articles variant with FileText icon', () => {
      const { container } = render(
        <EmptyState type="no-articles" title="No Articles" description="No articles yet" />
      );

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('should render no-reading-list variant with BookMarked icon', () => {
      const { container } = render(
        <EmptyState
          type="no-reading-list"
          title="No Reading List"
          description="Your reading list is empty"
        />
      );

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('Action Buttons', () => {
    it('should render primary action button', () => {
      const handleClick = vi.fn();

      render(
        <EmptyState
          title="Test"
          description="Test"
          primaryAction={{
            label: 'Primary Action',
            onClick: handleClick,
          }}
        />
      );

      const button = screen.getByText('Primary Action');
      expect(button).toBeInTheDocument();

      button.click();
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('should render both primary and secondary actions', () => {
      const handlePrimary = vi.fn();
      const handleSecondary = vi.fn();

      render(
        <EmptyState
          title="Test"
          description="Test"
          primaryAction={{
            label: 'Primary',
            onClick: handlePrimary,
          }}
          secondaryAction={{
            label: 'Secondary',
            onClick: handleSecondary,
          }}
        />
      );

      expect(screen.getByText('Primary')).toBeInTheDocument();
      expect(screen.getByText('Secondary')).toBeInTheDocument();
    });

    it('should support legacy action prop for backward compatibility', () => {
      render(
        <EmptyState title="Test" description="Test" action={<button>Legacy Action</button>} />
      );

      expect(screen.getByText('Legacy Action')).toBeInTheDocument();
    });
  });

  describe('Scheduler Status', () => {
    it('should display scheduler status when provided', () => {
      const schedulerStatus = {
        lastExecutionTime: new Date('2024-01-01T12:00:00Z'),
        nextScheduledTime: new Date('2024-01-01T13:00:00Z'),
        isRunning: false,
        lastExecutionArticleCount: 10,
        estimatedTimeUntilArticles: '5-10 分鐘',
      };

      render(
        <EmptyState
          type="no-articles"
          title="No Articles"
          description="Waiting for articles"
          schedulerStatus={schedulerStatus}
        />
      );

      expect(screen.getByText(/上次執行時間/)).toBeInTheDocument();
      expect(screen.getByText(/預計 5-10 分鐘 後會有新文章/)).toBeInTheDocument();
    });

    it('should not display scheduler status when not provided', () => {
      render(
        <EmptyState type="no-articles" title="No Articles" description="Waiting for articles" />
      );

      expect(screen.queryByText(/上次執行時間/)).not.toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('should render with dashed border card', () => {
      const { container } = render(<EmptyState title="Test" description="Test" />);

      const card = container.querySelector('.border-dashed');
      expect(card).toBeInTheDocument();
    });

    it('should center content', () => {
      const { container } = render(<EmptyState title="Test" description="Test" />);

      const content = container.querySelector('.items-center.justify-center');
      expect(content).toBeInTheDocument();
    });
  });
});
