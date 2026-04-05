import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FeedCard } from '../FeedCard';
import type { Feed } from '@/types/feed';

describe('FeedCard', () => {
  const mockFeed: Feed = {
    id: '123',
    name: 'Tech Blog',
    url: 'https://example.com/feed',
    category: 'Technology',
    isSubscribed: false,
  };

  it('should display feed information', () => {
    render(<FeedCard feed={mockFeed} onToggle={jest.fn()} />);

    expect(screen.getByText('Tech Blog')).toBeInTheDocument();
    expect(screen.getByText('Technology')).toBeInTheDocument();
    expect(screen.getByText('https://example.com/feed')).toBeInTheDocument();
  });

  it('should call onToggle when switch is clicked', async () => {
    const onToggle = jest.fn();
    render(<FeedCard feed={mockFeed} onToggle={onToggle} />);

    const toggle = screen.getByRole('switch');
    fireEvent.click(toggle);

    await waitFor(() => {
      expect(onToggle).toHaveBeenCalledWith('123');
    });
  });

  it('should apply different styles for subscribed feeds', () => {
    const subscribedFeed = { ...mockFeed, isSubscribed: true };
    const { container } = render(
      <FeedCard feed={subscribedFeed} onToggle={jest.fn()} />,
    );

    const card = container.querySelector('[class*="border-primary"]');
    expect(card).toBeInTheDocument();
  });

  it('should disable toggle while toggling', async () => {
    const onToggle = jest.fn(
      () => new Promise((resolve) => setTimeout(resolve, 100)),
    );
    render(<FeedCard feed={mockFeed} onToggle={onToggle} />);

    const toggle = screen.getByRole('switch');
    fireEvent.click(toggle);

    // Switch should be disabled while toggling
    expect(toggle).toBeDisabled();
  });

  it('should display feed URL as a link', () => {
    render(<FeedCard feed={mockFeed} onToggle={jest.fn()} />);

    const link = screen.getByRole('link', { name: /example\.com\/feed/i });
    expect(link).toHaveAttribute('href', 'https://example.com/feed');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });
});
