import { renderWithProviders as render } from '@/__tests__/utils/test-utils';
import { fireEvent, screen } from '@testing-library/react';
import { Navigation } from '@/components/Navigation';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock Next.js navigation
const mockUsePathname = vi.fn(() => '/dashboard');
vi.mock('next/navigation', () => ({
  usePathname: () => mockUsePathname(),
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  })),
  useSearchParams: vi.fn(() => new URLSearchParams()),
}));

// Mock Link component
vi.mock('next/link', () => {
  const MockLink = ({ children, href, ...props }: any) => {
    return (
      <a href={href} {...props}>
        {children}
      </a>
    );
  };
  MockLink.displayName = 'MockLink';
  return { default: MockLink };
});

// Mock useAuth hook
const mockLogout = vi.fn();
vi.mock('@/lib/hooks/useAuth', () => ({
  useAuth: () => ({
    logout: mockLogout,
    isAuthenticated: true,
    loading: false,
    login: vi.fn(),
    checkAuth: vi.fn(),
  }),
}));

describe('Navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUsePathname.mockReturnValue('/dashboard');
    // Reset body overflow
    document.body.style.overflow = '';
  });

  it('should display navigation links', () => {
    render(<Navigation />);

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Articles')).toBeInTheDocument();
    expect(screen.getByText('Reading List')).toBeInTheDocument();
  });

  it('should highlight active page', () => {
    mockUsePathname.mockReturnValue('/articles');

    render(<Navigation />);

    const articlesLink = screen.getByText('Articles').closest('a');
    expect(articlesLink).toHaveClass('bg-primary');
  });

  it('should display logout button', () => {
    render(<Navigation />);

    expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
  });

  it('should display application name', () => {
    render(<Navigation />);

    expect(screen.getByText('Tech News Agent')).toBeInTheDocument();
  });

  it('should have mobile menu toggle on small screens', () => {
    render(<Navigation />);

    // Mobile menu button should exist (hidden on desktop)
    const menuButton = screen.getByRole('button', { name: /toggle navigation menu/i });
    expect(menuButton).toBeInTheDocument();
  });

  it('should toggle mobile drawer when hamburger button is clicked', () => {
    render(<Navigation />);

    const menuButton = screen.getByRole('button', { name: /toggle navigation menu/i });

    // Initially drawer should not be visible
    expect(screen.queryByLabelText('Mobile navigation')).not.toBeInTheDocument();

    // Click to open drawer
    fireEvent.click(menuButton);

    // Drawer should be visible
    expect(screen.getByLabelText('Mobile navigation')).toBeInTheDocument();
  });

  it('should display backdrop overlay when drawer is open', () => {
    render(<Navigation />);

    const menuButton = screen.getByRole('button', { name: /toggle navigation menu/i });

    // Open drawer
    fireEvent.click(menuButton);

    // Backdrop should be present
    const backdrop = document.querySelector('.bg-black\\/50');
    expect(backdrop).toBeInTheDocument();
  });

  it('should close drawer when backdrop is clicked', () => {
    render(<Navigation />);

    const menuButton = screen.getByRole('button', { name: /toggle navigation menu/i });

    // Open drawer
    fireEvent.click(menuButton);
    expect(screen.getByLabelText('Mobile navigation')).toBeInTheDocument();

    // Click backdrop
    const backdrop = document.querySelector('.bg-black\\/50');
    if (backdrop) {
      fireEvent.click(backdrop);
    }

    // Drawer should be closed
    expect(screen.queryByLabelText('Mobile navigation')).not.toBeInTheDocument();
  });

  it('should close drawer when close button is clicked', () => {
    render(<Navigation />);

    const menuButton = screen.getByRole('button', { name: /toggle navigation menu/i });

    // Open drawer
    fireEvent.click(menuButton);
    expect(screen.getByLabelText('Mobile navigation')).toBeInTheDocument();

    // Click close button
    const closeButton = screen.getByRole('button', { name: /close navigation menu/i });
    fireEvent.click(closeButton);

    // Drawer should be closed
    expect(screen.queryByLabelText('Mobile navigation')).not.toBeInTheDocument();
  });

  it('should close drawer when navigation link is clicked', () => {
    render(<Navigation />);

    const menuButton = screen.getByRole('button', { name: /toggle navigation menu/i });

    // Open drawer
    fireEvent.click(menuButton);
    expect(screen.getByLabelText('Mobile navigation')).toBeInTheDocument();

    // Click a navigation link in the drawer
    const drawerNav = screen.getByLabelText('Mobile navigation');
    const dashboardLink = drawerNav.querySelector('a[href="/dashboard"]');
    if (dashboardLink) {
      fireEvent.click(dashboardLink);
    }

    // Drawer should be closed
    expect(screen.queryByLabelText('Mobile navigation')).not.toBeInTheDocument();
  });

  it('should display user profile in drawer when open', () => {
    render(<Navigation />);

    const menuButton = screen.getByRole('button', { name: /toggle navigation menu/i });

    // Open drawer
    fireEvent.click(menuButton);

    // User profile should be visible in drawer
    const drawer = screen.getByLabelText('Mobile navigation');
    expect(drawer).toHaveTextContent('testuser');
  });

  it('should display all navigation items in drawer with full-width touch targets', () => {
    render(<Navigation />);

    const menuButton = screen.getByRole('button', { name: /toggle navigation menu/i });

    // Open drawer
    fireEvent.click(menuButton);

    const drawer = screen.getByLabelText('Mobile navigation');

    // Check that all nav items are present
    expect(drawer).toHaveTextContent('Dashboard');
    expect(drawer).toHaveTextContent('Articles');
    expect(drawer).toHaveTextContent('Reading List');
    expect(drawer).toHaveTextContent('Recommendations');
    expect(drawer).toHaveTextContent('Subscriptions');
    expect(drawer).toHaveTextContent('Analytics');
    expect(drawer).toHaveTextContent('System Status');
    expect(drawer).toHaveTextContent('Settings');

    // Check that nav items have minimum height (56px)
    const navLinks = drawer.querySelectorAll('a');
    navLinks.forEach((link) => {
      expect(link).toHaveClass('min-h-56');
    });
  });

  it('should highlight active route in drawer', () => {
    mockUsePathname.mockReturnValue('/reading-list');

    render(<Navigation />);

    const menuButton = screen.getByRole('button', { name: /toggle navigation menu/i });

    // Open drawer
    fireEvent.click(menuButton);

    const drawer = screen.getByLabelText('Mobile navigation');
    const readingListLink = drawer.querySelector('a[href="/reading-list"]');

    expect(readingListLink).toHaveClass('bg-primary');
  });

  it('should prevent body scrolling when drawer is open', () => {
    render(<Navigation />);

    const menuButton = screen.getByRole('button', { name: /toggle navigation menu/i });

    // Initially body should be scrollable
    expect(document.body.style.overflow).toBe('');

    // Open drawer
    fireEvent.click(menuButton);

    // Body scrolling should be prevented
    expect(document.body.style.overflow).toBe('hidden');

    // Close drawer
    const closeButton = screen.getByRole('button', { name: /close navigation menu/i });
    fireEvent.click(closeButton);

    // Body scrolling should be restored
    expect(document.body.style.overflow).toBe('');
  });
});
