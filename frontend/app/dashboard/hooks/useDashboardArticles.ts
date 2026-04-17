import { useState, useEffect } from 'react';
import { fetchMyArticles } from '@/lib/api/articles';
import { toast } from '@/lib/toast';
import type { Article } from '@/types/article';

interface UseDashboardArticlesProps {
  selectedCategories: string[];
  loadingCategories: boolean;
}

export function useDashboardArticles({
  selectedCategories,
  loadingCategories,
}: UseDashboardArticlesProps) {
  const [articles, setArticles] = useState<Article[]>([]);
  const [page, setPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  const loadArticles = async (pageNum: number, append: boolean = false) => {
    try {
      if (append) {
        setLoadingMore(true);
      } else {
        setLoading(true);
      }

      const data = await fetchMyArticles(
        pageNum,
        20,
        selectedCategories.length > 0 ? selectedCategories : undefined
      );

      if (append) {
        setArticles((prev) => [...prev, ...(data?.articles || [])]);
      } else {
        setArticles(data?.articles || []);
      }

      setHasNextPage(data?.hasNextPage || false);
      setPage(pageNum);
    } catch (error) {
      toast.error('Failed to load articles');
      setArticles([]);
      setHasNextPage(false);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const handleLoadMore = () => {
    if (!loadingMore && hasNextPage) {
      loadArticles(page + 1, true);
    }
  };

  useEffect(() => {
    if (!loadingCategories) {
      loadArticles(1);
    }
  }, [selectedCategories, loadingCategories]);

  return {
    articles,
    loading,
    loadingMore,
    hasNextPage,
    handleLoadMore,
  };
}
