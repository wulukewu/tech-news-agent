'use client';

import React, { useEffect } from 'react';
import { usePWA } from '@/hooks/usePWA';
import { OfflineIndicator } from '@/components/ui/offline-indicator';
import { PWAInstallPrompt } from '@/components/ui/pwa-install-prompt';

interface PWAProviderProps {
  children: React.ReactNode;
}

/**
 * PWA Provider component
 * Handles PWA initialization, service worker registration, and global PWA features
 */
export function PWAProvider({ children }: PWAProviderProps) {
  const { registerServiceWorker, isOffline } = usePWA();

  useEffect(() => {
    // Register service worker on mount
    registerServiceWorker();

    // Handle service worker updates
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        // Reload the page when a new service worker takes control
        window.location.reload();
      });
    }
  }, [registerServiceWorker]);

  return (
    <>
      {children}

      {/* Global PWA components */}
      <OfflineIndicator variant="toast" />
      <PWAInstallPrompt className="fixed bottom-4 left-4 right-4 z-40 lg:relative lg:bottom-auto lg:left-auto lg:right-auto lg:z-auto lg:mb-4" />
    </>
  );
}
