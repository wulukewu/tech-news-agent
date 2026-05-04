import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { FeedHealthIndicator } from '@/features/subscriptions/components/FeedHealthIndicator';

describe('FeedHealthIndicator', () => {
  describe('Status Display', () => {
    it('should display healthy status correctly', () => {
      render(
        <FeedHealthIndicator lastUpdateTime={new Date('2024-01-15T10:00:00Z')} status="healthy" />
      );
      expect(screen.getByText('Healthy')).toBeInTheDocument();
    });

    it('should display warning status correctly', () => {
      render(
        <FeedHealthIndicator lastUpdateTime={new Date('2024-01-15T10:00:00Z')} status="warning" />
      );
      expect(screen.getByText('Warning')).toBeInTheDocument();
    });

    it('should display error status correctly', () => {
      render(
        <FeedHealthIndicator lastUpdateTime={new Date('2024-01-15T10:00:00Z')} status="error" />
      );
      expect(screen.getByText('Error')).toBeInTheDocument();
    });

    it('should display unknown status correctly', () => {
      render(
        <FeedHealthIndicator lastUpdateTime={new Date('2024-01-15T10:00:00Z')} status="unknown" />
      );
      expect(screen.getByText('Unknown')).toBeInTheDocument();
    });
  });

  describe('Last Update Time', () => {
    it('should display "Never updated" when lastUpdateTime is null', () => {
      render(<FeedHealthIndicator lastUpdateTime={null} status="unknown" />);
      expect(screen.getByText('Never updated')).toBeInTheDocument();
    });

    it('should display "Never updated" when lastUpdateTime is undefined', () => {
      render(<FeedHealthIndicator lastUpdateTime={undefined} status="unknown" />);
      expect(screen.getByText('Never updated')).toBeInTheDocument();
    });

    it('should handle string date format', () => {
      render(<FeedHealthIndicator lastUpdateTime="2024-01-15T10:00:00Z" status="healthy" />);
      expect(screen.getByText('Healthy')).toBeInTheDocument();
    });
  });

  describe('Visual Styling', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <FeedHealthIndicator
          lastUpdateTime={new Date()}
          status="healthy"
          className="custom-class"
        />
      );
      expect(container.querySelector('.custom-class')).toBeInTheDocument();
    });

    it('should render with correct badge for each status', () => {
      const statuses: Array<'healthy' | 'warning' | 'error' | 'unknown'> = [
        'healthy',
        'warning',
        'error',
        'unknown',
      ];
      const labels = { healthy: 'Healthy', warning: 'Warning', error: 'Error', unknown: 'Unknown' };
      statuses.forEach((status) => {
        const { unmount } = render(
          <FeedHealthIndicator lastUpdateTime={new Date()} status={status} />
        );
        expect(screen.getByText(labels[status])).toBeInTheDocument();
        unmount();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle very old update times', () => {
      render(
        <FeedHealthIndicator lastUpdateTime={new Date('2020-01-01T00:00:00Z')} status="warning" />
      );
      expect(screen.getByText('Warning')).toBeInTheDocument();
    });

    it('should handle invalid date strings', () => {
      render(<FeedHealthIndicator lastUpdateTime={'invalid-date' as any} status="error" />);
      expect(screen.getByText('Never updated')).toBeInTheDocument();
      expect(screen.getByText('Error')).toBeInTheDocument();
    });
  });
});
