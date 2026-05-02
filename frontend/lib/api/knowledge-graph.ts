import { apiClient } from './client';

export interface TechnicalDomain {
  id: string;
  name: string;
  display_name: string;
  description: string;
  icon: string;
  is_builtin: boolean;
  node_count: number;
  user_progress_pct: number;
}

export interface KnowledgeNode {
  id: string;
  domain_id: string;
  name: string;
  display_name: string;
  description: string;
  difficulty: number;
  estimated_hours: number;
  tags: string[];
  status: 'not_started' | 'in_progress' | 'completed';
  is_unlocked: boolean;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: 'prerequisite' | 'related' | 'extends';
  confidence: number;
}

export interface GraphData {
  domain: TechnicalDomain;
  nodes: KnowledgeNode[];
  edges: GraphEdge[];
  user_progress_pct: number;
}

export interface DomainProgress {
  domain_id: string;
  domain_name: string;
  total_nodes: number;
  completed_nodes: number;
  in_progress_nodes: number;
  progress_pct: number;
  badges: string[];
}

export interface LearningRecommendation {
  node: KnowledgeNode;
  reason: string;
  priority_score: number;
  estimated_hours: number;
}

export async function getDomains(): Promise<TechnicalDomain[]> {
  const res = await apiClient.get('/api/knowledge-graph/domains');
  return res.data;
}

export async function getDomainGraph(domainName: string): Promise<GraphData> {
  const res = await apiClient.get(`/api/knowledge-graph/domains/${domainName}`);
  return res.data;
}

export async function getDomainProgress(domainName: string): Promise<DomainProgress> {
  const res = await apiClient.get(`/api/knowledge-graph/domains/${domainName}/progress`);
  return res.data;
}

export async function updateNodeStatus(
  nodeId: string,
  status: 'not_started' | 'in_progress' | 'completed'
): Promise<void> {
  await apiClient.post(`/api/knowledge-graph/nodes/${nodeId}/complete`, { status });
}

export async function getRecommendations(
  domainName: string,
  maxResults = 5
): Promise<LearningRecommendation[]> {
  const res = await apiClient.get(
    `/api/knowledge-graph/domains/${domainName}/recommendations?max_results=${maxResults}`
  );
  return res.data;
}

export async function getNodeArticles(nodeId: string, limit = 5) {
  const res = await apiClient.get(`/api/knowledge-graph/nodes/${nodeId}/articles?limit=${limit}`);
  return res.data as Array<{
    id: string;
    title: string;
    url: string;
    published_at: string;
    reading_status: string | null;
  }>;
}

export async function rebuildDomain(domainName: string): Promise<TechnicalDomain> {
  const res = await apiClient.post(`/api/knowledge-graph/domains/${domainName}/rebuild`);
  return res.data;
}

export async function createDomain(data: {
  name: string;
  display_name: string;
  description?: string;
  icon?: string;
}): Promise<TechnicalDomain> {
  const res = await apiClient.post('/api/knowledge-graph/domains', data);
  return res.data;
}
