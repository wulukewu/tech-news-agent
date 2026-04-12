'use client';

import { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { BookmarkPlus, BookmarkCheck, Star, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { Article } from '@/types/article';
import { useAddToReadingList } from '@/lib/hooks/useReadingList';
import { toast } from '@/lib/toast';

interface ArticleCardProps {
  article: Article;
}

export function ArticleCard({ article }: ArticleCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isAdded, setIsAdded] = useState(article.isInReadingList);
  const addToReadingList = useAddToReadingList();

  const handleAddToReadingList = async () => {
    if (!article.id) {
      console.error('Cannot add to reading list: article.id is undefined');
      toast.error('Unable to add article: Invalid article data');
      return;
    }
    try {
      await addToReadingList.mutateAsync(article.id);
      setIsAdded(true);
      toast.success('Added to reading list');
    } catch (error) {
      // Error handling is done in the hook with toast
      console.error('Failed to add to reading list:', error);
    }
  };

  const formattedDate = article.publishedAt
    ? (() => {
        try {
          const date = new Date(article.publishedAt);
          // Check if date is valid
          if (isNaN(date.getTime())) {
            return 'Recently added';
          }

          const now = new Date();
          const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / 60000);

          if (diffInMinutes < 0) {
            // Future date, shouldn't happen but handle gracefully
            return 'Recently added';
          }

          if (diffInMinutes < 60) {
            return `${diffInMinutes} minutes ago`;
          }
          return formatDistanceToNow(date, { addSuffix: true });
        } catch (error) {
          console.error('Error formatting date:', error, 'publishedAt:', article.publishedAt);
          return 'Recently added';
        }
      })()
    : 'Recently added';

  const shouldShowReadMore = article.aiSummary && article.aiSummary.length > 200;

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
                {article.feedName && (
                  <>
                    <span aria-hidden="true">•</span>
                    <span className="truncate">{article.feedName}</span>
                  </>
                )}
                <span aria-hidden="true">•</span>
                <time dateTime={article.publishedAt || undefined}>{formattedDate}</time>
              </div>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <TinkeringIndexBadge index={article.tinkeringIndex} />
              <Button
                size="sm"
                variant="outline"
                onClick={handleAddToReadingList}
                disabled={addToReadingList.isPending || isAdded}
                aria-label={isAdded ? 'Added to reading list' : 'Add to reading list'}
              >
                {addToReadingList.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : isAdded ? (
                  <BookmarkCheck className="h-4 w-4" />
                ) : (
                  <BookmarkPlus className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
        {article.aiSummary && (
          <CardContent>
            <div
              className={cn(
                'text-sm text-muted-foreground',
                !isExpanded && shouldShowReadMore && 'line-clamp-3'
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
    <div className="flex items-center gap-0.5" aria-label={`Tinkering index: ${index} out of 5`}>
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={cn(
            'h-4 w-4',
            i < index ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300 dark:text-gray-600'
          )}
        />
      ))}
    </div>
  );
}
