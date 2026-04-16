/**
 * AI Analysis feature types
 *
 * Defines interfaces for AI analysis functionality including
 * analysis results, modal states, and API responses.
 */

export interface AnalysisResult {
  /** Core technical concepts extracted from the article */
  coreConcepts: string[];
  /** Practical application scenarios */
  applicationScenarios: string[];
  /** Potential risks and considerations */
  potentialRisks: string[];
  /** Recommended next steps for implementation */
  recommendedSteps: string[];
  /** When the analysis was generated */
  generatedAt: Date;
  /** AI model used for analysis */
  model: 'llama-3.1-8b' | 'llama-3.3-70b';
  /** Raw analysis text for copying */
  rawText: string;
}

export interface AnalysisModalProps {
  /** Article ID to analyze */
  articleId: string;
  /** Article title for display */
  articleTitle: string;
  /** Article source name */
  articleSource: string;
  /** Article published date */
  articlePublishedAt: string | null;
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback when modal is closed */
  onClose: () => void;
}

export interface AnalysisApiResponse {
  /** Whether the request was successful */
  success: boolean;
  /** Analysis data */
  data: {
    /** Core technical concepts */
    core_concepts: string[];
    /** Application scenarios */
    application_scenarios: string[];
    /** Potential risks */
    potential_risks: string[];
    /** Recommended steps */
    recommended_steps: string[];
    /** Generation timestamp */
    generated_at: string;
    /** Model used */
    model: string;
    /** Raw analysis text */
    raw_text: string;
  };
  /** Error message if failed */
  error?: string;
}

export interface AnalysisProgress {
  /** Current progress percentage (0-100) */
  progress: number;
  /** Current status message */
  status: string;
  /** Whether analysis is complete */
  isComplete: boolean;
  /** Whether analysis failed */
  hasError: boolean;
  /** Error message if failed */
  errorMessage?: string;
}

export interface ShareAnalysisOptions {
  /** Article title */
  title: string;
  /** Analysis summary */
  summary: string;
  /** Share URL */
  url: string;
}
