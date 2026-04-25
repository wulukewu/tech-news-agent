'use client';

import { useState } from 'react';
import { ExternalLink, CheckCircle2, XCircle, HelpCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { cn } from '@/lib/utils';
import type { Feed } from '@/types/feed';

interface FeedCardProps {
  feed: Feed;
  onToggle: (feedId: string) => Promise<void>;
}

export function FeedCard({ feed, onToggle }: FeedCardProps) {
  const [isToggling, setIsToggling] = useState(false);

  const handleToggle = async () => {
    setIsToggling(true);
    try {
      await onToggle(feed.id);
    } finally {
      setIsToggling(false);
    }
  };

  return (
    <Card
      className={cn(
        'transition-all cursor-pointer hover:shadow-md',
        feed.is_subscribed && 'border-primary'
      )}
    >
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <CardTitle className="text-lg truncate">{feed.name}</CardTitle>
              {feed.health_status === 'healthy' && (
                <CheckCircle2
                  className="h-4 w-4 text-green-500 flex-shrink-0"
                  aria-label="Feed is healthy"
                />
              )}
              {feed.health_status === 'error' && (
                <XCircle
                  className="h-4 w-4 text-red-500 flex-shrink-0"
                  aria-label="Feed has errors"
                />
              )}
              {(!feed.health_status || feed.health_status === 'unknown') && (
                <HelpCircle
                  className="h-4 w-4 text-muted-foreground flex-shrink-0"
                  aria-label="Feed status unknown"
                />
              )}
            </div>
            <Badge variant="secondary" className="mt-2">
              {feed.category}
            </Badge>
          </div>
          <Switch
            checked={feed.is_subscribed}
            onCheckedChange={handleToggle}
            disabled={isToggling}
            aria-label={`Toggle subscription for ${feed.name}`}
          />
        </div>
      </CardHeader>
      <CardContent>
        <a
          href={feed.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-muted-foreground hover:underline flex items-center gap-1 cursor-pointer"
          onClick={(e) => e.stopPropagation()}
        >
          <ExternalLink className="h-3 w-3 flex-shrink-0" />
          <span className="truncate">{feed.url}</span>
        </a>
      </CardContent>
    </Card>
  );
}
