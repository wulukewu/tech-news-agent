'use client';

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
    <Button variant="outline" onClick={handleTrigger} disabled={isTriggering} className="gap-2">
      <RefreshCw className={`h-4 w-4 ${isTriggering ? 'animate-spin' : ''}`} />
      {isTriggering ? '抓取中...' : '立即抓取新文章'}
    </Button>
  );
}
