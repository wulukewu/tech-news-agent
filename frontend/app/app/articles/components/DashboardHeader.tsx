import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { TriggerSchedulerButton } from '@/components/TriggerSchedulerButton';
import { SearchBar } from '@/components/SearchBar';
import { CategoryFilter } from '@/components/CategoryFilter';

interface DashboardHeaderProps {
  categories: string[];
  selectedCategories: string[];
  searchQuery: string;
  articlesCount: number;
  loadingCategories: boolean;
  onSearch: (query: string) => void;
  onToggleCategory: (category: string) => void;
  onSelectAll: () => void;
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
  onSelectAll,
  onClearAll,
}: DashboardHeaderProps) {
  const router = useRouter();

  return (
    <header className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-3xl font-bold">Your Articles</h1>
        <div className="flex gap-2">
          <TriggerSchedulerButton />
          <Button variant="outline" onClick={() => router.push('/dashboard/subscriptions')}>
            管理訂閱
          </Button>
        </div>
      </div>

      <div className="mb-4">
        <SearchBar onSearch={onSearch} placeholder="Search articles..." />
      </div>

      <CategoryFilter
        categories={categories}
        selectedCategories={selectedCategories}
        onToggleCategory={onToggleCategory}
        onSelectAll={onSelectAll}
        onClearAll={onClearAll}
        loading={loadingCategories}
      />

      {searchQuery && (
        <div className="mt-4 text-sm text-muted-foreground">
          {articlesCount > 0 ? (
            <span>
              {articlesCount} result{articlesCount !== 1 ? 's' : ''} found
            </span>
          ) : (
            <span>No results found for &quot;{searchQuery}&quot;</span>
          )}
        </div>
      )}
      {!searchQuery && articlesCount > 0 && (
        <div className="mt-4 text-sm text-muted-foreground">Showing all articles</div>
      )}
    </header>
  );
}
