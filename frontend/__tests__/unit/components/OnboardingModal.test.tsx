import React from 'react';
import { render, screen, fireEvent, waitFor } from '@/__tests__/utils/test-utils';
import { OnboardingModal } from '@/components/OnboardingModal';
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('sonner', () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

const mockFetch = vi.fn();
global.fetch = mockFetch as any;

const mockFeeds = {
  feeds: [
    {
      id: '1',
      name: 'Test Feed',
      url: 'https://example.com',
      category: 'AI',
      description: 'Test description',
      is_recommended: true,
      recommendation_priority: 100,
      is_subscribed: false,
    },
  ],
  grouped_by_category: {
    AI: [
      {
        id: '1',
        name: 'Test Feed',
        url: 'https://example.com',
        category: 'AI',
        description: 'Test description',
        is_recommended: true,
        recommendation_priority: 100,
        is_subscribed: false,
      },
    ],
  },
  total_count: 1,
};

describe('OnboardingModal', () => {
  const mockOnClose = vi.fn();
  const mockOnComplete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockClear();
  });

  it('should render welcome step initially', () => {
    render(<OnboardingModal isOpen={true} onClose={mockOnClose} onComplete={mockOnComplete} />);
    expect(screen.getByText('Welcome to Tech News Agent!')).toBeInTheDocument();
    expect(screen.getByText('Get Started')).toBeInTheDocument();
    expect(screen.getByText('Skip for now')).toBeInTheDocument();
  });

  it('should call onClose when skip button is clicked', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    render(<OnboardingModal isOpen={true} onClose={mockOnClose} onComplete={mockOnComplete} />);
    const skipButton = screen.getByText('Skip for now');
    fireEvent.click(skipButton);
    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it.skip('should navigate to recommendations step when Get Started is clicked', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: async () => mockFeeds });
    render(<OnboardingModal isOpen={true} onClose={mockOnClose} onComplete={mockOnComplete} />);
    await waitFor(() => expect(screen.getByText('Get Started')).toBeInTheDocument());
    // Wait for initial fetch to complete
    await new Promise((r) => setTimeout(r, 50));
    fireEvent.click(screen.getByText('Get Started'));
    await waitFor(
      () => {
        expect(screen.getByText('Test Feed')).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it.skip('should display recommended feeds on recommendations step', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: async () => mockFeeds });
    render(<OnboardingModal isOpen={true} onClose={mockOnClose} onComplete={mockOnComplete} />);
    await waitFor(() => expect(screen.getByText('Get Started')).toBeInTheDocument());
    await new Promise((r) => setTimeout(r, 50));
    fireEvent.click(screen.getByText('Get Started'));
    await waitFor(
      () => {
        expect(screen.getByText('Test Feed')).toBeInTheDocument();
        expect(screen.getByText('AI')).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('should not render when isOpen is false', () => {
    render(<OnboardingModal isOpen={false} onClose={mockOnClose} onComplete={mockOnComplete} />);
    expect(screen.queryByText('Welcome to Tech News Agent!')).not.toBeInTheDocument();
  });
});
