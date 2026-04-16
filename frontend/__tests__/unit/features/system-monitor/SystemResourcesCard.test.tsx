/**
 * SystemResourcesCard Component Tests
 *
 * Unit tests for the system resources display component.
 *
 * Requirements: 5.8
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SystemResourcesCard } from '@/features/system-monitor/components/SystemResourcesCard';
import type { SystemResources } from '@/features/system-monitor/types';

describe('SystemResourcesCard', () => {
  const mockResources: SystemResources = {
    cpu: {
      usage: 45.5,
      cores: 8,
      loadAverage: [1.5, 1.8, 2.1],
    },
    memory: {
      total: 17179869184, // 16 GB
      used: 12884901888, // 12 GB
      free: 4294967296, // 4 GB
      usagePercentage: 75.0,
    },
    disk: {
      total: 1000000000000, // ~1 TB
      used: 500000000000, // ~500 GB
      free: 500000000000, // ~500 GB
      usagePercentage: 50.0,
    },
    lastUpdated: new Date('2024-01-15T10:30:00Z'),
  };

  it('should render system resources card', () => {
    render(<SystemResourcesCard resources={mockResources} />);

    expect(screen.getByText('系統資源使用情況')).toBeInTheDocument();
  });

  it('should display CPU usage', () => {
    render(<SystemResourcesCard resources={mockResources} />);

    expect(screen.getByText('CPU 使用率')).toBeInTheDocument();
    expect(screen.getByText('45.5%')).toBeInTheDocument();
    expect(screen.getByText('8 核心')).toBeInTheDocument();
  });

  it('should display memory usage', () => {
    render(<SystemResourcesCard resources={mockResources} />);

    expect(screen.getByText('記憶體使用率')).toBeInTheDocument();
    expect(screen.getByText('75.0%')).toBeInTheDocument();
  });

  it('should display disk usage', () => {
    render(<SystemResourcesCard resources={mockResources} />);

    expect(screen.getByText('磁碟使用率')).toBeInTheDocument();
    expect(screen.getByText('50.0%')).toBeInTheDocument();
  });

  it('should display unavailable message when resources is null', () => {
    render(<SystemResourcesCard resources={undefined} />);

    expect(screen.getByText('系統資源資訊目前無法使用')).toBeInTheDocument();
  });

  it('should apply green color for low usage', () => {
    const lowUsageResources: SystemResources = {
      ...mockResources,
      cpu: { ...mockResources.cpu, usage: 50 },
      memory: { ...mockResources.memory, usagePercentage: 50 },
      disk: { ...mockResources.disk, usagePercentage: 50 },
    };

    const { container } = render(<SystemResourcesCard resources={lowUsageResources} />);

    // Check for green color classes
    const greenElements = container.querySelectorAll('.text-green-600, .dark\\:text-green-400');
    expect(greenElements.length).toBeGreaterThan(0);
  });

  it('should apply yellow color for medium usage', () => {
    const mediumUsageResources: SystemResources = {
      ...mockResources,
      cpu: { ...mockResources.cpu, usage: 75 },
      memory: { ...mockResources.memory, usagePercentage: 75 },
      disk: { ...mockResources.disk, usagePercentage: 75 },
    };

    const { container } = render(<SystemResourcesCard resources={mediumUsageResources} />);

    // Check for yellow color classes
    const yellowElements = container.querySelectorAll('.text-yellow-600, .dark\\:text-yellow-400');
    expect(yellowElements.length).toBeGreaterThan(0);
  });

  it('should apply red color for high usage', () => {
    const highUsageResources: SystemResources = {
      ...mockResources,
      cpu: { ...mockResources.cpu, usage: 90 },
      memory: { ...mockResources.memory, usagePercentage: 90 },
      disk: { ...mockResources.disk, usagePercentage: 90 },
    };

    const { container } = render(<SystemResourcesCard resources={highUsageResources} />);

    // Check for red color classes
    const redElements = container.querySelectorAll('.text-red-600, .dark\\:text-red-400');
    expect(redElements.length).toBeGreaterThan(0);
  });

  it('should display last updated time', () => {
    render(<SystemResourcesCard resources={mockResources} />);

    expect(screen.getByText(/最後更新:/)).toBeInTheDocument();
  });
});
