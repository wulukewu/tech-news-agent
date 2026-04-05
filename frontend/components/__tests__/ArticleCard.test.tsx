import { render, screen, fireEvent } from '@testing-library/react';
import { ArticleCard } from '../ArticleCard';
import type { Article } from '@/types/article';

describe('ArticleCard', () => {
  const mockArticle: Article = {
    id: 'article-1',
    title: 'Test Article Title',
    url: 'https://example.com/article',
    feedName: 'Tech Blog',
    category: 'Technology',
    publishedAt: new Date('2024-01-01').toISOString(),
    tinkeringIndex: 4,
    aiSummary:
      'This is a test article summary that is quite long and should be expandable when it exceeds 200 characters. '.repeat(
        3,
      ),
  };

  it('should display article information', () => {
    render(<ArticleCard article={mockArticle} />);

    expect(screen.getByText('Test Article Title')).toBeInTheDocument();
    expect(screen.getByText('Tech Blog')).toBeInTheDocument();
    expect(screen.getByText('Technology')).toBeInTheDocument();
  });

  it('should render article title as a link', () => {
    render(<ArticleCard article={mockArticle} />);

    const link = screen.getByRole('link', { name: /test article title/i });
    expect(link).toHaveAttribute('href', 'https://example.com/article');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('should display tinkering index as stars', () => {
    render(<ArticleCard article={mockArticle} />);

    // Should have 5 star icons (4 filled, 1 empty)
    const stars = screen.getAllByTestId(/star-icon/i);
    expect(stars).toHaveLength(5);
  });

  it('should expand AI summary when "Read more" is clicked', () => {
    render(<ArticleCard article={mockArticle} />);

    // Initially, summary should be clamped
    const summary = screen.getByText(/this is a test article summary/i);
    expect(summary).toHaveClass('line-clamp-3');

    // Click "Read more"
    const readMoreButton = screen.getByRole('button', { name: /read more/i });
    fireEvent.click(readMoreButton);

    // Summary should no longer be clamped
    expect(summary).not.toHaveClass('line-clamp-3');

    // Button text should change to "Show less"
    expect(
      screen.getByRole('button', { name: /show less/i }),
    ).toBeInTheDocument();
  });

  it('should not show "Read more" for short summaries', () => {
    const shortArticle = {
      ...mockArticle,
      aiSummary: 'Short summary',
    };
    render(<ArticleCard article={shortArticle} />);

    expect(
      screen.queryByRole('button', { name: /read more/i }),
    ).not.toBeInTheDocument();
  });

  it('should display "Add to Reading List" button', () => {
    render(<ArticleCard article={mockArticle} />);

    const addButton = screen.getByRole('button', { name: /bookmark/i });
    expect(addButton).toBeInTheDocument();
  });

  it('should handle missing published date', () => {
    const articleWithoutDate = {
      ...mockArticle,
      publishedAt: null,
    };
    render(<ArticleCard article={articleWithoutDate} />);

    expect(screen.getByText(/unknown date/i)).toBeInTheDocument();
  });
});
