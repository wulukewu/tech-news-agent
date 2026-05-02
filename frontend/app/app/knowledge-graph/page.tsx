'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useUser } from '@/contexts/UserContext';
import { useI18n } from '@/contexts/I18nContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Plus, BookOpen, ChevronRight, Loader2, Network, Sparkles, ArrowRight } from 'lucide-react';
import { getDomains, createDomain, type TechnicalDomain } from '@/lib/api/knowledge-graph';
import type { TranslationFunction } from '@/types/i18n';

export default function KnowledgeGraphPage() {
  const { user } = useUser();
  const { t } = useI18n();
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
    onSuccess: (domain) => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-graph', 'domains'] });
      setDialogOpen(false);
      setNewDomain({ name: '', display_name: '', description: '' });
      // Navigate directly to the new domain
      router.push(`/app/knowledge-graph/${domain.name}`);
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

  if (!user) return null;

  const hasStarted = domains.some((d) => d.user_progress_pct > 0);

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-primary/10">
            <Network className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">{t('knowledge-graph.title')}</h1>
            <p className="text-sm text-muted-foreground mt-0.5">{t('knowledge-graph.subtitle')}</p>
          </div>
        </div>

        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-1.5" />
              {t('knowledge-graph.new-domain')}
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>{t('knowledge-graph.create-domain-title')}</DialogTitle>
              <DialogDescription>{t('knowledge-graph.create-domain-subtitle')}</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 pt-1">
              <div className="space-y-1.5">
                <Label htmlFor="domain-name">{t('knowledge-graph.domain-id-label')}</Label>
                <Input
                  id="domain-name"
                  placeholder={t('knowledge-graph.domain-id-placeholder')}
                  value={newDomain.name}
                  onChange={(e) => setNewDomain((p) => ({ ...p, name: e.target.value }))}
                />
                <p className="text-xs text-muted-foreground">
                  {t('knowledge-graph.domain-id-hint')}
                </p>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="domain-display">{t('knowledge-graph.display-name-label')}</Label>
                <Input
                  id="domain-display"
                  placeholder={t('knowledge-graph.display-name-placeholder')}
                  value={newDomain.display_name}
                  onChange={(e) => setNewDomain((p) => ({ ...p, display_name: e.target.value }))}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="domain-desc">{t('knowledge-graph.description-label')}</Label>
                <Input
                  id="domain-desc"
                  placeholder={t('knowledge-graph.description-placeholder')}
                  value={newDomain.description}
                  onChange={(e) => setNewDomain((p) => ({ ...p, description: e.target.value }))}
                />
              </div>
              <div className="flex items-start gap-2 rounded-lg bg-muted p-3">
                <Sparkles className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                <p className="text-xs text-muted-foreground">{t('knowledge-graph.ai-notice')}</p>
              </div>
              <Button
                className="w-full"
                onClick={handleCreate}
                disabled={createMutation.isPending || !newDomain.name || !newDomain.display_name}
              >
                {createMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {t('knowledge-graph.creating-btn')}
                  </>
                ) : (
                  t('knowledge-graph.create-btn')
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* How it works — only show if user hasn't started anything yet */}
      {!hasStarted && !isLoading && (
        <div className="mb-6 mt-4 rounded-xl border bg-muted/40 px-4 py-3">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
            {t('knowledge-graph.how-it-works')}
          </p>
          <p className="text-sm text-foreground/80">{t('knowledge-graph.how-it-works-desc')}</p>
        </div>
      )}

      {/* Section title */}
      <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3 mt-6">
        {t('knowledge-graph.domains-title')}
      </h2>

      {/* Domain Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-36 rounded-xl" />
          ))}
        </div>
      ) : domains.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Network className="h-10 w-10 text-muted-foreground/40 mb-3" />
          <p className="text-muted-foreground">{t('knowledge-graph.domains-empty')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {domains.map((domain) => (
            <DomainCard
              key={domain.id}
              domain={domain}
              onClick={() => router.push(`/app/knowledge-graph/${domain.name}`)}
              t={t}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function DomainCard({
  domain,
  onClick,
  t,
}: {
  domain: TechnicalDomain;
  onClick: () => void;
  t: TranslationFunction;
}) {
  const started = domain.user_progress_pct > 0;
  const completed = domain.user_progress_pct >= 100;

  return (
    <Card
      className="cursor-pointer group hover:shadow-md hover:border-primary/40 transition-all duration-200"
      onClick={onClick}
    >
      <CardHeader className="pb-2 pt-4 px-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <span className="text-xl flex-shrink-0">{domain.icon}</span>
            <div className="min-w-0">
              <CardTitle className="text-base leading-tight truncate">
                {domain.display_name}
              </CardTitle>
              <div className="flex items-center gap-1 mt-0.5">
                <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4 font-normal">
                  {domain.is_builtin ? t('knowledge-graph.built-in') : t('knowledge-graph.custom')}
                </Badge>
                {domain.node_count > 0 && (
                  <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
                    <BookOpen className="h-2.5 w-2.5" />
                    {domain.node_count}
                  </span>
                )}
              </div>
            </div>
          </div>
          <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5 group-hover:text-primary transition-colors" />
        </div>
      </CardHeader>
      <CardContent className="px-4 pb-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">
              {completed
                ? '🏆 Completed'
                : started
                  ? t('knowledge-graph.continue-learning')
                  : t('knowledge-graph.start-learning')}
            </span>
            <span className="font-semibold tabular-nums">
              {Math.round(domain.user_progress_pct)}%
            </span>
          </div>
          <Progress value={domain.user_progress_pct} className="h-1.5" />
        </div>
      </CardContent>
    </Card>
  );
}
