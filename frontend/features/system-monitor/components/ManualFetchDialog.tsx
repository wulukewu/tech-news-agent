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
import { useI18n } from '@/contexts/I18nContext';

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
  const { t } = useI18n();

  const handleConfirm = () => {
    onConfirm();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('dialogs.manual-fetch.title')}</DialogTitle>
          <DialogDescription>{t('dialogs.manual-fetch.description')}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <p className="text-sm font-medium text-foreground">
              {t('dialogs.manual-fetch.notes-title')}
            </p>
            <ul className="list-disc list-inside text-sm space-y-1 ml-2 mt-2 text-muted-foreground">
              <li>{t('dialogs.manual-fetch.note-1')}</li>
              <li>{t('dialogs.manual-fetch.note-2')}</li>
              <li>{t('dialogs.manual-fetch.note-3')}</li>
            </ul>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isLoading}>
            {t('buttons.cancel')}
          </Button>
          <Button onClick={handleConfirm} disabled={isLoading}>
            {isLoading
              ? t('dialogs.manual-fetch.confirming-button')
              : t('dialogs.manual-fetch.confirm-button')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
