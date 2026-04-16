/**
 * AnalysisModal Component Tests
 *
 * Unit tests for the AnalysisModal component covering
 * rendering, interactions, and accessibility.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';

import { AnalysisModal } from '../../AnalysisModal';
import type { AnalysisModalProps } from '../../../types';

// Mock the hooks
vi.mock('../../../hooks', () => ({
  useAnalysisModal: vi.fn(),
  useAnalysisTracking: vi.fn(),
}));

// Mock the services
vi.mock('../../../services', () => ({
  generateAnalysis: vi.fn(),
  getCachedAnalysis: vi.fn(),
  copyAnalysisToClipboard: vi.fn(),
  formatAnalysisForSharing: vi.fn(),
}));

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockUseAnalysisModal = vi.mocked(await import('../../../hooks')).useAnalysisModal;

const mockUseAnalysisTracking = vi.mocked(await import('../../../hooks')).useAnalysisTracking;

describe('AnalysisModal', () => {
  let queryClient: QueryClient;

  const defaultProps: AnalysisModalProps = {
    articleId: 'test-article-id',
    articleTitle: 'Test Article Title',
    articleSource: 'Test Source',
    articlePublishedAt: '2024-01-01T00:00:00Z',
    isOpen: true,
    onClose: vi.fn(),
  };

  const mockAnalysis = {
    coreConcepts: ['React', 'TypeScript', 'Testing'],
    applicationScenarios: ['Web Development', 'Component Testing'],
    potentialRisks: ['Performance Issues', 'Complexity'],
    recommendedSteps: ['Setup Tests', 'Write Components'],
    generatedAt: new Date('2024-01-01T12:00:00Z'),
    model: 'llama-3.3-70b' as const,
    rawText: 'Mock analysis text',
  };

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    // Reset mocks
    vi.clearAllMocks();

    // Default mock implementations
    mockUseAnalysisModal.mockReturnValue({
      analysis: null,
      progress: {
        progress: 0,
        status: '準備分析...',
        isComplete: false,
        hasError: false,
      },
      isLoading: false,
      copyAnalysis: vi.fn(),
      shareAnalysis: vi.fn(),
    });

    mockUseAnalysisTracking.mockReturnValue({
      trackAnalysisView: vi.fn(),
      trackAnalysisCopy: vi.fn(),
      trackAnalysisShare: vi.fn(),
    });
  });

  const renderWithProviders = (props: Partial<AnalysisModalProps> = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <AnalysisModal {...defaultProps} {...props} />
      </QueryClientProvider>
    );
  };

  describe('Modal Display', () => {
    it('should display article title and metadata when open', () => {
      renderWithProviders();

      expect(screen.getByText('Test Article Title')).toBeInTheDocument();
      expect(screen.getByText('Test Source')).toBeInTheDocument();
      expect(screen.getByText('2024年1月1日')).toBeInTheDocument();
    });

    it('should not render when closed', () => {
      renderWithProviders({ isOpen: false });

      expect(screen.queryByTestId('analysis-modal')).not.toBeInTheDocument();
    });

    it('should have proper accessibility attributes', () => {
      renderWithProviders();

      const modal = screen.getByTestId('analysis-modal');
      expect(modal).toBeInTheDocument();

      const title = screen.getByRole('heading', { name: 'Test Article Title' });
      expect(title).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show loading spinner when analysis is loading', () => {
      mockUseAnalysisModal.mockReturnValue({
        analysis: null,
        progress: {
          progress: 50,
          status: '分析文章內容...',
          isComplete: false,
          hasError: false,
        },
        isLoading: true,
        copyAnalysis: vi.fn(),
        shareAnalysis: vi.fn(),
      });

      renderWithProviders();

      expect(screen.getByTestId('analysis-loading')).toBeInTheDocument();
      expect(screen.getAllByText('分析文章內容...')).toHaveLength(2); // One in spinner, one in progress
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('should show progress bar with correct width', () => {
      mockUseAnalysisModal.mockReturnValue({
        analysis: null,
        progress: {
          progress: 75,
          status: '生成建議步驟...',
          isComplete: false,
          hasError: false,
        },
        isLoading: true,
        copyAnalysis: vi.fn(),
        shareAnalysis: vi.fn(),
      });

      renderWithProviders();

      const progressBar = document.querySelector('[style*="width: 75%"]');
      expect(progressBar).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should show error message when analysis fails', () => {
      mockUseAnalysisModal.mockReturnValue({
        analysis: null,
        progress: {
          progress: 0,
          status: '',
          isComplete: false,
          hasError: true,
          errorMessage: 'Analysis failed',
        },
        isLoading: false,
        copyAnalysis: vi.fn(),
        shareAnalysis: vi.fn(),
      });

      renderWithProviders();

      expect(screen.getByText('Analysis failed')).toBeInTheDocument();
      expect(screen.getByText('重試')).toBeInTheDocument();
    });
  });

  describe('Analysis Results', () => {
    beforeEach(() => {
      mockUseAnalysisModal.mockReturnValue({
        analysis: mockAnalysis,
        progress: {
          progress: 100,
          status: '分析完成',
          isComplete: true,
          hasError: false,
        },
        isLoading: false,
        copyAnalysis: vi.fn(),
        shareAnalysis: vi.fn(),
      });
    });

    it('should display analysis results when available', () => {
      renderWithProviders();

      expect(screen.getByText('核心技術概念')).toBeInTheDocument();
      expect(screen.getByText('應用場景')).toBeInTheDocument();
      expect(screen.getByText('潛在風險')).toBeInTheDocument();
      expect(screen.getByText('建議步驟')).toBeInTheDocument();

      // Check some content
      expect(screen.getByText('React')).toBeInTheDocument();
      expect(screen.getByText('Web Development')).toBeInTheDocument();
    });

    it('should show analysis metadata', () => {
      renderWithProviders();

      expect(screen.getByText(/分析完成於/)).toBeInTheDocument();
      expect(screen.getByText('llama-3.3-70b')).toBeInTheDocument();
    });

    it('should have copy and share buttons', () => {
      renderWithProviders();

      expect(screen.getByTestId('copy-analysis')).toBeInTheDocument();
      expect(screen.getByTestId('share-analysis')).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    const mockCopyAnalysis = vi.fn();
    const mockShareAnalysis = vi.fn();
    const mockTrackAnalysisCopy = vi.fn();
    const mockTrackAnalysisShare = vi.fn();

    beforeEach(() => {
      mockUseAnalysisModal.mockReturnValue({
        analysis: mockAnalysis,
        progress: {
          progress: 100,
          status: '分析完成',
          isComplete: true,
          hasError: false,
        },
        isLoading: false,
        copyAnalysis: mockCopyAnalysis,
        shareAnalysis: mockShareAnalysis,
      });

      mockUseAnalysisTracking.mockReturnValue({
        trackAnalysisView: vi.fn(),
        trackAnalysisCopy: mockTrackAnalysisCopy,
        trackAnalysisShare: mockTrackAnalysisShare,
      });
    });

    it('should call copyAnalysis when copy button is clicked', async () => {
      renderWithProviders();

      const copyButton = screen.getByTestId('copy-analysis');
      fireEvent.click(copyButton);

      expect(mockCopyAnalysis).toHaveBeenCalled();
      expect(mockTrackAnalysisCopy).toHaveBeenCalled();
    });

    it('should call shareAnalysis when share button is clicked', async () => {
      renderWithProviders();

      const shareButton = screen.getByTestId('share-analysis');
      fireEvent.click(shareButton);

      expect(mockShareAnalysis).toHaveBeenCalled();
      expect(mockTrackAnalysisShare).toHaveBeenCalled();
    });
  });

  describe('Keyboard Navigation', () => {
    it('should be accessible via keyboard', () => {
      renderWithProviders();

      const modal = screen.getByTestId('analysis-modal');
      expect(modal).toBeInTheDocument();

      // Test that modal can receive focus
      const closeButton = screen.getByRole('button', { name: /close/i });
      expect(closeButton).toBeInTheDocument();
    });
  });
});
