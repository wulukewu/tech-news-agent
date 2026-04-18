import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

interface UseDashboardFiltersProps {
  categories: string[];
}

export function useDashboardFilters({ categories }: UseDashboardFiltersProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Initialize from URL
  useEffect(() => {
    const categoriesParam = searchParams.get('categories');
    const searchParam = searchParams.get('search');

    if (searchParam) {
      setSearchQuery(searchParam);
    }

    if (categoriesParam && categories.length > 0) {
      const urlCategories = categoriesParam.split(',').filter(Boolean);
      const validCategories = urlCategories.filter((cat) => categories.includes(cat));
      if (validCategories.length > 0) {
        setSelectedCategories(validCategories);
      }
    }
  }, [searchParams, categories]);

  const updateURL = (newCategories: string[], newSearch: string) => {
    const params = new URLSearchParams();

    if (newCategories.length > 0 && newCategories.length < categories.length) {
      params.set('categories', newCategories.join(','));
    }

    if (newSearch.trim()) {
      params.set('search', newSearch.trim());
    }

    const queryString = params.toString();
    const newURL = queryString ? `/dashboard/articles?${queryString}` : '/dashboard/articles';
    router.replace(newURL, { scroll: false });
  };

  const toggleCategory = (category: string) => {
    setSelectedCategories((prev) => {
      const newCategories = prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category];
      updateURL(newCategories, searchQuery);
      return newCategories;
    });
  };

  const selectAllCategories = () => {
    setSelectedCategories(categories);
    updateURL(categories, searchQuery);
  };

  const deselectAllCategories = () => {
    setSelectedCategories([]);
    updateURL([], searchQuery);
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    updateURL(selectedCategories, query);
  };

  return {
    selectedCategories,
    setSelectedCategories,
    searchQuery,
    toggleCategory,
    selectAllCategories,
    deselectAllCategories,
    handleSearch,
  };
}
