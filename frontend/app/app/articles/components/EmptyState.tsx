import { Button } from '@/components/ui/button';

interface EmptyStateProps {
  searchQuery: string;
  selectedCategoriesCount: number;
  onClearSearch: () => void;
}

export function EmptyState({
  searchQuery,
  selectedCategoriesCount,
  onClearSearch,
}: EmptyStateProps) {
  const getMessage = () => {
    if (searchQuery) {
      return `No articles match your search "${searchQuery}"`;
    }
    if (selectedCategoriesCount === 0) {
      return 'Please select at least one category to view articles';
    }
    return 'No articles available for the selected categories';
  };

  return (
    <section className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <h2 className="text-2xl font-bold mb-2">No articles found</h2>
      <p className="text-muted-foreground mb-6">{getMessage()}</p>
      {searchQuery && (
        <Button variant="outline" onClick={onClearSearch}>
          Clear search
        </Button>
      )}
    </section>
  );
}
