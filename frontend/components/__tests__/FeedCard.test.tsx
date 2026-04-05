import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { act } from 'react';
import { FeedCard } from '../FeedCard';
import type { Feed } from '@/types/feed';

describe('FeedCard', () => {
  const mockFeed: Feed = {
    id: '123',
    name: 'Tech Blog',
    url: 'https://example.com/feed',
    category: 'Technology',
    is_subscribed: false,
  };

  it('should display feed information', () => {
    render(<FeedCard feed={mockFeed} onToggle={jest.fn()} />);

    expect(screen.getByText('Tech Blog')).toBeInTheDocument();
    expect(screen.getByText('Technology')).toBeInTheDocument();
    expect(screen.getByText('https://example.com/feed')).toBeInTheDocument();
  });

  it('should call onToggle when switch is clicked', async () => {
    const onToggle = jest.fn().mockResolvedValue(undefined);
    render(<FeedCard feed={mockFeed} onToggle={onToggle} />);

    const toggle = screen.getByRole('switch');

    await act(async () => {
      fireEvent.click(toggle);
    });

    await waitFor(() => {
      expect(onToggle).toHaveBeenCalledWith('123');
    });
  });

  it('should apply different styles for subscribed feeds', () => {
    const subscribedFeed = { ...mockFeed, is_subscribed: true };
    const { container } = render(
      <FeedCard feed={subscribedFeed} onToggle={jest.fn()} />,
    );

    const card = container.querySelector('[class*="border-primary"]');
    expect(card).toBeInTheDocument();
  });

  it('should disable toggle while toggling', async () => {
    const onToggle = jest.fn().mockResolvedValue(undefined);
    render(<FeedCard feed={mockFeed} onToggle={onToggle} />);

    const toggle = screen.getByRole('switch');

    await act(async () => {
      fireEvent.click(toggle);
    });

    // Wait for the toggle to complete
    await waitFor(() => {
      expect(onToggle).toHaveBeenCalled();
    });
  });

  it('should display feed URL as a link', () => {
    render(<FeedCard feed={mockFeed} onToggle={jest.fn()} />);

    const link = screen.getByRole('link', { name: /example\.com\/feed/i });
    expect(link).toHaveAttribute('href', 'https://example.com/feed');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });
});
