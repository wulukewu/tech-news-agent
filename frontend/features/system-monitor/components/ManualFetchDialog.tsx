/**
 * Manual Fetch Confirmation Dialog
 *
 * Confirmation dialog for triggering manual fetch operation.
 *
 * Requirements: 5.3
 */

'use client';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

export interface ManualFetchDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog open state changes */
  onOpenChange: (open: boolean) => void;
  /** Callback when user confirms the action */
  onConfirm: () => void;
  /** Whether the fetch is in progress */
  isLoading?: boolean;
}

/**
 * ManualFetchDialog Component
 *
 * Displays a confirmation dialog before triggering manual fetch.
 * Provides information about the operation and its impact.
 *
 * @example
 * ```tsx
 * <ManualFetchDialog
 *   open={isOpen}
 *   onOpenChange={setIsOpen}
 *   onConfirm={handleConfirm}
 *   isLoading={false}
 * />
 * ```
 */
export function ManualFetchDialog({
  open,
  onOpenChange,
  onConfirm,
  isLoading = false,
}: ManualFetchDialogProps) {
  const handleConfirm = () => {
    onConfirm();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>確認手動觸發抓取</DialogTitle>
          <DialogDescription>
            此操作將立即觸發文章抓取任務，從所有訂閱的 RSS 來源獲取最新文章。
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <p className="text-sm font-medium text-foreground">注意事項：</p>
            <ul className="list-disc list-inside text-sm space-y-1 ml-2 mt-2 text-muted-foreground">
              <li>抓取過程可能需要數分鐘時間</li>
              <li>頻繁觸發可能影響系統效能</li>
              <li>建議等待當前任務完成後再次觸發</li>
            </ul>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isLoading}>
            取消
          </Button>
          <Button onClick={handleConfirm} disabled={isLoading}>
            {isLoading ? '觸發中...' : '確認觸發'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
