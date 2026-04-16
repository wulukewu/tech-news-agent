/**
 * AI Analysis API service
 *
 * Handles communication with the backend AI analysis endpoints
 * including analysis generation, caching, and error handling.
 */

import { apiClient, handleApiError } from '@/lib/api/client';
import type { AnalysisResult, AnalysisApiResponse } from '../types';

/**
 * Generate AI analysis for an article
 *
 * @param articleId - The article ID to analyze
 * @returns Promise resolving to analysis result
 *
 * **Validates: Requirements 2.3**
 * THE AI_Analysis_Panel SHALL call the backend API to generate
 * detailed technical analysis using Llama 3.3 70B
 */
export async function generateAnalysis(articleId: string): Promise<AnalysisResult> {
  try {
    const response = await apiClient.post<AnalysisApiResponse>(
      `/api/articles/${articleId}/analysis`,
      {
        model: 'llama-3.3-70b',
        include_sections: [
          'core_concepts',
          'application_scenarios',
          'potential_risks',
          'recommended_steps',
        ],
      }
    );

    if (!response.data.success) {
      throw new Error(response.data.error || 'Analysis generation failed');
    }

    const data = response.data.data;

    return {
      coreConcepts: data.core_concepts,
      applicationScenarios: data.application_scenarios,
      potentialRisks: data.potential_risks,
      recommendedSteps: data.recommended_steps,
      generatedAt: new Date(data.generated_at),
      model: data.model as 'llama-3.1-8b' | 'llama-3.3-70b',
      rawText: data.raw_text,
    };
  } catch (error: any) {
    const apiError = handleApiError(error);
    throw new Error(apiError.message);
  }
}

/**
 * Get cached analysis for an article
 *
 * @param articleId - The article ID
 * @returns Promise resolving to cached analysis or null if not found
 *
 * **Validates: Requirements 2.6**
 * THE AI_Analysis_Panel SHALL cache analysis results to avoid
 * regenerating for the same article
 */
export async function getCachedAnalysis(articleId: string): Promise<AnalysisResult | null> {
  try {
    const response = await apiClient.get<AnalysisApiResponse>(
      `/api/articles/${articleId}/analysis`
    );

    if (!response.data.success || !response.data.data) {
      return null;
    }

    const data = response.data.data;

    return {
      coreConcepts: data.core_concepts,
      applicationScenarios: data.application_scenarios,
      potentialRisks: data.potential_risks,
      recommendedSteps: data.recommended_steps,
      generatedAt: new Date(data.generated_at),
      model: data.model as 'llama-3.1-8b' | 'llama-3.3-70b',
      rawText: data.raw_text,
    };
  } catch (error: any) {
    // If analysis doesn't exist, return null instead of throwing
    if (error.response?.status === 404) {
      return null;
    }
    throw error;
  }
}

/**
 * Copy analysis text to clipboard
 *
 * @param analysisText - The analysis text to copy
 * @returns Promise resolving to success status
 *
 * **Validates: Requirements 2.7**
 * THE AI_Analysis_Panel SHALL provide a "Copy Analysis" button
 * to copy the text to clipboard
 */
export async function copyAnalysisToClipboard(analysisText: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(analysisText);
      return true;
    } else {
      // Fallback for older browsers or non-secure contexts
      const textArea = document.createElement('textarea');
      textArea.value = analysisText;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      textArea.style.top = '-999999px';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();

      const success = document.execCommand('copy');
      document.body.removeChild(textArea);
      return success;
    }
  } catch (error) {
    console.error('Failed to copy to clipboard:', error);
    return false;
  }
}

/**
 * Generate shareable link for analysis
 *
 * @param articleId - The article ID
 * @param analysisId - The analysis ID (optional)
 * @returns Shareable URL
 *
 * **Validates: Requirements 2.8**
 * THE AI_Analysis_Panel SHALL provide a "Share Analysis" button
 * to generate a shareable link
 */
export function generateShareableLink(articleId: string, analysisId?: string): string {
  const baseUrl = typeof window !== 'undefined' ? window.location.origin : '';
  const path = analysisId
    ? `/articles/${articleId}/analysis/${analysisId}`
    : `/articles/${articleId}/analysis`;

  return `${baseUrl}${path}`;
}

/**
 * Format analysis for sharing
 *
 * @param analysis - The analysis result
 * @param articleTitle - The article title
 * @returns Formatted text for sharing
 */
export function formatAnalysisForSharing(analysis: AnalysisResult, articleTitle: string): string {
  const sections = [
    `# AI 深度分析：${articleTitle}`,
    '',
    `分析時間：${analysis.generatedAt.toLocaleString('zh-TW')}`,
    `分析模型：${analysis.model}`,
    '',
    '## 核心技術概念',
    ...analysis.coreConcepts.map((concept) => `• ${concept}`),
    '',
    '## 應用場景',
    ...analysis.applicationScenarios.map((scenario) => `• ${scenario}`),
    '',
    '## 潛在風險',
    ...analysis.potentialRisks.map((risk) => `• ${risk}`),
    '',
    '## 建議步驟',
    ...analysis.recommendedSteps.map((step) => `• ${step}`),
    '',
    '---',
    '由 Tech News Agent AI 分析生成',
  ];

  return sections.join('\n');
}
