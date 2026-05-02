'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useUser } from '@/contexts/UserContext';
import { useI18n } from '@/contexts/I18nContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  ArrowLeft,
  Lightbulb,
  Trophy,
  Clock,
  Loader2,
  Lock,
  Network,
  ExternalLink,
} from 'lucide-react';
import {
  getDomainGraph,
  getDomainProgress,
  getRecommendations,
  updateNodeStatus,
  getNodeArticles,
  type KnowledgeNode,
} from '@/lib/api/knowledge-graph';
import { GraphVisualization } from '@/components/knowledge-graph/GraphVisualization';

const STATUS_BADGE_VARIANTS: Record<string, 'secondary' | 'default' | 'outline'> = {
  not_started: 'secondary',
  in_progress: 'default',
  completed: 'outline',
};

export default function DomainGraphPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useUser();
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const domainName = params.domain as string;
  const [selectedNode, setSelectedNode] = useState<KnowledgeNode | null>(null);

  const STATUS_LABELS: Record<string, string> = {
    not_started: t('knowledge-graph.not-started'),
    in_progress: t('knowledge-graph.in-progress'),
    completed: t('knowledge-graph.completed'),
  };

  const { data: graph, isLoading: graphLoading } = useQuery({
    queryKey: ['knowledge-graph', 'graph', domainName],
    queryFn: () => getDomainGraph(domainName),
    enabled: !!user && !!domainName,
  });

  const { data: progress } = useQuery({
    queryKey: ['knowledge-graph', 'progress', domainName],
    queryFn: () => getDomainProgress(domainName),
    enabled: !!user && !!domainName,
  });

  const { data: recommendations = [] } = useQuery({
    queryKey: ['knowledge-graph', 'recommendations', domainName],
    queryFn: () => getRecommendations(domainName),
    enabled: !!user && !!domainName,
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ nodeId, status }: { nodeId: string; status: KnowledgeNode['status'] }) =>
      updateNodeStatus(nodeId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-graph', 'graph', domainName] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-graph', 'progress', domainName] });
      queryClient.invalidateQueries({
        queryKey: ['knowledge-graph', 'recommendations', domainName],
      });
    },
  });

  if (!user) return null;

  return (
    <div className="-m-4 lg:-m-6 flex flex-col" style={{ height: 'calc(100vh - 64px)' }}>
      {/* Top bar */}
      <div className="flex items-center gap-4 px-4 py-3 border-b bg-background">
        <Button variant="ghost" size="icon" onClick={() => router.push('/app/knowledge-graph')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        {graph ? (
          <>
            <div className="p-1.5 rounded-md bg-primary/10">
              <Network className="h-4 w-4 text-primary" />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-tight">{graph.domain.display_name}</h1>
              <p className="text-xs text-muted-foreground">
                {graph.nodes.length} {t('knowledge-graph.nodes-count-label')}
              </p>
            </div>
            <div className="ml-auto flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-2 min-w-[160px]">
                <Progress value={graph.user_progress_pct} className="h-2 flex-1" />
                <span className="text-sm font-medium whitespace-nowrap">
                  {Math.round(graph.user_progress_pct)}%
                </span>
              </div>
              {progress?.badges.map((badge) => (
                <Badge key={badge} variant="secondary" className="hidden md:flex">
                  {badge}
                </Badge>
              ))}
            </div>
          </>
        ) : (
          <Skeleton className="h-6 w-48" />
        )}
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Graph area */}
        <div className="flex-1 relative bg-muted/20">
          {graphLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center space-y-3">
                <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
                <p className="text-sm text-muted-foreground">{t('knowledge-graph.building')}</p>
              </div>
            </div>
          ) : graph ? (
            <GraphVisualization
              nodes={graph.nodes}
              edges={graph.edges}
              onNodeClick={setSelectedNode}
            />
          ) : null}

          {/* Legend */}
          <div className="absolute bottom-4 left-4 bg-background/90 backdrop-blur rounded-lg p-3 text-xs space-y-1.5 border">
            <p className="font-medium mb-2">{t('knowledge-graph.legend')}</p>
            {[
              { color: '#22c55e', label: t('knowledge-graph.completed') },
              { color: '#f59e0b', label: t('knowledge-graph.in-progress') },
              { color: '#94a3b8', label: t('knowledge-graph.not-started') },
            ].map(({ color, label }) => (
              <div key={label} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                <span>{label}</span>
              </div>
            ))}
            <div className="flex items-center gap-2 mt-1">
              <Lock className="h-3 w-3 text-muted-foreground" />
              <span>{t('knowledge-graph.locked-desc')}</span>
            </div>
          </div>
        </div>

        {/* Right sidebar */}
        <div className="w-80 border-l bg-background overflow-y-auto hidden lg:block">
          <Tabs defaultValue="recommendations" className="h-full">
            <TabsList className="w-full rounded-none border-b">
              <TabsTrigger value="recommendations" className="flex-1">
                <Lightbulb className="h-3.5 w-3.5 mr-1" />
                {t('knowledge-graph.next-steps')}
              </TabsTrigger>
              <TabsTrigger value="progress" className="flex-1">
                <Trophy className="h-3.5 w-3.5 mr-1" />
                {t('knowledge-graph.overall-progress')}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="recommendations" className="p-4 space-y-3">
              {recommendations.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  {t('knowledge-graph.no-recommendations')}
                </p>
              ) : (
                recommendations.map((rec) => (
                  <Card
                    key={rec.node.id}
                    className="cursor-pointer hover:border-primary/50 transition-colors"
                    onClick={() => setSelectedNode(rec.node)}
                  >
                    <CardHeader className="pb-2 pt-3 px-3">
                      <CardTitle className="text-sm">{rec.node.display_name}</CardTitle>
                    </CardHeader>
                    <CardContent className="px-3 pb-3 space-y-1.5">
                      <p className="text-xs text-muted-foreground">{rec.reason}</p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {rec.estimated_hours}h
                        <span className="ml-auto">
                          {'★'.repeat(rec.node.difficulty)}
                          {'☆'.repeat(5 - rec.node.difficulty)}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </TabsContent>

            <TabsContent value="progress" className="p-4 space-y-4">
              {progress ? (
                <>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>{t('knowledge-graph.overall-progress')}</span>
                      <span className="font-medium">{progress.progress_pct}%</span>
                    </div>
                    <Progress value={progress.progress_pct} />
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    {[
                      {
                        labelKey: 'knowledge-graph.total' as const,
                        value: progress.total_nodes,
                        color: 'text-foreground',
                      },
                      {
                        labelKey: 'knowledge-graph.done' as const,
                        value: progress.completed_nodes,
                        color: 'text-green-600',
                      },
                      {
                        labelKey: 'knowledge-graph.active' as const,
                        value: progress.in_progress_nodes,
                        color: 'text-amber-600',
                      },
                    ].map(({ labelKey, value, color }) => (
                      <div key={labelKey} className="bg-muted rounded-lg p-2">
                        <p className={`text-xl font-bold ${color}`}>{value}</p>
                        <p className="text-xs text-muted-foreground">{t(labelKey)}</p>
                      </div>
                    ))}
                  </div>
                  {progress.badges.length > 0 && (
                    <div>
                      <p className="text-sm font-medium mb-2">{t('knowledge-graph.badges')}</p>
                      <div className="flex flex-wrap gap-2">
                        {progress.badges.map((badge) => (
                          <Badge key={badge} variant="secondary">
                            {badge}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <Skeleton className="h-32" />
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Node detail dialog */}
      <Dialog open={!!selectedNode} onOpenChange={(open) => !open && setSelectedNode(null)}>
        <DialogContent>
          {selectedNode && (
            <>
              <DialogHeader>
                <DialogTitle>{selectedNode.display_name}</DialogTitle>
                <DialogDescription>{selectedNode.description}</DialogDescription>
              </DialogHeader>
              <div className="mt-4 space-y-4">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge variant={STATUS_BADGE_VARIANTS[selectedNode.status]}>
                    {STATUS_LABELS[selectedNode.status]}
                  </Badge>
                  {!selectedNode.is_unlocked && (
                    <Badge variant="outline" className="flex items-center gap-1">
                      <Lock className="h-3 w-3" />
                      {t('knowledge-graph.locked')}
                    </Badge>
                  )}
                  <span className="text-sm text-muted-foreground ml-auto">
                    {'★'.repeat(selectedNode.difficulty)}
                    {'☆'.repeat(5 - selectedNode.difficulty)}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  {selectedNode.estimated_hours}h
                </div>

                {selectedNode.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {selectedNode.tags.map((tag) => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}

                <RelatedArticles nodeId={selectedNode.id} />

                {selectedNode.is_unlocked ? (
                  <div className="space-y-2 pt-1">
                    <p className="text-sm font-medium">{t('knowledge-graph.update-status')}</p>
                    <div className="grid grid-cols-1 gap-2">
                      {(
                        ['not_started', 'in_progress', 'completed'] as KnowledgeNode['status'][]
                      ).map((status) => (
                        <Button
                          key={status}
                          variant={selectedNode.status === status ? 'default' : 'outline'}
                          size="sm"
                          disabled={
                            updateStatusMutation.isPending || selectedNode.status === status
                          }
                          onClick={() => {
                            updateStatusMutation.mutate({ nodeId: selectedNode.id, status });
                            setSelectedNode({ ...selectedNode, status });
                          }}
                        >
                          {STATUS_LABELS[status]}
                        </Button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground bg-muted rounded-lg p-3">
                    {t('knowledge-graph.locked-hint')}
                  </p>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function RelatedArticles({ nodeId }: { nodeId: string }) {
  const { data: articles = [], isLoading } = useQuery({
    queryKey: ['knowledge-graph', 'node-articles', nodeId],
    queryFn: () => getNodeArticles(nodeId),
  });

  if (isLoading) return <div className="h-4 w-24 bg-muted animate-pulse rounded" />;
  if (articles.length === 0) return null;

  return (
    <div className="space-y-1.5">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
        Related Articles ({articles.length})
      </p>
      <div className="space-y-1">
        {articles.map((a) => (
          <a
            key={a.id}
            href={a.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-start gap-2 text-xs p-2 rounded-md hover:bg-muted transition-colors group"
          >
            <ExternalLink className="h-3 w-3 mt-0.5 flex-shrink-0 text-muted-foreground group-hover:text-primary" />
            <span className="line-clamp-2 flex-1">{a.title}</span>
            {a.reading_status === 'read' && (
              <Badge
                variant="outline"
                className="text-[10px] px-1 py-0 h-4 flex-shrink-0 text-green-600 border-green-200"
              >
                Read
              </Badge>
            )}
          </a>
        ))}
      </div>
    </div>
  );
}
