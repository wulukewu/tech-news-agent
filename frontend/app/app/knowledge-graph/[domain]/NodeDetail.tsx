'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Clock, ExternalLink, Loader2, Lock } from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';
import { getNodeArticles, type KnowledgeNode } from '@/lib/api/knowledge-graph';
import type { TranslationFunction } from '@/types/i18n';

// ─── RelatedArticles ──────────────────────────────────────────────────────────

export function RelatedArticles({ nodeId }: { nodeId: string }) {
  const { t } = useI18n();
  const { data: articles = [], isLoading } = useQuery({
    queryKey: ['knowledge-graph', 'node-articles', nodeId],
    queryFn: () => getNodeArticles(nodeId),
  });

  if (isLoading) return <div className="h-4 w-24 bg-muted animate-pulse rounded" />;

  return (
    <div className="space-y-1.5">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
        {t('knowledge-graph.related-articles')} {articles.length > 0 ? `(${articles.length})` : ''}
      </p>
      {articles.length === 0 ? (
        <p className="text-xs text-muted-foreground italic">
          {t('knowledge-graph.no-related-articles')}
        </p>
      ) : (
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
                  {t('knowledge-graph.article-read-badge')}
                </Badge>
              )}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── NodeDetail ───────────────────────────────────────────────────────────────

export function NodeDetail({
  node,
  statusLabels,
  isPending,
  onStatusChange,
  onClose,
  hideCloseButton = false,
  t,
}: {
  node: KnowledgeNode;
  statusLabels: Record<string, string>;
  isPending: boolean;
  onStatusChange: (status: KnowledgeNode['status']) => void;
  onClose: () => void;
  hideCloseButton?: boolean;
  t: TranslationFunction;
}) {
  const [pendingStatus, setPendingStatus] = useState<KnowledgeNode['status'] | null>(null);

  useEffect(() => {
    if (!isPending) setPendingStatus(null);
  }, [isPending]);

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold text-base leading-tight">{node.display_name}</h3>
          <p className="text-xs text-muted-foreground mt-0.5 leading-snug">{node.description}</p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className={`h-7 w-7 flex-shrink-0 -mt-0.5 ${hideCloseButton ? 'hidden' : ''}`}
          onClick={onClose}
        >
          <span className="text-base leading-none">×</span>
        </Button>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <Badge
          variant={
            node.status === 'completed'
              ? 'outline'
              : node.status === 'in_progress'
                ? 'default'
                : 'secondary'
          }
        >
          {statusLabels[node.status]}
        </Badge>
        {!node.is_unlocked && (
          <Badge variant="outline" className="flex items-center gap-1">
            <Lock className="h-3 w-3" />
            {t('knowledge-graph.locked')}
          </Badge>
        )}
        <span className="text-sm text-amber-500 ml-auto">
          {'★'.repeat(node.difficulty)}
          <span className="text-muted-foreground/40">{'★'.repeat(5 - node.difficulty)}</span>
        </span>
      </div>

      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Clock className="h-4 w-4" />
        {node.estimated_hours}h
      </div>

      {node.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {node.tags.map((tag) => (
            <Badge key={tag} variant="outline" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>
      )}

      <RelatedArticles nodeId={node.id} />

      {node.is_unlocked ? (
        <div className="space-y-2 pt-1">
          <p className="text-sm font-medium">{t('knowledge-graph.update-status')}</p>
          <div className="grid grid-cols-1 gap-2">
            {(['not_started', 'in_progress', 'completed'] as KnowledgeNode['status'][]).map(
              (status) => (
                <Button
                  key={status}
                  variant={node.status === status ? 'default' : 'outline'}
                  size="sm"
                  disabled={isPending}
                  onClick={() => {
                    setPendingStatus(status);
                    onStatusChange(status);
                  }}
                >
                  {isPending && pendingStatus === status ? (
                    <Loader2 className="h-3 w-3 animate-spin mr-1" />
                  ) : null}
                  {statusLabels[status]}
                </Button>
              )
            )}
          </div>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground bg-muted rounded-lg p-3">
          {t('knowledge-graph.locked-hint')}
        </p>
      )}
    </div>
  );
}
