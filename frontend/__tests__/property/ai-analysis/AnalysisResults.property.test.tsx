/**
 * Property Tests for AI Analysis Results Display
 * Feature: frontend-feature-enhancement, Task 5.6
 *
 * These tests validate the correctness properties of the analysis results display
 * including structure completeness, clipboard functionality, and share link generation.
 *
 * **Validates: Requirements 2.4, 2.7, 2.8**
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import fc from 'fast-check';
import { AnalysisModal } from '@/features/ai-analysis/components/AnalysisModal';
import {
  copyAnalysisToClipboard,
  formatAnalysisForSharing,
  generateShareableLink,
} from '@/features/ai-analysis/services';
import { renderWithProviders } from '../../utils/test-utils';
import {
  analysisResultArbitrary,
  analysisModalPropsArbitrary,
  articleIdArbitrary,
} from '../../utils/arbitraries';

// Mock clipboard API
const mockClipboard = {
  writeText: vi.fn(),
};

Object.assign(navigator, {
  clipboard: mockClipboard,
});

// Mock window.isSecureContext
Object.defineProperty(window, 'isSecureContext', {
  writable: true,
  value: true,
});

describe('AI Analysis Results Properties', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockClipboard.writeText.mockResolvedValue(undefined);
  });

  /**
   * Property 11: 分析結果結構完整性
   * For any successful analysis response, the displayed result should contain
   * all required sections: core technical concepts, application scenarios,
   * potential risks, and recommended next steps
   *
   * **Validates: Requirements 2.4**
   * THE AI_Analysis_Panel SHALL display analysis sections:
   * core technical concepts, application scenarios, potential risks, and recommended steps
   */
  it('Property 11: Analysis results should contain all required sections', () => {
    fc.assert(
      fc.property(analysisResultArbitrary, (analysis) => {
        // Mock the hook to return analysis data
        vi.mock('@/features/ai-analysis/hooks', () => ({
          useAnalysisModal: () => ({
            analysis,
            progress: {
              progress: 100,
              status: '分析完成',
              isComplete: true,
              hasError: false,
            },
            isLoading: false,
            copyAnalysis: vi.fn(),
            shareAnalysis: vi.fn(),
          }),
          useAnalysisTracking: () => ({
            trackAnalysisView: vi.fn(),
            trackAnalysisCopy: vi.fn(),
            trackAnalysisShare: vi.fn(),
          }),
        }));

        renderWithProviders(
          <AnalysisModal
            articleId="test-id"
            articleTitle="Test Article"
            articleSource="Test Source"
            articlePublishedAt={new Date().toISOString()}
            isOpen={true}
            onClose={vi.fn()}
          />
        );

        // All four required sections should be present
        expect(screen.getByText(/核心技術概念/i)).toBeInTheDocument();
        expect(screen.getByText(/應用場景/i)).toBeInTheDocument();
        expect(screen.getByText(/潛在風險/i)).toBeInTheDocument();
        expect(screen.getByText(/建議步驟/i)).toBeInTheDocument();

        // Each section should display its items
        if (analysis.coreConcepts.length > 0) {
          analysis.coreConcepts.forEach((concept) => {
            expect(screen.getByText(concept)).toBeInTheDocument();
          });
        }

        if (analysis.applicationScenarios.length > 0) {
          analysis.applicationScenarios.forEach((scenario) => {
            expect(screen.getByText(scenario)).toBeInTheDocument();
          });
        }

        if (analysis.potentialRisks.length > 0) {
          analysis.potentialRisks.forEach((risk) => {
            expect(screen.getByText(risk)).toBeInTheDocument();
          });
        }

        if (analysis.recommendedSteps.length > 0) {
          analysis.recommendedSteps.forEach((step) => {
            expect(screen.getByText(step)).toBeInTheDocument();
          });
        }

        vi.unmock('@/features/ai-analysis/hooks');
      }),
      { numRuns: 30 }
    );
  });

  /**
   * Property 14: 剪貼簿功能
   * For any completed analysis, the "Copy Analysis" button should successfully
   * copy the analysis text to the user's clipboard
   *
   * **Validates: Requirements 2.7**
   * THE AI_Analysis_Panel SHALL provide a "Copy Analysis" button
   * to copy the text to clipboard
   */
  it('Property 14: Copy Analysis button should copy text to clipboard', async () => {
    const user = userEvent.setup();

    await fc.assert(
      fc.asyncProperty(analysisResultArbitrary, async (analysis) => {
        const mockCopyAnalysis = vi.fn(async () => {
          const formattedText = formatAnalysisForSharing(analysis, 'Test Article');
          await copyAnalysisToClipboard(formattedText);
        });

        vi.mock('@/features/ai-analysis/hooks', () => ({
          useAnalysisModal: () => ({
            analysis,
            progress: {
              progress: 100,
              status: '分析完成',
              isComplete: true,
              hasError: false,
            },
            isLoading: false,
            copyAnalysis: mockCopyAnalysis,
            shareAnalysis: vi.fn(),
          }),
          useAnalysisTracking: () => ({
            trackAnalysisView: vi.fn(),
            trackAnalysisCopy: vi.fn(),
            trackAnalysisShare: vi.fn(),
          }),
        }));

        renderWithProviders(
          <AnalysisModal
            articleId="test-id"
            articleTitle="Test Article"
            articleSource="Test Source"
            articlePublishedAt={new Date().toISOString()}
            isOpen={true}
            onClose={vi.fn()}
          />
        );

        // Find and click the copy button
        const copyButton = screen.getByTestId('copy-analysis');
        expect(copyButton).toBeInTheDocument();

        await user.click(copyButton);

        // Copy function should have been called
        expect(mockCopyAnalysis).toHaveBeenCalledTimes(1);

        vi.unmock('@/features/ai-analysis/hooks');
      }),
      { numRuns: 20 }
    );
  });

  /**
   * Property 15: 分享連結生成
   * For any article analysis, the "Share Analysis" button should generate
   * a valid shareable link that provides access to the analysis
   *
   * **Validates: Requirements 2.8**
   * THE AI_Analysis_Panel SHALL provide a "Share Analysis" button
   * to generate a shareable link
   */
  it('Property 15: Share Analysis button should generate valid shareable link', async () => {
    const user = userEvent.setup();

    await fc.assert(
      fc.asyncProperty(articleIdArbitrary, analysisResultArbitrary, async (articleId, analysis) => {
        const mockShareAnalysis = vi.fn(() => {
          const shareUrl = generateShareableLink(articleId);
          copyAnalysisToClipboard(shareUrl);
        });

        vi.mock('@/features/ai-analysis/hooks', () => ({
          useAnalysisModal: () => ({
            analysis,
            progress: {
              progress: 100,
              status: '分析完成',
              isComplete: true,
              hasError: false,
            },
            isLoading: false,
            copyAnalysis: vi.fn(),
            shareAnalysis: mockShareAnalysis,
          }),
          useAnalysisTracking: () => ({
            trackAnalysisView: vi.fn(),
            trackAnalysisCopy: vi.fn(),
            trackAnalysisShare: vi.fn(),
          }),
        }));

        renderWithProviders(
          <AnalysisModal
            articleId={articleId}
            articleTitle="Test Article"
            articleSource="Test Source"
            articlePublishedAt={new Date().toISOString()}
            isOpen={true}
            onClose={vi.fn()}
          />
        );

        // Find and click the share button
        const shareButton = screen.getByTestId('share-analysis');
        expect(shareButton).toBeInTheDocument();

        await user.click(shareButton);

        // Share function should have been called
        expect(mockShareAnalysis).toHaveBeenCalledTimes(1);

        // Verify the generated link format
        const shareLink = generateShareableLink(articleId);
        expect(shareLink).toContain(articleId);
        expect(shareLink).toMatch(/\/articles\/[^/]+\/analysis/);

        vi.unmock('@/features/ai-analysis/hooks');
      }),
      { numRuns: 20 }
    );
  });

  /**
   * Property: Clipboard copy should work with any analysis content
   * For any analysis text, the clipboard API should be called correctly
   */
  it('Property: Clipboard API should be called with correct content', async () => {
    await fc.assert(
      fc.asyncProperty(fc.string({ minLength: 1, maxLength: 5000 }), async (analysisText) => {
        mockClipboard.writeText.mockClear();

        const success = await copyAnalysisToClipboard(analysisText);

        // Should return true for successful copy
        expect(success).toBe(true);

        // Clipboard API should be called with the text
        expect(mockClipboard.writeText).toHaveBeenCalledWith(analysisText);
        expect(mockClipboard.writeText).toHaveBeenCalledTimes(1);
      }),
      { numRuns: 30 }
    );
  });

  /**
   * Property: Formatted analysis should include all sections
   * For any analysis result, the formatted text should contain all sections
   */
  it('Property: Formatted analysis should include all required sections', () => {
    fc.assert(
      fc.property(
        analysisResultArbitrary,
        fc.string({ minLength: 1, maxLength: 200 }), // article title
        (analysis, articleTitle) => {
          const formattedText = formatAnalysisForSharing(analysis, articleTitle);

          // Should include article title
          expect(formattedText).toContain(articleTitle);

          // Should include all section headers
          expect(formattedText).toContain('核心技術概念');
          expect(formattedText).toContain('應用場景');
          expect(formattedText).toContain('潛在風險');
          expect(formattedText).toContain('建議步驟');

          // Should include model information
          expect(formattedText).toContain(analysis.model);

          // Should include all items from each section
          analysis.coreConcepts.forEach((concept) => {
            expect(formattedText).toContain(concept);
          });

          analysis.applicationScenarios.forEach((scenario) => {
            expect(formattedText).toContain(scenario);
          });

          analysis.potentialRisks.forEach((risk) => {
            expect(formattedText).toContain(risk);
          });

          analysis.recommendedSteps.forEach((step) => {
            expect(formattedText).toContain(step);
          });

          // Should include attribution
          expect(formattedText).toContain('Tech News Agent');
        }
      ),
      { numRuns: 30 }
    );
  });

  /**
   * Property: Empty sections should be handled gracefully
   * For any analysis with empty sections, the display should show appropriate message
   */
  it('Property: Empty sections should display appropriate message', () => {
    fc.assert(
      fc.property(
        fc.record({
          coreConcepts: fc.constant([]),
          applicationScenarios: fc.constant([]),
          potentialRisks: fc.constant([]),
          recommendedSteps: fc.constant([]),
          generatedAt: fc.date(),
          model: fc.constantFrom('llama-3.1-8b', 'llama-3.3-70b'),
          rawText: fc.string(),
        }),
        (analysis) => {
          vi.mock('@/features/ai-analysis/hooks', () => ({
            useAnalysisModal: () => ({
              analysis,
              progress: {
                progress: 100,
                status: '分析完成',
                isComplete: true,
                hasError: false,
              },
              isLoading: false,
              copyAnalysis: vi.fn(),
              shareAnalysis: vi.fn(),
            }),
            useAnalysisTracking: () => ({
              trackAnalysisView: vi.fn(),
              trackAnalysisCopy: vi.fn(),
              trackAnalysisShare: vi.fn(),
            }),
          }));

          renderWithProviders(
            <AnalysisModal
              articleId="test-id"
              articleTitle="Test Article"
              articleSource="Test Source"
              articlePublishedAt={new Date().toISOString()}
              isOpen={true}
              onClose={vi.fn()}
            />
          );

          // Should show "no content" message for empty sections
          const emptyMessages = screen.getAllByText(/此部分暫無內容/i);
          expect(emptyMessages.length).toBeGreaterThan(0);

          vi.unmock('@/features/ai-analysis/hooks');
        }
      ),
      { numRuns: 15 }
    );
  });

  /**
   * Property: Analysis metadata should be displayed correctly
   * For any analysis, the generation time and model should be shown
   */
  it('Property: Analysis metadata should be displayed', () => {
    fc.assert(
      fc.property(analysisResultArbitrary, (analysis) => {
        vi.mock('@/features/ai-analysis/hooks', () => ({
          useAnalysisModal: () => ({
            analysis,
            progress: {
              progress: 100,
              status: '分析完成',
              isComplete: true,
              hasError: false,
            },
            isLoading: false,
            copyAnalysis: vi.fn(),
            shareAnalysis: vi.fn(),
          }),
          useAnalysisTracking: () => ({
            trackAnalysisView: vi.fn(),
            trackAnalysisCopy: vi.fn(),
            trackAnalysisShare: vi.fn(),
          }),
        }));

        renderWithProviders(
          <AnalysisModal
            articleId="test-id"
            articleTitle="Test Article"
            articleSource="Test Source"
            articlePublishedAt={new Date().toISOString()}
            isOpen={true}
            onClose={vi.fn()}
          />
        );

        // Model badge should be displayed
        expect(screen.getByText(analysis.model)).toBeInTheDocument();

        // Generation time should be displayed
        expect(screen.getByText(/分析完成於/i)).toBeInTheDocument();

        // Success indicator should be present
        expect(screen.getByText(/分析完成/i)).toBeInTheDocument();

        vi.unmock('@/features/ai-analysis/hooks');
      }),
      { numRuns: 20 }
    );
  });

  /**
   * Property: Action buttons should be visible when analysis is complete
   * For any completed analysis, both copy and share buttons should be present
   */
  it('Property: Action buttons should be visible for completed analysis', () => {
    fc.assert(
      fc.property(analysisResultArbitrary, (analysis) => {
        vi.mock('@/features/ai-analysis/hooks', () => ({
          useAnalysisModal: () => ({
            analysis,
            progress: {
              progress: 100,
              status: '分析完成',
              isComplete: true,
              hasError: false,
            },
            isLoading: false,
            copyAnalysis: vi.fn(),
            shareAnalysis: vi.fn(),
          }),
          useAnalysisTracking: () => ({
            trackAnalysisView: vi.fn(),
            trackAnalysisCopy: vi.fn(),
            trackAnalysisShare: vi.fn(),
          }),
        }));

        renderWithProviders(
          <AnalysisModal
            articleId="test-id"
            articleTitle="Test Article"
            articleSource="Test Source"
            articlePublishedAt={new Date().toISOString()}
            isOpen={true}
            onClose={vi.fn()}
          />
        );

        // Both action buttons should be present
        expect(screen.getByTestId('copy-analysis')).toBeInTheDocument();
        expect(screen.getByTestId('share-analysis')).toBeInTheDocument();

        // Buttons should have proper labels
        expect(screen.getByText(/複製分析/i)).toBeInTheDocument();
        expect(screen.getByText(/分享分析/i)).toBeInTheDocument();

        vi.unmock('@/features/ai-analysis/hooks');
      }),
      { numRuns: 20 }
    );
  });

  /**
   * Property: Shareable link should be valid URL
   * For any article ID, the generated shareable link should be a valid URL
   */
  it('Property: Generated shareable links should be valid URLs', () => {
    fc.assert(
      fc.property(articleIdArbitrary, (articleId) => {
        const shareLink = generateShareableLink(articleId);

        // Should be a valid URL when combined with base URL
        expect(() => new URL(shareLink, 'http://localhost')).not.toThrow();

        // Should contain the article ID
        expect(shareLink).toContain(articleId);

        // Should follow the expected path pattern
        expect(shareLink).toMatch(/\/articles\/[^/]+\/analysis/);
      }),
      { numRuns: 50 }
    );
  });
});
