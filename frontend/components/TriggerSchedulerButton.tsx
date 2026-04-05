'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { triggerScheduler } from '@/lib/api/scheduler';
import { toast } from '@/lib/toast';
import { RefreshCw } from 'lucide-react';

export function TriggerSchedulerButton() {
  const [isTriggering, setIsTriggering] = useState(false);

  const handleTrigger = async () => {
    try {
      setIsTriggering(true);
      await triggerScheduler();
      toast.success('已觸發文章抓取任務，請稍後重新整理頁面查看新文章');
    } catch (error) {
      console.error('Failed to trigger scheduler:', error);
      toast.error('觸發失敗，請稍後再試');
    } finally {
      setIsTriggering(false);
    }
  };

  return (
    <Button
      variant="outline"
      onClick={handleTrigger}
      disabled={isTriggering}
      className="gap-2"
    >
      <RefreshCw className={`h-4 w-4 ${isTriggering ? 'animate-spin' : ''}`} />
      {isTriggering ? '抓取中...' : '立即抓取新文章'}
    </Button>
  );
}
