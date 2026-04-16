/**
 * CategoryFilterMenu Component Usage Examples
 *
 * This file demonstrates various ways to use the CategoryFilterMenu component
 * with different configurations and features.
 */

import React, { useState } from 'react';
import { CategoryFilterMenu } from './CategoryFilterMenu';

// Mock category data
const mockCategories: string[] = [
  'Technology',
  'Artificial Intelligence',
  'Web Development',
  'Mobile Development',
  'Data Science',
  'Cybersecurity',
  'Cloud Computing',
  'DevOps',
  'Blockchain',
  'Internet of Things',
  'Machine Learning',
  'Frontend Development',
  'Backend Development',
  'Database',
  'API Development',
  'Software Testing',
  'UI/UX Design',
  'Performance Optimization',
  'Software Architecture',
  'Microservices',
  'Containerization',
  'Serverless Computing',
  'Edge Computing',
  'Quantum Computing',
  'Augmented Reality',
];

// Example 1: Basic usage with default settings
export function BasicCategoryFilter() {
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);

  return (
    <div className="w-full max-w-md space-y-4">
      <h3 className="text-lg font-semibold">基本分類篩選</h3>
      <CategoryFilterMenu
        selectedCategories={selectedCategories}
        onCategoryChange={setSelectedCategories}
      />
      <div className="text-sm text-muted-foreground">
        已選擇: {selectedCategories.join(', ') || '無'}
      </div>
    </div>
  );
}

// Example 2: With custom max visible categories
export function CompactCategoryFilter() {
  const [selectedCategories, setSelectedCategories] = useState<string[]>(['tech', 'ai']);

  return (
    <div className="w-full max-w-md space-y-4">
      <h3 className="text-lg font-semibold">精簡分類篩選 (最多顯示 10 個)</h3>
      <CategoryFilterMenu
        selectedCategories={selectedCategories}
        onCategoryChange={setSelectedCategories}
        maxCategories={10}
      />
      <div className="text-sm text-muted-foreground">已選擇: {selectedCategories.join(', ')}</div>
    </div>
  );
}

// Example 3: Without search functionality
export function SimpleListFilter() {
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);

  return (
    <div className="w-full max-w-md space-y-4">
      <h3 className="text-lg font-semibold">簡單列表篩選 (無搜尋)</h3>
      <CategoryFilterMenu
        selectedCategories={selectedCategories}
        onCategoryChange={setSelectedCategories}
        maxCategories={8}
      />
    </div>
  );
}

// Example 4: Disabled state
export function DisabledCategoryFilter() {
  const [selectedCategories] = useState<string[]>(['tech', 'web']);

  return (
    <div className="w-full max-w-md space-y-4">
      <h3 className="text-lg font-semibold">停用狀態</h3>
      <CategoryFilterMenu
        selectedCategories={selectedCategories}
        onCategoryChange={() => {}} // No-op
        disabled={true}
      />
      <p className="text-sm text-muted-foreground">此篩選器已停用，無法進行選擇</p>
    </div>
  );
}

// Example 5: Integration with ArticleBrowser
export function IntegratedArticleFilter() {
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  const handleCategoryChange = (categories: string[]) => {
    setSelectedCategories(categories);
    console.log('Categories changed:', categories);
    // Here you would typically update the ArticleBrowser filters
  };

  return (
    <div className="w-full max-w-4xl space-y-6">
      <h3 className="text-lg font-semibold">整合式文章篩選</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">分類篩選</label>
          <CategoryFilterMenu
            selectedCategories={selectedCategories}
            onCategoryChange={handleCategoryChange}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">關鍵字搜尋</label>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜尋文章標題或內容..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
        <h4 className="font-medium mb-2">目前篩選條件:</h4>
        <div className="space-y-1 text-sm">
          <div>
            <strong>分類:</strong>{' '}
            {selectedCategories.length > 0 ? selectedCategories.join(', ') : '全部'}
          </div>
          <div>
            <strong>關鍵字:</strong> {searchQuery || '無'}
          </div>
        </div>
      </div>
    </div>
  );
}

// Example 6: Real-time filtering demonstration
export function RealTimeFilterDemo() {
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [filteredArticles, setFilteredArticles] = useState<any[]>([]);

  // Simulate article filtering
  React.useEffect(() => {
    // Mock articles data
    const mockArticles = [
      { id: 1, title: 'React 18 新功能介紹', category: 'web' },
      { id: 2, title: 'AI 在軟體開發中的應用', category: 'ai' },
      { id: 3, title: '雲端架構最佳實踐', category: 'cloud' },
      { id: 4, title: 'TypeScript 進階技巧', category: 'web' },
      { id: 5, title: '機器學習入門指南', category: 'ml' },
    ];

    if (selectedCategories.length === 0) {
      setFilteredArticles(mockArticles);
    } else {
      const filtered = mockArticles.filter((article) =>
        selectedCategories.includes(article.category)
      );
      setFilteredArticles(filtered);
    }
  }, [selectedCategories]);

  return (
    <div className="w-full max-w-2xl space-y-6">
      <h3 className="text-lg font-semibold">即時篩選示範</h3>

      <CategoryFilterMenu
        selectedCategories={selectedCategories}
        onCategoryChange={setSelectedCategories}
      />

      <div className="border rounded-lg p-4">
        <h4 className="font-medium mb-3">篩選結果 ({filteredArticles.length} 篇文章)</h4>
        {filteredArticles.length > 0 ? (
          <ul className="space-y-2">
            {filteredArticles.map((article) => (
              <li
                key={article.id}
                className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded"
              >
                <span>{article.title}</span>
                <span className="text-xs bg-blue-100 dark:bg-blue-900 px-2 py-1 rounded">
                  {article.category}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-muted-foreground">沒有符合條件的文章</p>
        )}
      </div>
    </div>
  );
}

// Example 7: Custom styling
export function StyledCategoryFilter() {
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);

  return (
    <div className="w-full max-w-md space-y-4">
      <h3 className="text-lg font-semibold">自訂樣式</h3>
      <CategoryFilterMenu
        selectedCategories={selectedCategories}
        onCategoryChange={setSelectedCategories}
        className="border-2 border-blue-200 rounded-lg"
      />
    </div>
  );
}
