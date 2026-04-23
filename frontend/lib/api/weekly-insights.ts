import { apiClient } from './client';

export interface TrendItem {
  name: string;
  domain: string;
  current_count: number;
  previous_count: number;
  momentum: number;
  direction: 'rising' | 'stable' | 'declining';
}

export interface ClusterItem {
  name: string;
  article_count: number;
  strength: number;
  top_keywords: string[];
  top_articles: Array<{ id: string; title: string; url: string }>;
}

export interface MissedArticle {
  id: string;
  title: string;
  url: string;
  tinkering_index: number;
}

export interface InsightReport {
  id: string | null;
  period_start: string;
  period_end: string;
  article_count: number;
  executive_summary: string;
  clusters: ClusterItem[];
  trends: TrendItem[];
  missed_articles: MissedArticle[];
  trend_data: TrendItem[];
  created_at: string;
}

export interface InsightHistoryItem {
  id: string;
  period_start: string;
  period_end: string;
  article_count: number;
  executive_summary: string;
  created_at: string;
}

export interface TrendsData {
  trends: TrendItem[];
  period_start: string | null;
  period_end: string | null;
}

/** Manually trigger weekly insights generation. */
export async function generateWeeklyInsights(
  days: number = 7,
  endDate?: string
): Promise<InsightReport> {
  const response = await apiClient.post<{ success: boolean; data: InsightReport }>(
    '/api/weekly-insights/generate',
    { days, end_date: endDate ?? null }
  );
  return response.data.data;
}

/** Get the most recently generated report. */
export async function getLatestInsights(): Promise<InsightReport | null> {
  const response = await apiClient.get<{ success: boolean; data: InsightReport | null }>(
    '/api/weekly-insights/latest'
  );
  return response.data.data;
}

/** Get paginated history of reports. */
export async function getInsightsHistory(
  page: number = 1,
  pageSize: number = 10
): Promise<{ reports: InsightHistoryItem[]; page: number; page_size: number }> {
  const response = await apiClient.get<{
    success: boolean;
    data: { reports: InsightHistoryItem[]; page: number; page_size: number };
  }>(`/api/weekly-insights/history?page=${page}&page_size=${pageSize}`);
  return response.data.data;
}

/** Get a specific report by ID. */
export async function getInsightsById(reportId: string): Promise<InsightReport> {
  const response = await apiClient.get<{ success: boolean; data: InsightReport }>(
    `/api/weekly-insights/${reportId}`
  );
  return response.data.data;
}

/** Get trend data for chart rendering. */
export async function getTrendsData(): Promise<TrendsData> {
  const response = await apiClient.get<{ success: boolean; data: TrendsData }>(
    '/api/weekly-insights/trends/data'
  );
  return response.data.data;
}
