'use client';

import { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { BookmarkPlus, Star } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { Article } from '@/types/article';

interface ArticleCardProps {
  article: Article;
}

export function ArticleCard({ article }: ArticleCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isAdding, setIsAdding] = useState(false);

  const handleAddToReadingList = async () => {
    setIsAdding(true);
    try {
      // TODO: Implement API call when reading list endpoint is ready
      // await addToReadingList(article.id);
      console.log('Add to reading list:', article.id);
      // toast.success('Added to reading list');
    } catch (error) {
      // toast.error('Failed to add to reading list');
      console.error('Failed to add to reading list:', error);
    } finally {
      setIsAdding(false);
    }
  };

  const formattedDate = article.publishedAt
    ? formatDistanceToNow(new Date(article.publishedAt), { addSuffix: true })
    : 'Unknown date';

  const shouldShowReadMore =
    article.aiSummary && article.aiSummary.length > 200;

  return (
    <article>
      <Card className="hover:shadow-md transition-shadow">
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:underline cursor-pointer"
              >
                <CardTitle className="text-xl">{article.title}</CardTitle>
              </a>
              <div className="flex flex-wrap items-center gap-2 mt-2 text-sm text-muted-foreground">
                <Badge variant="secondary">{article.category}</Badge>
                <span aria-hidden="true">•</span>
                <span className="truncate">{article.feedName}</span>
                <span aria-hidden="true">•</span>
                <time dateTime={article.publishedAt || undefined}>
                  {formattedDate}
                </time>
              </div>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <TinkeringIndexBadge index={article.tinkeringIndex} />
              <Button
                size="sm"
                variant="outline"
                onClick={handleAddToReadingList}
                disabled={isAdding}
                aria-label="Add to reading list"
              >
                <BookmarkPlus className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        {article.aiSummary && (
          <CardContent>
            <div
              className={cn(
                'text-sm text-muted-foreground',
                !isExpanded && shouldShowReadMore && 'line-clamp-3',
              )}
            >
              {article.aiSummary}
            </div>
            {shouldShowReadMore && (
              <Button
                variant="link"
                size="sm"
                onClick={() => setIsExpanded(!isExpanded)}
                className="mt-2 p-0 h-auto"
                aria-expanded={isExpanded}
              >
                {isExpanded ? 'Show less' : 'Read more'}
              </Button>
            )}
          </CardContent>
        )}
      </Card>
    </article>
  );
}

function TinkeringIndexBadge({ index }: { index: number }) {
  return (
    <div
      className="flex items-center gap-0.5"
      aria-label={`Tinkering index: ${index} out of 5`}
    >
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={cn(
            'h-4 w-4',
            i < index
              ? 'fill-yellow-400 text-yellow-400'
              : 'text-gray-300 dark:text-gray-600',
          )}
        />
      ))}
    </div>
  );
}
