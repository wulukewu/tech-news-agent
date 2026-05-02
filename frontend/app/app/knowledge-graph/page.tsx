'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useUser } from '@/contexts/UserContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Plus, BookOpen, ChevronRight, Loader2 } from 'lucide-react';
import { getDomains, createDomain, type TechnicalDomain } from '@/lib/api/knowledge-graph';

const DIFFICULTY_COLORS: Record<number, string> = {
  1: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  2: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  3: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  4: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  5: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

export default function KnowledgeGraphPage() {
  const { user } = useUser();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newDomain, setNewDomain] = useState({ name: '', display_name: '', description: '' });

  const { data: domains = [], isLoading } = useQuery({
    queryKey: ['knowledge-graph', 'domains'],
    queryFn: getDomains,
    enabled: !!user,
  });

  const createMutation = useMutation({
    mutationFn: createDomain,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-graph', 'domains'] });
      setDialogOpen(false);
      setNewDomain({ name: '', display_name: '', description: '' });
    },
  });

  const handleCreate = () => {
    if (!newDomain.name || !newDomain.display_name) return;
    createMutation.mutate({
      name: newDomain.name.toLowerCase().replace(/\s+/g, '-'),
      display_name: newDomain.display_name,
      description: newDomain.description,
    });
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Please log in to view knowledge graphs.</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Knowledge Graph</h1>
          <p className="text-muted-foreground mt-1">
            Visualize and track your learning path across technical domains
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Domain
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Custom Domain</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 pt-2">
              <div>
                <Label htmlFor="domain-name">Domain ID</Label>
                <Input
                  id="domain-name"
                  placeholder="e.g. graphql"
                  value={newDomain.name}
                  onChange={(e) => setNewDomain((p) => ({ ...p, name: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="domain-display">Display Name</Label>
                <Input
                  id="domain-display"
                  placeholder="e.g. GraphQL"
                  value={newDomain.display_name}
                  onChange={(e) => setNewDomain((p) => ({ ...p, display_name: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="domain-desc">Description</Label>
                <Input
                  id="domain-desc"
                  placeholder="Brief description..."
                  value={newDomain.description}
                  onChange={(e) => setNewDomain((p) => ({ ...p, description: e.target.value }))}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                The knowledge graph will be generated automatically using AI.
              </p>
              <Button
                className="w-full"
                onClick={handleCreate}
                disabled={createMutation.isPending || !newDomain.name || !newDomain.display_name}
              >
                {createMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Building graph...
                  </>
                ) : (
                  'Create Domain'
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Domain Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-48 rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {domains.map((domain) => (
            <DomainCard
              key={domain.id}
              domain={domain}
              onClick={() => router.push(`/app/knowledge-graph/${domain.name}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function DomainCard({ domain, onClick }: { domain: TechnicalDomain; onClick: () => void }) {
  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow border hover:border-primary/50"
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{domain.icon}</span>
            <div>
              <CardTitle className="text-lg">{domain.display_name}</CardTitle>
              {domain.is_builtin && (
                <Badge variant="secondary" className="text-xs mt-0.5">
                  Built-in
                </Badge>
              )}
            </div>
          </div>
          <ChevronRight className="h-5 w-5 text-muted-foreground mt-1" />
        </div>
        <CardDescription className="line-clamp-2 mt-1">{domain.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground flex items-center gap-1">
              <BookOpen className="h-3.5 w-3.5" />
              {domain.node_count} nodes
            </span>
            <span className="font-medium">{Math.round(domain.user_progress_pct)}%</span>
          </div>
          <Progress value={domain.user_progress_pct} className="h-2" />
        </div>
      </CardContent>
    </Card>
  );
}
