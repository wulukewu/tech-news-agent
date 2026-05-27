import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Rss } from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';

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
  const { t } = useI18n();

  if (hasNoSubscriptions) {
    return (
      <section className="flex flex-col items-center justify-center min-h-[50vh] text-center gap-4">
        <div className="rounded-full bg-muted p-4">
          <Rss className="h-8 w-8 text-muted-foreground" />
        </div>
        <div>
          <h2 className="text-xl font-semibold mb-1">{t('pages.articles.empty-no-subs-title')}</h2>
          <p className="text-muted-foreground">{t('pages.articles.empty-no-subs-desc')}</p>
        </div>
        <Button
          asChild
          className="transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
        >
          <Link href="/app/subscriptions">{t('pages.articles.empty-browse-feeds')}</Link>
        </Button>
      </section>
    );
  }

  const getMessage = () => {
    if (searchQuery) return t('pages.articles.empty-no-match', { query: searchQuery });
    if (selectedCategoriesCount === 0) return t('pages.articles.empty-select-category');
    return t('pages.articles.empty-no-articles-category');
  };

  return (
    <section className="flex flex-col items-center justify-center min-h-[40vh] text-center gap-4">
      <div>
        <h2 className="text-xl font-semibold">{t('pages.articles.empty-not-found-title')}</h2>
        <p className="text-muted-foreground">{getMessage()}</p>
      </div>
      {searchQuery && (
        <Button
          variant="outline"
          onClick={onClearSearch}
          className="transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
        >
          {t('pages.articles.empty-clear-search')}
        </Button>
      )}
    </section>
  );
}
