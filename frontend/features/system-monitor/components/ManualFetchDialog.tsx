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
      <DialogContent className="animate-in fade-in zoom-in-95 duration-300">
        <DialogHeader className="animate-in slide-in-from-top-4 duration-500 delay-200">
          <DialogTitle className="animate-in fade-in duration-300 delay-300">
            {t('dialogs.manual-fetch.title')}
          </DialogTitle>
          <DialogDescription className="animate-in fade-in duration-300 delay-400">
            {t('dialogs.manual-fetch.description')}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 animate-in slide-in-from-bottom-4 duration-500 delay-500">
          <div>
            <p className="text-sm font-medium text-foreground animate-in slide-in-from-left-2 duration-300 delay-600">
              {t('dialogs.manual-fetch.notes-title')}
            </p>
            <ul className="list-disc list-inside text-sm space-y-1 ml-2 mt-2 text-muted-foreground">
              <li className="animate-in slide-in-from-left-2 duration-300 delay-700 transition-colors hover:text-foreground">
                {t('dialogs.manual-fetch.note-1')}
              </li>
              <li className="animate-in slide-in-from-left-2 duration-300 delay-800 transition-colors hover:text-foreground">
                {t('dialogs.manual-fetch.note-2')}
              </li>
              <li className="animate-in slide-in-from-left-2 duration-300 delay-900 transition-colors hover:text-foreground">
                {t('dialogs.manual-fetch.note-3')}
              </li>
            </ul>
          </div>
        </div>
        <DialogFooter className="animate-in slide-in-from-bottom-4 duration-500 delay-1000">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isLoading}
            className="transition-all duration-200 hover:scale-105"
          >
            {t('buttons.cancel')}
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={isLoading}
            className="transition-all duration-200 hover:scale-105"
          >
            {isLoading
              ? t('dialogs.manual-fetch.confirming-button')
              : t('dialogs.manual-fetch.confirm-button')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
