import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Rss } from 'lucide-react';

interface EmptyStateProps {
  searchQuery: string;
  selectedCategoriesCount: number;
  onClearSearch: () => void;
  hasNoSubscriptions?: boolean;
}

export function EmptyState({
  searchQuery,
  selectedCategoriesCount,
  onClearSearch,
  hasNoSubscriptions,
}: EmptyStateProps) {
  if (hasNoSubscriptions) {
    return (
      <section className="flex flex-col items-center justify-center min-h-[50vh] text-center gap-4 animate-in fade-in-50 slide-in-from-bottom-4 duration-500">
        <div className="rounded-full bg-muted p-4 animate-in zoom-in-50 duration-700 delay-200">
          <Rss className="h-8 w-8 text-muted-foreground animate-pulse" />
        </div>
        <div className="animate-in slide-in-from-bottom-2 duration-500 delay-300">
          <h2 className="text-xl font-semibold mb-1">No articles yet</h2>
          <p className="text-muted-foreground">
            Subscribe to some feeds to start seeing articles here.
          </p>
        </div>
        <Button
          asChild
          className="animate-in slide-in-from-bottom-2 duration-500 delay-500 transition-all hover:scale-[1.02] hover:shadow-md"
        >
          <Link href="/app/subscriptions">Browse feeds</Link>
        </Button>
      </section>
    );
  }

  const getMessage = () => {
    if (searchQuery) return `No articles match "${searchQuery}"`;
    if (selectedCategoriesCount === 0) return 'Select at least one category to view articles';
    return 'No articles available for the selected categories';
  };

  return (
    <section className="flex flex-col items-center justify-center min-h-[40vh] text-center gap-4 animate-in fade-in-50 slide-in-from-bottom-4 duration-500">
      <div className="animate-in slide-in-from-bottom-2 duration-500 delay-200">
        <h2 className="text-xl font-semibold">No articles found</h2>
        <p className="text-muted-foreground">{getMessage()}</p>
      </div>
      {searchQuery && (
        <Button
          variant="outline"
          onClick={onClearSearch}
          className="animate-in slide-in-from-bottom-2 duration-500 delay-400 transition-all hover:scale-[1.02] hover:shadow-sm"
        >
          Clear search
        </Button>
      )}
    </section>
  );
}
