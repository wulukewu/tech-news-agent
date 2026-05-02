'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { useUser } from '@/contexts/UserContext';
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
import { ArrowLeft, Star, Lightbulb, Trophy, Clock, Loader2 } from 'lucide-react';
import {
  getDomainGraph,
  getDomainProgress,
  getRecommendations,
  updateNodeStatus,
  type KnowledgeNode,
} from '@/lib/api/knowledge-graph';
import { GraphVisualization } from '@/components/knowledge-graph/GraphVisualization';

const STATUS_LABELS = {
  not_started: 'Not Started',
  in_progress: 'In Progress',
  completed: 'Completed',
};

const STATUS_BADGE_VARIANTS: Record<string, 'secondary' | 'default' | 'outline'> = {
  not_started: 'secondary',
  in_progress: 'default',
  completed: 'outline',
};

export default function DomainGraphPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useUser();
  const queryClient = useQueryClient();
  const domainName = params.domain as string;

  const [selectedNode, setSelectedNode] = useState<KnowledgeNode | null>(null);

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

  if (!user) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Please log in.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Top bar */}
      <div className="flex items-center gap-4 px-4 py-3 border-b bg-background">
        <Button variant="ghost" size="icon" onClick={() => router.push('/app/knowledge-graph')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        {graph ? (
          <>
            <span className="text-xl">{graph.domain.icon}</span>
            <div>
              <h1 className="font-bold text-lg leading-tight">{graph.domain.display_name}</h1>
              <p className="text-xs text-muted-foreground">{graph.nodes.length} nodes</p>
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
                <p className="text-sm text-muted-foreground">Building knowledge graph with AI...</p>
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
            <p className="font-medium mb-2">Legend</p>
            {[
              { color: '#22c55e', label: 'Completed' },
              { color: '#f59e0b', label: 'In Progress' },
              { color: '#94a3b8', label: 'Not Started' },
            ].map(({ color, label }) => (
              <div key={label} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                <span>{label}</span>
              </div>
            ))}
            <div className="flex items-center gap-2 mt-1">
              <span className="text-base">🔒</span>
              <span>Locked (prerequisites needed)</span>
            </div>
          </div>
        </div>

        {/* Right sidebar */}
        <div className="w-80 border-l bg-background overflow-y-auto hidden lg:block">
          <Tabs defaultValue="recommendations" className="h-full">
            <TabsList className="w-full rounded-none border-b">
              <TabsTrigger value="recommendations" className="flex-1">
                <Lightbulb className="h-3.5 w-3.5 mr-1" />
                Next Steps
              </TabsTrigger>
              <TabsTrigger value="progress" className="flex-1">
                <Trophy className="h-3.5 w-3.5 mr-1" />
                Progress
              </TabsTrigger>
            </TabsList>

            <TabsContent value="recommendations" className="p-4 space-y-3">
              {recommendations.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  Complete some nodes to get recommendations!
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
                      <span>Overall Progress</span>
                      <span className="font-medium">{progress.progress_pct}%</span>
                    </div>
                    <Progress value={progress.progress_pct} />
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    {[
                      { label: 'Total', value: progress.total_nodes, color: 'text-foreground' },
                      {
                        label: 'Done',
                        value: progress.completed_nodes,
                        color: 'text-green-600',
                      },
                      {
                        label: 'Active',
                        value: progress.in_progress_nodes,
                        color: 'text-amber-600',
                      },
                    ].map(({ label, value, color }) => (
                      <div key={label} className="bg-muted rounded-lg p-2">
                        <p className={`text-xl font-bold ${color}`}>{value}</p>
                        <p className="text-xs text-muted-foreground">{label}</p>
                      </div>
                    ))}
                  </div>
                  {progress.badges.length > 0 && (
                    <div>
                      <p className="text-sm font-medium mb-2">Badges</p>
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
              <div className="mt-6 space-y-4">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge variant={STATUS_BADGE_VARIANTS[selectedNode.status]}>
                    {STATUS_LABELS[selectedNode.status]}
                  </Badge>
                  {!selectedNode.is_unlocked && <Badge variant="outline">🔒 Locked</Badge>}
                  <span className="text-sm text-muted-foreground ml-auto">
                    {'★'.repeat(selectedNode.difficulty)}
                    {'☆'.repeat(5 - selectedNode.difficulty)}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  Estimated: {selectedNode.estimated_hours} hours
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

                {/* Status actions */}
                {selectedNode.is_unlocked && (
                  <div className="space-y-2 pt-2">
                    <p className="text-sm font-medium">Update Status</p>
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
                            updateStatusMutation.mutate({
                              nodeId: selectedNode.id,
                              status,
                            });
                            setSelectedNode({ ...selectedNode, status });
                          }}
                        >
                          {STATUS_LABELS[status]}
                        </Button>
                      ))}
                    </div>
                  </div>
                )}

                {!selectedNode.is_unlocked && (
                  <p className="text-sm text-muted-foreground bg-muted rounded-lg p-3">
                    Complete the prerequisite nodes to unlock this topic.
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
