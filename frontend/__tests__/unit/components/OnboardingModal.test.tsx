import React from 'react';
import { render, screen, fireEvent, waitFor } from '@/__tests__/utils/test-utils';
import { OnboardingModal } from '@/components/OnboardingModal';
import { toast } from '@/lib/toast';

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch as any;

describe('OnboardingModal', () => {
  const mockOnClose = vi.fn();
  const mockOnComplete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockClear();
  });

  it('should render welcome step initially', () => {
    render(<OnboardingModal isOpen={true} onClose={mockOnClose} onComplete={mockOnComplete} />);

    expect(screen.getByText('歡迎使用技術新聞訂閱工具！')).toBeInTheDocument();
    expect(screen.getByText('開始使用')).toBeInTheDocument();
    expect(screen.getByText('稍後再說')).toBeInTheDocument();
  });

  it('should display platform benefits on welcome step', () => {
    render(<OnboardingModal isOpen={true} onClose={mockOnClose} onComplete={mockOnComplete} />);

    expect(screen.getByText(/訂閱優質的技術 RSS 來源/)).toBeInTheDocument();
    expect(screen.getByText(/每週自動抓取和分析文章/)).toBeInTheDocument();
    expect(screen.getByText(/透過 AI 評分找到最值得閱讀的內容/)).toBeInTheDocument();
  });

  it('should navigate to recommendations step when "開始使用" is clicked', async () => {
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

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockFeeds,
    });

    render(<OnboardingModal isOpen={true} onClose={mockOnClose} onComplete={mockOnComplete} />);

    const startButton = screen.getByText('開始使用');
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByText('選擇你感興趣的來源')).toBeInTheDocument();
    });
  });

  it('should call onClose when "稍後再說" is clicked', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    render(<OnboardingModal isOpen={true} onClose={mockOnClose} onComplete={mockOnComplete} />);

    const skipButton = screen.getByText('稍後再說');
    fireEvent.click(skipButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/onboarding/skip',
        expect.objectContaining({
          method: 'POST',
        })
      );
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('should display recommended feeds on recommendations step', async () => {
    const mockFeeds = {
      feeds: [
        {
          id: '1',
          name: 'Hacker News',
          url: 'https://news.ycombinator.com/rss',
          category: 'Tech News',
          description: '最熱門的科技新聞',
          is_recommended: true,
          recommendation_priority: 100,
          is_subscribed: false,
        },
        {
          id: '2',
          name: 'OpenAI Blog',
          url: 'https://openai.com/blog/rss',
          category: 'AI',
          description: 'OpenAI 官方部落格',
          is_recommended: true,
          recommendation_priority: 95,
          is_subscribed: false,
        },
      ],
      grouped_by_category: {
        'Tech News': [
          {
            id: '1',
            name: 'Hacker News',
            url: 'https://news.ycombinator.com/rss',
            category: 'Tech News',
            description: '最熱門的科技新聞',
            is_recommended: true,
            recommendation_priority: 100,
            is_subscribed: false,
          },
        ],
        AI: [
          {
            id: '2',
            name: 'OpenAI Blog',
            url: 'https://openai.com/blog/rss',
            category: 'AI',
            description: 'OpenAI 官方部落格',
            is_recommended: true,
            recommendation_priority: 95,
            is_subscribed: false,
          },
        ],
      },
      total_count: 2,
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockFeeds,
    });

    render(<OnboardingModal isOpen={true} onClose={mockOnClose} onComplete={mockOnComplete} />);

    // Click start button
    const startButton = screen.getByText('開始使用');
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByText('Hacker News')).toBeInTheDocument();
      expect(screen.getByText('OpenAI Blog')).toBeInTheDocument();
      expect(screen.getByText('Tech News')).toBeInTheDocument();
      expect(screen.getByText('AI')).toBeInTheDocument();
    });
  });

  it('should allow feed selection and deselection', async () => {
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

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockFeeds,
    });

    render(<OnboardingModal isOpen={true} onClose={mockOnClose} onComplete={mockOnComplete} />);

    // Navigate to recommendations
    fireEvent.click(screen.getByText('開始使用'));

    await waitFor(() => {
      expect(screen.getByText('Test Feed')).toBeInTheDocument();
    });

    // Feed should be pre-selected (top 5 feeds are pre-selected)
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeChecked();

    // Click to deselect
    fireEvent.click(checkbox);
    expect(checkbox).not.toBeChecked();

    // Click to select again
    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();
  });

  it('should complete onboarding and subscribe to selected feeds', async () => {
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

    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockFeeds,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          subscribed_count: 1,
          failed_count: 0,
          errors: [],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: '引導已完成' }),
      });

    render(<OnboardingModal isOpen={true} onClose={mockOnClose} onComplete={mockOnComplete} />);

    // Navigate to recommendations
    fireEvent.click(screen.getByText('開始使用'));

    await waitFor(() => {
      expect(screen.getByText('Test Feed')).toBeInTheDocument();
    });

    // Click confirm button
    const confirmButton = screen.getByText(/確認訂閱/);
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(screen.getByText('設定完成！')).toBeInTheDocument();
      expect(screen.getByText(/已成功訂閱 1 個來源/)).toBeInTheDocument();
    });

    // Should call batch subscribe API
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/subscriptions/batch',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ feed_ids: ['1'] }),
      })
    );

    // Should call complete API
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/onboarding/complete',
      expect.objectContaining({
        method: 'POST',
      })
    );
  });

  it('should show error when no feeds are selected', async () => {
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

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockFeeds,
    });

    render(<OnboardingModal isOpen={true} onClose={mockOnClose} onComplete={mockOnComplete} />);

    // Navigate to recommendations
    fireEvent.click(screen.getByText('開始使用'));

    await waitFor(() => {
      expect(screen.getByText('Test Feed')).toBeInTheDocument();
    });

    // Deselect the pre-selected feed
    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);

    // Try to confirm with no feeds selected
    const confirmButton = screen.getByText(/確認訂閱/);
    fireEvent.click(confirmButton);

    expect(toast.error).toHaveBeenCalledWith('請至少選擇一個訂閱來源');
  });
});
