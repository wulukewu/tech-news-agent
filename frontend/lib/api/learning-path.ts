/**
 * Learning Path API Client
 *
 * API functions for learning path planning agent.
 */

import { apiClient } from './client';

// Types
export interface LearningGoal {
  id: string;
  title: string;
  description: string;
  target_skill: string;
  difficulty_level: number;
  estimated_hours: number;
  status: 'active' | 'completed' | 'paused' | 'cancelled';
  created_at: string;
}

export interface CreateGoalRequest {
  goal_text: string;
}

export interface CreateGoalResponse {
  goal_id: string;
  parsed_goal: {
    target_skill: string;
    display_title: string;
    description: string;
    difficulty_level: number;
    estimated_hours: number;
    is_valid: boolean;
    clarification_needed?: string;
  };
  learning_path: {
    id: string;
    stages: Array<{
      name: string;
      order: number;
      description: string;
      estimated_hours: number;
      skills: string[];
    }>;
    total_hours: number;
  };
  success: boolean;
  message: string;
}

export interface LearningGoalDetails {
  goal: LearningGoal;
  learning_path: {
    id: string;
    stages: Array<{
      name: string;
      order: number;
      description: string;
      estimated_hours: number;
      skills: string[];
    }>;
    total_hours: number;
  } | null;
}

export interface LearningProgress {
  goal_id: string;
  overall_completion: number;
  current_stage: number;
  stages: Array<{
    name: string;
    order: number;
    completion_percentage: number;
    articles_completed: number;
    articles_total: number;
    time_spent_hours: number;
    status: string;
  }>;
  recommendations: string[];
}

export interface ArticleRecommendation {
  articles: Array<{
    id: string;
    title: string;
    url: string;
    category: string;
    published_at: string | null;
    relevance_score: number;
    difficulty_match: number;
    reason: string;
  }>;
  stage_name: string;
  total_count: number;
}

export interface CompleteArticleRequest {
  time_spent_minutes: number;
  notes: string;
}

export interface LearningEvaluation {
  goal_id: string;
  overall_performance: 'excellent' | 'good' | 'average' | 'below_average' | 'needs_improvement';
  efficiency_metrics: {
    time_efficiency: number;
    completion_rate: number;
    retention_score: number;
    consistency_score: number;
  };
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  next_steps: string[];
}

// API Functions

/**
 * Create a new learning goal
 */
export async function createLearningGoal(request: CreateGoalRequest): Promise<CreateGoalResponse> {
  const response = await apiClient.post<CreateGoalResponse>('/api/learning-path/goals', request);
  return response.data;
}

/**
 * Get all learning goals for current user
 */
export async function getLearningGoals(): Promise<LearningGoal[]> {
  const response = await apiClient.get<LearningGoal[]>('/api/learning-path/goals');
  return response.data;
}

/**
 * Get detailed information about a specific learning goal
 */
export async function getLearningGoalDetails(goalId: string): Promise<LearningGoalDetails> {
  const response = await apiClient.get<LearningGoalDetails>(`/api/learning-path/goals/${goalId}`);
  return response.data;
}

/**
 * Get learning progress for a specific goal
 */
export async function getLearningProgress(goalId: string): Promise<LearningProgress> {
  const response = await apiClient.get<LearningProgress>(
    `/api/learning-path/goals/${goalId}/progress`
  );
  return response.data;
}

/**
 * Get article recommendations for current learning stage
 */
export async function getArticleRecommendations(
  goalId: string,
  stage: number = 1,
  limit: number = 10
): Promise<ArticleRecommendation> {
  const response = await apiClient.get<ArticleRecommendation>(
    `/api/learning-path/goals/${goalId}/recommendations?stage=${stage}&limit=${limit}`
  );
  return response.data;
}

/**
 * Mark an article as completed
 */
export async function markArticleComplete(
  goalId: string,
  articleId: string,
  request: CompleteArticleRequest
): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.post<{ success: boolean; message: string }>(
    `/api/learning-path/goals/${goalId}/articles/${articleId}/complete`,
    request
  );
  return response.data;
}

/**
 * Manually adjust learning plan
 */
export async function adjustLearningPlan(
  goalId: string,
  adjustmentType: string,
  reason: string
): Promise<{
  success: boolean;
  message: string;
  adjustments: Array<{
    type: string;
    target: string;
    reason: string;
    actions: string[];
  }>;
  next_recommendations: string[];
}> {
  const response = await apiClient.put<{
    success: boolean;
    message: string;
    adjustments: Array<{
      type: string;
      target: string;
      reason: string;
      actions: string[];
    }>;
    next_recommendations: string[];
  }>(`/api/learning-path/goals/${goalId}/adjust`, {
    adjustment_type: adjustmentType,
    reason,
  });
  return response.data;
}

/**
 * Get comprehensive learning effectiveness evaluation
 */
export async function getLearningEvaluation(goalId: string): Promise<LearningEvaluation> {
  const response = await apiClient.get<LearningEvaluation>(
    `/api/learning-path/goals/${goalId}/evaluation`
  );
  return response.data;
}

/**
 * Delete a learning goal
 */
export async function deleteLearningGoal(
  goalId: string
): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.delete<{ success: boolean; message: string }>(
    `/api/learning-path/goals/${goalId}`
  );
  return response.data;
}
