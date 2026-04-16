'use client';

import React, { useState, useEffect } from 'react';
import { X, Download, Smartphone, Monitor } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { usePWA } from '@/hooks/usePWA';
import { cn } from '@/lib/utils';

interface PWAInstallPromptProps {
  className?: string;
  onDismiss?: () => void;
  showOnlyWhenInstallable?: boolean;
}

/**
 * PWA installation prompt component
 * Shows installation prompt when app is installable and provides installation instructions
 */
export function PWAInstallPrompt({
  className,
  onDismiss,
  showOnlyWhenInstallable = true,
}: PWAInstallPromptProps) {
  const { canInstall, isInstalled, isStandalone, installPWA } = usePWA();
  const [isDismissed, setIsDismissed] = useState(false);
  const [isInstalling, setIsInstalling] = useState(false);

  // Check if prompt was previously dismissed
  useEffect(() => {
    const dismissed = localStorage.getItem('pwa-install-dismissed');
    if (dismissed) {
      setIsDismissed(true);
    }
  }, []);

  // Don't show if conditions aren't met
  if (isDismissed || isInstalled || isStandalone || (showOnlyWhenInstallable && !canInstall)) {
    return null;
  }

  const handleInstall = async () => {
    setIsInstalling(true);
    try {
      const success = await installPWA();
      if (success) {
        setIsDismissed(true);
        localStorage.setItem('pwa-install-dismissed', 'true');
      }
    } catch (error) {
      console.error('Installation failed:', error);
    } finally {
      setIsInstalling(false);
    }
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    localStorage.setItem('pwa-install-dismissed', 'true');
    onDismiss?.();
  };

  return (
    <Card
      className={cn('border-primary/20 bg-gradient-to-r from-primary/5 to-primary/10', className)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Download className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg">Install Tech News Agent</CardTitle>
              <CardDescription>
                Get the full app experience with offline access and notifications
              </CardDescription>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleDismiss}
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            aria-label="Dismiss install prompt"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="space-y-4">
          {/* Benefits */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <div className="flex items-center gap-2">
              <Smartphone className="h-4 w-4 text-primary" />
              <span>Works offline</span>
            </div>
            <div className="flex items-center gap-2">
              <Monitor className="h-4 w-4 text-primary" />
              <span>Desktop app experience</span>
            </div>
            <div className="flex items-center gap-2">
              <Download className="h-4 w-4 text-primary" />
              <span>Faster loading</span>
            </div>
            <div className="flex items-center gap-2">
              <Smartphone className="h-4 w-4 text-primary" />
              <span>Push notifications</span>
            </div>
          </div>

          {/* Install button */}
          <div className="flex gap-2">
            <Button onClick={handleInstall} disabled={isInstalling} className="flex-1 sm:flex-none">
              {isInstalling ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent mr-2" />
                  Installing...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Install App
                </>
              )}
            </Button>
            <Button variant="outline" onClick={handleDismiss} className="sm:hidden">
              Maybe Later
            </Button>
          </div>

          {/* Manual installation instructions for unsupported browsers */}
          {!canInstall && (
            <div className="text-xs text-muted-foreground bg-muted/50 p-3 rounded-lg">
              <p className="font-medium mb-1">Manual Installation:</p>
              <p>On mobile: Tap the share button and select "Add to Home Screen"</p>
              <p>On desktop: Look for the install icon in your browser's address bar</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Floating PWA install button for minimal UI
 */
export function PWAInstallButton({ className }: { className?: string }) {
  const { canInstall, isInstalled, isStandalone, installPWA } = usePWA();
  const [isInstalling, setIsInstalling] = useState(false);

  if (isInstalled || isStandalone || !canInstall) {
    return null;
  }

  const handleInstall = async () => {
    setIsInstalling(true);
    try {
      await installPWA();
    } catch (error) {
      console.error('Installation failed:', error);
    } finally {
      setIsInstalling(false);
    }
  };

  return (
    <Button
      onClick={handleInstall}
      disabled={isInstalling}
      size="sm"
      className={cn('fixed bottom-20 right-4 z-50 shadow-lg', className)}
    >
      {isInstalling ? (
        <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent" />
      ) : (
        <Download className="h-4 w-4" />
      )}
      <span className="ml-2 hidden sm:inline">Install</span>
    </Button>
  );
}
