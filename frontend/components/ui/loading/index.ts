/**
 * Loading Components Index
 *
 * Centralized exports for all loading-related components
 * Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8
 */

// Skeleton Components
export {
  ArticleCardSkeletonMobile,
  ArticleCardSkeletonDesktop,
  ArticleGridSkeleton,
  FeedListSkeleton,
  NavigationSkeleton,
  ReadingListItemSkeleton,
  ReadingListSkeleton,
  // Legacy components
  FeedGridSkeleton,
  ArticleListSkeleton,
  LoadingScreen,
} from '@/components/LoadingSkeleton';

// Loading Indicators
export {
  InfiniteScrollSpinner,
  ComponentLoadingOverlay,
  InitialPageSkeleton,
  ButtonLoadingSpinner,
  CardLoadingOverlay,
  ListLoadingState,
} from '@/components/ui/loading-indicators';

// Loading Announcements
export {
  LoadingAnnouncement,
  PageLoadingAnnouncer,
  ArticleLoadingAnnouncer,
  FeedLoadingAnnouncer,
  ReadingListAnnouncer,
  SearchLoadingAnnouncer,
  FormLoadingAnnouncer,
} from '@/components/ui/loading-announcements';

// Content Transitions
export {
  FadeInContent,
  SlideUpContent,
  ScaleInContent,
  StaggeredListTransition,
  ContentTransition,
  ArticleGridTransition,
  PageContentTransition,
  CardContentTransition,
} from '@/components/ui/content-transitions';

// Base Loading Spinner
export { LoadingSpinner, PageLoader } from '@/components/ui/loading-spinner';
