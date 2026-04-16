'use client';

import { useCallback, useEffect, useState } from 'react';

interface OfflineAction {
  id: string;
  url: string;
  method: string;
  headers: Record<string, string>;
  body?: string;
  timestamp: number;
  retries: number;
}

interface BackgroundSyncState {
  isSupported: boolean;
  pendingActions: OfflineAction[];
  isOnline: boolean;
}

/**
 * Hook for managing background sync functionality
 * Queues actions when offline and syncs them when connection is restored
 */
export function useBackgroundSync() {
  const [state, setState] = useState<BackgroundSyncState>({
    isSupported: false,
    pendingActions: [],
    isOnline: navigator.onLine,
  });

  // Check if background sync is supported
  useEffect(() => {
    const checkSupport = async () => {
      if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
        setState((prev) => ({ ...prev, isSupported: true }));
      }
    };

    checkSupport();
  }, []);

  // Listen for online/offline events
  useEffect(() => {
    const handleOnline = () => {
      setState((prev) => ({ ...prev, isOnline: true }));
      // Trigger sync when coming back online
      if (state.pendingActions.length > 0) {
        triggerBackgroundSync();
      }
    };

    const handleOffline = () => {
      setState((prev) => ({ ...prev, isOnline: false }));
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [state.pendingActions.length]);

  // Load pending actions from localStorage
  useEffect(() => {
    const loadPendingActions = () => {
      try {
        const stored = localStorage.getItem('offline-actions');
        if (stored) {
          const actions = JSON.parse(stored) as OfflineAction[];
          setState((prev) => ({ ...prev, pendingActions: actions }));
        }
      } catch (error) {
        console.error('Failed to load offline actions:', error);
      }
    };

    loadPendingActions();
  }, []);

  // Save pending actions to localStorage
  const savePendingActions = useCallback((actions: OfflineAction[]) => {
    try {
      localStorage.setItem('offline-actions', JSON.stringify(actions));
      setState((prev) => ({ ...prev, pendingActions: actions }));
    } catch (error) {
      console.error('Failed to save offline actions:', error);
    }
  }, []);

  // Queue an action for background sync
  const queueAction = useCallback(
    async (url: string, options: RequestInit = {}): Promise<boolean> => {
      if (state.isOnline) {
        // If online, execute immediately
        try {
          const response = await fetch(url, options);
          return response.ok;
        } catch (error) {
          console.error('Failed to execute action:', error);
          // If immediate execution fails, queue it
        }
      }

      // Queue the action for later sync
      const action: OfflineAction = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        url,
        method: options.method || 'GET',
        headers: (options.headers as Record<string, string>) || {},
        body: options.body as string,
        timestamp: Date.now(),
        retries: 0,
      };

      const newActions = [...state.pendingActions, action];
      savePendingActions(newActions);

      // Register for background sync if supported
      if (state.isSupported) {
        try {
          const registration = await navigator.serviceWorker.ready;
          await (registration as any).sync.register('background-sync-articles');
        } catch (error) {
          console.error('Failed to register background sync:', error);
        }
      }

      return true;
    },
    [state.isOnline, state.pendingActions, state.isSupported, savePendingActions]
  );

  // Trigger background sync manually
  const triggerBackgroundSync = useCallback(async () => {
    if (!state.isOnline || state.pendingActions.length === 0) {
      return;
    }

    const successfulActions: string[] = [];
    const failedActions: OfflineAction[] = [];

    for (const action of state.pendingActions) {
      try {
        const response = await fetch(action.url, {
          method: action.method,
          headers: action.headers,
          body: action.body,
        });

        if (response.ok) {
          successfulActions.push(action.id);
        } else {
          // Retry failed actions up to 3 times
          if (action.retries < 3) {
            failedActions.push({ ...action, retries: action.retries + 1 });
          }
        }
      } catch (error) {
        console.error('Failed to sync action:', action.id, error);
        // Retry failed actions up to 3 times
        if (action.retries < 3) {
          failedActions.push({ ...action, retries: action.retries + 1 });
        }
      }
    }

    // Update pending actions (remove successful, keep failed for retry)
    savePendingActions(failedActions);

    return {
      successful: successfulActions.length,
      failed: failedActions.length,
    };
  }, [state.isOnline, state.pendingActions, savePendingActions]);

  // Clear all pending actions
  const clearPendingActions = useCallback(() => {
    localStorage.removeItem('offline-actions');
    setState((prev) => ({ ...prev, pendingActions: [] }));
  }, []);

  // Remove a specific pending action
  const removePendingAction = useCallback(
    (actionId: string) => {
      const newActions = state.pendingActions.filter((action) => action.id !== actionId);
      savePendingActions(newActions);
    },
    [state.pendingActions, savePendingActions]
  );

  return {
    ...state,
    queueAction,
    triggerBackgroundSync,
    clearPendingActions,
    removePendingAction,
  };
}
