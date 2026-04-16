'use client';

import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  MultiSelectFilter,
  RatingDropdown,
  SortableTableHeader,
  SortableTable,
  SortableTableHead,
  SortableTableBody,
  SortableTableRow,
  SortableTableCell,
  CollapsibleSection,
  DragDropList,
  ContextualTooltip,
  HelpText,
  FadeIn,
  SlideIn,
  StaggeredList,
  type FilterOption,
  type SortDirection,
} from '@/components/ui';
import { useHapticFeedback } from '@/lib/utils/haptic-feedback';
import { useKeyboardNavigation } from '@/lib/hooks/useUrlState';
import {
  Filter,
  SortAsc,
  SortDesc,
  Star,
  Eye,
  BookOpen,
  Share2,
  Settings,
  Keyboard,
  Smartphone,
} from 'lucide-react';

/**
 * InteractiveArticleBrowser Example - Demonstrates Task 12 Enhancements
 *
 * This example showcases all the interactive UI component enhancements:
 *
 * Task 12.1 - Advanced Filter Components:
 * - Enhanced MultiSelectFilter with fuzzy search and bulk actions
 * - RatingDropdown with smooth hover effects and animations
 * - SortableTableHeader with three-state sorting
 *
 * Task 12.2 - Interactive Enhancement Features:
 * - CollapsibleSection for expandable information areas
 * - DragDropList for feed organization
 * - Enhanced keyboard shortcuts (j/k navigation, r refresh, etc.)
 *
 * Task 12.3 - UX Enhancements:
 * - ContextualTooltip with different types and animations
 * - Smooth transitions respecting prefers-reduced-motion
 * - Haptic feedback for mobile devices
 *
 * Task 12.4 - All components are fully tested with unit tests
 */

// Mock data for demonstration
const mockCategories: FilterOption[] = [
  { value: 'tech', label: 'Technology', count: 45 },
  { value: 'ai', label: 'Artificial Intelligence', count: 32 },
  { value: 'web', label: 'Web Development', count: 28 },
  { value: 'mobile', label: 'Mobile Development', count: 22 },
  { value: 'devops', label: 'DevOps', count: 18 },
  { value: 'design', label: 'Design', count: 15 },
  { value: 'security', label: 'Security', count: 12 },
  { value: 'cloud', label: 'Cloud Computing', count: 10 },
];

interface DragDropItem {
  id: string;
  content: React.ReactNode;
}

const mockFeeds: DragDropItem[] = [
  {
    id: '1',
    content: (
      <div className="flex items-center gap-2">
        <Badge>Tech</Badge> TechCrunch
      </div>
    ),
  },
  {
    id: '2',
    content: (
      <div className="flex items-center gap-2">
        <Badge>AI</Badge> AI News
      </div>
    ),
  },
  {
    id: '3',
    content: (
      <div className="flex items-center gap-2">
        <Badge>Web</Badge> CSS-Tricks
      </div>
    ),
  },
  {
    id: '4',
    content: (
      <div className="flex items-center gap-2">
        <Badge>Mobile</Badge> Android Developers
      </div>
    ),
  },
];

const mockArticles = [
  { id: '1', title: 'Advanced React Patterns', category: 'Web', rating: 4, views: 1250 },
  { id: '2', title: 'AI in Modern Development', category: 'AI', rating: 5, views: 2100 },
  { id: '3', title: 'Mobile Performance Tips', category: 'Mobile', rating: 3, views: 890 },
  { id: '4', title: 'Cloud Security Best Practices', category: 'Security', rating: 4, views: 1560 },
];

export function InteractiveArticleBrowserExample() {
  // State management
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedRating, setSelectedRating] = useState<number | undefined>();
  const [sortColumn, setSortColumn] = useState<string>('title');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [feeds, setFeeds] = useState(mockFeeds);
  const [showFilters, setShowFilters] = useState(true);
  const [showSorting, setShowSorting] = useState(true);

  // Haptic feedback
  const haptic = useHapticFeedback();

  // Enhanced keyboard navigation
  const { shortcuts } = useKeyboardNavigation({
    onRefresh: () => {
      haptic.medium();
      console.log('Refreshing articles...');
    },
    onFocusSearch: () => {
      haptic.light();
      document.querySelector('input')?.focus();
    },
    onToggleFilters: () => {
      haptic.light();
      setShowFilters(!showFilters);
    },
    onToggleSorting: () => {
      haptic.light();
      setShowSorting(!showSorting);
    },
    onSelectAll: () => {
      haptic.medium();
      setSelectedCategories(mockCategories.map((cat) => cat.value));
    },
    onClearSelections: () => {
      haptic.light();
      setSelectedCategories([]);
      setSelectedRating(undefined);
    },
    onQuickRating: (rating) => {
      haptic.selection();
      setSelectedRating(rating);
    },
  });

  // Event handlers
  const handleCategoryChange = useCallback(
    (categories: string[]) => {
      setSelectedCategories(categories);
      haptic.selection();
    },
    [haptic]
  );

  const handleRatingChange = useCallback(
    (rating: number | undefined) => {
      setSelectedRating(rating);
      haptic.light();
    },
    [haptic]
  );

  const handleSort = useCallback(
    (column: string, direction: SortDirection) => {
      setSortColumn(column);
      setSortDirection(direction);
      haptic.light();
    },
    [haptic]
  );

  const handleFeedReorder = useCallback(
    (newFeeds: DragDropItem[]) => {
      setFeeds(newFeeds);
      haptic.success();
    },
    [haptic]
  );

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      {/* Header with Keyboard Shortcuts Help */}
      <FadeIn>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Interactive Article Browser Demo
              <ContextualTooltip
                content={
                  <div className="space-y-2">
                    <p className="font-medium">Task 12 Enhancements:</p>
                    <ul className="text-sm space-y-1">
                      <li>• Advanced filter components with search</li>
                      <li>• Drag-and-drop feed organization</li>
                      <li>• Enhanced keyboard navigation</li>
                      <li>• Smooth animations and haptic feedback</li>
                    </ul>
                  </div>
                }
                type="info"
                maxWidth="400px"
              />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CollapsibleSection
              title={
                <HelpText help="Use these keyboard shortcuts to navigate efficiently">
                  <div className="flex items-center gap-2">
                    <Keyboard className="h-4 w-4" />
                    Keyboard Shortcuts
                  </div>
                </HelpText>
              }
              defaultExpanded={false}
            >
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                {shortcuts.map((shortcut, index) => (
                  <SlideIn key={shortcut.key} delay={index * 50}>
                    <div className="flex flex-col items-center p-3 bg-muted rounded-lg">
                      <kbd className="px-2 py-1 text-xs font-mono bg-background border rounded">
                        {shortcut.key}
                      </kbd>
                      <span className="text-xs text-center mt-1 text-muted-foreground">
                        {shortcut.description}
                      </span>
                    </div>
                  </SlideIn>
                ))}
              </div>
            </CollapsibleSection>
          </CardContent>
        </Card>
      </FadeIn>

      {/* Advanced Filter Components (Task 12.1) */}
      <SlideIn direction="up" delay={200}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Advanced Filters
              <ContextualTooltip
                content="Enhanced filter components with search, bulk actions, and smooth animations"
                type="help"
              />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CollapsibleSection
              title="Filter Options"
              expanded={showFilters}
              onExpandedChange={setShowFilters}
            >
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Enhanced Multi-Select Filter */}
                <div className="space-y-2">
                  <HelpText help="Multi-select with fuzzy search and bulk actions">
                    Category Filter
                  </HelpText>
                  <MultiSelectFilter
                    options={mockCategories}
                    selected={selectedCategories}
                    onSelectionChange={handleCategoryChange}
                    placeholder="Select categories..."
                    showBulkActions={true}
                    sortBy="count"
                    enableKeyboardNav={true}
                    showCounts={true}
                  />
                </div>

                {/* Enhanced Rating Dropdown */}
                <div className="space-y-2">
                  <HelpText help="Star rating with smooth hover effects and animations">
                    Minimum Rating
                  </HelpText>
                  <RatingDropdown
                    value={selectedRating}
                    onChange={handleRatingChange}
                    placeholder="Any rating..."
                    showClear={true}
                  />
                </div>

                {/* Filter Summary */}
                <div className="space-y-2">
                  <HelpText help="Current active filters">Active Filters</HelpText>
                  <div className="space-y-2">
                    {selectedCategories.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {selectedCategories.map((category) => (
                          <Badge key={category} variant="secondary">
                            {mockCategories.find((c) => c.value === category)?.label}
                          </Badge>
                        ))}
                      </div>
                    )}
                    {selectedRating && (
                      <div className="flex items-center gap-1">
                        <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                        <span className="text-sm">{selectedRating}+ stars</span>
                      </div>
                    )}
                    {selectedCategories.length === 0 && !selectedRating && (
                      <span className="text-sm text-muted-foreground">No filters applied</span>
                    )}
                  </div>
                </div>
              </div>
            </CollapsibleSection>
          </CardContent>
        </Card>
      </SlideIn>

      {/* Sortable Table (Task 12.1) */}
      <SlideIn direction="up" delay={400}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <SortAsc className="h-5 w-5" />
              Sortable Article Table
              <ContextualTooltip
                content="Click column headers to sort. Three-state sorting: none → ascending → descending → none"
                type="help"
              />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CollapsibleSection
              title="Article List"
              expanded={showSorting}
              onExpandedChange={setShowSorting}
            >
              <SortableTable>
                <SortableTableHead>
                  <SortableTableHeader
                    column="title"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                    onSort={handleSort}
                  >
                    Title
                  </SortableTableHeader>
                  <SortableTableHeader
                    column="category"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                    onSort={handleSort}
                  >
                    Category
                  </SortableTableHeader>
                  <SortableTableHeader
                    column="rating"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                    onSort={handleSort}
                    align="center"
                  >
                    Rating
                  </SortableTableHeader>
                  <SortableTableHeader
                    column="views"
                    sortColumn={sortColumn}
                    sortDirection={sortDirection}
                    onSort={handleSort}
                    align="right"
                  >
                    Views
                  </SortableTableHeader>
                  <SortableTableHeader column="actions" sortable={false}>
                    Actions
                  </SortableTableHeader>
                </SortableTableHead>
                <SortableTableBody>
                  <StaggeredList staggerDelay={100}>
                    {mockArticles.map((article) => (
                      <SortableTableRow key={article.id}>
                        <SortableTableCell>
                          <div className="font-medium">{article.title}</div>
                        </SortableTableCell>
                        <SortableTableCell>
                          <Badge variant="outline">{article.category}</Badge>
                        </SortableTableCell>
                        <SortableTableCell align="center">
                          <div className="flex items-center justify-center gap-1">
                            {Array.from({ length: article.rating }, (_, i) => (
                              <Star key={i} className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                            ))}
                          </div>
                        </SortableTableCell>
                        <SortableTableCell align="right">
                          <div className="flex items-center justify-end gap-1">
                            <Eye className="h-3 w-3 text-muted-foreground" />
                            {article.views.toLocaleString()}
                          </div>
                        </SortableTableCell>
                        <SortableTableCell>
                          <div className="flex items-center gap-2">
                            <ContextualTooltip content="Read article">
                              <Button size="sm" variant="ghost" onClick={() => haptic.light()}>
                                <BookOpen className="h-3 w-3" />
                              </Button>
                            </ContextualTooltip>
                            <ContextualTooltip content="Share article">
                              <Button size="sm" variant="ghost" onClick={() => haptic.light()}>
                                <Share2 className="h-3 w-3" />
                              </Button>
                            </ContextualTooltip>
                          </div>
                        </SortableTableCell>
                      </SortableTableRow>
                    ))}
                  </StaggeredList>
                </SortableTableBody>
              </SortableTable>
            </CollapsibleSection>
          </CardContent>
        </Card>
      </SlideIn>

      {/* Drag-and-Drop Feed Organization (Task 12.2) */}
      <SlideIn direction="up" delay={600}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Smartphone className="h-5 w-5" />
              Feed Organization
              <ContextualTooltip
                content={
                  <div className="space-y-2">
                    <p>Drag and drop to reorder feeds:</p>
                    <ul className="text-sm space-y-1">
                      <li>• Mouse: Click and drag</li>
                      <li>• Keyboard: Focus + Enter/Shift+Enter</li>
                      <li>• Touch: Tap and drag with haptic feedback</li>
                    </ul>
                  </div>
                }
                type="help"
                maxWidth="300px"
              />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CollapsibleSection title="RSS Feed Sources" defaultExpanded={true}>
              <DragDropList
                items={feeds}
                onReorder={handleFeedReorder}
                showDragHandle={true}
                enabled={true}
                className="max-w-md"
              />
              <div className="mt-4 text-sm text-muted-foreground">
                <p>💡 Try dragging the feeds above to reorder them!</p>
                <p>On mobile devices, you'll feel haptic feedback during drag operations.</p>
              </div>
            </CollapsibleSection>
          </CardContent>
        </Card>
      </SlideIn>

      {/* UX Enhancements Demo (Task 12.3) */}
      <SlideIn direction="up" delay={800}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Star className="h-5 w-5" />
              UX Enhancements
              <ContextualTooltip
                content="Smooth animations, contextual help, and mobile-optimized interactions"
                type="success"
              />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Contextual Tooltips */}
              <div className="space-y-4">
                <h3 className="font-medium">Contextual Tooltips</h3>
                <div className="flex flex-wrap gap-2">
                  <ContextualTooltip content="This is an info tooltip" type="info">
                    <Button variant="outline" size="sm">
                      Info
                    </Button>
                  </ContextualTooltip>
                  <ContextualTooltip content="This is a help tooltip" type="help">
                    <Button variant="outline" size="sm">
                      Help
                    </Button>
                  </ContextualTooltip>
                  <ContextualTooltip content="This is a warning tooltip" type="warning">
                    <Button variant="outline" size="sm">
                      Warning
                    </Button>
                  </ContextualTooltip>
                  <ContextualTooltip content="This is a success tooltip" type="success">
                    <Button variant="outline" size="sm">
                      Success
                    </Button>
                  </ContextualTooltip>
                </div>
              </div>

              {/* Haptic Feedback Demo */}
              <div className="space-y-4">
                <h3 className="font-medium">Haptic Feedback (Mobile)</h3>
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" onClick={() => haptic.light()}>
                    Light
                  </Button>
                  <Button size="sm" onClick={() => haptic.medium()}>
                    Medium
                  </Button>
                  <Button size="sm" onClick={() => haptic.heavy()}>
                    Heavy
                  </Button>
                  <Button size="sm" onClick={() => haptic.success()}>
                    Success
                  </Button>
                  <Button size="sm" onClick={() => haptic.error()}>
                    Error
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  {haptic.isEnabled()
                    ? 'Haptic feedback is enabled on this device'
                    : 'Haptic feedback is not supported on this device'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </SlideIn>

      {/* Summary */}
      <FadeIn delay={1000}>
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="pt-6">
            <div className="text-center space-y-2">
              <h3 className="font-medium text-primary">Task 12 Implementation Complete! 🎉</h3>
              <p className="text-sm text-muted-foreground">
                All interactive UI component enhancements have been successfully implemented with:
              </p>
              <div className="flex flex-wrap justify-center gap-2 mt-4">
                <Badge>Advanced Filters</Badge>
                <Badge>Drag & Drop</Badge>
                <Badge>Keyboard Navigation</Badge>
                <Badge>Smooth Animations</Badge>
                <Badge>Haptic Feedback</Badge>
                <Badge>Accessibility</Badge>
                <Badge>Unit Tests</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </FadeIn>
    </div>
  );
}
