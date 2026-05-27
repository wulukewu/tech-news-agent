import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { TriggerSchedulerButton } from '@/components/TriggerSchedulerButton';
import { SearchBar } from '@/components/SearchBar';
import { CategoryFilter } from '@/components/CategoryFilter';
import { useI18n } from '@/contexts/I18nContext';

interface DashboardHeaderProps {
  categories: string[];
  selectedCategories: string[];
  searchQuery: string;
  articlesCount: number;
  loadingCategories: boolean;
  onSearch: (query: string) => void;
  onToggleCategory: (category: string) => void;
  onClearAll: () => void;
}

export function DashboardHeader({
  categories,
  selectedCategories,
  searchQuery,
  articlesCount,
  loadingCategories,
  onSearch,
  onToggleCategory,
  onClearAll,
}: DashboardHeaderProps) {
  const router = useRouter();
  const { t } = useI18n();

  return (
    <header className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-3xl font-bold">{t('pages.articles.title')}</h1>
        <div className="flex gap-2">
          <TriggerSchedulerButton />
          <Button variant="outline" onClick={() => router.push('/dashboard/subscriptions')}>
            {t('buttons.manage-subscriptions')}
          </Button>
        </div>
      </div>

      <div className="mb-4">
        <SearchBar onSearch={onSearch} placeholder={t('forms.placeholders.search-articles')} />
      </div>

      <CategoryFilter
        categories={categories}
        selectedCategories={selectedCategories}
        onToggleCategory={onToggleCategory}
        onClearAll={onClearAll}
        loading={loadingCategories}
      />

      {searchQuery && (
        <div className="mt-4 text-sm text-muted-foreground">
          {articlesCount > 0 ? (
            <span>{t('forms.labels.search-results', { count: articlesCount })}</span>
          ) : (
            <span>{t('pages.articles.empty-no-match', { query: searchQuery })}</span>
          )}
        </div>
      )}
      {!searchQuery && articlesCount > 0 && (
        <div className="mt-4 text-sm text-muted-foreground">{t('pages.articles.showing-all')}</div>
      )}
    </header>
  );
}
