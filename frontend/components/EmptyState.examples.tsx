/**
 * EmptyState Component Usage Examples
 *
 * This file demonstrates how to use the EmptyState component
 * with its three variants: no-subscriptions, no-articles, no-reading-list
 */

import { EmptyState } from './EmptyState';
import { useRouter } from 'next/navigation';

/**
 * Example 1: No Subscriptions Empty State
 *
 * Use this when the user has no RSS subscriptions yet.
 * Shows a primary action to navigate to the subscriptions page.
 */
export function NoSubscriptionsExample() {
  const router = useRouter();

  return (
    <EmptyState
      type="no-subscriptions"
      title="還沒有訂閱"
      description="開始訂閱一些 RSS 來源來查看文章。我們有許多推薦的技術新聞來源供您選擇。"
      primaryAction={{
        label: '管理訂閱',
        onClick: () => router.push('/subscriptions'),
      }}
    />
  );
}

/**
 * Example 2: No Articles Empty State (with Scheduler Status)
 *
 * Use this when the user has subscriptions but no articles have been fetched yet.
 * Shows both primary and secondary actions, plus scheduler status information.
 */
export function NoArticlesExample() {
  const router = useRouter();

  const schedulerStatus = {
    lastExecutionTime: new Date('2024-01-15T10:30:00Z'),
    nextScheduledTime: new Date('2024-01-15T11:00:00Z'),
    isRunning: false,
    lastExecutionArticleCount: 0,
    estimatedTimeUntilArticles: '5-10 分鐘',
  };

  return (
    <EmptyState
      type="no-articles"
      title="還沒有文章"
      description="您已經訂閱了一些來源，但還沒有抓取到文章。排程器會定期自動抓取，或者您可以手動觸發。"
      primaryAction={{
        label: '管理訂閱',
        onClick: () => router.push('/subscriptions'),
      }}
      secondaryAction={{
        label: '手動觸發抓取',
        onClick: () => {
          // Trigger scheduler manually
          console.log('Triggering scheduler...');
        },
      }}
      schedulerStatus={schedulerStatus}
    />
  );
}

/**
 * Example 3: No Articles Empty State (without Scheduler Status)
 *
 * Use this when the user has subscriptions but no articles,
 * and you don't want to show scheduler status.
 */
export function NoArticlesSimpleExample() {
  const router = useRouter();

  return (
    <EmptyState
      type="no-articles"
      title="還沒有文章"
      description="排程器會定期自動抓取文章，請稍候片刻。"
      primaryAction={{
        label: '管理訂閱',
        onClick: () => router.push('/subscriptions'),
      }}
      secondaryAction={{
        label: '手動觸發抓取',
        onClick: () => {
          // Trigger scheduler manually
          console.log('Triggering scheduler...');
        },
      }}
    />
  );
}

/**
 * Example 4: No Reading List Empty State
 *
 * Use this when the user's reading list is empty.
 * Provides guidance on how to add articles to the reading list.
 */
export function NoReadingListExample() {
  const router = useRouter();

  return (
    <EmptyState
      type="no-reading-list"
      title="閱讀清單為空"
      description="您還沒有儲存任何文章到閱讀清單。瀏覽文章時，點擊書籤圖示即可加入閱讀清單。"
      primaryAction={{
        label: '瀏覽文章',
        onClick: () => router.push('/'),
      }}
    />
  );
}

/**
 * Example 5: Custom Icon Override
 *
 * You can override the default variant icon with a custom one.
 */
export function CustomIconExample() {
  const router = useRouter();

  return (
    <EmptyState
      type="no-subscriptions"
      title="自訂圖示範例"
      description="這個範例展示如何使用自訂圖示覆蓋預設的變體圖示。"
      icon={<div className="text-4xl">🎨</div>}
      primaryAction={{
        label: '開始使用',
        onClick: () => console.log('Custom action'),
      }}
    />
  );
}

/**
 * Example 6: Backward Compatibility with Legacy Action Prop
 *
 * The component still supports the legacy `action` prop for backward compatibility.
 */
export function LegacyActionExample() {
  return (
    <EmptyState
      title="舊版 API 範例"
      description="這個範例展示向後相容的 action prop 用法。"
      action={
        <button className="px-4 py-2 bg-blue-500 text-white rounded">
          自訂動作按鈕
        </button>
      }
    />
  );
}
