'use client';
import { logger } from '@/lib/utils/logger';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { triggerScheduler } from '@/lib/api/scheduler';
import { toast } from '@/lib/toast';
import { RefreshCw } from 'lucide-react';
import { useI18n } from '@/contexts/I18nContext';

export function TriggerSchedulerButton() {
  const [isTriggering, setIsTriggering] = useState(false);
  const { t } = useI18n();

  const handleTrigger = async () => {
    try {
      setIsTriggering(true);
      await triggerScheduler();
      toast.success(t('success.scheduler-triggered'));
    } catch (error) {
      console.error('Failed to trigger scheduler:', error);
      toast.error(t('errors.scheduler-trigger-failed'));
    } finally {
      setIsTriggering(false);
    }
  };

  return (
    <Button
      variant="outline"
      onClick={handleTrigger}
      disabled={isTriggering}
      className="gap-2 transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
    >
      <RefreshCw
        className={`h-4 w-4 transition-transform duration-200 ${isTriggering ? 'animate-[spin_3s_linear_infinite]' : 'hover:rotate-180'}`}
      />
      {isTriggering ? t('time.scheduler-running') : t('time.manual-trigger')}
    </Button>
  );
}
