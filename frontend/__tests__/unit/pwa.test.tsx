/**
 * @vitest-environment jsdom
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { usePWA } from '@/hooks/usePWA';
import { PWAInstallPrompt } from '@/components/ui/pwa-install-prompt';
import { OfflineIndicator } from '@/components/ui/offline-indicator';
import { PullToRefresh } from '@/components/ui/pull-to-refresh';

// Mock the PWA hook
vi.mock('@/hooks/usePWA');
const mockUsePWA = usePWA as ReturnType<typeof vi.fn>;

// Mock navigator.serviceWorker
const mockServiceWorker = {
  register: vi.fn(),
  ready: Promise.resolve({
    sync: {
      register: vi.fn(),
    },
    showNotification: vi.fn(),
  }),
  controller: null,
  addEventListener: vi.fn(),
};

Object.defineProperty(navigator, 'serviceWorker', {
  value: mockServiceWorker,
  writable: true,
});

// Mock navigator.onLine
Object.defineProperty(navigator, 'onLine', {
  writable: true,
  value: true,
});

describe('PWA Functionality', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('PWAInstallPrompt Component', () => {
    it('should not render when app is already installed', () => {
      mockUsePWA.mockReturnValue({
        isInstallable: true,
        isInstalled: true,
        isOffline: false,
        isStandalone: false,
        canInstall: false,
        installPWA: vi.fn(),
        registerServiceWorker: vi.fn(),
        requestNotificationPermission: vi.fn(),
        showNotification: vi.fn(),
      });

      render(<PWAInstallPrompt />);

      expect(screen.queryByText('Install Tech News Agent')).not.toBeInTheDocument();
    });

    it('should render install prompt when app is installable', () => {
      mockUsePWA.mockReturnValue({
        isInstallable: true,
        isInstalled: false,
        isOffline: false,
        isStandalone: false,
        canInstall: true,
        installPWA: vi.fn(),
        registerServiceWorker: vi.fn(),
        requestNotificationPermission: vi.fn(),
        showNotification: vi.fn(),
      });

      render(<PWAInstallPrompt />);

      expect(screen.getByText('Install Tech News Agent')).toBeInTheDocument();
      expect(
        screen.getByText('Get the full app experience with offline access and notifications')
      ).toBeInTheDocument();
      expect(screen.getByText('Install App')).toBeInTheDocument();
    });

    it('should call installPWA when install button is clicked', async () => {
      const mockInstallPWA = vi.fn().mockResolvedValue(true);

      mockUsePWA.mockReturnValue({
        isInstallable: true,
        isInstalled: false,
        isOffline: false,
        isStandalone: false,
        canInstall: true,
        installPWA: mockInstallPWA,
        registerServiceWorker: vi.fn(),
        requestNotificationPermission: vi.fn(),
        showNotification: vi.fn(),
      });

      render(<PWAInstallPrompt />);

      const installButton = screen.getByText('Install App');
      await userEvent.click(installButton);

      expect(mockInstallPWA).toHaveBeenCalled();
    });
  });

  describe('OfflineIndicator Component', () => {
    it('should not render when online and showWhenOnline is false', () => {
      mockUsePWA.mockReturnValue({
        isInstallable: false,
        isInstalled: false,
        isOffline: false,
        isStandalone: false,
        canInstall: false,
        installPWA: vi.fn(),
        registerServiceWorker: vi.fn(),
        requestNotificationPermission: vi.fn(),
        showNotification: vi.fn(),
      });

      render(<OfflineIndicator />);

      expect(screen.queryByText("You're offline")).not.toBeInTheDocument();
    });

    it('should render offline indicator when offline', () => {
      mockUsePWA.mockReturnValue({
        isInstallable: false,
        isInstalled: false,
        isOffline: true,
        isStandalone: false,
        canInstall: false,
        installPWA: vi.fn(),
        registerServiceWorker: vi.fn(),
        requestNotificationPermission: vi.fn(),
        showNotification: vi.fn(),
      });

      render(<OfflineIndicator />);

      expect(screen.getByText("You're offline")).toBeInTheDocument();
      expect(
        screen.getByText(
          'Some features may be limited. Previously viewed content is still available.'
        )
      ).toBeInTheDocument();
    });

    it('should render badge variant correctly', () => {
      mockUsePWA.mockReturnValue({
        isInstallable: false,
        isInstalled: false,
        isOffline: true,
        isStandalone: false,
        canInstall: false,
        installPWA: vi.fn(),
        registerServiceWorker: vi.fn(),
        requestNotificationPermission: vi.fn(),
        showNotification: vi.fn(),
      });

      render(<OfflineIndicator variant="badge" />);

      expect(screen.getByText('Offline')).toBeInTheDocument();
    });
  });

  describe('PullToRefresh Component', () => {
    it('should render children correctly', () => {
      render(
        <PullToRefresh onRefresh={vi.fn()}>
          <div>Test Content</div>
        </PullToRefresh>
      );

      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('should not call onRefresh when disabled', async () => {
      const mockOnRefresh = vi.fn();

      render(
        <PullToRefresh onRefresh={mockOnRefresh} disabled={true}>
          <div>Test Content</div>
        </PullToRefresh>
      );

      const container = screen.getByText('Test Content').parentElement;

      fireEvent.touchStart(container!, {
        touches: [{ clientY: 100 }],
      });

      fireEvent.touchMove(container!, {
        touches: [{ clientY: 200 }],
      });

      fireEvent.touchEnd(container!);

      expect(mockOnRefresh).not.toHaveBeenCalled();
    });
  });
});
