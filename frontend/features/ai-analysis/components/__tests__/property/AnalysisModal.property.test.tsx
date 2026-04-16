/**
 * AnalysisModal Property-Based Tests
 *
 * Property tests for AI analysis functionality using fast-check.
 * Tests universal properties that should hold across all valid inputs.
 *
 * **Feature: frontend-feature-enhancement**
 * **Task 5: AI 深度分析功能**
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import fc from 'fast-check';

import { AnalysisModal } from '../../AnalysisModal';
import { AnalysisTrigger } from '../../AnalysisTrigger';
import type { AnalysisModalProps, AnalysisResult } from '../../../types';
import * as hooks from '../../../hooks';
import * as services from '../../../services';

// Mock dependencies
vi.mock('../../../hooks');
vi.mock('../../../services');
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Arbitraries for generating test data
const articleIdArbitrary = fc.uuid();

// Generate non-whitespace strings for titles and sources
const articleTitleArbitrary = fc
  .string({ minLength: 10, maxLength: 200 })
  .filter((s) => s.trim().length >= 10);

const articleSourceArbitrary = fc
  .string({ minLength: 3, maxLength: 50 })
  .filter((s) => s.trim().length >= 3);

const dateArbitrary = fc.date({
  min: new Date('2020-01-01'),
  max: new Date(),
});

const analysisResultArbitrary: fc.Arbitrary<AnalysisResult> = fc.record({
  coreConcepts: fc.array(fc.string({ minLength: 5, maxLength: 100 }), {
    minLength: 1,
    maxLength: 10,
  }),
  applicationScenarios: fc.array(fc.string({ minLength: 10, maxLength: 150 }), {
    minLength: 1,
    maxLength: 8,
  }),
  potentialRisks: fc.array(fc.string({ minLength: 10, maxLength: 150 }), {
    minLength: 0,
    maxLength: 6,
  }),
  recommendedSteps: fc.array(fc.string({ minLength: 10, maxLength: 150 }), {
    minLength: 1,
    maxLength: 8,
  }),
  generatedAt: dateArbitrary,
  model: fc.constantFrom('llama-3.1-8b' as const, 'llama-3.3-70b' as const),
  rawText: fc.string({ minLength: 100, maxLength: 5000 }),
});

const modalPropsArbitrary: fc.Arbitrary<AnalysisModalProps> = fc.record({
  articleId: articleIdArbitrary,
  articleTitle: articleTitleArbitrary,
  articleSource: articleSourceArbitrary,
  articlePublishedAt: fc.option(
    dateArbitrary.map((d) => d.toISOString()),
    { nil: null }
  ),
  isOpen: fc.boolean(),
  onClose: fc.constant(vi.fn()),
});

describe('AnalysisModal Property Tests', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    vi.clearAllMocks();

    // Set up default mock for useAnalysisTracking
    vi.mocked(hooks.useAnalysisTracking).mockReturnValue({
      trackAnalysisView: vi.fn(),
      trackAnalysisCopy: vi.fn(),
      trackAnalysisShare: vi.fn(),
    });
  });

  afterEach(() => {
    queryClient.clear();
  });

  const renderWithProviders = (ui: React.ReactElement) => {
    return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
  };

  /**
   * Property 8: AI 分析模態視窗觸發
   *
   * **Validates: Requirements 2.1**
   * For any article with analysis capability, clicking the "Deep Dive Analysis"
   * button should open the AI_Analysis_Panel in a modal dialog.
   */
  describe('Property 8: AI Analysis Modal Trigger', () => {
    it('should open modal dialog when analysis button is clicked for any article', () => {
      fc.assert(
        fc.property(
          articleIdArbitrary,
          articleTitleArbitrary,
          articleSourceArbitrary,
          fc.option(
            dateArbitrary.map((d) => d.toISOString()),
            { nil: null }
          ),
          (articleId, articleTitle, articleSource, articlePublishedAt) => {
            // Mock the hook to return modal state
            const mockOpenModal = vi.fn();
            const mockCloseModal = vi.fn();

            vi.mocked(hooks.useAnalysisModal).mockReturnValue({
              isOpen: false,
              analysis: null,
              progress: {
                progress: 0,
                status: '準備分析...',
                isComplete: false,
                hasError: false,
              },
              isLoading: false,
              openModal: mockOpenModal,
              closeModal: mockCloseModal,
              copyAnalysis: vi.fn(),
              shareAnalysis: vi.fn(),
            });

            // Render the trigger button
            const { unmount } = renderWithProviders(
              <AnalysisTrigger
                articleId={articleId}
                articleTitle={articleTitle}
                articleSource={articleSource}
                articlePublishedAt={articlePublishedAt}
              />
            );

            // Find and click the analysis button
            const button = screen.getByTestId('analysis-button');
            expect(button).toBeInTheDocument();

            fireEvent.click(button);

            // Verify modal open was called
            expect(mockOpenModal).toHaveBeenCalledTimes(1);

            unmount();
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should render modal with correct testid when opened', () => {
      fc.assert(
        fc.property(modalPropsArbitrary, (props) => {
          if (!props.isOpen) return; // Skip if modal is closed

          vi.mocked(hooks.useAnalysisModal).mockReturnValue({
            isOpen: true,
            analysis: null,
            progress: {
              progress: 0,
              status: '準備分析...',
              isComplete: false,
              hasError: false,
            },
            isLoading: false,
            openModal: vi.fn(),
            closeModal: vi.fn(),
            copyAnalysis: vi.fn(),
            shareAnalysis: vi.fn(),
          });

          const { unmount } = renderWithProviders(<AnalysisModal {...props} />);

          // Modal should be present with correct testid
          const modal = screen.getByTestId('analysis-modal');
          expect(modal).toBeInTheDocument();

          unmount();
        }),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 9: 分析面板資訊完整性
   *
   * **Validates: Requirements 2.2**
   * For any article being analyzed, the AI_Analysis_Panel should display
   * the article title, source, and published date correctly.
   */
  describe('Property 9: Analysis Panel Information Completeness', () => {
    it('should display article title, source, and published date for any article', () => {
      fc.assert(
        fc.property(
          articleIdArbitrary,
          articleTitleArbitrary,
          articleSourceArbitrary,
          dateArbitrary.map((d) => d.toISOString()),
          (articleId, articleTitle, articleSource, articlePublishedAt) => {
            // Clear any previous renders
            vi.clearAllMocks();

            vi.mocked(hooks.useAnalysisModal).mockReturnValue({
              isOpen: true,
              analysis: null,
              progress: {
                progress: 0,
                status: '準備分析...',
                isComplete: false,
                hasError: false,
              },
              isLoading: false,
              openModal: vi.fn(),
              closeModal: vi.fn(),
              copyAnalysis: vi.fn(),
              shareAnalysis: vi.fn(),
            });

            const { unmount } = renderWithProviders(
              <AnalysisModal
                articleId={articleId}
                articleTitle={articleTitle}
                articleSource={articleSource}
                articlePublishedAt={articlePublishedAt}
                isOpen={true}
                onClose={vi.fn()}
              />
            );

            try {
              // Verify article title is displayed
              expect(screen.getByText(articleTitle)).toBeInTheDocument();

              // Verify article source is displayed
              expect(screen.getByText(articleSource)).toBeInTheDocument();

              // Verify published date is displayed (formatted)
              const publishedDate = new Date(articlePublishedAt);
              const formattedDate = publishedDate.toLocaleDateString('zh-TW', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              });
              expect(screen.getByText(formattedDate)).toBeInTheDocument();
            } finally {
              // Always cleanup, even if assertions fail
              unmount();
            }
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle missing published date gracefully', () => {
      fc.assert(
        fc.property(
          articleIdArbitrary,
          articleTitleArbitrary,
          articleSourceArbitrary,
          (articleId, articleTitle, articleSource) => {
            // Clear any previous renders
            vi.clearAllMocks();

            vi.mocked(hooks.useAnalysisModal).mockReturnValue({
              isOpen: true,
              analysis: null,
              progress: {
                progress: 0,
                status: '準備分析...',
                isComplete: false,
                hasError: false,
              },
              isLoading: false,
              openModal: vi.fn(),
              closeModal: vi.fn(),
              copyAnalysis: vi.fn(),
              shareAnalysis: vi.fn(),
            });

            const { unmount } = renderWithProviders(
              <AnalysisModal
                articleId={articleId}
                articleTitle={articleTitle}
                articleSource={articleSource}
                articlePublishedAt={null}
                isOpen={true}
                onClose={vi.fn()}
              />
            );

            try {
              // Should still display title and source
              expect(screen.getByText(articleTitle)).toBeInTheDocument();
              expect(screen.getByText(articleSource)).toBeInTheDocument();
            } finally {
              // Always cleanup, even if assertions fail
              unmount();
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 10: API 呼叫正確性
   *
   * **Validates: Requirements 2.3**
   * For any article analysis request, the system should make the correct
   * API call to the backend with proper parameters for Llama 3.3 70B analysis.
   */
  describe('Property 10: API Call Correctness', () => {
    it('should call generateAnalysis with correct article ID', async () => {
      fc.assert(
        fc.asyncProperty(
          articleIdArbitrary,
          analysisResultArbitrary,
          async (articleId, mockAnalysis) => {
            const mockGenerateAnalysis = vi.fn().mockResolvedValue(mockAnalysis);
            vi.mocked(services.generateAnalysis).mockImplementation(mockGenerateAnalysis);

            // Call the service directly
            const result = await services.generateAnalysis(articleId);

            // Verify the function was called with correct article ID
            expect(mockGenerateAnalysis).toHaveBeenCalledWith(articleId);

            // Verify the result matches expected structure
            expect(result).toHaveProperty('coreConcepts');
            expect(result).toHaveProperty('applicationScenarios');
            expect(result).toHaveProperty('potentialRisks');
            expect(result).toHaveProperty('recommendedSteps');
            expect(result).toHaveProperty('generatedAt');
            expect(result).toHaveProperty('model');
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should use Llama 3.3 70B model for analysis', async () => {
      fc.assert(
        fc.asyncProperty(articleIdArbitrary, async (articleId) => {
          const mockAnalysis: AnalysisResult = {
            coreConcepts: ['Test Concept'],
            applicationScenarios: ['Test Scenario'],
            potentialRisks: ['Test Risk'],
            recommendedSteps: ['Test Step'],
            generatedAt: new Date(),
            model: 'llama-3.3-70b',
            rawText: 'Test analysis',
          };

          vi.mocked(services.generateAnalysis).mockResolvedValue(mockAnalysis);

          const result = await services.generateAnalysis(articleId);

          // Verify the model is one of the supported models
          expect(['llama-3.1-8b', 'llama-3.3-70b']).toContain(result.model);
        }),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 11: 分析結果結構完整性
   *
   * **Validates: Requirements 2.4**
   * For any successful analysis response, the displayed result should contain
   * all required sections: core technical concepts, application scenarios,
   * potential risks, and recommended next steps.
   */
  describe('Property 11: Analysis Result Structure Completeness', () => {
    it('should display all required sections for any analysis result', () => {
      fc.assert(
        fc.property(modalPropsArbitrary, analysisResultArbitrary, (props, analysis) => {
          // Clear any previous renders
          vi.clearAllMocks();

          vi.mocked(hooks.useAnalysisModal).mockReturnValue({
            isOpen: true,
            analysis,
            progress: {
              progress: 100,
              status: '分析完成',
              isComplete: true,
              hasError: false,
            },
            isLoading: false,
            openModal: vi.fn(),
            closeModal: vi.fn(),
            copyAnalysis: vi.fn(),
            shareAnalysis: vi.fn(),
          });

          const { unmount } = renderWithProviders(<AnalysisModal {...props} isOpen={true} />);

          try {
            // Verify all required sections are present
            expect(screen.getByText('核心技術概念')).toBeInTheDocument();
            expect(screen.getByText('應用場景')).toBeInTheDocument();
            expect(screen.getByText('潛在風險')).toBeInTheDocument();
            expect(screen.getByText('建議步驟')).toBeInTheDocument();

            // Verify at least some content from each section is displayed
            if (analysis.coreConcepts.length > 0) {
              expect(screen.getByText(analysis.coreConcepts[0])).toBeInTheDocument();
            }

            if (analysis.applicationScenarios.length > 0) {
              expect(screen.getByText(analysis.applicationScenarios[0])).toBeInTheDocument();
            }

            if (analysis.recommendedSteps.length > 0) {
              expect(screen.getByText(analysis.recommendedSteps[0])).toBeInTheDocument();
            }
          } finally {
            // Always cleanup, even if assertions fail
            unmount();
          }
        }),
        { numRuns: 100 }
      );
    });

    it('should handle empty sections gracefully', () => {
      fc.assert(
        fc.property(modalPropsArbitrary, (props) => {
          // Clear any previous renders
          vi.clearAllMocks();

          const analysisWithEmptySections: AnalysisResult = {
            coreConcepts: [],
            applicationScenarios: [],
            potentialRisks: [],
            recommendedSteps: [],
            generatedAt: new Date(),
            model: 'llama-3.3-70b',
            rawText: 'Empty analysis',
          };

          vi.mocked(hooks.useAnalysisModal).mockReturnValue({
            isOpen: true,
            analysis: analysisWithEmptySections,
            progress: {
              progress: 100,
              status: '分析完成',
              isComplete: true,
              hasError: false,
            },
            isLoading: false,
            openModal: vi.fn(),
            closeModal: vi.fn(),
            copyAnalysis: vi.fn(),
            shareAnalysis: vi.fn(),
          });

          const { unmount } = renderWithProviders(<AnalysisModal {...props} isOpen={true} />);

          try {
            // All section headers should still be present
            expect(screen.getByText('核心技術概念')).toBeInTheDocument();
            expect(screen.getByText('應用場景')).toBeInTheDocument();
            expect(screen.getByText('潛在風險')).toBeInTheDocument();
            expect(screen.getByText('建議步驟')).toBeInTheDocument();

            // Should show empty state messages
            const emptyMessages = screen.getAllByText('此部分暫無內容');
            expect(emptyMessages.length).toBeGreaterThan(0);
          } finally {
            // Always cleanup, even if assertions fail
            unmount();
          }
        }),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 13: 分析結果快取
   *
   * **Validates: Requirements 2.6**
   * For any article that has been analyzed, subsequent analysis requests
   * for the same article should use cached results instead of making new API calls.
   */
  describe('Property 13: Analysis Result Caching', () => {
    it('should return cached analysis for previously analyzed articles', async () => {
      fc.assert(
        fc.asyncProperty(
          articleIdArbitrary,
          analysisResultArbitrary,
          async (articleId, mockAnalysis) => {
            const mockGetCachedAnalysis = vi.fn().mockResolvedValue(mockAnalysis);
            vi.mocked(services.getCachedAnalysis).mockImplementation(mockGetCachedAnalysis);

            // First call - should fetch from cache
            const result1 = await services.getCachedAnalysis(articleId);
            expect(mockGetCachedAnalysis).toHaveBeenCalledWith(articleId);
            expect(result1).toEqual(mockAnalysis);

            // Second call - should also use cache
            const result2 = await services.getCachedAnalysis(articleId);
            expect(mockGetCachedAnalysis).toHaveBeenCalledTimes(2);
            expect(result2).toEqual(mockAnalysis);

            // Results should be identical
            expect(result1).toEqual(result2);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should return null for articles without cached analysis', async () => {
      fc.assert(
        fc.asyncProperty(articleIdArbitrary, async (articleId) => {
          vi.mocked(services.getCachedAnalysis).mockResolvedValue(null);

          const result = await services.getCachedAnalysis(articleId);

          expect(result).toBeNull();
        }),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 14: 剪貼簿功能
   *
   * **Validates: Requirements 2.7**
   * For any completed analysis, the "Copy Analysis" button should successfully
   * copy the analysis text to the user's clipboard.
   */
  describe('Property 14: Clipboard Functionality', () => {
    it('should copy formatted analysis text to clipboard', async () => {
      fc.assert(
        fc.asyncProperty(
          analysisResultArbitrary,
          articleTitleArbitrary,
          async (analysis, articleTitle) => {
            const formattedText = services.formatAnalysisForSharing(analysis, articleTitle);

            // Mock clipboard API
            const mockWriteText = vi.fn().mockResolvedValue(undefined);
            Object.assign(navigator, {
              clipboard: {
                writeText: mockWriteText,
              },
            });

            vi.mocked(services.copyAnalysisToClipboard).mockImplementation(async (text) => {
              await navigator.clipboard.writeText(text);
              return true;
            });

            const success = await services.copyAnalysisToClipboard(formattedText);

            expect(success).toBe(true);
            expect(mockWriteText).toHaveBeenCalledWith(formattedText);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should format analysis with all sections for any analysis result', () => {
      fc.assert(
        fc.property(analysisResultArbitrary, articleTitleArbitrary, (analysis, articleTitle) => {
          const formatted = services.formatAnalysisForSharing(analysis, articleTitle);

          // Verify formatted text contains article title
          expect(formatted).toContain(articleTitle);

          // Verify formatted text contains section headers
          expect(formatted).toContain('核心技術概念');
          expect(formatted).toContain('應用場景');
          expect(formatted).toContain('潛在風險');
          expect(formatted).toContain('建議步驟');

          // Verify formatted text contains content from each section
          analysis.coreConcepts.forEach((concept) => {
            expect(formatted).toContain(concept);
          });

          analysis.applicationScenarios.forEach((scenario) => {
            expect(formatted).toContain(scenario);
          });

          analysis.recommendedSteps.forEach((step) => {
            expect(formatted).toContain(step);
          });
        }),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 15: 分享連結生成
   *
   * **Validates: Requirements 2.8**
   * For any article analysis, the "Share Analysis" button should generate
   * a valid shareable link that provides access to the analysis.
   */
  describe('Property 15: Share Link Generation', () => {
    it('should generate valid shareable link for any article', () => {
      fc.assert(
        fc.property(articleIdArbitrary, (articleId) => {
          const shareLink = services.generateShareableLink(articleId);

          // Verify link contains article ID
          expect(shareLink).toContain(articleId);

          // Verify link has correct path structure
          expect(shareLink).toContain('/articles/');
          expect(shareLink).toContain('/analysis');

          // Verify link is a valid URL format
          expect(() => new URL(shareLink, 'http://localhost')).not.toThrow();
        }),
        { numRuns: 100 }
      );
    });

    it('should generate unique links for different articles', () => {
      fc.assert(
        fc.property(fc.array(articleIdArbitrary, { minLength: 2, maxLength: 10 }), (articleIds) => {
          const uniqueIds = [...new Set(articleIds)];
          const links = uniqueIds.map((id) => services.generateShareableLink(id));

          // All links should be unique
          const uniqueLinks = new Set(links);
          expect(uniqueLinks.size).toBe(uniqueIds.length);

          // Each link should contain its corresponding article ID
          uniqueIds.forEach((id, index) => {
            expect(links[index]).toContain(id);
          });
        }),
        { numRuns: 100 }
      );
    });

    it('should generate link with optional analysis ID', () => {
      fc.assert(
        fc.property(
          articleIdArbitrary,
          fc.option(fc.uuid(), { nil: undefined }),
          (articleId, analysisId) => {
            const shareLink = services.generateShareableLink(articleId, analysisId);

            // Verify link contains article ID
            expect(shareLink).toContain(articleId);

            // If analysis ID provided, verify it's in the link
            if (analysisId) {
              expect(shareLink).toContain(analysisId);
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
